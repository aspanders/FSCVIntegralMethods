package com.beadsnap.app.ui.screens.create

import android.graphics.Bitmap
import android.net.Uri
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import com.beadsnap.app.services.BackgroundRemover
import com.beadsnap.app.services.MaskModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

/**
 * Step one of the photo flow: decide what part of the photo becomes beads.
 *
 * Board size, colour count and the colour controls deliberately do NOT live
 * here any more - they are tuned in PhotoTuneScreen with the finished pattern
 * visible, instead of being guessed before a single bead has been seen.
 * Background removal stays here because it needs the photo itself, not the
 * pattern, to brush against.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PhotoSettingsSheet(
    imageUri: Uri,
    onNext: (maskedBitmap: Bitmap?) -> Unit,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    var removeBackground by remember { mutableStateOf(false) }
    var workBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var mask by remember { mutableStateOf<MaskModel?>(null) }
    var previewBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var isSegmenting by remember { mutableStateOf(false) }
    var autoUnavailable by remember { mutableStateOf(false) }
    var brushAddsBack by remember { mutableStateOf(false) }
    var loadError by remember { mutableStateOf<String?>(null) }
    var brushScale by remember { mutableFloatStateOf(0.05f) }
    var autoAttempt by remember { mutableIntStateOf(0) }

    suspend fun recomposite() {
        val src = workBitmap ?: return
        val m = mask ?: return
        previewBitmap = withContext(Dispatchers.Default) {
            BackgroundRemover.composite(src, m, fadeAlpha = 0.25f)
        }
    }

    // Load the working image and try the automatic mask when removal is first
    // enabled, or when the user asks to retry.
    //
    // Every failure path here used to leave previewBitmap null while the UI
    // below only had branches for "segmenting" and "preview ready", so a photo
    // that could not be decoded rendered NOTHING AT ALL: the switch went on and
    // the sheet just sat there. The manual brush was unreachable too, because it
    // needs workBitmap, which was only ever set on the happy path. Now the
    // bitmap loads independently of segmentation, so manual mode always works
    // even when the automatic pass is unavailable, and every failure is named.
    LaunchedEffect(removeBackground, autoAttempt) {
        if (!removeBackground) return@LaunchedEffect
        if (workBitmap != null && autoAttempt == 0) return@LaunchedEffect
        isSegmenting = true
        loadError = null
        autoUnavailable = false
        try {
            val bmp = workBitmap ?: withContext(Dispatchers.IO) {
                BackgroundRemover.decodeWorkBitmap {
                    context.contentResolver.openInputStream(imageUri)
                }
            }
            if (bmp == null) {
                loadError = "Could not open this photo for editing. Try picking it again."
                return@LaunchedEffect
            }
            workBitmap = bmp
            val m = MaskModel(bmp.width, bmp.height)
            val auto = BackgroundRemover.subjectMask(bmp)
            if (auto == null) {
                autoUnavailable = true
            } else {
                // A mask that keeps everything, or nothing, is not a usable
                // result even though ML Kit "succeeded" - treat it as a miss so
                // the user is told to paint rather than left wondering why the
                // preview looks untouched.
                val kept = auto.count { it }
                if (kept == 0 || kept == auto.size) autoUnavailable = true else m.setAll(auto)
            }
            mask = m
            recomposite()
        } catch (e: kotlinx.coroutines.CancellationException) {
            throw e   // the sheet closed or the effect restarted; not a failure
        } catch (e: Exception) {
            loadError = "Background removal failed: ${e.message ?: "unknown error"}"
        } finally {
            isSegmenting = false
        }
    }

    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 24.dp)
                .padding(bottom = 40.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text("Photo to Beads", style = MaterialTheme.typography.titleLarge)
            Text(
                "Choose what to keep. Board size and colours come next, with the " +
                "pattern in front of you.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            // ── Background removal ────────────────────────────────────────────
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column(Modifier.weight(1f)) {
                    Text("Remove background", style = MaterialTheme.typography.bodyLarge)
                    Text(
                        "Keep just the subject of the photo",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Switch(checked = removeBackground, onCheckedChange = { removeBackground = it })
            }

            if (removeBackground) {
                when {
                    isSegmenting -> {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            modifier = Modifier.padding(vertical = 8.dp)
                        ) {
                            CircularProgressIndicator(modifier = Modifier.size(20.dp))
                            Text("Finding the subject…", style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                    loadError != null -> {
                        Text(
                            loadError!!,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.error
                        )
                        TextButton(onClick = { autoAttempt++ }) { Text("Try again") }
                    }
                    previewBitmap != null -> {
                        MaskEditPreview(
                            preview = previewBitmap!!,
                            onBrush = { nx, ny ->
                                val m = mask ?: return@MaskEditPreview
                                val radius = max(4, (max(m.width, m.height) * brushScale).roundToInt())
                                m.brush(
                                    (nx * m.width).roundToInt(),
                                    (ny * m.height).roundToInt(),
                                    radius,
                                    keepValue = brushAddsBack
                                )
                            },
                            onBrushEnd = { recomposite() }
                        )

                        // Manual mode, PowerPoint style: paint what to drop and
                        // what to bring back.
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            FilterChip(
                                selected = !brushAddsBack,
                                onClick = { brushAddsBack = false },
                                label = { Text("Remove") }
                            )
                            FilterChip(
                                selected = brushAddsBack,
                                onClick = { brushAddsBack = true },
                                label = { Text("Add back") }
                            )
                        }
                        Text(
                            "Brush size",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Slider(
                            value = brushScale,
                            onValueChange = { brushScale = it },
                            valueRange = 0.02f..0.18f
                        )

                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            TextButton(onClick = { autoAttempt++ }) { Text("Auto again") }
                            TextButton(onClick = {
                                val m = mask
                                if (m != null) {
                                    m.setAll(BooleanArray(m.width * m.height) { true })
                                    scope.launch { recomposite() }
                                }
                            }) { Text("Keep all") }
                            TextButton(onClick = {
                                val m = mask
                                if (m != null) {
                                    m.setAll(BooleanArray(m.width * m.height) { false })
                                    scope.launch { recomposite() }
                                }
                            }) { Text("Clear all") }
                        }

                        Text(
                            "Drag on the photo to adjust. Faded areas are left out of the pattern.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        if (autoUnavailable) {
                            Text(
                                "Automatic selection didn't find a subject on this device, so nothing " +
                                "has been removed yet. Paint over the background with Remove, or start " +
                                "from Clear all and paint the subject back in with Add back.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.error
                            )
                        }
                    }
                    else -> {
                        // Reachable if the bitmap loaded but the first composite
                        // has not landed yet. Previously this case rendered
                        // nothing at all, which is what "not functioning" looked
                        // like on device.
                        Text(
                            "Preparing the photo…",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }

            HorizontalDivider()

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(onClick = onDismiss, modifier = Modifier.weight(1f)) {
                    Text("Cancel")
                }
                Button(
                    onClick = {
                        val masked = if (removeBackground) {
                            val src = workBitmap
                            val m = mask
                            if (src != null && m != null) BackgroundRemover.maskedForConversion(src, m) else null
                        } else null
                        onNext(masked)
                    },
                    enabled = !isSegmenting,
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Next")
                }
            }
        }
    }
}

/**
 * The faded-background preview with drag-to-brush. Touch positions are mapped
 * through the ContentScale.Fit letterbox into normalized image coordinates.
 */
