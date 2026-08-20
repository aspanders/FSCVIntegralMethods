package com.beadsnap.app.data.model

import kotlinx.serialization.Serializable

@Serializable
data class FusePattern(
    val id: String,
    var title: String,
    val category: PatternCategory = PatternCategory.custom,
    var createdBy: CreatorType = CreatorType.user,
    val grid: GridSize = GridSize.large,
    val palette: List<BeadColor> = emptyList(),
    val cells: List<Cell> = emptyList(),
    val difficulty: Difficulty = Difficulty.easy,
    val tags: List<String> = emptyList(),
    val sourcePrompt: String? = null,
    // 3D constructions include how to make the bead panel(s) and how to
    // assemble them into the finished object. Null for flat patterns.
    val buildGuide: String? = null,
    val assemblyGuide: String? = null,
    // Compact wire form: one string per grid row, each char = palette index
    // ('.' = empty). Present only in the shipped library; expanded to `cells`
    // on load via materialized(). Kept out of the in-memory pattern afterward.
    val rows: List<String>? = null,
    // Reduced versions of the same design, keyed "small"/"medium", each in the
    // same compact rows encoding and indexing the same palette. Built offline
    // (tools/library/scaling.py) rather than resampled here, because a reduced
    // board still has to be weldable: loose parts get re-welded and thin necks
    // re-widened at the smaller size, which is not something to redo on the
    // phone in two languages.
    val sizes: Map<String, PatternSize>? = null,
    // Which pegboard the pattern is built on. Defaults to `square`, so every
    // pattern written before this field existed (including the whole shipped
    // library/patterns.json) decodes unchanged.
    val shape: PegboardShape = PegboardShape.square,
    var version: Int = 1
) {
    val totalBeads: Int get() = cells.count { it.colorId != null }

    val hasInstructions: Boolean get() = !buildGuide.isNullOrBlank() || !assemblyGuide.isNullOrBlank()

    /** Expand the compact `rows` encoding into `cells` (no-op if already cells). */
    fun materialized(): FusePattern {
        val r = rows
        if (r == null || cells.isNotEmpty()) return if (rows == null) this else copy(rows = null)
        val expanded = ArrayList<Cell>()
        for (y in r.indices) {
            val row = r[y]
            for (x in row.indices) {
                val ch = row[x]
                if (ch == '.') continue
                val i = CHARS.indexOf(ch)
                if (i in palette.indices) expanded.add(Cell(x, y, palette[i].id))
            }
        }
        return copy(cells = expanded, rows = null)
    }

    /** The boards this design can be built on, smallest first. */
    fun scales(): List<BoardScale> =
        BoardScale.entries.filter { it == BoardScale.large || sizes?.containsKey(it.key) == true }

    /**
     * The same design on one of its other boards.
     *
     * A new id, because a small build and a large build of the same subject are
     * two different projects and must not overwrite each other's progress. The
     * palette is carried over whole so the reduced rows keep indexing it.
     */
    fun atScale(scale: BoardScale): FusePattern {
        if (scale == BoardScale.large) return materialized()
        val v = sizes?.get(scale.key) ?: return materialized()
        val expanded = ArrayList<Cell>()
        for (y in v.rows.indices) {
            val row = v.rows[y]
            for (x in row.indices) {
                val ch = row[x]
                if (ch == '.') continue
                val i = CHARS.indexOf(ch)
                if (i in palette.indices) expanded.add(Cell(x, y, palette[i].id))
            }
        }
        return copy(
            id    = "$id-${scale.key}",
            title = "$title (${scale.label})",
            grid  = GridSize(v.width, v.height),
            cells = expanded,
            rows  = null,
            sizes = null
        )
    }

    fun colorCounts(): List<Pair<BeadColor, Int>> {
        val counts = mutableMapOf<String, Int>()
        cells.forEach { cell -> cell.colorId?.let { counts[it] = (counts[it] ?: 0) + 1 } }
        return palette
            .mapNotNull { color -> counts[color.id]?.let { color to it } }
            .sortedByDescending { it.second }
    }

    fun colorIdAt(x: Int, y: Int): String? =
        cells.firstOrNull { it.x == x && it.y == y }?.colorId

    fun colorAt(x: Int, y: Int): BeadColor? {
        val id = colorIdAt(x, y) ?: return null
        return palette.firstOrNull { it.id == id }
    }

    companion object {
        // Palette-index charset for the compact `rows` encoding.
        // Keep in sync with tools/library/compact.py and the iOS model.
        const val CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    }
}

