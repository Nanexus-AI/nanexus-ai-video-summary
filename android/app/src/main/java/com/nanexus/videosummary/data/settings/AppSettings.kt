package com.nanexus.videosummary.data.settings

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.nanexus.videosummary.BuildConfig
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "nanexus_settings")

class AppSettings(private val context: Context) {
    private val baseUrlKey = stringPreferencesKey("base_url")
    private val cameraKey = stringPreferencesKey("camera_filter")

    val baseUrl: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[baseUrlKey] ?: BuildConfig.DEFAULT_BASE_URL
    }

    val cameraFilter: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[cameraKey] ?: ""
    }

    suspend fun setBaseUrl(value: String) {
        context.dataStore.edit { it[baseUrlKey] = value.trim().trimEnd('/') }
    }

    suspend fun setCameraFilter(value: String) {
        context.dataStore.edit { it[cameraKey] = value.trim() }
    }
}
