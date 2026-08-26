package com.beadsnap.app.ui.screens.create

import android.graphics.Bitmap
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoFixHigh
import androidx.compose.material.icons.filled.Brush
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Healing
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.model.GridSize
import com.beadsnap.app.data.model.PegboardShape
import com.beadsnap.app.services.BackgroundRemover
import com.beadsnap.app.services.ConvertOptions
import com.beadsnap.app.services.ImageConverter
import com.beadsnap.app.services.PhotoStudio
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.math.min
import kotlin.math.roundToInt

/** Which group of controls the bottom strip is showing. */
private enum class ControlTab(val label: String) {
    CutOut("Cut out"), Colour("Colour"), Board("Board")
}

/**
 * The photo studio: the photograph and the bead pattern it currently produces,
 * on screen together, with every control that connects them live.
 *
 * The photo sits above the beads in portrait and beside them in landscape,
 * both showing exactly the same crop, so a stroke of the brush and the beads it
 * changes are a glance apart. Painting the mask, moving white balance, changing
 * the board - all of it redraws the pattern immediately rather than on a
 * "convert" button.
 *
 * Why the studio is needed at all: on a real test photo the wooden background
 * took 74% of the beads and 7 of the 12 colours, and the blue subject came out
 * grey because the camera's white balance had crushed the blue channel. Neither
 * is visible until you see the beads, and neither is fixable without seeing the
 * photo at the same time.
 *
 * ALL mutable state lives in this function, deliberately. The portrait and
 * landscape arrangements are separate call sites, so a composable holding state
 * inside a pane would lose it on every rotation - the same trap that made the
 * editor go blank before AppNavigation was restructured.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PhotoTuneScreen(
    source: Bitmap,
    initialGridSize: GridSize,
    initialMaxColors: Int,
    /**
     * Run the automatic cut-out on open. False when the photo handed in has
     * already been cut out once - re-segmenting a subject that is already
     * alone on a transparent field has nothing to find.
     */
    autoSegment: Boolean = true,
    onCancel: () -> Unit,
    onDone: (pattern: FusePattern, grid: GridSize, colors: Int, cutout: Bitmap?) -> Unit
) {
    val scope = rememberCoroutineScope()

    // ── Board ────────────────────────────────────────────────────────────────
    var gridSize by remember { mutableStateOf(initialGridSize) }
    var maxColors by remember { mutableIntStateOf(initialMaxColors) }
    var shape by remember { mutableStateOf(PegboardShape.square) }

    // ── Colour ───────────────────────────────────────────────────────────────
    var brightness by remember { mutableFloatStateOf(0f) }
    var contrast by remember { mutableFloatStateOf(0f) }
    var saturation by remember { mutableFloatStateOf(0f) }
    var chromaLift by remember { mutableFloatStateOf(1f) }
    var wbStrength by remember { mutableFloatStateOf(0f) }
    var wbRaw by remember { mutableStateOf(ConvertOptions.NEUTRAL_GAINS) }

    // ── Cut out ──────────────────────────────────────────────────────────────
    var brushRestores by remember { mutableStateOf(true) }
    var brushSize by remember { mutableFloatStateOf(0.06f) }
    var fitToSubject by remember { mutableStateOf(true) }
    var autoRunning by remember { mutableStateOf(false) }
    var autoUnavailable by remember { mutableStateOf(false) }

    var tab by remember { mutableStateOf(ControlTab.CutOut) }

    // ── Live results ─────────────────────────────────────────────────────────
    var studio by remember { mutableStateOf<PhotoStudio?>(null) }
    var pattern by remember { mutableStateOf<FusePattern?>(null) }
    var photo by remember { mutableStateOf<ImageBitmap?>(null) }
    var cropRect by remember { mutableStateOf<android.graphics.Rect?>(null) }
    var busy by remember { mutableStateOf(true) }
    var committing by remember { mutableStateOf(false) }
    var failure by remember { mutableStateOf<String?>(null) }

    // Every read and write of the studio goes through this one channel, so the
    // brush (main thread, one message per pointer sample) and the rebuild
    // (background) can never touch it at the same time.
    val mailbox = remember { Channel<suspend (PhotoStudio) -> Unit>(Channel.UNLIMITED) }
    fun post(action: suspend (PhotoStudio) -> Unit) { mailbox.trySend(action) }

    LaunchedEffect(source) {
        busy = true
        val built = withContext(Dispatchers.Default) { PhotoStudio.from(source) }
        // Try the automatic cut-out straight away. The background is the single
        // biggest thing standing between a photo and a pattern that looks like
        // its subject, and "Keep all" is one tap away if the guess is wrong.
        //
        // This runs BEFORE the studio is published, so it cannot race the
        // consumer below - once published, every touch goes through the mailbox.
        if (autoSegment) {
            autoRunning = true
            try {
                val work = withContext(Dispatchers.Default) { built.sourceBitmap() }
                val mw = work.width
                val mh = work.height
                val mask = BackgroundRemover.subjectMask(work)
                work.recycle()
                val kept = mask?.count { it } ?: 0
                if (mask == null || kept == 0 || kept == mask.size) {
                    // A mask that keeps everything, or nothing, is not a usable
                    // result even when the segmenter reports success.
                    autoUnavailable = true
                } else {
                    built.adoptMask(mask, mw, mh)
                }
            } catch (e: CancellationException) {
                throw e
            } catch (_: Exception) {
                autoUnavailable = true
            } finally {
                autoRunning = false
            }
        }
        post { }          // buffered; the consumer picks it up when it starts
        studio = built
    }

    // The single consumer. Each pass drains everything already queued before
    // rebuilding, so a burst of brush samples costs one render, not one per
    // sample, and the loop self-balances against however slow the device is.
    LaunchedEffect(studio) {
        val s = studio ?: return@LaunchedEffect
        // Two buffers, alternated: the UI thread may still be drawing the frame
        // we just handed it, and writing new pixels into that same bitmap tears.
        val buffers = arrayOfNulls<Bitmap>(2)
        var slot = 0
        withContext(Dispatchers.Default) {
            while (true) {
                // receive() rather than `for (x in channel)`: cancellation comes
                // back as CancellationException, which the catch below rethrows,
                // so the loop ends with the effect instead of spinning.
                val first = mailbox.receive()
                try {
                    first(s)
                    while (true) {
                        val next = mailbox.tryReceive().getOrNull() ?: break
                        next(s)
                    }
                    val p = s.buildPattern("Imported Photo")
                    val drawn = s.photoPreview(buffers[slot])
                    buffers[slot] = drawn
                    slot = 1 - slot
                    val img = drawn.asImageBitmap()
                    withContext(Dispatchers.Main) {
                        pattern = p
                        photo = img
                        busy = false
                        failure = null
                    }
                } catch (e: CancellationException) {
                    throw e
                } catch (e: Exception) {
                    withContext(Dispatchers.Main) {
                        busy = false
                        failure = e.message ?: "Could not convert this photo"
                    }
                }
            }
        }
    }

    // Any knob moving re-points the studio at a new board. configure() decides
    // what that actually invalidates.
    LaunchedEffect(
        studio, gridSize, maxColors, shape, brightness, contrast, saturation,
        chromaLift, wbStrength, wbRaw, fitToSubject
    ) {
        if (studio == null) return@LaunchedEffect
        val gains = blend(wbRaw, wbStrength)
        post { s ->
            val crop = if (fitToSubject) s.subjectCrop(gridSize.width, gridSize.height) else null
            s.configure(
                cols = gridSize.width,
                rows = gridSize.height,
                crop = crop,
                options = ConvertOptions(
                    maxColors = maxColors,
                    brightness = brightness,
                    contrast = contrast,
                    saturation = saturation,
                    chromaLift = chromaLift,
                    shape = shape,
                    whiteBalance = gains
                ),
                shape = shape
            )
            withContext(Dispatchers.Main) { cropRect = s.currentCrop() }
        }
    }

    fun paint(nx: Float, ny: Float) {
        val restore = brushRestores
        val r = brushSize
        post { s ->
            // Refitting the crop mid-stroke would make the picture jump around
            // under the finger, so the crop is left alone until the knobs move.
            s.brush(nx, ny, r * 0.5f, restore)
        }
    }

    // A full-screen dialog rather than a sibling composable: the studio has to
    // cover the app's navigation bar, which lives above this in the tree, or
    // the controls and the nav bar fight over the bottom of the screen.
    Dialog(
        onDismissRequest = onCancel,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
    Surface(modifier = Modifier.fillMaxSize()) {
        Column(Modifier.fillMaxSize()) {
            TopAppBar(
                title = {
                    Column {
                        Text("Photo Studio", style = MaterialTheme.typography.titleMedium)
                        val p = pattern
                        Text(
                            when {
                                p == null -> "Preparing…"
                                else -> "${p.grid.width}×${p.grid.height}  •  " +
                                        "${p.totalBeads} beads  •  ${p.palette.size} colours"
                            },
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
                        enabled = pattern != null && !committing,
                        onClick = {
                            val s = studio ?: return@TextButton
                            committing = true
                            scope.launch {
                                try {
                                    // Committed patterns are re-derived from the
                                    // FULL-resolution photo. The live preview
                                    // samples a 384px working copy (mean dE2000
                                    // 0.80 against full res), which is right for
                                    // 60fps and wrong for something you keep.
                                    val cutout = if (s.hasRemoval) {
                                        withContext(Dispatchers.Default) { s.maskedFullRes(source) }
                                    } else null
                                    val committed = withContext(Dispatchers.Default) {
                                        ImageConverter.convert(
                                            cutout ?: source,
                                            gridSize,
                                            s.finalOptionsFor(source.width, source.height)
                                        )
                                    }
                                    onDone(committed, gridSize, maxColors, cutout)
                                } catch (e: CancellationException) {
                                    throw e
                                } catch (e: Exception) {
                                    failure = e.message ?: "Could not finish this pattern"
                                } finally {
                                    committing = false
                                }
                            }
                        }
                    ) { Text("Use This") }
                }
            )

            BoxWithConstraints(Modifier.fillMaxWidth().weight(1f)) {
                // Photo above beads in portrait, beside them in landscape.
                // Both arrangements are written out in full rather than shared,
                // and both panes are stateless: a composable holding state
                // inside one would lose it on every rotation, because the two
                // branches are different call sites.
                val landscape = maxWidth > maxHeight
                if (landscape) {
                    Row(Modifier.fillMaxSize()) {
                        PhotoPane(
                            photo = photo,
                            crop = cropRect,
                            onPaint = { nx, ny -> paint(nx, ny) },
                            modifier = Modifier.weight(1f).fillMaxHeight()
                        )
                        VerticalDivider()
                        BeadPane(pattern, Modifier.weight(1f).fillMaxHeight())
                    }
                } else {
                    Column(Modifier.fillMaxSize()) {
                        PhotoPane(
                            photo = photo,
                            crop = cropRect,
                            onPaint = { nx, ny -> paint(nx, ny) },
                            modifier = Modifier.weight(1f).fillMaxWidth()
                        )
                        HorizontalDivider()
                        BeadPane(pattern, Modifier.weight(1f).fillMaxWidth())
                    }
                }
                if (busy || autoRunning || committing) {
                    Box(
                        Modifier.fillMaxSize().background(Color.Black.copy(alpha = 0.12f)),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            CircularProgressIndicator()
                            if (autoRunning) {
                                Spacer(Modifier.height(8.dp))
                                Text("Finding the subject…", style = MaterialTheme.typography.labelMedium)
                            }
                        }
                    }
                }
            }

            HorizontalDivider()

            // ── Controls ─────────────────────────────────────────────────────
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 260.dp)
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    ControlTab.entries.forEach { t ->
                        FilterChip(
                            selected = tab == t,
                            onClick = { tab = t },
                            label = { Text(t.label) }
                        )
                    }
                }
                Spacer(Modifier.height(2.dp))

                when (tab) {
                    ControlTab.CutOut -> {
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            FilterChip(
                                selected = brushRestores,
                                onClick = { brushRestores = true },
                                leadingIcon = {
                                    Icon(Icons.Default.Healing, null, Modifier.size(16.dp))
                                },
                                label = { Text("Add back") }
                            )
                            FilterChip(
                                selected = !brushRestores,
                                onClick = { brushRestores = false },
                                leadingIcon = {
                                    Icon(Icons.Default.Brush, null, Modifier.size(16.dp))
                                },
                                label = { Text("Remove") }
                            )
                        }
                        Text(
                            "Drag on the photo. Faded areas are left out of the pattern, " +
                            "and the beads update as you go.",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        LabelledSlider("Brush size", pct(brushSize / 0.2f), brushSize, 0.01f..0.2f) {
                            brushSize = it
                        }
                        Row(
                            Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                            horizontalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            TextButton(onClick = {
                                val s = studio ?: return@TextButton
                                scope.launch {
                                    autoRunning = true
                                    autoUnavailable = false
                                    try {
                                        val work = withContext(Dispatchers.Default) { s.sourceBitmap() }
                                        val mw = work.width
                                        val mh = work.height
                                        val mask = BackgroundRemover.subjectMask(work)
                                        work.recycle()
                                        val kept = mask?.count { it } ?: 0
                                        if (mask == null || kept == 0 || kept == mask.size) {
                                            autoUnavailable = true
                                        } else {
                                            post { st -> st.adoptMask(mask, mw, mh) }
                                        }
                                    } catch (e: CancellationException) {
                                        throw e
                                    } catch (_: Exception) {
                                        autoUnavailable = true
                                    } finally {
                                        autoRunning = false
                                    }
                                }
                            }) {
                                Icon(Icons.Default.AutoFixHigh, null, Modifier.size(16.dp))
                                Spacer(Modifier.width(4.dp))
                                Text("Auto")
                            }
                            TextButton(onClick = { post { it.keepAll() } }) { Text("Keep all") }
                            TextButton(onClick = { post { it.clearAll() } }) { Text("Clear all") }
                        }
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Checkbox(checked = fitToSubject, onCheckedChange = { fitToSubject = it })
                            Column(Modifier.weight(1f)) {
                                Text("Fit board to subject", style = MaterialTheme.typography.bodyMedium)
                                Text(
                                    "Spend the whole board on what you kept, instead of a " +
                                    "centred square that clips it",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                        if (autoUnavailable) {
                            Text(
                                "Automatic selection didn't find a subject on this device. " +
                                "Nothing has been removed - switch the brush to Remove and " +
                                "paint over the background, or use Clear all and paint the " +
                                "subject back in.",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.error
                            )
                        }
                    }

                    ControlTab.Colour -> {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Button(
                                onClick = {
                                    val s = studio ?: return@Button
                                    scope.launch {
                                        val g = withContext(Dispatchers.Default) { s.measureGreyWorld() }
                                        wbRaw = g
                                        // 0.5 measured best on the test photo:
                                        // enough to bring Light Blue and Light
                                        // Green back, before the highlights
                                        // start bleaching out.
                                        wbStrength = 0.5f
                                    }
                                },
                                enabled = studio != null
                            ) { Text("Auto white balance") }
                            if (wbRaw !== ConvertOptions.NEUTRAL_GAINS) {
                                TextButton(onClick = {
                                    wbRaw = ConvertOptions.NEUTRAL_GAINS
                                    wbStrength = 0f
                                }) { Text("Reset") }
                            }
                        }
                        LabelledSlider(
                            "White balance", pct(wbStrength), wbStrength, 0f..1f
                        ) { wbStrength = it }
                        Text(
                            "Measured from the part of the photo you kept, so the background " +
                            "cannot drag the correction the wrong way. This is the only " +
                            "control that can undo a colour cast rather than a loss of " +
                            "saturation.",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        LabelledSlider("Colour rescue", num(chromaLift), chromaLift, 0f..2f) {
                            chromaLift = it
                        }
                        LabelledSlider("Brightness", num(brightness), brightness, -1f..1f) {
                            brightness = it
                        }
                        LabelledSlider("Contrast", num(contrast), contrast, -1f..1f) { contrast = it }
                        LabelledSlider("Saturation", num(saturation), saturation, -1f..1f) {
                            saturation = it
                        }
                    }

                    ControlTab.Board -> {
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
                        Text("Size", style = MaterialTheme.typography.labelLarge)
                        Row(
                            Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            listOf(GridSize.small, GridSize.medium, GridSize.large, GridSize.xlarge)
                                .forEach { gs ->
                                    FilterChip(
                                        selected = gridSize == gs,
                                        onClick = { gridSize = gs },
                                        label = { Text(gs.displayName) }
                                    )
                                }
                        }
                        LabelledSlider("Colours", "$maxColors", maxColors.toFloat(), 4f..24f, 19) {
                            maxColors = it.roundToInt()
                        }
                    }
                }
            }
        }
    }

    }

    failure?.let { msg ->
        AlertDialog(
            onDismissRequest = { failure = null },
            title = { Text("Photo Studio") },
            text = { Text(msg) },
            confirmButton = { TextButton(onClick = { failure = null }) { Text("OK") } }
        )
    }
}

