import SwiftUI

struct PalettePickerView: View {
    @ObservedObject var viewModel: EditorViewModel

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(viewModel.pattern.palette) { color in
                    colorSwatch(color)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
        }
        .background(.ultraThinMaterial)
    }

    private func colorSwatch(_ color: PaletteColor) -> some View {
        let isSelected = viewModel.selectedColor.id == color.id
        return Button {
            viewModel.selectedColor = color
        } label: {
            ZStack {
                Circle()
                    .fill(color.swiftUIColor)
                    .frame(
                        width: isSelected ? 42 : 32,
                        height: isSelected ? 42 : 32
                    )
                Circle()
                    .strokeBorder(
                        isSelected ? Color.primary : Color.black.opacity(0.18),
                        lineWidth: isSelected ? 3 : 1
                    )
                    .frame(
                        width: isSelected ? 42 : 32,
                        height: isSelected ? 42 : 32
                    )
                if isSelected {
                    Image(systemName: "checkmark")
                        .font(.caption2.bold())
                        .foregroundStyle(color.swiftUIColor.isDark ? .white : .black)
                }
            }
            .animation(.spring(response: 0.2, dampingFraction: 0.7), value: isSelected)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Color brightness helper

private extension Color {
    var isDark: Bool {
        var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
        UIColor(self).getRed(&r, green: &g, blue: &b, alpha: &a)
        return (0.299 * r + 0.587 * g + 0.114 * b) < 0.5
    }
}
