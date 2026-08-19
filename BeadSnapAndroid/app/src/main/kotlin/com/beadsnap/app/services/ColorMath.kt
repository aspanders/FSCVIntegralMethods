package com.beadsnap.app.services

import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.exp
import kotlin.math.pow
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Colour science for photo -> bead conversion.
 *
 * The old pipeline compared colours with plain squared-Euclidean distance in
 * CIELAB (dE76), which weights one unit of lightness exactly like one unit of
 * chroma. Against a 55-bead palette that contains nine pure neutrals, that
 * repeatedly scored a grey with the right lightness as "closer" than a bead of
 * the right hue, which is why converted photos came out grey.
 *
 * This uses CIEDE2000 instead, plus an explicit penalty for draining chroma out
 * of a colourful pixel.
 */
object ColorMath {

    /** sRGB component (0..1, gamma encoded) to linear light. */
    fun srgbToLinear(c: Float): Float =
        if (c > 0.04045f) ((c + 0.055f) / 1.055f).toDouble().pow(2.4).toFloat() else c / 12.92f

    /** Linear light (0..1) back to a gamma-encoded sRGB component. */
    fun linearToSrgb(c: Float): Float =
        if (c > 0.0031308f) 1.055f * c.toDouble().pow(1.0 / 2.4).toFloat() - 0.055f else 12.92f * c

    /** Linear-light RGB (0..1) to CIELAB (D65). */
    fun linearRgbToLab(rl: Double, gl: Double, bl: Double): DoubleArray {
        val x = (rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375) / 0.95047
        val y = (rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750) / 1.00000
        val z = (rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041) / 1.08883
        fun f(t: Double) = if (t > 0.008856) t.pow(1.0 / 3.0) else 7.787 * t + 16.0 / 116.0
        val fx = f(x); val fy = f(y); val fz = f(z)
        return doubleArrayOf(116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))
    }

    /** Gamma-encoded sRGB (0..1) to CIELAB. */
    fun srgbToLab(r: Float, g: Float, b: Float): DoubleArray = linearRgbToLab(
        srgbToLinear(r).toDouble(), srgbToLinear(g).toDouble(), srgbToLinear(b).toDouble()
    )

    fun chroma(lab: DoubleArray): Double = sqrt(lab[1] * lab[1] + lab[2] * lab[2])

    /**
     * CIEDE2000 colour difference. Considerably better than dE76 at deciding
     * whether a hue shift or a lightness shift is the lesser evil, which is
     * exactly the judgement every bead assignment makes.
     */
    fun deltaE2000(lab1: DoubleArray, lab2: DoubleArray): Double {
        val l1 = lab1[0]; val a1 = lab1[1]; val b1 = lab1[2]
        val l2 = lab2[0]; val a2 = lab2[1]; val b2 = lab2[2]

        val c1 = sqrt(a1 * a1 + b1 * b1)
        val c2 = sqrt(a2 * a2 + b2 * b2)
        val cBar = (c1 + c2) / 2.0
        val cBar7 = cBar.pow(7)
        val g = 0.5 * (1.0 - sqrt(cBar7 / (cBar7 + 6103515625.0)))   // 25^7

        val a1p = (1.0 + g) * a1
        val a2p = (1.0 + g) * a2
        val c1p = sqrt(a1p * a1p + b1 * b1)
        val c2p = sqrt(a2p * a2p + b2 * b2)

        fun hue(bb: Double, aa: Double): Double {
            if (aa == 0.0 && bb == 0.0) return 0.0
            var h = Math.toDegrees(atan2(bb, aa))
            if (h < 0) h += 360.0
            return h
        }
        val h1p = hue(b1, a1p)
        val h2p = hue(b2, a2p)

        val dLp = l2 - l1
        val dCp = c2p - c1p
        val cProd = c1p * c2p
        val dhp = when {
            cProd == 0.0 -> 0.0
            else -> {
                var d = h2p - h1p
                if (d > 180.0) d -= 360.0 else if (d < -180.0) d += 360.0
                d
            }
        }
        val dHp = 2.0 * sqrt(cProd) * sin(Math.toRadians(dhp / 2.0))

        val lBarP = (l1 + l2) / 2.0
        val cBarP = (c1p + c2p) / 2.0
        val hBarP = when {
            cProd == 0.0 -> h1p + h2p
            abs(h1p - h2p) <= 180.0 -> (h1p + h2p) / 2.0
            h1p + h2p < 360.0 -> (h1p + h2p + 360.0) / 2.0
            else -> (h1p + h2p - 360.0) / 2.0
        }

        val t = 1.0 -
            0.17 * cos(Math.toRadians(hBarP - 30.0)) +
            0.24 * cos(Math.toRadians(2.0 * hBarP)) +
            0.32 * cos(Math.toRadians(3.0 * hBarP + 6.0)) -
            0.20 * cos(Math.toRadians(4.0 * hBarP - 63.0))

        val dTheta = 30.0 * exp(-(((hBarP - 275.0) / 25.0).pow(2)))
        val cBarP7 = cBarP.pow(7)
        val rc = 2.0 * sqrt(cBarP7 / (cBarP7 + 6103515625.0))
        val sl = 1.0 + (0.015 * (lBarP - 50.0).pow(2)) / sqrt(20.0 + (lBarP - 50.0).pow(2))
        val sc = 1.0 + 0.045 * cBarP
        val sh = 1.0 + 0.015 * cBarP * t
        val rt = -sin(Math.toRadians(2.0 * dTheta)) * rc

        val termL = dLp / sl
        val termC = dCp / sc
        val termH = dHp / sh
        return sqrt(termL * termL + termC * termC + termH * termH + rt * termC * termH)
    }

    /**
     * Perceptual distance with a bias against desaturating the image.
     *
     * Even with CIEDE2000, a mid-tone pixel can sit almost equidistant between
     * the correct hue and a neutral of the same lightness. Beads are a flat,
     * saturated medium and readable pattern art wants the hue, so losing chroma
     * costs extra. The penalty is proportional to how much chroma the candidate
     * throws away, and is zero when the source pixel is genuinely neutral.
     *
     * 0.45 is a deliberately conservative starting point: enough to break ties
     * away from grey without oversaturating. It is a taste knob, not a derived
     * constant, so tune it against real conversions if greys still creep in.
     */
    fun beadDistance(src: DoubleArray, candidate: DoubleArray, chromaWeight: Double = 0.45): Double {
        val base = deltaE2000(src, candidate)
        val cs = chroma(src)
        val cc = chroma(candidate)
        val lost = (cs - cc).coerceAtLeast(0.0)     // only penalise losing chroma
        return base + chromaWeight * lost * (cs / (cs + 12.0))
    }
}
