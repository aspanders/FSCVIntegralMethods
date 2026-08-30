import UIKit

enum ConversionError: LocalizedError {
    case unreadableImage

    var errorDescription: String? {
        switch self {
        case .unreadableImage: return "Could not read that image. Try a different photo."
        }
    }
}

final class ImageConverter {
    static let shared = ImageConverter()
    private init() {}

    func convert(
        image: UIImage,
        gridSize: GridSize,
        maxColors: Int = 12
    ) throws -> FusePattern {
        let cols = gridSize.width
        let rows = gridSize.height
        guard let cells0 = sampleCells(from: image, cols: cols, rows: rows) else {
            throw ConversionError.unreadableImage
        }
        let (palette, assignments) = quantizeBeadSafe(
            cells: cells0, cols: cols, rows: rows, maxColors: min(maxColors, 16)
        )
        var cells: [Cell] = []
        for y in 0..<rows {
            for x in 0..<cols {
                if let colorId = assignments[y][x] {
                    cells.append(Cell(x: x, y: y, colorId: colorId))
                }
            }
        }
        let beadCount = cells.count
        let difficulty: Difficulty = beadCount < 80 ? .easy : beadCount < 350 ? .medium : .hard
        return FusePattern(
            id: UUID().uuidString,
            title: "Imported Photo",
            category: .custom,
            createdBy: .user,
            grid: gridSize,
            palette: palette,
            cells: cells,
            difficulty: difficulty,
            tags: ["photo", "imported"],
            sourcePrompt: nil,
            version: 1
        )
    }

    // MARK: - Shared Pattern Renderer

    /// Renders a pattern to an image: thumbnails, previews, and PNG export all
    /// use this so output matches Android's ImageConverter.renderToBitmap.
    static func renderToImage(pattern: FusePattern, cellSize: CGFloat = 16) -> UIImage {
        let w = CGFloat(pattern.grid.width) * cellSize
        let h = CGFloat(pattern.grid.height) * cellSize
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        let renderer = UIGraphicsImageRenderer(size: CGSize(width: w, height: h), format: format)
        let colorById = Dictionary(uniqueKeysWithValues: pattern.palette.map { ($0.id, $0) })
        let r = cellSize / 2                 // bead radius = half the pitch, so beads touch
        let holeR = cellSize * 0.17          // the tube hole through a fuse bead
        let rimWidth = max(0.5, cellSize * 0.05)
        return renderer.image { _ in
            UIColor.white.setFill()
            UIRectFill(CGRect(x: 0, y: 0, width: w, height: h))
            for cell in pattern.cells {
                guard let id = cell.colorId, let c = colorById[id] else { continue }
                let cx = CGFloat(cell.x) * cellSize + r
                let cy = CGFloat(cell.y) * cellSize + r
                let beadRect = CGRect(x: cx - r, y: cy - r, width: 2 * r, height: 2 * r)
                // Full-size bead: its edges meet the neighbors, like fused beads.
                c.uiColor.setFill()
                UIBezierPath(ovalIn: beadRect).fill()
                // Faint center hole gives the fused-bead look.
                UIColor.white.withAlphaComponent(0.11).setFill()
                UIBezierPath(ovalIn: CGRect(x: cx - holeR, y: cy - holeR,
                                            width: 2 * holeR, height: 2 * holeR)).fill()
                // Thin rim for definition where beads meet.
                let rim = UIBezierPath(ovalIn: beadRect.insetBy(dx: rimWidth / 2, dy: rimWidth / 2))
                UIColor.black.withAlphaComponent(0.12).setStroke()
                rim.lineWidth = rimWidth
                rim.stroke()
            }
        }
    }

    // MARK: - Crop

    /// A rectangle of source pixels, in source coordinates.
    struct CropRect {
        var minX: Int, minY: Int, width: Int, height: Int
    }

    /// The largest rect of the cols:rows ratio that fits inside `srcW` x `srcH`,
    /// no larger than `wantW` x `wantH`, sitting as close to (`cx`, `cy`) as
    /// staying inside the image allows.
    ///
    /// The sampler stretches whatever rect it is handed onto the grid, so a crop
    /// of the wrong shape squashes the picture. This is the one place that shape
    /// is enforced, and both the default crop and the crop the user drags come
    /// through it, so they cannot drift apart.
    ///
    /// Growing a box to a ratio and then clamping its edges into bounds
    /// separately undoes the ratio - that shipped on Android and squashed every
    /// portrait photo. See tools/kotlin-check/Crop.kt, which pins the same
    /// maths there.
    static func fitAspect(cx: Int, cy: Int,
                          wantW: Int, wantH: Int,
                          srcW: Int, srcH: Int,
                          cols: Int, rows: Int) -> CropRect {
        guard srcW > 0, srcH > 0, cols > 0, rows > 0 else {
            return CropRect(minX: 0, minY: 0, width: max(1, srcW), height: max(1, srcH))
        }
        let target = Double(cols) / Double(rows)
        var bw = max(1, wantW)
        var bh = max(1, wantH)
        if Double(bw) / Double(bh) < target {
            bw = Int((Double(bh) * target).rounded())
        } else {
            bh = Int((Double(bw) / target).rounded())
        }
        // Shrink to what the image can hold, keeping the ratio. Reaching the
        // second branch means the first left the other side room to spare, so
        // one pass in this order is enough.
        if bw > srcW { bw = srcW; bh = Int((Double(bw) / target).rounded()) }
        if bh > srcH { bh = srcH; bw = Int((Double(bh) * target).rounded()) }
        bw = min(max(bw, 1), srcW)
        bh = min(max(bh, 1), srcH)

        // Slide it fully inside the image rather than cutting an edge off it.
        let left = min(max(cx - bw / 2, 0), srcW - bw)
        let top = min(max(cy - bh / 2, 0), srcH - bh)
        return CropRect(minX: left, minY: top, width: bw, height: bh)
    }

