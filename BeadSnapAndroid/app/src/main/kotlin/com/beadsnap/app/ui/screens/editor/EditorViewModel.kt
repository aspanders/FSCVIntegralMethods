package com.beadsnap.app.ui.screens.editor

import androidx.compose.ui.graphics.Color
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.beadsnap.app.data.model.BeadColor
import com.beadsnap.app.data.model.Cell
import com.beadsnap.app.data.model.CreatorType
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.store.PatternStore
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID

class EditorViewModel(
    initialPattern: FusePattern,
    private val store: PatternStore
) : ViewModel() {

    private val _pattern = MutableStateFlow(initialPattern)
    val pattern: StateFlow<FusePattern> = _pattern.asStateFlow()

    private val _selectedColor = MutableStateFlow(
        initialPattern.palette.firstOrNull() ?: BeadColor.palette.first()
    )
    val selectedColor: StateFlow<BeadColor> = _selectedColor.asStateFlow()

    private val _canUndo = MutableStateFlow(false)
    val canUndo: StateFlow<Boolean> = _canUndo.asStateFlow()

    private val _cellMap = MutableStateFlow(buildCellMap(initialPattern.cells))
    val cellMap: StateFlow<Map<String, String>> = _cellMap.asStateFlow()

    val gridWidth: Int  get() = _pattern.value.grid.width
    val gridHeight: Int get() = _pattern.value.grid.height

    val colorCounts: List<Pair<BeadColor, Int>> get() = _pattern.value.colorCounts()
    val totalBeads: Int                          get() = _pattern.value.totalBeads

    fun colorLookup(): Map<String, Color> =
        _pattern.value.palette.associate { it.id to it.composeColor }

    private val undoStack = ArrayDeque<Map<String, String>>()
    private val maxUndoDepth = 50
    private var autosaveJob: Job? = null

    /** Set by [beginStroke]; cleared by the first change the stroke makes. */
    private var strokeArmed = false

    // ─── Write operations ─────────────────────────────────────────────────────

    fun selectColor(color: BeadColor) { _selectedColor.value = color }

    fun tapCell(x: Int, y: Int) {
        pushUndo()
        val k = key(x, y)
        val next = _cellMap.value.toMutableMap()
        if (next[k] == _selectedColor.value.id) next.remove(k) else next[k] = _selectedColor.value.id
        _cellMap.value = next
        commitCells()
        scheduleAutosave()
    }

    fun clearCell(x: Int, y: Int) {
        val k = key(x, y)
        if (k !in _cellMap.value) return   // no-op erases must not eat undo history
        pushUndo()
        _cellMap.value = _cellMap.value - k
        commitCells()
        scheduleAutosave()
    }

    // ─── Stroke API (drag painting) ───────────────────────────────────────────
    // A stroke is one undo entry; painting is set-only so dragging over
    // already-painted cells never erases them (tap keeps toggle semantics).

    /**
     * Arms the undo entry; it is only pushed if the stroke actually changes
     * something.
     *
     * Pushing it here unconditionally meant that dragging across beads that
     * were already the selected colour - or across a round board's empty
     * corner - recorded an undo step that undid nothing, and lit the Undo
     * button to say so. Tapping it then appeared to do nothing at all, and the
     * user had to tap again to reach the edit they actually wanted back.
     */
    fun beginStroke() {
        strokeArmed = true
    }

    fun strokePaint(x: Int, y: Int) = strokeCells(listOf(x to y), erase = false)

    fun strokeErase(x: Int, y: Int) = strokeCells(listOf(x to y), erase = true)

    /**
     * Apply one segment of a stroke - every cell the finger crossed since the
     * last pointer event - as a single map mutation and a single commit.
     *
     * One event can cover a dozen cells once the caller fills in the gaps
     * between samples, and committing per cell meant rebuilding the whole cell
     * list (up to 841 objects on a full board) a dozen times inside one frame,
     * each rebuild also waking every collector of the pattern. Once per event
     * is the same result for a fraction of the work.
     */
    fun strokeCells(cells: List<Pair<Int, Int>>, erase: Boolean) {
        if (cells.isEmpty()) return
        val current = _cellMap.value
        val next = current.toMutableMap()
        val id = _selectedColor.value.id
        for ((x, y) in cells) {
            val k = key(x, y)
            if (erase) next.remove(k) else next[k] = id
        }
        // Dragging over beads that are already right changes nothing, and must
        // not cost an undo entry or a save.
        if (next == current) return
        pushStrokeUndo()
        _cellMap.value = next
        commitCells()
        scheduleAutosave()
    }

    fun clearAll() {
        pushUndo()
        _cellMap.value = emptyMap()
        commitCells()
        scheduleAutosave()
    }

    /**
     * Select-all-of-a-colour, then recolour: every bead currently using [from]
     * becomes [to], as a single undo entry. [to] joins the pattern palette if it
     * is not already there, so a colour can be swapped for one the pattern has
     * never used.
     */
    fun replaceColor(from: BeadColor, to: BeadColor) {
        if (from.id == to.id) return
        if (_cellMap.value.none { it.value == from.id }) return
        pushUndo()
        _cellMap.value = _cellMap.value.mapValues { (_, id) -> if (id == from.id) to.id else id }
        if (_pattern.value.palette.none { it.id == to.id }) {
            _pattern.update { it.copy(palette = it.palette + to) }
        }
        commitCells()
        scheduleAutosave()
    }

    /** Select-all-of-a-colour, then delete: clears every bead using [color]. */
    fun removeColor(color: BeadColor) {
        if (_cellMap.value.none { it.value == color.id }) return
        pushUndo()
        _cellMap.value = _cellMap.value.filterValues { it != color.id }
        commitCells()
        scheduleAutosave()
    }

    fun undo() {
        val prev = undoStack.removeLastOrNull() ?: return
        _cellMap.value = prev
        commitCells()
        _canUndo.value = undoStack.isNotEmpty()
        scheduleAutosave()
    }

    fun saveAs(title: String): FusePattern {
        val copy = _pattern.value.copy(
            id = UUID.randomUUID().toString(),
            title = title,
            createdBy = CreatorType.user,
            version = 1
        )
        store.save(copy)
        _pattern.value = copy
        return copy
    }

    fun saveImmediately() {
        autosaveJob?.cancel()
        val p = _pattern.value
        if (p.createdBy != CreatorType.user) return
        if (store.userPatterns.value.none { it.id == p.id }) return
        store.save(p)
    }

    // ─── Private helpers ──────────────────────────────────────────────────────

    private fun key(x: Int, y: Int) = "$x,$y"

    private fun pushUndo() {
        strokeArmed = false          // a discrete edit ends any armed stroke
        undoStack.addLast(_cellMap.value)
        if (undoStack.size > maxUndoDepth) undoStack.removeFirst()
        _canUndo.value = true
    }

    /** One undo entry per stroke, recorded at its first real change. */
    private fun pushStrokeUndo() {
        if (!strokeArmed) return
        pushUndo()
    }

    private fun commitCells() {
        val cells = _cellMap.value.map { (k, id) ->
            val (x, y) = k.split(",").map { it.toInt() }
            Cell(x, y, id)
        }
        _pattern.update { it.copy(cells = cells, version = it.version + 1) }
    }

    private fun scheduleAutosave() {
        val p = _pattern.value
        if (p.createdBy != CreatorType.user) return
        autosaveJob?.cancel()
        autosaveJob = viewModelScope.launch {
            delay(500)
            if (store.userPatterns.value.none { it.id == p.id }) return@launch
            store.save(_pattern.value)
        }
    }

    override fun onCleared() {
        super.onCleared()
        saveImmediately()
    }

    companion object {
        private fun buildCellMap(cells: List<Cell>): Map<String, String> =
            buildMap {
                cells.forEach { cell -> cell.colorId?.let { put("${cell.x},${cell.y}", it) } }
            }
    }
}
