package com.nanexus.videosummary.data.api

import com.nanexus.videosummary.data.model.EventOut
import com.nanexus.videosummary.data.model.HealthResponse
import com.nanexus.videosummary.data.model.SearchRequest
import com.nanexus.videosummary.data.model.SearchResponse
import com.nanexus.videosummary.data.model.SummaryResponse
import com.nanexus.videosummary.data.model.TimelineResponse
import com.nanexus.videosummary.data.model.CapabilitiesV1
import com.nanexus.videosummary.data.model.ChatJobV1
import com.nanexus.videosummary.data.model.ChatRequestV1
import com.nanexus.videosummary.data.model.SemanticSearchRequestV1
import com.nanexus.videosummary.data.model.SemanticSearchResponseV1
import com.nanexus.videosummary.data.model.SummaryV1Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface NanexusApi {
    @GET("api/v1/capabilities") suspend fun capabilitiesV1(): CapabilitiesV1
    @GET("api/v1/summaries/{localDate}") suspend fun summaryV1(@Path("localDate") localDate: String, @Query("timezone") timezone: String, @Query("site_id") siteId: String = "default", @Query("camera_id") camera: String? = null): SummaryV1Response
    @POST("api/v1/search") suspend fun searchV1(@Body body: SemanticSearchRequestV1): SemanticSearchResponseV1
    @POST("api/v1/chat/jobs") suspend fun createChatJobV1(@Body body: ChatRequestV1): ChatJobV1
    @GET("api/v1/chat/jobs/{jobId}") suspend fun chatJobV1(@Path("jobId") jobId: String, @Query("owner_id") ownerId: String? = null): ChatJobV1
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
