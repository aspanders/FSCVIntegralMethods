package com.beadsnap.app.services

import com.beadsnap.app.data.model.BeadColor
import com.beadsnap.app.data.model.Cell
import com.beadsnap.app.data.model.CreatorType
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.model.GridSize
import com.beadsnap.app.data.model.PatternCategory
import kotlinx.coroutines.suspendCancellableCoroutine
import okhttp3.Call
import okhttp3.Callback
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.util.UUID
import java.util.concurrent.TimeUnit
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

sealed class AIError : Exception() {
    data object NoAPIKey : AIError() {
        override val message = "No API key set. Tap 'Set Up AI' to add your Claude or ChatGPT API key."
    }
    data class NetworkError(override val cause: Exception) : AIError() {
        override val message = "Network error: ${cause.message}"
    }
    data class HttpError(val code: Int) : AIError() {
        override val message = when (code) {
            401  -> "Invalid API key. Tap 'Set Up AI' to update it."
            400  -> "Bad request. Check your API key."
            429  -> "Rate limit reached. Please wait a moment and try again."
            else -> "Server error ($code). Please try again."
        }
    }
    data object NoContent : AIError() {
        override val message = "AI returned no content. Please try again."
    }
    /** The reply was cut off before the pattern was complete. */
    data object Truncated : AIError() {
        override val message = "The pattern came back unfinished. Try a smaller board."
    }
    data class InvalidJSON(val detail: String) : AIError() {
        override val message = "AI returned invalid JSON: $detail"
    }
    data class SchemaViolation(val detail: String) : AIError() {
        override val message = "Pattern validation failed: $detail"
    }
    data object Refused : AIError() {
        override val message = "The AI declined that request. Try describing something else."
    }
}

/**
 * The AI backend the user paired. Both call their provider over HTTPS with the
 * user's own key; keys live in EncryptedSharedPreferences (KeystoreHelper).
 */
enum class AIProvider(val displayName: String, val keyAccount: String, val keyHint: String) {
    CLAUDE("Claude (Anthropic)", "claude_api_key", "sk-ant-…"),
    OPENAI("ChatGPT (OpenAI)", "openai_api_key", "sk-…");

    companion object {
        fun from(s: String?): AIProvider = entries.firstOrNull { it.name == s } ?: CLAUDE
    }
}

/**
 * Turns a written prompt into a bead pattern.
 *
 * ## Why the board comes back as ROWS and not as a list of cells
 *
 * The first version asked the model for `cells: [{"x":..,"y":..,"colorId":".."}]`.
 * That object costs about ten tokens, so a 32x32 board - the app's default -
 * needs roughly 6,700 output tokens once it is two-thirds filled, against a
 * max_tokens of 4,096. The JSON was therefore cut off mid-array on every
 * ordinary request, the brace-matching extractor handed the decoder a truncated
 * object, and the user got "AI returned invalid JSON". The feature could only
 * succeed on a board small enough or sparse enough to fit, which is not the
 * default and not what anybody asks for.
 *
 * The same board as one string per row costs about 365 tokens - eighteen times
 * less - and it is the encoding the app already ships and decodes
 * ([FusePattern.rows]). It is also a far easier thing for a model to produce
 * well: laying out a subject as rows of characters is drawing, whereas emitting
 * six hundred coordinate triples in the right order is bookkeeping.
 *
 * ## Why the palette is fixed
 *
 * The model used to invent its own `{id, name, hex}` entries. A pattern whose
 * colours are not beads you can buy is not a bead pattern - the shopping list
 * names things that do not exist, and the shades drift away from what Perler
 * and Hama actually sell. The model now picks ids out of [BeadColor.palette]
 * and the app resolves them; anything it invents is rejected.
 */
