@file:Suppress("unused", "UNUSED_PARAMETER")
package android.graphics

import java.io.OutputStream

class Bitmap private constructor(val width: Int, val height: Int, val px: IntArray) {
    enum class Config { ARGB_8888, RGB_565 }
    enum class CompressFormat { PNG, JPEG }
    var config: Config? = Config.ARGB_8888
    var isRecycled: Boolean = false; private set
    val isMutable: Boolean = true
    fun recycle() { isRecycled = true }
    fun copy(config: Config, mutable: Boolean): Bitmap? = Bitmap(width, height, px.copyOf())
    fun compress(format: CompressFormat, quality: Int, stream: OutputStream): Boolean = true
    fun getPixels(pixels: IntArray, offset: Int, stride: Int, x: Int, y: Int, w: Int, h: Int) {
        for (r in 0 until h) for (c in 0 until w)
            pixels[offset + r * stride + c] = px[(y + r) * width + (x + c)]
    }
    fun setPixels(pixels: IntArray, offset: Int, stride: Int, x: Int, y: Int, w: Int, h: Int) {
        for (r in 0 until h) for (c in 0 until w)
            px[(y + r) * width + (x + c)] = pixels[offset + r * stride + c]
    }
    companion object {
        @JvmStatic fun createBitmap(w: Int, h: Int, c: Config): Bitmap = Bitmap(w, h, IntArray(w * h))
        @JvmStatic fun createBitmap(pixels: IntArray, w: Int, h: Int, c: Config): Bitmap =
            Bitmap(w, h, pixels.copyOf())
        @JvmStatic fun createBitmap(src: Bitmap, x: Int, y: Int, w: Int, h: Int, m: Matrix?, f: Boolean): Bitmap {
            var cw = w
            var ch = h
            var cur = IntArray(w * h)
            for (r in 0 until h) for (c in 0 until w) cur[r * w + c] = src.px[(y + r) * src.width + (x + c)]
            for (op in m?.ops ?: emptyList()) {
                val out = IntArray(cw * ch)
                when (op) {
                    Matrix.Op.ROT90 -> {
                        // clockwise: out(x', y') = in(y', ch - 1 - x')
                        for (yy in 0 until cw) for (xx in 0 until ch)
                            out[yy * ch + xx] = cur[(ch - 1 - xx) * cw + yy]
                        val t = cw; cw = ch; ch = t
                    }
                    Matrix.Op.ROT270 -> {
                        for (yy in 0 until cw) for (xx in 0 until ch)
                            out[yy * ch + xx] = cur[xx * cw + (cw - 1 - yy)]
                        val t = cw; cw = ch; ch = t
                    }
                    Matrix.Op.ROT180 ->
                        for (yy in 0 until ch) for (xx in 0 until cw)
                            out[yy * cw + xx] = cur[(ch - 1 - yy) * cw + (cw - 1 - xx)]
                    Matrix.Op.FLIP_H ->
                        for (yy in 0 until ch) for (xx in 0 until cw)
                            out[yy * cw + xx] = cur[yy * cw + (cw - 1 - xx)]
                    Matrix.Op.FLIP_V ->
                        for (yy in 0 until ch) for (xx in 0 until cw)
                            out[yy * cw + xx] = cur[(ch - 1 - yy) * cw + xx]
                }
                cur = out
            }
            return Bitmap(cw, ch, cur)
        }
        /** Nearest-neighbour is enough: the harness never exercises a real rescale. */
        @JvmStatic fun createScaledBitmap(src: Bitmap, w: Int, h: Int, filter: Boolean): Bitmap {
            val out = IntArray(w * h)
            for (y in 0 until h) { val sy = y * src.height / h
                for (x in 0 until w) out[y * w + x] = src.px[sy * src.width + x * src.width / w] }
            return Bitmap(w, h, out)
        }
    }
}

/**
 * Records its transform instead of ignoring it.
 *
 * The previous no-op version made Bitmap.createBitmap(src, .., m, ..) return a
 * blank bitmap with the ORIGINAL width and height, so a 90-degree EXIF rotation
 * came out with its sides unswapped and the harness could not have noticed. The
 * ops are replayed in order, which is enough for the eight EXIF orientations -
 * this is not a general affine transform.
 */
class Matrix {
    enum class Op { ROT90, ROT180, ROT270, FLIP_H, FLIP_V }
    val ops = mutableListOf<Op>()
    fun postRotate(d: Float) {
        when (((d % 360f) + 360f) % 360f) {
            90f -> ops += Op.ROT90
            180f -> ops += Op.ROT180
            270f -> ops += Op.ROT270
        }
    }
    fun postScale(x: Float, y: Float) {
        if (x < 0) ops += Op.FLIP_H
        if (y < 0) ops += Op.FLIP_V
    }
}

