import SwiftUI

struct AIStudioView: View {
    @StateObject private var viewModel = StudioViewModel()
    @State private var showAPIKeySheet = false
    @State private var apiKeyInput = ""
    @State private var savedPattern: FusePattern?
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                if !viewModel.hasAPIKey {
                    apiKeyBanner
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
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .sheet(isPresented: $showAPIKeySheet) {
                apiKeySheet
            }
            .navigationDestination(item: $savedPattern) { p in
                PatternEditorView(pattern: p)
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

            Button {
                Task { await viewModel.generate() }
            } label: {
                HStack {
                    Spacer()
                    if viewModel.isGenerating {
                        ProgressView().tint(.purple)
                    } else {
                        Label("Generate", systemImage: "wand.and.stars")
                            .foregroundStyle(.purple)
                    }
                    Spacer()
                }
            }
            .disabled(
                viewModel.prompt.trimmingCharacters(in: .whitespaces).isEmpty
                || viewModel.isGenerating
                || !viewModel.hasAPIKey
            )
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
                ForEach([GridSize.small, .medium, .large, .xlarge], id: \.width) { gs in
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
                savedPattern = viewModel.saveGenerated()
            } label: {
                Label("Save & Edit", systemImage: "square.and.arrow.down")
                    .foregroundStyle(.purple)
            }
        }
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
                    Text("Get a free key at console.anthropic.com. The key is stored only on your device.")
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
                        AIPatternService.shared.apiKey = apiKeyInput.trimmingCharacters(in: .whitespaces)
                        showAPIKeySheet = false
                    }
                    .disabled(apiKeyInput.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
        }
    }
}
