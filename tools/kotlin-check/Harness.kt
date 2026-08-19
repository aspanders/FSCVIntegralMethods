import android.graphics.Bitmap
import android.graphics.Rect
import com.beadsnap.app.data.model.GridSize
import com.beadsnap.app.data.model.PegboardShape
import com.beadsnap.app.services.ConvertOptions
import com.beadsnap.app.services.PhotoStudio
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder

/** Set with -Dfixture=DIR; defaults to the prepare_fixture.py default. */
private fun fixtureDir(): String = System.getProperty("fixture") ?: "/tmp/kcheck"


fun loadStudio(w: Int, h: Int): PhotoStudio {
    val bytes = File(fixtureDir(), "photo.argb").readBytes()
    val ib = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).asIntBuffer()
    val px = IntArray(w * h); ib.get(px)
    val bmp = Bitmap.createBitmap(px, w, h, Bitmap.Config.ARGB_8888)
    return PhotoStudio.from(bmp, 384)
}

fun loadMask(w: Int, h: Int): BooleanArray {
    val raw = File(fixtureDir(), "mask.u8").readBytes()
    return BooleanArray(w * h) { raw[it].toInt() != 0 }
}

fun dump(tag: String, s: PhotoStudio, cols: Int, rows: Int) {
    val p = s.buildPattern("t")
    val grid = Array(rows) { arrayOfNulls<String>(cols) }
    p.cells.forEach { c -> c.colorId?.let { grid[c.y][c.x] = it } }
    File(fixtureDir(), "out_$tag.txt").printWriter().use { out ->
        out.println("cols=$cols rows=$rows beads=${p.totalBeads} colours=${p.palette.size}")
        out.println("palette=" + p.palette.joinToString(",") { it.id })
        for (y in 0 until rows) out.println(grid[y].joinToString(",") { it ?: "." })
    }
    println("$tag: ${p.totalBeads} beads, ${p.palette.size} colours")
}

fun main() {
    val w = 288; val h = 384
    val cols = 48; val rows = 48

    // ── 1. no mask, app's aspect crop, neutral options ───────────────────────
    run {
        val s = loadStudio(w, h)
        s.configure(cols, rows, null, ConvertOptions(maxColors = 16), PegboardShape.square)
        dump("plain", s, cols, rows)
    }

    // ── 2. with the cut-out mask + subject crop ──────────────────────────────
    run {
        val s = loadStudio(w, h)
        s.adoptMask(loadMask(w, h), w, h)
        val crop = s.subjectCrop(cols, rows)!!
        println("subjectCrop = ${crop.left},${crop.top},${crop.right},${crop.bottom}")
        s.configure(cols, rows, crop, ConvertOptions(maxColors = 16), PegboardShape.square)
        dump("cutout", s, cols, rows)
        val g = s.measureGreyWorld()
        println("greyWorld = ${g[0]}, ${g[1]}, ${g[2]}")
        File(fixtureDir(), "crops.json").writeText(
            """{"subject":[${crop.left},${crop.top},${crop.right},${crop.bottom}],""" +
            """"gains":[${g[0]},${g[1]},${g[2]}]}"""
        )
        // 3. same, with white balance at 50%
        val half = floatArrayOf(1f + 0.5f * (g[0] - 1f), 1f + 0.5f * (g[1] - 1f), 1f + 0.5f * (g[2] - 1f))
        s.configure(cols, rows, crop, ConvertOptions(maxColors = 16, whiteBalance = half), PegboardShape.square)
        dump("wb50", s, cols, rows)
    }

    // ── 4. THE INCREMENTAL TEST ─────────────────────────────────────────────
    // Brush a stroke, rebuild incrementally, and compare against a studio that
    // reached the same mask state from scratch. They must agree exactly, or the
    // dirty-rect logic is dropping cells.
    run {
        val a = loadStudio(w, h); a.adoptMask(loadMask(w, h), w, h)
        val b = loadStudio(w, h); b.adoptMask(loadMask(w, h), w, h)
        val crop = Rect(0, 0, w, h)
        val opts = ConvertOptions(maxColors = 16)
        a.configure(cols, rows, crop, opts, PegboardShape.square)
        a.buildPattern("warm")                       // prime a's caches
        b.configure(cols, rows, crop, opts, PegboardShape.square)

        // a: incremental. b: identical strokes, then forced full rebuild.
        val strokes = listOf(
            Triple(0.45f, 0.30f, true), Triple(0.50f, 0.35f, true),
            Triple(0.20f, 0.80f, false), Triple(0.80f, 0.20f, false),
            Triple(0.55f, 0.55f, false), Triple(0.05f, 0.05f, true)
        )
        strokes.forEach { (x, y, k) -> a.brush(x, y, 0.03f, k); a.buildPattern("step") }
        strokes.forEach { (x, y, k) -> b.brush(x, y, 0.03f, k) }
        b.configure(cols, rows, crop, opts.copy(maxColors = 15), PegboardShape.square)
        b.configure(cols, rows, crop, opts, PegboardShape.square)   // force everythingStale
        dump("incremental", a, cols, rows)
        dump("fromscratch", b, cols, rows)
    }

    // ── 5. round board ──────────────────────────────────────────────────────
    run {
        val s = loadStudio(w, h)
        s.configure(cols, rows, null, ConvertOptions(maxColors = 12, shape = PegboardShape.circle),
                    PegboardShape.circle)
        dump("circle", s, cols, rows)
    }
    println("HARNESS DONE")
}