class AIPatternService private constructor() {

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)   // thinking models take longer to first byte
        .build()

    private val providerAccount = "ai_provider"

    /** Which provider requests use. Persisted (not sensitive), defaults to Claude. */
    var provider: AIProvider
        get() = AIProvider.from(KeystoreHelper.load(providerAccount))
        set(value) { KeystoreHelper.save(providerAccount, value.name) }

    // Per-provider keys, so both can be stored and swapped freely.
    fun apiKey(p: AIProvider): String = KeystoreHelper.load(p.keyAccount) ?: ""
    fun setApiKey(p: AIProvider, value: String) {
        if (value.isBlank()) KeystoreHelper.delete(p.keyAccount)
        else KeystoreHelper.save(p.keyAccount, value.trim())
    }
    fun hasKey(p: AIProvider): Boolean = apiKey(p).isNotBlank()

    var apiKey: String
        get() = apiKey(provider)
        set(value) { setApiKey(provider, value) }

    val hasAPIKey: Boolean get() = apiKey.isNotBlank()

    // ── The prompt ───────────────────────────────────────────────────────────

    /** Every real bead, as the model is allowed to refer to them. */
    private val paletteList: String =
        BeadColor.palette.joinToString("\n") { "  ${it.id} = ${it.name} ${it.hex}" }

    private val systemPrompt = """
        You design fuse bead patterns (Perler / Hama). A pattern is a rectangular
        peg board; the maker places one bead per peg, then irons them so touching
        beads fuse together.

        You return the board as ROWS OF CHARACTERS - one string per row of the
        board, one character per peg:
          - '.' means leave that peg empty.
          - '0'-'9' then 'a'-'z' then 'A'-'Z' select a colour, by its position in
            the palette you chose: '0' is the first colour, '1' the second, and
            so on.
        Every row string must be exactly `width` characters long, and there must
        be exactly `height` of them. This is a picture drawn in text - lay the
        subject out on the grid and read your own rows back to check the shape
        before you answer.

        Choose colours only from this list of real beads, by id:
        $paletteList

        What makes a bead pattern good, in priority order:

        1. RECOGNISABLE AT THIS SIZE. A 16x16 board holds a symbol, not a scene.
           Cover the title and ask whether the shape alone says what it is. Bold
           silhouettes beat detail. If the subject will not read at the size
           asked for, draw the most recognisable PART of it filling the board -
           a face rather than a whole animal - instead of shrinking the whole
           thing into mush.
        2. BUILDABLE. Beads fuse where their EDGES meet, not at their corners, so
           every filled peg must touch another filled peg up, down, left or right.
           A bead joined to the rest only diagonally falls off when lifted. One
           connected piece, no floating islands. A one-bead-wide leg, antenna or
           stem is fine - it fuses into a solid strand.
        3. FLAT COLOUR. No gradients, no dithering, no anti-aliasing, no shading
           ramps. Large blocks of one colour. Use an outline in a darker bead
           where the subject needs to stand out.
        4. FEW COLOURS. Two to eight is normal. Every extra colour is another
           bag the maker has to own.
        5. CENTRED, with the subject filling most of the board. Do not leave a
           wide empty margin.
        6. Suitable for children aged 4 and up.

        Leave the background empty ('.') unless the prompt asks for one - a
        pattern with no background is quicker to build and looks better on the
        board.
    """.trimIndent()

    /** The shape the model must return. Enforced by the API, not by hope. */
    private fun schema(width: Int, height: Int): JSONObject = JSONObject().apply {
        put("type", "object")
        put("additionalProperties", false)
        put("required", JSONArray(listOf("title", "palette", "rows", "difficulty", "tags")))
        put("properties", JSONObject().apply {
            put("title", JSONObject().apply {
                put("type", "string")
                put("description", "Short name for the finished pattern, 1-4 words")
            })
            put("palette", JSONObject().apply {
                put("type", "array")
                put("minItems", 2)
                put("maxItems", 16)
                put("description", "Bead ids from the supplied list, in the order the row characters index them")
                put("items", JSONObject().put("type", "string"))
            })
            put("rows", JSONObject().apply {
                put("type", "array")
                put("minItems", height)
                put("maxItems", height)
                put("description", "Exactly $height strings, each exactly $width characters")
                put("items", JSONObject().put("type", "string"))
            })
            put("difficulty", JSONObject().apply {
                put("type", "string")
                put("enum", JSONArray(listOf("easy", "medium", "hard")))
            })
            put("tags", JSONObject().apply {
                put("type", "array")
                put("maxItems", 6)
                put("items", JSONObject().put("type", "string"))
            })
        })
    }

    // ── Public API ───────────────────────────────────────────────────────────

    @Throws(AIError::class)
    suspend fun generate(
        prompt: String,
        category: PatternCategory? = null,
        gridSize: GridSize = GridSize.large
    ): FusePattern {
        if (!hasAPIKey) throw AIError.NoAPIKey
        val catHint = category?.let { " It belongs in the ${it.displayName} category." } ?: ""
        val msg = "Design a fuse bead pattern of: $prompt.$catHint " +
            "The board is ${gridSize.width} wide and ${gridSize.height} tall."
        return callAPI(msg, gridSize, prompt, category ?: PatternCategory.custom)
    }

    @Throws(AIError::class)
    suspend fun iterate(pattern: FusePattern, instruction: String): FusePattern {
        if (!hasAPIKey) throw AIError.NoAPIKey
        // No size limit any more. The old one refused anything over 400 cells
        // because it pasted every cell in as "(x,y)=colorId" text; the board
        // now goes back as the same rows the model produces, so a full 32x32
        // costs about 365 tokens each way.
        val ids = pattern.palette.map { it.id }
        val rows = renderRows(pattern, ids)
        val msg = """
            Here is an existing fuse bead pattern. Change it as follows: $instruction

            Title: ${pattern.title}
            Board: ${pattern.grid.width} wide, ${pattern.grid.height} tall
            Palette, in row-character order: ${ids.joinToString(", ")}
            Rows:
            ${rows.joinToString("\n            ")}

            Return the complete updated pattern. Keep everything the instruction
            did not ask you to change.
        """.trimIndent()
        val updated = callAPI(msg, pattern.grid, instruction, pattern.category)
        return updated.copy(id = pattern.id, title = pattern.title)
    }

    /** The pattern's cells as row strings, for handing back to the model. */
    private fun renderRows(p: FusePattern, ids: List<String>): List<String> {
        val grid = Array(p.grid.height) { CharArray(p.grid.width) { '.' } }
        for (c in p.cells) {
            val i = ids.indexOf(c.colorId ?: continue)
            if (i >= 0 && c.y in grid.indices && c.x in 0 until p.grid.width) {
                grid[c.y][c.x] = FusePattern.CHARS[i]
            }
        }
        return grid.map { String(it) }
    }

    // ── Transport ────────────────────────────────────────────────────────────

    private suspend fun callAPI(
        userMessage: String,
        grid: GridSize,
        sourcePrompt: String,
        category: PatternCategory
    ): FusePattern = suspendCancellableCoroutine { cont ->
        val call = client.newCall(buildRequest(userMessage, grid))
        cont.invokeOnCancellation { call.cancel() }
        call.enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                if (call.isCanceled()) return
                cont.resumeWithException(AIError.NetworkError(e))
            }

            override fun onResponse(call: Call, response: Response) {
                val result = try {
                    Result.success(parseResponse(response, grid, sourcePrompt, category))
                } catch (e: Exception) {
                    Result.failure(e)
                }
                result.fold(
                    onSuccess = { cont.resume(it) },
                    onFailure = { cont.resumeWithException(it) }
                )
            }
        })
    }

    private fun buildRequest(userMessage: String, grid: GridSize): Request = when (provider) {
        AIProvider.CLAUDE -> claudeRequest(userMessage, grid)
        AIProvider.OPENAI -> openAIRequest(userMessage, grid)
    }

    private fun claudeRequest(userMessage: String, grid: GridSize): Request {
        val body = JSONObject().apply {
            put("model", CLAUDE_MODEL)
            // 4,096 was not enough to finish a default board even in the compact
            // encoding once thinking tokens are counted. 16,000 is the
            // recommended figure for a non-streaming request: comfortably above
            // what this task needs, and still under the client HTTP timeout.
            put("max_tokens", 16000)
            put("system", systemPrompt)
            // Laying a subject out on a grid is spatial reasoning, and it is
            // what the model is worst at when it answers straight away.
            put("thinking", JSONObject().put("type", "adaptive"))
            put("output_config", JSONObject().apply {
                put("effort", "high")
                // Structured output. The old code asked for JSON in prose and
                // then hunted for the outermost braces, which also had to strip
                // markdown fences by dropping the first and last LINE - and that
                // ate real JSON whenever the model closed the fence differently.
                put("format", JSONObject().apply {
                    put("type", "json_schema")
                    put("schema", schema(grid.width, grid.height))
                })
            })
            put("messages", JSONArray().apply {
                put(JSONObject().apply {
                    put("role", "user")
                    put("content", userMessage)
                })
            })
        }
        return Request.Builder()
            .url("https://api.anthropic.com/v1/messages")
            .post(body.toString().toRequestBody("application/json".toMediaType()))
            .header("x-api-key", apiKey)
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .build()
    }

    private fun openAIRequest(userMessage: String, grid: GridSize): Request {
        val body = JSONObject().apply {
            put("model", OPENAI_MODEL)
            put("max_tokens", 16000)
            put("response_format", JSONObject().apply {
                put("type", "json_schema")
                put("json_schema", JSONObject().apply {
                    put("name", "bead_pattern")
                    put("strict", true)
                    put("schema", schema(grid.width, grid.height))
                })
            })
            put("messages", JSONArray().apply {
                put(JSONObject().put("role", "system").put("content", systemPrompt))
                put(JSONObject().put("role", "user").put("content", userMessage))
            })
        }
        return Request.Builder()
            .url("https://api.openai.com/v1/chat/completions")
            .post(body.toString().toRequestBody("application/json".toMediaType()))
            .header("Authorization", "Bearer $apiKey")
            .header("content-type", "application/json")
            .build()
    }

    // ── Response ─────────────────────────────────────────────────────────────

    private fun parseResponse(
        response: Response,
        grid: GridSize,
        sourcePrompt: String,
        category: PatternCategory
    ): FusePattern {
        response.use { resp ->
            if (!resp.isSuccessful) throw AIError.HttpError(resp.code)
            val raw = resp.body?.string() ?: throw AIError.NoContent
            val root = try { JSONObject(raw) } catch (_: Exception) { throw AIError.NoContent }

            val text: String = when (provider) {
                AIProvider.CLAUDE -> {
                    when (root.optString("stop_reason")) {
                        // A refusal is an HTTP 200 with an empty content array;
                        // reading content[0] would throw a confusing JSON error.
                        "refusal"    -> throw AIError.Refused
                        "max_tokens" -> throw AIError.Truncated
                    }
                    // NOT content[0]. With thinking on, the first block is a
                    // thinking block and the pattern is in a later text block.
                    val blocks = root.optJSONArray("content") ?: throw AIError.NoContent
                    (0 until blocks.length())
                        .map { blocks.getJSONObject(it) }
                        .firstOrNull { it.optString("type") == "text" }
                        ?.optString("text")
                        ?: throw AIError.NoContent
                }
                AIProvider.OPENAI -> {
                    val choice = root.optJSONArray("choices")?.optJSONObject(0)
                        ?: throw AIError.NoContent
                    if (choice.optString("finish_reason") == "length") throw AIError.Truncated
                    choice.optJSONObject("message")?.optString("content")
                        ?: throw AIError.NoContent
                }
            }
            if (text.isBlank()) throw AIError.NoContent

            val obj = try { JSONObject(text) }
            catch (e: Exception) { throw AIError.InvalidJSON(e.message ?: "not an object") }

            return buildPattern(obj, grid, sourcePrompt, category)
        }
    }

    /** Turns the model's rows into a real pattern, or explains why it cannot. */
    private fun buildPattern(
        obj: JSONObject,
        grid: GridSize,
        sourcePrompt: String,
        category: PatternCategory
    ): FusePattern {
        val ids = obj.optJSONArray("palette")?.let { arr ->
            (0 until arr.length()).map { arr.getString(it) }
        } ?: throw AIError.SchemaViolation("No palette")
        if (ids.size < 2) throw AIError.SchemaViolation("A pattern needs at least two colours")

        // Resolve against the REAL bead list. An invented id is the failure
        // this catches: a colour nobody sells cannot be bought or built.
        val beads = ids.map { id ->
            BeadColor.palette.firstOrNull { it.id == id }
                ?: throw AIError.SchemaViolation("'$id' is not a real bead colour")
        }

        val rows = obj.optJSONArray("rows")?.let { arr ->
            (0 until arr.length()).map { arr.getString(it) }
        } ?: throw AIError.SchemaViolation("No rows")
        if (rows.size != grid.height)
            throw AIError.SchemaViolation("Expected ${grid.height} rows, got ${rows.size}")
        rows.forEachIndexed { y, r ->
            if (r.length != grid.width)
                throw AIError.SchemaViolation("Row $y is ${r.length} wide, expected ${grid.width}")
        }

        val cells = ArrayList<Cell>()
        for (y in rows.indices) {
            for ((x, ch) in rows[y].withIndex()) {
                if (ch == '.') continue
                val i = FusePattern.CHARS.indexOf(ch)
                if (i < 0 || i >= beads.size)
                    throw AIError.SchemaViolation("Row $y uses '$ch', which is not a palette position")
                cells.add(Cell(x, y, beads[i].id))
            }
        }
        if (cells.isEmpty()) throw AIError.SchemaViolation("The board came back empty")

        val solid = dropFloatingIslands(cells, grid)

        return FusePattern(
            id = UUID.randomUUID().toString(),
            title = obj.optString("title").ifBlank { sourcePrompt.take(40) },
            category = category,
            createdBy = CreatorType.ai,
            grid = grid,
            palette = beads.filter { b -> solid.any { it.colorId == b.id } },
            cells = solid,
            difficulty = com.beadsnap.app.data.model.Difficulty.entries
                .firstOrNull { it.name == obj.optString("difficulty") }
                ?: com.beadsnap.app.data.model.Difficulty.medium,
            tags = obj.optJSONArray("tags")?.let { arr ->
                (0 until arr.length()).map { arr.getString(it) }
            } ?: emptyList(),
            sourcePrompt = sourcePrompt,
            version = 1
        )
    }

    /**
     * Removes beads that are not attached to the main body of the pattern.
     *
     * Fused beads bond where their edges meet, so a bead touching the rest only
     * at a corner - or not at all - falls off the moment the piece is lifted.
     * The prompt asks for one connected piece; this is what happens when the
     * model does not manage it. Islands of three beads or more are kept: they
     * are usually a deliberate detail such as a dot of an eye, and the maker can
     * iron them as a separate piece. Anything smaller is a stray.
     */
    private fun dropFloatingIslands(cells: List<Cell>, grid: GridSize): List<Cell> {
        val filled = HashMap<Long, Cell>(cells.size * 2)
        fun key(x: Int, y: Int) = x.toLong() * 100000L + y
        for (c in cells) filled[key(c.x, c.y)] = c

        val seen = HashSet<Long>()
        val islands = ArrayList<List<Long>>()
        for (start in filled.keys) {
            if (!seen.add(start)) continue
            val island = ArrayList<Long>()
            val stack = ArrayDeque<Long>().apply { add(start) }
            while (stack.isNotEmpty()) {
                val k = stack.removeLast()
                island.add(k)
                val c = filled[k] ?: continue
                for ((dx, dy) in NEIGHBOURS) {
                    val n = key(c.x + dx, c.y + dy)
                    if (filled.containsKey(n) && seen.add(n)) stack.add(n)
                }
            }
            islands.add(island)
        }
        if (islands.size <= 1) return cells

        val biggest = islands.maxOf { it.size }
        val keep = islands.filter { it.size >= MIN_ISLAND || it.size == biggest }
            .flatten().toHashSet()
        val solid = cells.filter { keep.contains(key(it.x, it.y)) }
        return if (solid.isEmpty()) cells else solid
    }

    companion object {
        /**
         * Spatial layout is the hardest part of this task and the part a small
         * model is worst at, so this is deliberately not a cheap model. The user
         * pays for their own key, so the choice is theirs to change - but the
         * default should be the one that produces a pattern worth building.
         */
        const val CLAUDE_MODEL = "claude-opus-5"

        /** Not verified against OpenAI's current lineup - review before relying on it. */
        const val OPENAI_MODEL = "gpt-4o"

        private const val MIN_ISLAND = 3
        private val NEIGHBOURS = listOf(1 to 0, -1 to 0, 0 to 1, 0 to -1)

        val shared: AIPatternService by lazy { AIPatternService() }
    }
}
