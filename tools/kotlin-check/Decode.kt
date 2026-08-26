import android.graphics.Bitmap
import androidx.exifinterface.media.ExifInterface
import com.beadsnap.app.services.BitmapLoader
import java.io.ByteArrayInputStream
import java.io.InputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Drives BitmapLoader against the android.graphics stubs.
 *
 * This exists because BitmapLoader was compiled by the harness but never CALLED
 * by it, and shipped a bug that failed on every photo: the bounds pass was
 * written as
 *
 *     open()?.use { BitmapFactory.decodeStream(it, null, bounds) } ?: return null
 *
 * which asks "did the bounds pass return a bitmap?" - and with
 * inJustDecodeBounds set the answer is always no. Compiling a file proves
 * nothing about whether it works.
 */

private var failures = 0

private fun check(name: String, ok: Boolean, detail: String = "") {
    println("  ${if (ok) "PASS" else "FAIL"}  $name${if (ok || detail.isEmpty()) "" else " - $detail"}")
    if (!ok) failures++
}

/** An image in the stub decoder's format: w, h, then w*h ARGB ints. */
private fun image(w: Int, h: Int): ByteArray {
    val bb = ByteBuffer.allocate(8 + w * h * 4).order(ByteOrder.LITTLE_ENDIAN)
    bb.putInt(w); bb.putInt(h)
    for (y in 0 until h) for (x in 0 until w) bb.putInt(0xFF000000.toInt() or (x * 7 + y * 13))
    return bb.array()
}

private fun opener(bytes: ByteArray): () -> InputStream? = { ByteArrayInputStream(bytes) }

fun main() {
    println("==> BitmapLoader.decodeSampled")

    // The regression. Against the old code every one of these is null.
    val small = BitmapLoader.decodeSampled(opener(image(40, 30)), 1024)
    check("a decodable image decodes", small != null)
    check("an image already under the limit is not resampled",
        small != null && small.width == 40 && small.height == 30,
        "got ${small?.width}x${small?.height}, wanted 40x30")

    val big = BitmapLoader.decodeSampled(opener(image(4000, 3000)), 1024)
    check("an oversized image decodes", big != null)
    check("BOTH sides end up within maxDim",
        big != null && big.width <= 1024 && big.height <= 1024,
        "got ${big?.width}x${big?.height}, limit 1024")
    check("it is not shrunk further than it has to be",
        big != null && (big.width > 512 || big.height > 512),
        "got ${big?.width}x${big?.height} - over-sampled")

    check("a stream that will not open gives null",
        BitmapLoader.decodeSampled({ null }, 1024) == null)
    check("an empty stream gives null",
        BitmapLoader.decodeSampled(opener(ByteArray(0)), 1024) == null)
    check("a header claiming zero size gives null",
        BitmapLoader.decodeSampled(opener(ByteBuffer.allocate(8)
            .order(ByteOrder.LITTLE_ENDIAN).putInt(0).putInt(0).array()), 1024) == null)

    println("==> BitmapLoader.readOrientation")
    check("an unreadable stream reports NORMAL rather than throwing",
        BitmapLoader.readOrientation { null } == ExifInterface.ORIENTATION_NORMAL)

    println("==> BitmapLoader.applyOrientation")
    val src = Bitmap.createBitmap(IntArray(40 * 30) { it }, 40, 30, Bitmap.Config.ARGB_8888)
    val same = BitmapLoader.applyOrientation(src, ExifInterface.ORIENTATION_NORMAL)
    check("NORMAL returns the very same bitmap", same === src)
    check("NORMAL does not recycle it", !src.isRecycled)

    val turned = BitmapLoader.applyOrientation(
        Bitmap.createBitmap(IntArray(40 * 30) { it }, 40, 30, Bitmap.Config.ARGB_8888),
        ExifInterface.ORIENTATION_ROTATE_90)
    check("ROTATE_90 swaps the sides",
        turned.width == 30 && turned.height == 40,
        "got ${turned.width}x${turned.height}, wanted 30x40")

    val flipped = BitmapLoader.applyOrientation(
        Bitmap.createBitmap(IntArray(40 * 30) { it }, 40, 30, Bitmap.Config.ARGB_8888),
        ExifInterface.ORIENTATION_ROTATE_180)
    check("ROTATE_180 keeps the sides",
        flipped.width == 40 && flipped.height == 30,
        "got ${flipped.width}x${flipped.height}")

    val orig = Bitmap.createBitmap(IntArray(40 * 30) { it }, 40, 30, Bitmap.Config.ARGB_8888)
    BitmapLoader.applyOrientation(orig, ExifInterface.ORIENTATION_ROTATE_90)
    check("the original is recycled once it has been replaced", orig.isRecycled)

    println(if (failures == 0) "BitmapLoader checks pass" else "$failures FAILED")
    if (failures > 0) kotlin.system.exitProcess(1)
}
