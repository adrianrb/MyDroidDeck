package com.mydroiddeck.app.net

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * A-19: pairing QR payload (`mydroiddeck://pair?url=…&code=…`), as printed by the
 * server's Dispositivos → Parear novo page.
 *
 * The literals here mirror what `server/app/core/qr.py::pairing_uri` produces
 * (and what `server/tests/test_pairing_qr.py` decodes back), so the two sides
 * stay in sync.
 */
class PairingQrTest {

    @Test
    fun parsesTheServerPayload() {
        val parsed = parsePairingQr(
            "mydroiddeck://pair?url=http%3A%2F%2F192.168.100.7%3A56997%2F&code=pair-dev"
        )
        assertEquals(PairingQr("http://192.168.100.7:56997/", "pair-dev"), parsed)
    }

    @Test
    fun trimsAndNormalizesTheEncodedUrl() {
        // The server already normalizes, but a hand-made code may not.
        val parsed = parsePairingQr("mydroiddeck://pair?url=192.168.0.10%3A56997&code=abc")
        assertEquals(PairingQr("http://192.168.0.10:56997/", "abc"), parsed)
    }

    @Test
    fun keepsUtf8AndEscapedDelimitersInTheCode() {
        val parsed = parsePairingQr("mydroiddeck://pair?url=http%3A%2F%2Fhost%2F&code=a%2Bb%20%26%C3%A7")
        assertEquals("a+b &ç", parsed?.code)
    }

    @Test
    fun acceptsSchemeAndTargetInAnyCase() {
        val parsed = parsePairingQr("MyDroidDeck://PAIR/?url=http%3A%2F%2Fhost%2F&code=x")
        assertEquals(PairingQr("http://host/", "x"), parsed)
    }

    @Test
    fun rejectsOtherQrCodes() {
        assertNull(parsePairingQr("https://example.com/"))
        assertNull(parsePairingQr("mydroiddeck://other?url=http%3A%2F%2Fhost%2F&code=x"))
        assertNull(parsePairingQr("just some text"))
        assertNull(parsePairingQr(""))
    }

    @Test
    fun rejectsPayloadsMissingUrlOrCode() {
        assertNull(parsePairingQr("mydroiddeck://pair?code=x"))
        assertNull(parsePairingQr("mydroiddeck://pair?url=http%3A%2F%2Fhost%2F"))
        assertNull(parsePairingQr("mydroiddeck://pair?url=http%3A%2F%2Fhost%2F&code="))
        assertNull(parsePairingQr("mydroiddeck://pair?url=%20&code=x"))
        assertNull(parsePairingQr("mydroiddeck://pair"))
    }

    @Test
    fun ignoresExtraParameters() {
        val parsed = parsePairingQr(
            "mydroiddeck://pair?v=1&url=http%3A%2F%2Fhost%3A1%2F&code=x&lang=pt"
        )
        assertEquals(PairingQr("http://host:1/", "x"), parsed)
    }
}
