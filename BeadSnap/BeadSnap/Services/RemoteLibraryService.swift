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

    // Where the hosted library lives, tried in order until one answers.
    //
    // A LIST, not a single URL, because the previous single URL pinned the
    // library to one git branch: deleting that branch after a merge would have
    // cut off pattern updates for every installed copy of the app, with no way
    // to fix it except shipping a new build to the App Store. Now the first
    // source that returns a usable manifest wins, so the library can move
    // between branches - or off GitHub entirely, onto Pages or a CDN - by
    // adding the new home to the front of this list in a future release while
    // the old one keeps serving everybody who has not updated yet.
    //
    // A source that 404s costs one cheap request and falls through to the next.
    // Keep in sync with the same list in the Android RemoteLibraryService.
    private let sources = [
        "https://raw.githubusercontent.com/aspanders/FSCVIntegralMethods/main",
        "https://raw.githubusercontent.com/aspanders/FSCVIntegralMethods/" +
        "claude/fuse-bead-converter-app-706h2s",
    ]

    // Version of library.json shipped in the app bundle. Keep in sync with the
    // "version" field of the bundled resource when you refresh it.
    private let bundledLibraryVersion = 52

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
        for base in sources {
            guard let manifestData = await fetch("\(base)/library/manifest.json"),
                  let manifest = try? JSONDecoder().decode(LibraryManifest.self,
                                                          from: manifestData)
            else { continue }   // offline, 404, or malformed: try the next source

            // The app already ships bundledLibraryVersion as a resource, so only
            // download when the hosted library is strictly newer. A source that
            // answered and is not newer means we are up to date - stop, rather
            // than asking the others the same question.
            guard manifest.version > max(appliedVersion, bundledLibraryVersion) else { return }

            // The sibling of the manifest we actually fetched comes first, and
            // the absolute patternsUrl written inside it second: that is what
            // lets the library be re-hosted without regenerating anything, since
            // a manifest copied to a new home still records the OLD patternsUrl.
            var body: Data?
            for candidate in ["\(base)/library/patterns.json", manifest.patternsUrl] {
                if let data = await fetch(candidate) { body = data; break }
            }
            guard let body,
                  let remote = try? JSONDecoder().decode(RemotePatterns.self, from: body)
            else { continue }

            PatternStore.shared.applyRemoteLibrary(remote.patterns, rawData: body)
            appliedVersion = manifest.version
            updateApplied = remote.patterns.count
            return
        }
    }

    /// GET a URL, returning nil on any failure INCLUDING a non-2xx status.
    ///
    /// The status check is the point. `URLSession.data(from:)` does not throw on
    /// a 404 - it hands back the error page as a perfectly good body - so
    /// without this a missing source would return GitHub's "404: Not Found"
    /// text and be treated as a fetch that worked but decoded badly. With a
    /// list of sources that distinction decides whether we fall through to the
    /// next one.
    private func fetch(_ url: String) async -> Data? {
        guard let url = URL(string: url) else { return nil }
        guard let (data, response) = try? await session.data(from: url) else { return nil }
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode)
        else { return nil }
        return data
    }
}
