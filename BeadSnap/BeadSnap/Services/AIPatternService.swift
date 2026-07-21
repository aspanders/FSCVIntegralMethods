import Foundation

enum AIError: LocalizedError {
    case noAPIKey
    case networkError(Error)
    case httpError(Int)
    case noContent
    case invalidJSON(String)
    case schemaViolation(String)
    case tooComplex

    var errorDescription: String? {
        switch self {
        case .noAPIKey:              return "No API key set. Tap 'Set Up AI' to add your Claude API key."
        case .networkError(let e):   return "Network error: \(e.localizedDescription)"
        case .httpError(let code):
            switch code {
            case 401: return "Invalid API key. Tap 'Set Up AI' to update it."
            case 400: return "Bad request. Check your API key."
            case 429: return "Rate limit reached. Please wait a moment and try again."
            default:  return "Server error (\(code)). Please try again."
            }
        case .noContent:             return "AI returned no content. Please try again."
        case .invalidJSON(let s):    return "AI returned invalid JSON: \(s)"
        case .schemaViolation(let s): return "Pattern validation failed: \(s)"
        case .tooComplex: return "Pattern is too large for AI refinement. Use a smaller grid or fill fewer cells."
        }
    }
}

final class AIPatternService {
    static let shared = AIPatternService()
    private init() {}

    private let apiURL = URL(string: "https://api.anthropic.com/v1/messages")!
    private let model = "claude-haiku-4-5"

    private let apiKeyAccount = "claude_api_key"

