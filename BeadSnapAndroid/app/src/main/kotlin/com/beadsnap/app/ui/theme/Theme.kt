package com.beadsnap.app.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val LightColorScheme = lightColorScheme(
    primary          = BeadPurple,
    onPrimary        = Color.White,
    primaryContainer = BeadPurpleContainer,
    secondary        = BeadOrange,
    onSecondary      = Color.White,
    background       = Color(0xFFFAFAFA),
    surface          = Color.White,
    onSurface        = Color(0xFF1C1B1F),
)

private val DarkColorScheme = darkColorScheme(
    primary          = BeadPurpleLight,
    onPrimary        = Color(0xFF2D0054),
    primaryContainer = Color(0xFF460080),
    secondary        = BeadOrangeLight,
    background       = Color(0xFF1C1B1F),
    surface          = Color(0xFF2B2930),
    onSurface        = Color(0xFFE6E1E5),
)

@Composable
fun BeadSnapTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else      -> LightColorScheme
    }

    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.primary.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    MaterialTheme(colorScheme = colorScheme, typography = Typography, content = content)
}
