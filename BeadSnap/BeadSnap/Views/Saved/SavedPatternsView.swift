import SwiftUI

struct SavedPatternsView: View {
    @ObservedObject private var store = PatternStore.shared
    @State private var searchQuery = ""
    @State private var patternToDelete: FusePattern?

    private let columns = [GridItem(.adaptive(minimum: 130, maximum: 180), spacing: 14)]

    private var filtered: [FusePattern] {
        let q = searchQuery.lowercased().trimmingCharacters(in: .whitespaces)
        guard !q.isEmpty else { return store.userPatterns }
        return store.userPatterns.filter {
            $0.title.lowercased().contains(q) ||
            $0.tags.contains { $0.lowercased().contains(q) }
        }
    }

    var body: some View {
        NavigationStack {
            Group {
                if store.userPatterns.isEmpty {
                    emptyState
                } else if filtered.isEmpty {
                    ContentUnavailableView.search(text: searchQuery)
                } else {
                    ScrollView {
                        LazyVGrid(columns: columns, spacing: 16) {
                            ForEach(filtered) { pattern in
                                NavigationLink(value: pattern) {
                                    PatternCard(pattern: pattern)
                                        .padding(4)
                                }
                                .buttonStyle(.plain)
                                .contextMenu {
                                    Button(role: .destructive) {
                                        patternToDelete = pattern
                                    } label: {
                                        Label("Delete", systemImage: "trash")
                                    }
                                }
                            }
                        }
                        .padding(16)
                    }
                }
            }
            .navigationTitle("My Patterns")
            .searchable(text: $searchQuery, prompt: "Search saved patterns")
            .navigationDestination(for: FusePattern.self) { pattern in
                PatternEditorView(pattern: pattern)
            }
            .confirmationDialog(
                "Delete "\(patternToDelete?.title ?? "")"?",
                isPresented: .init(
                    get: { patternToDelete != nil },
                    set: { if !$0 { patternToDelete = nil } }
                ),
                titleVisibility: .visible
            ) {
                Button("Delete", role: .destructive) {
                    if let p = patternToDelete { store.delete(p) }
                    patternToDelete = nil
                }
                Button("Cancel", role: .cancel) { patternToDelete = nil }
            }
        }
    }

    private var emptyState: some View {
        ContentUnavailableView(
            "No Saved Patterns",
            systemImage: "heart",
            description: Text("Tap Save in the editor to keep your creations here.")
        )
    }
}
