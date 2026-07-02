import SwiftUI

struct BeadCellView: View, Equatable {
    let color: Color?
    let size: CGFloat

    static func == (lhs: BeadCellView, rhs: BeadCellView) -> Bool {
        lhs.color == rhs.color && lhs.size == rhs.size
    }

    var body: some View {
        Circle()
            .fill(color ?? Color(.systemGray5))
            .frame(width: size * 0.88, height: size * 0.88)
            .overlay(
                Circle()
                    .strokeBorder(Color.black.opacity(color == nil ? 0.06 : 0.15), lineWidth: 0.5)
            )
    }
}
