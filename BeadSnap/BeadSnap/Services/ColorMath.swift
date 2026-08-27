import Foundation

/// Colour science for photo -> bead conversion.
///
/// A direct port of the Android `ColorMath.kt`, kept line-for-line comparable on
/// purpose: the two platforms must pick the same bead for the same pixel, or the
/// same photo produces two different patterns. `tools/kotlin-check/parity.py`
/// compares the numeric constants in the two files and fails the harness if they
/// drift apart.
///
/// The old iOS pipeline compared colours with plain squared-Euclidean distance in
/// CIELAB (dE76), which weights one unit of lightness exactly like one unit of
/// chroma. Against a 55-bead palette containing nine pure neutrals, that
/// repeatedly scored a grey of the right lightness as "closer" than a bead of the
/// right hue - which is why converted photos came out grey. This uses CIEDE2000,
/// plus an explicit penalty for draining chroma out of a colourful pixel.
enum ColorMath {

    /// sRGB component (0..1, gamma encoded) to linear light.
    static func srgbToLinear(_ c: Double) -> Double {
        c > 0.04045 ? pow((c + 0.055) / 1.055, 2.4) : c / 12.92
    }

    /// Linear light (0..1) back to a gamma-encoded sRGB component.
    static func linearToSrgb(_ c: Double) -> Double {
        c > 0.0031308 ? 1.055 * pow(c, 1.0 / 2.4) - 0.055 : 12.92 * c
    }

