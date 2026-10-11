package com.mydroiddeck.app.net

import com.mydroiddeck.app.model.ActionRequest
import com.mydroiddeck.app.model.ActionResult
import com.mydroiddeck.app.model.DeckProfile
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

/** REST surface of the MyDroidDeck server consumed by the app. */
interface DeckApi {

    @GET("profiles")
    suspend fun listProfiles(): List<DeckProfile>

    @POST("actions")
    suspend fun dispatch(@Body request: ActionRequest): ActionResult
}
