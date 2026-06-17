import Foundation
import Combine

@MainActor
final class PatternStore: ObservableObject {
    static let shared = PatternStore()

    @Published private(set) var systemPatterns: [FusePattern] = []
    @Published private(set) var userPatterns: [FusePattern] = []

    var allPatterns: [FusePattern] { systemPatterns + userPatterns }

    private let userDir: URL
    private let decoder = JSONDecoder()
    private let encoder: JSONEncoder = {
        let e = JSONEncoder()
        e.outputFormatting = [.prettyPrinted, .sortedKeys]
        return e
    }()

    private init() {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        userDir = docs.appendingPathComponent("patterns", isDirectory: true)
        try? FileManager.default.createDirectory(at: userDir, withIntermediateDirectories: true)
        systemPatterns = SeedPatterns.all.sorted { $0.title < $1.title }
        loadUserPatterns()
    }

    private func loadUserPatterns() {
        let urls = (try? FileManager.default.contentsOfDirectory(
            at: userDir, includingPropertiesForKeys: nil
        )) ?? []
        userPatterns = urls
            .filter { $0.pathExtension == "json" }
            .compactMap { url -> FusePattern? in
                guard let data = try? Data(contentsOf: url) else { return nil }
                return try? decoder.decode(FusePattern.self, from: data)
            }
            .sorted { $0.title.lowercased() < $1.title.lowercased() }
    }

    func save(_ pattern: FusePattern) {
        let url = userDir.appendingPathComponent("\(pattern.id).json")
        if let data = try? encoder.encode(pattern) {
            try? data.write(to: url, options: .atomic)
        }
        if let idx = userPatterns.firstIndex(where: { $0.id == pattern.id }) {
            userPatterns[idx] = pattern
        } else {
            userPatterns.append(pattern)
            userPatterns.sort { $0.title.lowercased() < $1.title.lowercased() }
        }
    }

    func delete(_ pattern: FusePattern) {
        guard pattern.createdBy == .user else { return }
        try? FileManager.default.removeItem(
            at: userDir.appendingPathComponent("\(pattern.id).json")
        )
        userPatterns.removeAll { $0.id == pattern.id }
    }

    func patterns(for category: PatternCategory) -> [FusePattern] {
        allPatterns.filter { $0.category == category }
    }

    func search(_ query: String) -> [FusePattern] {
        let q = query.lowercased().trimmingCharacters(in: .whitespaces)
        guard !q.isEmpty else { return allPatterns }
        return allPatterns.filter {
            $0.title.lowercased().contains(q) ||
            $0.tags.contains { $0.lowercased().contains(q) } ||
            $0.category.rawValue.contains(q)
        }
    }
}
