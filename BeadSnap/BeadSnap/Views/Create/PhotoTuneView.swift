import SwiftUI
import UIKit

/// The photo studio: the photograph and the bead pattern it currently produces,
/// on screen together, with every control that connects them live.
///
/// The photo sits above the beads in portrait and beside them in landscape, both
/// showing the same crop, so a stroke of the brush and the beads it changes are
/// a glance apart. Painting the mask, moving white balance and changing the
/// board all redraw the pattern immediately rather than on a "convert" button.
///
/// Why the studio is needed at all: on a real test photo the wooden background
/// took 74% of the beads and 7 of the 12 colours, and the blue subject came out
/// grey because the camera's white balance had crushed the blue channel. Neither
/// is visible until you see the beads, and neither is fixable without seeing the
/// photo at the same time.
///
/// The iOS counterpart of Android's `PhotoTuneScreen`. It is deliberately not a
/// line-by-line transliteration - the state lives in an `@StateObject` model
/// rather than in the view, which is what keeps it alive across the rotation
/// that swaps the portrait and landscape arrangements.
struct PhotoTuneView: View {
    let source: UIImage
    var autoSegment: Bool = true
    var onCancel: () -> Void
    var onDone: (FusePattern, GridSize, Int, UIImage?) -> Void

    @StateObject private var model = PhotoTuneModel()
    @Environment(\.horizontalSizeClass) private var sizeClass

    var body: some View {
        GeometryReader { geo in
            let landscape = geo.size.width > geo.size.height
            VStack(spacing: 0) {
                header
                Divider()
                if landscape {
                    HStack(spacing: 0) {
                        photoPane
                        Divider()
                        beadPane
                    }
                } else {
                    VStack(spacing: 0) {
                        photoPane
                        Divider()
                        beadPane
                    }
                }
                Divider()
                controls
            }
            .overlay { if model.busy { busyOverlay } }
        }
        .task { await model.start(source: source, autoSegment: autoSegment) }
        .alert("Something went wrong", isPresented: .constant(model.failure != nil)) {
            Button("OK") { model.failure = nil }
        } message: {
            Text(model.failure ?? "")
        }
    }

    // MARK: - Panes

    private var header: some View {
        HStack {
            Button("Cancel", action: onCancel)
            Spacer()
            Text("Tune photo").font(.headline)
            Spacer()
            Button("Done") {
                guard let pattern = model.pattern else { return }
                onDone(pattern, model.gridSize, model.maxColors, model.cutoutImage(from: source))
            }
            .disabled(model.pattern == nil || model.busy)
            .fontWeight(.semibold)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
    }

    /// The photo, with a drag that paints the keep-mask.
    ///
    /// The gesture is attached with `minimumDistance: 0` so a tap paints too,
    /// and the mapping from a touch to a photo coordinate is recomputed on every
    /// event from the CURRENT layout - never captured once - because the preview
    /// image is replaced on every rebuild and a captured frame would go stale
    /// mid-stroke.
    private var photoPane: some View {
        GeometryReader { geo in
            ZStack {
                Color(.secondarySystemBackground)
                if let preview = model.preview {
                    Image(uiImage: preview)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                }
            }
            .contentShape(Rectangle())
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { value in
                        // The crop overlay sits on top and takes these touches,
                        // but this guard is what actually guarantees the brush
                        // stays out of it. On Android, covering the pane was NOT
                        // enough - an unconsumed tap fell through to the brush
                        // and silently edited the cut-out mask. Not relying on
                        // hit-testing to be on my side twice.
                        guard model.tab != .crop else { return }
                        paint(at: value.location, in: geo.size)
                    }
            )
            .overlay {
                if model.tab == .crop {
                    CropOverlay(model: model, box: geo.size)
                }
            }
            .accessibilityLabel("Photo. Drag to include or exclude parts of it")
        }
    }

    /// Maps a touch inside the pane to 0..1 across the photo, allowing for the
    /// letterboxing that `.fit` introduces.
    private func paint(at point: CGPoint, in box: CGSize) {
        guard let preview = model.preview, box.width > 0, box.height > 0 else { return }
        let scale = min(box.width / preview.size.width, box.height / preview.size.height)
        let drawW = preview.size.width * scale
        let drawH = preview.size.height * scale
        let left = (box.width - drawW) / 2
        let top = (box.height - drawH) / 2
        let u = (point.x - left) / drawW
        let v = (point.y - top) / drawH
        guard (0...1).contains(u), (0...1).contains(v) else { return }
        model.paint(nx: Double(u), ny: Double(v))
    }

