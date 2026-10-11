package com.mydroiddeck.app.net

import com.mydroiddeck.app.model.DeckProfile
import retrofit2.http.GET

/** REST surface of the MyDroidDeck server consumed by the app. */
interface DeckApi {

    @GET("profiles")
    suspend fun listProfiles(): List<DeckProfile>
}
