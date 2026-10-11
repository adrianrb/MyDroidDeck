package com.mydroiddeck.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.mydroiddeck.app.ui.DeckScreen
import com.mydroiddeck.app.ui.theme.MyDroidDeckTheme

/** Hosts the Compose deck UI. */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MyDroidDeckTheme {
                DeckScreen()
            }
        }
    }
}
