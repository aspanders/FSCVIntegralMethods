package com.beadsnap.app.data.store

import android.content.Context
import com.beadsnap.app.data.model.CreatorType
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.model.PatternCategory
import com.beadsnap.app.data.model.SeedPatterns
import com.beadsnap.app.services.RemotePatterns
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File
import java.util.UUID

class PatternStore private constructor(context: Context) {

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val json = Json { prettyPrint = true; ignoreUnknownKeys = true; isLenient = true }

    private val assets = context.assets
    private val userDir: File = File(context.filesDir, "patterns").apply { mkdirs() }
    private val remoteCache: File = File(context.filesDir, "remote_library.json")

    // Three layers, low to high priority:
    //   seed     - the small curated set compiled into the app
    //   bundled  - the full library shipped as an asset (library.json), shown
    //              instantly on first run with no network needed
    //   remote   - the hosted library downloaded when it's newer than bundled
    // Higher layers win on id collisions.
    private val seed = SeedPatterns.all
    private var bundled: List<FusePattern> = emptyList()
    private var remote: List<FusePattern> = emptyList()

    private val _systemPatterns = MutableStateFlow(seed.sortedBy { it.title })
    val systemPatterns: StateFlow<List<FusePattern>> = _systemPatterns.asStateFlow()

    private val _userPatterns = MutableStateFlow<List<FusePattern>>(emptyList())
    val userPatterns: StateFlow<List<FusePattern>> = _userPatterns.asStateFlow()

    private val _lastError = MutableStateFlow<String?>(null)
    val lastError: StateFlow<String?> = _lastError.asStateFlow()

    val allPatterns: List<FusePattern>
        get() = systemPatterns.value + userPatterns.value

    init {
        scope.launch { loadUserPatterns() }
        scope.launch { loadBundledLibrary() }
        scope.launch { loadCachedRemote() }
    }

    // ─── Bundled library ───────────────────────────────────────────────────────

    /** Load the full library shipped as an app asset so it shows on first run. */
    private suspend fun loadBundledLibrary() {
        val loaded = withContext(Dispatchers.IO) {
            try {
                val text = assets.open("library.json").bufferedReader().use { it.readText() }
                json.decodeFromString<RemotePatterns>(text).patterns
            } catch (_: Exception) { emptyList() }
        }
        if (loaded.isNotEmpty()) {
            bundled = loaded.map { it.materialized().copy(createdBy = CreatorType.system) }
            recomputeSystem()
        }
    }

    // ─── Downloadable library ──────────────────────────────────────────────────

    /** Load any previously-downloaded library from disk so it shows offline. */
    private suspend fun loadCachedRemote() {
        val cached = withContext(Dispatchers.IO) {
            if (!remoteCache.exists()) return@withContext emptyList<FusePattern>()
            try {
                json.decodeFromString<RemotePatterns>(remoteCache.readText()).patterns
            } catch (_: Exception) { emptyList() }
        }
        if (cached.isNotEmpty()) applyRemote(cached)
    }

    /** Called by RemoteLibraryService after a fresh download. Persists + merges. */
    fun applyRemoteLibrary(patterns: List<FusePattern>, rawJson: String) {
        scope.launch {
            withContext(Dispatchers.IO) {
                try {
                    val tmp = File(remoteCache.parentFile, "remote_library.json.tmp")
                    tmp.writeText(rawJson)
                    tmp.renameTo(remoteCache)
                } catch (_: Exception) { /* cache best-effort */ }
            }
            applyRemote(patterns)
        }
    }

    private fun applyRemote(patterns: List<FusePattern>) {
        remote = patterns.map { it.materialized().copy(createdBy = CreatorType.system) }
        recomputeSystem()
    }

    /** Merge the three layers; later layers win on id collisions. */
    private fun recomputeSystem() {
        val merged = (seed + bundled + remote).associateBy { it.id }.values
        _systemPatterns.value = merged.sortedBy { it.title }
    }

    private suspend fun loadUserPatterns() {
        val loaded = withContext(Dispatchers.IO) {
            userDir.listFiles { f -> f.extension == "json" }
                ?.mapNotNull { file ->
                    try { json.decodeFromString<FusePattern>(file.readText()) }
                    catch (_: Exception) { null }
                }
                ?.sortedBy { it.title.lowercase() }
                ?: emptyList()
        }
        _userPatterns.value = loaded
    }

    fun save(pattern: FusePattern) {
        if (pattern.createdBy == CreatorType.system) return
        val file = File(userDir, "${pattern.id}.json")
        try {
            val tmp = File(userDir, "${pattern.id}.json.tmp")
            tmp.writeText(json.encodeToString(pattern))
            // atomic on most Android filesystems; renameTo reports failure via its result
            if (!tmp.renameTo(file)) {
                tmp.delete()
                _lastError.value = "Failed to save \"${pattern.title}\": could not commit file"
                return
            }
            _lastError.value = null
        } catch (e: Exception) {
            _lastError.value = "Failed to save \"${pattern.title}\": ${e.message}"
            return
        }
        val current = _userPatterns.value.toMutableList()
        val idx = current.indexOfFirst { it.id == pattern.id }
        if (idx >= 0) current[idx] = pattern else current.add(pattern)
        _userPatterns.value = current.sortedBy { it.title.lowercase() }
    }

    fun delete(pattern: FusePattern) {
        if (pattern.createdBy == CreatorType.system) return
        try {
            val file = File(userDir, "${pattern.id}.json")
            // tolerate a missing file; surface a real deletion failure
            if (file.exists() && !file.delete()) {
                _lastError.value = "Failed to delete \"${pattern.title}\": could not remove file"
                return
            }
            _lastError.value = null
        } catch (e: Exception) {
            _lastError.value = "Failed to delete \"${pattern.title}\": ${e.message}"
            return
        }
        _userPatterns.value = _userPatterns.value.filter { it.id != pattern.id }
    }

    fun duplicate(pattern: FusePattern) {
        save(pattern.copy(
            id = UUID.randomUUID().toString(),
            title = "${pattern.title} Copy",
            createdBy = CreatorType.user,
            version = 1
        ))
    }

    fun clearLastError() { _lastError.value = null }

    fun patternsFor(category: PatternCategory): List<FusePattern> =
        allPatterns.filter { it.category == category }

    companion object {
        @Volatile private var instance: PatternStore? = null

        fun getInstance(context: Context): PatternStore =
            instance ?: synchronized(this) {
                instance ?: PatternStore(context.applicationContext).also { instance = it }
            }
    }
}