    private var beadPane: some View {
        ZStack {
            Color(.systemBackground)
            if let pattern = model.pattern {
                Image(uiImage: ImageConverter.renderToImage(pattern: pattern, cellSize: 10))
                    .resizable()
                    .interpolation(.none)
                    .aspectRatio(contentMode: .fit)
                    .padding(8)
            } else {
                ProgressView()
            }
        }
    }

    private var busyOverlay: some View {
        ZStack {
            Color.black.opacity(0.12)
            ProgressView()
        }
        .allowsHitTesting(false)
    }

    // MARK: - Controls

    private var controls: some View {
        VStack(spacing: 10) {
            Picker("", selection: $model.tab) {
                ForEach(PhotoTuneModel.Tab.allCases) { t in Text(t.label).tag(t) }
            }
            .pickerStyle(.segmented)
            .padding(.horizontal, 16)

            // The tab's own controls scroll; the tab picker above does not.
            //
            // The picker is deliberately OUTSIDE this scroll view. On Android
            // the equivalent tab strip lived inside the scrolling area, so
            // scrolling a tall tab carried the tabs themselves off the top and
            // the board size looked as though it had been removed. Keeping the
            // picker pinned is what stops that happening here.
            //
            // maxHeight bounds the panel so the photo and bead panes above keep
            // their space; anything taller than that scrolls rather than being
            // clipped, which matters at large Dynamic Type sizes.
            ScrollView {
                Group {
                    switch model.tab {
                    case .cutOut: cutOutControls
                    case .crop:   cropControls
                    case .colour: colourControls
                    case .board:  boardControls
                    }
                }
                .padding(.horizontal, 16)
            }
            .frame(maxHeight: 215)
            // A fresh scroll view per tab, so every tab opens at its own top.
            // One shared scroll view keeps its offset across a tab change, and
            // arriving at a short tab already scrolled past its first control
            // is precisely how board size came to look missing on Android.
            .id(model.tab)
        }
        .padding(.vertical, 10)
    }

    private var cutOutControls: some View {
        VStack(spacing: 8) {
            HStack {
                Picker("", selection: $model.brushRestores) {
                    Text("Erase").tag(false)
                    Text("Restore").tag(true)
                }
                .pickerStyle(.segmented)
                .frame(maxWidth: 220)
                Spacer()
                Button("Keep all") { model.keepAll() }
                Button("Auto") { Task { await model.autoCutOut(source: source) } }
                    .disabled(model.autoRunning)
            }
            HStack {
                Text("Brush").font(.caption)
                Slider(value: $model.brushSize, in: 0.02...0.20)
            }
            if model.autoUnavailable {
                Text("Automatic selection didn't find a subject on this device.")
                    .font(.caption).foregroundStyle(.secondary)
            }
        }
    }

