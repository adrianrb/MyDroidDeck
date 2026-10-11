package com.mydroiddeck.app.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import com.mydroiddeck.app.net.TokenStore

/** Root of the Compose UI: shows the deck once a device token exists, else pairing. */
@Composable
fun DeckApp() {
    var paired by remember { mutableStateOf(!TokenStore.token.isNullOrBlank()) }

    if (paired) {
        DeckScreen(
            onUnauthorized = {
                TokenStore.clear()
                paired = false
            },
        )
    } else {
        PairingScreen(onPaired = { paired = true })
    }
}