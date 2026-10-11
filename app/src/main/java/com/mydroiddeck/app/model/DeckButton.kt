package com.mydroiddeck.app.model

/** A single deck button: grid position, visible label, and action id. */
data class DeckButton(
    val index: Int,
    val label: String,
    val action: String,
)
