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
import com.beadsnap.app.services.RemoteLibraryService
import com.beadsnap.app.services.TipJarManager
import com.beadsnap.app.ui.tipjar.TipJarSheet
import com.beadsnap.app.ui.tipjar.TipPromptBanner
import com.beadsnap.app.ui.screens.create.CreateScreen
import com.beadsnap.app.ui.screens.editor.EditorScreen
import com.beadsnap.app.ui.screens.editor.EditorViewModel
import com.beadsnap.app.ui.screens.creations.MyCreationsScreen
import com.beadsnap.app.ui.screens.library.LibraryScreen
import com.beadsnap.app.ui.screens.library.LibraryViewModel
import com.beadsnap.app.ui.screens.projects.ProjectsScreen
import com.beadsnap.app.ui.screens.studio.AIStudioScreen
import com.beadsnap.app.ui.screens.studio.StudioViewModel

private sealed class Destination(
    val route: String,
    val label: String,
    val icon: ImageVector
) {
    data object Library : Destination("library", "Library", Icons.Default.GridView)
    data object Create  : Destination("create",  "Create",  Icons.Default.Add)
    data object Photos  : Destination("photos",  "Photos",  Icons.Default.PhotoLibrary)
    data object Mine    : Destination("mine",    "Mine",    Icons.Default.Brush)

    /**
     * The AI studio. NOT in the bottom bar: it is reached from Create, which
     * is where somebody looking to make something goes, and the bar slot it
     * used to hold now belongs to the user's own work - far more useful to
     * reach in one tap than a second door to a screen Create already opens.
     * The route stays registered and the screen is unchanged.
     */
    data object Studio  : Destination("studio",  "Studio",  Icons.Default.AutoFixHigh)
}

private val topLevelDestinations = listOf(
    Destination.Library,
    Destination.Create,
    Destination.Photos,
    Destination.Mine
)

@Composable
fun AppNavigation(
    windowWidthSizeClass: WindowWidthSizeClass,
    store: PatternStore,
    aiService: AIPatternService,
    tipJar: TipJarManager,
    library: RemoteLibraryService
) {
    val navController = rememberNavController()
    val useRail = windowWidthSizeClass != WindowWidthSizeClass.Compact
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = backStackEntry?.destination?.route

    val isTopLevel = topLevelDestinations.any { currentRoute == it.route }

    val showTipPrompt by tipJar.shouldShowPrompt.collectAsState()
    var showTipJarSheet by remember { mutableStateOf(false) }

    Box(modifier = Modifier.fillMaxSize()) {
        // BeadSnapNavHost is deliberately called from exactly ONE place.
        //
        // It used to be called from inside both branches of `if (useRail)`. A
        // composable's identity comes from its position in the composition, so
        // rotating a phone (Compact -> Medium width flips useRail) moved the
        // NavHost to the other branch and destroyed its whole subtree: every
        // remember, the back stack's saveable state, and editorPattern below.
        // The nav controller still said route "editor" while editorPattern was
        // back to null, so the editor rendered nothing and neither nav bar was
        // drawn - a totally blank screen. That was the rotation "glitch".
        //
        // Now the Row and Scaffold are always present and only the chrome
        // inside them swaps, so the NavHost subtree survives the width change.
        Row(modifier = Modifier.fillMaxSize()) {
            if (useRail && isTopLevel) {
                NavigationRail {
                    topLevelDestinations.forEach { dest ->
                        NavigationRailItem(
                            selected = currentRoute == dest.route,
                            onClick  = { navigateTopLevel(navController, dest.route) },
                            icon  = { Icon(dest.icon, contentDescription = dest.label) },
                            label = { Text(dest.label) }
                        )
                    }
                }
            }
            Scaffold(
                modifier = Modifier.fillMaxSize(),
                bottomBar = {
                    if (!useRail && isTopLevel) {
                        NavigationBar {
                            topLevelDestinations.forEach { dest ->
                                NavigationBarItem(
                                    selected = currentRoute == dest.route,
                                    onClick  = { navigateTopLevel(navController, dest.route) },
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
                    library       = library,
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

/** Navigate to a top-level tab, preserving each tab's own back stack. */
private fun navigateTopLevel(navController: NavHostController, route: String) {
    navController.navigate(route) {
        popUpTo(navController.graph.startDestinationId) { saveState = true }
        launchSingleTop = true
        restoreState    = true
    }
}

/** Builds a ViewModel from a lambda, so screens can be Activity-scoped. */
private fun <T : ViewModel> vmFactory(build: () -> T) = object : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <VM : ViewModel> create(modelClass: Class<VM>): VM = build() as VM
}

/**
 * Holds the pattern being edited. This lives in a ViewModel rather than a
 * `remember` so it survives configuration changes, including a real Activity
 * recreation (dark-mode toggle, "don't keep activities"), which `remember`
 * does not.
 */
class NavStateViewModel : ViewModel() {
    var editorPattern by mutableStateOf<FusePattern?>(null)
}

@Composable
private fun BeadSnapNavHost(
    navController: NavHostController,
    store: PatternStore,
    aiService: AIPatternService,
    library: RemoteLibraryService,
    onOpenTipJar: () -> Unit,
    modifier: Modifier = Modifier
) {
    // These are Activity-scoped via viewModel() rather than `remember`. As
    // plain remembered objects they were never held by a ViewModelStore, so
    // onCleared() never ran and viewModelScope was never cancelled: every
    // rotation leaked the old StudioViewModel with its in-flight AI request
    // still running, and silently reset search/category/sort.
    val libraryViewModel = viewModel<LibraryViewModel>(
        factory = remember(store) { vmFactory { LibraryViewModel(store) } }
    )
    val studioViewModel = viewModel<StudioViewModel>(
        factory = remember(aiService, store) { vmFactory { StudioViewModel(aiService, store) } }
    )
    val navState = viewModel<NavStateViewModel>()

    NavHost(
        navController    = navController,
        startDestination = Destination.Library.route,
        modifier         = modifier
    ) {
        composable(Destination.Library.route) {
            LibraryScreen(
                viewModel      = libraryViewModel,
                store          = store,
                library        = library,
                onPatternClick = { pattern ->
                    navState.editorPattern = pattern
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
                    navState.editorPattern = p
                    if (p.createdBy == com.beadsnap.app.data.model.CreatorType.user) {
                        store.save(p)
                    }
                    navController.navigate("editor")
                },
                onOpenAIStudio = {
                    // An ordinary push, not the tab-switch navigate this used
                    // to be. The studio is no longer a tab, so clearing the
                    // stack back to Library would have left Back going to the
                    // Library from a screen you opened from Create.
                    navController.navigate(Destination.Studio.route) {
                        launchSingleTop = true
                    }
                }
            )
        }

        composable(Destination.Photos.route) {
            ProjectsScreen(
                store         = store,
                onOpenPattern = { pattern ->
                    navState.editorPattern = pattern
                    navController.navigate("editor")
                }
            )
        }

        composable(Destination.Mine.route) {
            MyCreationsScreen(
                store         = store,
                onOpenPattern = { pattern ->
                    navState.editorPattern = pattern
                    navController.navigate("editor")
                }
            )
        }

        composable(Destination.Studio.route) {
            AIStudioScreen(
                viewModel      = studioViewModel,
                onEditPattern  = { pattern ->
                    navState.editorPattern = pattern
                    navController.navigate("editor")
                },
                // No bottom bar here any more, so the screen carries its own
                // way out.
                onBack = { navController.popBackStack() }
            )
        }

        composable("editor") {
            val pattern = navState.editorPattern
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
