import SwiftUI

struct PatternEditorView: View {
    @ObservedObject var vm: PatternViewModel
    @State private var isErasing = false

    var body: some View {
        ZStack(alignment: .bottom) {
            Color(.systemGroupedBackground).ignoresSafeArea()

            VStack(spacing: 0) {
                // Mode badge
                HStack {
                    Spacer()
                    Button {
                        isErasing.toggle()
                    } label: {
                        Label(
                            isErasing ? "Erasing" : "Drawing",
                            systemImage: isErasing ? "eraser.fill" : "pencil.tip"
                        )
                        .font(.caption.bold())
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(isErasing ? Color.red.opacity(0.15) : Color.blue.opacity(0.15))
                        .clipShape(Capsule())
                    }
                    .padding(.trailing)
                    .padding(.top, 8)
                }

                // Interactive bead grid
                if let pattern = vm.pattern {
                    InteractiveBeadGrid(
                        pattern: pattern,
                        isErasing: isErasing,
                        onEdit: { row, col in
                            if isErasing {
                                vm.clearBead(row: row, col: col)
                            } else {
                                vm.setBead(row: row, col: col, color: vm.selectedEditorColor)
                            }
                        }
                    )
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    ProgressView("Generating pattern...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                }

                Divider()

                // Color picker
                BeadColorPicker(selectedColor: $vm.selectedEditorColor) {
                    isErasing = true
                }
                .padding(.bottom, 8)
            }
        }
        .navigationTitle("Edit Beads")
        .navigationBarTitleDisplayMode(.inline)
    }
}

// A UIKit-backed scrollable grid that translates touches to (row, col) edits
struct InteractiveBeadGrid: UIViewRepresentable {
    let pattern: BeadPattern
    let isErasing: Bool
    let onEdit: (Int, Int) -> Void

    func makeUIView(context: Context) -> BeadGridScrollView {
        let view = BeadGridScrollView()
        view.pattern = pattern
        view.onEdit = onEdit
        return view
    }

    func updateUIView(_ uiView: BeadGridScrollView, context: Context) {
        if uiView.pattern?.id != pattern.id {
            uiView.pattern = pattern
            uiView.setNeedsDisplay()
        } else {
            uiView.pattern = pattern
            uiView.setNeedsDisplay()
        }
    }
}

final class BeadGridScrollView: UIScrollView, UIScrollViewDelegate {
    var pattern: BeadPattern? { didSet { gridView?.pattern = pattern; layoutGrid() } }
    var onEdit: ((Int, Int) -> Void)?
    private var gridView: BeadGridCanvasView?

    override init(frame: CGRect) {
        super.init(frame: frame)
        setup()
    }
    required init?(coder: NSCoder) { fatalError() }

    private func setup() {
        delegate = self
        minimumZoomScale = 0.5
        maximumZoomScale = 4.0
        showsHorizontalScrollIndicator = false
        showsVerticalScrollIndicator = false
        backgroundColor = UIColor.secondarySystemBackground

        let gv = BeadGridCanvasView()
        gv.onEdit = { [weak self] row, col in self?.onEdit?(row, col) }
        addSubview(gv)
        gridView = gv
    }

    private func layoutGrid() {
        guard let pattern = pattern else { return }
        let bead: CGFloat = 18
        let w = CGFloat(pattern.cols) * bead
        let h = CGFloat(pattern.rows) * bead
        gridView?.frame = CGRect(x: 0, y: 0, width: w, height: h)
        gridView?.beadSize = bead
        contentSize = CGSize(width: w, height: h)
    }

    func viewForZooming(in scrollView: UIScrollView) -> UIView? { gridView }
}

final class BeadGridCanvasView: UIView {
    var pattern: BeadPattern? { didSet { setNeedsDisplay() } }
    var beadSize: CGFloat = 18 { didSet { setNeedsDisplay() } }
    var onEdit: ((Int, Int) -> Void)?

    override init(frame: CGRect) {
        super.init(frame: frame)
        backgroundColor = .secondarySystemBackground
        let pan = UIPanGestureRecognizer(target: self, action: #selector(handlePan))
        pan.minimumNumberOfTouches = 1
        pan.maximumNumberOfTouches = 1
        addGestureRecognizer(pan)
        let tap = UITapGestureRecognizer(target: self, action: #selector(handleTap))
        addGestureRecognizer(tap)
    }
    required init?(coder: NSCoder) { fatalError() }

    @objc private func handleTap(_ g: UITapGestureRecognizer) {
        edit(at: g.location(in: self))
    }

    @objc private func handlePan(_ g: UIPanGestureRecognizer) {
        edit(at: g.location(in: self))
    }

    private func edit(at point: CGPoint) {
        let col = Int(point.x / beadSize)
        let row = Int(point.y / beadSize)
        onEdit?(row, col)
        setNeedsDisplay()
    }

    override func draw(_ rect: CGRect) {
        guard let ctx = UIGraphicsGetCurrentContext(), let pattern = pattern else { return }
        ctx.setFillColor(UIColor.secondarySystemBackground.cgColor)
        ctx.fill(rect)

        let b = beadSize
        let inset = b * 0.06

        for row in 0..<pattern.rows {
            for col in 0..<pattern.cols {
                let x = CGFloat(col) * b
                let y = CGFloat(row) * b
                let ovalRect = CGRect(x: x + inset, y: y + inset, width: b - 2 * inset, height: b - 2 * inset)

                if let color = pattern.color(row: row, col: col) {
                    ctx.setFillColor(color.uiColor.cgColor)
                    ctx.fillEllipse(in: ovalRect)
                    ctx.setStrokeColor(UIColor.black.withAlphaComponent(0.15).cgColor)
                    ctx.setLineWidth(0.5)
                    ctx.strokeEllipse(in: ovalRect)
                } else if pattern.isInsideCircle(row: row, col: col) {
                    ctx.setFillColor(UIColor.systemGray5.cgColor)
                    ctx.fillEllipse(in: ovalRect)
                }
            }
        }

        // Subtle grid
        ctx.setStrokeColor(UIColor.black.withAlphaComponent(0.06).cgColor)
        ctx.setLineWidth(0.3)
        for r in 0...pattern.rows {
            let y = CGFloat(r) * b
            ctx.move(to: CGPoint(x: 0, y: y))
            ctx.addLine(to: CGPoint(x: CGFloat(pattern.cols) * b, y: y))
        }
        for c in 0...pattern.cols {
            let x = CGFloat(c) * b
            ctx.move(to: CGPoint(x: x, y: 0))
            ctx.addLine(to: CGPoint(x: x, y: CGFloat(pattern.rows) * b))
        }
        ctx.strokePath()
    }
}
