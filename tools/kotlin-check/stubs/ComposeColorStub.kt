@file:Suppress("unused", "UNUSED_PARAMETER")
package androidx.compose.ui.graphics

@JvmInline
value class Color(val value: Long) {
    constructor(argb: Int) : this(argb.toLong())
    fun copy(alpha: Float = 0f, red: Float = 0f, green: Float = 0f, blue: Float = 0f): Color = this
    companion object {
        val White = Color(0xFFFFFFFFL)
        val Black = Color(0xFF000000L)
    }
}

fun Color.luminance(): Float = 0.5f
fun Color.toArgb(): Int = value.toInt()
