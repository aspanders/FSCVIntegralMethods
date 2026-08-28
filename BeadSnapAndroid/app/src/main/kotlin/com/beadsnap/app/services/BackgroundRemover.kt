package com.beadsnap.app.services

import android.graphics.Bitmap
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.segmentation.subject.SubjectSegmentation
import com.google.mlkit.vision.segmentation.subject.SubjectSegmenterOptions
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume

/**
 * On-device subject segmentation.
 *
 * This is only ever the STARTING point for a cut-out. Everything that follows -
 * the touch-up brush, the preview compositing, the mask itself - lives in
 * PhotoStudio, so a segmenter that is unavailable or simply wrong costs the
 * user a few brush strokes rather than the whole feature.
 */
object BackgroundRemover {

    /**
     * Returns a keep-mask sized bitmap.width x bitmap.height, or null when the
     * model is unavailable (the caller falls back to keep-everything and manual
     * brushing).
     *
     * The bitmap is handed over with rotationDegrees 0, so it must already be
     * upright: a sideways image means the segmenter is looking for an upright
     * subject in a rotated frame.
     */
    suspend fun subjectMask(bitmap: Bitmap): BooleanArray? =
        suspendCancellableCoroutine { cont ->
            val segmenter = try {
                SubjectSegmentation.getClient(
                    SubjectSegmenterOptions.Builder()
                        .enableForegroundConfidenceMask()
                        .build()
                )
            } catch (_: Throwable) {
                cont.resume(null); return@suspendCancellableCoroutine
            }
            // Nothing else closes it if the caller walks away before either
            // listener fires - navigating back out of the tune screen does
            // exactly that - and a segmenter left open holds its model.
            cont.invokeOnCancellation { runCatching { segmenter.close() } }

            // Every path below has to resume EXACTLY once. A throw inside a
            // Play Services listener does not reach the caller and does not
            // trigger the other listener: it is handed to the executor and
            // logged, and the continuation is simply never resumed - so
            // background removal would sit there spinning for the life of the
            // process. Both listeners therefore close and resume inside a
            // guard, and reading the mask is wrapped rather than trusted.
            fun finish(value: BooleanArray?) {
                runCatching { segmenter.close() }
                if (cont.isActive) cont.resume(value)
            }

            val task = try {
                segmenter.process(InputImage.fromBitmap(bitmap, 0))
            } catch (_: Throwable) {
                // fromBitmap rejects a recycled bitmap by throwing.
                finish(null); return@suspendCancellableCoroutine
            }
            task
                .addOnSuccessListener { result ->
                    val arr = try {
                        val maskBuf = result.foregroundConfidenceMask
                        val n = bitmap.width * bitmap.height
                        maskBuf?.rewind()
                        // A mask that is not the size of the image cannot be
                        // read into it. Falling back to keep-everything costs
                        // the user some brushwork; reading it anyway would
                        // leave the tail false - "remove all of this" - and
                        // blank most of their photo.
                        if (maskBuf == null || maskBuf.remaining() < n) {
                            null
                        } else {
                            BooleanArray(n) { maskBuf.get() > 0.5f }
                        }
                    } catch (_: Throwable) {
                        null
                    }
                    finish(arr)
                }
                .addOnFailureListener { finish(null) }
        }
}
