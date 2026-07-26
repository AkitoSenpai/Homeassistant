package com.gemma.chat.ui.theme

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

private val DarkColorScheme = darkColorScheme(
    primary = Color(0xFF10A37F),
    onPrimary = Color.White,
    primaryContainer = Color(0xFF1A7F64),
    onPrimaryContainer = Color.White,
    secondary = Color(0xFF202123),
    onSecondary = Color.White,
    secondaryContainer = Color(0xFF343541),
    onSecondaryContainer = Color.White,
    tertiary = Color(0xFF444654),
    onTertiary = Color.White,
    background = Color(0xFF343541),
    onBackground = Color.White,
    surface = Color(0xFF343541),
    onSurface = Color.White,
    surfaceVariant = Color(0xFF444654),
    onSurfaceVariant = Color(0xFFCACACA),
    error = Color(0xFFEF4444),
    onError = Color.White,
    outline = Color(0xFF565869)
)

private val LightColorScheme = lightColorScheme(
    primary = Color(0xFF10A37F),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFD1F0E8),
    onPrimaryContainer = Color(0xFF003828),
    secondary = Color(0xFFF7F7F8),
    onSecondary = Color(0xFF202123),
    secondaryContainer = Color(0xFFE5E5E5),
    onSecondaryContainer = Color(0xFF202123),
    tertiary = Color(0xFFFAFAFA),
    onTertiary = Color(0xFF202123),
    background = Color(0xFFFFFFFF),
    onBackground = Color(0xFF202123),
    surface = Color(0xFFFFFFFF),
    onSurface = Color(0xFF202123),
    surfaceVariant = Color(0xFFF0F0F0),
    onSurfaceVariant = Color(0xFF565869),
    error = Color(0xFFDC2626),
    onError = Color.White,
    outline = Color(0xFFD1D5DB)
)

@Composable
fun GemmaChatTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }
    
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.background.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
