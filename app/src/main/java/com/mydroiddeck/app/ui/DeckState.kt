package com.mydroiddeck.app.ui

import com.mydroiddeck.app.model.ActionResult
import com.mydroiddeck.app.model.DeckButton
import com.mydroiddeck.app.model.DeckProfile

/** Outcome of dispatching a button, mapped to a user-facing status message. */
enum class DeckStatus { SENT, UNKNOWN, FAILED }

/** Maps the server's acknowledgement to a [DeckStatus]. */
fun statusOf(result: ActionResult): DeckStatus = when (result.status) {
    "ok" -> DeckStatus.SENT
    "unknown" -> DeckStatus.UNKNOWN
    // "failed" / "timeout": the binding exists but the program would not launch.
    else -> DeckStatus.FAILED
}

/** Returns [buttons] with the entries at [from]/[to] swapped, re-indexed 0..n-1. */
fun swapButtons(buttons: List<DeckButton>, from: Int, to: Int): List<DeckButton> {
    if (from !in buttons.indices || to !in buttons.indices || from == to) return buttons
    val mutable = buttons.toMutableList()
    val previous = mutable[from]
    mutable[from] = mutable[to]
    mutable[to] = previous
    return mutable.mapIndexed { index, button -> button.copy(index = index) }
}

/** Index of the profile to show first, or -1 when the server returned none. */
fun firstProfileIndex(profiles: List<DeckProfile>): Int =
    if (profiles.isEmpty()) -1 else 0

/** Steps [current] by [step], wrapping around a list of [size] profiles. */
fun cycleProfileIndex(current: Int, size: Int, step: Int): Int =
    if (size <= 0) -1 else ((current + step) % size + size) % size

/** Columns the deck shows per row in portrait (see [deckColumnCount]). */
const val DECK_GRID_COLUMNS = 4

/**
 * Columns to draw in a deck [availableWidthDp] wide when portrait is [portraitWidthDp] wide.
 *
 * The keys are sized by the screen's short side: portrait fits [columns] per row and a
 * wider (landscape) screen keeps roughly that same key size — it gains columns instead of
 * stretching the [columns] keys. The count is rounded to whichever side lands closest to
 * the portrait size, and never drops below [columns].
 */
fun deckColumnCount(
    availableWidthDp: Float,
    portraitWidthDp: Float,
    columns: Int = DECK_GRID_COLUMNS,
): Int {
    require(columns > 0) { "columns must be positive" }
    val keySize = (portraitWidthDp / columns).coerceAtLeast(1f)
    val fitted = availableWidthDp / keySize
    val whole = fitted.toInt()
    val rounded = if (fitted - whole > 0.5f) whole + 1 else whole
    return maxOf(columns, rounded)
}
