import com.beadsnap.app.data.model.BeadColor
import com.beadsnap.app.data.model.GridSize
import com.beadsnap.app.services.AIPatternService
import com.beadsnap.app.services.AIProvider
import com.beadsnap.app.services.KeystoreHelper
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeoutOrNull
import org.json.JSONArray
import org.json.JSONObject

/**
 * Drives AIPatternService against the okhttp / org.json stubs.
 *
 * The AI path had never been exercised at all: nothing compiled it off-device,
 * so nothing could notice that its default request could not succeed. A 32x32
 * board - the app's default - needs roughly 6,700 output tokens as a list of
 * per-cell JSON objects, against a max_tokens of 4,096, so the reply was cut
 * off and the user got "AI returned invalid JSON" for every ordinary prompt.
 *
 * These checks pin the shape of what goes out and what comes back.
 */

private var failures = 0

private fun check(name: String, ok: Boolean, detail: String = "") {
    println("  " + (if (ok) "PASS" else "FAIL") + "  " + name +
        (if (ok || detail.isEmpty()) "" else " - " + detail))
    if (!ok) failures++
}

/** A model reply in the shape the API actually returns it. */
private fun claudeReply(pattern: JSONObject, withThinking: Boolean = true): String {
    val content = JSONArray()
    if (withThinking) {
        content.put(JSONObject().put("type", "thinking").put("thinking", "laying out the grid..."))
    }
    content.put(JSONObject().put("type", "text").put("text", pattern.toString()))
    return JSONObject()
        .put("stop_reason", "end_turn")
        .put("content", content)
        .toString()
}

private fun pattern(rows: List<String>, palette: List<String>): JSONObject =
    JSONObject()
        .put("title", "Test")
        .put("palette", JSONArray(palette))
        .put("rows", JSONArray(rows))
        .put("difficulty", "easy")
        .put("tags", JSONArray(listOf("test")))

/** A solid block, so the connectivity pass has nothing to complain about. */
private fun solid(w: Int, h: Int, ch: Char = '0'): List<String> =
    List(h) { String(CharArray(w) { ch }) }

