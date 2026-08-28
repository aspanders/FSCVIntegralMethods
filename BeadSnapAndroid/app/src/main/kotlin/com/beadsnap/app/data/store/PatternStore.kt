package com.beadsnap.app.data.store

import android.content.Context
import com.beadsnap.app.data.model.CreatorType
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.model.PatternCategory
import com.beadsnap.app.data.model.SeedPatterns
import com.beadsnap.app.services.RemotePatterns
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CancellationException
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
            // catch Throwable, not Exception. Loading the library builds its
            // peak here - a ~5 MB String, the parsed tree, and then ~980,000
            // Cell objects from materialized() - and the process heap on a
            // 1 GB device is commonly 64 MB. Going over throws
            // OutOfMemoryError, which is an Error, NOT an Exception: it would
            // sail straight through `catch (_: Exception)`, out of the
            // coroutine, and kill the app on every single launch, on exactly
            // the devices least able to spare the memory. An empty library is
            // survivable; a crash loop is not.
            } catch (e: CancellationException) {
                throw e
            } catch (_: Throwable) { emptyList() }
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
            } catch (e: CancellationException) {
                throw e
            } catch (_: Throwable) { emptyList() }   // see loadBundledLibrary
        }
        if (cached.isNotEmpty()) applyRemote(cached)
    }

    /**
     * Called by RemoteLibraryService after a fresh download. Persists + merges.
     *
     * Returns whether the download reached DISK. The caller records the applied
     * version, and it must only do that when this says yes: File.renameTo
     * reports failure by returning false rather than throwing, and a ~5 MB
     * writeText onto a full disk throws before the rename is even reached. With
     * both swallowed, the app ended up with a preference claiming version N was
     * applied while the cache still held N-1 - and because the sync short
     * circuits on that preference, the new patterns were never downloaded
     * again. The library would simply stop updating, permanently and silently.
     */
    suspend fun applyRemoteLibrary(patterns: List<FusePattern>, rawJson: String): Boolean {
        val saved = withContext(Dispatchers.IO) {
            try {
                val tmp = File(remoteCache.parentFile, "remote_library.json.tmp")
                tmp.writeText(rawJson)
                tmp.renameTo(remoteCache).also { if (!it) tmp.delete() }
            } catch (e: CancellationException) {
                throw e
            } catch (_: Throwable) { false }
        }
        applyRemote(patterns)
        return saved
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

    /**
     * Save on the CALLING thread.
     *
     * Kept synchronous because the editor calls it from onCleared(), where the
     * write has to finish before the ViewModel and its scope go away. Anything
     * on a hot path should use [saveOffThread] instead.
     */
    fun save(pattern: FusePattern) {
        if (pattern.createdBy == CreatorType.system) return
        if (writeToDisk(pattern)) index(pattern)
    }

    /**
     * Save with the encode and the file write on the IO dispatcher.
     *
     * The editor autosaves every 500 ms while a stroke is in progress, and
     * viewModelScope is Dispatchers.Main.immediate - so serialising a full
     * board and writing it to disk was happening on the UI thread, in the
     * middle of the drag it was saving. It is a few milliseconds on a fast
     * device and a visible hitch on a slow one, and it is a StrictMode
     * violation either way.
     *
     * The index update deliberately stays on the caller's dispatcher: it is a
     * read-modify-write of _userPatterns, and every caller is on the main
     * thread, which is what keeps two saves from losing each other.
     */
    suspend fun saveOffThread(pattern: FusePattern) {
        if (pattern.createdBy == CreatorType.system) return
        if (withContext(Dispatchers.IO) { writeToDisk(pattern) }) index(pattern)
    }

    /** Returns whether the pattern reached disk; reports why if it did not. */
    private fun writeToDisk(pattern: FusePattern): Boolean {
        val file = File(userDir, "${pattern.id}.json")
        try {
            val tmp = File(userDir, "${pattern.id}.json.tmp")
            tmp.writeText(json.encodeToString(pattern))
            // atomic on most Android filesystems; renameTo reports failure via its result
            if (!tmp.renameTo(file)) {
                tmp.delete()
                _lastError.value = "Failed to save \"${pattern.title}\": could not commit file"
                return false
            }
            _lastError.value = null
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            _lastError.value = "Failed to save \"${pattern.title}\": ${e.message}"
            return false
        }
        return true
    }

    private fun index(pattern: FusePattern) {
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
