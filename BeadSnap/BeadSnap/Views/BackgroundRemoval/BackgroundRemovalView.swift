import SwiftUI

struct BackgroundRemovalView: View {
    let image: UIImage
    var onDismiss: () -> Void

    @StateObject private var vm: BackgroundRemovalViewModel
    @State private var navigateToPattern = false
    @State private var showBrushPanel = false
    @State private var createdProject: Project?

    private let persistence = PersistenceService.shared

    init(image: UIImage, onDismiss: @escaping () -> Void) {
        self.image = image
        self.onDismiss = onDismiss
        self._vm = StateObject(wrappedValue: BackgroundRemovalViewModel(image: image))
    }

    private func createProjectAndProceed() {
        let originalFilename = persistence.uniqueImageFilename()
        persistence.saveImage(image, filename: originalFilename)

        var project = Project(
            name: "Pattern \(projectDateString())",
            sourceType: .photo,
            originalImageFilename: originalFilename
        )

        if vm.maskedImage != nil {
            let maskedFilename = persistence.uniqueImageFilename()
            persistence.saveImage(vm.imageForPatternConversion, filename: maskedFilename)
            project.maskedImageFilename = maskedFilename
        }

        // Small thumbnail for gallery
        if let thumb = thumbnailData(from: image) {
            project.thumbnail = thumb
        }

        persistence.saveProject(project)
        createdProject = project
        navigateToPattern = true
    }

    private func projectDateString() -> String {
        let f = DateFormatter()
        f.dateStyle = .short
        f.timeStyle = .short
        return f.string(from: Date())
    }

    private func thumbnailData(from image: UIImage) -> Data? {
        let size = CGSize(width: 200, height: 200)
        UIGraphicsBeginImageContextWithOptions(size, false, 1)
        image.draw(in: CGRect(origin: .zero, size: size))
        let thumb = UIGraphicsGetImageFromCurrentImageContext()
        UIGraphicsEndImageContext()
        return thumb?.jpegData(compressionQuality: 0.7)
    }

    var body: some View {
        ZStack {
            Color(.systemGroupedBackground).ignoresSafeArea()

            VStack(spacing: 0) {
                // Main image canvas
                imageCanvas
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

                // Bottom controls
                bottomControls
            }
        }
        .navigationTitle("Remove Background")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button("Next") {
                    createProjectAndProceed()
                }
                .font(.headline)
                .disabled(vm.isProcessing)
            }
        }
        .task {
            await vm.autoRemoveBackground()
        }
        .navigationDestination(isPresented: $navigateToPattern) {
            if let project = createdProject {
                PatternView(
                    image: vm.imageForPatternConversion,
                    originalImage: image,
                    project: project
                )
            }
        }
    }

    private var imageCanvas: some View {
        GeometryReader { geo in
            ZStack {
                // Checkerboard background (transparency indicator)
                CheckerboardView()
                    .clipShape(RoundedRectangle(cornerRadius: 12))

                // Displayed image
                if let masked = vm.maskedImage {
                    Image(uiImage: masked)
                        .resizable()
                        .scaledToFit()
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                } else {
                    Image(uiImage: vm.originalImage)
                        .resizable()
                        .scaledToFit()
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                }

                // Loading overlay
                if vm.isProcessing {
                    ZStack {
                        RoundedRectangle(cornerRadius: 12)
                            .fill(.ultraThinMaterial)
                        VStack(spacing: 12) {
                            ProgressView()
                                .scaleEffect(1.5)
                            Text("Removing background...")
                                .font(.headline)
                        }
                    }
                }

                // Brush drawing layer
                if showBrushPanel {
                    MaskPaintCanvas(vm: vm, size: geo.size)
                }
            }
            .padding(16)
        }
    }

    private var bottomControls: some View {
        VStack(spacing: 0) {
            Divider()

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    // Auto remove
                    ControlButton(
                        icon: "wand.and.stars",
                        label: "Auto Remove",
                        color: .purple
                    ) {
                        Task { await vm.autoRemoveBackground() }
                    }

                    Divider().frame(height: 44)

                    // Brush mode toggle
                    ControlButton(
                        icon: "paintbrush.fill",
                        label: "Keep",
                        color: .green,
                        isActive: showBrushPanel && vm.brushMode == .include
                    ) {
                        vm.brushMode = .include
                        showBrushPanel = true
                    }

                    ControlButton(
                        icon: "eraser.fill",
                        label: "Remove",
                        color: .red,
                        isActive: showBrushPanel && vm.brushMode == .exclude
                    ) {
                        vm.brushMode = .exclude
                        showBrushPanel = true
                    }

                    // Brush size slider
                    if showBrushPanel {
                        HStack(spacing: 6) {
                            Image(systemName: "circle.fill")
                                .font(.caption2)
                                .foregroundColor(.secondary)
                            Slider(value: $vm.brushSize, in: 8...60)
                                .frame(width: 100)
                            Image(systemName: "circle.fill")
                                .font(.body)
                                .foregroundColor(.secondary)
                        }
                    }

                    Divider().frame(height: 44)

                    // Undo
                    ControlButton(icon: "arrow.uturn.backward", label: "Undo", color: .blue) {
                        vm.undoLastStroke()
                    }

                    // Reset
                    ControlButton(icon: "arrow.counterclockwise", label: "Reset", color: .orange) {
                        vm.resetMask()
                        showBrushPanel = false
                        Task { await vm.autoRemoveBackground() }
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
            }

            if let error = vm.errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundColor(.orange)
                    .padding(.horizontal)
                    .padding(.bottom, 8)
            }
        }
        .background(.regularMaterial)
    }
}

