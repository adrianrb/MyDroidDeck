package com.mydroiddeck.app.model

import com.google.gson.annotations.SerializedName

/** Body of `POST /pair`: the shared pairing code plus a friendly device name. */
data class PairRequest(
    val code: String,
    @SerializedName("device_name") val deviceName: String,
)

/** Response of `POST /pair`. The token is shown exactly once. */
data class PairResponse(
    val token: String,
    @SerializedName("device_id") val deviceId: Int,
    val name: String,
)