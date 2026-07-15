package com.beadsnap.app.services

import com.beadsnap.app.data.model.BeadColor
import com.beadsnap.app.data.model.Cell
import com.beadsnap.app.data.model.CreatorType
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.model.GridSize
import com.beadsnap.app.data.model.PatternCategory
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.serialization.json.Json
import okhttp3.Call
import okhttp3.Callback
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

sealed class AIError : Exception() {
    data object NoAPIKey : AIError() {
        override val message = "No API key set. Tap 'Set Up AI' to add your Claude API key."
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
    data class InvalidJSON(val detail: String) : AIError() {
        override val message = "AI returned invalid JSON: $detail"
    }
    data class SchemaViolation(val detail: String) : AIError() {
        override val message = "Pattern validation failed: $detail"
    }
    data object TooComplex : AIError() {
        override val message = "Pattern is too large for AI refinement. Use a smaller grid or fill fewer cells."
    }
}

class AIPatternService private constructor() {

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    private val json = Json { ignoreUnknownKeys = true; isLenient = true }
    private val apiKeyAccount = "claude_api_key"

    var apiKey: String
        get() = KeystoreHelper.load(apiKeyAccount) ?: ""
        set(value) {
            if (value.isBlank()) KeystoreHelper.delete(apiKeyAccount)
            else KeystoreHelper.save(apiKeyAccount, value.trim())
        }

    val hasAPIKey: Boolean get() = apiKey.isNotBlank()

    private val systemPrompt = """
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
    """.trimIndent()

    @Throws(AIError::class)
    suspend fun generate(
        prompt: String,
        category: PatternCategory? = null,
        gridSize: GridSize = GridSize.large
    ): FusePattern {
        if (!hasAPIKey) throw AIError.NoAPIKey
        val catHint = category?.let { " Category: ${it.name}." } ?: ""
        val msg = "Create a fuse bead pattern of: $prompt.$catHint Grid: ${gridSize.width}x${gridSize.height}."
        return callAPI(msg)
    }

    @Throws(AIError::class)
    suspend fun iterate(pattern: FusePattern, instruction: String): FusePattern {
        if (!hasAPIKey) throw AIError.NoAPIKey
        if (pattern.cells.size > 400) throw AIError.TooComplex
        val paletteDesc = pattern.palette.joinToString { "${it.id}: ${it.name} (${it.hex})" }
        val cellsDesc = pattern.cells.joinToString(" ") { "(${it.x},${it.y})=${it.colorId ?: "?"}" }
        val msg = """
            Modify this fuse bead pattern per this instruction: $instruction
            Grid: ${pattern.grid.width}×${pattern.grid.height}. Title: ${pattern.title}. Category: ${pattern.category.name}.
            Palette: $paletteDesc
            Filled cells as (x,y)=colorId: $cellsDesc
            Return only the full updated JSON object matching the schema.
        """.trimIndent()
        val updated = callAPI(msg)
        return updated.copy(id = pattern.id)
    }

    // Non-blocking: enqueues the call and cancels it if the coroutine is cancelled,
    // so tapping Cancel aborts the network request instead of letting it run out.
    private suspend fun callAPI(userMessage: String): FusePattern =
        suspendCancellableCoroutine { cont ->
            val call = client.newCall(buildRequest(userMessage))
            cont.invokeOnCancellation { call.cancel() }
            call.enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    if (call.isCanceled()) return
                    cont.resumeWithException(AIError.NetworkError(e))
                }

                override fun onResponse(call: Call, response: Response) {
                    val result = try {
                        Result.success(parseResponse(response))
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

    private fun buildRequest(userMessage: String): Request {
        val bodyJson = JSONObject().apply {
            put("model", "claude-haiku-4-5")
            put("max_tokens", 4096)
            put("system", systemPrompt)
            put("messages", org.json.JSONArray().apply {
                put(JSONObject().apply {
                    put("role", "user")
                    put("content", userMessage)
                })
            })
        }
        return Request.Builder()
            .url("https://api.anthropic.com/v1/messages")
            .post(bodyJson.toString().toRequestBody("application/json".toMediaType()))
            .header("x-api-key", apiKey)
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .build()
    }

    private fun parseResponse(response: Response): FusePattern {
        response.use { resp ->
            if (!resp.isSuccessful) throw AIError.HttpError(resp.code)
            val body = resp.body?.string() ?: throw AIError.NoContent
            val contentText = try {
                JSONObject(body)
                    .getJSONArray("content")
                    .getJSONObject(0)
                    .getString("text")
            } catch (_: Exception) { throw AIError.NoContent }

            if (contentText.isBlank()) throw AIError.NoContent

            val jsonData = extractJson(contentText)
            val pattern = try { json.decodeFromString<FusePattern>(jsonData) }
            catch (e: Exception) { throw AIError.InvalidJSON(e.message ?: "unknown") }

            return validate(pattern)
        }
    }

    private fun extractJson(text: String): String {
        var s = text.trim()
        if (s.startsWith("```")) {
            s = s.lines().drop(1).dropLast(1).joinToString("\n")
        }
        val start = s.indexOfFirst { it == '{' }
        val end = s.indexOfLast { it == '}' }
        if (start < 0 || end < 0) throw AIError.InvalidJSON("No JSON object found")
        return s.substring(start, end + 1)
    }

    private fun validate(p: FusePattern): FusePattern {
        if (p.grid.width < 8 || p.grid.width > 64 || p.grid.height < 8 || p.grid.height > 64)
            throw AIError.SchemaViolation("Grid ${p.grid.width}×${p.grid.height} out of 8–64 range")
        if (p.palette.size < 4 || p.palette.size > 16)
            throw AIError.SchemaViolation("Palette must have 4–16 colors, got ${p.palette.size}")
        val ids = p.palette.map { it.id }.toSet()
        for (cell in p.cells) {
            if (cell.colorId != null && cell.colorId !in ids)
                throw AIError.SchemaViolation("Cell references unknown colorId '${cell.colorId}'")
            if (cell.x < 0 || cell.x >= p.grid.width || cell.y < 0 || cell.y >= p.grid.height)
                throw AIError.SchemaViolation("Cell (${cell.x},${cell.y}) out of bounds")
        }
        // Deduplicate cells: last-writer-wins
        val seen = mutableSetOf<String>()
        val deduped = p.cells.reversed().filter { seen.add("${it.x},${it.y}") }.reversed()
        return p.copy(cells = deduped)
    }

    companion object {
        val shared: AIPatternService by lazy { AIPatternService() }
    }
}
