import SwiftUI
import PhotosUI
import UIKit

struct CreateView: View {
    var onOpenAIStudio: () -> Void = {}

    @StateObject private var importVM = ImportViewModel()
    @State private var showBlankSheet = false
    @State private var showCamera = false
    @State private var capturedImage: UIImage?
    @State private var editorPattern: FusePattern?
    @State private var blankTitle = "My Design"
    @State private var blankGridSize: GridSize = .large
    @State private var showPhotoSettings = false
    @State private var didStartConvert = false
    @State private var removeBackground = false
    @StateObject private var maskEditor = MaskEditor()

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                Spacer()
                header
                    .padding(.bottom, 40)
                options
                    .padding(.horizontal, 28)
                    .frame(maxWidth: 520)   // keep option cards scannable on iPad
                Spacer()
                Spacer()
            }
            .navigationTitle("Create")
            .navigationDestination(item: $editorPattern) { p in
                PatternEditorView(pattern: p)
            }
            .sheet(isPresented: $showBlankSheet) {
                blankSheet
            }
            .sheet(
                isPresented: $showPhotoSettings,
                onDismiss: {
                    // Swipe-down must clean up too, or re-picking the same photo
                    // is a dead end (the selection binding never changes)
                    if !didStartConvert {
                        importVM.selectedItem = nil
                        capturedImage = nil
                    }
                    didStartConvert = false
                    removeBackground = false
                    maskEditor.reset()
                }
            ) {
                photoSettingsSheet
            }
            .fullScreenCover(
                isPresented: $showCamera,
                onDismiss: {
                    // Fires only after the cover is fully off-screen, so the
                    // settings sheet can't race the dismissal animation
                    if capturedImage != nil {
                        showPhotoSettings = true
                    }
                }
            ) {
                CameraView(
                    onCapture: { image in
                        capturedImage = image
                        showCamera = false
                    },
                    onCancel: { showCamera = false }
                )
                .ignoresSafeArea()
            }
            .alert("Conversion Error", isPresented: Binding(
                get: { importVM.errorMessage != nil },
                set: { if !$0 { importVM.errorMessage = nil } }
            )) {
                Button("OK", role: .cancel) { importVM.errorMessage = nil }
            } message: {
                Text(importVM.errorMessage ?? "")
            }
            .overlay {
                if importVM.isConverting {
                    convertingOverlay
                }
            }
        }
    }

    // MARK: - Open in editor (single entry point, mirrors Android onPatternReady)

    private func openInEditor(_ pattern: FusePattern) {
        var p = pattern
        // Repeated imports get distinct names instead of piles of "Imported Photo"
        if p.title == "Imported Photo" {
            let existing = PatternStore.shared.userPatterns
                .filter { $0.title.hasPrefix("Imported Photo") }
                .count
            if existing > 0 { p.title = "Imported Photo \(existing + 1)" }
        }
        // Persist immediately so the pattern exists in the library and editor
        // autosaves have something to update — otherwise all edits are lost.
        if p.createdBy == .user {
            PatternStore.shared.save(p)
        }
        editorPattern = p
    }

    // MARK: - Header

    private var header: some View {
        VStack(spacing: 10) {
            Image(systemName: "sparkles")
                .font(.system(size: 52))
                .foregroundStyle(.purple)
            Text("What will you make?")
                .font(.title2.bold())
            Text("Pick a starting point below")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
    }

    // MARK: - Option rows

    private var options: some View {
        VStack(spacing: 14) {
            optionRow(
                icon: "square.grid.2x2.fill",
                iconColor: .purple,
                title: "Blank Canvas",
                subtitle: "Start from scratch on a fresh grid"
            ) {
                blankTitle = "My Design"
                showBlankSheet = true
            }

            PhotosPicker(
                selection: $importVM.selectedItem,
                matching: .images,
                photoLibrary: .shared()
            ) {
                optionRowContent(
                    icon: "photo.fill",
                    iconColor: .blue,
                    title: "From Photo",
                    subtitle: "Turn a picture into a bead pattern"
                )
            }
            .onChange(of: importVM.selectedItem) { _, item in
                if item != nil {
                    capturedImage = nil
                    showPhotoSettings = true
                }
            }

            if UIImagePickerController.isSourceTypeAvailable(.camera) {
                optionRow(
                    icon: "camera.fill",
                    iconColor: .teal,
                    title: "Camera",
                    subtitle: "Take a photo and convert it"
                ) {
                    showCamera = true
                }
            }

            optionRow(
                icon: "wand.and.stars",
                iconColor: .indigo,
                title: "AI Studio",
                subtitle: "Generate a pattern with Claude AI"
            ) {
                onOpenAIStudio()
            }
        }
    }

    private func optionRow(
        icon: String, iconColor: Color,
        title: String, subtitle: String,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            optionRowContent(icon: icon, iconColor: iconColor, title: title, subtitle: subtitle)
        }
        .buttonStyle(.plain)
    }

    private func optionRowContent(
        icon: String, iconColor: Color,
        title: String, subtitle: String
    ) -> some View {
        HStack(spacing: 16) {
            ZStack {
                RoundedRectangle(cornerRadius: 10)
                    .fill(iconColor.opacity(0.12))
                    .frame(width: 48, height: 48)
                Image(systemName: icon)
                    .font(.title3)
                    .foregroundStyle(iconColor)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.headline)
                Text(subtitle).font(.subheadline).foregroundStyle(.secondary)
            }
            Spacer()
            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundStyle(.tertiary)
        }
        .padding(16)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }

    // MARK: - Converting overlay

    private var convertingOverlay: some View {
        ZStack {
            Color.black.opacity(0.3).ignoresSafeArea()
            VStack(spacing: 16) {
                ProgressView()
                    .tint(.white)
                    .scaleEffect(1.4)
                Text("Converting photo…")
                    .foregroundStyle(.white)
                    .font(.subheadline)
            }
            .padding(32)
            .background(.ultraThinMaterial)
            .clipShape(RoundedRectangle(cornerRadius: 18))
            .accessibilityLabel("Converting photo")
        }
    }

    // MARK: - Blank canvas sheet

    private var blankSheet: some View {
        NavigationStack {
            Form {
                Section("Name") {
                    TextField("Pattern name", text: $blankTitle)
                        .autocorrectionDisabled()
                }
                Section("Grid Size") {
                    ForEach([GridSize.small, .medium, .large, .xlarge], id: \.width) { gs in
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(gs.displayName).font(.body)
                                Text(gridSizeHint(gs)).font(.caption).foregroundStyle(.secondary)
                            }
                            Spacer()
                            if blankGridSize == gs {
                                Image(systemName: "checkmark")
                                    .foregroundStyle(.purple)
                            }
                        }
                        .contentShape(Rectangle())
                        .onTapGesture { blankGridSize = gs }
                    }
                }
            }
            .navigationTitle("New Pattern")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { showBlankSheet = false }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Create") {
                        let title = blankTitle.trimmingCharacters(in: .whitespaces)
                        showBlankSheet = false
                        openInEditor(FusePattern(
                            id: UUID().uuidString,
                            title: title.isEmpty ? "My Design" : title,
                            category: .custom,
                            createdBy: .user,
                            grid: blankGridSize,
                            palette: PaletteColor.defaultPalette,
                            cells: [],
                            difficulty: .easy,
                            tags: [],
                            sourcePrompt: nil,
                            version: 1
                        ))
                    }
                }
            }
        }
        .presentationDetents([.medium])
    }

    private func gridSizeHint(_ gs: GridSize) -> String {
        switch (gs.width, gs.height) {
        case (16, 16): return "Good for icons & simple shapes"
        case (24, 24): return "Balanced size for most designs"
        case (32, 32): return "Standard fuse bead board size"
        default:       return "Large canvas for detailed art"
        }
    }

    // MARK: - Photo settings sheet

    private func loadSettingsImage() async -> UIImage? {
        if let captured = capturedImage { return captured }
        guard let item = importVM.selectedItem,
              let data = try? await item.loadTransferable(type: Data.self) else { return nil }
        return UIImage(data: data)
    }

    private var photoSettingsSheet: some View {
        NavigationStack {
            Form {
                Section("Background") {
                    Toggle("Remove background", isOn: $removeBackground)
                        .onChange(of: removeBackground) { _, isOn in
                            guard isOn, !maskEditor.hasImage else { return }
                            Task {
                                if let image = await loadSettingsImage() {
                                    await maskEditor.load(image: image)
                                }
                            }
                        }
                    if removeBackground {
                        if maskEditor.isProcessing {
                            HStack(spacing: 12) {
                                ProgressView()
                                Text("Finding the subject…")
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                            }
                        } else if maskEditor.previewImage != nil {
                            MaskEditView(editor: maskEditor)
                        }
                        if maskEditor.autoUnavailable && !maskEditor.isProcessing {
                            Text("Automatic selection isn't available — use Remove to paint over the background.")
                                .font(.caption)
                                .foregroundStyle(.red)
                        }
                    }
                }
                Section("Grid Size") {
                    ForEach([GridSize.small, .medium, .large, .xlarge], id: \.width) { gs in
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(gs.displayName).font(.body)
                                Text(gridSizeHint(gs)).font(.caption).foregroundStyle(.secondary)
                            }
                            Spacer()
                            if importVM.selectedGridSize == gs {
                                Image(systemName: "checkmark").foregroundStyle(.purple)
                            }
                        }
                        .contentShape(Rectangle())
                        .onTapGesture { importVM.selectedGridSize = gs }
                    }
                }
                Section("Bead Colors") {
                    Stepper("Max colors: \(importVM.maxColors)", value: $importVM.maxColors, in: 4...24)
                        .monospacedDigit()
                }
            }
            .navigationTitle("Photo to Beads")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        importVM.selectedItem = nil
                        capturedImage = nil
                        showPhotoSettings = false
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Convert") {
                        // capture inputs before dismissal so onDismiss cleanup
                        // can't race the async conversion
                        let masked = removeBackground ? maskEditor.maskedImage() : nil
                        let image = capturedImage
                        didStartConvert = true
                        showPhotoSettings = false
                        Task {
                            if let masked {
                                await importVM.convert(image: masked)
                            } else if let image {
                                await importVM.convert(image: image)
                            } else {
                                await importVM.convert()
                            }
                            capturedImage = nil
                            importVM.selectedItem = nil
                            removeBackground = false
                            maskEditor.reset()
                            if let p = importVM.convertedPattern {
                                openInEditor(p)
                                importVM.convertedPattern = nil
                            }
                        }
                    }
                    .disabled(removeBackground && maskEditor.isProcessing)
                }
            }
        }
        .presentationDetents([.medium, .large])
    }
}

