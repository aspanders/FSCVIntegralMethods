import SwiftUI

@MainActor
final class StudioViewModel: ObservableObject {
    @Published var prompt = ""
    @Published var selectedCategory: PatternCategory? = .geometric
    @Published var selectedGridSize: GridSize = .large
    @Published var isGenerating = false
    @Published var generatedPattern: FusePattern?
    @Published var errorMessage: String?
    @Published private(set) var hasAPIKey: Bool
    @Published private(set) var provider: AIProvider

    private let service = AIPatternService.shared
    private var generationTask: Task<Void, Never>?
    private var isSaving = false

    init() {
        let svc = AIPatternService.shared
        provider = svc.provider
        hasAPIKey = svc.hasAPIKey
    }

    func refreshAPIKeyStatus() {
        hasAPIKey = service.hasAPIKey
        provider = service.provider
    }

    var apiKey: String { service.apiKey }
    func apiKey(for p: AIProvider) -> String { service.apiKey(for: p) }
    func hasKey(for p: AIProvider) -> Bool { service.hasAPIKey(for: p) }

    /// Save the key for a provider and make it the active one.
    func saveAPIKey(_ key: String, for p: AIProvider) {
        // The keychain write can fail - a locked device, a keychain the OS will
        // not open. Without this the sheet closed, nothing was stored, and the
        // next tap said "No API key set" again, so the user retyped it forever.
        guard service.setAPIKey(key, for: p) else {
            errorMessage = "This device would not let us store the key securely. "
                + "AI features need the keychain, and we will not keep a key without it."
            return
        }
        service.provider = p
        refreshAPIKeyStatus()
    }

    func generate() {
        let trimmed = prompt.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        isGenerating = true
        errorMessage = nil
        generationTask = Task { [weak self] in
            guard let self else { return }
            defer { self.isGenerating = false }
            do {
                let pattern = try await self.service.generate(
                    prompt: trimmed,
                    category: self.selectedCategory,
                    gridSize: self.selectedGridSize
                )
                if !Task.isCancelled { self.generatedPattern = pattern }
            } catch is CancellationError {
                // user cancelled
            } catch {
                if !Task.isCancelled { self.errorMessage = error.localizedDescription }
            }
        }
    }

    func cancelGeneration() {
        generationTask?.cancel()
        isGenerating = false
    }

    func iterate(instruction: String) {
        guard let pattern = generatedPattern else { return }
        isGenerating = true
        errorMessage = nil
        generationTask = Task { [weak self] in
            guard let self else { return }
            defer { self.isGenerating = false }
            do {
                let updated = try await self.service.iterate(pattern: pattern, instruction: instruction)
                if !Task.isCancelled { self.generatedPattern = updated }
            } catch is CancellationError {
                // user cancelled
            } catch {
                if !Task.isCancelled { self.errorMessage = error.localizedDescription }
            }
        }
    }

    func saveGenerated() -> FusePattern? {
        guard !isSaving, var pattern = generatedPattern else { return nil }
        isSaving = true
        defer { isSaving = false }
        pattern.id = UUID().uuidString
        pattern.createdBy = .user
        PatternStore.shared.save(pattern)
        return pattern
    }
}
