package com.beadsnap.app.ui.screens.projects

import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.store.PatternStore
import com.beadsnap.app.data.store.PhotoProject
import com.beadsnap.app.data.store.PhotoProjectStore
import com.beadsnap.app.services.BitmapLoader
import com.beadsnap.app.ui.screens.create.PhotoTuneScreen
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * The photo shelf: every photo brought into the app, with the patterns made
 * from it filed underneath it.
 *
 * Converting a photo used to be a one-shot - the picture was read, turned into
 * beads and thrown away, so trying a different board size meant finding the
 * original in the gallery and starting over, and the earlier attempt was just
 * another loose entry in My Designs with no memory of where it came from.
 * Here the photo is the parent and each conversion is a variant of it.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProjectsScreen(
    store: PatternStore,
    onOpenPattern: (FusePattern) -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val projectStore = remember { PhotoProjectStore.getInstance(context) }
    val projects by projectStore.projects.collectAsState()
    val userPatterns by store.userPatterns.collectAsState()
    val projectError by projectStore.lastError.collectAsState()

    var expandedId by remember { mutableStateOf<String?>(null) }
    var renaming by remember { mutableStateOf<PhotoProject?>(null) }
    var deleting by remember { mutableStateOf<PhotoProject?>(null) }

    // Re-deriving a variant: the stored photo, reloaded, plus which project it
    // belongs to.
    var tuneSource by remember { mutableStateOf<Bitmap?>(null) }
    var tuneProject by remember { mutableStateOf<PhotoProject?>(null) }
    var tuneCutout by remember { mutableStateOf(false) }
    var loadingSource by remember { mutableStateOf(false) }
    var sourceError by remember { mutableStateOf<String?>(null) }
    // Set when a project has both an original and a cut-out and the user has
    // to say which one this new pattern starts from.
    var choosingFor by remember { mutableStateOf<PhotoProject?>(null) }

    fun startTuning(project: PhotoProject, cutout: Boolean) {
        scope.launch {
            loadingSource = true
            val bmp = projectStore.loadSource(project.id, cutout = cutout)
                ?: projectStore.loadSource(project.id, cutout = false)
            loadingSource = false
            if (bmp == null) {
                sourceError = "The photo for \"${project.title}\" is no longer on this device."
            } else {
                tuneProject = project
                tuneCutout = cutout
                tuneSource = bmp
            }
        }
    }

    fun newVariant(project: PhotoProject) {
        if (project.hasCutout) choosingFor = project else startTuning(project, cutout = false)
    }

    Scaffold(
        topBar = {
            TopAppBar(title = { Text("Photos", style = MaterialTheme.typography.titleLarge) })
        }
    ) { padding ->
        Box(Modifier.padding(padding).fillMaxSize()) {
            if (projects.isEmpty()) {
                Column(
                    modifier = Modifier.align(Alignment.Center).padding(40.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Icon(
                        Icons.Default.PhotoLibrary, contentDescription = null,
                        modifier = Modifier.size(56.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(Modifier.height(12.dp))
                    Text("No photos yet", style = MaterialTheme.typography.titleMedium)
                    Text(
                        "Convert a photo from Create and it is kept here, so you can " +
                        "try other board sizes and colour counts later without " +
                        "finding the picture again.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        textAlign = TextAlign.Center
                    )
                }
            } else {
                LazyColumn(
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(projects, key = { it.id }) { project ->
                        ProjectCard(
                            project = project,
                            expanded = expandedId == project.id,
                            onToggle = {
                                expandedId = if (expandedId == project.id) null else project.id
                            },
                            projectStore = projectStore,
                            patternFor = { id -> userPatterns.firstOrNull { it.id == id } },
                            onOpenPattern = onOpenPattern,
                            onNewVariant = { newVariant(project) },
                            onRename = { renaming = project },
                            onDelete = { deleting = project },
                            onRemoveVariant = { patternId ->
                                projectStore.removeVariant(project.id, patternId)
                                userPatterns.firstOrNull { it.id == patternId }
                                    ?.let { store.delete(it) }
                            }
                        )
                    }
                }
            }

            if (loadingSource) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            }
        }
    }

    // A new variant of an existing photo: the same live tuning screen the
    // first conversion used, so nothing behaves differently the second time.
    val source = tuneSource
    val project = tuneProject
    if (source != null && project != null) {
        PhotoTuneScreen(
            source = source,
            initialGridSize = com.beadsnap.app.data.model.GridSize.large,
            initialMaxColors = 12,
            // Starting from the stored cut-out means the subject is already
            // alone on a transparent field; there is nothing left to segment.
            autoSegment = !tuneCutout,
            onCancel = { tuneSource = null; tuneProject = null },
            onDone = { pattern, _, _, _ ->
                val titled = pattern.copy(
                    title = "${project.title} v${project.variants.size + 1}"
                )
                store.save(titled)
                projectStore.addVariant(
                    project.id, titled.id,
                    PhotoProjectStore.labelFor(titled, cutout = tuneCutout)
                )
                tuneSource = null
                tuneProject = null
                onOpenPattern(titled)
            }
        )
    }

    choosingFor?.let { p ->
        AlertDialog(
            onDismissRequest = { choosingFor = null },
            title = { Text("Start from") },
            text = {
                Text(
                    "This photo was saved with and without its background. " +
                    "Which one should the new pattern use?"
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    choosingFor = null
                    startTuning(p, cutout = true)
                }) { Text("Background removed") }
            },
            dismissButton = {
                TextButton(onClick = {
                    choosingFor = null
                    startTuning(p, cutout = false)
                }) { Text("Original photo") }
            }
        )
    }

    renaming?.let { p ->
        RenameDialog(
            initial = p.title,
            onConfirm = { projectStore.rename(p.id, it); renaming = null },
            onDismiss = { renaming = null }
        )
    }

    deleting?.let { p ->
        AlertDialog(
            onDismissRequest = { deleting = null },
            title = { Text("Delete \"${p.title}\"?") },
            text = {
                Text(
                    if (p.variants.isEmpty()) "The photo is removed from this device."
                    else "The photo and its ${p.variants.size} pattern" +
                         "${if (p.variants.size == 1) "" else "s"} are removed from this device."
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    p.variants.forEach { v ->
                        userPatterns.firstOrNull { it.id == v.patternId }?.let { store.delete(it) }
                    }
                    projectStore.delete(p.id)
                    deleting = null
                }) { Text("Delete", color = MaterialTheme.colorScheme.error) }
            },
            dismissButton = { TextButton(onClick = { deleting = null }) { Text("Cancel") } }
        )
    }

    (sourceError ?: projectError)?.let { msg ->
        AlertDialog(
            onDismissRequest = { sourceError = null; projectStore.clearLastError() },
            title = { Text("Photo Projects") },
            text = { Text(msg) },
            confirmButton = {
                TextButton(onClick = {
                    sourceError = null
                    projectStore.clearLastError()
                }) { Text("OK") }
            }
        )
    }
}

