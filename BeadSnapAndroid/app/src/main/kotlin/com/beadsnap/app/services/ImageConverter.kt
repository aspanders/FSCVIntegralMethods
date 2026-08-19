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
import com.beadsnap.app.data.model.PegboardShape
import java.util.UUID
import kotlin.math.pow
import kotlin.math.roundToInt
import kotlin.math.sqrt

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
    /**
     * Rescues washed-out pastels. Photographed plastic under indoor light is
     * systematically desaturated: a pale blue toy body measured on a real test
     * photo came out at chroma 6.3, so the nearest bead was correctly but
     * unhelpfully Silver rather than Light Blue. This lifts low-chroma colours
     * back toward their hue. See applyChromaLift for why it is not a flat
     * saturation boost. 0 disables it.
     */
    val chromaLift: Float = 1.0f,
    /** Source-pixel rect to use; null means the whole bitmap. */
    val crop: android.graphics.Rect? = null,
    /** Square pegboard, or the square lattice clipped to a round board. */
    val shape: PegboardShape = PegboardShape.square,
    /**
     * Per-channel linear-light gains, applied before anything else.
     *
     * This is the only control that can undo a colour CAST, as opposed to a
     * loss of saturation. Measured on a real test photo of a blue toy shot
     * under warm indoor light against wood: the toy's body came out at chroma
     * 4.3 with its hue still correct at 231 degrees, and handing the quantizer
     * the ENTIRE 55-bead palette with no budget cap still produced only 2.8%
     * cool beads. The blue was not in the file. chromaLift cannot fix that -
     * it is multiplicative, so it amplifies a hue that is present but cannot
     * put back a channel the camera's white balance crushed.
     */
    val whiteBalance: FloatArray = NEUTRAL_GAINS,
) {
    // FloatArray breaks data-class equality (identity, not contents), and the
    // live studio re-runs whenever the options change, so compare by value.
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is ConvertOptions) return false
        return maxColors == other.maxColors && brightness == other.brightness &&
            contrast == other.contrast && saturation == other.saturation &&
            chromaLift == other.chromaLift && crop == other.crop &&
            shape == other.shape && whiteBalance.contentEquals(other.whiteBalance)
    }

    override fun hashCode(): Int {
        var r = maxColors
        r = 31 * r + brightness.hashCode()
        r = 31 * r + contrast.hashCode()
        r = 31 * r + saturation.hashCode()
        r = 31 * r + chromaLift.hashCode()
        r = 31 * r + (crop?.hashCode() ?: 0)
        r = 31 * r + shape.hashCode()
        r = 31 * r + whiteBalance.contentHashCode()
        return r
    }

    val hasWhiteBalance: Boolean
        get() = whiteBalance[0] != 1f || whiteBalance[1] != 1f || whiteBalance[2] != 1f

    companion object {
        val NEUTRAL_GAINS = floatArrayOf(1f, 1f, 1f)
    }
}

object ImageConverter {

    /**
     * The beads a photo conversion is allowed to choose from.
     *
     * "Clear" is excluded. It is a translucent bead whose stand-in hex
     * (#E8F4F8) is a pale cool white, so it competes directly with White for
     * every highlight - on the test photo it took 3.3% of the beads, none of
     * which look like that once fused. It stays in the editor palette for
     * anyone who wants to place it deliberately.
     */
    val autoPalette: List<BeadColor> by lazy {
        BeadColor.palette.filter { it.id != "clear" }
    }

    private val autoPaletteLab: List<DoubleArray> by lazy {
        autoPalette.map { c ->
            val ac = c.androidColor
            ColorMath.srgbToLab(
                Color.red(ac) / 255f, Color.green(ac) / 255f, Color.blue(ac) / 255f
            )
        }
    }

    /** Distance from one cell colour to every selectable bead. */
    fun beadDistances(lab: DoubleArray): DoubleArray =
        DoubleArray(autoPaletteLab.size) { p -> ColorMath.beadDistance(lab, autoPaletteLab[p]) }

