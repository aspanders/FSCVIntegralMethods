import SwiftUI

struct PatternCard: View {
    let pattern: FusePattern

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            PatternThumbnail(pattern: pattern)
                .aspectRatio(1, contentMode: .fit)
                .clipShape(RoundedRectangle(cornerRadius: 10))
                .shadow(color: .black.opacity(0.08), radius: 4, y: 2)
                .accessibilityHidden(true)

            Text(pattern.title)
                .font(.caption)
                .fontWeight(.semibold)
                .lineLimit(1)
                .foregroundStyle(.primary)

            HStack(spacing: 4) {
                Text(pattern.difficulty.emoji)
                    .font(.caption2)
                Text("\(pattern.totalBeads) beads")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .monospacedDigit()
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(pattern.title), \(pattern.difficulty.displayName), \(pattern.totalBeads) beads")
    }
}

// MARK: - Thumbnail renderer with background caching

struct PatternThumbnail: View {
    let pattern: FusePattern
    @State private var thumbnail: UIImage?

    private var cacheKey: String { "\(pattern.id)-v\(pattern.version)" }

    var body: some View {
        Group {
            if let thumbnail {
                Image(uiImage: thumbnail)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
            } else {
                Color(.systemGray6)
            }
        }
        .background(Color(.systemGray6))
        .task(id: cacheKey) {
            if let cached = ThumbnailCache.shared.get(key: cacheKey) {
                thumbnail = cached
                return
            }
            let rendered = await Self.renderAsync(pattern: pattern)
            ThumbnailCache.shared.set(rendered, for: cacheKey)
            thumbnail = rendered
        }
    }

    private static func renderAsync(pattern: FusePattern) async -> UIImage {
        let p = pattern
        // Same shared renderer as previews and export, so thumbnails match Android
        return await Task.detached(priority: .userInitiated) {
            ImageConverter.renderToImage(pattern: p, cellSize: 6)
        }.value
    }
}

// MARK: - Thumbnail cache

private final class ThumbnailCache {
    static let shared = ThumbnailCache()
    private let cache = NSCache<NSString, UIImage>()
    private init() { cache.countLimit = 200 }
    func get(key: String) -> UIImage? { cache.object(forKey: key as NSString) }
    func set(_ image: UIImage, for key: String) { cache.setObject(image, forKey: key as NSString) }
}
