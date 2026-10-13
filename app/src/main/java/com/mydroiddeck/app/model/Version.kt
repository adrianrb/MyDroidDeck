package com.mydroiddeck.app.model

/** Response of `GET /version`: the server's SemVer, shown in the About dialog. */
data class VersionResponse(
    val version: String,
)
