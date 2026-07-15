package com.beadsnap.app.ui.screens.studio

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.model.GridSize
import com.beadsnap.app.data.model.PatternCategory
import com.beadsnap.app.services.ImageConverter
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AIStudioScreen(
    viewModel: StudioViewModel,
    onEditPattern: (FusePattern) -> Unit
) {
    val prompt           by viewModel.prompt.collectAsState()
    val selectedCategory by viewModel.selectedCategory.collectAsState()
    val selectedGridSize by viewModel.selectedGridSize.collectAsState()
    val isGenerating     by viewModel.isGenerating.collectAsState()
    val generatedPattern by viewModel.generatedPattern.collectAsState()
    val errorMessage     by viewModel.errorMessage.collectAsState()
    val hasKey           by viewModel.hasAPIKey.collectAsState()

    var showKeySetup     by remember { mutableStateOf(!viewModel.hasAPIKey.value) }
    var showIterateSheet by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(title = { Text("AI Studio", style = MaterialTheme.typography.titleLarge) })
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // API key banner
            if (!hasKey || showKeySetup) {
                APIKeySetupCard(
                    currentKey = viewModel.apiKey,
                    onSave = { key ->
                        viewModel.saveAPIKey(key)
                        showKeySetup = false
                    }
                )
            } else {
                TextButton(onClick = { showKeySetup = true }) {
                    Icon(Icons.Default.Key, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(Modifier.width(4.dp))
                    Text("Change API Key")
                }
            }

            // Prompt input
            OutlinedTextField(
                value = prompt,
                onValueChange = { viewModel.setPrompt(it) },
                label = { Text("Describe your pattern") },
                placeholder = { Text("e.g. a cute cat face with orange and white beads") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 3,
                maxLines = 5,
                enabled = !isGenerating
            )

            // Category selector
            Text("Category", style = MaterialTheme.typography.labelLarge)
            CategoryChips(
                selected = selectedCategory,
                onSelect = { viewModel.setCategory(it) },
                enabled  = !isGenerating
            )

            // Grid size selector
            Text("Grid Size", style = MaterialTheme.typography.labelLarge)
            GridSizeChips(
                selected = selectedGridSize,
                onSelect = { viewModel.setGridSize(it) },
                enabled  = !isGenerating
            )

            // Generate / cancel
            if (isGenerating) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    CircularProgressIndicator(modifier = Modifier.size(24.dp))
                    Text("Generating…", style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.weight(1f))
                    OutlinedButton(onClick = { viewModel.cancelGeneration() }) {
                        Icon(Icons.Default.Stop, contentDescription = null, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(4.dp))
                        Text("Cancel")
                    }
                }
            } else {
                Button(
                    onClick  = { viewModel.generate() },
                    enabled  = prompt.isNotBlank() && hasKey,
                    modifier = Modifier
                        .fillMaxWidth()
                        .semantics { contentDescription = "Generate pattern" }
                ) {
                    Icon(Icons.Default.AutoFixHigh, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Generate Pattern")
                }
            }

            // Error
            errorMessage?.let { msg ->
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.errorContainer
                    )
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.Default.Error, contentDescription = null,
                            tint = MaterialTheme.colorScheme.error)
                        Text(msg, style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onErrorContainer,
                            modifier = Modifier.weight(1f))
                        IconButton(onClick = { viewModel.clearError() }) {
                            Icon(Icons.Default.Close, contentDescription = "Dismiss error")
                        }
                    }
                }
            }

            // Generated pattern preview
            generatedPattern?.let { pattern ->
                GeneratedPatternCard(
                    pattern         = pattern,
                    onSaveAndEdit   = {
                        val saved = viewModel.saveGenerated()
                        if (saved != null) onEditPattern(saved)
                    },
                    onIterate       = { showIterateSheet = true },
                    isGenerating    = isGenerating
                )
            }
        }
    }

    if (showIterateSheet) {
        IterateSheet(
            onSubmit  = { instruction ->
                viewModel.iterate(instruction)
                showIterateSheet = false
            },
            onDismiss = { showIterateSheet = false }
        )
    }
}

// ─── API key setup ─────────────────────────────────────────────────────────────

