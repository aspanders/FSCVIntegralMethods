package com.beadsnap.app.ui.navigation

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.material3.windowsizeclass.WindowWidthSizeClass
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.compose.ui.Alignment
import androidx.compose.ui.unit.dp
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.store.PatternStore
import com.beadsnap.app.services.AIPatternService
import com.beadsnap.app.services.TipJarManager
import com.beadsnap.app.ui.tipjar.TipJarSheet
import com.beadsnap.app.ui.tipjar.TipPromptBanner
import com.beadsnap.app.ui.screens.create.CreateScreen
import com.beadsnap.app.ui.screens.editor.EditorScreen
import com.beadsnap.app.ui.screens.editor.EditorViewModel
import com.beadsnap.app.ui.screens.library.LibraryScreen
import com.beadsnap.app.ui.screens.library.LibraryViewModel
import com.beadsnap.app.ui.screens.studio.AIStudioScreen
import com.beadsnap.app.ui.screens.studio.StudioViewModel

private sealed class Destination(
    val route: String,
    val label: String,
    val icon: ImageVector
) {
    data object Library : Destination("library", "Library", Icons.Default.GridView)
    data object Create  : Destination("create",  "Create",  Icons.Default.Add)
    data object Studio  : Destination("studio",  "Studio",  Icons.Default.AutoFixHigh)
}

private val topLevelDestinations = listOf(
    Destination.Library,
    Destination.Create,
    Destination.Studio
)

@Composable
fun AppNavigation(
    windowWidthSizeClass: WindowWidthSizeClass,
    store: PatternStore,
    aiService: AIPatternService,
    tipJar: TipJarManager
) {
    val navController = rememberNavController()
    val useRail = windowWidthSizeClass != WindowWidthSizeClass.Compact
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = backStackEntry?.destination?.route

    val isTopLevel = topLevelDestinations.any { currentRoute == it.route }

    val showTipPrompt by tipJar.shouldShowPrompt.collectAsState()
    var showTipJarSheet by remember { mutableStateOf(false) }

    Box(modifier = Modifier.fillMaxSize()) {
        if (useRail) {
            // Tablet: NavigationRail on the left
            Row(modifier = Modifier.fillMaxSize()) {
                if (isTopLevel) {
                    NavigationRail {
                        topLevelDestinations.forEach { dest ->
                            NavigationRailItem(
                                selected = currentRoute == dest.route,
                                onClick  = {
                                    navController.navigate(dest.route) {
                                        popUpTo(navController.graph.startDestinationId) { saveState = true }
                                        launchSingleTop = true
                                        restoreState    = true
                                    }
                                },
                                icon  = { Icon(dest.icon, contentDescription = dest.label) },
                                label = { Text(dest.label) }
                            )
                        }
                    }
                }
                BeadSnapNavHost(
                    navController = navController,
                    store         = store,
                    aiService     = aiService,
                    onOpenTipJar  = { showTipJarSheet = true },
                    modifier      = Modifier.fillMaxSize()
                )
            }
        } else {
            // Phone: Bottom NavigationBar
            Scaffold(
                bottomBar = {
                    if (isTopLevel) {
                        NavigationBar {
                            topLevelDestinations.forEach { dest ->
                                NavigationBarItem(
                                    selected = currentRoute == dest.route,
                                    onClick  = {
                                        navController.navigate(dest.route) {
                                            popUpTo(navController.graph.startDestinationId) { saveState = true }
                                            launchSingleTop = true
                                            restoreState    = true
                                        }
                                    },
                                    icon  = { Icon(dest.icon, contentDescription = dest.label) },
                                    label = { Text(dest.label) }
                                )
                            }
                        }
                    }
                }
            ) { _ ->
                BeadSnapNavHost(
                    navController = navController,
                    store         = store,
                    aiService     = aiService,
                    onOpenTipJar  = { showTipJarSheet = true },
                    modifier      = Modifier.fillMaxSize()
                )
            }
        }

        // Wikipedia-style tip prompt, shown once after the 10th app use
        AnimatedVisibility(
            visible = showTipPrompt,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 96.dp),
            enter = slideInVertically(initialOffsetY = { it }) + fadeIn(),
            exit = slideOutVertically(targetOffsetY = { it }) + fadeOut()
        ) {
            TipPromptBanner(
                tipJar = tipJar,
                onDonate = { showTipJarSheet = true }
            )
        }
    }

    if (showTipJarSheet) {
        TipJarSheet(tipJar = tipJar, onDismiss = { showTipJarSheet = false })
    }
}

@Composable
private fun BeadSnapNavHost(
    navController: NavHostController,
    store: PatternStore,
    aiService: AIPatternService,
    onOpenTipJar: () -> Unit,
    modifier: Modifier = Modifier
) {
    // Shared ViewModel instances (survive recomposition, scoped to NavHost lifetime)
    val libraryViewModel = remember { LibraryViewModel(store) }
    val studioViewModel  = remember { StudioViewModel(aiService, store) }

    // EditorViewModel is keyed per-pattern; recreated on navigation
    var editorPattern by remember { mutableStateOf<FusePattern?>(null) }

    NavHost(
        navController    = navController,
        startDestination = Destination.Library.route,
        modifier         = modifier
    ) {
        composable(Destination.Library.route) {
            LibraryScreen(
                viewModel      = libraryViewModel,
                store          = store,
                onPatternClick = { pattern ->
                    editorPattern = pattern
                    navController.navigate("editor")
                },
                onOpenTipJar   = onOpenTipJar
            )
        }

        composable(Destination.Create.route) {
            CreateScreen(
                store          = store,
                onPatternReady = { pattern ->
                    var p = pattern
                    // Repeated imports get distinct names instead of piles of "Imported Photo"
                    if (p.title == "Imported Photo") {
                        val existing = store.userPatterns.value.count { it.title.startsWith("Imported Photo") }
                        if (existing > 0) p = p.copy(title = "Imported Photo ${existing + 1}")
                    }
                    editorPattern = p
                    if (p.createdBy == com.beadsnap.app.data.model.CreatorType.user) {
                        store.save(p)
                    }
                    navController.navigate("editor")
                },
                onOpenAIStudio = {
                    navController.navigate(Destination.Studio.route) {
                        popUpTo(navController.graph.startDestinationId) { saveState = true }
                        launchSingleTop = true
                        restoreState    = true
                    }
                }
            )
        }

        composable(Destination.Studio.route) {
            AIStudioScreen(
                viewModel      = studioViewModel,
                onEditPattern  = { pattern ->
                    editorPattern = pattern
                    navController.navigate("editor")
                }
            )
        }

        composable("editor") {
            val pattern = editorPattern
            if (pattern != null) {
                val factory = remember(pattern.id, store) {
                    object : ViewModelProvider.Factory {
                        @Suppress("UNCHECKED_CAST")
                        override fun <T : ViewModel> create(modelClass: Class<T>): T =
                            EditorViewModel(pattern, store) as T
                    }
                }
                val editorViewModel = viewModel<EditorViewModel>(
                    key     = "editor-${pattern.id}",
                    factory = factory
                )
                EditorScreen(
                    viewModel = editorViewModel,
                    onBack    = { navController.popBackStack() }
                )
            }
        }
    }
}
