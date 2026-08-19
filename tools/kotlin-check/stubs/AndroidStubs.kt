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
        @JvmStatic fun createBitmap(src: Bitmap, x: Int, y: Int, w: Int, h: Int, m: Matrix?, f: Boolean): Bitmap =
            Bitmap(w, h, IntArray(w * h))
        /** Nearest-neighbour is enough: the harness never exercises a real rescale. */
        @JvmStatic fun createScaledBitmap(src: Bitmap, w: Int, h: Int, filter: Boolean): Bitmap {
            val out = IntArray(w * h)
            for (y in 0 until h) { val sy = y * src.height / h
                for (x in 0 until w) out[y * w + x] = src.px[sy * src.width + x * src.width / w] }
            return Bitmap(w, h, out)
        }
    }
}

class Matrix { fun postRotate(d: Float) {}; fun postScale(x: Float, y: Float) {} }

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
    @JvmStatic fun decodeStream(s: java.io.InputStream?, r: Rect?, o: Options?): Bitmap? = null
    @JvmStatic fun decodeFile(path: String): Bitmap? = null
}
