package com.beadsnap.app.services

import android.graphics.Bitmap
import android.graphics.Rect
import com.beadsnap.app.data.model.Cell
import com.beadsnap.app.data.model.CreatorType
import com.beadsnap.app.data.model.Difficulty
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.model.GridSize
import com.beadsnap.app.data.model.PatternCategory
import com.beadsnap.app.data.model.PegboardShape
import java.util.UUID
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt
import kotlin.math.sqrt

/**
 * The live photo-to-beads workspace: one photo, one keep-mask, and the bead
 * pattern they currently produce, kept in a form that can be re-derived fast
 * enough to redraw while a finger is moving.
 *
 * Three things make that possible.
 *
 * 1. **A small working buffer.** The photo is resampled once to at most
 *    [WORK_MAX_DIM] and kept as linear-light floats. At 384px a 48x48 board
 *    still averages ~8x8 source pixels per bead; measured against sampling the
 *    full 1024px image, mean error is dE2000 0.80 with p95 3.13 - below or
 *    around the just-noticeable difference, and only at region edges. The
 *    committed pattern is re-derived from the full-resolution photo anyway
 *    (see [finalOptions]), so this approximation never ships in a saved
 *    pattern.
 *
 * 2. **Cached per-cell distance rows.** The expensive part of a conversion is
 *    CIEDE2000 from every cell to every bead. Those rows are kept and only
 *    recomputed for cells the brush actually touched, so a stroke costs work
 *    proportional to the brush, not to the board.
 *
 * 3. **Snapshotted white balance.** [measureGreyWorld] samples the kept pixels
 *    once, on demand. Recomputing it continuously would make every brush
 *    stroke shift the colour of the whole image - both bad to look at and fatal
 *    to the incremental cache above.
 */
