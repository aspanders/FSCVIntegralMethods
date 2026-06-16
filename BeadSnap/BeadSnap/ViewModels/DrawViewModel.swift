import SwiftUI

struct DrawStroke: Identifiable {
    var id = UUID()
    var points: [CGPoint]
    var color: Color
    var width: CGFloat
}

@MainActor
final class DrawViewModel: ObservableObject {
    @Published var strokes: [DrawStroke] = []
    @Published var currentStroke: DrawStroke?
    @Published var selectedColor: Color = .black
    @Published var selectedColorID: String = "black"
    @Published var brushWidth: CGFloat = 8
    @Published var isEraser = false
    @Published var canvasSize: CGSize = .zero

    func selectBeadColor(_ bead: BeadColor) {
        selectedColor = bead.swiftUIColor
        selectedColorID = bead.id
        isEraser = false
    }

    var undoStack: [[DrawStroke]] = []

    func beginDraw(at point: CGPoint) {
        let color = isEraser ? Color.white : selectedColor
        currentStroke = DrawStroke(points: [point], color: color, width: brushWidth)
    }

    func continueDraw(to point: CGPoint) {
        currentStroke?.points.append(point)
    }

    func endDraw() {
        guard let stroke = currentStroke else { return }
        undoStack.append(strokes)
        strokes.append(stroke)
        currentStroke = nil
    }

    func undo() {
        if let prev = undoStack.popLast() {
            strokes = prev
        }
    }

    func clearAll() {
        undoStack.append(strokes)
        strokes = []
    }

    func rasterize(size: CGSize) -> UIImage? {
        UIGraphicsBeginImageContextWithOptions(size, false, 0)
        defer { UIGraphicsEndImageContext() }

        guard let ctx = UIGraphicsGetCurrentContext() else { return nil }

        UIColor.white.setFill()
        ctx.fill(CGRect(origin: .zero, size: size))

        for stroke in strokes {
            drawStroke(stroke, in: ctx)
        }

        return UIGraphicsGetImageFromCurrentImageContext()
    }

    private func drawStroke(_ stroke: DrawStroke, in ctx: CGContext) {
        guard stroke.points.count >= 2 else {
            if let pt = stroke.points.first {
                let r = CGRect(
                    x: pt.x - stroke.width / 2,
                    y: pt.y - stroke.width / 2,
                    width: stroke.width,
                    height: stroke.width
                )
                UIColor(stroke.color).setFill()
                ctx.fillEllipse(in: r)
            }
            return
        }
        ctx.setStrokeColor(UIColor(stroke.color).cgColor)
        ctx.setLineWidth(stroke.width)
        ctx.setLineCap(.round)
        ctx.setLineJoin(.round)
        ctx.beginPath()
        ctx.move(to: stroke.points[0])
        for pt in stroke.points.dropFirst() {
            ctx.addLine(to: pt)
        }
        ctx.strokePath()
    }
}
