package com.nanexus.videosummary.presentation.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil.compose.AsyncImage
import com.nanexus.videosummary.presentation.components.ErrorBox
import com.nanexus.videosummary.presentation.components.EventListItem
import com.nanexus.videosummary.presentation.components.LoadingBox
import com.nanexus.videosummary.viewmodel.EventDetailViewModel
import com.nanexus.videosummary.viewmodel.SearchViewModel
import com.nanexus.videosummary.viewmodel.SettingsViewModel
import com.nanexus.videosummary.viewmodel.SummaryViewModel
import com.nanexus.videosummary.viewmodel.TimelineViewModel
import com.nanexus.videosummary.viewmodel.ChatViewModel
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.foundation.shape.RoundedCornerShape

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SummaryScreen(
    vm: SummaryViewModel,
    onOpenSettings: () -> Unit,
) {
    val uriHandler = LocalUriHandler.current
    val state by vm.state.collectAsStateWithLifecycle()
    val camera by vm.cameraFilter.collectAsStateWithLifecycle()

    LaunchedEffect(camera) { vm.refresh() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Today") },
                actions = {
                    IconButton(onClick = { vm.refresh() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                    }
                    IconButton(onClick = onOpenSettings) {
                        Icon(Icons.Default.Settings, contentDescription = "Settings")
                    }
                },
            )
        },
    ) { padding ->
        when {
            state.loading -> LoadingBox()
            state.error != null -> ErrorBox(state.error!!, onRetry = vm::refresh)
            state.data != null -> {
                val resp = state.data!!
                val content = resp.summary?.content.orEmpty()
                Column(
                    modifier = Modifier
                        .padding(padding)
                        .fillMaxSize()
                        .verticalScroll(rememberScrollState())
                        .padding(16.dp),
                ) {
                    Text(
                        text = if (camera.isBlank()) "All cameras" else "Camera: $camera",
                        style = MaterialTheme.typography.labelLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    resp.summary?.sourceSubjectIds?.forEach { subjectId ->
                        TextButton(onClick = { uriHandler.openUri(vm.subjectUrl(subjectId)) }) { Text("Open related event ${subjectId.take(8)}") }
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Summary · ${resp.summary?.localDate ?: "today"}",
                        style = MaterialTheme.typography.headlineSmall,
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = content.ifBlank { "No summary yet for this day." },
                        style = MaterialTheme.typography.bodyLarge,
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = buildString {
                            append(resp.summary?.generator ?: "No precomputed summary")
                        },
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TimelineScreen(
    vm: TimelineViewModel,
    onOpenEvent: (Int) -> Unit,
) {
    val state by vm.state.collectAsStateWithLifecycle()
    val camera by vm.cameraFilter.collectAsStateWithLifecycle()

    LaunchedEffect(camera) { vm.refresh() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Timeline") },
                actions = {
                    IconButton(onClick = { vm.refresh() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                    }
                },
            )
        },
    ) { padding ->
        when {
            state.loading -> LoadingBox()
            state.error != null -> ErrorBox(state.error!!, onRetry = vm::refresh)
            state.data != null -> {
                val items = state.data!!
                if (items.isEmpty()) {
                    ErrorBox("No events yet${if (camera.isNotBlank()) " for $camera" else ""}.")
                } else {
                    LazyColumn(
                        contentPadding = PaddingValues(vertical = 8.dp),
                        modifier = Modifier.padding(padding),
                    ) {
                        items(items, key = { it.id }) { event ->
                            EventListItem(
                                event = event,
                                snapshotUrl = vm.snapshotUrl(event.id),
                                onClick = { onOpenEvent(event.id) },
                            )
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchScreen(vm: SearchViewModel, onOpenSubject: (String) -> Unit) {
    val query by vm.query.collectAsStateWithLifecycle()
    val state by vm.state.collectAsStateWithLifecycle()

    Scaffold(
        topBar = { TopAppBar(title = { Text("Search") }) },
        floatingActionButton = {
            FloatingActionButton(onClick = { vm.search() }) {
                Icon(Icons.Default.Search, contentDescription = "Search")
            }
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize(),
        ) {
            OutlinedTextField(
                value = query,
                onValueChange = vm::onQueryChange,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                label = { Text("Semantic query") },
                singleLine = true,
                placeholder = { Text("person near car, package on porch…") },
            )
            when {
                state.loading -> LoadingBox()
                state.error != null -> ErrorBox(state.error!!, onRetry = vm::search)
                state.data != null -> {
                    val response = state.data!!
                    val hits = response.items
                    if (hits.isEmpty()) {
                        ErrorBox("No matches.")
                    } else {
                        LazyColumn(contentPadding = PaddingValues(bottom = 88.dp)) {
                            items(hits, key = { it.subjectId }) { hit ->
                                TextButton(onClick = { onOpenSubject(hit.subjectId) }) {
                                    Text("${hit.camera ?: "Event"} · ${hit.labels.joinToString()} · ${"%.2f".format(hit.score)}")
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable fun ChatScreen(vm: ChatViewModel) {
    val question by vm.question.collectAsStateWithLifecycle()
    val state by vm.state.collectAsStateWithLifecycle()
    val uriHandler = LocalUriHandler.current
    Scaffold(topBar = { TopAppBar(title = { Text("Chat") }) }) { padding ->
        Column(Modifier.padding(padding).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedTextField(question, vm::onQuestionChange, Modifier.fillMaxWidth(), label = { Text("Ask about events") })
            TextButton(onClick = vm::submit) { Text(if (state.loading) "Processing…" else "Ask") }
            state.error?.let { ErrorBox(it, onRetry = vm::submit) }
            state.data?.let { job ->
                Text("Job: ${job.status}")
                job.answer?.let { answer ->
                    if (answer.degraded) Text("Degraded answer", color = MaterialTheme.colorScheme.error)
                    Text(answer.content)
                    answer.citations.forEach { citation ->
                        TextButton(onClick = { uriHandler.openUri(vm.subjectUrl(citation.subjectId)) }) { Text("Open related event ${citation.subjectId.take(8)}") }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(vm: SettingsViewModel, onBack: () -> Unit) {
    val baseUrl by vm.baseUrl.collectAsStateWithLifecycle()
    val camera by vm.cameraFilter.collectAsStateWithLifecycle()
    val health by vm.health.collectAsStateWithLifecycle()
    val capabilities by vm.capabilities.collectAsStateWithLifecycle()

    var urlDraft by remember(baseUrl) { mutableStateOf(baseUrl) }
    var cameraDraft by remember(camera) { mutableStateOf(camera) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .padding(16.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                "API base URL",
                style = MaterialTheme.typography.titleMedium,
            )
            Text(
                "Emulator → host: http://10.0.2.2:8000\nPhone → LAN: http://192.168.x.x:8000",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            OutlinedTextField(
                value = urlDraft,
                onValueChange = { urlDraft = it },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                label = { Text("Base URL") },
            )
            OutlinedTextField(
                value = cameraDraft,
                onValueChange = { cameraDraft = it },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                label = { Text("Camera filter (optional)") },
                placeholder = { Text("front_yard") },
            )
            TextButton(onClick = { vm.save(urlDraft.trim(), cameraDraft.trim()) }) {
                Text("Save & test")
            }
            when {
                health.loading -> Text("Testing…")
                health.error != null -> Text(
                    "Error: ${health.error}",
                    color = MaterialTheme.colorScheme.error,
                )
                health.data != null -> {
                    val h = health.data!!
                    Text(
                        "OK · ${h.status} · db=${h.database} · redis=${h.redis}\n" +
                            "ai=${h.aiMode} · summary=${h.summaryMode} · chat=${h.chatMode}",
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
            }
            capabilities.data?.let { c -> Text("API ${c.apiVersion} · UUID subjects · summary=${c.summary.available} search=${c.search.available} chat=${c.chat.available}\nOwnership authentication: ${c.ownershipAuthentication}") }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EventDetailScreen(
    eventId: Int,
    vm: EventDetailViewModel,
    onBack: () -> Unit,
) {
    val state by vm.state.collectAsStateWithLifecycle()

    LaunchedEffect(eventId) { vm.load(eventId) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Event") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
    ) { padding ->
        when {
            state.loading -> LoadingBox()
            state.error != null -> ErrorBox(state.error!!, onRetry = { vm.load(eventId) })
            state.data != null -> {
                val event = state.data!!
                Column(
                    modifier = Modifier
                        .padding(padding)
                        .fillMaxSize()
                        .verticalScroll(rememberScrollState())
                        .padding(16.dp),
                ) {
                    AsyncImage(
                        model = vm.snapshotUrl(event.id),
                        contentDescription = event.label,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(220.dp)
                            .clip(RoundedCornerShape(12.dp)),
                        contentScale = ContentScale.Crop,
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("${event.camera} · ${event.label}", style = MaterialTheme.typography.titleLarge)
                    Text(
                        event.startTime.replace('T', ' ').take(19),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(event.caption ?: "(no caption)", style = MaterialTheme.typography.bodyLarge)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "status=${event.status} · id=${event.id}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}