@Composable
private fun MaskEditPreview(
    preview: Bitmap,
    onBrush: (nx: Float, ny: Float) -> Unit,
    onBrushEnd: suspend () -> Unit
) {
    var boxSize by remember { mutableStateOf(IntSize.Zero) }
    var brushTick by remember { mutableIntStateOf(0) }

    LaunchedEffect(brushTick) {
        if (brushTick > 0) onBrushEnd()
    }

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(240.dp)
            .clip(RoundedCornerShape(12.dp))
            .background(MaterialTheme.colorScheme.surfaceVariant)
            .onSizeChanged { boxSize = it }
            .pointerInput(preview.width, preview.height) {
                awaitEachGesture {
                    fun mapToImage(pos: Offset): Pair<Float, Float>? {
                        if (boxSize == IntSize.Zero) return null
                        val bw = boxSize.width.toFloat()
                        val bh = boxSize.height.toFloat()
                        val scale = min(bw / preview.width, bh / preview.height)
                        val drawnW = preview.width * scale
                        val drawnH = preview.height * scale
                        val left = (bw - drawnW) / 2f
                        val top = (bh - drawnH) / 2f
                        val nx = (pos.x - left) / drawnW
                        val ny = (pos.y - top) / drawnH
                        return if (nx in 0f..1f && ny in 0f..1f) nx to ny else null
                    }

                    val down = awaitFirstDown()
                    mapToImage(down.position)?.let { (nx, ny) -> onBrush(nx, ny) }
                    var moves = 0
                    var stillPressed = true
                    while (stillPressed) {
                        val event = awaitPointerEvent()
                        stillPressed = event.changes.any { it.pressed }
                        event.changes.forEach { change ->
                            if (change.pressed) {
                                change.consume()
                                mapToImage(change.position)?.let { (nx, ny) ->
                                    onBrush(nx, ny)
                                    if (++moves % 4 == 0) brushTick++   // live fade while dragging
                                }
                            }
                        }
                    }
                    brushTick++   // final recomposite at stroke end
                }
            },
        contentAlignment = Alignment.Center
    ) {
        Image(
            bitmap = preview.asImageBitmap(),
            contentDescription = "Background removal preview. Faded areas will be removed",
            contentScale = ContentScale.Fit,
            modifier = Modifier.fillMaxSize()
        )
    }
}
