import SwiftUI
import PhotosUI

@MainActor
final class HomeViewModel: ObservableObject {
    @Published var selectedImage: UIImage?
    @Published var isShowingCamera = false
    @Published var isShowingPhotoPicker = false
    @Published var isShowingBackgroundRemoval = false
    @Published var photosPickerItem: PhotosPickerItem?

    func handlePickedPhoto(_ item: PhotosPickerItem?) async {
        guard let item else { return }
        if let data = try? await item.loadTransferable(type: Data.self),
           let image = UIImage(data: data) {
            selectedImage = image
            isShowingBackgroundRemoval = true
        }
    }

    func handleCameraImage(_ image: UIImage) {
        selectedImage = image
        isShowingBackgroundRemoval = true
    }

    func reset() {
        selectedImage = nil
        photosPickerItem = nil
    }
}