    fun convert(bitmap: Bitmap, gridSize: GridSize, maxColors: Int = 12): FusePattern =
        convert(bitmap, gridSize, ConvertOptions(maxColors = maxColors))

    fun convert(bitmap: Bitmap, gridSize: GridSize, options: ConvertOptions): FusePattern {
        val cols = gridSize.width
        val rows = gridSize.height
        val cellLab = sampleCellsLab(bitmap, cols, rows, options)
        // Cells off a round board are not beads at all, so they never reach
        // palette selection - the disc's corners must not spend colour budget.
        if (options.shape != PegboardShape.square) {
            for (y in 0 until rows) for (x in 0 until cols) {
                if (!options.shape.contains(x, y, cols, rows)) cellLab[y][x] = null
            }
        }
        // The old cap of 16 silently ignored anything the colour slider set
        // above it, so asking for 24 quietly gave you 16.
        val (palette, assignments) =
            quantizeBeadSafe(cellLab, cols, rows, options.maxColors.coerceIn(1, 32))

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
            shape = options.shape,
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
        // With no explicit crop, take the largest centred rect matching the
        // grid's aspect ratio rather than stretching the whole frame onto it.
        // Every grid is square, so a 3:4 phone photo used to be squeezed
        // horizontally: subjects came out short and wide.
        val crop = options.crop ?: aspectCrop(src.width, src.height, cols, rows)
        val x0 = crop.left.coerceIn(0, src.width - 1)
        val y0 = crop.top.coerceIn(0, src.height - 1)
        val w = crop.width().coerceAtMost(src.width - x0).coerceAtLeast(1)
        val h = crop.height().coerceAtMost(src.height - y0).coerceAtLeast(1)

        val pixels = IntArray(w * h)
        src.getPixels(pixels, 0, w, x0, y0, w, h)

        // Cache the 256 possible sRGB byte values -> linear, so the inner loop
        // never repeats the pow().
        val lin = FloatArray(256) { ColorMath.srgbToLinear(it / 255f) }
        val gr = options.whiteBalance[0].toDouble()
        val gg = options.whiteBalance[1].toDouble()
        val gb = options.whiteBalance[2].toDouble()

        val out = Array(rows) { arrayOfNulls<DoubleArray>(cols) }
        val cell = DoubleArray(3)      // reused scratch: one per cell, not per pixel
        for (cy in 0 until rows) {
            val sy0 = (cy.toLong() * h / rows).toInt()
            val sy1 = (((cy + 1).toLong() * h / rows).toInt()).coerceAtLeast(sy0 + 1).coerceAtMost(h)
            for (cx in 0 until cols) {
                val sx0 = (cx.toLong() * w / cols).toInt()
                val sx1 = (((cx + 1).toLong() * w / cols).toInt()).coerceAtLeast(sx0 + 1).coerceAtMost(w)

                var rAcc = 0.0; var gAcc = 0.0; var bAcc = 0.0
                var aAcc = 0.0; var lAcc = 0.0; var n = 0
                var lMin = Double.MAX_VALUE; var lMax = -Double.MAX_VALUE
                for (sy in sy0 until sy1) {
                    var idx = sy * w + sx0
                    for (sx in sx0 until sx1) {
                        val p = pixels[idx++]
                        val a = (p ushr 24) and 0xFF
                        n++
                        if (a == 0) continue
                        val wgt = a / 255.0
                        val pr = lin[(p shr 16) and 0xFF].toDouble()
                        val pg = lin[(p shr 8) and 0xFF].toDouble()
                        val pb = lin[p and 0xFF].toDouble()
                        val y = ColorMath.luma(pr, pg, pb)
                        if (y < lMin) lMin = y
                        if (y > lMax) lMax = y
                        aAcc += wgt; lAcc += y * wgt
                        rAcc += pr * wgt; gAcc += pg * wgt; bAcc += pb * wgt
                    }
                }
                // Mostly-transparent cells stay empty so background removal and
                // non-square crops leave real holes instead of muddy edges.
                if (n == 0 || aAcc / n < 0.35) continue

                val mR = rAcc / aAcc; val mG = gAcc / aAcc; val mB = bAcc / aAcc
                cell[0] = mR; cell[1] = mG; cell[2] = mB
                if (lMax - lMin >= ColorMath.EDGE_MIN_LUMA_RANGE) {
                    // Second pass, only where the cell could be straddling an
                    // edge: split its pixels at their own mean luminance and
                    // let ColorMath.resolveCell decide between averaging and
                    // snapping to the dominant side.
                    val midL = lAcc / aAcc
                    var dr = 0.0; var dg = 0.0; var db = 0.0; var dw = 0.0
                    var xr = 0.0; var xg = 0.0; var xb = 0.0; var xw = 0.0
                    for (sy in sy0 until sy1) {
                        var idx = sy * w + sx0
                        for (sx in sx0 until sx1) {
                            val p = pixels[idx++]
                            val a = (p ushr 24) and 0xFF
                            if (a == 0) continue
                            val wgt = a / 255.0
                            val pr = lin[(p shr 16) and 0xFF].toDouble()
                            val pg = lin[(p shr 8) and 0xFF].toDouble()
                            val pb = lin[p and 0xFF].toDouble()
                            if (ColorMath.luma(pr, pg, pb) <= midL) {
                                dr += pr * wgt; dg += pg * wgt; db += pb * wgt; dw += wgt
                            } else {
                                xr += pr * wgt; xg += pg * wgt; xb += pb * wgt; xw += wgt
                            }
                        }
                    }
                    ColorMath.resolveCell(cell, mR, mG, mB, dr, dg, db, dw, xr, xg, xb, xw)
                }
                // White balance is a scale in LINEAR light, so it commutes with
                // the averaging above and can be applied once per cell rather
                // than once per pixel.
                val lab = ColorMath.linearRgbToLab(
                    (cell[0] * gr).coerceIn(0.0, 1.0),
                    (cell[1] * gg).coerceIn(0.0, 1.0),
                    (cell[2] * gb).coerceIn(0.0, 1.0)
                )
                out[cy][cx] = adjustLab(lab, options)
            }
        }
        return out
    }

