import SwiftUI

@MainActor
final class StudioViewModel: ObservableObject {
    @Published var prompt = ""
    @Published var selectedCategory: PatternCategory? = .animals
    @Published var selectedGridSize: GridSize = .large
    @Published var isGenerating = false
    @Published var generatedPattern: FusePattern?
    @Published var errorMessage: String?
    @Published private(set) var hasAPIKey: Bool

    private let service = AIPatternService.shared
    private var generationTask: Task<Void, Never>?
    private var isSaving = false

    init() {
        hasAPIKey = AIPatternService.shared.hasAPIKey
    }

    func refreshAPIKeyStatus() {
        hasAPIKey = service.hasAPIKey
    }

    func generate() {
        let trimmed = prompt.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        isGenerating = true
        errorMessage = nil
        generationTask = Task { [weak self] in
            guard let self else { return }
            defer { self.isGenerating = false }
            do {
                self.generatedPattern = try await self.service.generate(
                    prompt: trimmed,
                    category: self.selectedCategory,
                    gridSize: self.selectedGridSize
                )
            } catch is CancellationError {
                // user cancelled
            } catch {
                self.errorMessage = error.localizedDescription
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
                self.generatedPattern = try await self.service.iterate(pattern: pattern, instruction: instruction)
            } catch is CancellationError {
                // user cancelled
            } catch {
                self.errorMessage = error.localizedDescription
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
