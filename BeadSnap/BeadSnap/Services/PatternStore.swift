import Foundation
import Combine

@MainActor
final class PatternStore: ObservableObject {
    static let shared = PatternStore()

    @Published private(set) var systemPatterns: [FusePattern] = []
    @Published private(set) var userPatterns: [FusePattern] = []
    @Published private(set) var lastError: String?

    var allPatterns: [FusePattern] { systemPatterns + userPatterns }

    private let userDir: URL
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
        Task { await loadUserPatterns() }
    }

    private func loadUserPatterns() async {
        let dir = userDir
        let loaded: [FusePattern] = await Task.detached(priority: .userInitiated) {
            let urls = (try? FileManager.default.contentsOfDirectory(
                at: dir, includingPropertiesForKeys: nil
            )) ?? []
            return urls
                .filter { $0.pathExtension == "json" }
                .compactMap { url -> FusePattern? in
                    guard let data = try? Data(contentsOf: url) else { return nil }
                    return try? JSONDecoder().decode(FusePattern.self, from: data)
                }
                .sorted { $0.title.lowercased() < $1.title.lowercased() }
        }.value
        userPatterns = loaded
    }

    func save(_ pattern: FusePattern) {
        guard pattern.createdBy != .system else { return }
        let url = userDir.appendingPathComponent("\(pattern.id).json")
        do {
            let data = try encoder.encode(pattern)
            try data.write(to: url, options: .atomic)
            lastError = nil
        } catch {
            lastError = "Failed to save \"\(pattern.title)\": \(error.localizedDescription)"
            return
        }
        if let idx = userPatterns.firstIndex(where: { $0.id == pattern.id }) {
            userPatterns[idx] = pattern
        } else {
            userPatterns.append(pattern)
        }
        userPatterns.sort { $0.title.lowercased() < $1.title.lowercased() }
    }

    func delete(_ pattern: FusePattern) {
        guard pattern.createdBy != .system else { return }
        let url = userDir.appendingPathComponent("\(pattern.id).json")
        if FileManager.default.fileExists(atPath: url.path) {
            do {
                try FileManager.default.removeItem(at: url)
                lastError = nil
            } catch {
                lastError = "Failed to delete \"\(pattern.title)\": \(error.localizedDescription)"
                return
            }
        }
        userPatterns.removeAll { $0.id == pattern.id }
    }

    func clearLastError() { lastError = nil }

    func duplicate(_ pattern: FusePattern) {
        var copy = pattern
        copy.id = UUID().uuidString
        copy.title = "\(pattern.title) Copy"
        copy.createdBy = .user
        copy.version = 1
        save(copy)
    }

    func patterns(for category: PatternCategory) -> [FusePattern] {
        allPatterns.filter { $0.category == category }
    }
}
