package com.mydroiddeck.app.model

import com.google.gson.Gson
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Guards the Gson field mapping agreed with the server (snake_case JSON). */
class DtosTest {

    private val gson = Gson()

    @Test
    fun pairResponse_mapsSnakeCaseFields() {
        val parsed = gson.fromJson(
            """{"token":"abc","device_id":7,"name":"deck"}""",
            PairResponse::class.java,
        )
        assertEquals("abc", parsed.token)
        assertEquals(7, parsed.deviceId)
        assertEquals("deck", parsed.name)
    }

    @Test
    fun pairRequest_serializesDeviceNameField() {
        val json = gson.toJson(PairRequest(code = "pair-dev", deviceName = "meu deck"))
        assertTrue(json.contains("\"device_name\":\"meu deck\""))
        assertTrue(json.contains("\"code\":\"pair-dev\""))
    }

    @Test
    fun actionResult_mapsExecutedAt() {
        val parsed = gson.fromJson(
            """{"status":"ok","action":"obs.scene","executed_at":"2026-01-01T00:00:00Z"}""",
            ActionResult::class.java,
        )
        assertEquals("2026-01-01T00:00:00Z", parsed.executedAt)
    }

    @Test
    fun deckProfile_mapsServerIdAndSerializesThePutBody() {
        // The server includes an id on the profile (and on each button, ignored here).
        val parsed = gson.fromJson(
            """{"id":3,"name":"Deck","locale":"pt_BR","buttons":""" +
                """[{"id":9,"index":1,"label":"Play","action":"spotify.play"}]}""",
            DeckProfile::class.java,
        )
        assertEquals(3L, parsed.id)
        assertEquals("spotify.play", parsed.buttons[0].action)

        // Reorder round-trip: the full profile is PUT back with the new order.
        val json = gson.toJson(
            DeckProfile(
                name = "Deck",
                locale = "pt_BR",
                buttons = listOf(DeckButton(1, "Play", "spotify.play")),
                id = 3,
            ),
        )
        assertTrue(json.contains("\"id\":3"))
        assertTrue(json.contains("\"action\":\"spotify.play\""))
    }
}