package com.mydroiddeck.app.net

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

/** Builds the Retrofit client for the currently configured server URL. */
object ApiClient {

    /** Server base URL, editable on the pairing screen and persisted by [TokenStore]. */
    val baseUrl: String get() = TokenStore.baseUrl

    private var cached: DeckApi? = null
    private var cachedUrl: String? = null

    /** Returns a Retrofit [DeckApi], rebuilding it when the server URL changes. */
    @Synchronized
    fun api(): DeckApi {
        val url = baseUrl
        if (cached == null || cachedUrl != url) {
            cached = build(url)
            cachedUrl = url
        }
        return cached!!
    }

    private fun build(baseUrl: String): DeckApi {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }
        val httpClient = OkHttpClient.Builder()
            // Attach the pairing token to every REST call once one is stored.
            .addInterceptor { chain ->
                val token = TokenStore.token
                val request = if (token.isNullOrBlank()) {
                    chain.request()
                } else {
                    chain.request().newBuilder()
                        .header("Authorization", "Bearer $token")
                        .build()
                }
                chain.proceed(request)
            }
            .addInterceptor(logging)
            .build()
        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(httpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(DeckApi::class.java)
    }
}