// ─── Panes ────────────────────────────────────────────────────────────────────

/**
 * The photo, showing exactly the crop the beads are made from, with the brush
 * live on it. Touch positions are mapped through the same letterbox the image
 * is drawn into, so the brush lands where the finger is at any pane shape.
 */
@Composable
private fun PhotoPane(
    photo: ImageBitmap?,
    crop: android.graphics.Rect?,
    onPaint: (Float, Float) -> Unit,
    modifier: Modifier = Modifier
) {
    var box by remember { mutableStateOf(IntSize.Zero) }
    Box(
        modifier = modifier
            .background(MaterialTheme.colorScheme.surfaceVariant)
            .semantics { contentDescription = "Photo. Drag to include or exclude parts of it" },
        contentAlignment = Alignment.Center
    ) {
        if (photo == null) return@Box
        val srcX = crop?.left ?: 0
        val srcY = crop?.top ?: 0
        val srcW = crop?.width()?.coerceAtLeast(1) ?: photo.width
        val srcH = crop?.height()?.coerceAtLeast(1) ?: photo.height

        // The gesture handler must NOT be keyed on anything that changes while
        // a finger is down. It used to be pointerInput(photo, crop, box), and
        // `photo` is replaced by a brand-new ImageBitmap on every preview
        // rebuild - which the first dab of the stroke itself triggers. Compose
        // cancels and restarts the pointer coroutine whenever a key changes,
        // and the restarted block waits at awaitFirstDown(), which only fires
        // on a finger that goes from up to down. A finger already pressed never
        // produces one, so the rest of the stroke went nowhere: the brush
        // painted a single dab and then ignored the drag until you lifted and
        // tapped again.
        //
        // So the handler is created once, and the values it needs are read at
        // EVENT time instead of captured at composition time. `box` is already
        // a snapshot state read through its delegate, so it is live as written;
        // the parameters are not, and go through rememberUpdatedState.
        val liveCrop by rememberUpdatedState(crop)
        val liveImage by rememberUpdatedState(photo)
        val livePaint by rememberUpdatedState(onPaint)

        Canvas(
            modifier = Modifier
                .fillMaxSize()
                .onSizeChanged { box = it }
                .pointerInput(Unit) {
                    awaitEachGesture {
                        fun emit(pos: Offset) {
                            if (box.width == 0 || box.height == 0) return
                            val img = liveImage
                            val c = liveCrop
                            val sx = c?.left ?: 0
                            val sy = c?.top ?: 0
                            val sw = c?.width()?.coerceAtLeast(1) ?: img.width
                            val sh = c?.height()?.coerceAtLeast(1) ?: img.height
                            val scale = min(
                                box.width.toFloat() / sw,
                                box.height.toFloat() / sh
                            )
                            val drawW = sw * scale
                            val drawH = sh * scale
                            val left = (box.width - drawW) / 2f
                            val top = (box.height - drawH) / 2f
                            val u = (pos.x - left) / drawW
                            val v = (pos.y - top) / drawH
                            if (u !in 0f..1f || v !in 0f..1f) return
                            // Back out of the crop into whole-photo coordinates,
                            // which is what the studio's brush speaks.
                            val paintNow = livePaint
                            paintNow(
                                (sx + u * sw) / img.width,
                                (sy + v * sh) / img.height
                            )
                        }
                        val down = awaitFirstDown()
                        down.consume()
                        emit(down.position)
                        var pressed = true
                        while (pressed) {
                            val event = awaitPointerEvent()
                            pressed = event.changes.any { it.pressed }
                            event.changes.forEach { c ->
                                if (c.pressed) { c.consume(); emit(c.position) }
                            }
                        }
                    }
                }
        ) {
            val scale = min(size.width / srcW, size.height / srcH)
            val drawW = srcW * scale
            val drawH = srcH * scale
            drawImage(
                image = photo,
                srcOffset = IntOffset(srcX, srcY),
                srcSize = IntSize(srcW, srcH),
                dstOffset = IntOffset(
                    ((size.width - drawW) / 2f).roundToInt(),
                    ((size.height - drawH) / 2f).roundToInt()
                ),
                dstSize = IntSize(drawW.roundToInt(), drawH.roundToInt())
            )
        }
    }
}

