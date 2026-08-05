package com.nanexus.videosummary.data.api

import com.nanexus.videosummary.data.model.EventOut
import com.nanexus.videosummary.data.model.HealthResponse
import com.nanexus.videosummary.data.model.SearchRequest
import com.nanexus.videosummary.data.model.SearchResponse
import com.nanexus.videosummary.data.model.SummaryResponse
import com.nanexus.videosummary.data.model.TimelineResponse
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface NanexusApi {
    @GET("health")
    suspend fun health(): HealthResponse

    @GET("timeline")
    suspend fun timeline(
        @Query("limit") limit: Int = 50,
        @Query("offset") offset: Int = 0,
        @Query("camera") camera: String? = null,
        @Query("label") label: String? = null,
    ): TimelineResponse

    @GET("summary/today")
    suspend fun summaryToday(
        @Query("camera") camera: String? = null,
    ): SummaryResponse

    @POST("search")
    suspend fun search(@Body body: SearchRequest): SearchResponse

    @GET("events/{eventId}")
    suspend fun event(@Path("eventId") eventId: Int): EventOut
}
