import SwiftUI

@MainActor
final class EditorViewModel: ObservableObject {
    @Published private(set) var pattern: FusePattern
    @Published var selectedColor: PaletteColor
    @Published var canUndo = false

    // O(1) lookup: "x,y" → colorId
    private var cellMap: [String: String] = [:]
    private var undoStack: [[String: String]] = []
    private let store = PatternStore.shared

    init(pattern: FusePattern) {
        self.pattern = pattern
        self.selectedColor = pattern.palette.first ?? PaletteColor.full.first!
        self.cellMap = Self.buildMap(from: pattern.cells)
    }

    // MARK: - Read

    func colorId(at x: Int, y: Int) -> String? { cellMap[key(x, y)] }

    func color(at x: Int, y: Int) -> PaletteColor? {
        guard let id = colorId(at: x, y: y) else { return nil }
        return pattern.palette.first { $0.id == id }
    }

    // MARK: - Write

    func tapCell(x: Int, y: Int) {
        pushUndo()
        let k = key(x, y)
        if cellMap[k] == selectedColor.id {
            cellMap.removeValue(forKey: k)
        } else {
            cellMap[k] = selectedColor.id
        }
        commitCells()
        autosave()
    }

    func clearCell(x: Int, y: Int) {
        let k = key(x, y)
        guard cellMap[k] != nil else { return }   // no-op erases must not eat undo history
        pushUndo()
        cellMap.removeValue(forKey: k)
        commitCells()
        autosave()
    }

    // MARK: - Stroke API (drag painting)
    // A stroke is one undo entry; painting is set-only so dragging over
    // already-painted cells never erases them (tap keeps toggle semantics).

    func beginStroke() {
        pushUndo()
    }

    func strokePaint(x: Int, y: Int) {
        let k = key(x, y)
        guard cellMap[k] != selectedColor.id else { return }
        cellMap[k] = selectedColor.id
        commitCells()
        autosave()
    }

    func strokeErase(x: Int, y: Int) {
        let k = key(x, y)
        guard cellMap[k] != nil else { return }
        cellMap.removeValue(forKey: k)
        commitCells()
        autosave()
    }

    /// Reverts an in-progress stroke (e.g. when a pinch begins mid-drag).
    func cancelStroke() {
        undo()
    }

    func clearAll() {
        pushUndo()
        cellMap.removeAll()
        commitCells()
        autosave()
    }

    func undo() {
        guard let prev = undoStack.popLast() else { return }
        cellMap = prev
        commitCells()
        canUndo = !undoStack.isEmpty
        autosave()
    }

    func saveAs(title: String) -> FusePattern {
        var copy = pattern
        copy.id = UUID().uuidString
        copy.title = title
        copy.createdBy = .user
        copy.version = 1
        store.save(copy)
        pattern = copy
        return copy
    }

    var colorCounts: [(color: PaletteColor, count: Int)] { pattern.colorCounts }
    var totalBeads: Int { pattern.totalBeads }

    func renderToImage(cellSize: CGFloat = 16) -> UIImage {
        ImageConverter.renderToImage(pattern: pattern, cellSize: cellSize)
    }

    // MARK: - Private

    private func key(_ x: Int, _ y: Int) -> String { "\(x),\(y)" }

    private func pushUndo() {
        undoStack.append(cellMap)
        if undoStack.count > 50 { undoStack.removeFirst() }
        canUndo = true
    }

    private func commitCells() {
        var p = pattern
        p.cells = cellMap.map { k, id -> Cell in
            let parts = k.split(separator: ",").compactMap { Int($0) }
            return Cell(x: parts[0], y: parts[1], colorId: id)
        }
        p.version += 1
        pattern = p
    }

    private var autosaveTask: Task<Void, Never>?

    func saveImmediately() {
        autosaveTask?.cancel()
        guard pattern.createdBy == .user else { return }
        guard store.userPatterns.contains(where: { $0.id == pattern.id }) else { return }
        store.save(pattern)
    }

    private func autosave() {
        guard pattern.createdBy == .user else { return }
        autosaveTask?.cancel()
        let snapshot = pattern
        autosaveTask = Task { [weak self] in
            guard let self else { return }
            try? await Task.sleep(nanoseconds: 500_000_000)
            guard !Task.isCancelled else { return }
            // Skip if the pattern has been deleted since this task was queued
            guard self.store.userPatterns.contains(where: { $0.id == snapshot.id }) else { return }
            self.store.save(snapshot)
        }
    }

    private static func buildMap(from cells: [Cell]) -> [String: String] {
        var map: [String: String] = [:]
        for cell in cells {
            guard let id = cell.colorId else { continue }
            map["\(cell.x),\(cell.y)"] = id
        }
        return map
    }
}
