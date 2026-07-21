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

    // Remembered across dialog opens, matching iOS
    var blankGridSize by remember { mutableStateOf(GridSize.large) }

    // Photo picker
    val photoPickerLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.PickVisualMedia()
    ) { uri ->
        if (uri != null) {
            pendingImageUri = uri
            showPhotoSettings = true
        }
    }

    // Camera: captures go to a private cache file (never the user's gallery)
    var cameraImageUri by remember { mutableStateOf<Uri?>(null) }
    var cameraImageFile by remember { mutableStateOf<java.io.File?>(null) }
    val cameraLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.TakePicture()
    ) { success ->
        if (success && cameraImageUri != null) {
            pendingImageUri = cameraImageUri
            showPhotoSettings = true
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
            onConfirm = { title, gridSize ->
                blankGridSize = gridSize
                val pattern = FusePattern(
                    id = UUID.randomUUID().toString(),
                    title = title.trim().ifBlank { "My Design" },
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

    // Photo conversion settings (grid, colors, background removal)
    val settingsUri = pendingImageUri
    if (showPhotoSettings && settingsUri != null) {
        PhotoSettingsSheet(
            imageUri = settingsUri,
            gridSize = photoGridSize,
            maxColors = photoMaxColors,
            onGridSizeChanged = { photoGridSize = it },
            onMaxColorsChanged = { photoMaxColors = it },
            onConvert = { maskedBitmap ->
                showPhotoSettings = false
                scope.launch {
                    isConverting = true
                    try {
                        val bitmap = maskedBitmap ?: withContext(Dispatchers.IO) {
                            val stream = context.contentResolver.openInputStream(settingsUri)
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
                        cleanUpCameraCapture()
                    }
                }
            },
            onDismiss = {
                showPhotoSettings = false
                pendingImageUri = null
                cleanUpCameraCapture()
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
    onConfirm: (String, GridSize) -> Unit,
    onDismiss: () -> Unit
) {
    var title    by remember { mutableStateOf("My Design") }
    var gridSize by remember { mutableStateOf(initialGridSize) }
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
