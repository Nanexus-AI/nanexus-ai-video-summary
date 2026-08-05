package com.nanexus.videosummary.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.nanexus.videosummary.data.model.EventOut
import com.nanexus.videosummary.data.model.HealthResponse
import com.nanexus.videosummary.data.model.SearchHit
import com.nanexus.videosummary.data.model.SummaryResponse
import com.nanexus.videosummary.data.repo.NanexusRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class UiState<T>(
    val loading: Boolean = false,
    val data: T? = null,
    val error: String? = null,
)

class SummaryViewModel(private val repo: NanexusRepository) : ViewModel() {
    private val _state = MutableStateFlow(UiState<SummaryResponse>())
    val state = _state.asStateFlow()
    val cameraFilter = repo.cameraFilter.stateIn(viewModelScope, SharingStarted.Eagerly, "")

    fun refresh() {
        viewModelScope.launch {
            _state.value = UiState(loading = true)
            runCatching { repo.summaryToday(cameraFilter.value.ifBlank { null }) }
                .onSuccess { _state.value = UiState(data = it) }
                .onFailure { _state.value = UiState(error = it.message ?: "Failed to load summary") }
        }
    }
}

class TimelineViewModel(private val repo: NanexusRepository) : ViewModel() {
    private val _state = MutableStateFlow(UiState<List<EventOut>>())
    val state = _state.asStateFlow()
    val baseUrl = repo.baseUrl.stateIn(viewModelScope, SharingStarted.Eagerly, "")
    val cameraFilter = repo.cameraFilter.stateIn(viewModelScope, SharingStarted.Eagerly, "")

    fun refresh() {
        viewModelScope.launch {
            _state.value = UiState(loading = true)
            runCatching { repo.timeline(camera = cameraFilter.value.ifBlank { null }) }
                .onSuccess { _state.value = UiState(data = it.items) }
                .onFailure { _state.value = UiState(error = it.message ?: "Failed to load timeline") }
        }
    }

    fun snapshotUrl(eventId: Int): String = repo.snapshotUrl(baseUrl.value, eventId)
}

class SearchViewModel(private val repo: NanexusRepository) : ViewModel() {
    private val _query = MutableStateFlow("")
    val query = _query.asStateFlow()
    private val _state = MutableStateFlow(UiState<List<SearchHit>>())
    val state = _state.asStateFlow()
    val baseUrl = repo.baseUrl.stateIn(viewModelScope, SharingStarted.Eagerly, "")
    val cameraFilter = repo.cameraFilter.stateIn(viewModelScope, SharingStarted.Eagerly, "")

    fun onQueryChange(value: String) {
        _query.value = value
    }

    fun search() {
        val q = _query.value.trim()
        if (q.isEmpty()) return
        viewModelScope.launch {
            _state.value = UiState(loading = true)
            runCatching { repo.search(q, camera = cameraFilter.value.ifBlank { null }) }
                .onSuccess { _state.value = UiState(data = it.items) }
                .onFailure { _state.value = UiState(error = it.message ?: "Search failed") }
        }
    }

    fun snapshotUrl(eventId: Int): String = repo.snapshotUrl(baseUrl.value, eventId)
}

class SettingsViewModel(private val repo: NanexusRepository) : ViewModel() {
    val baseUrl = repo.baseUrl.stateIn(viewModelScope, SharingStarted.Eagerly, "")
    val cameraFilter = repo.cameraFilter.stateIn(viewModelScope, SharingStarted.Eagerly, "")

    private val _health = MutableStateFlow<UiState<HealthResponse>>(UiState())
    val health = _health.asStateFlow()

    fun save(baseUrl: String, camera: String) {
        viewModelScope.launch {
            repo.setBaseUrl(baseUrl)
            repo.setCameraFilter(camera)
            testConnection()
        }
    }

    fun testConnection() {
        viewModelScope.launch {
            _health.value = UiState(loading = true)
            runCatching { repo.health() }
                .onSuccess { _health.value = UiState(data = it) }
                .onFailure { _health.value = UiState(error = it.message ?: "Connection failed") }
        }
    }
}

class EventDetailViewModel(private val repo: NanexusRepository) : ViewModel() {
    private val _state = MutableStateFlow(UiState<EventOut>())
    val state = _state.asStateFlow()
    val baseUrl = repo.baseUrl.stateIn(viewModelScope, SharingStarted.Eagerly, "")

    fun load(eventId: Int) {
        viewModelScope.launch {
            _state.value = UiState(loading = true)
            runCatching { repo.event(eventId) }
                .onSuccess { _state.value = UiState(data = it) }
                .onFailure { _state.value = UiState(error = it.message ?: "Failed to load event") }
        }
    }

    fun snapshotUrl(eventId: Int): String = repo.snapshotUrl(baseUrl.value, eventId)
}

class AppViewModelFactory(private val repo: NanexusRepository) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        return when {
            modelClass.isAssignableFrom(SummaryViewModel::class.java) -> SummaryViewModel(repo) as T
            modelClass.isAssignableFrom(TimelineViewModel::class.java) -> TimelineViewModel(repo) as T
            modelClass.isAssignableFrom(SearchViewModel::class.java) -> SearchViewModel(repo) as T
            modelClass.isAssignableFrom(SettingsViewModel::class.java) -> SettingsViewModel(repo) as T
            modelClass.isAssignableFrom(EventDetailViewModel::class.java) -> EventDetailViewModel(repo) as T
            else -> throw IllegalArgumentException("Unknown ViewModel ${modelClass.name}")
        }
    }
}
