package com.mydroiddeck.app.model

import com.google.gson.annotations.SerializedName

/** REST payload sent when a deck button is pressed. */
data class ActionRequest(
    val action: String,
    val label: String? = null,
)

/** Server acknowledgement for a dispatched action. */
data class ActionResult(
    val status: String,
    val action: String,
    @SerializedName("executed_at") val executedAt: String? = null,
)
