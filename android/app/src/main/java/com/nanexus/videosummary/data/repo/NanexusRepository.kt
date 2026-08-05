package com.nanexus.videosummary.data.repo

import com.nanexus.videosummary.data.api.ApiClient
import com.nanexus.videosummary.data.api.NanexusApi
import com.nanexus.videosummary.data.model.EventOut
import com.nanexus.videosummary.data.model.HealthResponse
import com.nanexus.videosummary.data.model.SearchRequest
import com.nanexus.videosummary.data.model.SearchResponse
import com.nanexus.videosummary.data.model.SummaryResponse
import com.nanexus.videosummary.data.model.TimelineResponse
import com.nanexus.videosummary.data.settings.AppSettings
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first

class NanexusRepository(private val settings: AppSettings) {
    val baseUrl: Flow<String> = settings.baseUrl
    val cameraFilter: Flow<String> = settings.cameraFilter

    private var cachedUrl: String? = null
    private var api: NanexusApi? = null

    private suspend fun client(): NanexusApi {
        val url = settings.baseUrl.first()
        val current = api
        if (current != null && cachedUrl == url) return current
        return ApiClient.create(url).also {
            api = it
            cachedUrl = url
        }
    }

    suspend fun setBaseUrl(url: String) {
        settings.setBaseUrl(url)
        api = null
        cachedUrl = null
    }

    suspend fun setCameraFilter(camera: String) = settings.setCameraFilter(camera)

    suspend fun health(): HealthResponse = client().health()

    suspend fun timeline(
        limit: Int = 50,
        camera: String? = null,
    ): TimelineResponse = client().timeline(limit = limit, camera = camera)

    suspend fun summaryToday(camera: String? = null): SummaryResponse =
        client().summaryToday(camera)

    suspend fun search(
        query: String,
        camera: String? = null,
        limit: Int = 20,
    ): SearchResponse = client().search(
        SearchRequest(query = query, limit = limit, camera = camera),
    )

    suspend fun event(eventId: Int): EventOut = client().event(eventId)

    fun snapshotUrl(baseUrl: String, eventId: Int): String =
        "${baseUrl.trimEnd('/')}/events/$eventId/snapshot"
}