    /**
     * The largest centred rect of [srcW] x [srcH] whose aspect ratio matches a
     * cols x rows grid. Used as the default crop so photos keep their
     * proportions instead of being stretched onto a square board.
     */
    fun aspectCrop(srcW: Int, srcH: Int, cols: Int, rows: Int): android.graphics.Rect {
        if (srcW <= 0 || srcH <= 0 || cols <= 0 || rows <= 0) {
            return android.graphics.Rect(0, 0, srcW.coerceAtLeast(1), srcH.coerceAtLeast(1))
        }
        val target = cols.toDouble() / rows
        val current = srcW.toDouble() / srcH
        return if (current > target) {
            // Too wide: trim the sides.
            val w = (srcH * target).roundToInt().coerceIn(1, srcW)
            val left = (srcW - w) / 2
            android.graphics.Rect(left, 0, left + w, srcH)
        } else {
            // Too tall: trim top and bottom.
            val h = (srcW / target).roundToInt().coerceIn(1, srcH)
            val top = (srcH - h) / 2
            android.graphics.Rect(0, top, srcW, top + h)
        }
    }

    /** Brightness/contrast/saturation applied perceptually, in CIELAB. */
    private fun adjustLab(lab: DoubleArray, o: ConvertOptions): DoubleArray {
        var l = lab[0]
        var a = lab[1]
        var b = lab[2]
        if (o.brightness != 0f) l += o.brightness * 50.0
        if (o.contrast != 0f) l = 50.0 + (l - 50.0) * (1.0 + o.contrast)
        if (o.chromaLift > 0f) {
            val lifted = applyChromaLift(a, b, o.chromaLift.toDouble())
            a = lifted[0]; b = lifted[1]
        }
        // The user's own saturation slider rides on top of the photographic
        // correction above.
        if (o.saturation != 0f) {
            val s = (1.0 + o.saturation).coerceAtLeast(0.0)
            a *= s
            b *= s
        }
        return doubleArrayOf(l.coerceIn(0.0, 100.0), a, b)
    }

