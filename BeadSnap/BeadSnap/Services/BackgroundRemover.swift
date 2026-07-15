import UIKit
import Vision

/// Background removal for photo imports: an on-device Vision subject mask,
/// a faded-background preview, and a Remove / Add back touch-up brush.
/// Mirrors Android's BackgroundRemover + MaskModel.
@MainActor
final class MaskEditor: ObservableObject {
    static let workMaxDim: CGFloat = 512

    @Published private(set) var previewImage: UIImage?
    @Published private(set) var isProcessing = false
    @Published private(set) var autoUnavailable = false
    @Published var brushAddsBack = false   // false = remove, true = add back

    private(set) var width = 0
    private(set) var height = 0
    private var pixels: [UInt8] = []   // RGBA (straight alpha) of the working image
    private var mask: [Bool] = []      // true = keep (foreground)

    var hasImage: Bool { width > 0 }

    func reset() {
        previewImage = nil
        autoUnavailable = false
        width = 0; height = 0
        pixels = []; mask = []
    }

    /// Load a photo, run the automatic subject mask, and build the faded preview.
    func load(image: UIImage) async {
        isProcessing = true
        defer { isProcessing = false }
        reset()
        let work = Self.downscale(image, maxDim: Self.workMaxDim)
        guard let cg = work.cgImage,
              let buffer = Self.rgbaBuffer(from: cg) else {
            autoUnavailable = true
            return
        }
        width = cg.width
        height = cg.height
        pixels = buffer
        mask = Array(repeating: true, count: width * height)

        if let auto = await Self.subjectMask(cgImage: cg) {
            mask = auto
        } else {
            autoUnavailable = true
        }
        recomposite()
    }

    /// Paint a circle into the mask at normalized image coordinates (0–1).
    func brush(atNormalized point: CGPoint) {
        guard hasImage else { return }
        let cx = Int(point.x * CGFloat(width))
        let cy = Int(point.y * CGFloat(height))
        let radius = max(6, Int(CGFloat(max(width, height)) * 0.05))
        let keepValue = brushAddsBack
        let r2 = radius * radius
        for y in max(0, cy - radius)...min(height - 1, cy + radius) {
            for x in max(0, cx - radius)...min(width - 1, cx + radius) {
                let dx = x - cx, dy = y - cy
                if dx * dx + dy * dy <= r2 {
                    mask[y * width + x] = keepValue
                }
            }
        }
        recomposite()
    }

    /// Final image for conversion — background fully transparent, so the
    /// converter's alpha < 0.15 skip leaves those cells empty.
    func maskedImage() -> UIImage? {
        composite(fadeAlpha: 0)
    }

    // MARK: - Compositing

    private func recomposite() {
        previewImage = composite(fadeAlpha: 0.25)
    }

    private func composite(fadeAlpha: CGFloat) -> UIImage? {
        guard hasImage else { return nil }
        var out = pixels
        let fade = UInt32(fadeAlpha * 255)
        for i in 0..<(width * height) where !mask[i] {
            let p = i * 4
            // scale all channels so the buffer stays valid premultiplied RGBA
            out[p]     = UInt8(UInt32(out[p])     * fade / 255)
            out[p + 1] = UInt8(UInt32(out[p + 1]) * fade / 255)
            out[p + 2] = UInt8(UInt32(out[p + 2]) * fade / 255)
            out[p + 3] = UInt8(UInt32(out[p + 3]) * fade / 255)
        }
        guard let provider = CGDataProvider(data: Data(out) as CFData),
              let cg = CGImage(
                width: width, height: height,
                bitsPerComponent: 8, bitsPerPixel: 32, bytesPerRow: width * 4,
                space: CGColorSpaceCreateDeviceRGB(),
                bitmapInfo: CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue),
                provider: provider, decode: nil,
                shouldInterpolate: true, intent: .defaultIntent
              ) else { return nil }
        return UIImage(cgImage: cg)
    }

    // MARK: - Vision subject mask

    private nonisolated static func subjectMask(cgImage: CGImage) async -> [Bool]? {
        await Task.detached(priority: .userInitiated) { () -> [Bool]? in
            let request = VNGenerateForegroundInstanceMaskRequest()
            let handler = VNImageRequestHandler(cgImage: cgImage)
            guard (try? handler.perform([request])) != nil,
                  let result = request.results?.first,
                  !result.allInstances.isEmpty,
                  let maskBuffer = try? result.generateScaledMaskForImage(
                      forInstances: result.allInstances, from: handler
                  ) else { return nil }

            CVPixelBufferLockBaseAddress(maskBuffer, .readOnly)
            defer { CVPixelBufferUnlockBaseAddress(maskBuffer, .readOnly) }
            guard let base = CVPixelBufferGetBaseAddress(maskBuffer) else { return nil }
            let mw = CVPixelBufferGetWidth(maskBuffer)
            let mh = CVPixelBufferGetHeight(maskBuffer)
            let rowBytes = CVPixelBufferGetBytesPerRow(maskBuffer)
            guard mw == cgImage.width, mh == cgImage.height else { return nil }

            var keep = [Bool](repeating: false, count: mw * mh)
            for y in 0..<mh {
                let row = base.advanced(by: y * rowBytes)
                    .assumingMemoryBound(to: Float32.self)
                for x in 0..<mw {
                    keep[y * mw + x] = row[x] > 0.5
                }
            }
            return keep
        }.value
    }

    // MARK: - Image helpers

    private nonisolated static func downscale(_ image: UIImage, maxDim: CGFloat) -> UIImage {
        let size = image.size
        let longest = max(size.width, size.height)
        guard longest > maxDim else { return image.fixedOrientation() }
        let scale = maxDim / longest
        let newSize = CGSize(width: size.width * scale, height: size.height * scale)
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        return UIGraphicsImageRenderer(size: newSize, format: format).image { _ in
            image.draw(in: CGRect(origin: .zero, size: newSize))
        }
    }

    private nonisolated static func rgbaBuffer(from cg: CGImage) -> [UInt8]? {
        let w = cg.width, h = cg.height
        var data = [UInt8](repeating: 0, count: w * h * 4)
        guard let ctx = CGContext(
            data: &data, width: w, height: h,
            bitsPerComponent: 8, bytesPerRow: w * 4,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else { return nil }
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))
        return data
    }
}
