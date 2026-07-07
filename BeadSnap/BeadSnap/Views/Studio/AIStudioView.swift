import SwiftUI

struct AIStudioView: View {
    @StateObject private var viewModel = StudioViewModel()
    @State private var showAPIKeySheet = false
    @State private var apiKeyInput = ""
    @State private var iterateInstruction = ""
    @State private var showIterateSheet = false
    @State private var editingPattern: FusePattern?

    var body: some View {
        NavigationStack {
            Form {
                if !viewModel.hasAPIKey {
                    apiKeyBanner
                } else {
                    Section {
                        Button {
                            apiKeyInput = ""
                            showAPIKeySheet = true
                        } label: {
                            Label("Change API Key", systemImage: "key")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                promptSection
                settingsSection
                if let error = viewModel.errorMessage {
                    Section {
                        Text(error)
                            .foregroundStyle(.red)
                            .font(.caption)
                    }
                }
                if let pattern = viewModel.generatedPattern {
                    previewSection(pattern)
                }
            }
            .navigationTitle("AI Studio")
            .navigationBarTitleDisplayMode(.inline)
            .navigationDestination(item: $editingPattern) { p in
                PatternEditorView(pattern: p)
            }
            .sheet(isPresented: $showAPIKeySheet) {
                apiKeySheet
            }
            .sheet(isPresented: $showIterateSheet) {
                iterateSheet
            }
        }
    }

    // MARK: - API key banner

    private var apiKeyBanner: some View {
        Section {
            Button {
                showAPIKeySheet = true
            } label: {
                Label("Set Up AI (API Key Required)", systemImage: "key")
                    .foregroundStyle(.purple)
            }
        } footer: {
            Text("AI Studio needs a free Claude API key from console.anthropic.com.")
        }
    }

    // MARK: - Prompt

    private var promptSection: some View {
        Section("Describe your pattern") {
            TextField(
                "e.g. a cute orange cat sitting in a flower field",
                text: $viewModel.prompt,
                axis: .vertical
            )
            .lineLimit(2...5)
            .autocorrectionDisabled()

            if viewModel.isGenerating {
                HStack {
                    Spacer()
                    ProgressView().tint(.purple)
                    Text("Generating…").font(.subheadline).foregroundStyle(.secondary)
                    Spacer()
                    Button("Cancel") { viewModel.cancelGeneration() }
                        .foregroundStyle(.red)
                }
            } else {
                Button {
                    viewModel.generate()
                } label: {
                    HStack {
                        Spacer()
                        Label("Generate", systemImage: "wand.and.stars").foregroundStyle(.purple)
                        Spacer()
                    }
                }
                .disabled(
                    viewModel.prompt.trimmingCharacters(in: .whitespaces).isEmpty
                    || !viewModel.hasAPIKey
                )
            }
        }
    }

    // MARK: - Settings

    private var settingsSection: some View {
        Section("Options") {
            Picker("Category", selection: $viewModel.selectedCategory) {
                Text("Any").tag(Optional<PatternCategory>.none)
                ForEach(PatternCategory.allCases) { cat in
                    Text("\(cat.emoji) \(cat.displayName)").tag(Optional(cat))
                }
            }
            Picker("Grid Size", selection: $viewModel.selectedGridSize) {
                ForEach([GridSize.small, .medium, .large], id: \.width) { gs in
                    Text(gs.displayName).tag(gs)
                }
            }
        }
    }

    // MARK: - Preview

    private func previewSection(_ pattern: FusePattern) -> some View {
        Section("Result") {
            PatternThumbnail(pattern: pattern)
                .aspectRatio(
                    CGFloat(pattern.grid.width) / CGFloat(pattern.grid.height),
                    contentMode: .fit
                )
                .frame(maxHeight: 220)
                .clipShape(RoundedRectangle(cornerRadius: 10))

            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(pattern.title).font(.headline)
                    Text("\(pattern.grid.displayName) · \(pattern.totalBeads) beads")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Text(pattern.difficulty.emoji + " " + pattern.difficulty.displayName)
                    .font(.caption)
            }

            Button {
                showIterateSheet = true
            } label: {
                Label("Refine with AI", systemImage: "arrow.triangle.2.circlepath")
                    .foregroundStyle(.indigo)
            }
            .disabled(viewModel.isGenerating)

            Button {
                if let saved = viewModel.saveGenerated() {
                    editingPattern = saved
                }
            } label: {
                Label("Save & Edit", systemImage: "square.and.arrow.down")
                    .foregroundStyle(.purple)
            }
            .disabled(viewModel.isGenerating)
        }
    }

    // MARK: - Iterate sheet

    private var iterateSheet: some View {
        NavigationStack {
            Form {
                Section("What would you like to change?") {
                    TextField(
                        "e.g. make it more colorful, add a hat",
                        text: $iterateInstruction,
                        axis: .vertical
                    )
                    .lineLimit(2...4)
                    .autocorrectionDisabled()
                }
            }
            .navigationTitle("Refine Pattern")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { showIterateSheet = false }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Apply") {
                        let inst = iterateInstruction.trimmingCharacters(in: .whitespaces)
                        guard !inst.isEmpty else { return }
                        showIterateSheet = false
                        viewModel.iterate(instruction: inst)
                        iterateInstruction = ""
                    }
                    .bold()
                    .disabled(iterateInstruction.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
        }
        .presentationDetents([.medium])
    }

    // MARK: - API key sheet

    private var apiKeySheet: some View {
        NavigationStack {
            Form {
                Section {
                    SecureField("sk-ant-...", text: $apiKeyInput)
                        .autocorrectionDisabled()
                        .textInputAutocapitalization(.never)
                } header: {
                    Text("Claude API Key")
                } footer: {
                    Text("Get a free key at console.anthropic.com. Stored securely in the iOS Keychain.")
                }
            }
            .navigationTitle("Set Up AI")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { showAPIKeySheet = false }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        viewModel.saveAPIKey(apiKeyInput)
                        showAPIKeySheet = false
                    }
                    .bold()
                    .disabled(apiKeyInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
        }
    }
}
