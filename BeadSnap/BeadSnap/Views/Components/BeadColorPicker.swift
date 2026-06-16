import SwiftUI

struct BeadColorPicker: View {
    @Binding var selectedColor: BeadColor
    var onClear: (() -> Void)?

    private let columns = Array(repeating: GridItem(.flexible(), spacing: 6), count: 8)

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Bead Color")
                    .font(.headline)
                Spacer()
                if let onClear = onClear {
                    Button(action: onClear) {
                        Label("Erase", systemImage: "xmark.circle")
                            .font(.subheadline)
                            .foregroundColor(.red)
                    }
                }
            }
            .padding(.horizontal)

            LazyVGrid(columns: columns, spacing: 6) {
                ForEach(BeadColor.palette) { color in
                    BeadColorCell(color: color, isSelected: color.id == selectedColor.id)
                        .onTapGesture { selectedColor = color }
                }
            }
            .padding(.horizontal)
        }
        .padding(.vertical, 12)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
    }
}

struct BeadColorCell: View {
    let color: BeadColor
    let isSelected: Bool

    var body: some View {
        ZStack {
            Circle()
                .fill(color.swiftUIColor)
                .shadow(color: .black.opacity(0.2), radius: 2, x: 0, y: 1)
            if isSelected {
                Circle()
                    .strokeBorder(Color.white, lineWidth: 2)
                Circle()
                    .strokeBorder(Color.black.opacity(0.5), lineWidth: 3.5)
            }
        }
        .frame(width: 36, height: 36)
        .scaleEffect(isSelected ? 1.15 : 1)
        .animation(.spring(response: 0.2), value: isSelected)
        .accessibilityLabel(color.name)
    }
}
