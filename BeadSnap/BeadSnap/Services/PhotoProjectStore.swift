import UIKit
import Combine

/// One pattern derived from a project's photo, with the settings that made it.
struct PhotoVariant: Codable, Identifiable, Equatable {
    var patternId: String
    var label: String
    var createdAt: Double
    var id: String { patternId }
}

/// A photo and every pattern made from it.
///
/// The photo is the parent; the variants are the different boards, colour
/// counts, shapes and background cut-outs tried against it. Only the photo lives
/// here - the patterns themselves stay ordinary user patterns in PatternStore,
/// so opening a variant in the editor, autosaving it and exporting it all work
/// with no special cases.
struct PhotoProject: Codable, Identifiable, Equatable {
    var id: String
    var title: String
    var createdAt: Double
    var variants: [PhotoVariant] = []
    /// Whether a background-removed copy was kept alongside the original.
    ///
    /// Both are stored on purpose. Keeping only the cut-out would make the
    /// removal permanent - "different background removals" is one of the things
    /// a variant is supposed to differ in, and a cut-out cannot be un-cut.
    /// Keeping only the original would throw away brushwork done by hand.
    var hasCutout: Bool = false
}

/// Keeps the source photos so a pattern can be re-derived from the original
/// months later, instead of the photo being thrown away the moment the first
/// conversion finished.
///
/// A port of the Android `PhotoProjectStore`, including both faults found in it
/// during review: a failed PNG write that reported success, and an index that
/// raced itself on every save. See `writePNG` and `persist`.
///
/// The photo is written as PNG, not JPEG, because a background-removed source
/// carries an alpha channel and JPEG would silently flatten it onto black.
@MainActor
final class PhotoProjectStore: ObservableObject {
    static let shared = PhotoProjectStore()

    @Published private(set) var projects: [PhotoProject] = []
    @Published var lastError: String?

    private let dir: URL
    private let indexFile: URL

    /// Every index write goes through this one queue, in order. See `persist`.
    private let ioQueue = DispatchQueue(label: "com.beadsnap.photoprojects", qos: .utility)
    private var writeSeq: Int = 0

