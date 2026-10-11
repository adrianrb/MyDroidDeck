package com.mydroiddeck.app.net

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

/** Builds the Retrofit client. */
object ApiClient {

    /** Android emulator maps the host machine to 10.0.2.2; use the LAN IP on a device. */
    const val BASE_URL = "http://10.0.2.2:8000/"

    val api: DeckApi by lazy {
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
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(httpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(DeckApi::class.java)
    }
}