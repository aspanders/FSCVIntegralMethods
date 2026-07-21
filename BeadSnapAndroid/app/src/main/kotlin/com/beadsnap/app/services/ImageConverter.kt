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
import kotlin.math.pow

object ImageConverter {

    fun convert(bitmap: Bitmap, gridSize: GridSize, maxColors: Int = 12): FusePattern {
        val cols = gridSize.width
        val rows = gridSize.height
        val pixels = samplePixels(bitmap, cols, rows)
        val (palette, assignments) = quantizeBeadSafe(pixels, cols, rows, min(maxColors, 16))

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
        val strokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 0.5f
            color = Color.argb(38, 0, 0, 0)   // 15% black
        }
        val colorById = pattern.palette.associateBy { it.id }
        val inset = cellSizePx * 0.06f

        for (cell in pattern.cells) {
            val color = colorById[cell.colorId] ?: continue
            paint.color = color.androidColor
            paint.style = Paint.Style.FILL
            val left  = cell.x * cellSizePx + inset
            val top   = cell.y * cellSizePx + inset
            val right  = left + cellSizePx - 2 * inset
            val bottom = top  + cellSizePx - 2 * inset
            canvas.drawOval(left, top, right, bottom, paint)
            canvas.drawOval(left, top, right, bottom, strokePaint)
        }
        return bitmap
    }

    // ─── Pixel Sampling ───────────────────────────────────────────────────────

    private fun samplePixels(src: Bitmap, cols: Int, rows: Int): Array<Array<FloatArray>> {
        val scaled = Bitmap.createScaledBitmap(src, cols, rows, true)
        val result = Array(rows) { Array(cols) { FloatArray(4) } }
        for (y in 0 until rows) {
            for (x in 0 until cols) {
                val pixel = scaled.getPixel(x, y)
                val a = Color.alpha(pixel) / 255f
                if (a < 0.15f) {
                    result[y][x] = floatArrayOf(-1f, -1f, -1f, -1f)
                } else {
                    // getPixel returns straight (un-premultiplied) ARGB: no alpha division
                    result[y][x] = floatArrayOf(
                        Color.red(pixel) / 255f,
                        Color.green(pixel) / 255f,
                        Color.blue(pixel) / 255f,
                        a
                    )
                }
            }
        }
        if (scaled != src) scaled.recycle()
        return result
    }

    // ─── Bead-safe nearest-colour quantization ────────────────────────────────

    private fun quantizeBeadSafe(
        pixels: Array<Array<FloatArray>>,
        cols: Int, rows: Int, maxColors: Int
    ): Pair<List<BeadColor>, Array<Array<String?>>> {
        val full = BeadColor.palette
        val fullLab = full.map { c ->
            val ac = c.androidColor
            BeadColor.rgbToLab(Color.red(ac) / 255.0, Color.green(ac) / 255.0, Color.blue(ac) / 255.0)
        }

        val assignments = Array(rows) { arrayOfNulls<String>(cols) }
        val counts = mutableMapOf<String, Int>()

        for (y in 0 until rows) {
            for (x in 0 until cols) {
                val p = pixels[y][x]
                if (p[3] < 0) continue
                val lab = BeadColor.rgbToLab(p[0].toDouble(), p[1].toDouble(), p[2].toDouble())
                var bestIdx = 0; var bestDist = Double.MAX_VALUE
                fullLab.forEachIndexed { i, pLab ->
                    val d = (lab.first-pLab.first).pow(2) + (lab.second-pLab.second).pow(2) + (lab.third-pLab.third).pow(2)
                    if (d < bestDist) { bestDist = d; bestIdx = i }
                }
                val id = full[bestIdx].id
                assignments[y][x] = id
                counts[id] = (counts[id] ?: 0) + 1
            }
        }

        if (counts.size > maxColors) {
            val topIds = counts.entries.sortedByDescending { it.value }.take(maxColors).map { it.key }.toSet()
            val topPalette = full.filter { it.id in topIds }
            val topLab = topPalette.map { c ->
                val ac = c.androidColor
                BeadColor.rgbToLab(Color.red(ac) / 255.0, Color.green(ac) / 255.0, Color.blue(ac) / 255.0)
            }
            for (y in 0 until rows) {
                for (x in 0 until cols) {
                    val id = assignments[y][x] ?: continue
                    if (id in topIds) continue
                    val p = pixels[y][x]
                    val lab = BeadColor.rgbToLab(p[0].toDouble(), p[1].toDouble(), p[2].toDouble())
                    var bestIdx = 0; var bestDist = Double.MAX_VALUE
                    topLab.forEachIndexed { i, pLab ->
                        val d = (lab.first-pLab.first).pow(2) + (lab.second-pLab.second).pow(2) + (lab.third-pLab.third).pow(2)
                        if (d < bestDist) { bestDist = d; bestIdx = i }
                    }
                    assignments[y][x] = topPalette[bestIdx].id
                }
            }
        }

        val usedIds = assignments.flatMap { it.toList() }.filterNotNull().toSet()
        val palette = full.filter { it.id in usedIds }
        return palette to assignments
    }
}
