import SwiftUI

struct BeadCellView: View, Equatable {
    let color: Color?
    let size: CGFloat

    static func == (lhs: BeadCellView, rhs: BeadCellView) -> Bool {
        lhs.color == rhs.color && lhs.size == rhs.size
    }

    var body: some View {
        // Bead fills the whole cell so, with zero grid spacing, fused beads
        // touch their neighbors (diameter == cell pitch).
        Circle()
            .fill(color ?? Color(.systemGray5))
            .frame(width: size, height: size)
            .overlay(
                // Faint center hole gives filled beads the fused-bead look.
                Circle()
                    .fill(Color.white.opacity(color == nil ? 0 : 0.11))
                    .frame(width: size * 0.34, height: size * 0.34)
            )
            .overlay(
                Circle()
                    .strokeBorder(Color.black.opacity(color == nil ? 0.06 : 0.12),
                                  lineWidth: max(0.5, size * 0.05))
            )
    }
}
