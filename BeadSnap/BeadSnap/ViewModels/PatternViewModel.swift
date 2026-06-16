import SwiftUI

@MainActor
final class PatternViewModel: ObservableObject {
    @Published var sourceImage: UIImage
    @Published var pattern: BeadPattern?
    @Published var config: PatternConfig = .default
    @Published var isConverting = false
    @Published var selectedEditorColor: BeadColor = BeadColor.palette.first!
    @Published var isEditing = false

    var project: Project?

    private let converter = PatternConverter.shared
    private let persistence = PersistenceService.shared

    init(image: UIImage, project: Project? = nil) {
        self.sourceImage = image
        self.project = project
        if let existing = project?.pattern(for: config) {
            self.pattern = existing
        }
    }

    func generatePattern() async {
        isConverting = true
        let cfg = config
        let img = sourceImage
        let result = await Task.detached(priority: .userInitiated) {
            PatternConverter.shared.convert(image: img, config: cfg)
        }.value
        pattern = result
        isConverting = false
        savePattern()
    }

    func updateConfig(_ newConfig: PatternConfig) {
        config = newConfig
        if let existing = project?.pattern(for: newConfig) {
            pattern = existing
        } else {
            pattern = nil
            Task { await generatePattern() }
        }
    }

    func setBead(row: Int, col: Int, color: BeadColor?) {
        pattern?.setColor(row: row, col: col, colorID: color?.id)
        savePattern()
    }

    func clearBead(row: Int, col: Int) {
        pattern?.setColor(row: row, col: col, colorID: nil)
        savePattern()
    }

    private func savePattern() {
        guard var proj = project, let pat = pattern else { return }
        proj.addPattern(pat)
        persistence.saveProject(proj)
        project = proj
    }

    var colorInventory: [(color: BeadColor, count: Int)] {
        guard let pattern else { return [] }
        return pattern.colorCount
            .compactMap { (id, count) in BeadColor.paletteByID[id].map { ($0, count) } }
            .sorted { $0.count > $1.count }
    }

    var renderedImage: UIImage? {
        guard let pattern else { return nil }
        return PatternConverter.shared.renderPatternImage(pattern: pattern)
    }
}
