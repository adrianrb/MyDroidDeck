package com.mydroiddeck.app.net

import android.content.Context
import android.content.SharedPreferences

/**
 * Device token vault backed by plain SharedPreferences.
 *
 * Fine for a LAN tool; swap for EncryptedSharedPreferences/Keystore before
 * shipping builds that run outside the local network.
 */
object TokenStore {

    private const val PREFS_NAME = "mydroiddeck"
    private const val KEY_TOKEN = "device_token"

    private var prefs: SharedPreferences? = null

    fun init(context: Context) {
        prefs = context.applicationContext
            .getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    var token: String?
        get() = prefs?.getString(KEY_TOKEN, null)
        set(value) {
            prefs?.edit()?.putString(KEY_TOKEN, value)?.apply()
        }

    fun clear() {
        prefs?.edit()?.remove(KEY_TOKEN)?.apply()
    }
}