    /// The largest centred rect of `width` x `height` whose aspect ratio matches
    /// a cols x rows grid.
    ///
    /// Used as the default crop so photos keep their proportions instead of
    /// being stretched onto a square board - a face converted without this comes
    /// out squashed. Ported from the Android `ImageConverter.aspectCrop`.
    static func aspectCrop(width srcW: Int, height srcH: Int, cols: Int, rows: Int) -> CropRect {
        guard srcW > 0, srcH > 0, cols > 0, rows > 0 else {
            return CropRect(minX: 0, minY: 0, width: max(1, srcW), height: max(1, srcH))
        }
        let target = Double(cols) / Double(rows)
        let current = Double(srcW) / Double(srcH)
        if current > target {
            // Too wide: trim the sides.
            let w = min(max(Int((Double(srcH) * target).rounded()), 1), srcW)
            return CropRect(minX: (srcW - w) / 2, minY: 0, width: w, height: srcH)
        } else {
            // Too tall: trim top and bottom.
            let h = min(max(Int((Double(srcW) / target).rounded()), 1), srcH)
            return CropRect(minX: 0, minY: (srcH - h) / 2, width: srcW, height: h)
        }
    }

    // MARK: - Pixel Sampling

    /// The photo, upright and no larger than this on its long side.
    ///
    /// `UIImage.cgImage` throws away `imageOrientation`, so drawing it directly
    /// renders a photo taken in portrait on its side - which is what iOS was
    /// doing to every camera capture. Redrawing through UIGraphics bakes the
    /// orientation into the pixels.
    private static let workMaxDim: CGFloat = 1024

    private func upright(_ image: UIImage) -> CGImage? {
        let scale = min(1.0, ImageConverter.workMaxDim / max(image.size.width, image.size.height))
        let target = CGSize(width: (image.size.width * scale).rounded(),
                            height: (image.size.height * scale).rounded())
        guard target.width >= 1, target.height >= 1 else { return image.cgImage }
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        format.opaque = false
        let drawn = UIGraphicsImageRenderer(size: target, format: format).image { _ in
            image.draw(in: CGRect(origin: .zero, size: target))
        }
        return drawn.cgImage
    }

    /// Straight (un-premultiplied) 8-bit RGBA of the upright photo.
    private func rgba(from image: UIImage) -> (px: [UInt8], w: Int, h: Int)? {
        guard let cg = upright(image) else { return nil }
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
        return (raw, w, h)
    }

