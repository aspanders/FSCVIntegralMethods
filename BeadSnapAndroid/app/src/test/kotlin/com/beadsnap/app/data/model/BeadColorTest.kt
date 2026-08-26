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

    // ─── hex parsing ─────────────────────────────────────────────────────────
    // These three assertions are why BeadColor no longer imports
    // android.graphics.Color. It used parseColor for this, which made every
    // colour calculation in the app unreachable from a JVM unit test: the real
    // android.jar throws RuntimeException("Stub!") from every method, so
    // `distanceTo` - pure arithmetic - failed on a device-only dependency.

    @Test
    fun `six-digit hex parses to opaque ARGB`() {
        assertEquals(0xFFFFFDD0.toInt(), BeadColor.parseHex("#FFFDD0"))
        assertEquals(0xFF000000.toInt(), BeadColor.parseHex("#000000"))
        assertEquals(0xFFFFFFFF.toInt(), BeadColor.parseHex("#FFFFFF"))
    }

    @Test
    fun `channels land in the right byte`() {
        val c = BeadColor.parseHex("#123456")
        assertEquals(0x12, (c shr 16) and 0xFF)
        assertEquals(0x34, (c shr 8) and 0xFF)
        assertEquals(0x56, c and 0xFF)
    }

    @Test
    fun `shorthand and alpha forms are accepted`() {
        assertEquals(BeadColor.parseHex("#FFFFFF"), BeadColor.parseHex("#FFF"))
        assertEquals(0x80FF0000.toInt(), BeadColor.parseHex("#80FF0000"))
    }

    @Test
    fun `the leading hash is optional`() {
        assertEquals(BeadColor.parseHex("#FFFDD0"), BeadColor.parseHex("FFFDD0"))
    }

    @Test(expected = IllegalArgumentException::class)
    fun `a malformed hex is rejected rather than silently wrong`() {
        BeadColor.parseHex("#FFFD")
    }

    @Test
    fun `every shipped palette colour parses`() {
        // A bad hex anywhere in the palette would otherwise surface as one
        // wrong bead colour in a finished pattern, which is very hard to spot.
        for (c in BeadColor.palette) {
            val argb = BeadColor.parseHex(c.hex)
            assertEquals("${c.id} must be opaque", 0xFF, (argb shr 24) and 0xFF)
        }
    }
}
