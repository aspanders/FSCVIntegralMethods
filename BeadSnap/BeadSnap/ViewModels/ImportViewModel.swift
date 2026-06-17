import SwiftUI
import PhotosUI

@MainActor
final class ImportViewModel: ObservableObject {
    @Published var selectedItem: PhotosPickerItem?
    @Published var selectedGridSize: GridSize = .large
    @Published var maxColors: Int = 12
    @Published var isConverting = false
    @Published var convertedPattern: FusePattern?
    @Published var errorMessage: String?

    private let converter = ImageConverter.shared

    func convert() async {
        guard let item = selectedItem else { return }
        isConverting = true
        errorMessage = nil
        defer { isConverting = false }
        do {
            guard let data = try await item.loadTransferable(type: Data.self),
                  let image = UIImage(data: data) else {
                errorMessage = "Could not load image."
                return
            }
            convertedPattern = converter.convert(
                image: image,
                gridSize: selectedGridSize,
                maxColors: maxColors
            )
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func saveConverted(title: String) -> FusePattern? {
        guard var pattern = convertedPattern else { return nil }
        pattern.title = title.trimmingCharacters(in: .whitespaces).isEmpty ? "Imported Photo" : title
        pattern.id = UUID().uuidString
        PatternStore.shared.save(pattern)
        return pattern
    }
}
