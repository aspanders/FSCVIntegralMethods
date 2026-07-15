package com.beadsnap.app.services

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.segmentation.subject.SubjectSegmentation
import com.google.mlkit.vision.segmentation.subject.SubjectSegmenterOptions
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume
import kotlin.math.roundToInt

/**
 * Pure mask state — true = keep (foreground). Kept free of android.graphics
 * so the brush math is unit-testable.
 */
class MaskModel(val width: Int, val height: Int) {
    val keep = BooleanArray(width * height) { true }

    fun setAll(values: BooleanArray) {
        require(values.size == keep.size)
        values.copyInto(keep)
    }

    /** Paint a filled circle of `keepValue` into the mask, clipped to bounds. */
    fun brush(cx: Int, cy: Int, radius: Int, keepValue: Boolean) {
        val r2 = radius * radius
        val x0 = (cx - radius).coerceAtLeast(0)
        val x1 = (cx + radius).coerceAtMost(width - 1)
        val y0 = (cy - radius).coerceAtLeast(0)
        val y1 = (cy + radius).coerceAtMost(height - 1)
        for (y in y0..y1) {
            for (x in x0..x1) {
                val dx = x - cx
                val dy = y - cy
                if (dx * dx + dy * dy <= r2) keep[y * width + x] = keepValue
            }
        }
    }
}

object BackgroundRemover {

    const val WORK_MAX_DIM = 512

    /** Decode a content URI to a working bitmap no larger than WORK_MAX_DIM. */
    fun decodeWorkBitmap(open: () -> java.io.InputStream?): Bitmap? {
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        open()?.use { BitmapFactory.decodeStream(it, null, bounds) } ?: return null
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0) return null
        var sample = 1
        while (bounds.outWidth / (sample * 2) >= WORK_MAX_DIM ||
               bounds.outHeight / (sample * 2) >= WORK_MAX_DIM) {
            sample *= 2
        }
        val opts = BitmapFactory.Options().apply { inSampleSize = sample }
        return open()?.use { BitmapFactory.decodeStream(it, null, opts) }
    }

    /**
     * On-device subject segmentation via ML Kit. Returns a keep-mask sized
     * bitmap.width × bitmap.height, or null when the model is unavailable
     * (the caller falls back to keep-everything + manual brushing).
     */
    suspend fun subjectMask(bitmap: Bitmap): BooleanArray? =
        suspendCancellableCoroutine { cont ->
            val segmenter = try {
                SubjectSegmentation.getClient(
                    SubjectSegmenterOptions.Builder()
                        .enableForegroundConfidenceMask()
                        .build()
                )
            } catch (_: Exception) {
                cont.resume(null); return@suspendCancellableCoroutine
            }
            segmenter.process(InputImage.fromBitmap(bitmap, 0))
                .addOnSuccessListener { result ->
                    val maskBuf = result.foregroundConfidenceMask
                    if (maskBuf == null) {
                        cont.resume(null)
                    } else {
                        val arr = BooleanArray(bitmap.width * bitmap.height)
                        maskBuf.rewind()
                        for (i in arr.indices) arr[i] = maskBuf.get() > 0.5f
                        cont.resume(arr)
                    }
                    segmenter.close()
                }
                .addOnFailureListener {
                    segmenter.close()
                    cont.resume(null)
                }
        }

    /** Preview composite: background pixels faded to `fadeAlpha` (0..1). */
    fun composite(src: Bitmap, mask: MaskModel, fadeAlpha: Float): Bitmap {
        val w = src.width
        val h = src.height
        val pixels = IntArray(w * h)
        src.getPixels(pixels, 0, w, 0, 0, w, h)
        val fade = (fadeAlpha * 255).roundToInt().coerceIn(0, 255)
        for (i in pixels.indices) {
            if (!mask.keep[i]) {
                val p = pixels[i]
                val a = (Color.alpha(p) * fade) / 255
                pixels[i] = Color.argb(a, Color.red(p), Color.green(p), Color.blue(p))
            }
        }
        return Bitmap.createBitmap(pixels, w, h, Bitmap.Config.ARGB_8888)
    }

    /** Final image for conversion: background fully transparent. */
    fun maskedForConversion(src: Bitmap, mask: MaskModel): Bitmap =
        composite(src, mask, fadeAlpha = 0f)
}
