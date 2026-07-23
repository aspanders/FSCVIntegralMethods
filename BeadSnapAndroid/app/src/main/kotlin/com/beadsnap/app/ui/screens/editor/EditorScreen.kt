package com.beadsnap.app.ui.screens.editor

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import com.beadsnap.app.data.model.BeadColor
import com.beadsnap.app.data.model.CreatorType
import com.beadsnap.app.data.model.FusePattern
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.ui.graphics.luminance
import com.beadsnap.app.services.ImageConverter

private const val MIN_CELL_PX = 18
private const val MAX_CELL_PX = 120
private const val CELL_STEP   = 10

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditorScreen(
    viewModel: EditorViewModel,
    onBack: () -> Unit
) {
    val context     = LocalContext.current
    val scope       = rememberCoroutineScope()
    val pattern     by viewModel.pattern.collectAsState()
    val selectedColor by viewModel.selectedColor.collectAsState()
    val canUndo     by viewModel.canUndo.collectAsState()
    val cellMap     by viewModel.cellMap.collectAsState()
    val colorLookup = remember(pattern.version) { viewModel.colorLookup() }

    var cellSizePx  by remember { mutableIntStateOf(36) }
    var scrollMode  by remember { mutableStateOf(false) }
    var isErasing   by remember { mutableStateOf(false) }

    var showSaveAs    by remember { mutableStateOf(false) }
    var showClearAll  by remember { mutableStateOf(false) }
    var showColorList by remember { mutableStateOf(false) }
    var showInstructions by remember { mutableStateOf(false) }
    var isExporting   by remember { mutableStateOf(false) }
    var exportError   by remember { mutableStateOf<String?>(null) }
    val snackbarHostState = remember { SnackbarHostState() }

    // First-paint hint: mark seen immediately so backing out early doesn't reshow it
    val prefs = remember { context.getSharedPreferences("beadsnap", Context.MODE_PRIVATE) }
    var showHint by remember {
        val seen = prefs.getBoolean("hasSeenPaintHint", false)
        if (!seen) prefs.edit().putBoolean("hasSeenPaintHint", true).apply()
        mutableStateOf(!seen)
    }
    LaunchedEffect(showHint) {
        if (showHint) {
            delay(3_000)
            showHint = false
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(pattern.title, style = MaterialTheme.typography.titleMedium)
                        Text(
                            "${pattern.grid.width}×${pattern.grid.height}  •  ${pattern.totalBeads} beads",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(
                        onClick = { viewModel.undo() },
                        enabled = canUndo,
                        modifier = Modifier.semantics { contentDescription = "Undo" }
                    ) {
                        Icon(Icons.Default.Undo, contentDescription = null)
                    }
                    IconButton(onClick = { showColorList = true },
                        modifier = Modifier.semantics { contentDescription = "Bead counts" }) {
                        Icon(Icons.Default.List, contentDescription = null)
                    }
                    if (pattern.hasInstructions) {
                        IconButton(onClick = { showInstructions = true },
                            modifier = Modifier.semantics { contentDescription = "Build instructions" }) {
                            Icon(Icons.Default.MenuBook, contentDescription = null)
                        }
                    }
                    IconButton(
                        onClick = {
                            scope.launch {
                                isExporting = true
                                try { exportPng(context, viewModel) }
                                catch (e: Exception) { exportError = e.message }
                                finally { isExporting = false }
                            }
                        },
                        modifier = Modifier.semantics { contentDescription = "Export PNG" }
                    ) {
                        Icon(Icons.Default.Share, contentDescription = null)
                    }
                    var menuExpanded by remember { mutableStateOf(false) }
                    IconButton(onClick = { menuExpanded = true }) {
                        Icon(Icons.Default.MoreVert, contentDescription = "More options")
                    }
                    DropdownMenu(expanded = menuExpanded, onDismissRequest = { menuExpanded = false }) {
                        if (pattern.createdBy == CreatorType.user) {
                            DropdownMenuItem(
                                text = { Text("Save As…") },
                                leadingIcon = { Icon(Icons.Default.SaveAs, null) },
                                onClick = { menuExpanded = false; showSaveAs = true }
                            )
                        }
                        DropdownMenuItem(
                            text = { Text("Clear All") },
                            leadingIcon = { Icon(Icons.Default.DeleteSweep, null) },
                            onClick = { menuExpanded = false; showClearAll = true }
                        )
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
        ) {
            // System pattern banner
            if (pattern.createdBy == CreatorType.system) {
                Surface(
                    color = MaterialTheme.colorScheme.secondaryContainer,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            "System pattern. Tap Save As to keep your changes",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSecondaryContainer,
                            modifier = Modifier.weight(1f)
                        )
                        TextButton(onClick = { showSaveAs = true }) { Text("Save As") }
                    }
                }
            }

            // Zoom + mode controls
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 12.dp, vertical = 4.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                IconButton(
                    onClick = { cellSizePx = (cellSizePx - CELL_STEP).coerceAtLeast(MIN_CELL_PX) },
                    enabled = cellSizePx > MIN_CELL_PX
                ) {
                    Icon(Icons.Default.ZoomOut, contentDescription = "Zoom out")
                }
                Text(
                    "${cellSizePx}px",
                    style = MaterialTheme.typography.labelMedium,
                    modifier = Modifier.width(40.dp),
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center
                )
                IconButton(
                    onClick = { cellSizePx = (cellSizePx + CELL_STEP).coerceAtMost(MAX_CELL_PX) },
                    enabled = cellSizePx < MAX_CELL_PX
                ) {
                    Icon(Icons.Default.ZoomIn, contentDescription = "Zoom in")
                }
                Spacer(Modifier.weight(1f))
                FilterChip(
                    selected = isErasing,
                    onClick = { isErasing = !isErasing },
                    label = { Text("Erase") },
                    leadingIcon = {
                        Icon(
                            Icons.Default.Delete,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp)
                        )
                    },
                    modifier = Modifier.semantics {
                        contentDescription = if (isErasing) "Eraser on" else "Eraser off"
                    }
                )
                Spacer(Modifier.width(8.dp))
                FilterChip(
                    selected = scrollMode,
                    onClick = { scrollMode = !scrollMode },
                    label = { Text(if (scrollMode) "Scroll" else "Paint") },
                    leadingIcon = {
                        Icon(
                            if (scrollMode) Icons.Default.PanTool else Icons.Default.Brush,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                )
            }

            HorizontalDivider()

            // Grid area
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
            ) {
                BeadGridCanvas(
                    viewModel   = viewModel,
                    cellMap     = cellMap,
                    colorLookup = colorLookup,
                    cellSizePx  = cellSizePx,
                    scrollMode  = scrollMode,
                    isErasing   = isErasing
                )
                if (showHint) {
                    Surface(
                        modifier = Modifier
                            .align(Alignment.Center)
                            .clip(RoundedCornerShape(12.dp))
                            .clickable { showHint = false },
                        color = MaterialTheme.colorScheme.inverseSurface.copy(alpha = 0.85f)
                    ) {
                        Text(
                            "Tap or drag to paint beads",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.inverseOnSurface,
                            modifier = Modifier.padding(horizontal = 20.dp, vertical = 12.dp)
                        )
                    }
                }
                if (isExporting) {
                    Box(Modifier.fillMaxSize().background(Color.Black.copy(alpha = 0.4f)),
                        contentAlignment = Alignment.Center) {
                        CircularProgressIndicator()
                    }
                }
            }

            HorizontalDivider()

            // Selected color name (sighted users need it too, not just TalkBack)
            Text(
                text = selectedColor.name,
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(start = 16.dp, top = 6.dp)
            )

            // Palette row
            PaletteRow(
                palette       = pattern.palette,
                selectedColor = selectedColor,
                onSelect      = { viewModel.selectColor(it) }
            )
        }
    }

    if (showSaveAs) {
        SaveAsDialog(
            initialTitle = pattern.title,
            onConfirm = { title ->
                viewModel.saveAs(title)
                showSaveAs = false
                scope.launch { snackbarHostState.showSnackbar("Pattern saved!") }
            },
            onDismiss = { showSaveAs = false }
        )
    }

    if (showClearAll) {
        AlertDialog(
            onDismissRequest = { showClearAll = false },
            title = { Text("Clear All Beads?") },
            text = { Text("This will remove all placed beads. You can undo immediately after.") },
            confirmButton = {
                TextButton(onClick = { viewModel.clearAll(); showClearAll = false }) {
                    Text("Clear", color = MaterialTheme.colorScheme.error)
                }
            },
            dismissButton = {
                TextButton(onClick = { showClearAll = false }) { Text("Cancel") }
            }
        )
    }

    if (showColorList) {
        BeadCountSheet(
            counts    = viewModel.colorCounts,
            total     = viewModel.totalBeads,
            onDismiss = { showColorList = false },
            onShare   = { scope.launch { shareShoppingList(context, viewModel.colorCounts, pattern.title) } }
        )
    }

    if (showInstructions) {
        InstructionsSheet(
            title         = pattern.title,
            buildGuide    = pattern.buildGuide,
            assemblyGuide = pattern.assemblyGuide,
            onDismiss     = { showInstructions = false }
        )
    }

    exportError?.let { msg ->
        AlertDialog(
            onDismissRequest = { exportError = null },
            title = { Text("Export Failed") },
            text = { Text(msg) },
            confirmButton = { TextButton(onClick = { exportError = null }) { Text("OK") } }
        )
    }
}

