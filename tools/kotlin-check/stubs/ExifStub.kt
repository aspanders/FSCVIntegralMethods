@file:Suppress("unused", "UNUSED_PARAMETER")
package androidx.exifinterface.media

class ExifInterface(stream: java.io.InputStream) {
    fun getAttributeInt(tag: String, default: Int): Int = default
    companion object {
        const val TAG_ORIENTATION = "Orientation"
        const val ORIENTATION_NORMAL = 1
        const val ORIENTATION_FLIP_HORIZONTAL = 2
        const val ORIENTATION_ROTATE_180 = 3
        const val ORIENTATION_FLIP_VERTICAL = 4
        const val ORIENTATION_TRANSPOSE = 5
        const val ORIENTATION_ROTATE_90 = 6
        const val ORIENTATION_TRANSVERSE = 7
        const val ORIENTATION_ROTATE_270 = 8
        const val ORIENTATION_UNDEFINED = 0
    }
}
