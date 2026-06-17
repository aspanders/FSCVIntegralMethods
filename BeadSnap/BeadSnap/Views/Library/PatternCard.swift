import SwiftUI

struct PatternCard: View {
    let pattern: FusePattern

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            PatternThumbnail(pattern: pattern)
                .aspectRatio(1, contentMode: .fit)
                .clipShape(RoundedRectangle(cornerRadius: 10))
                .shadow(color: .black.opacity(0.08), radius: 4, y: 2)

            Text(pattern.title)
                .font(.caption)
                .fontWeight(.semibold)
                .lineLimit(1)
                .foregroundStyle(.primary)

            HStack(spacing: 4) {
                Text(pattern.difficulty.emoji)
                    .font(.caption2)
                Text("\(pattern.totalBeads)")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .monospacedDigit()
            }
        }
    }
}

// MARK: - Thumbnail renderer

struct PatternThumbnail: View {
    let pattern: FusePattern

    var body: some View {
        GeometryReader { geo in
            Canvas { ctx, size in
                let cols = CGFloat(pattern.grid.width)
                let rows = CGFloat(pattern.grid.height)
                let cellW = size.width / cols
                let cellH = size.height / rows
                let lookup = Dictionary(
                    uniqueKeysWithValues: pattern.palette.map { ($0.id, Color($0.uiColor)) }
                )
                for cell in pattern.cells {
                    guard let cid = cell.colorId, let color = lookup[cid] else { continue }
                    let rect = CGRect(
                        x: CGFloat(cell.x) * cellW,
                        y: CGFloat(cell.y) * cellH,
                        width: cellW, height: cellH
                    )
                    ctx.fill(Path(rect), with: .color(color))
                }
            }
            .background(Color(.systemGray6))
            .frame(width: geo.size.width, height: geo.size.height)
        }
    }
}
