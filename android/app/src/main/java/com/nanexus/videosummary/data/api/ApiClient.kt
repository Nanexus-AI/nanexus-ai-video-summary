package com.nanexus.videosummary.data.api

import com.nanexus.videosummary.BuildConfig
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Interceptor
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import java.util.concurrent.TimeUnit

object ApiClient {
    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        explicitNulls = false
    }

    fun create(baseUrl: String, tokenProvider: TokenProvider = NoTokenProvider): NanexusApi {
        require(BuildConfig.DEBUG || baseUrl.startsWith("https://")) { "Release builds require an HTTPS Video Summary URL" }
        val client = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .addInterceptor(Interceptor { chain ->
                val token = tokenProvider.token()
                val request = if (token.isNullOrBlank()) chain.request() else chain.request().newBuilder().header("Authorization", "Bearer $token").build()
                chain.proceed(request)
            })
            .apply { if (BuildConfig.DEBUG) addInterceptor(HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.HEADERS; redactHeader("Authorization") }) }
            .build()
        val normalized = baseUrl.trimEnd('/') + "/"
        return Retrofit.Builder()
            .baseUrl(normalized)
            .client(client)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(NanexusApi::class.java)
    }
}

fun interface TokenProvider { fun token(): String? }
object NoTokenProvider : TokenProvider { override fun token(): String? = null }
