import SwiftUI

struct BeadGridView: View {
    @ObservedObject var viewModel: EditorViewModel
    var isErasing: Bool = false

    @State private var cellSize: CGFloat = 22
    @State private var baseCellSize: CGFloat = 22
    @State private var isPaintMode = true
    @State private var lastPaintedCell: (x: Int, y: Int)? = nil

    private let minCell: CGFloat = 8
    private let maxCell: CGFloat = 44
    private let spacing: CGFloat = 1

    private var step: CGFloat { cellSize + spacing }

    var body: some View {
        VStack(spacing: 0) {
            toolbar.padding(.vertical, 6)
            ScrollView([.horizontal, .vertical], showsIndicators: false) {
                gridContent
                    .padding(8)
                    .gesture(
                        MagnifyGesture()
                            .onChanged { val in
                                let clamped = (baseCellSize * val.magnification)
                                    .clamped(to: minCell...maxCell)
                                cellSize = clamped
                            }
                            .onEnded { val in
                                baseCellSize = (baseCellSize * val.magnification)
                                    .clamped(to: minCell...maxCell)
                                cellSize = baseCellSize
                            }
                    )
            }
            .scrollDisabled(isPaintMode)
        }
    }

    // MARK: - Grid

    private var gridContent: some View {
        let cols = viewModel.pattern.grid.width
        let rows = viewModel.pattern.grid.height

        return ZStack(alignment: .topLeading) {
            LazyVGrid(
                columns: Array(repeating: GridItem(.fixed(cellSize), spacing: spacing), count: cols),
                spacing: spacing
            ) {
                ForEach(0..<(cols * rows), id: \.self) { idx in
                    let x = idx % cols
                    let y = idx / cols
                    BeadCellView(
                        color: viewModel.color(at: x, y: y)?.swiftUIColor,
                        size: cellSize
                    )
                    .equatable()
                    .frame(width: cellSize, height: cellSize)
                }
            }

            if isPaintMode {
                Color.clear
                    .frame(
                        width: CGFloat(cols) * step,
                        height: CGFloat(rows) * step
                    )
                    .contentShape(Rectangle())
                    .gesture(
                        DragGesture(minimumDistance: 0, coordinateSpace: .local)
                            .onChanged { value in
                                let x = Int(value.location.x / step)
                                let y = Int(value.location.y / step)
                                guard x >= 0, x < cols, y >= 0, y < rows else { return }
                                guard lastPaintedCell?.x != x || lastPaintedCell?.y != y else { return }
                                lastPaintedCell = (x, y)
                                if isErasing {
                                    viewModel.clearCell(x: x, y: y)
                                } else {
                                    viewModel.tapCell(x: x, y: y)
                                }
                            }
                            .onEnded { _ in lastPaintedCell = nil }
                    )
            }
        }
    }

    // MARK: - Toolbar

    private var toolbar: some View {
        HStack(spacing: 20) {
            Button {
                cellSize = max(minCell, cellSize - 4)
                baseCellSize = cellSize
            } label: {
                Image(systemName: "minus.magnifyingglass").font(.title3)
            }
            .disabled(cellSize <= minCell)

            Text("\(Int(cellSize))px")
                .font(.caption)
                .monospacedDigit()
                .foregroundStyle(.secondary)

            Button {
                cellSize = min(maxCell, cellSize + 4)
                baseCellSize = cellSize
            } label: {
                Image(systemName: "plus.magnifyingglass").font(.title3)
            }
            .disabled(cellSize >= maxCell)

            Spacer()

            Button {
                isPaintMode.toggle()
            } label: {
                Label(
                    isPaintMode ? "Painting" : "Scrolling",
                    systemImage: isPaintMode ? "pencil.tip" : "hand.point.up"
                )
                .font(.caption.bold())
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(isPaintMode ? Color.purple.opacity(0.12) : Color(.secondarySystemBackground))
                .clipShape(Capsule())
            }
            .padding(.trailing, 8)
        }
        .padding(.horizontal, 12)
    }
}

private extension Comparable {
    func clamped(to range: ClosedRange<Self>) -> Self {
        min(max(self, range.lowerBound), range.upperBound)
    }
}