class PhotoStudio private constructor(
    val width: Int,
    val height: Int,
    /** Linear-light RGB, 3 floats per pixel, row-major. */
    private val lin: FloatArray,
    /** The source bitmap's own alpha, 0..1 - already-transparent input stays out. */
    private val srcAlpha: FloatArray,
    /**
     * The photo's original ARGB pixels.
     *
     * Kept alongside the linear copy purely so the preview costs nothing: the
     * pixels never change, only which of them are masked, so re-encoding
     * linear light back to sRGB every frame was ~330k pow() calls for an
     * image that had not moved. Now a preview frame is one blend per pixel.
     */
    private val srgb: IntArray
) {

    /** true = this pixel becomes beads. */
    val keep = BooleanArray(width * height) { true }

    // ─── Grid state ───────────────────────────────────────────────────────────

    private var cols = 0
    private var rows = 0
    private var crop = Rect(0, 0, width, height)
    private var options = ConvertOptions()
    private var shape = PegboardShape.square

    /** Per-cell distance-to-every-bead rows; null = no bead in that cell. */
    private var dist: Array<DoubleArray?> = emptyArray()
    private var stale: BooleanArray = BooleanArray(0)
    private var everythingStale = true

    // ─── Configuration ────────────────────────────────────────────────────────

    /**
     * Point the studio at a board. Anything that changes a cell's colour -
     * grid size, crop, colour knobs, board shape - invalidates every cell;
     * only the mask is handled incrementally.
     */
    fun configure(
        cols: Int,
        rows: Int,
        crop: Rect?,
        options: ConvertOptions,
        shape: PegboardShape
    ) {
        val newCrop = crop ?: ImageConverter.aspectCrop(width, height, cols, rows)
        val resized = cols != this.cols || rows != this.rows
        val changed = resized || newCrop != this.crop ||
            options != this.options || shape != this.shape
        this.cols = cols
        this.rows = rows
        this.crop = newCrop
        this.options = options
        this.shape = shape
        if (resized) {
            dist = arrayOfNulls(cols * rows)
            stale = BooleanArray(cols * rows) { true }
        }
        if (changed) everythingStale = true
    }

    // ─── Mask editing ─────────────────────────────────────────────────────────

    fun keepAll() {
        java.util.Arrays.fill(keep, true)
        everythingStale = true
    }

    fun clearAll() {
        java.util.Arrays.fill(keep, false)
        everythingStale = true
    }

    /**
     * Adopt an automatic mask of any resolution, nearest-neighbour resampled
     * onto the working buffer. ML Kit runs at its own working size, which is
     * not this one.
     */
    fun adoptMask(mask: BooleanArray, maskW: Int, maskH: Int) {
        if (maskW <= 0 || maskH <= 0 || mask.size != maskW * maskH) return
        for (y in 0 until height) {
            val sy = (y.toLong() * maskH / height).toInt().coerceIn(0, maskH - 1)
            for (x in 0 until width) {
                val sx = (x.toLong() * maskW / width).toInt().coerceIn(0, maskW - 1)
                keep[y * width + x] = mask[sy * maskW + sx]
            }
        }
        everythingStale = true
    }

    /**
     * Paint a circle into the mask. [nx]/[ny] are 0..1 across the photo and
     * [radiusFrac] is a fraction of its longer side, so the caller never has to
     * know the working resolution.
     *
     * Returns true if anything changed, and marks only the cells under the
     * brush for recomputation.
     */
    fun brush(nx: Float, ny: Float, radiusFrac: Float, keepValue: Boolean): Boolean {
        val cx = (nx * width).roundToInt()
        val cy = (ny * height).roundToInt()
        val radius = max(1, (radiusFrac * max(width, height)).roundToInt())
        val x0 = (cx - radius).coerceIn(0, width - 1)
        val x1 = (cx + radius).coerceIn(0, width - 1)
        val y0 = (cy - radius).coerceIn(0, height - 1)
        val y1 = (cy + radius).coerceIn(0, height - 1)
        val r2 = radius.toLong() * radius
        var changed = false
        for (y in y0..y1) {
            val dy = (y - cy).toLong()
            val base = y * width
            for (x in x0..x1) {
                val dx = (x - cx).toLong()
                if (dx * dx + dy * dy > r2) continue
                if (keep[base + x] != keepValue) {
                    keep[base + x] = keepValue
                    changed = true
                }
            }
        }
        if (changed) markStalePixels(x0, y0, x1, y1)
        return changed
    }

    /** Fraction of the photo currently kept - drives the "nothing left" hint. */
    fun keptFraction(): Float {
        var n = 0
        for (k in keep) if (k) n++
        return n.toFloat() / keep.size
    }

    // ─── White balance ────────────────────────────────────────────────────────

    /**
     * Grey-world gains measured over the KEPT pixels only, clamped to a sane
     * range.
     *
     * Measuring over the whole frame is what makes naive auto white balance
     * fail on exactly the photos that need it: on the test photo - a blue toy
     * on a wooden shelf - the full frame gives R 0.63 / G 1.13 / B 1.88,
     * because the wood, not the subject, is setting the average, and applying
     * that turns the wood lavender. Measured over the cut-out subject the same
     * photo gives R 0.74 / G 1.07 / B 1.42, which is the correction that
     * actually puts the blue back.
     *
     * The clamp is the backstop for the case where the user has not removed
     * anything yet, so "kept" still means the whole frame.
     */
    fun measureGreyWorld(): FloatArray {
        var r = 0.0; var g = 0.0; var b = 0.0; var n = 0
        for (i in keep.indices) {
            if (!keep[i] || srcAlpha[i] < 0.5f) continue
            val j = i * 3
            r += lin[j]; g += lin[j + 1]; b += lin[j + 2]
            n++
        }
        if (n == 0 || r <= 0.0 || g <= 0.0 || b <= 0.0) return ConvertOptions.NEUTRAL_GAINS
        r /= n; g /= n; b /= n
        val mean = (r + g + b) / 3.0
        return floatArrayOf(
            (mean / r).coerceIn(GAIN_MIN, GAIN_MAX).toFloat(),
            (mean / g).coerceIn(GAIN_MIN, GAIN_MAX).toFloat(),
            (mean / b).coerceIn(GAIN_MIN, GAIN_MAX).toFloat()
        )
    }

    // ─── Preview of the photo pane ────────────────────────────────────────────

    /**
     * The photo with dropped pixels knocked back to [fade] of their brightness
     * over a light checker, so what will and will not become beads is obvious
     * at a glance without hiding what is underneath the brush.
     */
    fun photoPreview(into: Bitmap? = null, fade: Float = 0.22f): Bitmap {
        val px = IntArray(width * height)
        val f = (fade.coerceIn(0f, 1f) * 256f).roundToInt()
        val inv = 256 - f
        var i = 0
        for (y in 0 until height) {
            val band = (y / CHECKER) and 1
            for (x in 0 until width) {
                val p = srgb[i]
                px[i] = if (keep[i]) {
                    p or (0xFF shl 24)
                } else {
                    // Checkerboard behind the dropped area: a plain fade reads
                    // as the photo simply being dark there.
                    val tile = if ((((x / CHECKER) and 1) xor band) == 0) 230 else 199
                    val r = (((p shr 16) and 0xFF) * f + tile * inv) shr 8
                    val g = (((p shr 8) and 0xFF) * f + tile * inv) shr 8
                    val b = ((p and 0xFF) * f + tile * inv) shr 8
                    (0xFF shl 24) or (r shl 16) or (g shl 8) or b
                }
                i++
            }
        }
        // Reuse the caller's bitmap when it fits. A brush stroke redraws this
        // every frame, and a fresh 384x384 ARGB_8888 per frame is ~590 KB of
        // garbage per frame.
        val target = if (into != null && !into.isRecycled && into.isMutable &&
                         into.width == width && into.height == height) into
                     else Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        target.setPixels(px, 0, width, 0, 0, width, height)
        return target
    }

    // ─── The live pattern ─────────────────────────────────────────────────────

    /**
     * Rebuild the pattern, recomputing only the cells that are stale.
     *
     * Cheap enough to call on every frame of a brush stroke; the caller still
     * debounces slider drags, because those invalidate everything.
     */
    fun buildPattern(title: String): FusePattern {
        refreshStaleCells()
        val (palette, assignments) = ImageConverter.chooseAndAssign(
            dist, cols, rows, options.maxColors.coerceIn(1, 32)
        )
        val cells = ArrayList<Cell>(cols * rows)
        for (y in 0 until rows) {
            for (x in 0 until cols) {
                assignments[y][x]?.let { cells.add(Cell(x, y, it)) }
            }
        }
        val difficulty = when {
            cells.size < 80 -> Difficulty.easy
            cells.size < 350 -> Difficulty.medium
            else -> Difficulty.hard
        }
        return FusePattern(
            id = UUID.randomUUID().toString(),
            title = title,
            category = PatternCategory.custom,
            createdBy = CreatorType.user,
            grid = GridSize(cols, rows),
            palette = palette,
            cells = cells,
            difficulty = difficulty,
            tags = listOf("photo", "imported"),
            shape = shape,
            version = 1
        )
    }

    /**
     * The options to hand [ImageConverter.convert] for the committed pattern,
     * with the studio's crop scaled onto a [targetW] x [targetH] photo. The
     * final conversion runs against the FULL-resolution photo, so the
     * preview's small working buffer never ends up in a saved pattern.
     */
    fun finalOptionsFor(targetW: Int, targetH: Int): ConvertOptions =
        options.copy(crop = scaleCropTo(crop, targetW, targetH))

    /** The crop the board is currently sampling, in working-buffer pixels. */
    fun currentCrop(): Rect = Rect(crop)

    /** Has the user actually dropped anything? Drives whether a cut-out is saved. */
    val hasRemoval: Boolean
        get() {
            for (k in keep) if (!k) return true
            return false
        }


    /** The full-resolution photo with everything the user removed made transparent. */
    fun maskedFullRes(src: Bitmap): Bitmap {
        val w = src.width
        val h = src.height
        val px = IntArray(w * h)
        src.getPixels(px, 0, w, 0, 0, w, h)
        for (y in 0 until h) {
            val sy = (y.toLong() * height / h).toInt().coerceIn(0, height - 1)
            val base = y * w
            for (x in 0 until w) {
                val sx = (x.toLong() * width / w).toInt().coerceIn(0, width - 1)
                if (!keep[sy * width + sx]) px[base + x] = px[base + x] and 0x00FFFFFF
            }
        }
        return Bitmap.createBitmap(px, w, h, Bitmap.Config.ARGB_8888)
    }

    /**
     * Bounding box of the kept pixels, grown to the board's aspect ratio.
     *
     * Cropping to the subject is the other half of the background-removal win:
     * without it the app's centred square crop both clips the subject and
     * spends most of the board on empty space, so the parts that matter get
     * too few beads to resolve.
     */
    fun subjectCrop(cols: Int, rows: Int, padFrac: Float = 0.04f): Rect? {
        var minX = width; var minY = height; var maxX = -1; var maxY = -1
        for (y in 0 until height) {
            val base = y * width
            for (x in 0 until width) {
                if (!keep[base + x] || srcAlpha[base + x] < 0.5f) continue
                if (x < minX) minX = x
                if (x > maxX) maxX = x
                if (y < minY) minY = y
                if (y > maxY) maxY = y
            }
        }
        if (maxX < minX || maxY < minY) return null
        val pad = (max(maxX - minX, maxY - minY) * padFrac).roundToInt()
        var x0 = minX - pad; var y0 = minY - pad
        var x1 = maxX + 1 + pad; var y1 = maxY + 1 + pad
        // Grow the subject box to the board's aspect ratio, then FIT that box
        // inside the photo without changing its shape.
        //
        // The previous version grew the box to the ratio and then clamped each
        // edge into bounds on its own, which silently threw the ratio away
        // again. A subject near an edge - or any subject whose grown box was
        // wider than the photo, which is every tall portrait shot on a square
        // board - came back as a rect of some other shape, and sampling that
        // onto a square board stretches one axis. That is the squashed pattern:
        // it happened by default, because fitting to the subject is on by
        // default and every board this app offers is square.
        val target = cols.toDouble() / rows
        val cx = (x0 + x1) / 2
        val cy = (y0 + y1) / 2
        var bw = x1 - x0
        var bh = y1 - y0
        if (bw.toDouble() / bh < target) bw = (bh * target).roundToInt()
        else bh = (bw / target).roundToInt()

        // Shrink to what the photo can hold, keeping the ratio. Order matters
        // and is safe either way round: reaching the second branch means the
        // first left the other side with room to spare.
        if (bw > width) { bw = width; bh = (bw / target).roundToInt() }
        if (bh > height) { bh = height; bw = (bh * target).roundToInt() }
        bw = bw.coerceIn(1, width)
        bh = bh.coerceIn(1, height)

        // Slide it fully inside the photo rather than cutting an edge off it.
        val left = (cx - bw / 2).coerceIn(0, width - bw)
        val top = (cy - bh / 2).coerceIn(0, height - bh)
        return Rect(left, top, left + bw, top + bh)
    }

    /** Scale a working-buffer rect up to a full-resolution photo's pixels. */
    fun scaleCropTo(rect: Rect, targetW: Int, targetH: Int): Rect = Rect(
        (rect.left.toLong() * targetW / width).toInt().coerceIn(0, targetW - 1),
        (rect.top.toLong() * targetH / height).toInt().coerceIn(0, targetH - 1),
        (rect.right.toLong() * targetW / width).toInt().coerceIn(1, targetW),
        (rect.bottom.toLong() * targetH / height).toInt().coerceIn(1, targetH)
    )

    // ─── Internals ────────────────────────────────────────────────────────────

    private fun markStalePixels(px0: Int, py0: Int, px1: Int, py1: Int) {
        if (cols == 0 || rows == 0) return
        val cw = max(1, crop.width())
        val ch = max(1, crop.height())
        // Widen by one cell each way: a cell straddling the brush edge changes
        // too, and integer division truncates toward the near edge.
        val cx0 = (((px0 - crop.left).toLong() * cols / cw).toInt() - 1).coerceIn(0, cols - 1)
        val cx1 = (((px1 - crop.left).toLong() * cols / cw).toInt() + 1).coerceIn(0, cols - 1)
        val cy0 = (((py0 - crop.top).toLong() * rows / ch).toInt() - 1).coerceIn(0, rows - 1)
        val cy1 = (((py1 - crop.top).toLong() * rows / ch).toInt() + 1).coerceIn(0, rows - 1)
        for (cy in cy0..cy1) for (cx in cx0..cx1) stale[cy * cols + cx] = true
    }

    private fun refreshStaleCells() {
        if (cols == 0 || rows == 0) return
        val x0 = crop.left.coerceIn(0, width - 1)
        val y0 = crop.top.coerceIn(0, height - 1)
        val w = crop.width().coerceAtMost(width - x0).coerceAtLeast(1)
        val h = crop.height().coerceAtMost(height - y0).coerceAtLeast(1)
        val gr = options.whiteBalance[0]
        val gg = options.whiteBalance[1]
        val gb = options.whiteBalance[2]
        val cell = DoubleArray(3)      // reused scratch: one per cell, not per pixel

        for (cy in 0 until rows) {
            val sy0 = (cy.toLong() * h / rows).toInt()
            val sy1 = ((cy + 1).toLong() * h / rows).toInt().coerceAtLeast(sy0 + 1).coerceAtMost(h)
            for (cx in 0 until cols) {
                val idx = cy * cols + cx
                if (!everythingStale && !stale[idx]) continue
                stale[idx] = false

                if (!shape.contains(cx, cy, cols, rows)) { dist[idx] = null; continue }

                val sx0 = (cx.toLong() * w / cols).toInt()
                val sx1 = ((cx + 1).toLong() * w / cols).toInt().coerceAtLeast(sx0 + 1).coerceAtMost(w)

                var rAcc = 0.0; var gAcc = 0.0; var bAcc = 0.0
                var aAcc = 0.0; var lAcc = 0.0; var n = 0
                var lMin = Double.MAX_VALUE; var lMax = -Double.MAX_VALUE
                for (sy in sy0 until sy1) {
                    val row = (y0 + sy) * width + x0
                    for (sx in sx0 until sx1) {
                        val pi = row + sx
                        n++
                        // A dropped pixel contributes nothing, exactly as a
                        // transparent one does in the one-shot converter.
                        val a = if (keep[pi]) srcAlpha[pi].toDouble() else 0.0
                        if (a <= 0.0) continue
                        val j = pi * 3
                        val pr = lin[j].toDouble()
                        val pg = lin[j + 1].toDouble()
                        val pb = lin[j + 2].toDouble()
                        val y = ColorMath.luma(pr, pg, pb)
                        if (y < lMin) lMin = y
                        if (y > lMax) lMax = y
                        aAcc += a; lAcc += y * a
                        rAcc += pr * a; gAcc += pg * a; bAcc += pb * a
                    }
                }
                if (n == 0 || aAcc / n < 0.35) { dist[idx] = null; continue }

                val mR = rAcc / aAcc; val mG = gAcc / aAcc; val mB = bAcc / aAcc
                cell[0] = mR; cell[1] = mG; cell[2] = mB
                if (lMax - lMin >= ColorMath.EDGE_MIN_LUMA_RANGE) {
                    val midL = lAcc / aAcc
                    var dr = 0.0; var dg = 0.0; var db = 0.0; var dw = 0.0
                    var xr = 0.0; var xg = 0.0; var xb = 0.0; var xw = 0.0
                    for (sy in sy0 until sy1) {
                        val row = (y0 + sy) * width + x0
                        for (sx in sx0 until sx1) {
                            val pi = row + sx
                            val a = if (keep[pi]) srcAlpha[pi].toDouble() else 0.0
                            if (a <= 0.0) continue
                            val j = pi * 3
                            val pr = lin[j].toDouble()
                            val pg = lin[j + 1].toDouble()
                            val pb = lin[j + 2].toDouble()
                            if (ColorMath.luma(pr, pg, pb) <= midL) {
                                dr += pr * a; dg += pg * a; db += pb * a; dw += a
                            } else {
                                xr += pr * a; xg += pg * a; xb += pb * a; xw += a
                            }
                        }
                    }
                    ColorMath.resolveCell(cell, mR, mG, mB, dr, dg, db, dw, xr, xg, xb, xw)
                }
                val lab = ColorMath.linearRgbToLab(
                    (cell[0] * gr).coerceIn(0.0, 1.0),
                    (cell[1] * gg).coerceIn(0.0, 1.0),
                    (cell[2] * gb).coerceIn(0.0, 1.0)
                )
                dist[idx] = ImageConverter.beadDistances(adjust(lab))
            }
        }
        everythingStale = false
    }

    /** Same perceptual adjustments the one-shot converter applies. */
    private fun adjust(lab: DoubleArray): DoubleArray {
        var l = lab[0]; var a = lab[1]; var b = lab[2]
        if (options.brightness != 0f) l += options.brightness * 50.0
        if (options.contrast != 0f) l = 50.0 + (l - 50.0) * (1.0 + options.contrast)
        if (options.chromaLift > 0f) {
            val c = sqrt(a * a + b * b)
            if (c > 0.0) {
                val k = 16.0
                val t = k / (c + k)
                val s = 1.0 + options.chromaLift * t * t
                a *= s; b *= s
            }
        }
        if (options.saturation != 0f) {
            val s = (1.0 + options.saturation).coerceAtLeast(0.0)
            a *= s; b *= s
        }
        return doubleArrayOf(l.coerceIn(0.0, 100.0), a, b)
    }

    companion object {
        const val WORK_MAX_DIM = 384
        private const val CHECKER = 12
        private const val GAIN_MIN = 0.70
        private const val GAIN_MAX = 1.45

        /** Resample [src] into a working buffer and take its linear-light copy. */
        fun from(src: Bitmap, maxDim: Int = WORK_MAX_DIM): PhotoStudio {
            val scale = min(1.0, maxDim.toDouble() / max(src.width, src.height))
            val w = max(1, (src.width * scale).roundToInt())
            val h = max(1, (src.height * scale).roundToInt())
            val small = if (w == src.width && h == src.height) src
                        else Bitmap.createScaledBitmap(src, w, h, true)

            val px = IntArray(w * h)
            small.getPixels(px, 0, w, 0, 0, w, h)
            if (small !== src) small.recycle()

            val lut = FloatArray(256) { ColorMath.srgbToLinear(it / 255f) }
            val lin = FloatArray(w * h * 3)
            val alpha = FloatArray(w * h)
            for (i in px.indices) {
                val p = px[i]
                alpha[i] = ((p ushr 24) and 0xFF) / 255f
                val j = i * 3
                lin[j] = lut[(p shr 16) and 0xFF]
                lin[j + 1] = lut[(p shr 8) and 0xFF]
                lin[j + 2] = lut[p and 0xFF]
            }
            return PhotoStudio(w, h, lin, alpha, px)
        }
    }
}
