package com.beadsnap.app.ui.screens.creations

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.horizontalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Brush
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.store.PatternStore
import com.beadsnap.app.data.store.PhotoProjectStore
import com.beadsnap.app.ui.screens.library.PatternCard

/**
 * Which of your own patterns to show.
 *
 * Provenance is read off data that already exists rather than a new field, so
 * everything made before this screen existed is filed correctly too: a pattern
 * listed as a variant of a photo project came from a photo, one carrying the
 * prompt it was generated from came from the AI, and what is left was drawn or
 * edited by hand.
 */
private enum class Creations(val label: String) {
    All("Everything"),
    Drawn("Drawn & edited"),
    FromPhoto("From photos"),
    FromAI("From AI")
}

/**
 * Everything the user has made, in one place.
 *
 * The Library mixes these few patterns in with more than two thousand shipped
 * ones, where they are effectively unfindable. This screen is the opposite
 * view: only what you made.
 *
 * It is deliberately a READER of PatternStore and PhotoProjectStore, holding no
 * state of its own beyond the filter chip. Opening, duplicating and deleting
 * all go through the same PatternCard the Library uses, so a pattern behaves
 * identically whichever screen you reached it from.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MyCreationsScreen(
    store: PatternStore,
    onOpenPattern: (FusePattern) -> Unit
) {
    val context = LocalContext.current
    val userPatterns by store.userPatterns.collectAsState()
    val projectStore = remember { PhotoProjectStore.getInstance(context) }
    val projects by projectStore.projects.collectAsState()

    // The NAME, not the enum: rememberSaveable can only store what goes in a
    // Bundle, and an enum is not one of those - it throws at runtime rather
    // than at compile time, on rotation, which is a poor place to find out.
    var filterName by rememberSaveable { mutableStateOf(Creations.All.name) }
    val filter = Creations.entries.firstOrNull { it.name == filterName } ?: Creations.All

    // Every pattern id that some photo project claims as one of its variants.
    val fromPhoto = remember(projects) {
        projects.flatMap { p -> p.variants.map { it.patternId } }.toHashSet()
    }

    fun kindOf(p: FusePattern): Creations = when {
        p.id in fromPhoto -> Creations.FromPhoto
        !p.sourcePrompt.isNullOrBlank() -> Creations.FromAI
        else -> Creations.Drawn
    }

    val counts = remember(userPatterns, fromPhoto) {
        userPatterns.groupingBy { kindOf(it) }.eachCount()
    }
    // Left in the store's own order, which is by title. Sorting newest-first
    // would be nicer, but a FusePattern carries no timestamp and its id is a
    // random UUID - ordering by that would look chronological and be arbitrary.
    val shown = remember(userPatterns, fromPhoto, filter) {
        if (filter == Creations.All) userPatterns
        else userPatterns.filter { kindOf(it) == filter }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("My Creations", style = MaterialTheme.typography.titleLarge)
                        Text(
                            if (userPatterns.isEmpty()) "Nothing yet"
                            else "${userPatterns.size} saved",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            )
        }
    ) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            if (userPatterns.isNotEmpty()) {
                Row(
                    Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState())
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Creations.entries.forEach { c ->
                        // A filter that would show nothing is not offered -
                        // tapping a chip and getting an empty grid reads as a
                        // bug rather than as an answer.
                        val n = if (c == Creations.All) userPatterns.size else counts[c] ?: 0
                        if (n > 0) {
                            FilterChip(
                                selected = filter == c,
                                onClick = { filterName = c.name },
                                label = { Text("${c.label} ($n)") }
                            )
                        }
                    }
                }
            }

            if (shown.isEmpty()) {
                Column(
                    modifier = Modifier.fillMaxSize().padding(40.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Icon(
                        Icons.Default.Brush, contentDescription = null,
                        modifier = Modifier.size(56.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(Modifier.height(12.dp))
                    Text("Nothing here yet", style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "Anything you draw, make from a photo, or save from the AI " +
                        "studio lands here - including a copy you edit from the " +
                        "library. Start from Create.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        textAlign = TextAlign.Center
                    )
                }
            } else {
                LazyVerticalGrid(
                    columns = GridCells.Adaptive(minSize = 140.dp),
                    contentPadding = PaddingValues(16.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(shown, key = { it.id }) { pattern ->
                        PatternCard(
                            pattern = pattern,
                            onClick = { onOpenPattern(pattern) },
                            onDuplicate = { store.duplicate(pattern) },
                            onDelete = {
                                // Delete the pattern AND the photo project's
                                // reference to it, or the project keeps a
                                // variant row pointing at nothing.
                                projects.forEach { proj ->
                                    if (proj.variants.any { it.patternId == pattern.id }) {
                                        projectStore.removeVariant(proj.id, pattern.id)
                                    }
                                }
                                store.delete(pattern)
                            }
                        )
                    }
                }
            }
        }
    }
}
