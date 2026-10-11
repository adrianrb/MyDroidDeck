package com.mydroiddeck.app.ui

import org.junit.Assert.assertEquals
import org.junit.Test

class ThemeModeTest {

    @Test
    fun systemFollowsTheDeviceSetting() {
        assertEquals(true, ThemeMode.SYSTEM.isDark(systemDark = true))
        assertEquals(false, ThemeMode.SYSTEM.isDark(systemDark = false))
    }

    @Test
    fun explicitChoiceOverridesTheSystem() {
        assertEquals(false, ThemeMode.LIGHT.isDark(systemDark = true))
        assertEquals(true, ThemeMode.DARK.isDark(systemDark = false))
    }

    @Test
    fun persistedNameRoundTripsAndUnknownFallsBackToSystem() {
        assertEquals(ThemeMode.DARK, ThemeMode.fromName(ThemeMode.DARK.name))
        assertEquals(ThemeMode.LIGHT, ThemeMode.fromName("light"))
        assertEquals(ThemeMode.SYSTEM, ThemeMode.fromName(null))
        assertEquals(ThemeMode.SYSTEM, ThemeMode.fromName("roxo"))
    }
}
