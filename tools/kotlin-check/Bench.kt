import android.graphics.Bitmap
import android.graphics.Rect
import com.beadsnap.app.data.model.PegboardShape
import com.beadsnap.app.services.ConvertOptions
import com.beadsnap.app.services.PhotoStudio
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder

/** Set with -Dfixture=DIR; defaults to the prepare_fixture.py default. */
private fun fixtureDir(): String = System.getProperty("fixture") ?: "/tmp/kcheck"


private fun studio(w: Int, h: Int): PhotoStudio {
    val bytes = File(fixtureDir(), "photo.argb").readBytes()
    val ib = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).asIntBuffer()
    val px = IntArray(w * h); ib.get(px)
    return PhotoStudio.from(Bitmap.createBitmap(px, w, h, Bitmap.Config.ARGB_8888), 384)
}

private fun ms(n: Int, body: () -> Unit): Double {
    repeat(5) { body() }                       // warm the JIT
    val t0 = System.nanoTime()
    repeat(n) { body() }
    return (System.nanoTime() - t0) / 1e6 / n
}

fun main() {
    val w = 288; val h = 384
    val raw = File(fixtureDir(), "mask.u8").readBytes()
    val mask = BooleanArray(w * h) { raw[it].toInt() != 0 }

    for (n in intArrayOf(16, 24, 32, 48)) {
        val s = studio(w, h)
        s.adoptMask(mask, w, h)
        val crop = s.subjectCrop(n, n)!!
        val o = ConvertOptions(maxColors = 16)

        // Cold: every cell invalid (what a slider move costs).
        var flip = 0
        val cold = ms(20) {
            s.configure(n, n, crop, o.copy(maxColors = if (flip++ % 2 == 0) 16 else 15),
                        PegboardShape.square)
            s.buildPattern("b")
        }
        // Warm: only the cells under a brush changed (what a finger costs).
        s.configure(n, n, crop, o, PegboardShape.square)
        s.buildPattern("b")
        var t = 0
        val warm = ms(60) {
            s.brush(0.4f + (t % 7) * 0.02f, 0.4f + (t % 5) * 0.02f, 0.03f, t++ % 2 == 0)
            s.buildPattern("b")
        }
        val preview = ms(20) { s.photoPreview(null) }
        println(String.format(
            "%2dx%-2d  slider(full rebuild) %6.1f ms   brush(incremental) %6.1f ms   photo preview %5.1f ms",
            n, n, cold, warm, preview))
    }

    // Where does the full rebuild's time actually go?
    val s = studio(w, h); s.adoptMask(mask, w, h)
    val crop = s.subjectCrop(48, 48)!!
    s.configure(48, 48, crop, ConvertOptions(maxColors = 16), PegboardShape.square)
    s.buildPattern("b")
    println("grey-world scan: " + String.format("%.2f ms", ms(50) { s.measureGreyWorld() }))
    println("subject crop scan: " + String.format("%.2f ms", ms(50) { s.subjectCrop(48, 48) }))
    println("BENCH DONE")
}
