import SwiftUI
import PhotosUI

struct CreateView: View {
    @StateObject private var importVM = ImportViewModel()
    @State private var showBlankSheet = false
    @State private var showAIStudio = false
    @State private var importedPattern: FusePattern?
    @State private var newPattern: FusePattern?
    @State private var blankTitle = "My Design"
    @State private var blankGridSize: GridSize = .large

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                Spacer()
                header
                    .padding(.bottom, 40)
                options
                    .padding(.horizontal, 28)
                Spacer()
                Spacer()
            }
            .navigationTitle("Create")
            .navigationDestination(item: $newPattern) { p in
                PatternEditorView(pattern: p)
            }
            .navigationDestination(item: $importedPattern) { p in
                PatternEditorView(pattern: p)
            }
            .sheet(isPresented: $showBlankSheet) {
                blankSheet
            }
            .sheet(isPresented: $showAIStudio) {
                AIStudioView()
            }
            .overlay {
                if importVM.isConverting {
                    convertingOverlay
                }
            }
        }
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
            .onChange(of: importVM.selectedItem) { _, _ in
                Task {
                    await importVM.convert()
                    if let p = importVM.convertedPattern {
                        importedPattern = p
                    }
                }
            }

            optionRow(
                icon: "wand.and.stars",
                iconColor: .indigo,
                title: "AI Studio",
                subtitle: "Generate a pattern with Claude AI"
            ) {
                showAIStudio = true
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
                        newPattern = FusePattern(
                            id: UUID().uuidString,
                            title: title.isEmpty ? "My Design" : title,
                            category: .custom,
                            createdBy: .user,
                            grid: blankGridSize,
                            palette: Array(PaletteColor.beadSafe.prefix(8)),
                            cells: [],
                            difficulty: .easy,
                            tags: [],
                            sourcePrompt: nil,
                            version: 1
                        )
                        showBlankSheet = false
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
}
