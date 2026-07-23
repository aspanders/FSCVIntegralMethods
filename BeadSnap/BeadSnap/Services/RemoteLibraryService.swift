import Foundation

struct LibraryManifest: Decodable {
    let version: Int
    let count: Int
    let patternsUrl: String
    let updatedAt: String

    enum CodingKeys: String, CodingKey {
        case version, count, patternsUrl, updatedAt
    }
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        version = try c.decode(Int.self, forKey: .version)
        count = try c.decodeIfPresent(Int.self, forKey: .count) ?? 0
        patternsUrl = try c.decode(String.self, forKey: .patternsUrl)
        updatedAt = try c.decodeIfPresent(String.self, forKey: .updatedAt) ?? ""
    }
}

struct RemotePatterns: Decodable {
    let version: Int
    let patterns: [FusePattern]
}

/// Keeps the app's pattern library up to date from a hosted manifest.
///
/// Fetches the tiny manifest.json; if its version is newer than what we've
/// already applied, downloads patterns.json, hands it to PatternStore (which
/// caches + merges it), and records the new version. Cheap to call on launch.
@MainActor
final class RemoteLibraryService: ObservableObject {
    static let shared = RemoteLibraryService()
    private init() {}

    // Point this at wherever manifest.json is hosted (raw GitHub, Pages, CDN…).
    private let manifestURL = URL(string:
        "https://raw.githubusercontent.com/aspanders/FSCVIntegralMethods/" +
        "claude/fuse-bead-converter-app-706h2s/library/manifest.json")!

    // Version of library.json shipped in the app bundle. Keep in sync with the
    // "version" field of the bundled resource when you refresh it.
    private let bundledLibraryVersion = 2

    private let versionKey = "remoteLibrary.appliedVersion"

    /// Set to the new pattern count when an update is applied; UI shows a banner.
    @Published var updateApplied: Int?

    private var appliedVersion: Int {
        get { UserDefaults.standard.integer(forKey: versionKey) }
        set { UserDefaults.standard.set(newValue, forKey: versionKey) }
    }

    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 15
        config.timeoutIntervalForResource = 30
        return URLSession(configuration: config)
    }()

    /// Check for and apply a newer library. Silent + non-fatal on any failure
    /// (offline, malformed, already current): keeps whatever is already loaded.
    func syncIfNeeded() async {
        guard let manifestData = try? await session.data(from: manifestURL).0,
              let manifest = try? JSONDecoder().decode(LibraryManifest.self, from: manifestData),
              manifest.version > max(appliedVersion, bundledLibraryVersion),
              let patternsURL = URL(string: manifest.patternsUrl)
        else { return }

        guard let (body, _) = try? await session.data(from: patternsURL),
              let remote = try? JSONDecoder().decode(RemotePatterns.self, from: body)
        else { return }

        PatternStore.shared.applyRemoteLibrary(remote.patterns, rawData: body)
        appliedVersion = manifest.version
        updateApplied = remote.patterns.count
    }
}
