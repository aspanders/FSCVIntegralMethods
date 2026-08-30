import UIKit

/// The live photo-to-beads workspace: one photo, one keep-mask, and the bead
/// pattern they currently produce.
///
/// A port of the Android `PhotoStudio`, with one deliberate simplification noted
/// under `buildPattern`. The colour maths is shared with Android through
/// `ColorMath`, and `tools/kotlin-check/parity.py` fails the build if the two
/// drift apart - the same photo must give the same pattern on both platforms.
///
/// The photo is resampled once to at most `workMaxDim` and kept as linear-light
/// floats. At 384px a 48x48 board still averages roughly 8x8 source pixels per
/// bead; the committed pattern is re-derived from the full-resolution photo, so
/// this approximation never ships inside a saved pattern.
/// `@unchecked Sendable` because it is a mutable class handed to
/// `Task.detached` for the rebuild. Every mutation goes through
/// `PhotoTuneModel`, which is `@MainActor`, and a rebuild only READS - so there
/// is exactly one writer and the reads cannot interleave with it. The compiler
/// cannot see that, hence "unchecked". If a second writer is ever added, this
/// annotation stops being true and must go.
final class PhotoStudio: @unchecked Sendable {

    static let workMaxDim = 384

    let width: Int
    let height: Int

    /// Linear-light RGB, 3 floats per pixel, row-major.
    private let lin: [Double]
    /// The source image's own alpha, 0..1 - already-transparent input stays out.
    private let srcAlpha: [Double]
    /// The photo's original sRGB bytes, for a preview that costs nothing.
    private let srgb: [UInt8]      // 3 per pixel

    /// true = this pixel becomes beads.
    private(set) var keep: [Bool]

    private init(width: Int, height: Int, lin: [Double], srcAlpha: [Double], srgb: [UInt8]) {
        self.width = width
        self.height = height
        self.lin = lin
        self.srcAlpha = srcAlpha
        self.srgb = srgb
        self.keep = Array(repeating: true, count: width * height)
    }

    /// Resample `image` into a working buffer and take its linear-light copy.
    static func from(_ image: UIImage, maxDim: Int = workMaxDim) -> PhotoStudio? {
        guard let cg = uprightCGImage(image, maxDim: maxDim) else { return nil }
        let w = cg.width, h = cg.height
        guard w > 0, h > 0 else { return nil }

        var raw = [UInt8](repeating: 0, count: w * h * 4)
        guard let ctx = CGContext(
            data: &raw, width: w, height: h,
            bitsPerComponent: 8, bytesPerRow: w * 4,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else { return nil }
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))

        var table = [Double](repeating: 0, count: 256)
        for i in 0..<256 { table[i] = ColorMath.srgbToLinear(Double(i) / 255.0) }

