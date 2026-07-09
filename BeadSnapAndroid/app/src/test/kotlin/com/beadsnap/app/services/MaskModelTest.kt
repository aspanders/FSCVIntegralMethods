package com.beadsnap.app.services

import org.junit.Assert.*
import org.junit.Test

class MaskModelTest {

    @Test
    fun `mask starts as keep-everything`() {
        val m = MaskModel(4, 4)
        assertTrue(m.keep.all { it })
    }

    @Test
    fun `brush removes a circle and add-back restores it`() {
        val m = MaskModel(20, 20)
        m.brush(10, 10, radius = 3, keepValue = false)
        assertFalse(m.keep[10 * 20 + 10])          // center removed
        assertFalse(m.keep[10 * 20 + 12])          // within radius
        assertTrue(m.keep[10 * 20 + 14])           // outside radius untouched
        m.brush(10, 10, radius = 3, keepValue = true)
        assertTrue(m.keep.all { it })              // fully restored
    }

    @Test
    fun `brush near the edge is clipped, not crashing`() {
        val m = MaskModel(8, 8)
        m.brush(0, 0, radius = 5, keepValue = false)
        m.brush(7, 7, radius = 5, keepValue = false)
        assertFalse(m.keep[0])
        assertFalse(m.keep[7 * 8 + 7])
    }

    @Test
    fun `setAll replaces the mask contents`() {
        val m = MaskModel(2, 2)
        m.setAll(booleanArrayOf(false, true, false, true))
        assertFalse(m.keep[0]); assertTrue(m.keep[1])
        assertFalse(m.keep[2]); assertTrue(m.keep[3])
    }

    @Test(expected = IllegalArgumentException::class)
    fun `setAll rejects wrong-size input`() {
        MaskModel(2, 2).setAll(booleanArrayOf(true))
    }
}