@Serializable
// The icon property is named `symbol`, not `emoji`, because one of the entries
// is itself called `emoji` and an entry cannot share a name with a property.
enum class PatternCategory(val displayName: String, val symbol: String) {
    // 23 content categories (100 patterns each) + 3D specialty + user designs.
    geometric("Geometric", "🔷"),
    mandalas("Mandalas", "🌀"),
    hearts("Hearts", "💗"),
    stars("Stars", "⭐"),
    flowers("Flowers", "🌸"),
    rainbows("Rainbows", "🌈"),
    space("Space", "🚀"),
    emoji("Emoji", "😊"),
    gems("Gems", "💎"),
    icons("Icons", "🔤"),
    animals("Animals", "🐾"),
    birds("Birds", "🐦"),
    fish("Fish", "🐟"),
    bugs("Bugs", "🐛"),
    food("Food", "🍎"),
    sweets("Sweets", "🍬"),
    trees("Trees", "🌳"),
    vehicles("Vehicles", "🚗"),
    snowflakes("Snowflakes", "❄️"),
    holidays("Holidays", "🎁"),
    videogame("Video Game", "🎮"),
    sports("Sports", "⚽"),
    circles("Circles", "⭕"),
    threeD("3D", "🧊"),
    custom("My Designs", "✏️")
}

/**
 * The physical pegboard a pattern is pegged out on.
 *
 * A round pegboard is not a different lattice - the pegs still sit on the same
 * square pitch - it is the square lattice clipped to a disc, which is why this
 * is a mask over the existing grid rather than a second coordinate system.
 * Cells outside the disc simply do not exist: they are not drawn, not painted,
 * not sampled from the photo, and not exported.
 */
@Serializable
enum class PegboardShape(val displayName: String) {
    square("Square"),
    circle("Circle");

    /** Is cell (x, y) a real peg on a [cols] x [rows] board of this shape? */
    fun contains(x: Int, y: Int, cols: Int, rows: Int): Boolean = when (this) {
        square -> x in 0 until cols && y in 0 until rows
        circle -> {
            if (x !in 0 until cols || y !in 0 until rows) false
            else {
                val r = minOf(cols, rows) / 2.0
                val dx = x + 0.5 - cols / 2.0
                val dy = y + 0.5 - rows / 2.0
                dx * dx + dy * dy <= r * r
            }
        }
    }
}

@Serializable
enum class CreatorType { system, user, ai }

/** One reduced board for a pattern, in the same compact encoding as `rows`. */
@Serializable
data class PatternSize(val width: Int, val height: Int, val rows: List<String>)

/**
 * Which of a pattern's boards to build. `large` is the pattern as designed;
 * the others come from its `sizes` map and are only offered when they exist.
 */
enum class BoardScale(val key: String, val label: String) {
    small("small", "Small"),
    medium("medium", "Medium"),
    large("large", "Large")
}

@Serializable
data class GridSize(val width: Int, val height: Int) {
    val displayName: String get() = "${width}×${height}"

    companion object {
        val small  = GridSize(16, 16)
        val medium = GridSize(24, 24)
        val large  = GridSize(32, 32)
        val xlarge = GridSize(48, 48)
    }
}

@Serializable
data class Cell(val x: Int, val y: Int, val colorId: String? = null)

@Serializable
enum class Difficulty(val displayName: String, val emoji: String) {
    easy("Easy", "🟢"),
    medium("Medium", "🟡"),
    hard("Hard", "🔴")
}
