package com.nanexus.videosummary.data.repo

import com.nanexus.videosummary.data.api.ApiClient
import com.nanexus.videosummary.data.api.NanexusApi
import com.nanexus.videosummary.data.model.*
import com.nanexus.videosummary.data.settings.AppSettings
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first

interface NanexusDataSource {
    val baseUrl: Flow<String>
    val cameraFilter: Flow<String>
    suspend fun setBaseUrl(url: String)
    suspend fun setCameraFilter(camera: String)
    suspend fun health(): HealthResponse
    suspend fun timeline(limit: Int = 50, camera: String? = null): TimelineResponse
    suspend fun summaryToday(camera: String? = null): SummaryResponse
    suspend fun search(query: String, camera: String? = null, limit: Int = 20): SearchResponse
    suspend fun event(eventId: Int): EventOut
    fun snapshotUrl(baseUrl: String, eventId: Int): String
    suspend fun capabilitiesV1(): CapabilitiesV1
    suspend fun summaryV1(localDate: String, timezone: String = "UTC", camera: String? = null): SummaryV1Response
    suspend fun searchV1(query: String, camera: String? = null, limit: Int = 20, offset: Int = 0): SemanticSearchResponseV1
    suspend fun createChatJobV1(message: String, ownerId: String, conversationId: Int? = null, camera: String? = null, timezone: String = "UTC"): ChatJobV1
    suspend fun chatJobV1(jobId: String, ownerId: String): ChatJobV1
    fun subjectUrl(baseUrl: String, subjectId: String): String
}

class NanexusRepository(private val settings: AppSettings) : NanexusDataSource {
    override val baseUrl: Flow<String> = settings.baseUrl
    override val cameraFilter: Flow<String> = settings.cameraFilter
    private var cachedUrl: String? = null
    private var api: NanexusApi? = null

    private suspend fun client(): NanexusApi {
        val url = settings.baseUrl.first()
        val current = api
        if (current != null && cachedUrl == url) return current
        return ApiClient.create(url).also { api = it; cachedUrl = url }
    }

    override suspend fun setBaseUrl(url: String) { settings.setBaseUrl(url); api = null; cachedUrl = null }
    override suspend fun setCameraFilter(camera: String) = settings.setCameraFilter(camera)
    override suspend fun health(): HealthResponse = client().health()
    override suspend fun timeline(limit: Int, camera: String?): TimelineResponse = client().timeline(limit = limit, camera = camera)
    override suspend fun summaryToday(camera: String?): SummaryResponse = client().summaryToday(camera)
    override suspend fun search(query: String, camera: String?, limit: Int): SearchResponse = client().search(SearchRequest(query = query, limit = limit, camera = camera))
    override suspend fun event(eventId: Int): EventOut = client().event(eventId)
    override fun snapshotUrl(baseUrl: String, eventId: Int): String = "${baseUrl.trimEnd('/')}/events/$eventId/snapshot"
    override suspend fun capabilitiesV1() = client().capabilitiesV1()
    override suspend fun summaryV1(localDate: String, timezone: String, camera: String?) = client().summaryV1(localDate, timezone, camera = camera)
    override suspend fun searchV1(query: String, camera: String?, limit: Int, offset: Int) = client().searchV1(SemanticSearchRequestV1(query, limit, offset, camera))
    override suspend fun createChatJobV1(message: String, ownerId: String, conversationId: Int?, camera: String?, timezone: String) = client().createChatJobV1(ChatRequestV1(message, ownerId, conversationId, camera, timezone = timezone))
    override suspend fun chatJobV1(jobId: String, ownerId: String) = client().chatJobV1(jobId, ownerId)
    override fun subjectUrl(baseUrl: String, subjectId: String) = "${baseUrl.trimEnd('/')}/api/v1/subjects/$subjectId"
}
