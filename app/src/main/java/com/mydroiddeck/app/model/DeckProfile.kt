package com.mydroiddeck.app.model

/** A named set of buttons shipped to the device by the server. */
data class DeckProfile(
    val name: String,
    val locale: String,
    val buttons: List<DeckButton> = emptyList(),
)
