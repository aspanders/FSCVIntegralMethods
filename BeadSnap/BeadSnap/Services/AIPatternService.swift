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
        case .noAPIKey:              return "No API key set. Tap 'Set Up AI' to add your Claude or ChatGPT API key."
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

/// The AI backend the user paired. Both use the user's own key over HTTPS; keys
/// live in the Keychain, the provider choice (not sensitive) in UserDefaults.
enum AIProvider: String, CaseIterable, Identifiable {
    case claude, openai
    var id: String { rawValue }
    var displayName: String { self == .claude ? "Claude (Anthropic)" : "ChatGPT (OpenAI)" }
    var keyAccount: String { self == .claude ? "claude_api_key" : "openai_api_key" }
    var keyPrefixHint: String { self == .claude ? "sk-ant-…" : "sk-…" }
    var consoleURL: String {
        self == .claude ? "https://console.anthropic.com/settings/keys"
                        : "https://platform.openai.com/api-keys"
    }
}

final class AIPatternService {
    static let shared = AIPatternService()
    private init() {}

    private let claudeURL = URL(string: "https://api.anthropic.com/v1/messages")!
    private let openAIURL = URL(string: "https://api.openai.com/v1/chat/completions")!
    private let claudeModel = "claude-haiku-4-5"
    private let openAIModel = "gpt-4o-mini"

    private let providerKey = "ai_provider"

    // Bounded timeouts matching Android's OkHttp config (30s connect / 60s read)
    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 60
        config.timeoutIntervalForResource = 90
        return URLSession(configuration: config)
    }()

    /// Which provider requests use. Persisted, defaults to Claude.
    var provider: AIProvider {
        get { AIProvider(rawValue: UserDefaults.standard.string(forKey: providerKey) ?? "") ?? .claude }
        set { UserDefaults.standard.set(newValue.rawValue, forKey: providerKey) }
    }

    // Per-provider keys (Keychain), so both can be stored and swapped freely.
    func apiKey(for p: AIProvider) -> String { Keychain.load(for: p.keyAccount) ?? "" }
    func setAPIKey(_ value: String, for p: AIProvider) {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty { Keychain.delete(for: p.keyAccount) }
        else { Keychain.save(trimmed, for: p.keyAccount) }
    }
    func hasAPIKey(for p: AIProvider) -> Bool {
        !apiKey(for: p).trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    // Current-provider convenience (keeps existing call sites working).
    var apiKey: String {
        get { apiKey(for: provider) }
        set { setAPIKey(newValue, for: provider) }
    }
    var hasAPIKey: Bool { hasAPIKey(for: provider) }

    // MARK: - System Prompt

    private let systemPrompt = """
    Generate fuse bead pixel-art patterns as JSON only. No commentary. No prose. No markdown.
    Output must be a single valid JSON object matching this exact schema:
    {
      "id": "<uuid-string>",
      "title": "<short title>",
      "category": "<animals|space|food|emoji|holidays|icons|custom>",
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
        let text = try await requestText(user: userMessage)
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

    /// Get the raw model text from whichever provider is selected.
    private func requestText(user: String) async throws -> String {
        switch provider {
        case .claude: return try await callClaude(user: user)
        case .openai: return try await callOpenAI(user: user)
        }
    }

    private func send(_ req: URLRequest) async throws -> Data {
        let data: Data
        let resp: URLResponse
        do { (data, resp) = try await session.data(for: req) }
        catch {
            if error is CancellationError || (error as? URLError)?.code == .cancelled {
                throw CancellationError()
            }
            throw AIError.networkError(error)
        }
        if let http = resp as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw AIError.httpError(http.statusCode)
        }
        return data
    }

    private func callClaude(user: String) async throws -> String {
        var req = URLRequest(url: claudeURL)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue(apiKey, forHTTPHeaderField: "x-api-key")
        req.setValue("2023-06-01", forHTTPHeaderField: "anthropic-version")
        let body: [String: Any] = [
            "model": claudeModel,
            "max_tokens": 4096,
            "system": systemPrompt,
            "messages": [["role": "user", "content": user]]
        ]
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        let data = try await send(req)
        struct R: Decodable { struct C: Decodable { let text: String }; let content: [C] }
        guard let r = try? JSONDecoder().decode(R.self, from: data),
              let t = r.content.first?.text,
              !t.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw AIError.noContent
        }
        return t
    }

    private func callOpenAI(user: String) async throws -> String {
        var req = URLRequest(url: openAIURL)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        let body: [String: Any] = [
            "model": openAIModel,
            "max_tokens": 4096,
            // Force strict JSON output so extractJSON always has a clean object.
            "response_format": ["type": "json_object"],
            "messages": [
                ["role": "system", "content": systemPrompt],
                ["role": "user", "content": user]
            ]
        ]
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        let data = try await send(req)
        struct R: Decodable {
            struct Choice: Decodable { struct Msg: Decodable { let content: String }; let message: Msg }
            let choices: [Choice]
        }
        guard let r = try? JSONDecoder().decode(R.self, from: data),
              let t = r.choices.first?.message.content,
              !t.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw AIError.noContent
        }
        return t
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
