import SwiftUI

struct KidButton: View {
    let title: String
    let icon: String
    var color: Color = .blue
    var size: ButtonSize = .regular
    var action: () -> Void

    enum ButtonSize {
        case small, regular, large
        var font: Font {
            switch self {
            case .small: return .subheadline.bold()
            case .regular: return .title3.bold()
            case .large: return .title.bold()
            }
        }
        var padding: CGFloat {
            switch self {
            case .small: return 10
            case .regular: return 16
            case .large: return 22
            }
        }
        var iconSize: CGFloat {
            switch self {
            case .small: return 18
            case .regular: return 26
            case .large: return 36
            }
        }
    }

    @State private var isPressed = false

    var body: some View {
        Button(action: {
            withAnimation(.spring(response: 0.15, dampingFraction: 0.5)) { isPressed = true }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                withAnimation { isPressed = false }
            }
            action()
        }) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: size.iconSize, weight: .bold))
                Text(title)
                    .font(size.font)
            }
            .foregroundColor(.white)
            .padding(size.padding)
            .background(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .fill(color.gradient)
                    .shadow(color: color.opacity(0.4), radius: 6, x: 0, y: 4)
            )
            .scaleEffect(isPressed ? 0.92 : 1)
        }
        .buttonStyle(.plain)
    }
}
