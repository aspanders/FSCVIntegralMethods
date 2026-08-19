package com.beadsnap.app.services

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.beadsnap.app.data.model.BeadColor
import com.beadsnap.app.data.model.Cell
import com.beadsnap.app.data.model.CreatorType
import com.beadsnap.app.data.model.Difficulty
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.model.GridSize
import com.beadsnap.app.data.model.PatternCategory
import java.util.UUID
import kotlin.math.min

/**
 * Tunables for photo -> pattern conversion. Exposed so the editor can re-run a
 * conversion live as the user drags a slider, rather than forcing every choice
 * to be made up front.
 *
 * brightness/contrast/saturation are all -1..1, 0 meaning "leave alone", and are
 * applied in CIELAB so they behave perceptually rather than clipping channels.
 */
data class ConvertOptions(
    val maxColors: Int = 12,
    val brightness: Float = 0f,
    val contrast: Float = 0f,
    val saturation: Float = 0f,
    /** Source-pixel rect to use; null means the whole bitmap. */
    val crop: android.graphics.Rect? = null,
)

object ImageConverter {

    fun convert(bitmap: Bitmap, gridSize: GridSize, maxColors: Int = 12): FusePattern =
        convert(bitmap, gridSize, ConvertOptions(maxColors = maxColors))

    fun convert(bitmap: Bitmap, gridSize: GridSize, options: ConvertOptions): FusePattern {
        val cols = gridSize.width
        val rows = gridSize.height
        val cellLab = sampleCellsLab(bitmap, cols, rows, options)
        val (palette, assignments) = quantizeBeadSafe(cellLab, cols, rows, min(options.maxColors, 16))

        val cells = mutableListOf<Cell>()
        for (y in 0 until rows) {
            for (x in 0 until cols) {
                assignments[y][x]?.let { cells.add(Cell(x, y, it)) }
            }
        }
        val difficulty = when {
            cells.size < 80  -> Difficulty.easy
            cells.size < 350 -> Difficulty.medium
            else             -> Difficulty.hard
        }
        return FusePattern(
            id = UUID.randomUUID().toString(),
            title = "Imported Photo",
            category = PatternCategory.custom,
            createdBy = CreatorType.user,
            grid = gridSize,
            palette = palette,
            cells = cells,
            difficulty = difficulty,
            tags = listOf("photo", "imported"),
            version = 1
        )
    }