    /**
     * Scale chroma by 1 + amount * (K/(C+K))^2.
     *
     * A FLAT saturation boost cannot do this job: measured on a real photo,
     * the boost needed to move a pale blue body (chroma 6.3) off Silver and
     * onto Light Blue was also enough to push a vivid pink past Hot Pink and
     * into Magenta. The squared falloff concentrates the correction where it
     * is needed - at chroma 6 the lift is ~1.5x, by chroma 64 it is ~1.04x -
     * so pastels regain their hue and saturated colours stay put.
     *
     * Because it is multiplicative it can only amplify a hue that is already
     * present: a true neutral (chroma 0) stays exactly neutral rather than
     * having a colour invented for it.
     */
    private fun applyChromaLift(a: Double, b: Double, amount: Double): DoubleArray {
        val c = sqrt(a * a + b * b)
        if (c <= 0.0) return doubleArrayOf(a, b)
        val k = 16.0
        val s = 1.0 + amount * (k / (c + k)).pow(2.0)
        return doubleArrayOf(a * s, b * s)
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
        val dist = arrayOfNulls<DoubleArray>(cols * rows)
        for (y in 0 until rows) {
            for (x in 0 until cols) {
                val lab = cellLab[y][x] ?: continue
                dist[y * cols + x] = beadDistances(lab)
            }
        }
        return chooseAndAssign(dist, cols, rows, maxColors)
    }

    /**
     * Choose which beads to use, then assign every cell to one of them.
     *
     * Takes the per-cell distance rows rather than the cell colours, because
     * the live studio keeps those rows cached: brushing the mask only changes
     * the cells the brush touched, so only those rows are recomputed, while
     * this selection still runs over the whole board exactly as a one-shot
     * conversion would. Sharing this function is what keeps the live preview
     * and the committed pattern from drifting apart.
     *
     * A null row means "no bead here" - transparent, or off a round board.
     *
     * Selection is error-minimizing rather than frequency-based. The old code
     * matched each cell against the full palette, kept the N most COMMON beads
     * and reassigned the rest, which reliably threw away exactly the colours
     * that carry an image: a red scarf covering 3% of the photo lost to three
     * near-identical background greys. Here each additional bead is the one
     * that most reduces total error across the whole image, so a small but
     * distinct region keeps its colour.
     */
    fun chooseAndAssign(
        dist: Array<DoubleArray?>,
        cols: Int, rows: Int, maxColors: Int
    ): Pair<List<BeadColor>, Array<Array<String?>>> {
        val assignments = Array(rows) { arrayOfNulls<String>(cols) }

        // Flatten the live cells so selection works on a dense list.
        val coords = ArrayList<Int>(cols * rows)
        val live = ArrayList<DoubleArray>(cols * rows)
        for (i in 0 until cols * rows) {
            val row = dist[i] ?: continue
            coords.add(i)
            live.add(row)
        }
        if (live.isEmpty()) return emptyList<BeadColor>() to assignments

        val nCells = live.size
        val nPal = autoPalette.size

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
                    val d = live[i][p]
                    total += if (d < best[i]) d else best[i]
                    if (total >= bestTotal) break      // prune: cannot win
                }
                if (total < bestTotal) { bestTotal = total; bestPal = p }
            }
            if (bestPal < 0) return@repeat
            chosen.add(bestPal)
            for (i in 0 until nCells) {
                val d = live[i][bestPal]
                if (d < best[i]) best[i] = d
            }
        }
        if (chosen.isEmpty()) chosen.add(0)

        // Final assignment against the chosen set.
        val usedIds = HashSet<String>(chosen.size * 2)
        for (i in 0 until nCells) {
            var bestPal = chosen[0]
            var bestD = Double.MAX_VALUE
            for (p in chosen) {
                val d = live[i][p]
                if (d < bestD) { bestD = d; bestPal = p }
            }
            val flat = coords[i]
            val id = autoPalette[bestPal].id
            usedIds.add(id)
            assignments[flat / cols][flat % cols] = id
        }

        val palette = autoPalette.filter { it.id in usedIds }
        return palette to assignments
    }
}
