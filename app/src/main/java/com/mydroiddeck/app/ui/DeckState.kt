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
