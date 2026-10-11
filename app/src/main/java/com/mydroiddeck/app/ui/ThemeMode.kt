package com.mydroiddeck.app.ui

import com.mydroiddeck.app.net.TokenStore

/** How the deck picks its colour scheme (the user's choice in the "Tema" menu). */
enum class ThemeMode {
    /** Follow the device's system setting. */
    SYSTEM,

    /** Always light. */
    LIGHT,

    /** Always dark. */
    DARK;

    /** True when the deck should render with the dark colour scheme. */
    fun isDark(systemDark: Boolean): Boolean = when (this) {
        SYSTEM -> systemDark
        LIGHT -> false
        DARK -> true
    }

    companion object {
        /** Parses a persisted name, falling back to [SYSTEM] for anything unknown. */
        fun fromName(name: String?): ThemeMode =
            entries.firstOrNull { it.name.equals(name, ignoreCase = true) } ?: SYSTEM
    }
}

/** Persists the chosen [ThemeMode] in the app preferences vault. */
object ThemePreference {

    var mode: ThemeMode
        get() = ThemeMode.fromName(TokenStore.themeModeName)
        set(value) {
            TokenStore.themeModeName = value.name
        }
}
