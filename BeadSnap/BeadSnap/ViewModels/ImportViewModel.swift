import SwiftUI
import PhotosUI
import UIKit

@MainActor
final class ImportViewModel: ObservableObject {
    @Published var selectedItem: PhotosPickerItem?
    @Published var selectedGridSize: GridSize = .large
    @Published var maxColors: Int = 12
    @Published var isConverting = false
    @Published var convertedPattern: FusePattern?
    @Published var errorMessage: String?

    func convert() async {
        guard let item = selectedItem else { return }
        isConverting = true
        errorMessage = nil
        defer { isConverting = false }
        do {
            guard let data = try await item.loadTransferable(type: Data.self) else {
                errorMessage = "Could not load image."
                return
            }
            convertedPattern = try await Self.convertOffMain(
                data: data, gridSize: selectedGridSize, maxColors: maxColors
            )
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// Convert a camera-captured image through the same pipeline.
    func convert(image: UIImage) async {
        isConverting = true
        errorMessage = nil
        defer { isConverting = false }
        do {
            let gridSize = selectedGridSize
            let colors = maxColors
            convertedPattern = try await Task.detached(priority: .userInitiated) {
                try ImageConverter.shared.convert(image: image, gridSize: gridSize, maxColors: colors)
            }.value
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // Decode + quantize off the main thread so the converting overlay stays live
    private static func convertOffMain(
        data: Data, gridSize: GridSize, maxColors: Int
    ) async throws -> FusePattern {
        try await Task.detached(priority: .userInitiated) {
            guard let image = UIImage(data: data) else {
                throw ConversionError.unreadableImage
            }
            return try ImageConverter.shared.convert(
                image: image, gridSize: gridSize, maxColors: maxColors
            )
        }.value
    }
}
