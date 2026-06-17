import SwiftUI

@MainActor
final class StudioViewModel: ObservableObject {
    @Published var prompt = ""
    @Published var selectedCategory: PatternCategory? = .animals
    @Published var selectedGridSize: GridSize = .large
    @Published var isGenerating = false
    @Published var generatedPattern: FusePattern?
    @Published var errorMessage: String?

    private let service = AIPatternService.shared

    var hasAPIKey: Bool { service.hasAPIKey }

    func generate() async {
        let trimmed = prompt.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        isGenerating = true
        errorMessage = nil
        defer { isGenerating = false }
        do {
            generatedPattern = try await service.generate(
                prompt: trimmed,
                category: selectedCategory,
                gridSize: selectedGridSize
            )
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func iterate(instruction: String) async {
        guard let pattern = generatedPattern else { return }
        isGenerating = true
        errorMessage = nil
        defer { isGenerating = false }
        do {
            generatedPattern = try await service.iterate(pattern: pattern, instruction: instruction)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func saveGenerated() -> FusePattern? {
        guard var pattern = generatedPattern else { return nil }
        pattern.id = UUID().uuidString
        pattern.createdBy = .user
        PatternStore.shared.save(pattern)
        return pattern
    }
}
