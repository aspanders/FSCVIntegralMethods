import SwiftUI
import Combine

@MainActor
final class LibraryViewModel: ObservableObject {
    @Published var selectedCategory: PatternCategory? = nil
    @Published var searchQuery = ""
    @Published var patterns: [FusePattern] = []

    private let store = PatternStore.shared
    private var cancellables = Set<AnyCancellable>()

    init() {
        store.$systemPatterns
            .combineLatest(store.$userPatterns, $selectedCategory, $searchQuery)
            .debounce(for: .milliseconds(80), scheduler: RunLoop.main)
            .sink { [weak self] system, user, category, query in
                self?.filter(system: system, user: user, category: category, query: query)
            }
            .store(in: &cancellables)
    }

    private func filter(
        system: [FusePattern], user: [FusePattern],
        category: PatternCategory?, query: String
    ) {
        var all = system + user
        if let cat = category { all = all.filter { $0.category == cat } }
        let q = query.lowercased().trimmingCharacters(in: .whitespaces)
        if !q.isEmpty {
            all = all.filter {
                $0.title.lowercased().contains(q) ||
                $0.tags.contains { $0.lowercased().contains(q) }
            }
        }
        patterns = all
    }

    func count(for category: PatternCategory) -> Int {
        (store.systemPatterns + store.userPatterns).filter { $0.category == category }.count
    }
}
