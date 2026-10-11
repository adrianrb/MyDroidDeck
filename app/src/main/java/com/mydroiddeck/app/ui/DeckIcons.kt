package com.mydroiddeck.app.ui

import android.graphics.BitmapFactory
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.Stable
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.remember
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import com.mydroiddeck.app.net.ApiClient

/**
 * In-memory cache of the buttons' icons, served by the server as one PNG per action.
 *
 * The server extracts the icon from the Windows executable bound to the action
 * (see ``app.core.icons``), so the deck shows the program's *real* icon. Missing
 * icons (404 — unknown action or a program without an icon) are cached as `null`,
 * so every action is fetched at most once per screen.
 */
@Stable
class DeckIconCache {

    private val icons = mutableStateMapOf<String, ImageBitmap?>()
    private val requested = mutableSetOf<String>()

    /** Icon for [action], or `null` while loading / when the action has none. */
    @Composable
    fun icon(action: String): ImageBitmap? {
        val loaded = icons[action]
        if (!requested.contains(action)) {
            LaunchedEffect(action) { load(action) }
        }
        return loaded
    }

    private suspend fun load(action: String) {
        if (!requested.add(action)) return
        icons[action] = fetch(action)
    }

    private suspend fun fetch(action: String): ImageBitmap? = try {
        ApiClient.api().icon(action).use { body ->
            val bytes = body.bytes()
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.asImageBitmap()
        }
    } catch (_: Exception) {
        // 404 (no icon), offline, or token revoked: the button keeps its label.
        null
    }
}

/** Remembers an icon cache for the current screen. */
@Composable
fun rememberDeckIconCache(): DeckIconCache = remember { DeckIconCache() }
