import Foundation

enum AIError: LocalizedError {
    case noAPIKey
    case networkError(Error)
    case noContent
    case invalidJSON(String)
    case schemaViolation(String)

    var errorDescription: String? {
        switch self {
        case .noAPIKey:              return "No API key set. Tap 'Set Up AI' to add your Claude API key."
        case .networkError(let e):   return "Network error: \(e.localizedDescription)"
        case .noContent:             return "AI returned no content. Please try again."
        case .invalidJSON(let s):    return "AI returned invalid JSON: \(s)"
        case .schemaViolation(let s): return "Pattern validation failed: \(s)"
        }
    }
}

final class AIPatternService {
    static let shared = AIPatternService()
    private init() {}

    private let apiURL = URL(string: "https://api.anthropic.com/v1/messages")!
    private let model = "claude-haiku-4-5-20251001"

    var apiKey: String {
        get { UserDefaults.standard.string(forKey: "claude_api_key") ?? "" }
        set { UserDefaults.standard.set(newValue, forKey: "claude_api_key") }
    }
    var hasAPIKey: Bool { !apiKey.trimmingCharacters(in: .whitespaces).isEmpty }

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
    - Cells: sparse list. Include only filled cells — omit empty/background positions.
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
        let json = (try? String(data: JSONEncoder().encode(pattern), encoding: .utf8)) ?? "{}"
        let msg = """
        Modify this fuse bead pattern per this instruction: \(instruction)
        Preserve schema and structure unless grid resize is explicitly requested.
        Return only the full updated JSON object.

        Existing pattern:
        \(json)
        """
        var updated = try await callAPI(userMessage: msg)
        updated.id = pattern.id  // keep same ID for in-place update
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
        do { (data, _) = try await URLSession.shared.data(for: req) }
        catch { throw AIError.networkError(error) }

        struct Response: Decodable {
            struct Content: Decodable { let text: String }
            let content: [Content]
        }
        guard let resp = try? JSONDecoder().decode(Response.self, from: data),
              let text = resp.content.first?.text, !text.isEmpty else {
            throw AIError.noContent
        }

        let jsonData = try extractJSON(from: text)
        let pattern: FusePattern
        do { pattern = try JSONDecoder().decode(FusePattern.self, from: jsonData) }
        catch { throw AIError.invalidJSON(error.localizedDescription) }

        try validate(pattern)
        return pattern
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

    private func validate(_ p: FusePattern) throws {
        guard p.grid.width >= 8, p.grid.width <= 64,
              p.grid.height >= 8, p.grid.height <= 64 else {
            throw AIError.schemaViolation("Grid \(p.grid.width)×\(p.grid.height) out of 8–64 range")
        }
        guard p.palette.count >= 4, p.palette.count <= 16 else {
            throw AIError.schemaViolation("Palette must have 4–16 colors, got \(p.palette.count)")
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
    }
}
