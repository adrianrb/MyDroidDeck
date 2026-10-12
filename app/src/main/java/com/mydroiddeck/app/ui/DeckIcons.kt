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
 *
 * [bytes] is a plain function on purpose: reading the snapshot map from the button's
 * own composition scope is what makes a loaded icon repaint. Returning the icon from
 * a `@Composable` helper would record that read in the helper's scope instead, so the
 * button would keep the stale `null` until something else forced it to recompose.
 */
@Stable
class DeckIconCache(
    private val fetch: suspend (String) -> ByteArray? = { action ->
        ApiClient.api().icon(action).use { body -> body.bytes() }
    },
) {

    private val icons = mutableStateMapOf<String, ByteArray?>()
    private val requested = mutableSetOf<String>()

    /** Raw PNG for [action], or `null` while loading / when the action has no icon. */
    fun bytes(action: String): ByteArray? = icons[action]

    /** Kicks off the one-shot load of [action]; call it from the button's composition. */
    @Composable
    fun prefetch(action: String) {
        LaunchedEffect(action) { load(action) }
    }

    /** Fetches [action] once and stores the outcome (the PNG, or `null` on failure). */
    internal suspend fun load(action: String) {
        if (!requested.add(action)) return
        icons[action] = try {
            fetch(action)
        } catch (_: Exception) {
            // 404 (no icon), offline, or token revoked: the button keeps its label.
            null
        }
    }
}

/** Decodes the PNG served by the server into Compose's bitmap type. */
fun decodeIcon(bytes: ByteArray): ImageBitmap? =
    BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.asImageBitmap()

/** Remembers an icon cache for the current screen. */
@Composable
fun rememberDeckIconCache(): DeckIconCache = remember { DeckIconCache() }
