package com.beadsnap.app.ui.screens.create

import android.content.ContentValues
import android.content.Context
import android.net.Uri
import android.provider.MediaStore
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.beadsnap.app.data.model.BeadColor
import com.beadsnap.app.data.model.CreatorType
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.model.GridSize
import com.beadsnap.app.data.model.PatternCategory
import com.beadsnap.app.data.store.PatternStore
import com.beadsnap.app.services.ImageConverter
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
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
    val scope = rememberCoroutineScope()

    var showBlankDialog    by remember { mutableStateOf(false) }
    var showPhotoSettings  by remember { mutableStateOf(false) }
    var pendingImageUri    by remember { mutableStateOf<Uri?>(null) }
    var isConverting       by remember { mutableStateOf(false) }
    var conversionError    by remember { mutableStateOf<String?>(null) }

    // Photo conversion settings
    var photoGridSize  by remember { mutableStateOf(GridSize.large) }
    var photoMaxColors by remember { mutableIntStateOf(12) }

    // Photo picker
    val photoPickerLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.PickVisualMedia()
    ) { uri ->
        if (uri != null) {
            pendingImageUri = uri
            showPhotoSettings = true
        }
    }

    // Camera
    var cameraImageUri by remember { mutableStateOf<Uri?>(null) }
    val cameraLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.TakePicture()
    ) { success ->
        val uri = cameraImageUri
        if (success && uri != null) {
            pendingImageUri = uri
            showPhotoSettings = true
        } else if (uri != null) {
            // user cancelled — remove the empty MediaStore entry we reserved
            context.contentResolver.delete(uri, null, null)
            cameraImageUri = null
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(title = { Text("Create", style = MaterialTheme.typography.titleLarge) })
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
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
                        ActivityResultContracts.PickVisualMedia.ImageOnly
                    )
                }
            )
            Spacer(Modifier.height(14.dp))
            OptionRow(
                icon = Icons.Default.CameraAlt,
                iconTint = MaterialTheme.colorScheme.tertiary,
                title = "Camera",
                subtitle = "Take a photo and convert it",
                onClick = {
                    val uri = createCameraUri(context)
                    cameraImageUri = uri
                    cameraLauncher.launch(uri)
                }
            )
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
            Box(
                modifier = Modifier.fillMaxSize(),
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

    // Blank canvas dialog
    if (showBlankDialog) {
        BlankCanvasDialog(
            onConfirm = { title, gridSize ->
                val pattern = FusePattern(
                    id = UUID.randomUUID().toString(),
                    title = title.ifBlank { "My Design" },
                    category = PatternCategory.custom,
                    createdBy = CreatorType.user,
                    grid = gridSize,
                    palette = BeadColor.defaultPalette,
                    difficulty = com.beadsnap.app.data.model.Difficulty.easy,
                    version = 1
                )
                onPatternReady(pattern)
                showBlankDialog = false
            },
            onDismiss = { showBlankDialog = false }
        )
    }

    // Photo conversion settings dialog
    if (showPhotoSettings) {
        PhotoSettingsDialog(
            gridSize = photoGridSize,
            maxColors = photoMaxColors,
            onGridSizeChanged = { photoGridSize = it },
            onMaxColorsChanged = { photoMaxColors = it },
            onConvert = {
                showPhotoSettings = false
                val uri = pendingImageUri ?: return@PhotoSettingsDialog
                scope.launch {
                    isConverting = true
                    try {
                        val bitmap = withContext(Dispatchers.IO) {
                            val stream = context.contentResolver.openInputStream(uri)
                                ?: throw Exception("Could not open image")
                            android.graphics.BitmapFactory.decodeStream(stream)
                                ?: throw Exception("Could not decode image")
                        }
                        val pattern = withContext(Dispatchers.Default) {
                            ImageConverter.convert(bitmap, photoGridSize, photoMaxColors)
                        }
                        bitmap.recycle()
                        onPatternReady(pattern)
                    } catch (e: Exception) {
                        conversionError = e.message ?: "Conversion failed"
                    } finally {
                        isConverting = false
                        pendingImageUri = null
                    }
                }
            },
            onDismiss = {
                showPhotoSettings = false
                pendingImageUri = null
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
private fun BlankCanvasDialog(onConfirm: (String, GridSize) -> Unit, onDismiss: () -> Unit) {
    var title    by remember { mutableStateOf("My Design") }
    var gridSize by remember { mutableStateOf(GridSize.large) }
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
            TextButton(onClick = { onConfirm(title, gridSize) }) { Text("Create") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}

@Composable
private fun PhotoSettingsDialog(
    gridSize: GridSize,
    maxColors: Int,
    onGridSizeChanged: (GridSize) -> Unit,
    onMaxColorsChanged: (Int) -> Unit,
    onConvert: () -> Unit,
    onDismiss: () -> Unit
) {
    val sizes = listOf(GridSize.small, GridSize.medium, GridSize.large, GridSize.xlarge)

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Photo to Beads") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Grid Size", style = MaterialTheme.typography.labelLarge)
                sizes.forEach { gs ->
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.fillMaxWidth().clickable { onGridSizeChanged(gs) }.padding(vertical = 4.dp)
                    ) {
                        RadioButton(selected = gridSize == gs, onClick = { onGridSizeChanged(gs) })
                        Spacer(Modifier.width(8.dp))
                        Column {
                            Text(gs.displayName, style = MaterialTheme.typography.bodyMedium)
                            Text(gridSizeHint(gs), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
                HorizontalDivider()
                Text("Max bead colors: $maxColors", style = MaterialTheme.typography.bodyMedium)
                Slider(value = maxColors.toFloat(), onValueChange = { onMaxColorsChanged(it.toInt()) }, valueRange = 4f..24f, steps = 19)
            }
        },
        confirmButton = { TextButton(onClick = onConvert) { Text("Convert") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } }
    )
}

private fun gridSizeHint(gs: GridSize) = when {
    gs.width <= 16  -> "Good for icons & simple shapes"
    gs.width <= 24  -> "Balanced size for most designs"
    gs.width <= 32  -> "Standard fuse bead board size"
    else            -> "Large canvas for detailed art"
}

private fun createCameraUri(context: Context): Uri {
    val values = ContentValues().apply {
        put(MediaStore.Images.Media.DISPLAY_NAME, "beadsnap_camera_${System.currentTimeMillis()}.jpg")
        put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg")
    }
    return context.contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
        ?: throw IllegalStateException("Could not create camera URI")
}
