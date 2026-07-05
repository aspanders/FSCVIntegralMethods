package com.beadsnap.app.data.model

import org.junit.Assert.*
import org.junit.Test

class BeadColorTest {

    @Test
    fun `palette has at least 20 colors`() {
        assertTrue("Expected >= 20 colors", BeadColor.palette.size >= 20)
    }

    @Test
    fun `all palette ids are unique`() {
        val ids = BeadColor.palette.map { it.id }
        assertEquals("Duplicate palette IDs found", ids.size, ids.toSet().size)
    }

    @Test
    fun `paletteById map covers all palette colors`() {
        BeadColor.palette.forEach { color ->
            assertNotNull("paletteById missing ${color.id}", BeadColor.paletteById[color.id])
        }
    }

    @Test
    fun `defaultPalette is a subset of full palette`() {
        val allIds = BeadColor.palette.map { it.id }.toSet()
        BeadColor.defaultPalette.forEach { color ->
            assertTrue("${color.id} in defaultPalette not found in full palette", allIds.contains(color.id))
        }
    }

    @Test
    fun `distanceTo returns 0 for same color`() {
        val red = BeadColor.palette.first()
        assertEquals(0.0, red.distanceTo(red), 0.001)
    }

    @Test
    fun `distanceTo is symmetric`() {
        val c1 = BeadColor.palette[0]
        val c2 = BeadColor.palette[1]
        assertEquals(c1.distanceTo(c2), c2.distanceTo(c1), 0.001)
    }

    @Test
    fun `nearest returns self when palette only has one entry`() {
        val color = BeadColor.palette.first()
        val nearest = BeadColor.palette.minByOrNull { color.distanceTo(it) }
        assertEquals(color.id, nearest?.id)
    }
}
