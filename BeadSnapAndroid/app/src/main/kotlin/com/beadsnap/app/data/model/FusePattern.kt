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
    var version: Int = 1
) {
    val totalBeads: Int get() = cells.count { it.colorId != null }

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
}

@Serializable
enum class PatternCategory(val displayName: String, val emoji: String) {
    animals("Animals", "🐾"),
    fantasy("Fantasy", "🔮"),
    vehicles("Vehicles", "🚀"),
    nature("Nature", "🌿"),
    icons("Icons", "⭐"),
    holidays("Holidays", "🎉"),
    custom("My Designs", "✏️")
}

@Serializable
enum class CreatorType { system, user, ai }

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
