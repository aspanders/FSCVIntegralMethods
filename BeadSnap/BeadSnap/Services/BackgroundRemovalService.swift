import UIKit
import Vision

enum BackgroundRemovalError: Error {
    case noForeground
    case processingFailed(String)
}

final class BackgroundRemovalService {
    static let shared = BackgroundRemovalService()
    private init() {}

    // Returns the masked image (transparent background) and the mask itself
    func removeBg(from image: UIImage) async throws -> (masked: UIImage, mask: UIImage) {
        if #available(iOS 17.0, *) {
            return try await removeBgVisionV2(image)
        } else {
            return try await removeBgSaliency(image)
        }
    }

    @available(iOS 17.0, *)
    private func removeBgVisionV2(_ image: UIImage) async throws -> (masked: UIImage, mask: UIImage) {
        guard let cgImage = image.cgImage else {
            throw BackgroundRemovalError.processingFailed("No CGImage")
        }

        return try await withCheckedThrowingContinuation { continuation in
            let request = VNGenerateForegroundInstanceMaskRequest { req, err in
                if let err = err {
                    continuation.resume(throwing: BackgroundRemovalError.processingFailed(err.localizedDescription))
                    return
                }
                guard let result = req.results?.first as? VNInstanceMaskObservation else {
                    continuation.resume(throwing: BackgroundRemovalError.noForeground)
                    return
                }
                do {
                    let allInstances = result.allInstances
                    let maskBuffer = try result.generateScaledMaskForImage(
                        forInstances: allInstances,
                        from: VNImageRequestHandler(cgImage: cgImage)
                    )
                    let maskImage = UIImage(pixelBuffer: maskBuffer) ?? UIImage()
                    let maskedImage = applyMask(maskImage, to: image)
                    continuation.resume(returning: (maskedImage, maskImage))
                } catch {
                    continuation.resume(throwing: BackgroundRemovalError.processingFailed(error.localizedDescription))
                }
            }

            let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
            do {
                try handler.perform([request])
            } catch {
                continuation.resume(throwing: BackgroundRemovalError.processingFailed(error.localizedDescription))
            }
        }
    }

    private func removeBgSaliency(_ image: UIImage) async throws -> (masked: UIImage, mask: UIImage) {
        guard let cgImage = image.cgImage else {
            throw BackgroundRemovalError.processingFailed("No CGImage")
        }

        return try await withCheckedThrowingContinuation { continuation in
            let request = VNGenerateAttentionBasedSaliencyImageRequest { req, err in
                if let err = err {
                    continuation.resume(throwing: BackgroundRemovalError.processingFailed(err.localizedDescription))
                    return
                }
                guard let obs = req.results?.first as? VNSaliencyImageObservation,
                      let saliencyMap = obs.pixelBuffer else {
                    continuation.resume(throwing: BackgroundRemovalError.noForeground)
                    return
                }
                let maskImage = thresholdMask(from: saliencyMap, threshold: 0.3)
                let maskedImage = applyMask(maskImage, to: image)
                continuation.resume(returning: (maskedImage, maskImage))
            }

            let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
            do {
                try handler.perform([request])
            } catch {
                continuation.resume(throwing: BackgroundRemovalError.processingFailed(error.localizedDescription))
            }
        }
    }

    func applyMask(_ mask: UIImage, to image: UIImage) -> UIImage {
        let size = image.size
        UIGraphicsBeginImageContextWithOptions(size, false, image.scale)
        defer { UIGraphicsEndImageContext() }

        guard let ctx = UIGraphicsGetCurrentContext(),
              let cgMask = mask.cgImage,
              let cgImage = image.cgImage else {
            return image
        }

        let rect = CGRect(origin: .zero, size: size)
        ctx.translateBy(x: 0, y: size.height)
        ctx.scaleBy(x: 1, y: -1)

        ctx.clip(to: rect, mask: cgMask)
        ctx.draw(cgImage, in: rect)

        return UIGraphicsGetImageFromCurrentImageContext() ?? image
    }

    // Apply user-painted mask adjustments
    func applyManualMask(
        baseMask: UIImage,
        includeStrokes: [MaskStroke],
        excludeStrokes: [MaskStroke],
        imageSize: CGSize
    ) -> UIImage {
        UIGraphicsBeginImageContextWithOptions(imageSize, false, 1)
        defer { UIGraphicsEndImageContext() }

        guard let ctx = UIGraphicsGetCurrentContext() else { return baseMask }

        // Draw base mask
        baseMask.draw(in: CGRect(origin: .zero, size: imageSize))

        // Paint include strokes (white = keep)
        ctx.setBlendMode(.normal)
        ctx.setStrokeColor(UIColor.white.cgColor)
        for stroke in includeStrokes {
            drawStroke(stroke, in: ctx)
        }

        // Paint exclude strokes (black = remove)
        ctx.setStrokeColor(UIColor.black.cgColor)
        for stroke in excludeStrokes {
            drawStroke(stroke, in: ctx)
        }

        return UIGraphicsGetImageFromCurrentImageContext() ?? baseMask
    }

    private func drawStroke(_ stroke: MaskStroke, in ctx: CGContext) {
        guard stroke.points.count >= 2 else { return }
        ctx.setLineWidth(stroke.brushSize)
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

private func thresholdMask(from pixelBuffer: CVPixelBuffer, threshold: Float) -> UIImage {
    CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
    defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, .readOnly) }

    let width = CVPixelBufferGetWidth(pixelBuffer)
    let height = CVPixelBufferGetHeight(pixelBuffer)
    let bytesPerRow = CVPixelBufferGetBytesPerRow(pixelBuffer)
    guard let base = CVPixelBufferGetBaseAddress(pixelBuffer) else {
        return UIImage()
    }

    let float32Ptr = base.assumingMemoryBound(to: Float32.self)
    var bytes = [UInt8](repeating: 0, count: width * height)
    for y in 0..<height {
        for x in 0..<width {
            let idx = y * (bytesPerRow / MemoryLayout<Float32>.size) + x
            bytes[y * width + x] = float32Ptr[idx] > threshold ? 255 : 0
        }
    }

    guard let provider = CGDataProvider(data: Data(bytes) as CFData),
          let cgImage = CGImage(
              width: width, height: height,
              bitsPerComponent: 8, bitsPerPixel: 8,
              bytesPerRow: width,
              space: CGColorSpaceCreateDeviceGray(),
              bitmapInfo: [],
              provider: provider,
              decode: nil,
              shouldInterpolate: false,
              intent: .defaultIntent
          ) else {
        return UIImage()
    }
    return UIImage(cgImage: cgImage)
}

extension UIImage {
    convenience init?(pixelBuffer: CVPixelBuffer) {
        let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
        let context = CIContext()
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else { return nil }
        self.init(cgImage: cgImage)
    }
}

struct MaskStroke: Identifiable {
    var id: UUID = UUID()
    var points: [CGPoint]
    var brushSize: CGFloat
}
