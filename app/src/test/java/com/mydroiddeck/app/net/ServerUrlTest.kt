package com.mydroiddeck.app.net

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** A-13: base-URL normalization / validation (pairing + Server dialog). */
class ServerUrlTest {

    @Test
    fun trimsAndAddsTrailingSlash() {
        assertEquals("http://host:56997/", normalizeBaseUrl("  http://host:56997  "))
    }

    @Test
    fun assumesHttpWhenNoScheme() {
        assertEquals("http://192.168.0.10:56997/", normalizeBaseUrl("192.168.0.10:56997"))
    }

    @Test
    fun keepsHttpsScheme() {
        assertEquals("https://deck.example/", normalizeBaseUrl("https://deck.example"))
    }

    @Test
    fun doesNotDuplicateTrailingSlash() {
        assertEquals("http://host/", normalizeBaseUrl("http://host/"))
    }

    @Test
    fun blankBecomesEmpty() {
        assertEquals("", normalizeBaseUrl("   "))
    }

    @Test
    fun validUrlsAreAccepted() {
        assertTrue(isValidBaseUrl("http://192.168.0.10:56997/"))
        assertTrue(isValidBaseUrl("192.168.0.10:56997"))
        assertTrue(isValidBaseUrl("https://deck.example/base/"))
    }

    @Test
    fun blankAndSpacedUrlsAreRejected() {
        assertFalse(isValidBaseUrl(""))
        assertFalse(isValidBaseUrl("   "))
        assertFalse(isValidBaseUrl("http://with space/"))
    }
}
