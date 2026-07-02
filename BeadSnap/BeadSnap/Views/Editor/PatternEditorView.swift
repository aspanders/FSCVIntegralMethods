import SwiftUI

struct PatternEditorView: View {
    @StateObject private var viewModel: EditorViewModel
    @State private var isErasing = false
    @State private var showSaveSheet = false
    @State private var saveTitle = ""
    @State private var saveTitleError = false
    @State private var showClearConfirm = false
    @State private var showColorCounts = false
    @State private var showSaveSuccess = false
    @State private var showExport = false

    init(pattern: FusePattern) {
        _viewModel = StateObject(wrappedValue: EditorViewModel(pattern: pattern))
    }

    var body: some View {
        VStack(spacing: 0) {
            if viewModel.pattern.createdBy != .user {
                systemPatternBanner
            }

            BeadGridView(viewModel: viewModel, isErasing: isErasing)
                .frame(maxWidth: .infinity, maxHeight: .infinity)

            Divider()

            PalettePickerView(viewModel: viewModel)
        }
        .navigationTitle(viewModel.pattern.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar { toolbarItems }
        .sheet(isPresented: $showSaveSheet) { saveSheet }
        .sheet(isPresented: $showColorCounts) { colorCountSheet }
        .sheet(isPresented: $showExport) {
            ShareSheet(items: [viewModel.renderToImage()])
        }
        .confirmationDialog(
            "Clear all beads?",
            isPresented: $showClearConfirm,
            titleVisibility: .visible
        ) {
            Button("Clear All", role: .destructive) { viewModel.clearAll() }
            Button("Cancel", role: .cancel) {}
        }
        .overlay(alignment: .top) {
            if showSaveSuccess {
                saveSuccessBanner
                    .transition(.move(edge: .top).combined(with: .opacity))
                    .onAppear {
                        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                            withAnimation { showSaveSuccess = false }
                        }
                    }
            }
        }
        .animation(.easeInOut(duration: 0.25), value: showSaveSuccess)
    }

    // MARK: - Banners

    private var systemPatternBanner: some View {
        HStack(spacing: 6) {
            Image(systemName: "info.circle.fill").foregroundStyle(.blue)
            Text("Built-in pattern. Edits won't be saved unless you")
                .font(.caption)
            Button("Save a Copy") {
                saveTitle = viewModel.pattern.title
                showSaveSheet = true
            }
            .font(.caption.bold())
            Spacer()
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 8)
        .background(Color.blue.opacity(0.08))
    }

    private var saveSuccessBanner: some View {
        HStack(spacing: 8) {
            Image(systemName: "checkmark.circle.fill").foregroundStyle(.green)
            Text("Pattern saved!").font(.subheadline.bold())
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 10)
        .background(.regularMaterial, in: Capsule())
        .shadow(radius: 4, y: 2)
        .padding(.top, 8)
    }

    // MARK: - Toolbar

    @ToolbarContentBuilder
    private var toolbarItems: some ToolbarContent {
        ToolbarItem(placement: .navigationBarLeading) {
            Button { showClearConfirm = true } label: {
                Image(systemName: "trash")
            }
            .tint(.red)
            .accessibilityLabel("Clear all beads")
        }

        ToolbarItemGroup(placement: .navigationBarTrailing) {
            Button { showExport = true } label: {
                Image(systemName: "square.and.arrow.up")
            }
            .accessibilityLabel("Export as image")

            Button { showColorCounts = true } label: {
                Image(systemName: "list.bullet.rectangle")
            }
            .accessibilityLabel("Show bead count")

            Button {
                withAnimation { isErasing.toggle() }
            } label: {
                Image(systemName: isErasing ? "eraser.fill" : "pencil.tip")
                    .foregroundStyle(isErasing ? .red : .primary)
            }
            .accessibilityLabel(isErasing ? "Drawing mode" : "Erasing mode")

            Button { viewModel.undo() } label: {
                Image(systemName: "arrow.uturn.backward")
            }
            .disabled(!viewModel.canUndo)
            .accessibilityLabel("Undo")

            if viewModel.pattern.createdBy != .user {
                Button {
                    saveTitle = viewModel.pattern.title
                    showSaveSheet = true
                } label: {
                    Image(systemName: "square.and.arrow.down")
                }
                .accessibilityLabel("Save as copy")
            }
        }
    }

    // MARK: - Save sheet

    private var saveSheet: some View {
        NavigationStack {
            Form {
                Section("Pattern Name") {
                    TextField("Name", text: $saveTitle)
                        .autocorrectionDisabled()
                }
                if saveTitleError {
                    Section {
                        Label("Name cannot be empty.", systemImage: "exclamationmark.triangle")
                            .foregroundStyle(.red)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("Save Copy")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { showSaveSheet = false }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        let t = saveTitle.trimmingCharacters(in: .whitespaces)
                        guard !t.isEmpty else { saveTitleError = true; return }
                        _ = viewModel.saveAs(title: t)
                        UINotificationFeedbackGenerator().notificationOccurred(.success)
                        showSaveSheet = false
                        withAnimation { showSaveSuccess = true }
                    }
                    .bold()
                }
            }
        }
        .presentationDetents([.medium])
        .onAppear { saveTitleError = false }
    }

    // MARK: - Color count sheet

    private var colorCountSheet: some View {
        NavigationStack {
            List {
                Section {
                    HStack {
                        Text("Total beads")
                        Spacer()
                        Text("\(viewModel.totalBeads)").monospacedDigit().foregroundStyle(.secondary)
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
                            Text("\(entry.count)").monospacedDigit().foregroundStyle(.secondary)
                        }
                    }
                }
            }
            .navigationTitle("Bead Count")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button {
                        shareShoppingList()
                    } label: {
                        Label("Share List", systemImage: "square.and.arrow.up")
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { showColorCounts = false }
                }
            }
        }
        .presentationDetents([.medium, .large])
    }

    private func shareShoppingList() {
        let lines = viewModel.colorCounts.map { "• \($0.color.name): \($0.count)" }
        let text = """
        Bead Shopping List — \(viewModel.pattern.title)
        \(lines.joined(separator: "\n"))
        Total: \(viewModel.totalBeads) beads
        """
        let vc = UIActivityViewController(activityItems: [text], applicationActivities: nil)
        UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .first { $0.isKeyWindow }?
            .rootViewController?
            .present(vc, animated: true)
    }
}

// MARK: - Share sheet wrapper

struct ShareSheet: UIViewControllerRepresentable {
    let items: [Any]
    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: items, applicationActivities: nil)
    }
    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}
