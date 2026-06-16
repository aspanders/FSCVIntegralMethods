import UIKit

final class PatternConverter {
    static let shared = PatternConverter()
    private let quantizer = ColorQuantizer.shared
    private init() {}

    func convert(image: UIImage, config: PatternConfig) -> BeadPattern {
        let (cols, rows) = config.size.beadCount
        let grid = buildGrid(image: image, cols: cols, rows: rows, layout: config.layout)
        return BeadPattern(config: config, grid: grid)
    }

    private func buildGrid(
        image: UIImage,
        cols: Int,
        rows: Int,
        layout: PatternLayout
    ) -> [[String?]] {
        guard let cgImage = image.cgImage else {
            return Array(repeating: Array(repeating: nil, count: cols), count: rows)
        }

        let colorSpace = CGColorSpaceCreateDeviceRGB()
        let bytesPerPixel = 4
        let width = cols
        let height = rows
        let bytesPerRow = width * bytesPerPixel
        var rawData = [UInt8](repeating: 0, count: width * height * bytesPerPixel)

        guard let context = CGContext(
            data: &rawData,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: bytesPerRow,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            return Array(repeating: Array(repeating: nil, count: cols), count: rows)
        }

        context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))

        let cx = Double(cols) / 2.0
        let cy = Double(rows) / 2.0
        let radius = Double(min(cols, rows)) / 2.0

        var result: [[String?]] = []
        for row in 0..<rows {
            var rowColors: [String?] = []
            for col in 0..<cols {
                // For circle layout, exclude corners
                if layout == .circle {
                    let dx = Double(col) + 0.5 - cx
                    let dy = Double(row) + 0.5 - cy
                    if (dx * dx + dy * dy) > (radius * radius) {
                        rowColors.append(nil)
                        continue
                    }
                }

                let pixelIndex = (row * width + col) * bytesPerPixel
                let r = Double(rawData[pixelIndex]) / 255.0
                let g = Double(rawData[pixelIndex + 1]) / 255.0
                let b = Double(rawData[pixelIndex + 2]) / 255.0
                let a = Double(rawData[pixelIndex + 3]) / 255.0

                // Transparent pixels = empty bead
                if a < 0.2 {
                    rowColors.append(nil)
                } else {
                    // Un-premultiply alpha for accurate color matching
                    let ra = a > 0 ? r / a : r
                    let ga = a > 0 ? g / a : g
                    let ba = a > 0 ? b / a : b
                    let nearest = quantizer.nearestColor(r: min(ra, 1), g: min(ga, 1), b: min(ba, 1))
                    rowColors.append(nearest.id)
                }
            }
            result.append(rowColors)
        }
        return result
    }

    // Generate a PDF-ready UIImage of the pattern for printing
    func renderPatternImage(pattern: BeadPattern, beadPixelSize: CGFloat = 20) -> UIImage {
        let rows = pattern.rows
        let cols = pattern.cols
        let size = CGSize(
            width: CGFloat(cols) * beadPixelSize,
            height: CGFloat(rows) * beadPixelSize
        )

        UIGraphicsBeginImageContextWithOptions(size, true, 1)
        defer { UIGraphicsEndImageContext() }

        guard let ctx = UIGraphicsGetCurrentContext() else { return UIImage() }

        // Background
        UIColor.white.setFill()
        ctx.fill(CGRect(origin: .zero, size: size))

        for row in 0..<rows {
            for col in 0..<cols {
                let x = CGFloat(col) * beadPixelSize
                let y = CGFloat(row) * beadPixelSize
                let beadRect = CGRect(x: x, y: y, width: beadPixelSize, height: beadPixelSize)

                if let color = pattern.color(row: row, col: col) {
                    let inset: CGFloat = beadPixelSize * 0.05
                    let ovalRect = beadRect.insetBy(dx: inset, dy: inset)
                    color.uiColor.setFill()
                    ctx.fillEllipse(in: ovalRect)
                    UIColor.black.withAlphaComponent(0.15).setStroke()
                    ctx.setLineWidth(0.5)
                    ctx.strokeEllipse(in: ovalRect)
                } else if !pattern.isInsideCircle(row: row, col: col) {
                    // Outside circle: dimmed
                } else {
                    // Empty bead slot
                    UIColor(white: 0.93, alpha: 1).setFill()
                    let inset: CGFloat = beadPixelSize * 0.1
                    ctx.fillEllipse(in: beadRect.insetBy(dx: inset, dy: inset))
                }
            }
        }

        // Grid lines
        UIColor.black.withAlphaComponent(0.08).setStroke()
        ctx.setLineWidth(0.3)
        for row in 0...rows {
            let y = CGFloat(row) * beadPixelSize
            ctx.move(to: CGPoint(x: 0, y: y))
            ctx.addLine(to: CGPoint(x: size.width, y: y))
        }
        for col in 0...cols {
            let x = CGFloat(col) * beadPixelSize
            ctx.move(to: CGPoint(x: x, y: 0))
            ctx.addLine(to: CGPoint(x: x, y: size.height))
        }
        ctx.strokePath()

        return UIGraphicsGetImageFromCurrentImageContext() ?? UIImage()
    }
}
