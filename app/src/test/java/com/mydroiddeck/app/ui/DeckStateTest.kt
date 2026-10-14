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
    fun profileIndexByName_keepsTheProfileTheUserPicked() {
        val deck = listOf(DeckProfile("Sistema", "pt_BR"), DeckProfile("Utilidades", "pt_BR"))
        assertEquals(1, profileIndexByName(deck, "Utilidades"))
        // Rotation recreates the screen and reloads the same list: still the picked one.
        assertEquals(1, profileIndexByName(deck, "Utilidades"))
    }

    @Test
    fun profileIndexByName_fallsBackToTheFirstProfile() {
        val deck = listOf(DeckProfile("Sistema", "pt_BR"), DeckProfile("Utilidades", "pt_BR"))
        assertEquals(0, profileIndexByName(deck, ""))          // nothing picked yet
        assertEquals(0, profileIndexByName(deck, "Jogos"))     // profile renamed/removed
        assertEquals(-1, profileIndexByName(emptyList(), "Sistema"))
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

    @Test
    fun deckKeepsThePortraitKeySizeWhenRotated() {
        // Phone: 352dp of grid in portrait -> 4 keys of 88dp.
        assertEquals(4, deckColumnCount(availableWidthDp = 352f, portraitWidthDp = 352f))
        // Same screen rotated: 792dp fits 9 columns of the very same 88dp.
        assertEquals(9, deckColumnCount(availableWidthDp = 792f, portraitWidthDp = 352f))
        assertEquals(
            352f / deckColumnCount(352f, 352f),
            792f / deckColumnCount(792f, 352f),
            0.001f,
        )
    }

    @Test
    fun deckShowsFourColumnsOnANarrowOrSquareScreen() {
        assertEquals(4, deckColumnCount(availableWidthDp = 312f, portraitWidthDp = 312f))
        assertEquals(4, deckColumnCount(availableWidthDp = 792f, portraitWidthDp = 792f))
        assertEquals(4, deckColumnCount(availableWidthDp = 0f, portraitWidthDp = 0f))
    }

    @Test
    fun deckGainsAColumnInsteadOfStretchingTheKeys() {
        // A phone with 403dp of grid: 403/4 = 100.75dp keys. Rotated, 910dp nearly
        // fits 9 of them -> 9 (a hair smaller) rather than 8 stretched to 113dp.
        assertEquals(4, deckColumnCount(availableWidthDp = 403f, portraitWidthDp = 403f))
        assertEquals(9, deckColumnCount(availableWidthDp = 910f, portraitWidthDp = 403f))
        assertEquals(403f / 4f, 910f / 9f, 0.5f)
    }

    @Test
    fun deckFitsMoreColumnsOnATabletInLandscape() {
        // 800x1280 tablet: portrait 4 keys of 198dp; landscape shows 6 of them (7 would
        // shrink the keys to 181dp, further from the portrait size).
        assertEquals(6, deckColumnCount(availableWidthDp = 1272f, portraitWidthDp = 792f))
    }
}
