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
}