@Composable
private fun ProjectCard(
    project: PhotoProject,
    expanded: Boolean,
    onToggle: () -> Unit,
    projectStore: PhotoProjectStore,
    patternFor: (String) -> FusePattern?,
    onOpenPattern: (FusePattern) -> Unit,
    onNewVariant: () -> Unit,
    onRename: () -> Unit,
    onDelete: () -> Unit,
    onRemoveVariant: (String) -> Unit
) {
    Card(shape = RoundedCornerShape(16.dp), modifier = Modifier.fillMaxWidth()) {
        Column {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { onToggle() }
                    .padding(12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                ProjectThumb(projectStore, project.id)
                Column(Modifier.weight(1f)) {
                    Text(project.title, style = MaterialTheme.typography.titleMedium)
                    Text(
                        if (project.variants.isEmpty()) "No patterns yet"
                        else "${project.variants.size} pattern" +
                             "${if (project.variants.size == 1) "" else "s"}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Icon(
                    if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                    contentDescription = if (expanded) "Collapse" else "Expand",
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            if (expanded) {
                HorizontalDivider()
                project.variants.sortedBy { it.createdAt }.forEach { variant ->
                    val pattern = patternFor(variant.patternId)
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .then(
                                if (pattern != null) Modifier.clickable { onOpenPattern(pattern) }
                                else Modifier
                            )
                            .padding(horizontal = 16.dp, vertical = 10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Icon(
                            if (pattern != null) Icons.Default.GridOn else Icons.Default.ErrorOutline,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Column(Modifier.weight(1f)) {
                            Text(
                                pattern?.title ?: "Deleted pattern",
                                style = MaterialTheme.typography.bodyMedium
                            )
                            Text(
                                variant.label,
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        IconButton(onClick = { onRemoveVariant(variant.patternId) }) {
                            Icon(
                                Icons.Default.Delete,
                                contentDescription = "Delete this pattern",
                                tint = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 4.dp),
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    TextButton(onClick = onNewVariant) {
                        Icon(Icons.Default.AddPhotoAlternate, contentDescription = null,
                            modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(6.dp))
                        Text("New pattern")
                    }
                    Spacer(Modifier.weight(1f))
                    TextButton(onClick = onRename) { Text("Rename") }
                    TextButton(onClick = onDelete) {
                        Text("Delete", color = MaterialTheme.colorScheme.error)
                    }
                }
            }
        }
    }
}

/**
 * The photo itself, decoded small. Keyed on the project id so a card that
 * scrolls back into view does not re-read the file every frame.
 */
@Composable
private fun ProjectThumb(projectStore: PhotoProjectStore, projectId: String) {
    var thumb by remember(projectId) { mutableStateOf<Bitmap?>(null) }
    LaunchedEffect(projectId) {
        thumb = withContext(Dispatchers.IO) {
            val f = projectStore.sourceFile(projectId)
            if (!f.exists()) null
            else BitmapLoader.decodeSampled({ f.inputStream() }, maxDim = 256)
        }
    }
    Box(
        modifier = Modifier
            .size(64.dp)
            .clip(RoundedCornerShape(10.dp))
            .background(MaterialTheme.colorScheme.surfaceVariant),
        contentAlignment = Alignment.Center
    ) {
        thumb?.let {
            Image(
                bitmap = it.asImageBitmap(),
                contentDescription = null,
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize()
            )
        } ?: Icon(
            Icons.Default.Photo, contentDescription = null,
            tint = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun RenameDialog(
    initial: String,
    onConfirm: (String) -> Unit,
    onDismiss: () -> Unit
) {
    var text by remember { mutableStateOf(initial) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Rename photo") },
        text = {
            OutlinedTextField(
                value = text,
                onValueChange = { text = it },
                singleLine = true,
                label = { Text("Name") },
                modifier = Modifier.fillMaxWidth()
            )
        },
        confirmButton = {
            TextButton(
                onClick = { onConfirm(text.trim().ifBlank { initial }) },
                enabled = text.isNotBlank()
            ) { Text("Save") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } }
    )
}
