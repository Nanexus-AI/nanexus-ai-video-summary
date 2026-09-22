package com.nanexus.videosummary

import com.nanexus.videosummary.data.model.*
import com.nanexus.videosummary.data.repo.NanexusDataSource
import com.nanexus.videosummary.viewmodel.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.*
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.decodeFromJsonElement
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class BaselineTest {
    private val dispatcher = StandardTestDispatcher()
    @Before fun setUp() = Dispatchers.setMain(dispatcher)
    @After fun tearDown() = Dispatchers.resetMain()

    @Test fun healthDtoKeepsLegacyAiModeAndReadsModelProvider() {
        val json = Json { ignoreUnknownKeys = true }
        val legacy = json.decodeFromString<HealthResponse>("""{"status":"ok","database":true,"redis":true,"ai_mode":"openclip","summary_mode":"rule","chat_mode":"extractive"}""")
        assertEquals("openclip", legacy.aiMode)
        assertEquals("", legacy.modelProvider)
        val current = json.decodeFromString<HealthResponse>("""{"status":"ok","database":true,"redis":true,"ai_mode":"openclip","summary_mode":"rule","chat_mode":"extractive","model_provider":"stub"}""")
        assertEquals("stub", current.modelProvider)
        assertEquals("openclip", current.aiMode)
    }

    @Test fun dtoDeserialization() {
        val json = """{"total":1,"items":[{"id":101,"frigate_id":"evt-person-001","camera":"front_door","label":"person","start_time":"2026-08-20T03:30:00Z","snapshot_uri":null,"status":"done"}]}"""
        val response = Json { ignoreUnknownKeys = true }.decodeFromString<TimelineResponse>(json)
        assertEquals("evt-person-001", response.items.single().frigateId)
        assertNull(response.items.single().snapshotUri)
    }

    @Test fun v1FixtureUsesUuidSubjectsAndAsyncChat() {
        val fixture = javaClass.getResource("/client-v1.json")!!.readText()
        val root = Json.parseToJsonElement(fixture).jsonObject
        val capabilities = Json.decodeFromJsonElement<CapabilitiesV1>(root.getValue("capabilities"))
        val search = Json.decodeFromJsonElement<SemanticSearchResponseV1>(root.getValue("search"))
        val chat = Json.decodeFromJsonElement<ChatJobV1>(root.getValue("chat"))
        assertEquals("uuid", capabilities.subjectReference)
        assertTrue(capabilities.chat.asynchronous)
        assertEquals(36, search.items.single().subjectId.length)
        assertEquals("completed", chat.status)
        assertTrue(chat.answer!!.degraded)
        assertEquals(search.items.single().subjectId, chat.answer!!.citations.single().subjectId)
    }

    @Test fun repositoryUrlComposition() {
        assertEquals("http://example.test/events/42/snapshot", FakeSource().snapshotUrl("http://example.test/", 42))
    }

    @Test fun summaryStateSuccess() = runTest(dispatcher) {
        val vm = SummaryViewModel(FakeSource())
        vm.refresh(); advanceUntilIdle()
        assertFalse(vm.state.value.loading)
        assertEquals("baseline summary", vm.state.value.data?.summary?.content)
    }

    @Test fun timelineStateFailure() = runTest(dispatcher) {
        val vm = TimelineViewModel(FakeSource(failTimeline = true))
        vm.refresh(); advanceUntilIdle()
        assertEquals("timeline unavailable", vm.state.value.error)
    }

    @Test fun searchStateAndBlankQuery() = runTest(dispatcher) {
        val source = FakeSource()
        val vm = SearchViewModel(source)
        vm.search(); advanceUntilIdle()
        assertNull(vm.state.value.data)
        vm.onQueryChange(" person "); vm.search(); advanceUntilIdle()
        assertEquals("person", source.lastQuery)
        assertEquals("58e8dd46-66d0-4ac4-a025-7a44af2b6722", vm.state.value.data?.items?.single()?.subjectId)
    }
}

private class FakeSource(private val failTimeline: Boolean = false) : NanexusDataSource {
    override val baseUrl: Flow<String> = MutableStateFlow("http://example.test")
    override val cameraFilter: Flow<String> = MutableStateFlow("")
    var lastQuery: String? = null
    private val event = EventOut(101, "evt-person-001", "front_door", "person", startTime = "2026-08-20T03:30:00Z", status = "done")
    override suspend fun setBaseUrl(url: String) = Unit
    override suspend fun setCameraFilter(camera: String) = Unit
    override suspend fun health() = HealthResponse("ok", true, true, "stub", "rule", "extractive")
    override suspend fun timeline(limit: Int, camera: String?): TimelineResponse {
        if (failTimeline) error("timeline unavailable")
        return TimelineResponse(1, listOf(event))
    }
    override suspend fun summaryToday(camera: String?) = SummaryResponse("2026-08-20", SummaryOut(1, "2026-08-20", content = "baseline summary", model = "rule-v0", eventCount = 1, createdAt = "2026-08-21T00:00:00Z"))
    override suspend fun search(query: String, camera: String?, limit: Int): SearchResponse { lastQuery = query; return SearchResponse(query, "keyword-stub", 1, listOf(SearchHit(event))) }
    override suspend fun event(eventId: Int) = event
    override fun snapshotUrl(baseUrl: String, eventId: Int) = "${baseUrl.trimEnd('/')}/events/$eventId/snapshot"
    override suspend fun capabilitiesV1() = CapabilitiesV1("v1", "uuid", "/api/v1/subjects/{subject_id}", FeatureCapability(true), FeatureCapability(true), FeatureCapability(true, asynchronous = true), true, "not-configured")
    override suspend fun summaryV1(localDate: String, timezone: String, camera: String?) = SummaryV1Response(SummaryV1("48e8dd46-66d0-4ac4-a025-7a44af2b6722", localDate, timezone, "default", content = "baseline summary", generator = "rule", modelVersion = "v1", status = "ready"))
    override suspend fun searchV1(query: String, camera: String?, limit: Int, offset: Int): SemanticSearchResponseV1 { lastQuery = query; return SemanticSearchResponseV1(query, "semantic", items = listOf(SemanticSearchHitV1("58e8dd46-66d0-4ac4-a025-7a44af2b6722", .9, labels = listOf("person"), subjectPath = "/api/v1/subjects/58e8dd46-66d0-4ac4-a025-7a44af2b6722"))) }
    override suspend fun createChatJobV1(message: String, ownerId: String, conversationId: Int?, camera: String?, timezone: String) = ChatJobV1("68e8dd46-66d0-4ac4-a025-7a44af2b6722", 1, "completed", answer = ChatMessageV1("answer", "extractive", degraded = true))
    override suspend fun chatJobV1(jobId: String, ownerId: String) = createChatJobV1("", ownerId)
    override fun subjectUrl(baseUrl: String, subjectId: String) = "${baseUrl.trimEnd('/')}/api/v1/subjects/$subjectId"
}