    /// One linear-light colour per bead, or nil where the cell is see-through.
    ///
    /// The old version handed the whole photo to Core Graphics at cols x rows and
    /// let it box-average, which is right for a shaded surface and wrong at a
    /// boundary: a cell covering 60% muzzle and 40% nose averages to a muddy
    /// brown belonging to neither. Sampling the real pixels and letting
    /// `ColorMath.resolveCell` choose between averaging and snapping is what
    /// keeps small dark features - an eye, a nostril - from dissolving.
    private func sampleCells(from image: UIImage, cols: Int, rows: Int) -> [[(Double, Double, Double)?]]? {
        guard let (px, w, h) = rgba(from: image) else { return nil }

        // sRGB byte -> linear light, once.
        var lin = [Double](repeating: 0, count: 256)
        for i in 0..<256 { lin[i] = ColorMath.srgbToLinear(Double(i) / 255.0) }

        var out = Array(repeating: Array<(Double, Double, Double)?>(repeating: nil, count: cols), count: rows)

        for cy in 0..<rows {
            let sy0 = cy * h / rows
            let sy1 = max(sy0 + 1, (cy + 1) * h / rows)
            for cx in 0..<cols {
                let sx0 = cx * w / cols
                let sx1 = max(sx0 + 1, (cx + 1) * w / cols)

                var rAcc = 0.0, gAcc = 0.0, bAcc = 0.0, aAcc = 0.0, lAcc = 0.0
                var n = 0
                var lMin = Double.greatestFiniteMagnitude
                var lMax = -Double.greatestFiniteMagnitude

                for sy in sy0..<sy1 {
                    for sx in sx0..<sx1 {
                        let i = (sy * w + sx) * 4
                        let a = Int(px[i + 3])
                        n += 1
                        if a == 0 { continue }
                        // The buffer is premultiplied; recover straight colour.
                        let inv = 255.0 / Double(a)
                        let pr = lin[min(255, Int(Double(px[i]) * inv))]
                        let pg = lin[min(255, Int(Double(px[i + 1]) * inv))]
                        let pb = lin[min(255, Int(Double(px[i + 2]) * inv))]
                        let y = ColorMath.luma(pr, pg, pb)
                        if y < lMin { lMin = y }
                        if y > lMax { lMax = y }
                        let wgt = Double(a) / 255.0
                        aAcc += wgt; lAcc += y * wgt
                        rAcc += pr * wgt; gAcc += pg * wgt; bAcc += pb * wgt
                    }
                }
                // Mostly-transparent cells stay empty, so a cut-out leaves real
                // holes instead of muddy edges.
                if n == 0 || aAcc / Double(n) < 0.35 { continue }

                let mR = rAcc / aAcc, mG = gAcc / aAcc, mB = bAcc / aAcc
                if lMax - lMin < ColorMath.edgeMinLumaRange {
                    out[cy][cx] = (mR, mG, mB)
                    continue
                }

                // Second pass, only where the cell could straddle an edge.
                let midL = lAcc / aAcc
                var dr = 0.0, dg = 0.0, db = 0.0, dw = 0.0
                var xr = 0.0, xg = 0.0, xb = 0.0, xw = 0.0
                for sy in sy0..<sy1 {
                    for sx in sx0..<sx1 {
                        let i = (sy * w + sx) * 4
                        let a = Int(px[i + 3])
                        if a == 0 { continue }
                        let inv = 255.0 / Double(a)
                        let pr = lin[min(255, Int(Double(px[i]) * inv))]
                        let pg = lin[min(255, Int(Double(px[i + 1]) * inv))]
                        let pb = lin[min(255, Int(Double(px[i + 2]) * inv))]
                        let wgt = Double(a) / 255.0
                        if ColorMath.luma(pr, pg, pb) <= midL {
                            dr += pr * wgt; dg += pg * wgt; db += pb * wgt; dw += wgt
                        } else {
                            xr += pr * wgt; xg += pg * wgt; xb += pb * wgt; xw += wgt
                        }
                    }
                }
                out[cy][cx] = ColorMath.resolveCell(
                    meanR: mR, meanG: mG, meanB: mB,
                    darkR: dr, darkG: dg, darkB: db, darkW: dw,
                    liteR: xr, liteG: xg, liteB: xb, liteW: xw
                )
            }
        }
        return out
    }

    // MARK: - Bead-Safe Nearest-Color Quantization

    /// Assigns a bead to every cell, then narrows to `maxColors`.
    ///
    /// Distance is `ColorMath.beadDistance` - CIEDE2000 with a penalty for
    /// draining chroma - not the squared Euclidean dE76 this used before. Plain
    /// dE76 weights a unit of lightness exactly like a unit of chroma, and
    /// against a palette holding nine pure neutrals it kept scoring a grey of
    /// the right lightness as closer than a bead of the right hue. That is why
    /// photos converted grey.
    private func quantizeBeadSafe(
        cells: [[(Double, Double, Double)?]],
        cols: Int, rows: Int,
        maxColors: Int
    ) -> ([PaletteColor], [[String?]]) {
        let full = PaletteColor.full
        let fullLAB: [(Double, Double, Double)] = full.map { c in
            var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
            c.uiColor.getRed(&r, green: &g, blue: &b, alpha: &a)
            return ColorMath.srgbToLab(Double(r), Double(g), Double(b))
        }
        let paletteIndex = Dictionary(uniqueKeysWithValues: full.enumerated().map { ($1.id, $0) })

        var assignments = Array(repeating: Array<String?>(repeating: nil, count: cols), count: rows)
        var counts: [String: Int] = [:]

        // The cell colours are LINEAR light, so they go to LAB directly.
        var labs = Array(repeating: Array<(Double, Double, Double)?>(repeating: nil, count: cols), count: rows)

        for y in 0..<rows {
            for x in 0..<cols {
                guard let c = cells[y][x] else { continue }
                let lab = ColorMath.linearRgbToLab(c.0, c.1, c.2)
                labs[y][x] = lab
                var bestIdx = 0, bestD = Double.infinity
                for (i, pLAB) in fullLAB.enumerated() {
                    let d = ColorMath.beadDistance(lab, pLAB)
                    if d < bestD { bestD = d; bestIdx = i }
                }
                let id = full[bestIdx].id
                assignments[y][x] = id
                counts[id, default: 0] += 1
            }
        }

        // Keep the most-used colours; break ties by palette order so the same
        // photo always yields the same palette.
        let topIDs = Set(
            counts.sorted {
                $0.value != $1.value
                    ? $0.value > $1.value
                    : (paletteIndex[$0.key] ?? 0) < (paletteIndex[$1.key] ?? 0)
            }
            .prefix(maxColors).map(\.key)
        )

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

        let usedIDs = Set(assignments.flatMap { $0 }.compactMap { $0 })
        let palette = full.filter { usedIDs.contains($0.id) }
        return (palette, assignments)
    }

}
