import SwiftUI
import UIKit

struct CameraView: UIViewControllerRepresentable {
    var onCapture: (UIImage) -> Void

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType = .camera
        picker.delegate = context.coordinator
        picker.allowsEditing = false
        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(onCapture: onCapture) }

    final class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let onCapture: (UIImage) -> Void
        init(onCapture: @escaping (UIImage) -> Void) { self.onCapture = onCapture }

        func imagePickerController(
            _ picker: UIImagePickerController,
            didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]
        ) {
            if let image = info[.originalImage] as? UIImage {
                onCapture(image.fixedOrientation())
            }
            picker.dismiss(animated: true)
        }

        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            picker.dismiss(animated: true)
        }
    }
}

extension UIImage {
    func fixedOrientation() -> UIImage {
        guard imageOrientation != .up else { return self }
        UIGraphicsBeginImageContextWithOptions(size, false, scale)
        draw(in: CGRect(origin: .zero, size: size))
        let fixed = UIGraphicsGetImageFromCurrentImageContext()
        UIGraphicsEndImageContext()
        return fixed ?? self
    }
}

struct OnboardingView: View {
    @Environment(\.dismiss) var dismiss
    @State private var page = 0

    // Same four pages as the Android onboarding
    private let pages: [(icon: String, title: String, body: String)] = [
        ("square.grid.2x2.fill", "Design Bead Patterns",
         "Create pixel-art patterns for Perler, Hama, and other fuse beads. Tap to place beads on the grid — it's that simple."),
        ("photo.fill", "Convert Any Photo",
         "Import a photo or snap one with your camera and BeadSnap automatically converts it into a color-quantized bead pattern."),
        ("wand.and.stars", "AI-Powered Generation",
         "Describe what you want and Claude AI will generate a unique bead pattern for you. Bring your ideas to life instantly."),
        ("square.and.arrow.up", "Export & Share",
         "Export your pattern as a PNG image and share with the community or use the shopping list to buy exactly the right beads."),
    ]

    var body: some View {
        VStack {
            TabView(selection: $page) {
                ForEach(Array(pages.enumerated()), id: \.offset) { idx, p in
                    VStack(spacing: 0) {
                        Spacer()
                        ZStack {
                            Circle()
                                .fill(Color.purple.opacity(0.12))
                                .frame(width: 96, height: 96)
                            Image(systemName: p.icon)
                                .font(.system(size: 42))
                                .foregroundStyle(.purple)
                        }
                        Text(p.title)
                            .font(.title.bold())
                            .multilineTextAlignment(.center)
                            .padding(.top, 32)
                        Text(p.body)
                            .font(.body)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                            .padding(.top, 16)
                            .padding(.horizontal, 40)
                        Spacer()
                    }
                    .tag(idx)
                }
            }
            .tabViewStyle(.page(indexDisplayMode: .always))
            .indexViewStyle(.page(backgroundDisplayMode: .always))

            HStack {
                if page > 0 {
                    Button("Back") { withAnimation { page -= 1 } }
                } else {
                    Button("Skip") { dismiss() }
                }
                Spacer()
                if page < pages.count - 1 {
                    Button {
                        withAnimation { page += 1 }
                    } label: {
                        Label("Next", systemImage: "arrow.right")
                            .labelStyle(.titleAndIcon)
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.purple)
                } else {
                    Button {
                        dismiss()
                    } label: {
                        Label("Get Started", systemImage: "checkmark")
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.purple)
                }
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 16)
        }
        .interactiveDismissDisabled(false)
    }
}