/** The live bead pattern, drawn straight from the cells - no intermediate bitmap. */
@Composable
private fun BeadPane(pattern: FusePattern?, modifier: Modifier = Modifier) {
    val empty = MaterialTheme.colorScheme.surfaceVariant
    Box(
        modifier = modifier.background(MaterialTheme.colorScheme.surface),
        contentAlignment = Alignment.Center
    ) {
        val p = pattern ?: return@Box
        val lookup = remember(p.version, p.id) { p.palette.associate { it.id to it.composeColor } }
        val cells = remember(p.version, p.id) {
            p.cells.mapNotNull { c -> c.colorId?.let { Triple(c.x, c.y, it) } }
        }
        Canvas(Modifier.fillMaxSize().padding(6.dp)) {
            drawBeads(cells, lookup, p.grid.width, p.grid.height, empty)
        }
    }
}

private fun DrawScope.drawBeads(
    cells: List<Triple<Int, Int, String>>,
    lookup: Map<String, Color>,
    cols: Int,
    rows: Int,
    empty: Color
) {
    if (cols <= 0 || rows <= 0) return
    val step = min(size.width / cols, size.height / rows)
    val ox = (size.width - step * cols) / 2f
    val oy = (size.height - step * rows) / 2f
    val r = step / 2f
    val holeR = step * 0.17f
    // Faint ground so an empty board still reads as a board.
    drawRect(color = empty.copy(alpha = 0.35f), topLeft = Offset(ox, oy),
             size = Size(step * cols, step * rows))
    cells.forEach { (x, y, id) ->
        val color = lookup[id] ?: return@forEach
        val c = Offset(ox + x * step + r, oy + y * step + r)
        drawCircle(color = color, radius = r, center = c)
        if (step > 5f) drawCircle(Color.White.copy(alpha = 0.11f), holeR, c)
    }
}

// ─── Small pieces ─────────────────────────────────────────────────────────────

@Composable
private fun LabelledSlider(
    label: String,
    value: String,
    current: Float,
    range: ClosedFloatingPointRange<Float>,
    steps: Int = 0,
    onChange: (Float) -> Unit
) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
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

/** Interpolate measured gains toward neutral by [strength]. */
private fun blend(raw: FloatArray, strength: Float): FloatArray {
    if (strength <= 0f) return ConvertOptions.NEUTRAL_GAINS
    val s = strength.coerceIn(0f, 1f)
    return FloatArray(3) { 1f + s * (raw[it] - 1f) }
}

private fun pct(v: Float) = "${(v * 100).roundToInt()}%"
private fun num(v: Float) = "${(v * 100).roundToInt() / 100f}"
