package com.nanexus.videosummary.presentation.navigation

sealed class Dest(val route: String) {
    data object Summary : Dest("summary")
    data object Timeline : Dest("timeline")
    data object Search : Dest("search")
    data object Chat : Dest("chat")
    data object Settings : Dest("settings")
    data object Event : Dest("event/{eventId}") {
        fun create(eventId: Int) = "event/$eventId"
    }
}
