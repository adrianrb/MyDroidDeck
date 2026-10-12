package com.mydroiddeck.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.core.view.WindowCompat
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
            val dark = themeMode.isDark(isSystemInDarkTheme())

            // Edge-to-edge: keep the status/navigation bar icons legible for the
            // *chosen* scheme (enableEdgeToEdge only knows the system setting).
            SideEffect {
                WindowCompat.getInsetsController(window, window.decorView).apply {
                    isAppearanceLightStatusBars = !dark
                    isAppearanceLightNavigationBars = !dark
                }
            }

            MyDroidDeckTheme(darkTheme = dark) {
                // Paint the whole window with the scheme's background. Without this
                // the app keeps the framework window theme's background (light), so
                // picking "Escuro" only recoloured the widgets, not the app.
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background,
                ) {
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
}
