package com.mydroiddeck.app.model

import org.junit.Assert.assertEquals
import org.junit.Test

class DeckProfileTest {

    @Test
    fun keepsButtonsInOrder() {
        val profile = DeckProfile(
            name = "Deck principal",
            locale = "pt_BR",
            buttons = listOf(
                DeckButton(0, "Cena inicial", "obs.scene.iniciar"),
                DeckButton(1, "Play", "spotify.play"),
            ),
        )

        assertEquals(2, profile.buttons.size)
        assertEquals("Cena inicial", profile.buttons[0].label)
        assertEquals("spotify.play", profile.buttons[1].action)
    }

    @Test
    fun defaultsToEmptyButtons() {
        assertEquals(0, DeckProfile("vazio", "pt_BR").buttons.size)
    }
}