class Rect(var left: Int, var top: Int, var right: Int, var bottom: Int) {
    constructor() : this(0, 0, 0, 0)
    constructor(r: Rect) : this(r.left, r.top, r.right, r.bottom)
    fun width(): Int = right - left
    fun height(): Int = bottom - top
    override fun equals(other: Any?): Boolean = other is Rect &&
        left == other.left && top == other.top && right == other.right && bottom == other.bottom
    override fun hashCode(): Int = (((left * 31) + top) * 31 + right) * 31 + bottom
}

object Color {
    const val WHITE = -1
    const val BLACK = -16777216
    @JvmStatic fun parseColor(s: String): Int {
        val hex = s.removePrefix("#")
        val v = hex.toLong(16)
        return if (hex.length == 8) v.toInt() else (0xFF000000L or v).toInt()
    }
    @JvmStatic fun red(c: Int): Int = (c shr 16) and 0xFF
    @JvmStatic fun green(c: Int): Int = (c shr 8) and 0xFF
    @JvmStatic fun blue(c: Int): Int = c and 0xFF
    @JvmStatic fun alpha(c: Int): Int = (c ushr 24) and 0xFF
    @JvmStatic fun argb(a: Int, r: Int, g: Int, b: Int): Int = 0
}

class Paint(flags: Int = 0) {
    companion object { const val ANTI_ALIAS_FLAG = 1 }
    enum class Style { FILL, STROKE }
    enum class Align { LEFT, CENTER, RIGHT }
    var color: Int = 0
    var style: Style = Style.FILL
    var strokeWidth: Float = 0f
    var isAntiAlias: Boolean = false
    var textSize: Float = 0f
    var textAlign: Align = Align.LEFT
}

class Canvas(bitmap: Bitmap? = null) {
    fun drawColor(c: Int) {}
    fun drawCircle(cx: Float, cy: Float, r: Float, p: Paint) {}
    fun drawText(t: String, x: Float, y: Float, p: Paint) {}
}

object BitmapFactory {
    class Options { var inJustDecodeBounds = false; var inSampleSize = 1; var outWidth = 0; var outHeight = 0; var inPreferredConfig: Bitmap.Config? = null }

    /**
     * Decodes a deliberately trivial format: two little-endian ints (width,
     * height) followed by width*height ARGB ints. Not a JPEG decoder - it
     * exists so the harness can drive BitmapLoader's control flow.
     *
     * The one contract it models faithfully is the one that matters, and the
     * one whose absence let a shipped bug through: with inJustDecodeBounds set,
     * fill in outWidth/outHeight and RETURN NULL, allocating no pixels. The old
     * stub returned null unconditionally, which made
     *
     *     open()?.use { decodeStream(it, null, bounds) } ?: return null
     *
     * look exactly as correct as the version that works. Returning null only in
     * the bounds case is what gives Decode.kt something to catch.
     */
    @JvmStatic fun decodeStream(s: java.io.InputStream?, r: Rect?, o: Options?): Bitmap? {
        if (s == null) return null
        val bytes = try { s.readBytes() } catch (_: Exception) { return null }
        if (bytes.size < 8) return null
        val bb = java.nio.ByteBuffer.wrap(bytes).order(java.nio.ByteOrder.LITTLE_ENDIAN)
        val w = bb.int
        val h = bb.int
        if (w <= 0 || h <= 0) return null
        o?.outWidth = w
        o?.outHeight = h
        if (o?.inJustDecodeBounds == true) return null
        if (bytes.size < 8 + w * h * 4) return null
        val src = IntArray(w * h)
        bb.asIntBuffer().get(src)
        val sample = (o?.inSampleSize ?: 1).coerceAtLeast(1)
        val ow = w / sample
        val oh = h / sample
        if (ow <= 0 || oh <= 0) return null
        val out = IntArray(ow * oh)
        for (y in 0 until oh) for (x in 0 until ow) out[y * ow + x] = src[(y * sample) * w + (x * sample)]
        return createBitmapFor(ow, oh, out)
    }

    @JvmStatic fun decodeFile(path: String): Bitmap? = null

    private fun createBitmapFor(w: Int, h: Int, px: IntArray): Bitmap =
        Bitmap.createBitmap(px, w, h, Bitmap.Config.ARGB_8888)
}
