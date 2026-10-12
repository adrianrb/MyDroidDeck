package com.mydroiddeck.app.net

import com.mydroiddeck.app.model.ActionRequest
import com.mydroiddeck.app.model.ActionResult
import com.mydroiddeck.app.model.DeckProfile
import com.mydroiddeck.app.model.PairRequest
import com.mydroiddeck.app.model.PairResponse
import okhttp3.ResponseBody
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

/** REST surface of the MyDroidDeck server consumed by the app. */
interface DeckApi {

    @POST("pair")
    suspend fun pair(@Body request: PairRequest): PairResponse

    @GET("profiles")
    suspend fun listProfiles(): List<DeckProfile>

    /** Replaces the profile (name/locale/buttons) with the given ordered buttons. */
    @PUT("profiles/{id}")
    suspend fun updateProfile(@Path("id") id: Long, @Body profile: DeckProfile): DeckProfile

    @POST("actions")
    suspend fun dispatch(@Body request: ActionRequest): ActionResult

    /**
     * The real icon (PNG) of the program bound to [action], extracted from the
     * Windows executable by the server. 404 when the action has no icon.
     */
    @GET("icon")
    suspend fun icon(@Query("action") action: String): ResponseBody
}