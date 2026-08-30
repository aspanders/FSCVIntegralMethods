import SwiftUI

/// Which of your own patterns to show.
///
/// Provenance is read off data that already exists rather than a new field, so
/// everything made before this screen existed is filed correctly too: a pattern
/// listed as a variant of a photo project came from a photo, one carrying the
/// prompt it was generated from came from the AI, and what is left was drawn or
/// edited by hand. A port of the Android `Creations` enum, same rules.
private enum CreationKind: String, CaseIterable, Identifiable {
    case all, drawn, fromPhoto, fromAI
    var id: String { rawValue }
    var label: String {
        switch self {
        case .all:       return "Everything"
        case .drawn:     return "Drawn & edited"
        case .fromPhoto: return "From photos"
        case .fromAI:    return "From AI"
        }
    }
}

/// Everything the user has made, in one place.
///
/// The Library mixes these few patterns in with more than two thousand shipped
/// ones, where they are effectively unfindable. This screen is the opposite
/// view: only what you made.
///
/// A reader of PatternStore and PhotoProjectStore, holding no state of its own
/// beyond the filter. Opening, duplicating and deleting go through the same
/// PatternCard and the same store calls the Library uses, so a pattern behaves
/// identically whichever screen you reached it from.
struct MyCreationsView: View {
    @ObservedObject private var store = PatternStore.shared
    @ObservedObject private var projectStore = PhotoProjectStore.shared

    @State private var filter: CreationKind = .all
    @State private var path: [FusePattern] = []
    @State private var patternToDelete: FusePattern?

    private let columns = [GridItem(.adaptive(minimum: 140), spacing: 16)]

    /// Every pattern id some photo project claims as one of its variants.
    private var fromPhotoIds: Set<String> {
        Set(projectStore.projects.flatMap { $0.variants.map(\.patternId) })
    }

    private func kind(of p: FusePattern) -> CreationKind {
        if fromPhotoIds.contains(p.id) { return .fromPhoto }
        if let prompt = p.sourcePrompt, !prompt.isEmpty { return .fromAI }
        return .drawn
    }

    private func count(_ k: CreationKind) -> Int {
        k == .all ? store.userPatterns.count
                  : store.userPatterns.filter { kind(of: $0) == k }.count
    }

    /// Left in the store's own order, which is by title. Sorting newest-first
    /// would be nicer, but a FusePattern carries no timestamp and its id is a
    /// UUID - ordering by that would look chronological and be arbitrary.
    private var shown: [FusePattern] {
        filter == .all ? store.userPatterns
                       : store.userPatterns.filter { kind(of: $0) == filter }
    }

    var body: some View {
        NavigationStack(path: $path) {
            Group {
                if store.userPatterns.isEmpty {
                    emptyState
                } else {
                    VStack(spacing: 0) {
                        filterChips
                        ScrollView {
                            LazyVGrid(columns: columns, spacing: 16) {
                                ForEach(shown) { pattern in
                                    Button {
                                        path.append(pattern)
                                    } label: {
                                        PatternCard(pattern: pattern)
                                            .padding(4)
                                    }
                                    .buttonStyle(.plain)
                                    .contextMenu {
                                        Button {
                                            store.duplicate(pattern)
                                        } label: {
                                            Label("Duplicate", systemImage: "plus.square.on.square")
                                        }
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
            }
            .navigationTitle("My Creations")
            .navigationDestination(for: FusePattern.self) { pattern in
                PatternEditorView(pattern: pattern)
            }
            .confirmationDialog(
                patternToDelete.map { "Delete \"\($0.title)\"?" } ?? "",
                isPresented: Binding(
                    get: { patternToDelete != nil },
                    set: { if !$0 { patternToDelete = nil } }
                ),
                titleVisibility: .visible
            ) {
                Button("Delete", role: .destructive) {
                    if let p = patternToDelete { delete(p) }
                    patternToDelete = nil
                }
                Button("Cancel", role: .cancel) { patternToDelete = nil }
            }
        }
    }

    private var filterChips: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                // A filter that would show nothing is not offered - tapping a
                // chip and getting an empty grid reads as a bug, not an answer.
                ForEach(CreationKind.allCases.filter { count($0) > 0 }) { k in
                    let selected = filter == k
                    Button {
                        filter = k
                    } label: {
                        Text("\(k.label) (\(count(k)))")
                            .font(.caption)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 7)
                            .background(
                                Capsule().fill(selected
                                               ? Color.accentColor.opacity(0.20)
                                               : Color(.secondarySystemBackground))
                            )
                            .overlay(
                                Capsule().stroke(selected ? Color.accentColor : .clear,
                                                 lineWidth: 1)
                            )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
        }
    }

    private var emptyState: some View {
        VStack(spacing: 10) {
            Image(systemName: "paintbrush.pointed.fill")
                .font(.system(size: 52))
                .foregroundStyle(.secondary)
            Text("Nothing here yet").font(.headline)
            Text("Anything you draw, make from a photo, or save from the AI "
                 + "studio lands here - including a copy you edit from the "
                 + "library. Start from Create.")
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding(40)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    /// Deleting also drops the photo project's reference, or the project keeps
    /// a variant row pointing at a pattern that no longer exists.
    private func delete(_ pattern: FusePattern) {
        for project in projectStore.projects
        where project.variants.contains(where: { $0.patternId == pattern.id }) {
            projectStore.removeVariant(project.id, patternId: pattern.id)
        }
        store.delete(pattern)
    }
}
