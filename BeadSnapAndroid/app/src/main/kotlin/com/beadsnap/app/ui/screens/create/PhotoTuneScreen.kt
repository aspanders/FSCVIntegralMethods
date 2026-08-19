package com.beadsnap.app.ui.screens.create

import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.model.GridSize
import com.beadsnap.app.data.model.PegboardShape
import com.beadsnap.app.services.ConvertOptions
import com.beadsnap.app.services.ImageConverter
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import kotlin.math.roundToInt

/**
 * Live photo tuning: the finished bead pattern and every control that shapes it
 * on screen at the same time.
 *
 * Before this, board size and colour count had to be committed in a sheet
 * BEFORE seeing a single bead, so getting a good result meant converting,
 * looking, backing out and converting again. Here the pattern is re-derived
 * from the source photo whenever a control moves, so the effect of each knob is
 * visible immediately.
 *
 * The re-conversion is debounced and runs off the main thread; dragging a
 * slider cancels the in-flight conversion rather than queueing one per pixel
 * of travel.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PhotoTuneScreen(
    source: Bitmap,
    initialGridSize: GridSize,
    initialMaxColors: Int,
    onCancel: () -> Unit,
    onDone: (FusePattern, GridSize, Int) -> Unit
) {
    var gridSize   by remember { mutableStateOf(initialGridSize) }
    var maxColors  by remember { mutableIntStateOf(initialMaxColors) }
    var shape      by remember { mutableStateOf(PegboardShape.square) }
    var brightness by remember { mutableFloatStateOf(0f) }
    var contrast   by remember { mutableFloatStateOf(0f) }
    var saturation by remember { mutableFloatStateOf(0f) }
    var chromaLift by remember { mutableFloatStateOf(1f) }

    var pattern by remember { mutableStateOf<FusePattern?>(null) }
    var preview by remember { mutableStateOf<Bitmap?>(null) }
    var working by remember { mutableStateOf(true) }
    var failure by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(gridSize, maxColors, shape, brightness, contrast, saturation, chromaLift) {
        working = true
        failure = null
        // Debounce: a slider drag emits a value per frame, and a full
        // conversion is far too expensive to run at that rate. Restarting the
        // effect cancels this delay, so only the value the finger settles on
        // actually converts.
        delay(180)
        try {
            val result = withContext(Dispatchers.Default) {
                val p = ImageConverter.convert(
                    source, gridSize,
                    ConvertOptions(
                        maxColors  = maxColors,
                        brightness = brightness,
                        contrast   = contrast,
                        saturation = saturation,
                        chromaLift = chromaLift,
                        shape      = shape
                    )
                )
                // Preview at a fixed ~600px regardless of board size, so a
                // 16x16 board is not previewed as a postage stamp.
                val cell = (600 / gridSize.width.coerceAtLeast(1)).coerceIn(4, 40)
                p to ImageConverter.renderToBitmap(p, cellSizePx = cell)
            }
            pattern = result.first
            // Deliberately not recycled: the outgoing bitmap may still be held
            // by a frame that has not been drawn yet, and recycling under it
            // crashes the renderer. Letting it fall out of scope is enough.
            preview = result.second
        } catch (e: kotlinx.coroutines.CancellationException) {
            throw e
        } catch (e: Exception) {
            failure = e.message ?: "Could not convert this photo"
        } finally {
            working = false
        }
    }

    Dialog(
        onDismissRequest = onCancel,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Surface(modifier = Modifier.fillMaxSize()) {
            Column(Modifier.fillMaxSize()) {
                TopAppBar(
                    title = {
                        Column {
                            Text("Adjust Pattern", style = MaterialTheme.typography.titleMedium)
                            val p = pattern
                            Text(
                                if (p == null) "Converting…"
                                else "${p.grid.width}×${p.grid.height}  •  ${p.totalBeads} beads  •  " +
                                     "${p.palette.size} colours",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    },
                    navigationIcon = {
                        IconButton(onClick = onCancel) {
                            Icon(Icons.Default.Close, contentDescription = "Cancel")
                        }
                    },
                    actions = {
                        TextButton(
                            onClick = { pattern?.let { onDone(it, gridSize, maxColors) } },
                            enabled = pattern != null
                        ) { Text("Use This") }
                    }
                )

                // ── Live pattern ──────────────────────────────────────────────
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f)
                        .background(MaterialTheme.colorScheme.surfaceVariant),
                    contentAlignment = Alignment.Center
                ) {
                    preview?.let { bmp ->
                        Image(
                            bitmap = bmp.asImageBitmap(),
                            contentDescription = "Live preview of the bead pattern",
                            contentScale = ContentScale.Fit,
                            modifier = Modifier.fillMaxSize().padding(8.dp)
                        )
                    }
                    if (working) {
                        Box(
                            Modifier.fillMaxSize().background(Color.Black.copy(alpha = 0.18f)),
                            contentAlignment = Alignment.Center
                        ) { CircularProgressIndicator() }
                    }
                    failure?.let {
                        Text(
                            it,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.error,
                            modifier = Modifier.padding(24.dp)
                        )
                    }
                }

                HorizontalDivider()

                // ── Controls, on screen at the same time as the pattern ───────
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 340.dp)
                        .verticalScroll(rememberScrollState())
                        .padding(horizontal = 20.dp, vertical = 12.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Text("Board", style = MaterialTheme.typography.labelLarge)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        PegboardShape.entries.forEach { s ->
                            FilterChip(
                                selected = shape == s,
                                onClick = { shape = s },
                                label = { Text(s.displayName) }
                            )
                        }
                    }

                    Spacer(Modifier.height(4.dp))
                    Text("Size", style = MaterialTheme.typography.labelLarge)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        listOf(GridSize.small, GridSize.medium, GridSize.large, GridSize.xlarge)
                            .forEach { gs ->
                                FilterChip(
                                    selected = gridSize == gs,
                                    onClick = { gridSize = gs },
                                    label = { Text(gs.displayName) }
                                )
                            }
                    }

                    TuneSlider("Colours", "$maxColors", maxColors.toFloat(), 4f..24f, 19) {
                        maxColors = it.roundToInt()
                    }
                    TuneSlider("Brightness", fmt(brightness), brightness, -1f..1f) { brightness = it }
                    TuneSlider("Contrast", fmt(contrast), contrast, -1f..1f) { contrast = it }
                    TuneSlider("Saturation", fmt(saturation), saturation, -1f..1f) { saturation = it }
                    TuneSlider("Colour rescue", fmt(chromaLift), chromaLift, 0f..2f) { chromaLift = it }
                    Text(
                        "Colour rescue pulls washed-out pastels back toward their real hue " +
                        "without over-saturating colours that are already vivid.",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}

private fun fmt(v: Float) = ((v * 100).roundToInt() / 100f).toString()

@Composable
private fun TuneSlider(
    label: String,
    value: String,
    current: Float,
    range: ClosedFloatingPointRange<Float>,
    steps: Int = 0,
    onChange: (Float) -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(label, style = MaterialTheme.typography.labelMedium)
        Text(value, style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
    Slider(
        value = current,
        onValueChange = onChange,
        valueRange = range,
        steps = steps,
        modifier = Modifier.fillMaxWidth()
    )
}
