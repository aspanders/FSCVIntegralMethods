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
                        paint(at: value.location, in: geo.size)
                    }
            )
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
        case cutOut, colour, board
        var id: String { rawValue }
        var label: String {
            switch self {
            case .cutOut: return "Cut out"
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
        let built = await Task.detached {
            studio.buildPattern(title: "Imported Photo", cols: cols, rows: rows,
                                maxColors: colors, shape: shp, gains: g)
        }.value
        pattern = built
        preview = studio.photoPreview()
        busy = false
    }
}
