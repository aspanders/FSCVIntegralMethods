import SwiftUI

// MARK: - Core Model

struct FusePattern: Identifiable, Codable, Hashable {
    var id: String
    var title: String
    var category: PatternCategory
    var createdBy: CreatorType
    var grid: GridSize
    var palette: [PaletteColor]
    var cells: [Cell]
    var difficulty: Difficulty
    var tags: [String]
    var sourcePrompt: String?
    // 3D constructions include how to make the bead panel(s) and how to
    // assemble them into the finished object. Nil for flat patterns.
    var buildGuide: String?
    var assemblyGuide: String?
    // Compact wire form: one string per grid row, each char = palette index
    // ('.' = empty). Present only in the shipped library; expanded to `cells`
    // when decoded. Defaults to nil so the explicit init below need not set it.
    var rows: [String]? = nil
    // Which pegboard the pattern is built on. Defaults to .square, so every
    // pattern written before this field existed decodes unchanged.
    var shape: PegboardShape = .square
    // Reduced versions of the same design, keyed "small"/"medium", each in the
    // same compact rows encoding and indexing the same palette. Built offline
    // (tools/library/scaling.py) rather than resampled here, because a reduced
    // board still has to be weldable: loose parts get re-welded and thin necks
    // re-widened at the smaller size, which is not something to redo on the
    // phone in two languages.
    var sizes: [String: PatternSize]? = nil
    var version: Int

    /// The boards this design can be built on, smallest first.
    var scales: [BoardScale] {
        BoardScale.allCases.filter { $0 == .large || sizes?[$0.key] != nil }
    }

    /// The same design on one of its other boards.
    ///
    /// A new id, because a small build and a large build of the same subject
    /// are two different projects and must not overwrite each other's
    /// progress. The palette is carried over whole so the reduced rows keep
    /// indexing it.
    func at(scale: BoardScale) -> FusePattern {
        guard scale != .large, let v = sizes?[scale.key] else { return self }
        var copy = self
        copy.id = "\(id)-\(scale.key)"
        copy.title = "\(title) (\(scale.label))"
        copy.grid = GridSize(width: v.width, height: v.height)
        copy.cells = FusePattern.expand(rows: v.rows, palette: palette)
        copy.rows = nil
        copy.sizes = nil
        return copy
    }

    var hasInstructions: Bool {
        !(buildGuide?.isEmpty ?? true) || !(assemblyGuide?.isEmpty ?? true)
    }

    // Palette-index charset for the compact `rows` encoding.
    // Keep in sync with tools/library/compact.py and the Android model.
    static let rowChars = Array("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")

    static func expand(rows: [String], palette: [PaletteColor]) -> [Cell] {
        var out: [Cell] = []
        for (y, row) in rows.enumerated() {
            for (x, ch) in row.enumerated() {
                if ch == "." { continue }
                if let idx = rowChars.firstIndex(of: ch), idx < palette.count {
                    out.append(Cell(x: x, y: y, colorId: palette[idx].id))
                }
            }
        }
        return out
    }

    init(
        id: String,
        title: String,
        category: PatternCategory,
        createdBy: CreatorType,
        grid: GridSize,
        palette: [PaletteColor],
        cells: [Cell],
        difficulty: Difficulty,
        tags: [String],
        sourcePrompt: String? = nil,
        buildGuide: String? = nil,
        assemblyGuide: String? = nil,
        shape: PegboardShape = .square,
        version: Int
    ) {
        self.id = id
        self.title = title
        self.category = category
        self.createdBy = createdBy
        self.grid = grid
        self.palette = palette
        self.cells = cells
        self.difficulty = difficulty
        self.tags = tags
        self.sourcePrompt = sourcePrompt
        self.buildGuide = buildGuide
        self.assemblyGuide = assemblyGuide
        self.shape = shape
        self.version = version
    }

