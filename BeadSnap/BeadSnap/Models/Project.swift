import Foundation

struct Project: Identifiable, Codable {
    var id: UUID
    var name: String
    var createdAt: Date
    var updatedAt: Date
    var sourceType: SourceType
    var originalImageFilename: String
    var maskedImageFilename: String?
    var patterns: [BeadPattern]
    var thumbnail: Data?

    enum SourceType: String, Codable {
        case photo
        case drawing
    }

    init(name: String, sourceType: SourceType, originalImageFilename: String) {
        self.id = UUID()
        self.name = name
        self.createdAt = Date()
        self.updatedAt = Date()
        self.sourceType = sourceType
        self.originalImageFilename = originalImageFilename
        self.maskedImageFilename = nil
        self.patterns = []
        self.thumbnail = nil
    }

    mutating func addPattern(_ pattern: BeadPattern) {
        if let idx = patterns.firstIndex(where: {
            $0.config == pattern.config
        }) {
            patterns[idx] = pattern
        } else {
            patterns.append(pattern)
        }
        updatedAt = Date()
    }

    mutating func removePattern(id: UUID) {
        patterns.removeAll { $0.id == id }
        updatedAt = Date()
    }

    func pattern(for config: PatternConfig) -> BeadPattern? {
        patterns.first { $0.config == config }
    }
}
