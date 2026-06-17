import SwiftUI

struct BeadGridView: View {
    @ObservedObject var viewModel: EditorViewModel
    @State private var cellSize: CGFloat = 22

    private let minCell: CGFloat = 8
    private let maxCell: CGFloat = 44

    var body: some View {
        VStack(spacing: 0) {
            zoomBar
                .padding(.vertical, 6)
            ScrollView([.horizontal, .vertical], showsIndicators: false) {
                grid
                    .padding(8)
            }
        }
    }

    // MARK: - Grid

    private var grid: some View {
        let cols = viewModel.pattern.grid.width
        let rows = viewModel.pattern.grid.height
        let totalCells = cols * rows
        return LazyVGrid(
            columns: Array(
                repeating: GridItem(.fixed(cellSize), spacing: 1),
                count: cols
            ),
            spacing: 1
        ) {
            ForEach(0..<totalCells, id: \.self) { idx in
                let x = idx % cols
                let y = idx / cols
                BeadCellView(
                    color: viewModel.color(at: x, y: y)?.swiftUIColor,
                    size: cellSize
                )
                .frame(width: cellSize, height: cellSize)
                .contentShape(Rectangle())
                .onTapGesture { viewModel.tapCell(x: x, y: y) }
                .onLongPressGesture(minimumDuration: 0.4) {
                    viewModel.clearCell(x: x, y: y)
                }
            }
        }
    }

    // MARK: - Zoom bar

    private var zoomBar: some View {
        HStack(spacing: 20) {
            Button {
                cellSize = max(minCell, cellSize - 4)
            } label: {
                Image(systemName: "minus.magnifyingglass")
                    .font(.title3)
            }
            .disabled(cellSize <= minCell)

            Text("\(Int(cellSize))px")
                .font(.caption)
                .monospacedDigit()
                .foregroundStyle(.secondary)

            Button {
                cellSize = min(maxCell, cellSize + 4)
            } label: {
                Image(systemName: "plus.magnifyingglass")
                    .font(.title3)
            }
            .disabled(cellSize >= maxCell)
        }
    }
}
