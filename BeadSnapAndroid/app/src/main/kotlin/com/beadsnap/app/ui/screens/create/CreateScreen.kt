package com.beadsnap.app.ui.screens.create

import android.content.Context
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.beadsnap.app.data.model.BeadColor
import com.beadsnap.app.data.model.CreatorType
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.model.GridSize
import com.beadsnap.app.data.model.PatternCategory
import com.beadsnap.app.data.model.PegboardShape
import com.beadsnap.app.data.store.PatternStore
import com.beadsnap.app.data.store.PhotoProjectStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.UUID

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CreateScreen(
    store: PatternStore,
    onPatternReady: (FusePattern) -> Unit,
    onOpenAIStudio: () -> Unit
) {
    val context = LocalContext.current
    val projectStore = remember { PhotoProjectStore.getInstance(context) }

    var showBlankDialog    by remember { mutableStateOf(false) }
    var pendingImageUri    by remember { mutableStateOf<Uri?>(null) }
    var isConverting       by remember { mutableStateOf(false) }
    var conversionError    by remember { mutableStateOf<String?>(null) }

    // The photo waiting to be tuned into a pattern. Non-null means the studio
    // is up. This is always the UNCUT original: the studio owns the mask, and
    // the project stores the original alongside whatever cut-out came back,
    // because a cut-out cannot be un-cut and "different background removals"
    // is one of the things later variants are meant to differ in.
    var tuneBitmap by remember { mutableStateOf<android.graphics.Bitmap?>(null) }

    // Photo conversion settings: only the starting point now - the real choice
    // happens in PhotoTuneScreen, and what the user lands on is remembered here
    // as the default for the next photo.
    var photoGridSize  by remember { mutableStateOf(GridSize.large) }
    var photoMaxColors by remember { mutableIntStateOf(12) }

    // Remembered across dialog opens, matching iOS
    var blankGridSize  by remember { mutableStateOf(GridSize.large) }
    var blankShape     by remember { mutableStateOf(PegboardShape.square) }

    // Photo picker
    val photoPickerLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.PickVisualMedia()
    ) { uri ->
        if (uri != null) pendingImageUri = uri
    }

    // Camera: captures go to a private cache file (never the user's gallery)
    var cameraImageUri by remember { mutableStateOf<Uri?>(null) }
    var cameraImageFile by remember { mutableStateOf<java.io.File?>(null) }
    val cameraLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.TakePicture()
    ) { success ->
        if (success && cameraImageUri != null) {
            pendingImageUri = cameraImageUri
        } else {
            cameraImageFile?.delete()
            cameraImageFile = null
            cameraImageUri = null
        }
    }

    fun cleanUpCameraCapture() {
        cameraImageFile?.delete()
        cameraImageFile = null
        cameraImageUri = null
    }

    Scaffold(
        topBar = {
            TopAppBar(title = { Text("Create", style = MaterialTheme.typography.titleLarge) })
        }
    ) { padding ->
        Box(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
        Column(
            modifier = Modifier
                .fillMaxHeight()
                .widthIn(max = 520.dp)    // keep option cards scannable on tablets
                .padding(horizontal = 28.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Spacer(Modifier.weight(1f))

            Icon(
                Icons.Default.AutoAwesome, contentDescription = null,
                modifier = Modifier.size(64.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            Spacer(Modifier.height(12.dp))
            Text("What will you make?", style = MaterialTheme.typography.titleLarge)
            Text(
                "Pick a starting point below",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(Modifier.height(36.dp))

            OptionRow(
                icon = Icons.Default.GridOn,
                iconTint = MaterialTheme.colorScheme.primary,
                title = "Blank Canvas",
                subtitle = "Start from scratch on a fresh grid",
                onClick = { showBlankDialog = true }
            )
            Spacer(Modifier.height(14.dp))
            OptionRow(
                icon = Icons.Default.Photo,
                iconTint = MaterialTheme.colorScheme.secondary,
                title = "From Photo",
                subtitle = "Turn a picture into a bead pattern",
                onClick = {
                    photoPickerLauncher.launch(
                        PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)
                    )
                }
            )
            // Hide the Camera option on devices without one (e.g. some tablets),
            // where launching the capture intent would throw
            if (context.packageManager.hasSystemFeature(android.content.pm.PackageManager.FEATURE_CAMERA_ANY)) {
                Spacer(Modifier.height(14.dp))
                OptionRow(
                    icon = Icons.Default.CameraAlt,
                    iconTint = MaterialTheme.colorScheme.tertiary,
                    title = "Camera",
                    subtitle = "Take a photo and convert it",
                    onClick = {
                        try {
                            val file = createCameraFile(context)
                            val uri = androidx.core.content.FileProvider.getUriForFile(
                                context, "${context.packageName}.fileprovider", file
                            )
                            cameraImageFile = file
                            cameraImageUri = uri
                            cameraLauncher.launch(uri)
                        } catch (e: Exception) {
                            cleanUpCameraCapture()
                            conversionError = "Could not open the camera: ${e.message}"
                        }
                    }
                )
            }
            Spacer(Modifier.height(14.dp))
            OptionRow(
                icon = Icons.Default.AutoFixHigh,
                iconTint = MaterialTheme.colorScheme.error,
                title = "AI Studio",
                subtitle = "Generate a pattern with Claude AI",
                onClick = onOpenAIStudio
            )

            Spacer(Modifier.weight(2f))
        }

        if (isConverting) {
            // Scrim blocks all input while converting: without it the user can
            // start a second flow underneath the spinner
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black.copy(alpha = 0.3f))
                    .clickable(
                        interactionSource = remember { MutableInteractionSource() },
                        indication = null
                    ) { /* consume */ },
                contentAlignment = Alignment.Center
            ) {
                Card(shape = RoundedCornerShape(18.dp)) {
                    Column(
                        modifier = Modifier.padding(32.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        CircularProgressIndicator()
                        Text("Converting photo…", style = MaterialTheme.typography.bodyMedium)
                    }
                }
            }
        }
        }
    }

    // Blank canvas dialog
    if (showBlankDialog) {
        BlankCanvasDialog(
            initialGridSize = blankGridSize,
            initialShape = blankShape,
            onConfirm = { title, gridSize, shape ->
                blankGridSize = gridSize
                blankShape = shape
                val pattern = FusePattern(
                    id = UUID.randomUUID().toString(),
                    title = title.trim().ifBlank { "My Design" },
                    category = PatternCategory.custom,
                    createdBy = CreatorType.user,
                    grid = gridSize,
                    palette = BeadColor.defaultPalette,
                    difficulty = com.beadsnap.app.data.model.Difficulty.easy,
                    shape = shape,
                    version = 1
                )
                onPatternReady(pattern)
                showBlankDialog = false
            },
            onDismiss = { showBlankDialog = false }
        )
    }

    // Photo picked: decode it upright and open the studio. There is no
    // settings sheet in front of it any more - board size, colours and the
    // background cut-out are all decisions best made with the beads visible,
    // which is exactly what the studio shows.
    val settingsUri = pendingImageUri
    LaunchedEffect(settingsUri) {
        val uri = settingsUri ?: return@LaunchedEffect
        isConverting = true
        try {
            // decodeUpright applies EXIF orientation and bounds the size; a raw
            // decodeStream here returned sideways photos.
            tuneBitmap = withContext(Dispatchers.IO) {
                com.beadsnap.app.services.BitmapLoader
                    .decodeUpright(context, uri)
                    ?: throw Exception("Could not decode image")
            }
        } catch (e: Exception) {
            conversionError = e.message ?: "Could not open that photo"
        } finally {
            isConverting = false
            pendingImageUri = null
            cleanUpCameraCapture()
        }
    }

    // Live tuning: pattern and controls on screen together. The source bitmap
    // is dropped rather than recycled on the way out - a conversion cancelled
    // mid-getPixels would crash on a recycled bitmap, and the GC handles it.
    tuneBitmap?.let { source ->
        PhotoTuneScreen(
            source = source,
            initialGridSize = photoGridSize,
            initialMaxColors = photoMaxColors,
            onCancel = { tuneBitmap = null },
            onDone = { pattern, gridSize, colors, cutout ->
                photoGridSize = gridSize
                photoMaxColors = colors
                // Keep the PHOTO, not just this one conversion of it. Before
                // this the source was decoded, converted and dropped, so
                // trying a different board size meant hunting the picture down
                // in the gallery again and the earlier attempt was a loose
                // entry in My Designs with no memory of where it came from.
                val project = projectStore.createProject(
                    title  = "Photo ${projectStore.projects.value.size + 1}",
                    source = source,
                    cutout = cutout
                )
                val titled = pattern.copy(title = "${project.title} v1")
                projectStore.addVariant(
                    project.id, titled.id,
                    PhotoProjectStore.labelFor(titled, cutout = cutout != null)
                )
                tuneBitmap = null
                onPatternReady(titled)
            }
        )
    }

    // Conversion error
    conversionError?.let { msg ->
        AlertDialog(
            onDismissRequest = { conversionError = null },
            title = { Text("Conversion Error") },
            text = { Text(msg) },
            confirmButton = {
                TextButton(onClick = { conversionError = null }) { Text("OK") }
            }
        )
    }
}

@Composable
private fun OptionRow(
    icon: ImageVector,
    iconTint: androidx.compose.ui.graphics.Color,
    title: String,
    subtitle: String,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .padding(4.dp),
                contentAlignment = Alignment.Center
            ) {
                Icon(icon, contentDescription = null, tint = iconTint, modifier = Modifier.size(32.dp))
            }
            Column(modifier = Modifier.weight(1f)) {
                Text(title, style = MaterialTheme.typography.titleMedium)
                Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Icon(Icons.Default.ChevronRight, contentDescription = null, tint = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun BlankCanvasDialog(
    initialGridSize: GridSize,
    initialShape: PegboardShape,
    onConfirm: (String, GridSize, PegboardShape) -> Unit,
    onDismiss: () -> Unit
) {
    var title    by remember { mutableStateOf("My Design") }
    var gridSize by remember { mutableStateOf(initialGridSize) }
    var shape    by remember { mutableStateOf(initialShape) }
    val sizes = listOf(GridSize.small, GridSize.medium, GridSize.large, GridSize.xlarge)

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("New Pattern") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(
                    value = title,
                    onValueChange = { title = it },
                    label = { Text("Pattern name") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Text("Pegboard", style = MaterialTheme.typography.labelLarge)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    PegboardShape.entries.forEach { s ->
                        FilterChip(
                            selected = shape == s,
                            onClick = { shape = s },
                            label = { Text(s.displayName) }
                        )
                    }
                }
                Text("Grid Size", style = MaterialTheme.typography.labelLarge)
                sizes.forEach { gs ->
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { gridSize = gs }
                            .padding(vertical = 4.dp)
                    ) {
                        RadioButton(selected = gridSize == gs, onClick = { gridSize = gs })
                        Spacer(Modifier.width(8.dp))
                        Column {
                            Text(gs.displayName, style = MaterialTheme.typography.bodyMedium)
                            Text(gridSizeHint(gs), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = { onConfirm(title, gridSize, shape) }) { Text("Create") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}

private fun gridSizeHint(gs: GridSize) = when {
    gs.width <= 16  -> "Good for icons & simple shapes"
    gs.width <= 24  -> "Balanced size for most designs"
    gs.width <= 32  -> "Standard fuse bead board size"
    else            -> "Large canvas for detailed art"
}

// Private cache file for the capture: never touches the user's gallery,
// and gets deleted once the conversion is done or abandoned.
private fun createCameraFile(context: Context): java.io.File {
    val dir = java.io.File(context.cacheDir, "camera").apply { mkdirs() }
    return java.io.File(dir, "capture_${System.currentTimeMillis()}.jpg")
}
