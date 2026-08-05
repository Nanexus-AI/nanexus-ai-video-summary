package com.nanexus.videosummary.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class EventOut(
    val id: Int,
    @SerialName("frigate_id") val frigateId: String,
    val camera: String,
    val label: String,
    @SerialName("sub_label") val subLabel: String? = null,
    @SerialName("start_time") val startTime: String,
    @SerialName("end_time") val endTime: String? = null,
    @SerialName("snapshot_uri") val snapshotUri: String? = null,
    @SerialName("clip_uri") val clipUri: String? = null,
    val caption: String? = null,
    val tags: List<String>? = null,
    val status: String,
)

@Serializable
data class TimelineResponse(
    val total: Int,
    val items: List<EventOut>,
)

@Serializable
data class SummaryOut(
    val id: Int,
    @SerialName("summary_date") val summaryDate: String,
    val camera: String? = null,
    val content: String,
    val model: String,
    @SerialName("event_count") val eventCount: Int,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class SummaryResponse(
    val date: String,
    val summary: SummaryOut? = null,
    val fallback: String? = null,
)

@Serializable
data class HealthResponse(
    val status: String,
    val database: Boolean,
    val redis: Boolean,
    @SerialName("ai_mode") val aiMode: String,
    @SerialName("summary_mode") val summaryMode: String,
    @SerialName("chat_mode") val chatMode: String,
)

@Serializable
data class SearchRequest(
    val query: String,
    val limit: Int = 20,
    val camera: String? = null,
    val label: String? = null,
)

@Serializable
data class SearchHit(
    val event: EventOut,
    val score: Double? = null,
)

@Serializable
data class SearchResponse(
    val query: String,
    val method: String,
    val total: Int,
    val items: List<SearchHit>,
)
