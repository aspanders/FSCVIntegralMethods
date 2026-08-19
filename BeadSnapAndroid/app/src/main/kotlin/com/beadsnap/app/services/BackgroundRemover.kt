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
}
