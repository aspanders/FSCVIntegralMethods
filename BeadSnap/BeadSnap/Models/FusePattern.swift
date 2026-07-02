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
    var version: Int

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

enum PatternCategory: String, Codable, CaseIterable, Identifiable {
    case animals, fantasy, vehicles, nature, icons, holidays, custom
    var id: String { rawValue }
    var displayName: String {
        switch self {
        case .animals:  return "Animals"
        case .fantasy:  return "Fantasy"
        case .vehicles: return "Vehicles"
        case .nature:   return "Nature"
        case .icons:    return "Icons"
        case .holidays: return "Holidays"
        case .custom:   return "My Designs"
        }
    }
    var emoji: String {
        switch self {
        case .animals:  return "🐾"
        case .fantasy:  return "🔮"
        case .vehicles: return "🚀"
        case .nature:   return "🌿"
        case .icons:    return "⭐"
        case .holidays: return "🎉"
        case .custom:   return "✏️"
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
