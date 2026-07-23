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
        guard let pixels = samplePixels(from: image, cols: cols, rows: rows) else {
            throw ConversionError.unreadableImage
        }
        let (palette, assignments) = quantizeBeadSafe(
            pixels: pixels, cols: cols, rows: rows, maxColors: min(maxColors, 16)
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

    // MARK: - Pixel Sampling

    private func samplePixels(from image: UIImage, cols: Int, rows: Int) -> [[[CGFloat]]]? {
        guard let cgImage = image.cgImage else { return nil }
        var rawData = [UInt8](repeating: 0, count: cols * rows * 4)
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        guard let ctx = CGContext(
            data: &rawData, width: cols, height: rows,
            bitsPerComponent: 8, bytesPerRow: cols * 4, space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else { return nil }
        ctx.draw(cgImage, in: CGRect(x: 0, y: 0, width: cols, height: rows))
        var pixels = Array(repeating: Array(repeating: [CGFloat](repeating: 0, count: 4), count: cols), count: rows)
        for y in 0..<rows {
            for x in 0..<cols {
                let i = (y * cols + x) * 4
                let a = CGFloat(rawData[i + 3]) / 255
                if a < 0.15 {
                    pixels[y][x] = [-1, -1, -1, -1]
                } else {
                    // buffer is premultiplied: divide by alpha to recover straight color
                    let scale = a > 0 ? 1 / (255 * a) : 0
                    pixels[y][x] = [
                        min(CGFloat(rawData[i])   * scale, 1),
                        min(CGFloat(rawData[i+1]) * scale, 1),
                        min(CGFloat(rawData[i+2]) * scale, 1),
                        a
                    ]
                }
            }
        }
        return pixels
    }

    // MARK: - Bead-Safe Nearest-Color Quantization

    private func quantizeBeadSafe(
        pixels: [[[CGFloat]]],
        cols: Int, rows: Int,
        maxColors: Int
    ) -> ([PaletteColor], [[String?]]) {
        let full = PaletteColor.full
        let fullLAB = full.map { c -> (Double, Double, Double) in
            var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
            c.uiColor.getRed(&r, green: &g, blue: &b, alpha: &a)
            return rgbToLAB(r: Double(r), g: Double(g), b: Double(b))
        }
        let paletteIndex = Dictionary(uniqueKeysWithValues: full.enumerated().map { ($1.id, $0) })

        var assignments = Array(repeating: Array<String?>(repeating: nil, count: cols), count: rows)
        var counts: [String: Int] = [:]

        for y in 0..<rows {
            for x in 0..<cols {
                let p = pixels[y][x]
                guard p[3] >= 0 else { continue }
                let lab = rgbToLAB(r: Double(p[0]), g: Double(p[1]), b: Double(p[2]))
                var bestIdx = 0; var bestD = Double.infinity
                for (i, pLAB) in fullLAB.enumerated() {
                    let d = pow(lab.0-pLAB.0,2)+pow(lab.1-pLAB.1,2)+pow(lab.2-pLAB.2,2)
                    if d < bestD { bestD = d; bestIdx = i }
                }
                let id = full[bestIdx].id
                assignments[y][x] = id
                counts[id, default: 0] += 1
            }
        }

        // Limit palette to maxColors most-used; break count ties by palette order
        // so the same photo always yields the same palette.
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
            let topLAB = topPalette.map { c -> (Double, Double, Double) in
                var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
                c.uiColor.getRed(&r, green: &g, blue: &b, alpha: &a)
                return rgbToLAB(r: Double(r), g: Double(g), b: Double(b))
            }
            for y in 0..<rows {
                for x in 0..<cols {
                    guard let id = assignments[y][x], !topIDs.contains(id) else { continue }
                    let p = pixels[y][x]
                    let lab = rgbToLAB(r: Double(p[0]), g: Double(p[1]), b: Double(p[2]))
                    var bestIdx = 0; var bestD = Double.infinity
                    for (i, pLAB) in topLAB.enumerated() {
                        let d = pow(lab.0-pLAB.0,2)+pow(lab.1-pLAB.1,2)+pow(lab.2-pLAB.2,2)
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

    // MARK: - CIE LAB

    private func rgbToLAB(r: Double, g: Double, b: Double) -> (Double, Double, Double) {
        let lab = BeadColor.rgbToLAB(r: r, g: g, b: b)
        return (lab.l, lab.a, lab.b)
    }
}
