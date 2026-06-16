import SwiftUI
import PhotosUI

struct HomeView: View {
    @StateObject private var vm = HomeViewModel()
    @State private var showOnboarding = false

    var body: some View {
        NavigationStack {
            ZStack {
                backgroundGradient

                ScrollView {
                    VStack(spacing: 32) {
                        headerSection
                        photoSourceButtons
                        recentTipCard
                    }
                    .padding(.horizontal, 24)
                    .padding(.top, 16)
                    .padding(.bottom, 40)
                }
            }
            .navigationTitle("")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    logoHeader
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showOnboarding = true
                    } label: {
                        Image(systemName: "questionmark.circle.fill")
                            .foregroundColor(.blue)
                            .font(.title3)
                    }
                }
            }
            .sheet(isPresented: $vm.isShowingCamera) {
                CameraView { image in
                    vm.handleCameraImage(image)
                    vm.isShowingCamera = false
                }
            }
            .photosPicker(
                isPresented: $vm.isShowingPhotoPicker,
                selection: $vm.photosPickerItem,
                matching: .images
            )
            .onChange(of: vm.photosPickerItem) { item in
                Task { await vm.handlePickedPhoto(item) }
            }
            .navigationDestination(isPresented: $vm.isShowingBackgroundRemoval) {
                if let image = vm.selectedImage {
                    BackgroundRemovalView(image: image) {
                        vm.reset()
                    }
                }
            }
            .sheet(isPresented: $showOnboarding) {
                OnboardingView()
            }
        }
    }

    private var backgroundGradient: some View {
        LinearGradient(
            colors: [
                Color(red: 1.0, green: 0.95, blue: 0.85),
                Color(red: 0.95, green: 0.85, blue: 1.0)
            ],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()
    }

    private var logoHeader: some View {
        HStack(spacing: 6) {
            Image(systemName: "circle.grid.3x3.fill")
                .foregroundStyle(
                    LinearGradient(
                        colors: [.orange, .pink, .purple],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .font(.title2)
            Text("BeadSnap")
                .font(.title2.bold())
                .foregroundStyle(
                    LinearGradient(
                        colors: [.orange, .purple],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
        }
    }

    private var headerSection: some View {
        VStack(spacing: 12) {
            Image(systemName: "camera.fill")
                .font(.system(size: 70))
                .foregroundStyle(
                    LinearGradient(
                        colors: [.orange, .pink],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .symbolEffect(.bounce, options: .speed(0.5))

            Text("Turn Any Photo Into\nFuse Bead Art!")
                .font(.system(size: 26, weight: .bold, design: .rounded))
                .multilineTextAlignment(.center)
                .foregroundColor(.primary)

            Text("Take a photo or pick one from your library")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding(.top, 16)
    }

    private var photoSourceButtons: some View {
        VStack(spacing: 16) {
            Button {
                vm.isShowingCamera = true
            } label: {
                sourceButtonLabel(
                    icon: "camera.fill",
                    title: "Take a Photo",
                    subtitle: "Use your camera",
                    color: .orange
                )
            }
            .buttonStyle(.plain)

            Button {
                vm.isShowingPhotoPicker = true
            } label: {
                sourceButtonLabel(
                    icon: "photo.fill",
                    title: "Choose from Library",
                    subtitle: "Pick an existing photo",
                    color: .purple
                )
            }
            .buttonStyle(.plain)
        }
    }

    private func sourceButtonLabel(
        icon: String,
        title: String,
        subtitle: String,
        color: Color
    ) -> some View {
        HStack(spacing: 18) {
            ZStack {
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(color.opacity(0.15))
                    .frame(width: 60, height: 60)
                Image(systemName: icon)
                    .font(.system(size: 26, weight: .medium))
                    .foregroundColor(color)
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.headline)
                    .foregroundColor(.primary)
                Text(subtitle)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }

            Spacer()

            Image(systemName: "chevron.right")
                .foregroundColor(.secondary)
                .font(.body.bold())
        }
        .padding(18)
        .background(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(.white)
                .shadow(color: .black.opacity(0.06), radius: 8, x: 0, y: 4)
        )
    }

    private var recentTipCard: some View {
        HStack(spacing: 12) {
            Text("💡")
                .font(.title2)
            VStack(alignment: .leading, spacing: 2) {
                Text("Pro Tip")
                    .font(.caption.bold())
                    .foregroundColor(.orange)
                Text("Photos with simple shapes and bold colors make the best bead patterns!")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(Color.orange.opacity(0.08))
                .overlay(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .strokeBorder(Color.orange.opacity(0.2), lineWidth: 1)
                )
        )
    }
}
