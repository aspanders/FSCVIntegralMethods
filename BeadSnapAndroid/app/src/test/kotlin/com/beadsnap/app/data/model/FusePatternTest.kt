package com.beadsnap.app.data.model

import org.junit.Assert.*
import org.junit.Test

class FusePatternTest {

    private val color1 = BeadColor.defaultPalette[0]
    private val color2 = BeadColor.defaultPalette[1]

    private fun pattern(cells: List<Cell> = emptyList()) = FusePattern(
        id      = "test-id",
        title   = "Test",
        grid    = GridSize.small,
        palette = BeadColor.defaultPalette,
        cells   = cells
    )

    @Test
    fun `totalBeads counts only non-null colorId cells`() {
        val cells = listOf(
            Cell(0, 0, color1.id),
            Cell(1, 0, null),
            Cell(2, 0, color2.id)
        )
        assertEquals(2, pattern(cells).totalBeads)
    }

    @Test
    fun `totalBeads is zero for empty grid`() {
        assertEquals(0, pattern().totalBeads)
    }

    @Test
    fun `colorCounts groups cells by colorId correctly`() {
        val cells = listOf(
            Cell(0, 0, color1.id),
            Cell(1, 0, color1.id),
            Cell(2, 0, color2.id)
        )
        val counts = pattern(cells).colorCounts()
        val countMap = counts.associate { (color, count) -> color.id to count }
        assertEquals(2, countMap[color1.id])
        assertEquals(1, countMap[color2.id])
    }

    @Test
    fun `colorCounts returns empty list when no cells placed`() {
        assertTrue(pattern().colorCounts().isEmpty())
    }

    @Test
    fun `colorCounts is sorted descending by count`() {
        val cells = listOf(
            Cell(0, 0, color2.id),
            Cell(1, 0, color1.id),
            Cell(2, 0, color1.id),
            Cell(3, 0, color1.id)
        )
        val counts = pattern(cells).colorCounts()
        assertTrue(counts.size >= 2)
        // First element should have highest count
        assertTrue(counts[0].second >= counts[1].second)
    }

    @Test
    fun `colorAt returns correct color for placed bead`() {
        val cells = listOf(Cell(3, 5, color1.id))
        val p = pattern(cells)
        assertEquals(color1.id, p.colorAt(3, 5)?.id)
    }

    @Test
    fun `colorAt returns null for empty cell`() {
        assertNull(pattern().colorAt(0, 0))
    }

    @Test
    fun `FusePattern copy preserves all fields except overridden`() {
        val original = pattern()
        val copy = original.copy(title = "Copy")
        assertEquals("Copy", copy.title)
        assertEquals(original.id, copy.id)
        assertEquals(original.grid, copy.grid)
        assertEquals(original.palette, copy.palette)
    }
}