struct ControlButton: View {
    let icon: String
    let label: String
    var color: Color = .blue
    var isActive: Bool = false
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                ZStack {
                    RoundedRectangle(cornerRadius: 10)
                        .fill(isActive ? color : color.opacity(0.12))
                        .frame(width: 44, height: 44)
                    Image(systemName: icon)
                        .font(.system(size: 18, weight: .medium))
                        .foregroundColor(isActive ? .white : color)
                }
                Text(label)
                    .font(.caption2.bold())
                    .foregroundColor(isActive ? color : .secondary)
            }
        }
        .buttonStyle(.plain)
    }
}

struct MaskPaintCanvas: View {
    @ObservedObject var vm: BackgroundRemovalViewModel
    let size: CGSize

    var body: some View {
        Canvas { context, _ in
            for stroke in vm.includeStrokes {
                drawStroke(stroke, in: &context, color: .green)
            }
            for stroke in vm.excludeStrokes {
                drawStroke(stroke, in: &context, color: .red)
            }
            if let current = vm.currentStroke {
                let strokeColor: Color = vm.brushMode == .include ? .green : .red
                drawStroke(current, in: &context, color: strokeColor)
            }
        }
        .opacity(0.5)
        .gesture(
            DragGesture(minimumDistance: 0)
                .onChanged { val in
                    if val.startLocation == val.location {
                        vm.beginStroke(at: val.location)
                    } else {
                        vm.continueStroke(to: val.location)
                    }
                }
                .onEnded { _ in vm.endStroke() }
        )
    }

    private func drawStroke(_ stroke: MaskStroke, in context: inout GraphicsContext, color: Color) {
        guard stroke.points.count >= 2 else {
            if let pt = stroke.points.first {
                let r = CGRect(
                    x: pt.x - stroke.brushSize / 2,
                    y: pt.y - stroke.brushSize / 2,
                    width: stroke.brushSize,
                    height: stroke.brushSize
                )
                context.fill(Path(ellipseIn: r), with: .color(color))
            }
            return
        }
        var path = Path()
        path.move(to: stroke.points[0])
        for pt in stroke.points.dropFirst() {
            path.addLine(to: pt)
        }
        context.stroke(path, with: .color(color), style: StrokeStyle(
            lineWidth: stroke.brushSize,
            lineCap: .round,
            lineJoin: .round
        ))
    }
}

struct CheckerboardView: View {
    let tileSize: CGFloat = 12

    var body: some View {
        Canvas { context, size in
            let cols = Int(ceil(size.width / tileSize))
            let rows = Int(ceil(size.height / tileSize))
            for row in 0..<rows {
                for col in 0..<cols {
                    let isLight = (row + col) % 2 == 0
                    let color: Color = isLight ? Color(white: 0.9) : Color(white: 0.75)
                    let rect = CGRect(
                        x: CGFloat(col) * tileSize,
                        y: CGFloat(row) * tileSize,
                        width: tileSize,
                        height: tileSize
                    )
                    context.fill(Path(rect), with: .color(color))
                }
            }
        }
    }
}
