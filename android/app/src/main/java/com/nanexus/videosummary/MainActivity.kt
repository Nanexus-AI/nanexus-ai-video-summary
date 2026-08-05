package com.nanexus.videosummary

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.nanexus.videosummary.presentation.navigation.Dest
import com.nanexus.videosummary.presentation.screens.EventDetailScreen
import com.nanexus.videosummary.presentation.screens.SearchScreen
import com.nanexus.videosummary.presentation.screens.SettingsScreen
import com.nanexus.videosummary.presentation.screens.SummaryScreen
import com.nanexus.videosummary.presentation.screens.TimelineScreen
import com.nanexus.videosummary.presentation.theme.NanexusTheme
import com.nanexus.videosummary.viewmodel.AppViewModelFactory
import com.nanexus.videosummary.viewmodel.EventDetailViewModel
import com.nanexus.videosummary.viewmodel.SearchViewModel
import com.nanexus.videosummary.viewmodel.SettingsViewModel
import com.nanexus.videosummary.viewmodel.SummaryViewModel
import com.nanexus.videosummary.viewmodel.TimelineViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val app = application as NanexusApp
        val factory = AppViewModelFactory(app.repository)
        setContent {
            NanexusTheme {
                NanexusRoot(factory)
            }
        }
    }
}

@Composable
private fun NanexusRoot(factory: AppViewModelFactory) {
    val navController = rememberNavController()
    val backStack by navController.currentBackStackEntryAsState()
    val route = backStack?.destination?.route
    val showBottomBar = route in setOf(
        Dest.Summary.route,
        Dest.Timeline.route,
        Dest.Search.route,
    )

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar {
                    NavigationBarItem(
                        selected = route == Dest.Summary.route,
                        onClick = {
                            navController.navigate(Dest.Summary.route) {
                                popUpTo(Dest.Summary.route) { inclusive = false }
                                launchSingleTop = true
                            }
                        },
                        icon = { Icon(Icons.Default.Home, contentDescription = null) },
                        label = { Text("Today") },
                    )
                    NavigationBarItem(
                        selected = route == Dest.Timeline.route,
                        onClick = {
                            navController.navigate(Dest.Timeline.route) {
                                popUpTo(Dest.Summary.route)
                                launchSingleTop = true
                            }
                        },
                        icon = { Icon(Icons.Default.DateRange, contentDescription = null) },
                        label = { Text("Timeline") },
                    )
                    NavigationBarItem(
                        selected = route == Dest.Search.route,
                        onClick = {
                            navController.navigate(Dest.Search.route) {
                                popUpTo(Dest.Summary.route)
                                launchSingleTop = true
                            }
                        },
                        icon = { Icon(Icons.Default.Search, contentDescription = null) },
                        label = { Text("Search") },
                    )
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = Dest.Summary.route,
            modifier = Modifier.padding(padding),
        ) {
            composable(Dest.Summary.route) {
                val vm: SummaryViewModel = viewModel(factory = factory)
                SummaryScreen(
                    vm = vm,
                    onOpenSettings = { navController.navigate(Dest.Settings.route) },
                )
            }
            composable(Dest.Timeline.route) {
                val vm: TimelineViewModel = viewModel(factory = factory)
                TimelineScreen(
                    vm = vm,
                    onOpenEvent = { id -> navController.navigate(Dest.Event.create(id)) },
                )
            }
            composable(Dest.Search.route) {
                val vm: SearchViewModel = viewModel(factory = factory)
                SearchScreen(
                    vm = vm,
                    onOpenEvent = { id -> navController.navigate(Dest.Event.create(id)) },
                )
            }
            composable(Dest.Settings.route) {
                val vm: SettingsViewModel = viewModel(factory = factory)
                SettingsScreen(
                    vm = vm,
                    onBack = { navController.popBackStack() },
                )
            }
            composable(
                route = Dest.Event.route,
                arguments = listOf(navArgument("eventId") { type = NavType.IntType }),
            ) { entry ->
                val eventId = entry.arguments?.getInt("eventId") ?: return@composable
                val vm: EventDetailViewModel = viewModel(factory = factory)
                EventDetailScreen(
                    eventId = eventId,
                    vm = vm,
                    onBack = { navController.popBackStack() },
                )
            }
        }
    }
}