fun main() = runBlocking {
    val svc = AIPatternService.shared
    svc.provider = AIProvider.CLAUDE
    KeystoreHelper.save("claude_api_key", "sk-ant-test")

    // ── what goes out ────────────────────────────────────────────────────────
    println("==> the request body")

    val grid = GridSize.large
    val probe = svc.javaClass.getDeclaredMethod(
        "claudeRequest", String::class.java, GridSize::class.java
    ).apply { isAccessible = true }
    val req = probe.invoke(svc, "a red heart", grid) as okhttp3.Request
    val body = JSONObject(req.bodyText)

    check("uses the model the skill mandates",
        body.optString("model") == AIPatternService.CLAUDE_MODEL &&
            AIPatternService.CLAUDE_MODEL == "claude-opus-5",
        "got " + body.optString("model"))

    check("max_tokens is no longer 4096",
        body.optInt("max_tokens") >= 16000,
        "got " + body.optInt("max_tokens") + " - a 32x32 board does not fit in 4096")

    check("adaptive thinking is on",
        body.optJSONObject("thinking")?.optString("type") == "adaptive")

    check("budget_tokens is absent (400s on this model)",
        body.optJSONObject("thinking")?.has("budget_tokens") != true)

    check("no temperature (removed on this model)", !body.has("temperature"))

    val fmt = body.optJSONObject("output_config")?.optJSONObject("format")
    check("structured output is requested",
        fmt?.optString("type") == "json_schema")

    val schema = fmt?.optJSONObject("schema")
    val props = schema?.optJSONObject("properties")
    check("the schema asks for rows, not per-cell objects",
        props?.has("rows") == true && props.has("cells") != true)

    check("the schema pins the row count to the board height",
        props?.optJSONObject("rows")?.optInt("minItems") == grid.height &&
            props.optJSONObject("rows")?.optInt("maxItems") == grid.height)

    check("the system prompt offers the real bead list",
        body.optString("system").contains("light_blue = Light Blue") &&
            body.optString("system").contains("#"))

    check("the system prompt states the fusing rule",
        body.optString("system").contains("EDGES meet"))

    // ── what comes back ──────────────────────────────────────────────────────
    println("==> the response")

    val client = svc.javaClass.getDeclaredField("client").apply { isAccessible = true }
        .get(svc) as okhttp3.OkHttpClient

    suspend fun generate(reply: String): Result<com.beadsnap.app.data.model.FusePattern> {
        client.nextResponse = okhttp3.Response(200, reply)
        return runCatching { svc.generate("a red heart", null, grid) }
    }

    val good = pattern(solid(grid.width, grid.height), listOf("red"))
        .put("palette", JSONArray(listOf("red", "white")))
    val ok = generate(claudeReply(good))
    check("a thinking block before the text does not break parsing",
        ok.isSuccess, ok.exceptionOrNull()?.message ?: "")
    check("every cell of a full board is decoded",
        ok.getOrNull()?.cells?.size == grid.width * grid.height,
        "got " + ok.getOrNull()?.cells?.size)
    check("the palette resolves to real beads",
        ok.getOrNull()?.palette?.all { b -> BeadColor.palette.any { it.id == b.id } } == true)

    val invented = generate(claudeReply(
        pattern(solid(grid.width, grid.height), listOf("unicorn_sparkle", "red"))))
    check("a colour that is not a real bead is rejected",
        invented.isFailure &&
            invented.exceptionOrNull()?.message?.contains("not a real bead") == true,
        invented.exceptionOrNull()?.message ?: "accepted it")

    val shortRows = generate(claudeReply(
        pattern(solid(grid.width, grid.height - 3), listOf("red", "white"))))
    check("a board with too few rows is rejected",
        shortRows.isFailure, "accepted a short board")

    val ragged = generate(claudeReply(pattern(
        solid(grid.width, grid.height).toMutableList().also { it[4] = "01" },
        listOf("red", "white"))))
    check("a ragged row is rejected", ragged.isFailure, "accepted a ragged row")

    val truncated = generate(JSONObject()
        .put("stop_reason", "max_tokens")
        .put("content", JSONArray()).toString())
    check("a cut-off reply says so instead of 'invalid JSON'",
        truncated.exceptionOrNull()?.message?.contains("unfinished") == true,
        truncated.exceptionOrNull()?.message ?: "")

    val refused = generate(JSONObject()
        .put("stop_reason", "refusal")
        .put("content", JSONArray()).toString())
    check("a refusal is reported as a refusal",
        refused.exceptionOrNull()?.message?.contains("declined") == true,
        refused.exceptionOrNull()?.message ?: "")

    // ── buildability ─────────────────────────────────────────────────────────
    println("==> buildability")

    // A body, plus one bead marooned in the corner. Fused beads bond edge to
    // edge, so that bead falls off the finished piece.
    val withStray = solid(grid.width, grid.height, '.').toMutableList()
    for (y in 4 until 12) withStray[y] = buildString {
        repeat(grid.width) { x -> append(if (x in 4 until 12) '0' else '.') }
    }
    withStray[0] = "0" + ".".repeat(grid.width - 1)
    val cleaned = generate(claudeReply(pattern(withStray, listOf("red", "white"))))
    check("a floating single bead is dropped",
        cleaned.getOrNull()?.cells?.none { it.x == 0 && it.y == 0 } == true,
        "the stray survived")
    check("the body of the pattern is kept",
        (cleaned.getOrNull()?.cells?.size ?: 0) == 64,
        "got " + cleaned.getOrNull()?.cells?.size + " of 64")

    // ── failures the user has to be able to act on ───────────────────────────
    println("==> errors")

    // A 400 with a real explanation. This used to be flattened to "Bad request.
    // Check your API key", which is the wrong advice for every 400 that is not
    // about the key - an out-of-credit account, a schema the provider rejects.
    client.nextResponse = okhttp3.Response(400, JSONObject().put("error",
        JSONObject().put("message", "your credit balance is too low")).toString())
    val http400 = runCatching { svc.generate("a red heart", null, grid) }
    check("an HTTP error repeats what the provider said",
        http400.exceptionOrNull()?.message?.contains("credit balance is too low") == true,
        http400.exceptionOrNull()?.message ?: "")

    check("a 401 still tells the user to fix their key", run {
        client.nextResponse = okhttp3.Response(401, "")
        runCatching { svc.generate("a red heart", null, grid) }
            .exceptionOrNull()?.message?.contains("API key") == true
    })

    // The body throws WHILE the callback is reading it - a dropped link, or the
    // read timeout expiring part way through. OkHttp does not call onFailure for
    // anything thrown inside onResponse, so a handler that lets it escape never
    // resumes and generate() hangs for the life of the process. The timeout is
    // the whole check: without it this test would not finish.
    client.nextResponse = okhttp3.Response(200, "",
        java.io.IOException("unexpected end of stream"))
    val hung = withTimeoutOrNull(3_000) {
        runCatching { svc.generate("a red heart", null, grid) }
    }
    check("a body that fails mid-read still finishes the call",
        hung != null && hung.isFailure,
        if (hung == null) "generate() never returned" else "it succeeded on a broken body")

    // And the case that actually escaped: string() buffers the whole body, so
    // it can throw OutOfMemoryError, which is an Error and NOT an Exception. A
    // callback catching Exception lets that straight out, and OkHttp only logs
    // it - so the continuation is never resumed at all.
    client.nextResponse = okhttp3.Response(200, "", OutOfMemoryError("Failed to allocate"))
    val oom = withTimeoutOrNull(3_000) {
        runCatching { svc.generate("a red heart", null, grid) }
    }
    check("an Error from the body does not strand the caller forever",
        oom != null && oom.isFailure,
        if (oom == null) "generate() never returned - the callback caught Exception, not Throwable"
        else "it succeeded on a body that could not be read")

    // ── the other provider ───────────────────────────────────────────────────
    println("==> openai request")

    val oaProbe = svc.javaClass.getDeclaredMethod(
        "openAIRequest", String::class.java, GridSize::class.java
    ).apply { isAccessible = true }
    val oaBody = JSONObject((oaProbe.invoke(svc, "a red heart", grid) as okhttp3.Request).bodyText)
    val oaSchema = oaBody.optJSONObject("response_format")
        ?.optJSONObject("json_schema")?.optJSONObject("schema")
    val oaProps = oaSchema?.optJSONObject("properties")

    // OpenAI's strict Structured Outputs mode supports only a subset of JSON
    // Schema, and rejects minItems/maxItems with a 400 "Invalid schema" - so
    // sharing the Claude schema verbatim meant the ChatGPT provider could not
    // produce a single pattern, ever.
    check("the openai schema carries no keyword strict mode rejects",
        oaProps?.optJSONObject("rows")?.has("minItems") != true &&
            oaProps?.optJSONObject("rows")?.has("maxItems") != true &&
            oaProps?.optJSONObject("palette")?.has("minItems") != true &&
            oaProps?.optJSONObject("tags")?.has("maxItems") != true)

    // Strict mode also requires every property to be listed in `required` and
    // additionalProperties to be false.
    check("the openai schema still satisfies strict mode",
        oaSchema?.optBoolean("additionalProperties", true) == false &&
            (oaSchema.optJSONArray("required")?.length() ?: 0) ==
                (oaProps?.length() ?: -1))

    // The row count has to survive somewhere, since the schema can no longer
    // carry it. buildPattern enforces it; the description tells the model.
    check("the openai schema still states the row count",
        oaProps?.optJSONObject("rows")?.optString("description")
            ?.contains("Exactly " + grid.height) == true)

    println(if (failures == 0) "AI pattern service checks pass" else "$failures FAILED")
    if (failures > 0) kotlin.system.exitProcess(1)
}
