import SwiftUI

struct DrawView: View {
    @StateObject private var vm = DrawViewModel()
    @State private var navigateToPattern = false
    @State private var drawnImage: UIImage?

    var body: some View {
        NavigationStack {
            ZStack {
                Color(.systemGroupedBackground).ignoresSafeArea()

                VStack(spacing: 0) {
                    drawingCanvas
                    toolbarPanel
                }
            }
            .navigationTitle("Draw")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Convert to Beads") {
                        convertToPattern()
                    }
                    .font(.headline)
                    .foregroundColor(.purple)
                    .disabled(vm.strokes.isEmpty)
                }
            }
            .navigationDestination(isPresented: $navigateToPattern) {
                if let img = drawnImage {
                    PatternView(image: img, originalImage: img)
                }
            }
        }
    }

    private var drawingCanvas: some View {
        GeometryReader { geo in
            ZStack {
                // White drawing surface
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .fill(Color.white)
                    .shadow(color: .black.opacity(0.08), radius: 8, x: 0, y: 4)
                    .padding(16)

                // Dot grid hint
                Canvas { context, size in
                    let spacing: CGFloat = 24
                    let color = Color.gray.opacity(0.2)
                    var x: CGFloat = 32
                    while x < size.width - 16 {
                        var y: CGFloat = 32
                        while y < size.height - 16 {
                            context.fill(
                                Path(ellipseIn: CGRect(x: x - 1, y: y - 1, width: 2, height: 2)),
                                with: .color(color)
                            )
                            y += spacing
                        }
                        x += spacing
                    }
                }

                // Drawn strokes
                Canvas { context, _ in
                    for stroke in vm.strokes {
                        drawCanvasStroke(stroke, in: &context)
                    }
                    if let current = vm.currentStroke {
                        drawCanvasStroke(current, in: &context)
                    }
                }
                .padding(16)
            }
            .contentShape(Rectangle())
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { val in
                        if val.startLocation == val.location {
                            vm.beginDraw(at: val.location)
                        } else {
                            vm.continueDraw(to: val.location)
                        }
                    }
                    .onEnded { _ in
                        vm.canvasSize = geo.size
                        vm.endDraw()
                    }
            )
            .onAppear { vm.canvasSize = geo.size }
        }
    }

    private func drawCanvasStroke(_ stroke: DrawStroke, in context: inout GraphicsContext) {
        guard stroke.points.count >= 2 else {
            if let pt = stroke.points.first {
                let r = CGRect(
                    x: pt.x - stroke.width / 2,
                    y: pt.y - stroke.width / 2,
                    width: stroke.width,
                    height: stroke.width
                )
                context.fill(Path(ellipseIn: r), with: .color(stroke.color))
            }
            return
        }
        var path = Path()
        path.move(to: stroke.points[0])
        for pt in stroke.points.dropFirst() {
            path.addLine(to: pt)
        }
        context.stroke(path, with: .color(stroke.color), style: StrokeStyle(
            lineWidth: stroke.width,
            lineCap: .round,
            lineJoin: .round
        ))
    }

    private var toolbarPanel: some View {
        VStack(spacing: 0) {
            Divider()
            HStack(spacing: 0) {
                // Color picker
                colorPaletteRow

                Divider()
                    .frame(height: 44)
                    .padding(.horizontal, 8)

                // Brush size
                HStack(spacing: 6) {
                    Image(systemName: "circle.fill")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    Slider(value: $vm.brushWidth, in: 4...40)
                        .frame(width: 80)
                    Image(systemName: "circle.fill")
                        .foregroundColor(.secondary)
                }

                Divider()
                    .frame(height: 44)
                    .padding(.horizontal, 8)

                // Eraser
                Button {
                    vm.isEraser.toggle()
                } label: {
                    Image(systemName: vm.isEraser ? "eraser.fill" : "eraser")
                        .font(.title2)
                        .foregroundColor(vm.isEraser ? .red : .secondary)
                }
                .frame(width: 44)

                // Undo
                Button { vm.undo() } label: {
                    Image(systemName: "arrow.uturn.backward")
                        .font(.title2)
                        .foregroundColor(.blue)
                }
                .frame(width: 44)
                .disabled(vm.undoStack.isEmpty)

                // Clear
                Button { vm.clearAll() } label: {
                    Image(systemName: "trash")
                        .font(.title2)
                        .foregroundColor(.red)
                }
                .frame(width: 44)
                .disabled(vm.strokes.isEmpty)
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 10)
            .background(.regularMaterial)
        }
    }

    private var colorPaletteRow: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(BeadColor.palette.prefix(20)) { bead in
                    Button {
                        vm.selectBeadColor(bead)
                    } label: {
                        Circle()
                            .fill(bead.swiftUIColor)
                            .frame(width: 30, height: 30)
                            .overlay(
                                Circle()
                                    .strokeBorder(
                                        vm.selectedColorID == bead.id ? Color.black : Color.clear,
                                        lineWidth: 2
                                    )
                            )
                            .shadow(radius: 1)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 4)
        }
    }

    private func convertToPattern() {
        guard let img = vm.rasterize(size: vm.canvasSize) else { return }

        let persistence = PersistenceService.shared
        let filename = persistence.uniqueImageFilename(ext: "png")
        persistence.saveImage(img, filename: filename)
        var project = Project(name: "Drawing \(drawingDateString())", sourceType: .drawing, originalImageFilename: filename)
        if let thumb = img.jpegData(compressionQuality: 0.7) {
            project.thumbnail = thumb
        }
        persistence.saveProject(project)

        drawnImage = img
        navigateToPattern = true
    }

    private func drawingDateString() -> String {
        let f = DateFormatter()
        f.dateStyle = .short
        f.timeStyle = .short
        return f.string(from: Date())
    }
}
