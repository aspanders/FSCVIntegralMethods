import android.graphics.Bitmap
import android.graphics.Rect
import com.beadsnap.app.data.model.GridSize
import com.beadsnap.app.data.model.PegboardShape
import com.beadsnap.app.services.ConvertOptions
import com.beadsnap.app.services.ImageConverter
import com.beadsnap.app.services.PhotoStudio
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder

/** Set with -Dfixture=DIR; defaults to the prepare_fixture.py default. */
private fun fixtureDir(): String = System.getProperty("fixture") ?: "/tmp/kcheck"


/**
 * The live preview and the committed pattern must be the same function of the
 * same pixels. Fed an identical bitmap, crop and options, PhotoStudio and
 * ImageConverter should produce identical boards.
 */
fun main() {
    val w = 288; val h = 384
    val bytes = File(fixtureDir(), "photo.argb").readBytes()
    val ib = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).asIntBuffer()
    val px = IntArray(w * h); ib.get(px)
    val raw = File(fixtureDir(), "mask.u8").readBytes()

    // Apply the mask to the bitmap itself, so the converter sees the same
    // transparency the studio sees through its keep-mask.
    val masked = IntArray(w * h) { if (raw[it].toInt() != 0) px[it] else px[it] and 0x00FFFFFF }

    var failures = 0
    for ((tag, shape) in listOf("square" to PegboardShape.square, "circle" to PegboardShape.circle)) {
        for (n in intArrayOf(16, 32, 48)) {
            for (useMask in booleanArrayOf(false, true)) {
                for (gains in listOf(
                    ConvertOptions.NEUTRAL_GAINS, floatArrayOf(0.87f, 1.04f, 1.21f)
                )) {
                    val src = if (useMask) masked else px
                    val bmp = Bitmap.createBitmap(src, w, h, Bitmap.Config.ARGB_8888)

                    val studio = PhotoStudio.from(bmp, 384)
                    if (useMask) studio.adoptMask(BooleanArray(w * h) { raw[it].toInt() != 0 }, w, h)
                    val crop: Rect? = null
                    val opts = ConvertOptions(
                        maxColors = 14, shape = shape, whiteBalance = gains,
                        brightness = 0.1f, contrast = -0.15f, saturation = 0.2f, chromaLift = 1.3f
                    )
                    studio.configure(n, n, crop, opts, shape)
                    val a = studio.buildPattern("x")
                    val b = ImageConverter.convert(bmp, GridSize(n, n), opts)

                    val ga = HashMap<Int, String>(); a.cells.forEach { c -> c.colorId?.let { ga[c.y * n + c.x] = it } }
                    val gb = HashMap<Int, String>(); b.cells.forEach { c -> c.colorId?.let { gb[c.y * n + c.x] = it } }
                    val same = ga == gb
                    if (!same) {
                        failures++
                        val diff = (ga.keys + gb.keys).count { ga[it] != gb[it] }
                        println("MISMATCH $tag n=$n mask=$useMask wb=${gains[2]}: " +
                                "${a.totalBeads} vs ${b.totalBeads} beads, $diff cells differ")
                    }
                }
            }
        }
    }
    println(if (failures == 0) "CROSS-CHECK: studio == converter on all 24 configurations"
            else "CROSS-CHECK FAILED: $failures configurations")
}