    private init() {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        dir = docs.appendingPathComponent("projects", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        indexFile = dir.appendingPathComponent("projects.json")
        load()
    }

    private func load() {
        guard let data = try? Data(contentsOf: indexFile),
              let decoded = try? JSONDecoder().decode([PhotoProject].self, from: data) else {
            projects = []
            return
        }
        projects = decoded.sorted { $0.createdAt > $1.createdAt }
    }

    // MARK: - Files

    private func projectDir(_ projectId: String) -> URL {
        let d = dir.appendingPathComponent(projectId, isDirectory: true)
        try? FileManager.default.createDirectory(at: d, withIntermediateDirectories: true)
        return d
    }

    func sourceFile(_ projectId: String) -> URL {
        projectDir(projectId).appendingPathComponent("source.png")
    }

    func cutoutFile(_ projectId: String) -> URL {
        projectDir(projectId).appendingPathComponent("cutout.png")
    }

    /// `cutout` true loads the background-removed copy, if the project has one.
    ///
    /// Our own PNG, written upright and already size-bounded, so unlike a photo
    /// from the picker there is no orientation to re-apply here.
    func loadSource(_ projectId: String, cutout: Bool = false) -> UIImage? {
        let f = cutout ? cutoutFile(projectId) : sourceFile(projectId)
        guard let data = try? Data(contentsOf: f) else { return nil }
        return UIImage(data: data)
    }

    // MARK: - Mutations

    /// Start a project from `source`. Returns immediately; the PNG is written on
    /// this store's own queue so navigating away cannot cancel it half-finished.
    @discardableResult
    func createProject(title: String, source: UIImage, cutout: UIImage? = nil) -> PhotoProject {
        let project = PhotoProject(
            id: UUID().uuidString,
            title: title,
            createdAt: Date().timeIntervalSince1970,
            hasCutout: cutout != nil
        )
        persist(projects + [project])

        let srcFile = sourceFile(project.id)
        let cutFile = cutoutFile(project.id)
        ioQueue.async { [weak self] in
            do {
                try Self.writePNG(source, to: srcFile)
                if let cutout { try Self.writePNG(cutout, to: cutFile) }
                Task { @MainActor in self?.lastError = nil }
            } catch {
                Task { @MainActor in
                    self?.lastError = "Could not save the photo for \"\(title)\": \(error.localizedDescription)"
                }
            }
        }
        return project
    }

    /// Writes `image` to `target`, or throws.
    ///
    /// Two things the Android one-liner this replaces got wrong, both worth
    /// keeping out of the Swift. Encoding failure is reported by a nil return,
    /// not by throwing, so an out-of-space device produced a truncated file that
    /// the caller recorded as a success - and since the project row was already
    /// in the index and the file then existed, the photo came back nil forever:
    /// a blank thumbnail that could never re-derive a pattern, with no error
    /// ever shown. And it wrote straight into the destination, so a failed
    /// re-save destroyed the good file already there. Write beside it and move,
    /// which is atomic.
    private static func writePNG(_ image: UIImage, to target: URL) throws {
        guard let data = image.pngData() else {
            throw NSError(domain: "BeadSnap", code: 1, userInfo: [
                NSLocalizedDescriptionKey: "Could not encode \(target.lastPathComponent)"
            ])
        }
        let tmp = target.deletingLastPathComponent()
            .appendingPathComponent("\(target.lastPathComponent).\(UUID().uuidString).tmp")
        do {
            try data.write(to: tmp, options: .atomic)
            try moveIntoPlace(tmp, target)
        } catch {
            try? FileManager.default.removeItem(at: tmp)
            throw error
        }
    }

    /// Move `tmp` onto `target`, whether or not `target` already exists.
    ///
    /// `replaceItemAt` throws when the destination is missing, which is exactly
    /// the FIRST write of every file - so using it alone would have failed to
    /// save the very first photo of every project and the very first index.
    private static func moveIntoPlace(_ tmp: URL, _ target: URL) throws {
        if FileManager.default.fileExists(atPath: target.path) {
            _ = try FileManager.default.replaceItemAt(target, withItemAt: tmp)
        } else {
            try FileManager.default.moveItem(at: tmp, to: target)
        }
    }

    func addVariant(_ projectId: String, patternId: String, label: String) {
        persist(projects.map { p in
            guard p.id == projectId else { return p }
            var copy = p
            // Re-saving the same pattern updates its label rather than adding a
            // second row for it.
            copy.variants = p.variants.filter { $0.patternId != patternId }
                + [PhotoVariant(patternId: patternId, label: label,
                                createdAt: Date().timeIntervalSince1970)]
            return copy
        })
    }

    func removeVariant(_ projectId: String, patternId: String) {
        persist(projects.map { p in
            guard p.id == projectId else { return p }
            var copy = p
            copy.variants = p.variants.filter { $0.patternId != patternId }
            return copy
        })
    }

    func rename(_ projectId: String, title: String) {
        persist(projects.map { p in
            guard p.id == projectId else { return p }
            var copy = p
            copy.title = title
            return copy
        })
    }

    /// Drops the project and its photo. Variant patterns are the caller's call.
    func delete(_ projectId: String) {
        persist(projects.filter { $0.id != projectId })
        let d = dir.appendingPathComponent(projectId, isDirectory: true)
        ioQueue.async { try? FileManager.default.removeItem(at: d) }
    }

    func clearLastError() { lastError = nil }

    // MARK: - Index

    /// Index writes are serialised and last-one-wins.
    ///
    /// The Android version launched each write onto a concurrent pool, all of
    /// them using one hard-coded temp path. Saving a photo fires two persists in
    /// the same frame - createProject then addVariant - so it was hit on every
    /// conversion. Either the second move found the temp file already taken away
    /// and reported a spurious failure over a save that worked, leaving the older
    /// snapshot on disk so the variant vanished on restart; or one write
    /// truncated the temp another was mid-move on, and the next cold start hit a
    /// decode error that `load()` swallows into an empty list - after which the
    /// next mutation writes that empty list back and every project is gone.
    ///
    /// A serial queue removes the interleaving. The sequence number means a
    /// snapshot already superseded in memory is not written at all, so the last
    /// state on disk is the last state the user produced.
    private func persist(_ next: [PhotoProject]) {
        let sorted = next.sorted { $0.createdAt > $1.createdAt }
        projects = sorted
        writeSeq += 1
        let seq = writeSeq
        let target = indexFile
        let folder = dir

        // No "is this snapshot superseded" check. A serial queue is FIFO, so
        // the blocks run in submission order and the last snapshot submitted is
        // the last one written - which is the property that actually matters.
        // Skipping intermediate writes would only save IO, and getting at the
        // newest sequence number from here would mean reading main-actor state
        // off the main actor.
        ioQueue.async { [weak self] in
            let tmp = folder.appendingPathComponent("projects.json.\(seq).tmp")
            do {
                let encoder = JSONEncoder()
                encoder.outputFormatting = .prettyPrinted
                try encoder.encode(sorted).write(to: tmp, options: .atomic)
                try Self.moveIntoPlace(tmp, target)
                Task { @MainActor in self?.lastError = nil }
            } catch {
                try? FileManager.default.removeItem(at: tmp)
                Task { @MainActor in
                    self?.lastError = "Could not save your photo projects: \(error.localizedDescription)"
                }
            }
        }
    }

    /// "32×32 · 12 colours · Circle · No background" - what makes it differ.
    static func labelFor(_ pattern: FusePattern, cutout: Bool = false) -> String {
        "\(pattern.grid.width)×\(pattern.grid.height) · "
            + "\(pattern.palette.count) colours · \(pattern.shape.displayName)"
            + (cutout ? " · No background" : "")
    }
}
