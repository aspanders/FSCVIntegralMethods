import SwiftUI

enum MaskBrushMode {
    case include
    case exclude
}

@MainActor
final class BackgroundRemovalViewModel: ObservableObject {
    @Published var originalImage: UIImage
    @Published var maskedImage: UIImage?
    @Published var maskImage: UIImage?
    @Published var isProcessing = false
    @Published var errorMessage: String?

    @Published var brushMode: MaskBrushMode = .include
    @Published var brushSize: CGFloat = 20
    @Published var includeStrokes: [MaskStroke] = []
    @Published var excludeStrokes: [MaskStroke] = []
    @Published var currentStroke: MaskStroke?
    @Published var showMaskOverlay = true

    private let bgService = BackgroundRemovalService.shared

    init(image: UIImage) {
        self.originalImage = image
    }

    func autoRemoveBackground() async {
        isProcessing = true
        errorMessage = nil
        do {
            let (masked, mask) = try await bgService.removeBg(from: originalImage)
            maskedImage = masked
            maskImage = mask
            includeStrokes = []
            excludeStrokes = []
        } catch {
            maskedImage = originalImage
            errorMessage = "Could not auto-remove background. Use the brush tools to remove it manually."
        }
        isProcessing = false
    }

    func beginStroke(at point: CGPoint) {
        currentStroke = MaskStroke(points: [point], brushSize: brushSize)
    }

    func continueStroke(to point: CGPoint) {
        currentStroke?.points.append(point)
    }

    func endStroke() {
        guard let stroke = currentStroke else { return }
        switch brushMode {
        case .include: includeStrokes.append(stroke)
        case .exclude: excludeStrokes.append(stroke)
        }
        currentStroke = nil
        rebuildMaskedImage()
    }

    func undoLastStroke() {
        switch brushMode {
        case .include: if !includeStrokes.isEmpty { includeStrokes.removeLast() }
        case .exclude: if !excludeStrokes.isEmpty { excludeStrokes.removeLast() }
        }
        rebuildMaskedImage()
    }

    func resetMask() {
        maskedImage = originalImage
        maskImage = nil
        includeStrokes = []
        excludeStrokes = []
    }

    private func rebuildMaskedImage() {
        guard let baseMask = maskImage else {
            maskedImage = originalImage
            return
        }
        let updated = bgService.applyManualMask(
            baseMask: baseMask,
            includeStrokes: includeStrokes,
            excludeStrokes: excludeStrokes,
            imageSize: originalImage.size
        )
        maskImage = updated
        maskedImage = bgService.applyMask(updated, to: originalImage)
    }

    var imageForPatternConversion: UIImage {
        maskedImage ?? originalImage
    }
}