    // Tolerates missing fields with the same defaults as the Android model,
    // so pattern JSON is interchangeable across platforms.
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id           = try c.decode(String.self, forKey: .id)
        title        = try c.decode(String.self, forKey: .title)
        category     = try c.decodeIfPresent(PatternCategory.self, forKey: .category) ?? .custom
        createdBy    = try c.decodeIfPresent(CreatorType.self, forKey: .createdBy) ?? .user
        grid         = try c.decodeIfPresent(GridSize.self, forKey: .grid) ?? .large
        palette      = try c.decodeIfPresent([PaletteColor].self, forKey: .palette) ?? []
        var decodedCells = try c.decodeIfPresent([Cell].self, forKey: .cells) ?? []
        if decodedCells.isEmpty,
           let compactRows = try c.decodeIfPresent([String].self, forKey: .rows) {
            decodedCells = FusePattern.expand(rows: compactRows, palette: palette)
        }
        cells        = decodedCells
        rows         = nil
        difficulty   = try c.decodeIfPresent(Difficulty.self, forKey: .difficulty) ?? .easy
        tags         = try c.decodeIfPresent([String].self, forKey: .tags) ?? []
        sourcePrompt = try c.decodeIfPresent(String.self, forKey: .sourcePrompt)
        buildGuide    = try c.decodeIfPresent(String.self, forKey: .buildGuide)
        assemblyGuide = try c.decodeIfPresent(String.self, forKey: .assemblyGuide)
        shape        = try c.decodeIfPresent(PegboardShape.self, forKey: .shape) ?? .square
        sizes        = try c.decodeIfPresent([String: PatternSize].self, forKey: .sizes)
        version      = try c.decodeIfPresent(Int.self, forKey: .version) ?? 1
    }

    func color(at x: Int, y: Int) -> PaletteColor? {
        guard let id = cellColorId(at: x, y: y) else { return nil }
        return palette.first { $0.id == id }
    }

    func cellColorId(at x: Int, y: Int) -> String? {
        cells.first { $0.x == x && $0.y == y }?.colorId
    }

    mutating func setColor(at x: Int, y: Int, colorId: String?) {
        cells.removeAll { $0.x == x && $0.y == y }
        if let colorId { cells.append(Cell(x: x, y: y, colorId: colorId)) }
        version += 1
    }

    var totalBeads: Int { cells.compactMap(\.colorId).count }

    var colorCounts: [(color: PaletteColor, count: Int)] {
        var counts: [String: Int] = [:]
        for cell in cells { if let id = cell.colorId { counts[id, default: 0] += 1 } }
        return palette.compactMap { c in counts[c.id].map { (c, $0) } }
            .sorted { $0.count > $1.count }
    }
}

// MARK: - Supporting Types

/// One reduced board for a pattern, in the same compact encoding as `rows`.
struct PatternSize: Codable, Hashable {
    var width: Int
    var height: Int
    var rows: [String]
}

/// Which of a pattern's boards to build. `.large` is the pattern as designed;
/// the others come from its `sizes` map and are only offered when they exist.
enum BoardScale: String, CaseIterable, Identifiable {
    case small, medium, large
    var id: String { rawValue }
    var key: String { rawValue }
    var label: String {
        switch self {
        case .small:  return "Small"
        case .medium: return "Medium"
        case .large:  return "Large"
        }
    }
}

