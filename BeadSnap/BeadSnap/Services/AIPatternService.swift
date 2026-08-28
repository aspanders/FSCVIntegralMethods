import Foundation

enum AIError: LocalizedError {
    case noAPIKey
    case networkError(Error)
    case httpError(Int, String?)
    case noContent
    case invalidJSON(String)
    case schemaViolation(String)
    case tooComplex
    case truncated
    case refused

    var errorDescription: String? {
        switch self {
        case .noAPIKey:              return "No API key set. Tap 'Set Up AI' to add your Claude or ChatGPT API key."
        case .networkError(let e):   return "Network error: \(e.localizedDescription)"
        case .httpError(let code, let detail):
            let head: String
            switch code {
            case 401: head = "Invalid API key. Tap 'Set Up AI' to update it."
            case 402: head = "Your AI account is out of credit."
            case 429: head = "Rate limit reached. Please wait a moment and try again."
            case 500...599: head = "The AI service is having trouble (\(code)). Please try again."
            default:  head = "The AI service rejected the request (\(code))."
            }
            // The provider says WHY in the error body - "your credit balance is
            // too low", "model not found", "invalid schema". Dropping it made
            // every 400 read "Bad request. Check your API key.", which sent
            // people off to re-paste a key that was never the problem.
            guard let detail, !detail.isEmpty else { return head }
            return head + " " + String(detail.prefix(200))
        case .noContent:             return "AI returned no content. Please try again."
        case .invalidJSON(let s):    return "AI returned invalid JSON: \(s)"
        case .schemaViolation(let s): return "Pattern validation failed: \(s)"
        case .tooComplex: return "Pattern is too large for AI refinement. Use a smaller grid or fill fewer cells."
        case .truncated:  return "The pattern came back unfinished. Try a smaller board."
        case .refused:    return "The AI declined that request. Try describing something else."
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
    /// Spatial layout is the hard part of this task and the part a small model
    /// is worst at. Keep in step with AIPatternService.CLAUDE_MODEL on Android.
    static let claudeModel = "claude-opus-5"
    /// Not verified against OpenAI's current lineup - review before relying on it.
    static let openAIModel = "gpt-4o"

    private let providerKey = "ai_provider"

    // Bounded timeouts matching Android's OkHttp config (30s connect / 60s read)
    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 120
        config.timeoutIntervalForResource = 180
        return URLSession(configuration: config)
    }()

    /// Which provider requests use. Persisted, defaults to Claude.
    var provider: AIProvider {
        get { AIProvider(rawValue: UserDefaults.standard.string(forKey: providerKey) ?? "") ?? .claude }
        set { UserDefaults.standard.set(newValue.rawValue, forKey: providerKey) }
    }

    // Per-provider keys (Keychain), so both can be stored and swapped freely.
    func apiKey(for p: AIProvider) -> String { Keychain.load(for: p.keyAccount) ?? "" }
    /// Returns whether the key was stored. See `Keychain.save`.
    @discardableResult
    func setAPIKey(_ value: String, for p: AIProvider) -> Bool {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty {
            Keychain.delete(for: p.keyAccount)
            return true
        }
        return Keychain.save(trimmed, for: p.keyAccount)
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

    /// Every real bead, as the model is allowed to refer to them.
    private var paletteList: String {
        PaletteColor.full.map { "  \($0.id) = \($0.name) \($0.hex)" }.joined(separator: "\n")
    }

    /// Keep in step with the Android systemPrompt - the two platforms should
    /// produce comparable patterns from the same words.
    private var systemPrompt: String { """
    You design fuse bead patterns (Perler / Hama). A pattern is a rectangular peg
    board; the maker places one bead per peg, then irons them so touching beads
    fuse together.

    You return the board as ROWS OF CHARACTERS - one string per row of the board,
    one character per peg:
      - '.' means leave that peg empty.
      - '0'-'9' then 'a'-'z' then 'A'-'Z' select a colour, by its position in the
        palette you chose: '0' is the first colour, '1' the second, and so on.
    Every row string must be exactly `width` characters long, and there must be
    exactly `height` of them. This is a picture drawn in text - lay the subject
    out on the grid and read your own rows back to check the shape before you
    answer.

    Choose colours only from this list of real beads, by id:
    \(paletteList)

    What makes a bead pattern good, in priority order:

    1. RECOGNISABLE AT THIS SIZE. A 16x16 board holds a symbol, not a scene.
       Cover the title and ask whether the shape alone says what it is. Bold
       silhouettes beat detail. If the subject will not read at the size asked
       for, draw the most recognisable PART of it filling the board - a face
       rather than a whole animal - instead of shrinking the whole thing to mush.
    2. BUILDABLE. Beads fuse where their EDGES meet, not at their corners, so
       every filled peg must touch another filled peg up, down, left or right. A
       bead joined to the rest only diagonally falls off when lifted. One
       connected piece, no floating islands. A one-bead-wide leg, antenna or stem
       is fine - it fuses into a solid strand.
    3. FLAT COLOUR. No gradients, no dithering, no anti-aliasing, no shading
       ramps. Large blocks of one colour. Use an outline in a darker bead where
       the subject needs to stand out.
    4. FEW COLOURS. Two to eight is normal. Every extra colour is another bag the
       maker has to own.
    5. CENTRED, with the subject filling most of the board. Do not leave a wide
       empty margin.
    6. Suitable for children aged 4 and up.

    Leave the background empty ('.') unless the prompt asks for one - a pattern
    with no background is quicker to build and looks better on the board.
    """ }

    /// The shape the model must return. Enforced by the API, not by hope.
    ///
    /// `itemCounts` is false for OpenAI. Its strict Structured Outputs mode
    /// supports only a subset of JSON Schema and rejects minItems/maxItems
    /// outright - the whole request comes back 400 "Invalid schema", so the
    /// ChatGPT provider could never produce a single pattern. There the counts
    /// live in the descriptions, and `buildPattern` enforces them on the way
    /// in, which it does for both providers anyway.
    private func schema(width: Int, height: Int, itemCounts: Bool = true) -> [String: Any] {
        var palette: [String: Any] = [
            "type": "array",
            "description": "Between 2 and 16 bead ids from the supplied list, "
                + "in the order the row characters index them",
            "items": ["type": "string"]
        ]
        var rows: [String: Any] = [
            "type": "array",
            "description": "Exactly \(height) strings, each exactly \(width) characters",
            "items": ["type": "string"]
        ]
        var tags: [String: Any] = [
            "type": "array",
            "description": "Up to 6 short keywords",
            "items": ["type": "string"]
        ]
        if itemCounts {
            palette["minItems"] = 2
            palette["maxItems"] = 16
            rows["minItems"] = height
            rows["maxItems"] = height
            tags["maxItems"] = 6
        }
        return [
            "type": "object",
            "additionalProperties": false,
            "required": ["title", "palette", "rows", "difficulty", "tags"],
            "properties": [
                "title": ["type": "string",
                          "description": "Short name for the finished pattern, 1-4 words"],
                "palette": palette,
                "rows": rows,
                "difficulty": ["type": "string", "enum": ["easy", "medium", "hard"]],
                "tags": tags
            ]
        ]
    }

    // MARK: - Public API

    func generate(
        prompt: String,
        category: PatternCategory? = nil,
        gridSize: GridSize = .large
    ) async throws -> FusePattern {
        guard hasAPIKey else { throw AIError.noAPIKey }
        let catHint = category.map { " It belongs in the \($0.displayName) category." } ?? ""
        let msg = "Design a fuse bead pattern of: \(prompt).\(catHint) " +
            "The board is \(gridSize.width) wide and \(gridSize.height) tall."
        return try await callAPI(userMessage: msg, grid: gridSize,
                                 sourcePrompt: prompt, category: category ?? .custom)
    }

    func iterate(pattern: FusePattern, instruction: String) async throws -> FusePattern {
        guard hasAPIKey else { throw AIError.noAPIKey }
        // No size limit any more. The old one refused anything over 400 cells
        // because it pasted every cell in as "(x,y)=colorId" text; the board now
        // goes back as the same rows the model produces.
        let ids = pattern.palette.map(\.id)
        let rows = renderRows(pattern, ids: ids)
        let msg = """
        Here is an existing fuse bead pattern. Change it as follows: \(instruction)

        Title: \(pattern.title)
        Board: \(pattern.grid.width) wide, \(pattern.grid.height) tall
        Palette, in row-character order: \(ids.joined(separator: ", "))
        Rows:
        \(rows.joined(separator: "\n"))

        Return the complete updated pattern. Keep everything the instruction did
        not ask you to change.
        """
        var updated = try await callAPI(userMessage: msg, grid: pattern.grid,
                                        sourcePrompt: instruction, category: pattern.category)
        updated.id = pattern.id
        updated.title = pattern.title
        return updated
    }

    /// The pattern's cells as row strings, for handing back to the model.
    private func renderRows(_ p: FusePattern, ids: [String]) -> [String] {
        var grid = Array(repeating: Array(repeating: Character("."), count: p.grid.width),
                         count: p.grid.height)
        let chars = Array(FusePattern.rowChars)
        for c in p.cells {
            guard let id = c.colorId, let i = ids.firstIndex(of: id), i < chars.count,
                  c.y >= 0, c.y < p.grid.height, c.x >= 0, c.x < p.grid.width else { continue }
            grid[c.y][c.x] = chars[i]
        }
        return grid.map { String($0) }
    }

    // MARK: - Private

    private func callAPI(userMessage: String, grid: GridSize,
                         sourcePrompt: String, category: PatternCategory) async throws -> FusePattern {
        let text = try await requestText(user: userMessage, grid: grid)
        guard let data = text.data(using: .utf8),
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw AIError.invalidJSON("not an object")
        }
        return try buildPattern(obj, grid: grid, sourcePrompt: sourcePrompt, category: category)
    }

    /// Get the raw model text from whichever provider is selected.
    private func requestText(user: String, grid: GridSize) async throws -> String {
        switch provider {
        case .claude: return try await callClaude(user: user, grid: grid)
        case .openai: return try await callOpenAI(user: user, grid: grid)
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
            // Both providers use the same error envelope: {"error": {"message": ...}}
            var detail: String?
            if let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let err = root["error"] as? [String: Any] {
                detail = err["message"] as? String
            }
            throw AIError.httpError(http.statusCode, detail)
        }
        return data
    }

    private func callClaude(user: String, grid: GridSize) async throws -> String {
        var req = URLRequest(url: claudeURL)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue(apiKey, forHTTPHeaderField: "x-api-key")
        req.setValue("2023-06-01", forHTTPHeaderField: "anthropic-version")
        let body: [String: Any] = [
            "model": Self.claudeModel,
            // 4,096 could not finish a default board even in the compact
            // encoding once thinking tokens are counted.
            "max_tokens": 16000,
            "system": systemPrompt,
            // Laying a subject out on a grid is spatial reasoning, and it is what
            // the model is worst at when it answers straight away.
            "thinking": ["type": "adaptive"],
            "output_config": [
                "effort": "high",
                // Structured output, instead of asking for JSON in prose and
                // hunting for the outermost braces.
                "format": ["type": "json_schema",
                           "schema": schema(width: grid.width, height: grid.height)]
            ],
            "messages": [["role": "user", "content": user]]
        ]
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        let data = try await send(req)

        guard let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw AIError.noContent
        }
        // A refusal or a token cut-off is an HTTP 200 with an empty content
        // array; reading content[0] would surface as a confusing JSON error.
        switch root["stop_reason"] as? String {
        case "refusal":    throw AIError.refused
        case "max_tokens": throw AIError.truncated
        default:           break
        }
        // NOT content[0]. With thinking on, the first block is a thinking block
        // and the pattern is in a later text block.
        guard let blocks = root["content"] as? [[String: Any]],
              let text = blocks.first(where: { $0["type"] as? String == "text" })?["text"] as? String,
              !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw AIError.noContent
        }
        return text
    }

    private func callOpenAI(user: String, grid: GridSize) async throws -> String {
        var req = URLRequest(url: openAIURL)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        let body: [String: Any] = [
            "model": Self.openAIModel,
            "max_tokens": 16000,
            "response_format": [
                "type": "json_schema",
                "json_schema": ["name": "bead_pattern", "strict": true,
                                "schema": schema(width: grid.width, height: grid.height,
                                                 itemCounts: false)]
            ],
            "messages": [
                ["role": "system", "content": systemPrompt],
                ["role": "user", "content": user]
            ]
        ]
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        let data = try await send(req)
        struct R: Decodable {
            struct Choice: Decodable {
                struct Msg: Decodable { let content: String? }
                let message: Msg
                let finish_reason: String?
            }
            let choices: [Choice]
        }
        guard let r = try? JSONDecoder().decode(R.self, from: data),
              let choice = r.choices.first else {
            throw AIError.noContent
        }
        // Android reported this and iOS did not, so the same cut-off reply said
        // "try a smaller board" on one platform and "AI returned no content" on
        // the other - advice that leads nowhere.
        if choice.finish_reason == "length" { throw AIError.truncated }
        guard let t = choice.message.content,
              !t.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw AIError.noContent
        }
        return t
    }

    /// Turns the model's rows into a real pattern, or explains why it cannot.
    private func buildPattern(_ obj: [String: Any], grid: GridSize,
                              sourcePrompt: String, category: PatternCategory) throws -> FusePattern {
        guard let ids = obj["palette"] as? [String], ids.count >= 2 else {
            throw AIError.schemaViolation("A pattern needs at least two colours")
        }
        // Resolve against the REAL bead list. An invented id is the failure this
        // catches: a colour nobody sells cannot be bought or built.
        var beads: [PaletteColor] = []
        for id in ids {
            guard let bead = PaletteColor.full.first(where: { $0.id == id }) else {
                throw AIError.schemaViolation("'\(id)' is not a real bead colour")
            }
            beads.append(bead)
        }

        guard let rows = obj["rows"] as? [String] else {
            throw AIError.schemaViolation("No rows")
        }
        guard rows.count == grid.height else {
            throw AIError.schemaViolation("Expected \(grid.height) rows, got \(rows.count)")
        }
        let chars = Array(FusePattern.rowChars)
        var cells: [Cell] = []
        for (y, row) in rows.enumerated() {
            let line = Array(row)
            guard line.count == grid.width else {
                throw AIError.schemaViolation("Row \(y) is \(line.count) wide, expected \(grid.width)")
            }
            for (x, ch) in line.enumerated() {
                if ch == "." { continue }
                guard let i = chars.firstIndex(of: ch), i < beads.count else {
                    throw AIError.schemaViolation("Row \(y) uses '\(ch)', which is not a palette position")
                }
                cells.append(Cell(x: x, y: y, colorId: beads[i].id))
            }
        }
        guard !cells.isEmpty else { throw AIError.schemaViolation("The board came back empty") }

        let solid = dropFloatingIslands(cells)
        let usedIDs = Set(solid.compactMap(\.colorId))

        return FusePattern(
            id: UUID().uuidString,
            title: (obj["title"] as? String).flatMap { $0.isEmpty ? nil : $0 } ?? String(sourcePrompt.prefix(40)),
            category: category,
            createdBy: .ai,
            grid: grid,
            palette: beads.filter { usedIDs.contains($0.id) },
            cells: solid,
            difficulty: Difficulty(rawValue: obj["difficulty"] as? String ?? "") ?? .medium,
            tags: obj["tags"] as? [String] ?? [],
            sourcePrompt: sourcePrompt,
            version: 1
        )
    }

    /// Removes beads not attached to the main body of the pattern.
    ///
    /// Fused beads bond where their edges meet, so a bead touching the rest only
    /// at a corner - or not at all - falls off the moment the piece is lifted.
    /// Islands of three or more are kept: usually a deliberate detail such as an
    /// eye, which the maker can iron separately. Anything smaller is a stray.
    private func dropFloatingIslands(_ cells: [Cell]) -> [Cell] {
        struct P: Hashable { let x: Int; let y: Int }
        var filled = Set<P>()
        for c in cells { filled.insert(P(x: c.x, y: c.y)) }

        var seen = Set<P>()
        var islands: [[P]] = []
        for start in filled where !seen.contains(start) {
            var island: [P] = []
            var stack = [start]
            seen.insert(start)
            while let p = stack.popLast() {
                island.append(p)
                for (dx, dy) in [(1, 0), (-1, 0), (0, 1), (0, -1)] {
                    let n = P(x: p.x + dx, y: p.y + dy)
                    if filled.contains(n), !seen.contains(n) { seen.insert(n); stack.append(n) }
                }
            }
            islands.append(island)
        }
        guard islands.count > 1 else { return cells }

        let biggest = islands.map(\.count).max() ?? 0
        var keep = Set<P>()
        for island in islands where island.count >= 3 || island.count == biggest {
            keep.formUnion(island)
        }
        let solid = cells.filter { keep.contains(P(x: $0.x, y: $0.y)) }
        return solid.isEmpty ? cells : solid
    }
}
