import SwiftUI

struct SavedPatternsView: View {
    @ObservedObject private var store = PatternStore.shared
    @State private var searchQuery = ""
    @State private var patternToDelete: FusePattern?
    @State private var isEditing = false

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
                                patternCell(pattern)
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
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(isEditing ? "Done" : "Edit") {
                        withAnimation { isEditing.toggle() }
                    }
                    .disabled(store.userPatterns.isEmpty)
                }
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
                    if store.userPatterns.isEmpty { isEditing = false }
                }
                Button("Cancel", role: .cancel) { patternToDelete = nil }
            }
        }
    }

    // MARK: - Pattern cell

    @ViewBuilder
    private func patternCell(_ pattern: FusePattern) -> some View {
        NavigationLink(value: pattern) {
            PatternCard(pattern: pattern)
                .padding(4)
        }
        .buttonStyle(.plain)
        .contextMenu {
            Button {
                store.duplicate(pattern)
            } label: {
                Label("Duplicate", systemImage: "doc.on.doc")
            }
            Button(role: .destructive) {
                patternToDelete = pattern
            } label: {
                Label("Delete", systemImage: "trash")
            }
        }
        .overlay(alignment: .topTrailing) {
            if isEditing {
                Button {
                    patternToDelete = pattern
                } label: {
                    Image(systemName: "minus.circle.fill")
                        .font(.title2)
                        .symbolRenderingMode(.multicolor)
                        .background(Color.white.clipShape(Circle()).padding(4))
                }
                .padding(6)
                .transition(.scale.combined(with: .opacity))
            }
        }
        .animation(.spring(response: 0.25, dampingFraction: 0.8), value: isEditing)
    }

    private var emptyState: some View {
        ContentUnavailableView(
            "No Saved Patterns",
            systemImage: "heart",
            description: Text("Tap Save in the editor to keep your creations here.")
        )
    }
}
