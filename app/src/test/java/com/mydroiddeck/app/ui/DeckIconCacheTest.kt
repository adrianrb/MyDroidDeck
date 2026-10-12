package com.mydroiddeck.app.ui

import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class DeckIconCacheTest {

    private val png = byteArrayOf(1, 2, 3, 4)

    @Test
    fun iconIsUnknownUntilLoaded() {
        val cache = DeckIconCache { png }

        assertNull(cache.bytes("calc"))
    }

    @Test
    fun loadsEachActionOnce() = runBlocking {
        val calls = mutableListOf<String>()
        val cache = DeckIconCache { action ->
            calls.add(action)
            png
        }

        cache.load("calc")
        cache.load("calc")
        cache.load("paint")

        assertEquals(listOf("calc", "paint"), calls)
        assertArrayEquals(png, cache.bytes("calc"))
        assertArrayEquals(png, cache.bytes("paint"))
    }

    @Test
    fun aFailedFetchIsCachedAsMissing() = runBlocking {
        var calls = 0
        val cache = DeckIconCache {
            calls++
            throw IllegalStateException("offline")
        }

        cache.load("calc")
        cache.load("calc")

        assertEquals(1, calls)
        assertNull(cache.bytes("calc"))
    }
}
