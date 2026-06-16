import Foundation

enum PatternSize: String, CaseIterable, Codable, Identifiable {
    case small   = "small"
    case medium  = "medium"
    case large   = "large"
    case xlarge  = "xlarge"

    var id: String { rawValue }

    var beadCount: (cols: Int, rows: Int) {
        switch self {
        case .small:  return (16, 16)
        case .medium: return (29, 29)
        case .large:  return (58, 58)
        case .xlarge: return (116, 116)
        }
    }

    var displayName: String {
        switch self {
        case .small:  return "Mini"
        case .medium: return "Medium"
        case .large:  return "Full Tray"
        case .xlarge: return "Multi-Tray"
        }
    }

    var subtitle: String {
        switch self {
        case .small:  return "16×16 beads"
        case .medium: return "29×29 beads (≈3\"×3\")"
        case .large:  return "58×58 beads (standard tray)"
        case .xlarge: return "116×116 beads (4 trays)"
        }
    }

    var emoji: String {
        switch self {
        case .small:  return "🔵"
        case .medium: return "🟡"
        case .large:  return "🟢"
        case .xlarge: return "🌟"
        }
    }
}

enum PatternLayout: String, CaseIterable, Codable, Identifiable {
    case grid    = "grid"
    case circle  = "circle"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .grid:   return "Square Grid"
        case .circle: return "Circle Tray"
        }
    }

    var emoji: String {
        switch self {
        case .grid:   return "⬜"
        case .circle: return "⭕"
        }
    }
}

struct PatternConfig: Codable, Hashable {
    var size: PatternSize
    var layout: PatternLayout

    static let `default` = PatternConfig(size: .medium, layout: .grid)
}