// ─── Bead grid canvas ─────────────────────────────────────────────────────────

@Composable
private fun BeadGridCanvas(
    viewModel: EditorViewModel,
    cellMap: Map<String, String>,
    colorLookup: Map<String, Color>,
    cellSizePx: Int,
    scrollMode: Boolean,
    isErasing: Boolean
) {
    val density    = LocalDensity.current
    val cols       = viewModel.gridWidth
    val rows       = viewModel.gridHeight
    val cellDp: Dp = with(density) { cellSizePx.toDp() }
    val totalW     = cellDp * cols
    val totalH     = cellDp * rows
    val gridColor  = MaterialTheme.colorScheme.outline.copy(alpha = 0.25f)
    val emptyColor = MaterialTheme.colorScheme.surfaceVariant

    // One pair of scroll states for BOTH modes: the offset persists when the
    // user toggles to paint mode, so every cell of a large grid stays reachable.
    val hScroll = rememberScrollState()
    val vScroll = rememberScrollState()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .horizontalScroll(hScroll, enabled = scrollMode)
            .verticalScroll(vScroll, enabled = scrollMode)
    ) {
        Canvas(
            modifier = Modifier
                .size(totalW, totalH)
                .pointerInput(cellSizePx, cols, rows, scrollMode, isErasing) {
                    if (scrollMode) return@pointerInput
                    awaitEachGesture {
                        // Positions are in full-canvas coordinates, so painting
                        // works at any scroll offset. Taps toggle; drags paint
                        // set-only with a single undo entry per stroke.
                        fun cellAt(pos: Offset): Pair<Int, Int>? {
                            val x = (pos.x / cellSizePx).toInt()
                            val y = (pos.y / cellSizePx).toInt()
                            return if (x in 0 until cols && y in 0 until rows) x to y else null
                        }
                        fun apply(cell: Pair<Int, Int>) {
                            if (isErasing) viewModel.strokeErase(cell.first, cell.second)
                            else viewModel.strokePaint(cell.first, cell.second)
                        }

                        val down = awaitFirstDown()
                        val downCell = cellAt(down.position)
                        var strokeActive = false
                        var lastCell = downCell

                        var stillPressed = true
                        while (stillPressed) {
                            val event = awaitPointerEvent()
                            stillPressed = event.changes.any { it.pressed }
                            event.changes.forEach { change ->
                                if (!change.pressed) return@forEach
                                change.consume()
                                val cell = cellAt(change.position) ?: return@forEach
                                if (!strokeActive) {
                                    if (cell == downCell) return@forEach
                                    viewModel.beginStroke()
                                    strokeActive = true
                                    downCell?.let { apply(it) }
                                }
                                if (cell != lastCell) {
                                    lastCell = cell
                                    apply(cell)
                                }
                            }
                        }

                        // finger never left the starting cell → it's a tap
                        if (!strokeActive && downCell != null) {
                            if (isErasing) viewModel.clearCell(downCell.first, downCell.second)
                            else viewModel.tapCell(downCell.first, downCell.second)
                        }
                    }
                }
        ) {
            drawBeadGrid(cellMap, colorLookup, cols, rows, cellSizePx.toFloat(), emptyColor, gridColor)
        }
    }
}

