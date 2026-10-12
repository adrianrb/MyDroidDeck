package com.mydroiddeck.app.ui

import com.mydroiddeck.app.model.ActionResult
import com.mydroiddeck.app.model.DeckButton
import com.mydroiddeck.app.model.DeckProfile
import org.junit.Assert.assertEquals
import org.junit.Assert.assertSame
import org.junit.Test

class DeckStateTest {

    private fun buttons(vararg actions: String): List<DeckButton> =
        actions.mapIndexed { index, action -> DeckButton(index, action, action) }

    @Test
    fun mapsServerAcknowledgementToStatus() {
        assertEquals(DeckStatus.SENT, statusOf(ActionResult(status = "ok", action = "a")))
        assertEquals(DeckStatus.UNKNOWN, statusOf(ActionResult(status = "unknown", action = "a")))
    }

    @Test
    fun mapsFailedDispatchToFailedStatus() {
        assertEquals(DeckStatus.FAILED, statusOf(ActionResult(status = "failed", action = "a")))
        assertEquals(DeckStatus.FAILED, statusOf(ActionResult(status = "timeout", action = "a")))
    }

    @Test
    fun firstProfileIndexIsNegativeWhenEmpty() {
        assertEquals(-1, firstProfileIndex(emptyList()))
        assertEquals(0, firstProfileIndex(listOf(DeckProfile("principal", "pt_BR"))))
    }

    @Test
    fun cycleWrapsAroundBothWays() {
        assertEquals(1, cycleProfileIndex(0, 3, 1))
        assertEquals(2, cycleProfileIndex(0, 3, -1))
        assertEquals(0, cycleProfileIndex(2, 3, 1))
        assertEquals(-1, cycleProfileIndex(0, 0, 1))
    }

    @Test
    fun swapButtons_swapsPositionsAndReindexes() {
        val swapped = swapButtons(buttons("a", "b", "c", "d"), from = 1, to = 2)
        assertEquals(listOf("a", "c", "b", "d"), swapped.map { it.action })
        assertEquals(listOf(0, 1, 2, 3), swapped.map { it.index })
    }

    @Test
    fun swapButtons_isSymmetric() {
        assertEquals(
            swapButtons(buttons("a", "b", "c", "d"), from = 0, to = 3).map { it.action },
            swapButtons(buttons("a", "b", "c", "d"), from = 3, to = 0).map { it.action },
        )
    }

    @Test
    fun swapButtons_ignoresOutOfRangeOrIdenticalIndexes() {
        val original = buttons("a", "b", "c")
        assertSame(original, swapButtons(original, from = -1, to = 2))
        assertSame(original, swapButtons(original, from = 0, to = 9))
        assertSame(original, swapButtons(original, from = 1, to = 1))
    }
}
