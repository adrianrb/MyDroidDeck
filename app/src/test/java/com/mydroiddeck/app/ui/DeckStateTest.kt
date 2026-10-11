package com.mydroiddeck.app.ui

import com.mydroiddeck.app.model.ActionResult
import com.mydroiddeck.app.model.DeckProfile
import org.junit.Assert.assertEquals
import org.junit.Test

class DeckStateTest {

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
}