    // Bounded timeouts matching Android's OkHttp config (30s connect / 60s read)
    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 60
        config.timeoutIntervalForResource = 90
        return URLSession(configuration: config)
    }()

    var apiKey: String {
        get { Keychain.load(for: apiKeyAccount) ?? "" }
        set {
            let trimmed = newValue.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmed.isEmpty {
                Keychain.delete(for: apiKeyAccount)
            } else {
                Keychain.save(trimmed, for: apiKeyAccount)
            }
        }
    }
    var hasAPIKey: Bool { !apiKey.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }

    // MARK: - System Prompt

    private let systemPrompt = """
    Generate fuse bead pixel-art patterns as JSON only. No commentary. No prose. No markdown.
    Output must be a single valid JSON object matching this exact schema:
    {
      "id": "<uuid-string>",
      "title": "<short title>",
      "category": "<animals|fantasy|vehicles|nature|icons|holidays|custom>",
      "createdBy": "ai",
      "grid": {"width": <8-64>, "height": <8-64>},
      "palette": [{"id": "<id>", "name": "<name>", "hex": "<#RRGGBB>"}],
      "cells": [{"x": <int>, "y": <int>, "colorId": "<id>"}],
      "difficulty": "<easy|medium|hard>",
      "tags": ["<tag>"],
      "sourcePrompt": "<prompt used>",
      "version": 1
    }
    Rules (strictly enforced):
    - Grid: width and height each between 8 and 64. Default 32x32 unless asked.
    - Palette: exactly 4 to 16 colors. Use only real Perler/Hama bead colors.
    - Cells: sparse list. Include only filled cells: omit empty/background positions.
    - All colorId values in cells must match an id in palette.
    - Pixel-art style only. Bold simple shapes. No gradients. No realism.
    - Safe for children ages 4+. No violence, weapons, or inappropriate content.
    - Pattern must be physically buildable as real fuse bead art.
    """

    // MARK: - Public API

    func generate(
        prompt: String,
        category: PatternCategory? = nil,
        gridSize: GridSize = .large
    ) async throws -> FusePattern {
        guard hasAPIKey else { throw AIError.noAPIKey }
        let catHint = category.map { " Category: \($0.rawValue)." } ?? ""
        let msg = "Create a fuse bead pattern of: \(prompt).\(catHint) Grid: \(gridSize.width)x\(gridSize.height)."
        return try await callAPI(userMessage: msg)
    }

    func iterate(pattern: FusePattern, instruction: String) async throws -> FusePattern {
        guard hasAPIKey else { throw AIError.noAPIKey }
        guard pattern.cells.count <= 400 else { throw AIError.tooComplex }
        let paletteDesc = pattern.palette
            .map { "\($0.id): \($0.name) (\($0.hex))" }
            .joined(separator: ", ")
        let cellsDesc = pattern.cells
            .map { "(\($0.x),\($0.y))=\($0.colorId ?? "?")" }
            .joined(separator: " ")
        let msg = """
        Modify this fuse bead pattern per this instruction: \(instruction)
        Grid: \(pattern.grid.width)×\(pattern.grid.height). Title: \(pattern.title). Category: \(pattern.category.rawValue).
        Palette: \(paletteDesc)
        Filled cells as (x,y)=colorId: \(cellsDesc)
        Return only the full updated JSON object matching the schema.
        """
        var updated = try await callAPI(userMessage: msg)
        updated.id = pattern.id
        return updated
    }

    // MARK: - Private

    private func callAPI(userMessage: String) async throws -> FusePattern {
        var req = URLRequest(url: apiURL)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue(apiKey, forHTTPHeaderField: "x-api-key")
        req.setValue("2023-06-01", forHTTPHeaderField: "anthropic-version")

        let body: [String: Any] = [
            "model": model,
            "max_tokens": 4096,
            "system": systemPrompt,
            "messages": [["role": "user", "content": userMessage]]
        ]
        req.httpBody = try JSONSerialization.data(withJSONObject: body)

        let data: Data
        let urlResponse: URLResponse
        do { (data, urlResponse) = try await session.data(for: req) }
        catch {
            // Rethrow cancellation so callers can distinguish user cancel from failure
            if error is CancellationError || (error as? URLError)?.code == .cancelled {
                throw CancellationError()
            }
            throw AIError.networkError(error)
        }

        if let http = urlResponse as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw AIError.httpError(http.statusCode)
        }

        struct Response: Decodable {
            struct Content: Decodable { let text: String }
            let content: [Content]
        }
        guard let resp = try? JSONDecoder().decode(Response.self, from: data),
              let text = resp.content.first?.text,
              !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw AIError.noContent
        }

        let jsonData = try extractJSON(from: text)
        let pattern: FusePattern
        let decoder = JSONDecoder()
        decoder.allowsJSON5 = true   // tolerate lenient model output like Android's isLenient
        do { pattern = try decoder.decode(FusePattern.self, from: jsonData) }
        catch { throw AIError.invalidJSON(error.localizedDescription) }

        var mutable = pattern
        try validate(&mutable)
        return mutable
    }

    private func extractJSON(from text: String) throws -> Data {
        var s = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if s.hasPrefix("```") {
            let lines = s.components(separatedBy: "\n")
            s = lines.dropFirst().dropLast().joined(separator: "\n")
        }
        guard let start = s.firstIndex(of: "{"), let end = s.lastIndex(of: "}") else {
            throw AIError.invalidJSON("No JSON object found")
        }
        guard let data = String(s[start...end]).data(using: .utf8) else {
            throw AIError.invalidJSON("Encoding error")
        }
        return data
    }

    private func validate(_ p: inout FusePattern) throws {
        guard p.grid.width >= 8, p.grid.width <= 64,
              p.grid.height >= 8, p.grid.height <= 64 else {
            throw AIError.schemaViolation("Grid \(p.grid.width)×\(p.grid.height) out of 8-64 range")
        }
        guard p.palette.count >= 4, p.palette.count <= 16 else {
            throw AIError.schemaViolation("Palette must have 4-16 colors, got \(p.palette.count)")
        }
        let ids = Set(p.palette.map(\.id))
        for cell in p.cells {
            if let id = cell.colorId, !ids.contains(id) {
                throw AIError.schemaViolation("Cell references unknown colorId '\(id)'")
            }
            guard cell.x >= 0, cell.x < p.grid.width,
                  cell.y >= 0, cell.y < p.grid.height else {
                throw AIError.schemaViolation("Cell (\(cell.x),\(cell.y)) out of bounds")
            }
        }
        // Deduplicate cells: last writer wins; prevents EditorViewModel crash
        var seen = Set<String>()
        p.cells = p.cells.reversed().filter { cell in
            let key = "\(cell.x),\(cell.y)"
            return seen.insert(key).inserted
        }.reversed()
    }
}
