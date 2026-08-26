package com.beadsnap.app.services

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.net.Uri
import androidx.exifinterface.media.ExifInterface
import java.io.InputStream

/**
 * Decodes image URIs into upright, memory-safe bitmaps.
 *
 * Every previous decode path called BitmapFactory.decodeStream directly, which
 * ignores EXIF entirely. Phone cameras almost always write the sensor buffer in
 * its native landscape orientation and record the real orientation in the EXIF
 * tag, so a portrait photo decoded naively comes out rotated 90 degrees. That
 * one omission was behind both the sideways photos and the background remover
 * being handed an image the segmenter could not make sense of.
 *
 * Decoding also downsamples to a bounded size. A modern phone photo is well
 * over 50 MB as an ARGB_8888 bitmap, which is a real OOM risk when it is held
 * in Compose state across a configuration change.
 */
object BitmapLoader {

    /** Plenty of detail for area-averaging down to a <=48 cell grid, ~4 MB decoded. */
    const val CONVERT_MAX_DIM = 1024

    /**
     * Decode [uri] to an upright bitmap whose longest edge is at most [maxDim].
     * Returns null if the image cannot be read or decoded.
     */
    fun decodeUpright(context: Context, uri: Uri, maxDim: Int = CONVERT_MAX_DIM): Bitmap? {
        val open = { context.contentResolver.openInputStream(uri) }
        val decoded = decodeSampled(open, maxDim) ?: return null
        val orientation = readOrientation(open)
        return applyOrientation(decoded, orientation)
    }

    /** Decode with inSampleSize so the result is no larger than [maxDim] per side. */
    fun decodeSampled(open: () -> InputStream?, maxDim: Int): Bitmap? {
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        // The bounds pass is run for its SIDE EFFECT on `bounds`. With
        // inJustDecodeBounds set, decodeStream returns null by contract - it
        // reads the header and fills in outWidth/outHeight without allocating
        // any pixels. An earlier version wrote
        //
        //     open()?.use { BitmapFactory.decodeStream(it, null, bounds) } ?: return null
        //
        // meaning to ask "did the stream open?", but `use` returns the lambda's
        // value, so what it actually asked was "did the bounds pass return a
        // bitmap?" - which is never. Every photo failed to decode, on both the
        // camera and the gallery path. Open the stream first, and let the
        // outWidth check below be the thing that decides.
        val header = open() ?: return null
        header.use { BitmapFactory.decodeStream(it, null, bounds) }
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0) return null

        // Halve until BOTH sides are within maxDim. The previous condition
        // compared outWidth / (sample * 2), which stops one halving early and
        // leaves an image up to twice maxDim per side - four times the pixels,
        // and four times the ~4 MB this is documented to produce.
        var sample = 1
        while (bounds.outWidth / sample > maxDim || bounds.outHeight / sample > maxDim) {
            sample *= 2
        }
        val opts = BitmapFactory.Options().apply {
            inSampleSize = sample
            inPreferredConfig = Bitmap.Config.ARGB_8888
        }
        return open()?.use { BitmapFactory.decodeStream(it, null, opts) }
    }

    /** EXIF orientation tag, or ORIENTATION_NORMAL when absent/unreadable. */
    fun readOrientation(open: () -> InputStream?): Int = try {
        open()?.use { ExifInterface(it).getAttributeInt(
            ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL
        ) } ?: ExifInterface.ORIENTATION_NORMAL
    } catch (_: Exception) {
        ExifInterface.ORIENTATION_NORMAL
    }

    /**
     * Rotate/flip [src] so it displays the way it was actually shot. Returns
     * [src] untouched when no transform is needed, and recycles the original
     * only when it has genuinely been replaced.
     */
    fun applyOrientation(src: Bitmap, orientation: Int): Bitmap {
        val m = Matrix()
        when (orientation) {
            ExifInterface.ORIENTATION_ROTATE_90 -> m.postRotate(90f)
            ExifInterface.ORIENTATION_ROTATE_180 -> m.postRotate(180f)
            ExifInterface.ORIENTATION_ROTATE_270 -> m.postRotate(270f)
            ExifInterface.ORIENTATION_FLIP_HORIZONTAL -> m.postScale(-1f, 1f)
            ExifInterface.ORIENTATION_FLIP_VERTICAL -> m.postScale(1f, -1f)
            ExifInterface.ORIENTATION_TRANSPOSE -> { m.postRotate(90f); m.postScale(-1f, 1f) }
            ExifInterface.ORIENTATION_TRANSVERSE -> { m.postRotate(270f); m.postScale(-1f, 1f) }
            else -> return src
        }
        return try {
            val out = Bitmap.createBitmap(src, 0, 0, src.width, src.height, m, true)
            if (out != src) src.recycle()
            out
        } catch (_: OutOfMemoryError) {
            src   // better to show it sideways than to crash
        }
    }
}