@Composable
private fun APIKeySetupCard(
    currentKey: String,
    onSave: (String) -> Unit
) {
    var key by remember { mutableStateOf(currentKey) }
    var visible by remember { mutableStateOf(false) }

    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Icon(Icons.Default.Key, contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary)
                Text("Anthropic API Key Required",
                    style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.onPrimaryContainer)
            }
            Text(
                "Enter your Anthropic API key to enable AI pattern generation. " +
                "Keys are stored securely in device Keystore.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
            OutlinedTextField(
                value = key,
                onValueChange = { key = it },
                label = { Text("API Key") },
                placeholder = { Text("sk-ant-…") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                visualTransformation = if (visible) VisualTransformation.None
                                       else PasswordVisualTransformation(),
                trailingIcon = {
                    IconButton(onClick = { visible = !visible }) {
                        Icon(
                            if (visible) Icons.Default.VisibilityOff else Icons.Default.Visibility,
                            contentDescription = if (visible) "Hide key" else "Show key"
                        )
                    }
                }
            )
            Button(
                onClick  = { onSave(key.trim()) },
                enabled  = key.isNotBlank(),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Save Key")
            }
        }
    }
}

// ─── Generated pattern preview ────────────────────────────────────────────────

@Composable
private fun GeneratedPatternCard(
    pattern: FusePattern,
    onSaveAndEdit: () -> Unit,
    onIterate: () -> Unit,
    isGenerating: Boolean
) {
    var thumbnail by remember(pattern.id, pattern.version) {
        mutableStateOf<android.graphics.Bitmap?>(null)
    }
    LaunchedEffect(pattern.id, pattern.version) {
        val bmp = withContext(Dispatchers.Default) {
            ImageConverter.renderToBitmap(pattern, cellSizePx = 6)
        }
        thumbnail = bmp
    }

    Card(shape = RoundedCornerShape(16.dp)) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Icon(Icons.Default.AutoAwesome, contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary)
                Text(pattern.title, style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.weight(1f))
            }

            thumbnail?.let { bmp ->
                Image(
                    bitmap = bmp.asImageBitmap(),
                    contentDescription = "Preview of ${pattern.title}",
                    contentScale = ContentScale.Fit,
                    modifier = Modifier
                        .fillMaxWidth()
                        .aspectRatio(pattern.grid.width.toFloat() / pattern.grid.height.toFloat())
                        .clip(RoundedCornerShape(8.dp))
                        .background(MaterialTheme.colorScheme.surfaceVariant)
                )
            } ?: Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(1f)
                    .clip(RoundedCornerShape(8.dp))
                    .background(MaterialTheme.colorScheme.surfaceVariant),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }

            Text(
                "${pattern.grid.width}×${pattern.grid.height} grid  •  ${pattern.totalBeads} beads  •  ${pattern.palette.size} colors",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(
                    onClick  = onIterate,
                    enabled  = !isGenerating,
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(Icons.Default.Refresh, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(4.dp))
                    Text("Iterate")
                }
                Button(
                    onClick  = onSaveAndEdit,
                    enabled  = !isGenerating,
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(Icons.Default.Edit, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(4.dp))
                    Text("Edit")
                }
            }
        }
    }
}

// ─── Iterate sheet ─────────────────────────────────────────────────────────────

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun IterateSheet(
    onSubmit: (String) -> Unit,
    onDismiss: () -> Unit
) {
    var instruction by remember { mutableStateOf("") }
    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp)
                .padding(bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text("Iterate on Pattern", style = MaterialTheme.typography.titleMedium)
            Text(
                "Describe how you'd like to change the pattern",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            OutlinedTextField(
                value = instruction,
                onValueChange = { instruction = it },
                label = { Text("Instructions") },
                placeholder = { Text("e.g. make the eyes bigger, add a bow") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 3
            )
            Button(
                onClick  = { onSubmit(instruction.trim()) },
                enabled  = instruction.isNotBlank(),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Apply")
            }
        }
    }
}

// ─── Category chips ────────────────────────────────────────────────────────────

@Composable
private fun CategoryChips(
    selected: PatternCategory?,
    onSelect: (PatternCategory?) -> Unit,
    enabled: Boolean
) {
    val scroll = rememberScrollState()
    Row(
        modifier = Modifier.horizontalScroll(scroll),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        FilterChip(
            selected = selected == null,
            onClick = { if (enabled) onSelect(null) },
            label = { Text("Any") }
        )
        PatternCategory.entries.forEach { cat ->
            FilterChip(
                selected = selected == cat,
                onClick  = { if (enabled) onSelect(cat) },
                label    = { Text("${cat.emoji} ${cat.displayName}") }
            )
        }
    }
}

// ─── Grid size chips ───────────────────────────────────────────────────────────

@Composable
private fun GridSizeChips(
    selected: GridSize,
    onSelect: (GridSize) -> Unit,
    enabled: Boolean
) {
    // Exclude xlarge — too large for AI token budget
    val sizes = listOf(GridSize.small, GridSize.medium, GridSize.large)
    Row(
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        sizes.forEach { gs ->
            FilterChip(
                selected = selected == gs,
                onClick  = { if (enabled) onSelect(gs) },
                label    = { Text(gs.displayName) }
            )
        }
    }
}
