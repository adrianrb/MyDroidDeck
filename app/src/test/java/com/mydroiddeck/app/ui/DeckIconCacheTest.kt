package com.mydroiddeck.app.ui

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
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

    @Test
    fun clearingDropsIconsAndAllowsARefetch() = runBlocking {
        var calls = 0
        val cache = DeckIconCache {
            calls++
            png
        }

        cache.load("calc")
        assertArrayEquals(png, cache.bytes("calc"))
        assertEquals(1, calls)

        cache.clear()

        assertNull(cache.bytes("calc"))
        cache.load("calc")
        assertArrayEquals(png, cache.bytes("calc"))
        assertEquals(2, calls)
    }

    @Test
    fun aCancelledFetchIsFetchedAgainByTheNextComposition() = runBlocking {
        // Regression: "Atualizar" clears the cache and swaps the deck for the
        // loading state, which cancels the in-flight fetch. That aborted attempt
        // must not count as "already asked", otherwise every button stays on its
        // monogram because the icon is never requested again.
        var calls = 0
        val cache = DeckIconCache {
            calls++
            if (calls == 1) CompletableDeferred<ByteArray?>().await() else png
        }

        val attempt = launch { cache.load("calc") }
        while (calls == 0) delay(1) // let the first fetch reach the network call
        attempt.cancelAndJoin()

        assertNull(cache.bytes("calc"))
        assertEquals(1, calls)

        // The next composition (the deck returning after the reload) retries.
        cache.load("calc")

        assertArrayEquals(png, cache.bytes("calc"))
        assertEquals(2, calls)
    }
}
