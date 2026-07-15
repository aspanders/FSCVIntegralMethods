import SwiftUI

struct PalettePickerView: View {
    @ObservedObject var viewModel: EditorViewModel

    var body: some View {
        VStack(spacing: 4) {
            // Selected color name label
            Text(viewModel.selectedColor.name)
                .font(.caption)
                .foregroundStyle(.secondary)
                .frame(height: 14)
                .animation(.none, value: viewModel.selectedColor.id)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    ForEach(viewModel.pattern.palette) { color in
                        colorSwatch(color)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
            }
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
                    .frame(width: 36, height: 36)
                Circle()
                    .strokeBorder(
                        isSelected ? Color.primary : Color.black.opacity(0.18),
                        lineWidth: isSelected ? 3 : 1
                    )
                    .frame(width: 36, height: 36)
                if isSelected {
                    Image(systemName: "checkmark")
                        .font(.caption2.bold())
                        .foregroundStyle(color.swiftUIColor.isDark ? .white : .black)
                }
            }
        }
        .buttonStyle(.plain)
        .accessibilityLabel(color.name)
        .accessibilityAddTraits(isSelected ? .isSelected : [])
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
