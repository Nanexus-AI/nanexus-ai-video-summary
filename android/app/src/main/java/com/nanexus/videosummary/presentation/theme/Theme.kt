package com.nanexus.videosummary.presentation.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightColors = lightColorScheme(
    primary = Color(0xFF1F6F5B),
    secondary = Color(0xFF3A5A40),
    tertiary = Color(0xFFBC6C25),
    background = Color(0xFFF4F7F5),
    surface = Color(0xFFFFFFFF),
)

private val DarkColors = darkColorScheme(
    primary = Color(0xFF7DCFB6),
    secondary = Color(0xFFA3B18A),
    tertiary = Color(0xFFE9C46A),
)

@Composable
fun NanexusTheme(content: @Composable () -> Unit) {
    val dark = isSystemInDarkTheme()
    MaterialTheme(
        colorScheme = if (dark) DarkColors else LightColors,
        content = content,
    )
}