// MARK: - Background mask editor (faded preview + Remove / Add back brush)

private struct MaskEditView: View {
    @ObservedObject var editor: MaskEditor

    var body: some View {
        VStack(spacing: 10) {
            Picker("Brush", selection: $editor.brushAddsBack) {
                Text("Remove").tag(false)
                Text("Add back").tag(true)
            }
            .pickerStyle(.segmented)

            if let preview = editor.previewImage {
                GeometryReader { geo in
                    let fit = fitRect(image: preview.size, in: geo.size)
                    Image(uiImage: preview)
                        .resizable()
                        .scaledToFit()
                        .frame(width: geo.size.width, height: geo.size.height)
                        .contentShape(Rectangle())
                        .gesture(
                            DragGesture(minimumDistance: 0)
                                .onChanged { value in
                                    let nx = (value.location.x - fit.minX) / fit.width
                                    let ny = (value.location.y - fit.minY) / fit.height
                                    guard (0...1).contains(nx), (0...1).contains(ny) else { return }
                                    editor.brush(atNormalized: CGPoint(x: nx, y: ny))
                                }
                        )
                        .accessibilityLabel("Background removal preview. Faded areas will be removed. Drag to adjust.")
                }
                .frame(height: 240)
                .background(Color(.secondarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 12))
            }

            Text("Drag on the photo to adjust — faded areas are left out of the pattern.")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
    }

    /// The rect an aspect-fit image actually occupies inside the container.
    private func fitRect(image: CGSize, in container: CGSize) -> CGRect {
        guard image.width > 0, image.height > 0 else { return .zero }
        let scale = min(container.width / image.width, container.height / image.height)
        let w = image.width * scale
        let h = image.height * scale
        return CGRect(
            x: (container.width - w) / 2,
            y: (container.height - h) / 2,
            width: w, height: h
        )
    }
}