enum PatternCategory: String, Codable, CaseIterable, Identifiable {
    // 23 content categories (100 patterns each) + 3D specialty + user designs.
    case geometric, mandalas, hearts, stars, flowers, rainbows, space, emoji,
         gems, icons, animals, birds, fish, bugs, food, sweets, trees, vehicles,
         snowflakes, holidays, videogame, sports, circles, threeD, custom
    var id: String { rawValue }
    var displayName: String {
        switch self {
        case .geometric:  return "Geometric"
        case .mandalas:   return "Mandalas"
        case .hearts:     return "Hearts"
        case .stars:      return "Stars"
        case .flowers:    return "Flowers"
        case .rainbows:   return "Rainbows"
        case .space:      return "Space"
        case .emoji:      return "Emoji"
        case .gems:       return "Gems"
        case .icons:      return "Icons"
        case .animals:    return "Animals"
        case .birds:      return "Birds"
        case .fish:       return "Fish"
        case .bugs:       return "Bugs"
        case .food:       return "Food"
        case .sweets:     return "Sweets"
        case .trees:      return "Trees"
        case .vehicles:   return "Vehicles"
        case .snowflakes: return "Snowflakes"
        case .holidays:   return "Holidays"
        case .videogame:  return "Video Game"
        case .sports:     return "Sports"
        case .circles:    return "Circles"
        case .threeD:     return "3D"
        case .custom:     return "My Designs"
        }
    }
    // Named `symbol`, not `emoji`, because one of the cases is itself `emoji`.
    var symbol: String {
        switch self {
        case .geometric:  return "🔷"
        case .mandalas:   return "🌀"
        case .hearts:     return "💗"
        case .stars:      return "⭐"
        case .flowers:    return "🌸"
        case .rainbows:   return "🌈"
        case .space:      return "🚀"
        case .emoji:      return "😊"
        case .gems:       return "💎"
        case .icons:      return "🔤"
        case .animals:    return "🐾"
        case .birds:      return "🐦"
        case .fish:       return "🐟"
        case .bugs:       return "🐛"
        case .food:       return "🍎"
        case .sweets:     return "🍬"
        case .trees:      return "🌳"
        case .vehicles:   return "🚗"
        case .snowflakes: return "❄️"
        case .holidays:   return "🎁"
        case .videogame:  return "🎮"
        case .sports:     return "⚽"
        case .circles:    return "⭕"
        case .threeD:     return "🧊"
        case .custom:     return "✏️"
        }
    }
}

/// The physical pegboard a pattern is pegged out on.
///
/// A round pegboard is not a different lattice - the pegs still sit on the same
/// square pitch - it is the square lattice clipped to a disc, which is why this
/// is a mask over the existing grid rather than a second coordinate system.
/// Cells outside the disc simply do not exist: not drawn, not painted, not
/// sampled from a photo, not exported.
/// Keep in sync with PegboardShape on Android.
enum PegboardShape: String, Codable, CaseIterable, Identifiable {
    case square, circle
    var id: String { rawValue }
    var displayName: String {
        switch self {
        case .square: return "Square"
        case .circle: return "Circle"
        }
    }

    /// Is cell (x, y) a real peg on a `cols` x `rows` board of this shape?
    func contains(x: Int, y: Int, cols: Int, rows: Int) -> Bool {
        guard x >= 0, x < cols, y >= 0, y < rows else { return false }
        switch self {
        case .square:
            return true
        case .circle:
            let r = Double(min(cols, rows)) / 2.0
            let dx = Double(x) + 0.5 - Double(cols) / 2.0
            let dy = Double(y) + 0.5 - Double(rows) / 2.0
            return dx * dx + dy * dy <= r * r
        }
    }
}

enum CreatorType: String, Codable { case system, user, ai }

struct GridSize: Codable, Equatable, Hashable {
    var width: Int
    var height: Int
    static let small  = GridSize(width: 16, height: 16)
    static let medium = GridSize(width: 24, height: 24)
    static let large  = GridSize(width: 32, height: 32)
    static let xlarge = GridSize(width: 48, height: 48)
    var displayName: String { "\(width)×\(height)" }
}

struct PaletteColor: Codable, Identifiable, Hashable {
    var id: String
    var name: String
    var hex: String

    var uiColor: UIColor { UIColor(hex: hex) }
    var swiftUIColor: Color { Color(uiColor) }
}

struct Cell: Codable, Equatable {
    var x: Int
    var y: Int
    var colorId: String?
}

enum Difficulty: String, Codable, CaseIterable, Identifiable {
    case easy, medium, hard
    var id: String { rawValue }
    var displayName: String { rawValue.capitalized }
    var emoji: String {
        switch self { case .easy: return "🟢"; case .medium: return "🟡"; case .hard: return "🔴" }
    }
    var color: Color {
        switch self { case .easy: return .green; case .medium: return .orange; case .hard: return .red }
    }
}

// UIColor(hex:) lives in BeadColor.swift to avoid duplicate extension
