package com.beadsnap.app.ui.screens.create

import android.graphics.Bitmap
import android.net.Uri
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import com.beadsnap.app.data.model.GridSize
import com.beadsnap.app.services.BackgroundRemover
import com.beadsnap.app.services.MaskModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

/**
 * Photo-to-beads settings: grid size, max colors, and optional background
 * removal with a faded preview and a Remove / Add back touch-up brush.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PhotoSettingsSheet(
    imageUri: Uri,
    gridSize: GridSize,
    maxColors: Int,
    onGridSizeChanged: (GridSize) -> Unit,
    onMaxColorsChanged: (Int) -> Unit,
    onConvert: (maskedBitmap: Bitmap?) -> Unit,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    val sizes = listOf(GridSize.small, GridSize.medium, GridSize.large, GridSize.xlarge)

    var removeBackground by remember { mutableStateOf(false) }
    var workBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var mask by remember { mutableStateOf<MaskModel?>(null) }
    var previewBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var isSegmenting by remember { mutableStateOf(false) }
    var autoUnavailable by remember { mutableStateOf(false) }
    var brushAddsBack by remember { mutableStateOf(false) }

    suspend fun recomposite() {
        val src = workBitmap ?: return
        val m = mask ?: return
        previewBitmap = withContext(Dispatchers.Default) {
            BackgroundRemover.composite(src, m, fadeAlpha = 0.25f)
        }
    }

    // Load the working image + auto mask when removal is first enabled
    LaunchedEffect(removeBackground) {
        if (!removeBackground || workBitmap != null) return@LaunchedEffect
        isSegmenting = true
        try {
            val bmp = withContext(Dispatchers.IO) {
                BackgroundRemover.decodeWorkBitmap {
                    context.contentResolver.openInputStream(imageUri)
                }
            } ?: run { autoUnavailable = true; return@LaunchedEffect }
            workBitmap = bmp
            val m = MaskModel(bmp.width, bmp.height)
            val auto = BackgroundRemover.subjectMask(bmp)
            if (auto != null) m.setAll(auto) else autoUnavailable = true
            mask = m
            recomposite()
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
                    previewBitmap != null -> {
                        MaskEditPreview(
                            preview = previewBitmap!!,
                            onBrush = { nx, ny ->
                                val m = mask ?: return@MaskEditPreview
                                val radius = max(6, (max(m.width, m.height) * 0.05f).roundToInt())
                                m.brush(
                                    (nx * m.width).roundToInt(),
                                    (ny * m.height).roundToInt(),
                                    radius,
                                    keepValue = brushAddsBack
                                )
                            },
                            onBrushEnd = { recomposite() }
                        )
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
                            "Drag on the photo to adjust. Faded areas are left out of the pattern.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        if (autoUnavailable) {
                            Text(
                                "Automatic selection isn't available on this device. Use Remove to paint over the background.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.error
                            )
                        }
                    }
                }
            }

            HorizontalDivider()

            // ── Grid size ─────────────────────────────────────────────────────
            Text("Grid Size", style = MaterialTheme.typography.labelLarge)
            sizes.forEach { gs ->
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.fillMaxWidth().clickable { onGridSizeChanged(gs) }.padding(vertical = 2.dp)
                ) {
                    RadioButton(selected = gridSize == gs, onClick = { onGridSizeChanged(gs) })
                    Spacer(Modifier.width(8.dp))
                    Text(gs.displayName, style = MaterialTheme.typography.bodyMedium)
                }
            }

            HorizontalDivider()

            Text("Max bead colors: $maxColors", style = MaterialTheme.typography.bodyMedium)
            Slider(
                value = maxColors.toFloat(),
                onValueChange = { onMaxColorsChanged(it.roundToInt()) },
                valueRange = 4f..24f,
                steps = 19
            )

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
                        onConvert(masked)
                    },
                    enabled = !isSegmenting,
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Convert")
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
