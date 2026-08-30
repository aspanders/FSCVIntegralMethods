import android.graphics.Bitmap
import android.graphics.Rect
import com.beadsnap.app.services.ImageConverter
import com.beadsnap.app.services.PhotoStudio
import kotlin.math.abs

/**
 * The crop has to match the board, or the picture is stretched onto it.
 *
 * Every board this app offers is square, so a crop of any other shape is
 * sampled onto a square grid and one axis is squashed. That shipped: the
 * subject crop grew its box to the board's ratio and then clamped each edge
 * into the photo separately, which threw the ratio away again for any subject
 * near an edge - and for EVERY tall portrait photo, because the grown box is
 * wider than the frame. Fitting to the subject is on by default, so the default
 * path was the broken one.
 *
 * A reviewer cannot see that by reading; the clamp looks like ordinary bounds
 * safety. So it is checked here, over subjects placed all round the frame, on
 * both portrait and landscape sources.
 */

private var failures = 0

private fun check(name: String, ok: Boolean, detail: String = "") {
    println("  " + (if (ok) "PASS" else "FAIL") + "  " + name +
        (if (ok || detail.isEmpty()) "" else " - " + detail))
    if (!ok) failures++
}

/** A studio over a blank photo, with `box` marked as the kept subject. */
private fun studioWithSubject(w: Int, h: Int, box: Rect): PhotoStudio {
    val px = IntArray(w * h) { 0xFF808080.toInt() }
    val studio = PhotoStudio.from(Bitmap.createBitmap(px, w, h, Bitmap.Config.ARGB_8888), maxOf(w, h))
    val mask = BooleanArray(w * h)
    for (y in box.top until box.bottom) {
        for (x in box.left until box.right) mask[y * w + x] = true
    }
    studio.adoptMask(mask, w, h)
    return studio
}

private fun aspect(r: Rect): Double = r.width().toDouble() / r.height()

fun main() {
    println("==> crop keeps the board's shape")

    // Portrait and landscape sources, and a subject in the middle, hard against
    // each edge, and in a corner. The edge and corner cases are the ones the
    // old clamp mangled.
    val sources = listOf(288 to 384, 384 to 288, 300 to 300)
    var worst = 0.0
    var worstWhere = ""

    for ((w, h) in sources) {
        val boxes = mapOf(
            "centre" to Rect(w / 3, h / 3, 2 * w / 3, 2 * h / 3),
            "tall centre" to Rect(w / 3, 8, 2 * w / 3, h - 8),
            "wide centre" to Rect(8, h / 3, w - 8, 2 * h / 3),
            "top-left corner" to Rect(0, 0, w / 3, h / 3),
            "bottom-right corner" to Rect(2 * w / 3, 2 * h / 3, w, h),
            "full frame" to Rect(0, 0, w, h),
            "sliver at the left edge" to Rect(0, h / 2 - 10, 12, h / 2 + 10)
        )
        for ((where, box) in boxes) {
            val studio = studioWithSubject(w, h, box)
            for ((cols, rows) in listOf(16 to 16, 32 to 32, 48 to 48)) {
                val crop = studio.subjectCrop(cols, rows)
                if (crop == null) {
                    check("$where on ${w}x$h returns a crop", false, "got null")
                    continue
                }
                val want = cols.toDouble() / rows
                val err = abs(aspect(crop) - want) / want
                if (err > worst) { worst = err; worstWhere = "$where on ${w}x$h at ${cols}x$rows" }
                check(
                    "$where, ${w}x$h -> ${cols}x$rows board",
                    err <= 0.02 &&
                        crop.left >= 0 && crop.top >= 0 &&
                        crop.right <= w && crop.bottom <= h &&
                        crop.width() > 0 && crop.height() > 0,
                    "crop ${crop.width()}x${crop.height()} = aspect %.3f, wanted %.3f".format(
                        aspect(crop), want)
                )
            }
        }
    }
    println("  worst aspect error %.4f%% (%s)".format(worst * 100, worstWhere))

    // The no-subject path has always been right; keep it that way.
    println("==> the plain aspect crop, for comparison")
    for ((w, h) in sources) {
        for ((cols, rows) in listOf(16 to 16, 32 to 32)) {
            val r = ImageConverter.aspectCrop(w, h, cols, rows)
            val want = cols.toDouble() / rows
            check(
                "aspectCrop ${w}x$h -> ${cols}x$rows",
                abs(aspect(r) - want) / want <= 0.02 &&
                    r.width() <= w && r.height() <= h && r.left >= 0 && r.top >= 0,
                "got ${r.width()}x${r.height()}"
            )
        }
    }

    // fitAspect is now the single implementation behind both the automatic
    // subject crop and the crop the user drags, so it is checked directly:
    // a box far bigger than the photo, one far smaller, and one pinned to a
    // corner all have to come back the board's shape and inside the frame.
    println("==> fitAspect, the one place the shape is enforced")
    for ((w, h) in sources) {
        val cases = listOf(
            "huge box" to listOf(w / 2, h / 2, w * 4, h * 4),
            "tiny box" to listOf(w / 2, h / 2, 3, 3),
            "off the top-left" to listOf(-50, -50, w, h),
            "off the bottom-right" to listOf(w + 50, h + 50, w, h),
            "tall and thin" to listOf(w / 2, h / 2, 5, h),
            "short and wide" to listOf(w / 2, h / 2, w, 5)
        )
        for ((name, v) in cases) {
            for ((cols, rows) in listOf(16 to 16, 32 to 32)) {
                val r = ImageConverter.fitAspect(v[0], v[1], v[2], v[3], w, h, cols, rows)
                val want = cols.toDouble() / rows
                check(
                    "fitAspect $name on ${w}x$h",
                    abs(aspect(r) - want) / want <= 0.02 &&
                        r.left >= 0 && r.top >= 0 && r.right <= w && r.bottom <= h &&
                        r.width() > 0 && r.height() > 0,
                    "got ${r.left},${r.top} ${r.width()}x${r.height()}"
                )
            }
        }
    }

    println(if (failures == 0) "crop checks pass" else "$failures FAILED")
    if (failures > 0) kotlin.system.exitProcess(1)
}