        var lin = [Double](repeating: 0, count: w * h * 3)
        var alpha = [Double](repeating: 0, count: w * h)
        var srgb = [UInt8](repeating: 0, count: w * h * 3)
        for i in 0..<(w * h) {
            let a = Int(raw[i * 4 + 3])
            alpha[i] = Double(a) / 255.0
            let inv = a > 0 ? 255.0 / Double(a) : 0.0
            for c in 0..<3 {
                let v = min(255, Int(Double(raw[i * 4 + c]) * inv))
                srgb[i * 3 + c] = UInt8(v)
                lin[i * 3 + c] = table[v]
            }
        }
        return PhotoStudio(width: w, height: h, lin: lin, srcAlpha: alpha, srgb: srgb)
    }

    /// The image, upright and bounded. `UIImage.cgImage` discards
    /// `imageOrientation`, so a portrait capture would otherwise be worked on
    /// sideways for the whole session.
    private static func uprightCGImage(_ image: UIImage, maxDim: Int) -> CGImage? {
        let longest = max(image.size.width, image.size.height)
        let scale = min(1.0, CGFloat(maxDim) / max(longest, 1))
        let target = CGSize(width: max(1, (image.size.width * scale).rounded()),
                            height: max(1, (image.size.height * scale).rounded()))
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        format.opaque = false
        return UIGraphicsImageRenderer(size: target, format: format).image { _ in
            image.draw(in: CGRect(origin: .zero, size: target))
        }.cgImage
    }

    // MARK: - Mask editing

    func keepAll() { keep = Array(repeating: true, count: width * height) }
    func clearAll() { keep = Array(repeating: false, count: width * height) }

    /// Adopt an automatic mask of any resolution, nearest-neighbour resampled
    /// onto the working buffer. The segmenter runs at its own working size,
    /// which is not this one.
    func adoptMask(_ mask: [Bool], maskW: Int, maskH: Int) {
        guard maskW > 0, maskH > 0, mask.count == maskW * maskH else { return }
        for y in 0..<height {
            let sy = min(max(y * maskH / height, 0), maskH - 1)
            for x in 0..<width {
                let sx = min(max(x * maskW / width, 0), maskW - 1)
                keep[y * width + x] = mask[sy * maskW + sx]
            }
        }
    }

    /// Paint a circle of the mask. `nx`/`ny` are 0..1 across the whole photo;
    /// `radiusFrac` is a fraction of its longer side. Returns whether anything
    /// actually changed, so a caller can skip a rebuild that would be identical.
    @discardableResult
    func brush(nx: Double, ny: Double, radiusFrac: Double, keepValue: Bool) -> Bool {
        let cx = Int((nx * Double(width)).rounded())
        let cy = Int((ny * Double(height)).rounded())
        let radius = max(1, Int((radiusFrac * Double(max(width, height))).rounded()))
        let x0 = min(max(cx - radius, 0), width - 1)
        let x1 = min(max(cx + radius, 0), width - 1)
        let y0 = min(max(cy - radius, 0), height - 1)
        let y1 = min(max(cy + radius, 0), height - 1)
        let r2 = radius * radius
        var changed = false
        guard x0 <= x1, y0 <= y1 else { return false }
        for y in y0...y1 {
            let dy = y - cy
            let base = y * width
            for x in x0...x1 {
                let dx = x - cx
                if dx * dx + dy * dy > r2 { continue }
                if keep[base + x] != keepValue {
                    keep[base + x] = keepValue
                    changed = true
                }
            }
        }
        return changed
    }

    var keptFraction: Double {
        var n = 0
        for k in keep where k { n += 1 }
        return keep.isEmpty ? 0 : Double(n) / Double(keep.count)
    }

    // MARK: - White balance

    /// Grey-world gains measured over the KEPT pixels only.
    ///
    /// Measuring the whole frame lets a large background drag the estimate
    /// around - a wooden table makes everything bluer to compensate. Measuring
    /// what will actually become beads is what puts the blue back in a blue
    /// subject. The clamp is the backstop for a session where nothing has been
    /// removed yet, so "kept" still means the whole frame.
    func measureGreyWorld() -> (Double, Double, Double) {
        var r = 0.0, g = 0.0, b = 0.0, n = 0
        for i in 0..<keep.count {
            if !keep[i] || srcAlpha[i] < 0.5 { continue }
            r += lin[i * 3]; g += lin[i * 3 + 1]; b += lin[i * 3 + 2]
            n += 1
        }
        guard n > 0, r > 0, g > 0, b > 0 else { return (1, 1, 1) }
        r /= Double(n); g /= Double(n); b /= Double(n)
        let mean = (r + g + b) / 3.0
        func clamp(_ v: Double) -> Double { min(max(v, Self.gainMin), Self.gainMax) }
        return (clamp(mean / r), clamp(mean / g), clamp(mean / b))
    }

    private static let gainMin = 0.70
    private static let gainMax = 1.45

    // MARK: - Preview

    private static let checker = 12

    /// The photo with dropped pixels knocked back to `fade` of their brightness
    /// over a light checker, so what will and will not become beads is obvious
    /// at a glance without hiding what is underneath the brush.
    func photoPreview(fade: Double = 0.22) -> UIImage? {
        var px = [UInt8](repeating: 255, count: width * height * 4)
        let f = min(max(fade, 0), 1)
        for y in 0..<height {
            let band = (y / Self.checker) & 1
            for x in 0..<width {
                let i = y * width + x
                let o = i * 4
                if keep[i] {
                    px[o] = srgb[i * 3]; px[o + 1] = srgb[i * 3 + 1]; px[o + 2] = srgb[i * 3 + 2]
                } else {
                    // A checkerboard behind the dropped area: a plain fade just
                    // reads as the photo being dark there.
                    let tile: Double = (((x / Self.checker) & 1) ^ band) == 0 ? 230 : 199
                    for c in 0..<3 {
                        px[o + c] = UInt8(min(255, max(0,
                            Int((Double(srgb[i * 3 + c]) * f + tile * (1 - f)).rounded()))))
                    }
                }
                px[o + 3] = 255
            }
        }
        return Self.image(from: px, width: width, height: height)
    }

    private static func image(from rgba: [UInt8], width: Int, height: Int) -> UIImage? {
        var data = rgba
        guard let ctx = CGContext(
            data: &data, width: width, height: height,
            bitsPerComponent: 8, bytesPerRow: width * 4,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ), let cg = ctx.makeImage() else { return nil }
        return UIImage(cgImage: cg)
    }

    // MARK: - The pattern

    /// The bead pattern the photo and mask currently produce.
    ///
    /// Unlike Android this does NOT keep a per-cell cache of distances to every
    /// bead and recompute only the cells a brush stroke touched. At the 384px
    /// working size a full rebuild is a few tens of milliseconds, which a
    /// debounced live preview absorbs; the cache exists on Android to hold 60fps
    /// while a finger is moving. The OUTPUT is identical either way - the
    /// caching is about when the work happens, not what it produces.
    /// `userCrop` is the rect the user chose in the Crop tab, in this studio's
    /// own pixels. Nil keeps the previous behaviour exactly: the largest centred
    /// rect of the board's shape.
    func buildPattern(title: String, cols: Int, rows: Int,
                      maxColors: Int, shape: PegboardShape,
                      gains: (Double, Double, Double),
                      userCrop: ImageConverter.CropRect? = nil) -> FusePattern {
        // Even a user-chosen crop goes back through fitAspect, so changing the
        // board size afterwards reshapes it rather than leaving a rect of the
        // old proportions to be stretched onto the new grid.
        let crop: ImageConverter.CropRect
        if let u = userCrop {
            crop = ImageConverter.fitAspect(
                cx: u.minX + u.width / 2, cy: u.minY + u.height / 2,
                wantW: u.width, wantH: u.height,
                srcW: width, srcH: height, cols: cols, rows: rows)
        } else {
            crop = ImageConverter.aspectCrop(width: width, height: height, cols: cols, rows: rows)
        }
        let full = PaletteColor.full
        let fullLAB: [(Double, Double, Double)] = full.map { c in
            var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
            c.uiColor.getRed(&r, green: &g, blue: &b, alpha: &a)
            return ColorMath.srgbToLab(Double(r), Double(g), Double(b))
        }

        var assignments = Array(repeating: [String?](repeating: nil, count: cols), count: rows)
        var counts: [String: Int] = [:]
        var labs = Array(repeating: [(Double, Double, Double)?](repeating: nil, count: cols), count: rows)

        for cy in 0..<rows {
            let sy0 = crop.minY + cy * crop.height / rows
            let sy1 = max(sy0 + 1, crop.minY + (cy + 1) * crop.height / rows)
            for cx in 0..<cols {
                if !shape.contains(x: cx, y: cy, cols: cols, rows: rows) { continue }
                let sx0 = crop.minX + cx * crop.width / cols
                let sx1 = max(sx0 + 1, crop.minX + (cx + 1) * crop.width / cols)

                var r = 0.0, g = 0.0, b = 0.0, w = 0.0, kept = 0, total = 0
                for sy in sy0..<min(sy1, height) {
                    for sx in sx0..<min(sx1, width) {
                        let i = sy * width + sx
                        total += 1
                        if !keep[i] || srcAlpha[i] < 0.5 { continue }
                        kept += 1
                        let a = srcAlpha[i]
                        r += lin[i * 3] * a; g += lin[i * 3 + 1] * a; b += lin[i * 3 + 2] * a
                        w += a
                    }
                }
                // A cell that is mostly masked out stays an empty peg, so a
                // cut-out leaves real holes rather than muddy edges.
                if total == 0 || w <= 0 || Double(kept) / Double(total) < 0.35 { continue }

                let lab = ColorMath.linearRgbToLab(
                    min(max(r / w * gains.0, 0), 1),
                    min(max(g / w * gains.1, 0), 1),
                    min(max(b / w * gains.2, 0), 1)
                )
                labs[cy][cx] = lab
                var bestIdx = 0, bestD = Double.infinity
                for (i, pLAB) in fullLAB.enumerated() {
                    let d = ColorMath.beadDistance(lab, pLAB)
                    if d < bestD { bestD = d; bestIdx = i }
                }
                let id = full[bestIdx].id
                assignments[cy][cx] = id
                counts[id, default: 0] += 1
            }
        }

        // Narrow to the most-used colours, ties broken by palette order so the
        // same photo always yields the same palette.
        let paletteIndex = Dictionary(uniqueKeysWithValues: full.enumerated().map { ($1.id, $0) })
        let topIDs = Set(counts.sorted {
            $0.value != $1.value ? $0.value > $1.value
                                 : (paletteIndex[$0.key] ?? 0) < (paletteIndex[$1.key] ?? 0)
        }.prefix(maxColors).map(\.key))

        if counts.count > maxColors {
            let topPalette = full.filter { topIDs.contains($0.id) }
            let topLAB: [(Double, Double, Double)] = topPalette.map { c in
                var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
                c.uiColor.getRed(&r, green: &g, blue: &b, alpha: &a)
                return ColorMath.srgbToLab(Double(r), Double(g), Double(b))
            }
            for y in 0..<rows {
                for x in 0..<cols {
                    guard let id = assignments[y][x], !topIDs.contains(id),
                          let lab = labs[y][x] else { continue }
                    var bestIdx = 0, bestD = Double.infinity
                    for (i, pLAB) in topLAB.enumerated() {
                        let d = ColorMath.beadDistance(lab, pLAB)
                        if d < bestD { bestD = d; bestIdx = i }
                    }
                    assignments[y][x] = topPalette[bestIdx].id
                }
            }
        }

        var cells: [Cell] = []
        for y in 0..<rows {
            for x in 0..<cols {
                if let id = assignments[y][x] { cells.append(Cell(x: x, y: y, colorId: id)) }
            }
        }
        let usedIDs = Set(cells.compactMap(\.colorId))
        let beadCount = cells.count
        return FusePattern(
            id: UUID().uuidString,
            title: title,
            category: .custom,
            createdBy: .user,
            grid: GridSize(width: cols, height: rows),
            palette: full.filter { usedIDs.contains($0.id) },
            cells: cells,
            difficulty: beadCount < 80 ? .easy : beadCount < 350 ? .medium : .hard,
            tags: ["photo", "imported"],
            sourcePrompt: nil,
            shape: shape,
            version: 1
        )
    }

    /// The full-resolution photo with everything the user removed made
    /// transparent, so the saved project keeps the cut-out rather than only the
    /// board that came out of it.
    func maskedFullRes(_ src: UIImage) -> UIImage? {
        guard let cg = src.cgImage else { return nil }
        let w = cg.width, h = cg.height
        guard w > 0, h > 0 else { return nil }
        var raw = [UInt8](repeating: 0, count: w * h * 4)
        guard let ctx = CGContext(
            data: &raw, width: w, height: h,
            bitsPerComponent: 8, bytesPerRow: w * 4,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else { return nil }
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))
        for y in 0..<h {
            let sy = min(max(y * height / h, 0), height - 1)
            for x in 0..<w {
                let sx = min(max(x * width / w, 0), width - 1)
                if !keep[sy * width + sx] {
                    let o = (y * w + x) * 4
                    raw[o] = 0; raw[o + 1] = 0; raw[o + 2] = 0; raw[o + 3] = 0
                }
            }
        }
        return Self.image(from: raw, width: w, height: h)
    }
}
