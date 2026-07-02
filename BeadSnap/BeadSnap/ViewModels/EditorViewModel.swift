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
        self.selectedColor = pattern.palette.first ?? PaletteColor.beadSafe.first!
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
        pushUndo()
        cellMap.removeValue(forKey: key(x, y))
        commitCells()
        autosave()
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

    func renderToImage(cellSize: CGFloat = 18) -> UIImage {
        let w = CGFloat(pattern.grid.width) * cellSize
        let h = CGFloat(pattern.grid.height) * cellSize
        let renderer = UIGraphicsImageRenderer(size: CGSize(width: w, height: h))
        return renderer.image { _ in
            UIColor.white.setFill()
            UIRectFill(CGRect(x: 0, y: 0, width: w, height: h))
            let inset = cellSize * 0.06
            for row in 0..<pattern.grid.height {
                for col in 0..<pattern.grid.width {
                    let rect = CGRect(
                        x: CGFloat(col) * cellSize + inset,
                        y: CGFloat(row) * cellSize + inset,
                        width: cellSize - 2 * inset,
                        height: cellSize - 2 * inset
                    )
                    if let c = color(at: col, y: row) {
                        c.uiColor.setFill()
                        UIBezierPath(ovalIn: rect).fill()
                        let stroke = UIBezierPath(ovalIn: rect)
                        UIColor.black.withAlphaComponent(0.15).setStroke()
                        stroke.lineWidth = 0.5
                        stroke.stroke()
                    }
                }
            }
        }
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