    // Render FusePattern to Bitmap (used for export / sharing)
    fun renderToBitmap(pattern: FusePattern, cellSizePx: Int = 18): Bitmap {
        val w = pattern.grid.width * cellSizePx
        val h = pattern.grid.height * cellSizePx
        val bitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        canvas.drawColor(Color.WHITE)

        val paint = Paint(Paint.ANTI_ALIAS_FLAG)
        // Thin rim for bead definition where fused beads meet.
        val rimPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = (cellSizePx * 0.05f).coerceAtLeast(0.5f)
            color = Color.argb(30, 0, 0, 0)   // ~12% black
        }
        // The center hole of a fuse bead, drawn as a faint light ring.
        val holePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
            color = Color.argb(28, 255, 255, 255)
        }
        val colorById = pattern.palette.associateBy { it.id }
        val r = cellSizePx / 2f          // bead radius = half the pitch, so beads touch
        val holeR = cellSizePx * 0.17f   // hole = the tube through the bead

        for (cell in pattern.cells) {
            val color = colorById[cell.colorId] ?: continue
            val cx = cell.x * cellSizePx + r
            val cy = cell.y * cellSizePx + r
            paint.color = color.androidColor
            paint.style = Paint.Style.FILL
            canvas.drawCircle(cx, cy, r, paint)        // full-size bead: edges touch neighbors
            canvas.drawCircle(cx, cy, holeR, holePaint) // faint center hole = fused-bead look
            canvas.drawCircle(cx, cy, r - rimPaint.strokeWidth / 2f, rimPaint)
        }
        return bitmap
    }

    // ─── Cell sampling ────────────────────────────────────────────────────────

    /**
     * Average every source pixel that falls under each bead, in LINEAR light,
     * and return the result as CIELAB (null for cells that are mostly
     * transparent).
     *
     * The old version handed the whole job to a single
     * Bitmap.createScaledBitmap(src, cols, rows, true). Collapsing a
     * multi-megapixel photo straight to ~29x29 that way does not box-average the
     * source: the bilinear filter reads a tiny neighbourhood per output pixel
     * and ignores the rest, so most of the photo never contributes at all. It
     * also averaged gamma-encoded sRGB, which biases every blend dark and flat.
     * Between them that was the main reason converted photos looked muddy.
     */
    private fun sampleCellsLab(
        src: Bitmap, cols: Int, rows: Int, options: ConvertOptions
    ): Array<Array<DoubleArray?>> {
        val crop = options.crop
        val x0 = crop?.left?.coerceIn(0, src.width - 1) ?: 0
        val y0 = crop?.top?.coerceIn(0, src.height - 1) ?: 0
        val w = (crop?.width() ?: src.width).coerceAtMost(src.width - x0).coerceAtLeast(1)
        val h = (crop?.height() ?: src.height).coerceAtMost(src.height - y0).coerceAtLeast(1)

        val pixels = IntArray(w * h)
        src.getPixels(pixels, 0, w, x0, y0, w, h)

        // Cache the 256 possible sRGB byte values -> linear, so the inner loop
        // never repeats the pow().
        val lin = FloatArray(256) { ColorMath.srgbToLinear(it / 255f) }

        val out = Array(rows) { arrayOfNulls<DoubleArray>(cols) }
        for (cy in 0 until rows) {
            val sy0 = (cy.toLong() * h / rows).toInt()
            val sy1 = (((cy + 1).toLong() * h / rows).toInt()).coerceAtLeast(sy0 + 1).coerceAtMost(h)
            for (cx in 0 until cols) {
                val sx0 = (cx.toLong() * w / cols).toInt()
                val sx1 = (((cx + 1).toLong() * w / cols).toInt()).coerceAtLeast(sx0 + 1).coerceAtMost(w)

                var rAcc = 0.0; var gAcc = 0.0; var bAcc = 0.0
                var aAcc = 0.0; var n = 0
                for (sy in sy0 until sy1) {
                    var idx = sy * w + sx0
                    for (sx in sx0 until sx1) {
                        val p = pixels[idx++]
                        val a = (p ushr 24) and 0xFF
                        n++
                        if (a == 0) continue
                        val wgt = a / 255.0
                        aAcc += wgt
                        rAcc += lin[(p shr 16) and 0xFF] * wgt
                        gAcc += lin[(p shr 8) and 0xFF] * wgt
                        bAcc += lin[p and 0xFF] * wgt
                    }
                }
                // Mostly-transparent cells stay empty so background removal and
                // non-square crops leave real holes instead of muddy edges.
                if (n == 0 || aAcc / n < 0.35) continue
                val lab = ColorMath.linearRgbToLab(rAcc / aAcc, gAcc / aAcc, bAcc / aAcc)
                out[cy][cx] = adjustLab(lab, options)
            }
        }
        return out
    }

    /** Brightness/contrast/saturation applied perceptually, in CIELAB. */
    private fun adjustLab(lab: DoubleArray, o: ConvertOptions): DoubleArray {
        var l = lab[0]
        var a = lab[1]
        var b = lab[2]
        if (o.brightness != 0f) l += o.brightness * 50.0
        if (o.contrast != 0f) l = 50.0 + (l - 50.0) * (1.0 + o.contrast)
        if (o.saturation != 0f) {
            val s = (1.0 + o.saturation).coerceAtLeast(0.0)
            a *= s
            b *= s
        }
        return doubleArrayOf(l.coerceIn(0.0, 100.0), a, b)
    }

    // ─── Bead-safe nearest-colour quantization ────────────────────────────────

    /**
     * Choose which beads to use, then assign every cell to one of them.
     *
     * Selection is error-minimizing rather than frequency-based. The old code
     * matched each cell against the full palette, kept the N most COMMON beads
     * and reassigned the rest, which reliably threw away exactly the colours
     * that carry an image: a red scarf covering 3% of the photo lost to three
     * near-identical background greys. Here each additional bead is the one
     * that most reduces total error across the whole image, so a small but
     * distinct region keeps its colour.
     */
    private fun quantizeBeadSafe(
        cellLab: Array<Array<DoubleArray?>>,
        cols: Int, rows: Int, maxColors: Int
    ): Pair<List<BeadColor>, Array<Array<String?>>> {
        val full = BeadColor.palette
        val fullLab = full.map { c ->
            val ac = c.androidColor
            ColorMath.srgbToLab(
                Color.red(ac) / 255f, Color.green(ac) / 255f, Color.blue(ac) / 255f
            )
        }

        // Flatten the non-empty cells so selection works on a flat list.
        val coords = ArrayList<Int>(cols * rows)
        val labs = ArrayList<DoubleArray>(cols * rows)
        for (y in 0 until rows) {
            for (x in 0 until cols) {
                val lab = cellLab[y][x] ?: continue
                coords.add(y * cols + x)
                labs.add(lab)
            }
        }
        val assignments = Array(rows) { arrayOfNulls<String>(cols) }
        if (labs.isEmpty()) return emptyList<BeadColor>() to assignments

        // Distance from every cell to every candidate bead, computed once.
        val nCells = labs.size
        val nPal = full.size
        val dist = Array(nCells) { i ->
            DoubleArray(nPal) { p -> ColorMath.beadDistance(labs[i], fullLab[p]) }
        }

        // Greedy: repeatedly add whichever bead most reduces the total error.
        val chosen = ArrayList<Int>(maxColors)
        val best = DoubleArray(nCells) { Double.MAX_VALUE }
        val budget = maxColors.coerceAtLeast(1)
        repeat(budget) {
            var bestPal = -1
            var bestTotal = Double.MAX_VALUE
            for (p in 0 until nPal) {
                if (p in chosen) continue
                var total = 0.0
                for (i in 0 until nCells) {
                    val d = dist[i][p]
                    total += if (d < best[i]) d else best[i]
                    if (total >= bestTotal) break      // prune: cannot win
                }
                if (total < bestTotal) { bestTotal = total; bestPal = p }
            }
            if (bestPal < 0) return@repeat
            chosen.add(bestPal)
            for (i in 0 until nCells) {
                val d = dist[i][bestPal]
                if (d < best[i]) best[i] = d
            }
        }
        if (chosen.isEmpty()) chosen.add(0)

        // Final assignment against the chosen set.
        for (i in 0 until nCells) {
            var bestPal = chosen[0]
            var bestD = Double.MAX_VALUE
            for (p in chosen) {
                val d = dist[i][p]
                if (d < bestD) { bestD = d; bestPal = p }
            }
            val flat = coords[i]
            assignments[flat / cols][flat % cols] = full[bestPal].id
        }

        val usedIds = assignments.flatMap { it.toList() }.filterNotNull().toSet()
        val palette = full.filter { it.id in usedIds }
        return palette to assignments
    }
}
