import SwiftUI

struct LibraryView: View {
    @StateObject private var viewModel = LibraryViewModel()

    private let columns = [GridItem(.adaptive(minimum: 130, maximum: 180), spacing: 14)]

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                categoryBar
                Divider()
                ScrollView {
                    if viewModel.patterns.isEmpty {
                        emptyState
                    } else {
                        LazyVGrid(columns: columns, spacing: 16) {
                            ForEach(viewModel.patterns) { pattern in
                                NavigationLink(value: pattern) {
                                    PatternCard(pattern: pattern)
                                        .padding(4)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                        .padding(16)
                    }
                }
            }
            .navigationTitle("Library")
            .searchable(text: $viewModel.searchQuery, prompt: "Search patterns")
            .navigationDestination(for: FusePattern.self) { pattern in
                PatternEditorView(pattern: pattern)
            }
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        ForEach(LibrarySortOrder.allCases) { order in
                            Button {
                                viewModel.sortOrder = order
                            } label: {
                                Label(order.displayName, systemImage: order.systemImage)
                            }
                        }
                    } label: {
                        Image(systemName: "arrow.up.arrow.down")
                    }
                    .accessibilityLabel("Sort patterns")
                }
            }
        }
    }

    // MARK: - Category filter

    private var categoryBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                chip(nil, label: "All")
                ForEach(PatternCategory.allCases) { cat in
                    chip(cat, label: "\(cat.emoji) \(cat.displayName)")
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
        }
    }

    private func chip(_ cat: PatternCategory?, label: String) -> some View {
        let isSelected = viewModel.selectedCategory == cat
        return Button {
            viewModel.selectedCategory = cat
        } label: {
            Text(label)
                .font(.subheadline)
                .padding(.horizontal, 14)
                .padding(.vertical, 7)
                .background(isSelected ? Color.purple : Color(.secondarySystemBackground))
                .foregroundStyle(isSelected ? .white : .primary)
                .clipShape(Capsule())
        }
        .buttonStyle(.plain)
        .animation(.easeInOut(duration: 0.15), value: isSelected)
        .accessibilityAddTraits(isSelected ? .isSelected : [])
        .accessibilityLabel(cat.map { $0.displayName } ?? "All categories")
    }

    // MARK: - Empty state

    private var emptyState: some View {
        ContentUnavailableView(
            "No Patterns Found",
            systemImage: "square.grid.2x2",
            description: Text("Try a different category or search term.")
        )
        .padding(.top, 60)
    }
}