    /// Linear-light RGB (0..1) to CIELAB (D65).
    static func linearRgbToLab(_ rl: Double, _ gl: Double, _ bl: Double) -> (Double, Double, Double) {
        let x = (rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375) / 0.95047
        let y = (rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750) / 1.00000
        let z = (rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041) / 1.08883
        func f(_ t: Double) -> Double {
            t > 0.008856 ? pow(t, 1.0 / 3.0) : 7.787 * t + 16.0 / 116.0
        }
        let fx = f(x), fy = f(y), fz = f(z)
        return (116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))
    }

    /// Gamma-encoded sRGB (0..1) to CIELAB.
    static func srgbToLab(_ r: Double, _ g: Double, _ b: Double) -> (Double, Double, Double) {
        linearRgbToLab(srgbToLinear(r), srgbToLinear(g), srgbToLinear(b))
    }

    static func chroma(_ lab: (Double, Double, Double)) -> Double {
        (lab.1 * lab.1 + lab.2 * lab.2).squareRoot()
    }

    /// CIEDE2000 colour difference. Considerably better than dE76 at deciding
    /// whether a hue shift or a lightness shift is the lesser evil, which is
    /// exactly the judgement every bead assignment makes.
    static func deltaE2000(_ lab1: (Double, Double, Double), _ lab2: (Double, Double, Double)) -> Double {
        let l1 = lab1.0, a1 = lab1.1, b1 = lab1.2
        let l2 = lab2.0, a2 = lab2.1, b2 = lab2.2

        let c1 = (a1 * a1 + b1 * b1).squareRoot()
        let c2 = (a2 * a2 + b2 * b2).squareRoot()
        let cBar = (c1 + c2) / 2.0
        let cBar7 = pow(cBar, 7)
        let g = 0.5 * (1.0 - (cBar7 / (cBar7 + 6103515625.0)).squareRoot())   // 25^7

        let a1p = (1.0 + g) * a1
        let a2p = (1.0 + g) * a2
        let c1p = (a1p * a1p + b1 * b1).squareRoot()
        let c2p = (a2p * a2p + b2 * b2).squareRoot()

        func hue(_ bb: Double, _ aa: Double) -> Double {
            if aa == 0.0 && bb == 0.0 { return 0.0 }
            var h = atan2(bb, aa) * 180.0 / Double.pi
            if h < 0 { h += 360.0 }
            return h
        }
        let h1p = hue(b1, a1p)
        let h2p = hue(b2, a2p)

        let dLp = l2 - l1
        let dCp = c2p - c1p
        let cProd = c1p * c2p
        var dhp = 0.0
        if cProd != 0.0 {
            var d = h2p - h1p
            if d > 180.0 { d -= 360.0 } else if d < -180.0 { d += 360.0 }
            dhp = d
        }
        let dHp = 2.0 * cProd.squareRoot() * sin(dhp / 2.0 * Double.pi / 180.0)

        let lBarP = (l1 + l2) / 2.0
        let cBarP = (c1p + c2p) / 2.0
        let hBarP: Double
        if cProd == 0.0 {
            hBarP = h1p + h2p
        } else if abs(h1p - h2p) <= 180.0 {
            hBarP = (h1p + h2p) / 2.0
        } else if h1p + h2p < 360.0 {
            hBarP = (h1p + h2p + 360.0) / 2.0
        } else {
            hBarP = (h1p + h2p - 360.0) / 2.0
        }

        func rad(_ deg: Double) -> Double { deg * Double.pi / 180.0 }

        let t = 1.0
            - 0.17 * cos(rad(hBarP - 30.0))
            + 0.24 * cos(rad(2.0 * hBarP))
            + 0.32 * cos(rad(3.0 * hBarP + 6.0))
            - 0.20 * cos(rad(4.0 * hBarP - 63.0))

        let dTheta = 30.0 * exp(-pow((hBarP - 275.0) / 25.0, 2))
        let cBarP7 = pow(cBarP, 7)
        let rc = 2.0 * (cBarP7 / (cBarP7 + 6103515625.0)).squareRoot()
        let sl = 1.0 + (0.015 * pow(lBarP - 50.0, 2)) / (20.0 + pow(lBarP - 50.0, 2)).squareRoot()
        let sc = 1.0 + 0.045 * cBarP
        let sh = 1.0 + 0.015 * cBarP * t
        let rt = -sin(rad(2.0 * dTheta)) * rc

        let termL = dLp / sl
        let termC = dCp / sc
        let termH = dHp / sh
        return (termL * termL + termC * termC + termH * termH + rt * termC * termH).squareRoot()
    }

    /// Perceptual distance with a bias against desaturating the image.
    ///
    /// Even with CIEDE2000, a mid-tone pixel can sit almost equidistant between
    /// the correct hue and a neutral of the same lightness. Beads are a flat,
    /// saturated medium and readable pattern art wants the hue, so losing chroma
    /// costs extra. The penalty is proportional to how much chroma the candidate
    /// throws away, and is zero when the source pixel is genuinely neutral.
    ///
    /// 0.45 is a deliberately conservative starting point: enough to break ties
    /// away from grey without oversaturating. It is a taste knob, not a derived
    /// constant.
    static func beadDistance(_ src: (Double, Double, Double),
                             _ candidate: (Double, Double, Double),
                             chromaWeight: Double = 0.45) -> Double {
        let base = deltaE2000(src, candidate)
        let cs = chroma(src)
        let cc = chroma(candidate)
        let lost = max(cs - cc, 0.0)     // only penalise losing chroma
        return base + chromaWeight * lost * (cs / (cs + 12.0))
    }

    // MARK: - Edge-aware cell resolution

    /// How far apart the two halves of a cell must be before the cell is treated
    /// as straddling an edge rather than as one shaded surface. dE2000 20 is
    /// several times the just-noticeable difference, so only genuine boundaries
    /// qualify.
    static let edgeSnapDE = 20.0

    /// Below this spread in relative luminance a cell cannot be straddling
    /// anything, and the split is skipped outright.
    static let edgeMinLumaRange = 0.02

    /// Rec.709 relative luminance of a LINEAR-light RGB triple.
    static func luma(_ r: Double, _ g: Double, _ b: Double) -> Double {
        0.2126 * r + 0.7152 * g + 0.0722 * b
    }

    /// The colour of one bead, given the mean of all its pixels and the means of
    /// its darker and lighter halves (split at the cell's own mean luminance).
    /// All values are LINEAR light.
    ///
    /// Plain averaging is right for a shaded surface and wrong at a boundary. A
    /// cell covering 60% yellow muzzle and 40% black nose averages to a muddy
    /// brown that belongs to neither, and on the test photo that is literally how
    /// the nose went missing: the boundary cells blended away, and with no
    /// strongly dark cells left, Black never earned a place in the palette at
    /// all. Beads are a flat, posterised medium - at a real edge the honest
    /// answer is the side that covers more of the bead, not the average of both.
    static func resolveCell(
        meanR: Double, meanG: Double, meanB: Double,
        darkR: Double, darkG: Double, darkB: Double, darkW: Double,
        liteR: Double, liteG: Double, liteB: Double, liteW: Double
    ) -> (Double, Double, Double) {
        if darkW <= 0.0 || liteW <= 0.0 {
            return (meanR, meanG, meanB)
        }
        let dr = darkR / darkW, dg = darkG / darkW, db = darkB / darkW
        let lr = liteR / liteW, lg = liteG / liteW, lb = liteB / liteW
        let labDark = linearRgbToLab(min(max(dr, 0.0), 1.0), min(max(dg, 0.0), 1.0), min(max(db, 0.0), 1.0))
        let labLite = linearRgbToLab(min(max(lr, 0.0), 1.0), min(max(lg, 0.0), 1.0), min(max(lb, 0.0), 1.0))
        if deltaE2000(labDark, labLite) < edgeSnapDE {
            return (meanR, meanG, meanB)
        }
        return darkW >= liteW ? (dr, dg, db) : (lr, lg, lb)
    }
}
