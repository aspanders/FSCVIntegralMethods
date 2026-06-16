import UIKit

final class PersistenceService: ObservableObject {
    static let shared = PersistenceService()

    private let projectsURL: URL
    private let imagesURL: URL

    @Published var projects: [Project] = []

    private init() {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        projectsURL = docs.appendingPathComponent("projects.json")
        imagesURL = docs.appendingPathComponent("images", isDirectory: true)
        try? FileManager.default.createDirectory(at: imagesURL, withIntermediateDirectories: true)
        load()
    }

    private func load() {
        guard let data = try? Data(contentsOf: projectsURL),
              let decoded = try? JSONDecoder().decode([Project].self, from: data) else {
            projects = []
            return
        }
        projects = decoded.sorted { $0.updatedAt > $1.updatedAt }
    }

    private func save() {
        guard let data = try? JSONEncoder().encode(projects) else { return }
        try? data.write(to: projectsURL)
    }

    func saveProject(_ project: Project) {
        if let idx = projects.firstIndex(where: { $0.id == project.id }) {
            projects[idx] = project
        } else {
            projects.insert(project, at: 0)
        }
        save()
    }

    func deleteProject(_ project: Project) {
        projects.removeAll { $0.id == project.id }
        deleteImage(named: project.originalImageFilename)
        if let masked = project.maskedImageFilename {
            deleteImage(named: masked)
        }
        save()
    }

    func saveImage(_ image: UIImage, filename: String) {
        let url = imagesURL.appendingPathComponent(filename)
        if let data = image.jpegData(compressionQuality: 0.85) {
            try? data.write(to: url)
        }
    }

    func loadImage(named filename: String) -> UIImage? {
        let url = imagesURL.appendingPathComponent(filename)
        guard let data = try? Data(contentsOf: url) else { return nil }
        return UIImage(data: data)
    }

    func deleteImage(named filename: String) {
        let url = imagesURL.appendingPathComponent(filename)
        try? FileManager.default.removeItem(at: url)
    }

    func uniqueImageFilename(ext: String = "jpg") -> String {
        "\(UUID().uuidString).\(ext)"
    }
}
