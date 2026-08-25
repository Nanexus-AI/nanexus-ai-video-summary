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

// Stable v1 product DTOs. Legacy DTOs above remain rollback-only.
@Serializable data class FeatureCapability(val available: Boolean, val mode: String? = null, val asynchronous: Boolean = false)
@Serializable data class CapabilitiesV1(
    @SerialName("api_version") val apiVersion: String,
    @SerialName("subject_reference") val subjectReference: String,
    @SerialName("subject_path_template") val subjectPathTemplate: String,
    val summary: FeatureCapability,
    val search: FeatureCapability,
    val chat: FeatureCapability,
    @SerialName("legacy_fallback_available") val legacyFallbackAvailable: Boolean,
    @SerialName("ownership_authentication") val ownershipAuthentication: String,
)

@Serializable data class SummaryV1(
    val id: String,
    @SerialName("local_date") val localDate: String,
    val timezone: String,
    @SerialName("site_id") val siteId: String,
    @SerialName("camera_id") val cameraId: String? = null,
    val content: String,
    @SerialName("source_subject_ids") val sourceSubjectIds: List<String> = emptyList(),
    val generator: String,
    @SerialName("model_version") val modelVersion: String,
    val status: String,
)
@Serializable data class SummaryV1Response(val summary: SummaryV1? = null)

@Serializable data class SemanticSearchRequestV1(val query: String, val limit: Int = 20, val offset: Int = 0, val camera: String? = null)
@Serializable data class SemanticSearchHitV1(
    @SerialName("subject_id") val subjectId: String,
    val score: Double,
    val camera: String? = null,
    val labels: List<String> = emptyList(),
    @SerialName("occurred_at") val occurredAt: String? = null,
    @SerialName("subject_path") val subjectPath: String,
)
@Serializable data class SemanticSearchResponseV1(
    val query: String,
    val method: String,
    val degraded: Boolean = false,
    @SerialName("degradation_reason") val degradationReason: String? = null,
    @SerialName("next_offset") val nextOffset: Int? = null,
    val items: List<SemanticSearchHitV1>,
)

@Serializable data class ChatRequestV1(
    val message: String,
    @SerialName("owner_id") val ownerId: String,
    @SerialName("conversation_id") val conversationId: Int? = null,
    val camera: String? = null,
    @SerialName("site_id") val siteId: String = "default",
    val timezone: String = "UTC",
)
@Serializable data class CitationV1(@SerialName("subject_id") val subjectId: String, @SerialName("review_path") val reviewPath: String)
@Serializable data class ChatMessageV1(
    val content: String,
    val method: String? = null,
    val degraded: Boolean = false,
    @SerialName("error_code") val errorCode: String? = null,
    val citations: List<CitationV1> = emptyList(),
)
@Serializable data class ChatJobV1(
    val id: String,
    @SerialName("conversation_id") val conversationId: Int,
    val status: String,
    @SerialName("error_code") val errorCode: String? = null,
    val answer: ChatMessageV1? = null,
)