private fun DrawScope.drawBeadGrid(
    cellMap: Map<String, String>,
    colorLookup: Map<String, Color>,
    cols: Int,
    rows: Int,
    step: Float,
    emptyColor: Color,
    gridColor: Color
) {
    val holeR = step * 0.17f
    for (row in 0 until rows) {
        for (col in 0 until cols) {
            val key    = "$col,$row"
            val filled = cellMap[key]?.let { colorLookup[it] }
            val color  = filled ?: emptyColor
            val center = Offset(col * step + step / 2f, row * step + step / 2f)
            // Bead radius = half the pitch, so fused beads touch their neighbors.
            drawCircle(color = color, radius = step / 2f, center = center)
            // Faint center hole gives filled beads the fused-bead look.
            if (filled != null) {
                drawCircle(color = Color.White.copy(alpha = 0.11f), radius = holeR, center = center)
            }
            // subtle grid lines
            drawRect(
                color    = gridColor,
                topLeft  = Offset(col * step, row * step),
                size     = Size(step, step),
                style    = androidx.compose.ui.graphics.drawscope.Stroke(width = 0.5f)
            )
        }
    }
}

// ─── Palette row ──────────────────────────────────────────────────────────────

@Composable
private fun PaletteRow(
    palette: List<BeadColor>,
    selectedColor: BeadColor,
    onSelect: (BeadColor) -> Unit
) {
    LazyRow(
        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(palette, key = { it.id }) { color ->
            val selected = color.id == selectedColor.id
            Box(
                modifier = Modifier
                    .size(if (selected) 44.dp else 36.dp)
                    .clip(CircleShape)
                    .background(
                        if (selected) MaterialTheme.colorScheme.primary
                        else color.composeColor
                    )
                    .padding(if (selected) 3.dp else 0.dp)
                    .clip(CircleShape)
                    .background(color.composeColor)
                    .pointerInput(color.id) { detectTapGestures { onSelect(color) } }
                    .semantics {
                        contentDescription = "${color.name}${if (selected) ", selected" else ""}"
                    },
                contentAlignment = Alignment.Center
            ) {
                if (selected) {
                    Icon(
                        Icons.Default.Check,
                        contentDescription = null,
                        // black check on light beads, white on dark: always visible
                        tint = if (color.composeColor.luminance() < 0.5f) Color.White else Color.Black,
                        modifier = Modifier.size(20.dp)
                    )
                }
            }
        }
    }
}

