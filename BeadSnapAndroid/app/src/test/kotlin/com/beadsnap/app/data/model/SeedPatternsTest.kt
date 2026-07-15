package com.beadsnap.app.data.model

import org.junit.Assert.*
import org.junit.Test

class SeedPatternsTest {

    @Test
    fun `all seed patterns have non-blank titles`() {
        SeedPatterns.all.forEach { p ->
            assertTrue("Pattern ${p.id} has blank title", p.title.isNotBlank())
        }
    }

    @Test
    fun `all seed patterns are marked as system`() {
        SeedPatterns.all.forEach { p ->
            assertEquals("Pattern ${p.title} should be CreatorType.system",
                CreatorType.system, p.createdBy)
        }
    }

    @Test
    fun `all seed pattern cells are within grid bounds`() {
        SeedPatterns.all.forEach { pattern ->
            pattern.cells.forEach { cell ->
                assertTrue("Cell (${cell.x},${cell.y}) out of bounds in '${pattern.title}'",
                    cell.x >= 0 && cell.x < pattern.grid.width &&
                    cell.y >= 0 && cell.y < pattern.grid.height)
            }
        }
    }

    @Test
    fun `no seed pattern has duplicate cell positions`() {
        SeedPatterns.all.forEach { pattern ->
            val positions = pattern.cells.map { "${it.x},${it.y}" }
            val unique = positions.toSet()
            assertEquals("Pattern '${pattern.title}' has duplicate cells",
                unique.size, positions.size)
        }
    }

    @Test
    fun `all palette color ids referenced in cells exist in the pattern palette`() {
        SeedPatterns.all.forEach { pattern ->
            val paletteIds = pattern.palette.map { it.id }.toSet()
            pattern.cells.forEach { cell ->
                val id = cell.colorId ?: return@forEach
                assertTrue("Pattern '${pattern.title}' cell references unknown color '$id'",
                    paletteIds.contains(id))
            }
        }
    }

    @Test
    fun `seed library has at least 10 patterns`() {
        assertTrue("Expected >= 10 seed patterns, got ${SeedPatterns.all.size}",
            SeedPatterns.all.size >= 10)
    }
}
