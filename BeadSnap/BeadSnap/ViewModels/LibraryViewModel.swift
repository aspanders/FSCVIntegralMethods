import SwiftUI
import Combine

enum LibrarySortOrder: String, CaseIterable, Identifiable {
    case title, difficulty, newest
    var id: String { rawValue }
    var displayName: String {
        switch self {
        case .title:      return "Name"
        case .difficulty: return "Difficulty"
        case .newest:     return "Newest First"
        }
    }
    var systemImage: String {
        switch self {
        case .title:      return "textformat.abc"
        case .difficulty: return "chart.bar"
        case .newest:     return "clock"
        }
    }
}

@MainActor
final class LibraryViewModel: ObservableObject {
    @Published var selectedCategory: PatternCategory? = nil
    @Published var searchQuery = ""
    @Published var sortOrder: LibrarySortOrder = .title
    @Published var patterns: [FusePattern] = []
    @Published private(set) var categoryCounts: [PatternCategory: Int] = [:]

    private let store = PatternStore.shared
    private var cancellables = Set<AnyCancellable>()

    init() {
        store.$systemPatterns
            .combineLatest(store.$userPatterns, $selectedCategory, $searchQuery)
            .combineLatest($sortOrder)
            .debounce(for: .milliseconds(80), scheduler: DispatchQueue.main)
            .sink { [weak self] combined, sort in
                let (system, user, category, query) = combined
                self?.filter(system: system, user: user, category: category, query: query, sort: sort)
            }
            .store(in: &cancellables)
    }

    private func filter(
        system: [FusePattern], user: [FusePattern],
        category: PatternCategory?, query: String,
        sort: LibrarySortOrder
    ) {
        let all = system + user

        // Cache counts (single pass, no extra alloc per call)
        var counts: [PatternCategory: Int] = [:]
        for p in all { counts[p.category, default: 0] += 1 }
        categoryCounts = counts

        var result = all
        if let cat = category { result = result.filter { $0.category == cat } }
        let q = query.lowercased().trimmingCharacters(in: .whitespaces)
        if !q.isEmpty {
            result = result.filter {
                $0.title.lowercased().contains(q) ||
                $0.tags.contains { $0.lowercased().contains(q) }
            }
        }

        switch sort {
        case .title:
            result.sort { $0.title.lowercased() < $1.title.lowercased() }
        case .difficulty:
            let order: [Difficulty] = [.easy, .medium, .hard]
            result.sort {
                (order.firstIndex(of: $0.difficulty) ?? 0) <
                (order.firstIndex(of: $1.difficulty) ?? 0)
            }
        case .newest:
            // User patterns come last in `all`; reverse so user patterns appear first
            result = result.reversed()
        }

        patterns = result
    }

    func count(for category: PatternCategory) -> Int {
        categoryCounts[category] ?? 0
    }
}
