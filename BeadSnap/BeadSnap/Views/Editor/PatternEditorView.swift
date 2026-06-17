import SwiftUI

struct PatternEditorView: View {
    @StateObject private var viewModel: EditorViewModel
    @State private var showSaveDialog = false
    @State private var saveTitle = ""
    @State private var showClearConfirm = false
    @State private var showColorCounts = false

    init(pattern: FusePattern) {
        _viewModel = StateObject(wrappedValue: EditorViewModel(pattern: pattern))
    }

    var body: some View {
        VStack(spacing: 0) {
            BeadGridView(viewModel: viewModel)
                .frame(maxWidth: .infinity, maxHeight: .infinity)

            Divider()

            PalettePickerView(viewModel: viewModel)
        }
        .navigationTitle(viewModel.pattern.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar { toolbarItems }
        .alert("Save Copy As", isPresented: $showSaveDialog) {
            TextField("Pattern name", text: $saveTitle)
                .autocorrectionDisabled()
            Button("Save") {
                let t = saveTitle.trimmingCharacters(in: .whitespaces)
                guard !t.isEmpty else { return }
                _ = viewModel.saveAs(title: t)
            }
            Button("Cancel", role: .cancel) {}
        }
        .confirmationDialog(
            "Clear all beads?",
            isPresented: $showClearConfirm,
            titleVisibility: .visible
        ) {
            Button("Clear All", role: .destructive) { viewModel.clearAll() }
            Button("Cancel", role: .cancel) {}
        }
        .sheet(isPresented: $showColorCounts) {
            colorCountSheet
        }
    }

    // MARK: - Toolbar

    @ToolbarContentBuilder
    private var toolbarItems: some ToolbarContent {
        ToolbarItem(placement: .navigationBarLeading) {
            Button {
                showClearConfirm = true
            } label: {
                Image(systemName: "trash")
            }
            .tint(.red)
        }

        ToolbarItemGroup(placement: .navigationBarTrailing) {
            Button {
                showColorCounts = true
            } label: {
                Image(systemName: "list.bullet.rectangle")
            }

            Button {
                viewModel.undo()
            } label: {
                Image(systemName: "arrow.uturn.backward")
            }
            .disabled(!viewModel.canUndo)

            if viewModel.pattern.createdBy != .user {
                Button {
                    saveTitle = viewModel.pattern.title
                    showSaveDialog = true
                } label: {
                    Image(systemName: "square.and.arrow.down")
                }
            }
        }
    }

    // MARK: - Color count sheet

    private var colorCountSheet: some View {
        NavigationStack {
            List {
                Section {
                    HStack {
                        Text("Total beads")
                        Spacer()
                        Text("\(viewModel.totalBeads)")
                            .monospacedDigit()
                            .foregroundStyle(.secondary)
                    }
                }
                Section("By color") {
                    ForEach(viewModel.colorCounts, id: \.color.id) { entry in
                        HStack(spacing: 12) {
                            Circle()
                                .fill(entry.color.swiftUIColor)
                                .frame(width: 22, height: 22)
                                .overlay(Circle().strokeBorder(.black.opacity(0.15), lineWidth: 0.5))
                            Text(entry.color.name)
                            Spacer()
                            Text("\(entry.count)")
                                .monospacedDigit()
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
            .navigationTitle("Bead Count")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { showColorCounts = false }
                }
            }
        }
        .presentationDetents([.medium, .large])
    }
}
