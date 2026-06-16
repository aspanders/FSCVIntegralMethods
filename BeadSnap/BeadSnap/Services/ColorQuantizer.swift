import UIKit

final class ColorQuantizer {
    static let shared = ColorQuantizer()

    private let palette = BeadColor.palette

    // Pre-compute LAB values for the full palette
    private lazy var paletteLAB: [(l: Double, a: Double, b: Double)] = {
        palette.map { $0.lab }
    }()

    private init() {}

    func nearestColor(r: Double, g: Double, b: Double) -> BeadColor {
        let lab = BeadColor.rgbToLAB(r: r, g: g, b: b)
        var bestDist = Double.infinity
        var bestIdx = 0
        for (i, pLAB) in paletteLAB.enumerated() {
            let dl = lab.l - pLAB.l
            let da = lab.a - pLAB.a
            let db = lab.b - pLAB.b
            let dist = dl * dl + da * da + db * db
            if dist < bestDist {
                bestDist = dist
                bestIdx = i
            }
        }
        return palette[bestIdx]
    }

    func nearestColor(uiColor: UIColor) -> BeadColor {
        var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
        uiColor.getRed(&r, green: &g, blue: &b, alpha: &a)
        return nearestColor(r: Double(r), g: Double(g), b: Double(b))
    }
}
