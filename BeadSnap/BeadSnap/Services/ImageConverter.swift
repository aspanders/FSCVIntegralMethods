import UIKit

final class ImageConverter {
    static let shared = ImageConverter()
    private init() {}

    func convert(
        image: UIImage,
        gridSize: GridSize,
        maxColors: Int = 12
    ) -> FusePattern {
        let cols = gridSize.width
        let rows = gridSize.height
        let pixels = samplePixels(from: image, cols: cols, rows: rows)
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

    // MARK: - Pixel Sampling

    private func samplePixels(from image: UIImage, cols: Int, rows: Int) -> [[[CGFloat]]] {
        guard let cgImage = image.cgImage else { return [] }
        var rawData = [UInt8](repeating: 0, count: cols * rows * 4)
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        guard let ctx = CGContext(
            data: &rawData, width: cols, height: rows,
            bitsPerComponent: 8, bytesPerRow: cols * 4, space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else { return [] }
        ctx.draw(cgImage, in: CGRect(x: 0, y: 0, width: cols, height: rows))
        var pixels = Array(repeating: Array(repeating: [CGFloat](repeating: 0, count: 4), count: cols), count: rows)
        for y in 0..<rows {
            for x in 0..<cols {
                let i = (y * cols + x) * 4
                let a = CGFloat(rawData[i + 3]) / 255
                if a < 0.15 {
                    pixels[y][x] = [-1, -1, -1, -1]
                } else {
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
        let full = PaletteColor.beadSafe
        let fullLAB = full.map { c -> (Double, Double, Double) in
            var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
            c.uiColor.getRed(&r, green: &g, blue: &b, alpha: &a)
            return rgbToLAB(r: Double(r), g: Double(g), b: Double(b))
        }

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

        // Limit palette to maxColors most-used
        let topIDs = Set(counts.sorted { $0.value > $1.value }.prefix(maxColors).map(\.key))

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
        func lin(_ c: Double) -> Double { c > 0.04045 ? pow((c+0.055)/1.055, 2.4) : c/12.92 }
        let (rl, gl, bl) = (lin(r), lin(g), lin(b))
        let x = (rl*0.4124564 + gl*0.3575761 + bl*0.1804375) / 0.95047
        let y = (rl*0.2126729 + gl*0.7151522 + bl*0.0721750) / 1.00000
        let z = (rl*0.0193339 + gl*0.1191920 + bl*0.9503041) / 1.08883
        func f(_ t: Double) -> Double { t > 0.008856 ? pow(t, 1.0/3.0) : 7.787*t+16.0/116.0 }
        return (116*f(y)-16, 500*(f(x)-f(y)), 200*(f(y)-f(z)))
    }
}
