package com.beadsnap.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.material3.windowsizeclass.ExperimentalMaterial3WindowSizeClassApi
import androidx.compose.material3.windowsizeclass.calculateWindowSizeClass
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import com.beadsnap.app.data.store.PatternStore
import com.beadsnap.app.services.AIPatternService
import com.beadsnap.app.services.TipJarManager
import com.beadsnap.app.ui.navigation.AppNavigation
import com.beadsnap.app.ui.screens.onboarding.OnboardingScreen
import com.beadsnap.app.ui.theme.BeadSnapTheme

class MainActivity : ComponentActivity() {

    @OptIn(ExperimentalMaterial3WindowSizeClassApi::class)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val store      = PatternStore.getInstance(this)
        val aiService  = AIPatternService.shared
        val tipJar     = TipJarManager.getInstance(this)
        if (savedInstanceState == null) tipJar.recordUse()

        setContent {
            BeadSnapTheme {
                val windowSizeClass = calculateWindowSizeClass(this)
                val prefs = getSharedPreferences("beadsnap", MODE_PRIVATE)
                var onboardingDone by rememberSaveable {
                    mutableStateOf(prefs.getBoolean("onboardingDone", false))
                }

                if (!onboardingDone) {
                    OnboardingScreen(
                        onDone = {
                            prefs.edit().putBoolean("onboardingDone", true).apply()
                            onboardingDone = true
                        }
                    )
                } else {
                    AppNavigation(
                        windowWidthSizeClass = windowSizeClass.widthSizeClass,
                        store                = store,
                        aiService            = aiService,
                        tipJar               = tipJar
                    )
                }
            }
        }
    }
}
