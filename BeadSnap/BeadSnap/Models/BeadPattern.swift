import Foundation

struct BeadPattern: Identifiable, Codable {
    var id: UUID
    var config: PatternConfig
    // nil = empty/transparent bead position
    var grid: [[String?]]
    var createdAt: Date

    init(config: PatternConfig, grid: [[String?]]) {
        self.id = UUID()
        self.config = config
        self.grid = grid
        self.createdAt = Date()
    }

    var rows: Int { grid.count }
    var cols: Int { grid.first?.count ?? 0 }

    func color(row: Int, col: Int) -> BeadColor? {
        guard row >= 0, row < rows, col >= 0, col < cols else { return nil }
        guard let colorID = grid[row][col] else { return nil }
        return BeadColor.paletteByID[colorID]
    }

    mutating func setColor(row: Int, col: Int, colorID: String?) {
        guard row >= 0, row < rows, col >= 0, col < cols else { return }
        grid[row][col] = colorID
    }

    var colorCount: [String: Int] {
        var counts: [String: Int] = [:]
        for row in grid {
            for colorID in row {
                if let id = colorID {
                    counts[id, default: 0] += 1
                }
            }
        }
        return counts
    }

    var totalBeads: Int {
        grid.flatMap { $0 }.compactMap { $0 }.count
    }

    func isInsideCircle(row: Int, col: Int) -> Bool {
        guard config.layout == .circle else { return true }
        let cx = Double(cols) / 2.0
        let cy = Double(rows) / 2.0
        let dx = Double(col) + 0.5 - cx
        let dy = Double(row) + 0.5 - cy
        let radius = Double(min(cols, rows)) / 2.0
        return (dx * dx + dy * dy) <= (radius * radius)
    }
}