    private var cropControls: some View {
        VStack(spacing: 8) {
            Text("Drag the box to choose what goes on the board, and pinch to "
                 + "resize it. The box is locked to the board's shape, so the "
                 + "picture cannot come out stretched.")
                .font(.caption)
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
            HStack(spacing: 12) {
                Button("Automatic") { model.resetCrop() }
                    .disabled(model.userCrop == nil)
                Button("As much as fits") { model.cropWholePhoto() }
                Spacer()
            }
            Text(model.userCrop == nil
                 ? "Automatic: the largest centred square of the photo."
                 : "Using your crop. Automatic puts it back.")
                .font(.caption2)
                .foregroundStyle(model.userCrop == nil ? .secondary : .primary)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var colourControls: some View {
        VStack(spacing: 6) {
            labelled("Colours", value: "\(model.maxColors)") {
                Slider(value: Binding(
                    get: { Double(model.maxColors) },
                    set: { model.setMaxColors(Int($0.rounded())) }
                ), in: 2...24, step: 1)
            }
            labelled("White balance", value: model.wbStrength > 0 ? "on" : "off") {
                Slider(value: Binding(
                    get: { model.wbStrength },
                    set: { model.setWhiteBalance($0) }
                ), in: 0...1)
            }
        }
    }

    private var boardControls: some View {
        VStack(spacing: 8) {
            Picker("", selection: Binding(
                get: { model.gridSize },
                set: { model.setGrid($0) }
            )) {
                Text("16×16").tag(GridSize.small)
                Text("24×24").tag(GridSize.medium)
                Text("32×32").tag(GridSize.large)
                Text("48×48").tag(GridSize.xlarge)
            }
            .pickerStyle(.segmented)

            Picker("", selection: Binding(
                get: { model.shape },
                set: { model.setShape($0) }
            )) {
                Text("Square").tag(PegboardShape.square)
                Text("Circle").tag(PegboardShape.circle)
            }
            .pickerStyle(.segmented)
        }
    }

    private func labelled<C: View>(_ title: String, value: String,
                                   @ViewBuilder content: () -> C) -> some View {
        HStack {
            Text(title).font(.caption).frame(width: 96, alignment: .leading)
            content()
            Text(value).font(.caption.monospacedDigit())
                .frame(width: 40, alignment: .trailing)
        }
    }
}

/// All the studio's mutable state, deliberately outside the view.
///
/// The portrait and landscape arrangements are separate call sites, so state
/// held inside a pane would be thrown away on every rotation - the same trap
/// that made the Android editor go blank before it was restructured.
@MainActor
final class PhotoTuneModel: ObservableObject {

    enum Tab: String, CaseIterable, Identifiable {
        case cutOut, crop, colour, board
        var id: String { rawValue }
        var label: String {
            switch self {
            case .cutOut: return "Cut out"
            case .crop:   return "Crop"
            case .colour: return "Colour"
            case .board:  return "Board"
            }
        }
    }

    @Published var tab: Tab = .cutOut
    @Published var brushRestores = false
    @Published var brushSize: Double = 0.06
    @Published private(set) var gridSize: GridSize = .large
    @Published private(set) var maxColors = 12
    @Published private(set) var shape: PegboardShape = .square
    @Published private(set) var wbStrength: Double = 0

    /// The crop the user dragged, in studio pixels, or nil for the automatic
    /// centred one. Kept here rather than in the view because the portrait and
    /// landscape arrangements are separate call sites - state held in a pane
    /// would be lost on every rotation.
    @Published private(set) var userCrop: ImageConverter.CropRect?

    /// Size of the image the crop is expressed in, so a view can map between
    /// studio pixels and screen points without reaching into the studio.
    var sourceSize: CGSize {
        guard let s = studio else { return .zero }
        return CGSize(width: s.width, height: s.height)
    }

    /// The crop currently in force, automatic or chosen.
    var effectiveCrop: ImageConverter.CropRect {
        if let u = userCrop { return u }
        guard let s = studio else {
            return ImageConverter.CropRect(minX: 0, minY: 0, width: 1, height: 1)
        }
        return ImageConverter.aspectCrop(width: s.width, height: s.height,
                                         cols: gridSize.width, rows: gridSize.height)
    }

    /// Move and resize the crop. Always routed through fitAspect, so no amount
    /// of dragging can produce a rect of the wrong shape - which is the only
    /// way a crop can squash the picture.
    func moveCrop(dxPixels: Double, dyPixels: Double, scale: Double) {
        guard let s = studio else { return }
        let c = effectiveCrop
        userCrop = ImageConverter.fitAspect(
            cx: c.minX + c.width / 2 + Int(dxPixels.rounded()),
            cy: c.minY + c.height / 2 + Int(dyPixels.rounded()),
            wantW: Int((Double(c.width) * scale).rounded()),
            wantH: Int((Double(c.height) * scale).rounded()),
            srcW: s.width, srcH: s.height,
            cols: gridSize.width, rows: gridSize.height)
        scheduleRebuild()
    }

    func resetCrop() {
        guard userCrop != nil else { return }
        userCrop = nil
        scheduleRebuild()
    }

    func cropWholePhoto() {
        guard let s = studio else { return }
        userCrop = ImageConverter.fitAspect(
            cx: s.width / 2, cy: s.height / 2,
            wantW: s.width, wantH: s.height,
            srcW: s.width, srcH: s.height,
            cols: gridSize.width, rows: gridSize.height)
        scheduleRebuild()
    }

    @Published private(set) var preview: UIImage?
    @Published private(set) var pattern: FusePattern?
    @Published private(set) var busy = true
    @Published private(set) var autoRunning = false
    @Published private(set) var autoUnavailable = false
    @Published var failure: String?

    private var studio: PhotoStudio?
    private var gains: (Double, Double, Double) = (1, 1, 1)
    private var measuredGains: (Double, Double, Double) = (1, 1, 1)

    /// Coalesces rebuilds so a fast drag does not queue one per touch event.
    private var rebuildTask: Task<Void, Never>?

    func start(source: UIImage, autoSegment: Bool) async {
        guard studio == nil else { return }
        busy = true
        let built = await Task.detached { PhotoStudio.from(source) }.value
        guard let built else {
            failure = "Could not read that photo."
            busy = false
            return
        }
        studio = built
        if autoSegment { await autoCutOut(source: source, initial: true) }
        measuredGains = built.measureGreyWorld()
        await rebuild()
    }

    // MARK: - Edits

    func paint(nx: Double, ny: Double) {
        guard let studio else { return }
        if studio.brush(nx: nx, ny: ny, radiusFrac: brushSize * 0.5, keepValue: brushRestores) {
            scheduleRebuild()
        }
    }

    func keepAll() {
        studio?.keepAll()
        scheduleRebuild()
    }

    func setMaxColors(_ n: Int) { maxColors = n; scheduleRebuild() }
    func setGrid(_ g: GridSize) { gridSize = g; scheduleRebuild() }
    func setShape(_ s: PegboardShape) { shape = s; scheduleRebuild() }

    /// White balance is a blend towards the gains measured ONCE, on demand.
    ///
    /// Re-measuring continuously would make every brush stroke shift the colour
    /// of the whole image - both bad to look at, and it would invalidate the
    /// pattern between one stroke and the next for reasons the user cannot see.
    func setWhiteBalance(_ strength: Double) {
        wbStrength = strength
        let t = min(max(strength, 0), 1)
        gains = (1 + (measuredGains.0 - 1) * t,
                 1 + (measuredGains.1 - 1) * t,
                 1 + (measuredGains.2 - 1) * t)
        scheduleRebuild()
    }

    func autoCutOut(source: UIImage, initial: Bool = false) async {
        guard let studio else { return }
        autoRunning = true
        autoUnavailable = false
        defer { autoRunning = false }
        // The FULL-RESOLUTION photo, not the studio's 384px working buffer: the
        // segmenter asks for at least 512x512 for an accurate mask, and adopting
        // a mask of any size is what adoptMask is for.
        guard let mask = await BackgroundRemover.subjectMask(source) else {
            autoUnavailable = true
            return
        }
        let kept = mask.values.filter { $0 }.count
        // A mask that keeps everything, or nothing, is not a usable result even
        // when the segmenter reports success.
        if kept == 0 || kept == mask.values.count {
            autoUnavailable = true
            return
        }
        studio.adoptMask(mask.values, maskW: mask.width, maskH: mask.height)
        if !initial { await rebuild() }
    }

    /// The full-resolution photo with the removed areas made transparent, or nil
    /// when nothing was removed and there is no cut-out worth keeping.
    func cutoutImage(from source: UIImage) -> UIImage? {
        guard let studio, studio.keptFraction < 0.999 else { return nil }
        return studio.maskedFullRes(source)
    }

    // MARK: - Rebuild

    private func scheduleRebuild() {
        rebuildTask?.cancel()
        rebuildTask = Task { [weak self] in
            // One frame of slack, so a drag coalesces into a single rebuild.
            try? await Task.sleep(nanoseconds: 16_000_000)
            guard !Task.isCancelled else { return }
            await self?.rebuild()
        }
        // The preview is cheap and must track the finger immediately, even while
        // the pattern is still catching up.
        preview = studio?.photoPreview()
    }

    private func rebuild() async {
        guard let studio else { return }
        busy = true
        let cols = gridSize.width, rows = gridSize.height
        let colors = maxColors, shp = shape, g = gains
        let uc = userCrop
        let built = await Task.detached {
            studio.buildPattern(title: "Imported Photo", cols: cols, rows: rows,
                                maxColors: colors, shape: shp, gains: g,
                                userCrop: uc)
        }.value
        pattern = built
        preview = studio.photoPreview()
        busy = false
    }
}

// MARK: - Crop overlay

/// The whole photo with the crop box on it: drag to move it, pinch to resize.
///
/// Sits over the photo pane and exists only while the Crop tab is open. The
/// pane underneath also guards on the tab, so the brush cannot paint here even
/// if a touch were to reach it - on Android, relying on the overlay alone let
/// an unconsumed tap fall through and edit the cut-out mask silently.
///
/// Every gesture result goes through `model.moveCrop`, which routes it through
/// `ImageConverter.fitAspect`, so no amount of dragging can produce a box of
/// the wrong shape. That is the whole reason the crop cannot squash a picture.
private struct CropOverlay: View {
    @ObservedObject var model: PhotoTuneModel
    let box: CGSize

    /// Both gestures report CUMULATIVE values, so the previous one is kept and
    /// subtracted to get the increment. Reset on end, or the next gesture
    /// starts with a jump.
    @State private var lastTranslation: CGSize = .zero
    @State private var lastMagnification: CGFloat = 1

    private var imageSize: CGSize { model.sourceSize }

    /// Points per studio pixel, through the same `.fit` letterbox the photo is
    /// drawn into, so the box lands where the picture actually is.
    private var scale: CGFloat {
        guard imageSize.width > 0, imageSize.height > 0,
              box.width > 0, box.height > 0 else { return 0 }
        return min(box.width / imageSize.width, box.height / imageSize.height)
    }

    private var cropFrame: CGRect {
        guard scale > 0 else { return .zero }
        let drawW = imageSize.width * scale
        let drawH = imageSize.height * scale
        let left = (box.width - drawW) / 2
        let top = (box.height - drawH) / 2
        let c = model.effectiveCrop
        return CGRect(x: left + CGFloat(c.minX) * scale,
                      y: top + CGFloat(c.minY) * scale,
                      width: CGFloat(c.width) * scale,
                      height: CGFloat(c.height) * scale)
    }

    var body: some View {
        let r = cropFrame
        Canvas { ctx, size in
            guard r.width > 0, r.height > 0 else { return }
            // Dim what will be thrown away, in four bands around the box.
            let scrim = GraphicsContext.Shading.color(.black.opacity(0.55))
            ctx.fill(Path(CGRect(x: 0, y: 0, width: size.width, height: max(0, r.minY))), with: scrim)
            ctx.fill(Path(CGRect(x: 0, y: r.maxY,
                                 width: size.width,
                                 height: max(0, size.height - r.maxY))), with: scrim)
            ctx.fill(Path(CGRect(x: 0, y: r.minY, width: max(0, r.minX), height: r.height)), with: scrim)
            ctx.fill(Path(CGRect(x: r.maxX, y: r.minY,
                                 width: max(0, size.width - r.maxX),
                                 height: r.height)), with: scrim)

            ctx.stroke(Path(r), with: .color(.accentColor), lineWidth: 3)
            // Thirds, so it reads as a camera crop frame rather than a selection.
            for i in 1...2 {
                let gx = r.minX + r.width * CGFloat(i) / 3
                let gy = r.minY + r.height * CGFloat(i) / 3
                var v = Path(); v.move(to: CGPoint(x: gx, y: r.minY)); v.addLine(to: CGPoint(x: gx, y: r.maxY))
                var h = Path(); h.move(to: CGPoint(x: r.minX, y: gy)); h.addLine(to: CGPoint(x: r.maxX, y: gy))
                ctx.stroke(v, with: .color(.accentColor.opacity(0.35)), lineWidth: 1)
                ctx.stroke(h, with: .color(.accentColor.opacity(0.35)), lineWidth: 1)
            }
        }
        .contentShape(Rectangle())
        .gesture(
            SimultaneousGesture(
                DragGesture()
                    .onChanged { value in
                        guard scale > 0 else { return }
                        let dx = value.translation.width - lastTranslation.width
                        let dy = value.translation.height - lastTranslation.height
                        lastTranslation = value.translation
                        // The box follows the finger.
                        model.moveCrop(dxPixels: Double(dx / scale),
                                       dyPixels: Double(dy / scale),
                                       scale: 1)
                    }
                    .onEnded { _ in lastTranslation = .zero },
                MagnifyGesture()
                    .onChanged { value in
                        guard lastMagnification > 0 else { return }
                        let step = value.magnification / lastMagnification
                        lastMagnification = value.magnification
                        guard step.isFinite, step > 0 else { return }
                        // Pinching apart makes the box itself bigger.
                        model.moveCrop(dxPixels: 0, dyPixels: 0, scale: Double(step))
                    }
                    .onEnded { _ in lastMagnification = 1 }
            )
        )
        .accessibilityLabel("Crop area. Drag to move it, pinch to resize it")
    }
}
