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
    @State private var showInstructions = false
    @AppStorage("hasSeenPaintHint") private var hasSeenPaintHint = false
    @State private var showPaintHint = false

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
        .sheet(isPresented: $showInstructions) { instructionsSheet }
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
        .onDisappear { viewModel.saveImmediately() }
        .overlay(alignment: .center) {
            if showPaintHint {
                paintHintOverlay
                    .transition(.opacity)
            }
        }
        .animation(.easeInOut(duration: 0.3), value: showPaintHint)
        .onAppear {
            if !hasSeenPaintHint {
                showPaintHint = true
                hasSeenPaintHint = true
                DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                    withAnimation { showPaintHint = false }
                }
            }
        }
    }

    private var paintHintOverlay: some View {
        VStack(spacing: 8) {
            Image(systemName: "hand.point.up.fill")
                .font(.largeTitle)
                .foregroundStyle(.white)
            Text("Tap a bead to paint it")
                .font(.headline)
                .foregroundStyle(.white)
            Text("Drag to fill a row • Pinch to zoom")
                .font(.subheadline)
                .foregroundStyle(.white.opacity(0.85))
        }
        .padding(24)
        .background(.black.opacity(0.65), in: RoundedRectangle(cornerRadius: 20))
        .onTapGesture { withAnimation { showPaintHint = false } }
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

            if viewModel.pattern.hasInstructions {
                Button { showInstructions = true } label: {
                    Image(systemName: "book")
                }
                .accessibilityLabel("Build instructions")
            }

            Button {
                withAnimation { isErasing.toggle() }
            } label: {
                Image(systemName: isErasing ? "eraser.fill" : "pencil.tip")
                    .foregroundStyle(isErasing ? .red : .primary)
            }
            .accessibilityLabel(isErasing ? "Eraser" : "Pencil")
            .accessibilityHint(isErasing ? "Switches to drawing" : "Switches to erasing")

            Button { viewModel.undo() } label: {
                Image(systemName: "arrow.uturn.backward")
            }
            .disabled(!viewModel.canUndo)
            .accessibilityLabel("Undo")

            Button {
                saveTitle = viewModel.pattern.title
                showSaveSheet = true
            } label: {
                Image(systemName: "square.and.arrow.down")
            }
            .accessibilityLabel(viewModel.pattern.createdBy == .user ? "Save as" : "Save as copy")
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

    // MARK: - Build & assembly instructions (3D patterns)

    private var instructionsSheet: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 8) {
                    if let build = viewModel.pattern.buildGuide, !build.isEmpty {
                        Text("Build the panels")
                            .font(.headline)
                            .foregroundStyle(.purple)
                        Text(build)
                            .font(.body)
                            .padding(.bottom, 8)
                    }
                    if let assembly = viewModel.pattern.assemblyGuide, !assembly.isEmpty {
                        Text("Assemble")
                            .font(.headline)
                            .foregroundStyle(.purple)
                        Text(assembly)
                            .font(.body)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
            }
            .navigationTitle("How to Build")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { showInstructions = false }
                }
            }
        }
        .presentationDetents([.medium, .large])
    }

    private func shareShoppingList() {
        let lines = viewModel.colorCounts.map { "• \($0.color.name): \($0.count)" }
        let text = """
        Bead Shopping List: \(viewModel.pattern.title)

        \(lines.joined(separator: "\n"))

        Total: \(viewModel.totalBeads) beads
        """
        let vc = UIActivityViewController(activityItems: [text], applicationActivities: nil)
        // This runs while the Bead Count sheet is presented, so we must present
        // from the TOPMOST controller: presenting from the root silently fails.
        let scene = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .first { $0.activationState == .foregroundActive } ??
            UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first
        guard let window = scene?.keyWindow ?? scene?.windows.first,
              var top = window.rootViewController else { return }
        while let presented = top.presentedViewController { top = presented }
        // iPad requires a sourceView/sourceRect for the popover anchor
        if let popover = vc.popoverPresentationController {
            popover.sourceView = top.view
            popover.sourceRect = CGRect(
                x: top.view.bounds.midX, y: top.view.bounds.midY, width: 0, height: 0
            )
            popover.permittedArrowDirections = []
        }
        top.present(vc, animated: true)
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
