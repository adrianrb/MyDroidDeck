package com.mydroiddeck.app

import android.app.Application
import com.mydroiddeck.app.net.TokenStore

/** Initializes app-wide singletons (token store) before any UI reads them. */
class DeckApplication : Application() {

    override fun onCreate() {
        super.onCreate()
        TokenStore.init(this)
    }
}