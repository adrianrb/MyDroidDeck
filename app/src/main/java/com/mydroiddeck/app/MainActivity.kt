package com.mydroiddeck.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import com.mydroiddeck.app.ui.DeckApp
import com.mydroiddeck.app.ui.ThemePreference
import com.mydroiddeck.app.ui.theme.MyDroidDeckTheme

/** Hosts the Compose deck UI. */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            // The user's theme choice (dark mode) outlives the process.
            var themeMode by remember { mutableStateOf(ThemePreference.mode) }
            MyDroidDeckTheme(darkTheme = themeMode.isDark(isSystemInDarkTheme())) {
                DeckApp(
                    themeMode = themeMode,
                    onThemeModeChange = { chosen ->
                        themeMode = chosen
                        ThemePreference.mode = chosen
                    },
                )
            }
        }
    }
}