// ─── Save As dialog ───────────────────────────────────────────────────────────

@Composable
private fun SaveAsDialog(
    initialTitle: String,
    onConfirm: (String) -> Unit,
    onDismiss: () -> Unit
) {
    var title by remember { mutableStateOf(initialTitle) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Save As") },
        text = {
            OutlinedTextField(
                value = title,
                onValueChange = { title = it },
                label = { Text("Pattern name") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
        },
        confirmButton = {
            TextButton(
                onClick = { onConfirm(title.trim().ifBlank { "My Design" }) },
                enabled = title.isNotBlank()
            ) { Text("Save") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}

// ─── Build & assembly instructions sheet (3D patterns) ────────────────────────

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun InstructionsSheet(
    title: String,
    buildGuide: String?,
    assemblyGuide: String?,
    onDismiss: () -> Unit
) {
    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 24.dp)
                .padding(bottom = 40.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text("How to build $title", style = MaterialTheme.typography.titleLarge)
            if (!buildGuide.isNullOrBlank()) {
                Spacer(Modifier.height(4.dp))
                Text("Build the panels", style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.primary)
                Text(buildGuide, style = MaterialTheme.typography.bodyMedium)
            }
            if (!assemblyGuide.isNullOrBlank()) {
                Spacer(Modifier.height(8.dp))
                Text("Assemble", style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.primary)
                Text(assemblyGuide, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}

// ─── Bead count sheet ─────────────────────────────────────────────────────────

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun BeadCountSheet(
    counts: List<Pair<BeadColor, Int>>,
    total: Int,
    onDismiss: () -> Unit,
    onShare: () -> Unit
) {
    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())   // long color lists must scroll
                .padding(horizontal = 24.dp)
                .padding(bottom = 32.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Bead Count ($total total)", style = MaterialTheme.typography.titleMedium)
                IconButton(onClick = onShare) {
                    Icon(Icons.Default.Share, contentDescription = "Share shopping list")
                }
            }
            Spacer(Modifier.height(12.dp))
            counts.forEach { (color, count) ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(24.dp)
                            .clip(CircleShape)
                            .background(color.composeColor)
                    )
                    Text(color.name, modifier = Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium)
                    Text("$count", style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}

// ─── Export helpers ───────────────────────────────────────────────────────────

private suspend fun exportPng(context: Context, viewModel: EditorViewModel) {
    val bitmap = withContext(Dispatchers.Default) {
        ImageConverter.renderToBitmap(viewModel.pattern.value, cellSizePx = 16)
    }
    val file = withContext(Dispatchers.IO) {
        val dir = File(context.cacheDir, "exports").apply { mkdirs() }
        val f   = File(dir, "beadsnap_export.png")
        f.outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
        bitmap.recycle()
        f
    }
    val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
    val intent = Intent(Intent.ACTION_SEND).apply {
        type = "image/png"
        putExtra(Intent.EXTRA_STREAM, uri)
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    context.startActivity(Intent.createChooser(intent, "Share Pattern"))
}

private suspend fun shareShoppingList(
    context: Context,
    counts: List<Pair<BeadColor, Int>>,
    title: String
) {
    val text = buildString {
        appendLine("Bead Shopping List: $title")
        appendLine()
        counts.forEach { (color, count) -> appendLine("• ${color.name}: $count") }
        appendLine()
        appendLine("Total: ${counts.sumOf { it.second }} beads")
    }
    val intent = Intent(Intent.ACTION_SEND).apply {
        type = "text/plain"
        putExtra(Intent.EXTRA_SUBJECT, "Bead Shopping List: $title")
        putExtra(Intent.EXTRA_TEXT, text)
    }
    context.startActivity(Intent.createChooser(intent, "Share Shopping List"))
}
