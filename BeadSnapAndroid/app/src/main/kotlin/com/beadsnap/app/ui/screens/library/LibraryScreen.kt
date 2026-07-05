package com.beadsnap.app.ui.screens.library

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Sort
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.model.PatternCategory
import com.beadsnap.app.services.ImageConverter
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LibraryScreen(
    viewModel: LibraryViewModel,
    onPatternClick: (FusePattern) -> Unit
) {
    val patterns    by viewModel.patterns.collectAsState()
    val category    by viewModel.selectedCategory.collectAsState()
    val query       by viewModel.searchQuery.collectAsState()
    val sort        by viewModel.sortOrder.collectAsState()
    val counts      by viewModel.categoryCounts.collectAsState()
    var showSortMenu by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Library", style = MaterialTheme.typography.titleLarge) },
                actions = {
                    IconButton(onClick = { showSortMenu = true }) {
                        Icon(Icons.Default.Sort, contentDescription = "Sort patterns")
                    }
                    DropdownMenu(expanded = showSortMenu, onDismissRequest = { showSortMenu = false }) {
                        LibrarySortOrder.entries.forEach { order ->
                            DropdownMenuItem(
                                text = { Text(order.displayName) },
                                onClick = { viewModel.setSortOrder(order); showSortMenu = false },
                                leadingIcon = {
                                    if (sort == order) Icon(Icons.Default.Search, null, tint = MaterialTheme.colorScheme.primary)
                                }
                            )
                        }
                    }
                }
            )
        }
    ) { padding ->
        Column(modifier = Modifier.padding(padding)) {
            // Search bar
            OutlinedTextField(
                value = query,
                onValueChange = { viewModel.setQuery(it) },
                modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
                placeholder = { Text("Search patterns") },
                leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
                singleLine = true,
                shape = RoundedCornerShape(28.dp)
            )

            // Category chips
            CategoryChipsRow(
                selectedCategory = category,
                categoryCounts = counts,
                onCategorySelected = { viewModel.setCategory(it) }
            )

            HorizontalDivider()

            if (patterns.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("No Patterns Found", style = MaterialTheme.typography.titleMedium)
                        Text("Try a different category or search term.", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            } else {
                LazyVerticalGrid(
                    columns = GridCells.Adaptive(minSize = 140.dp),
                    contentPadding = PaddingValues(16.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                    modifier = Modifier.fillMaxSize()
                ) {
                    items(patterns, key = { it.id }) { pattern ->
                        PatternCard(
                            pattern = pattern,
                            onClick = { onPatternClick(pattern) }
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun CategoryChipsRow(
    selectedCategory: PatternCategory?,
    categoryCounts: Map<PatternCategory, Int>,
    onCategorySelected: (PatternCategory?) -> Unit
) {
    androidx.compose.foundation.lazy.LazyRow(
        contentPadding = PaddingValues(horizontal = 16.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        modifier = Modifier.padding(vertical = 8.dp)
    ) {
        item {
            FilterChip(
                selected = selectedCategory == null,
                onClick = { onCategorySelected(null) },
                label = { Text("All") },
                modifier = Modifier.semantics { contentDescription = "All categories" }
            )
        }
        items(PatternCategory.entries.toTypedArray()) { cat ->
            FilterChip(
                selected = selectedCategory == cat,
                onClick = { onCategorySelected(cat) },
                label = { Text("${cat.emoji} ${cat.displayName}") },
                modifier = Modifier.semantics { contentDescription = cat.displayName }
            )
        }
    }
}

@Composable
private fun PatternCard(pattern: FusePattern, onClick: () -> Unit) {
    val cacheKey = "${pattern.id}-v${pattern.version}"
    var thumbnail by remember(cacheKey) { mutableStateOf(ThumbnailCache.get(cacheKey)) }

    LaunchedEffect(cacheKey) {
        if (thumbnail == null) {
            val bmp = withContext(Dispatchers.Default) {
                ImageConverter.renderToBitmap(pattern, cellSizePx = 4)
            }
            ThumbnailCache.put(cacheKey, bmp)
            thumbnail = bmp
        }
    }

    Card(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .semantics(mergeDescendants = true) {
                contentDescription = "${pattern.title}, ${pattern.difficulty.displayName}, ${pattern.totalBeads} beads"
            },
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(modifier = Modifier.padding(8.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(1f)
                    .clip(RoundedCornerShape(8.dp))
                    .background(MaterialTheme.colorScheme.surfaceVariant)
            ) {
                thumbnail?.let { bmp ->
                    androidx.compose.foundation.Image(
                        bitmap = bmp.asImageBitmap(),
                        contentDescription = null,
                        contentScale = ContentScale.Crop,
                        modifier = Modifier.fillMaxSize()
                    )
                }
            }
            Text(
                text = pattern.title,
                style = MaterialTheme.typography.labelLarge,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
            Row(horizontalArrangement = Arrangement.spacedBy(4.dp), verticalAlignment = Alignment.CenterVertically) {
                Text(pattern.difficulty.emoji, style = MaterialTheme.typography.labelSmall)
                Text(
                    "${pattern.totalBeads} beads",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

// Lightweight in-memory thumbnail cache
private object ThumbnailCache {
    private val cache = android.util.LruCache<String, android.graphics.Bitmap>(200)
    fun get(key: String): android.graphics.Bitmap? = cache[key]
    fun put(key: String, bmp: android.graphics.Bitmap) { cache.put(key, bmp) }
}
