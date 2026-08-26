package com.beadsnap.app.services

import android.content.Context
import android.content.SharedPreferences
import com.beadsnap.app.data.model.FusePattern
import com.beadsnap.app.data.store.PatternStore
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.Call
import okhttp3.Callback
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import java.io.IOException
import java.util.concurrent.TimeUnit
import kotlin.coroutines.cancellation.CancellationException
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

@Serializable
data class LibraryManifest(
    val version: Int,
    val count: Int = 0,
    val patternsUrl: String,
    val updatedAt: String = ""
)

@Serializable
data class RemotePatterns(
    val version: Int,
    val patterns: List<FusePattern>
)

/**
 * Where to look for a hosted library, and in what order.
 *
 * Pure string work, kept out of [RemoteLibraryService] so it can be unit-tested
 * without a network or an Android context - the same reason [TipPromptLogic]
 * sits outside TipJarManager.
 */
object LibrarySources {

    /**
     * Bases tried in order until one answers, most-preferred first.
     *
     * A LIST, not a single URL, because a single URL pinned the library to one
     * git branch: deleting that branch after a merge would have cut off pattern
     * updates for every installed copy of the app, with no fix short of
     * shipping a new build to the store. The library can now move between
     * branches - or off GitHub entirely, onto Pages or a CDN - by adding the
     * new home to the front of this list in a future release, while the old one
     * keeps serving everybody who has not updated yet.
     *
     * A source that 404s costs one cheap request and falls through to the next.
     * Keep in sync with the same list in the iOS RemoteLibraryService.
     */
    val BASES = listOf(
        "https://raw.githubusercontent.com/aspanders/FSCVIntegralMethods/main",
        "https://raw.githubusercontent.com/aspanders/FSCVIntegralMethods/" +
            "claude/fuse-bead-converter-app-706h2s",
    )

    fun manifestUrl(base: String): String = "${base.trimEnd('/')}/library/manifest.json"

    /**
     * Where to look for the patterns file, best first.
     *
     * The sibling of the manifest we actually fetched comes before the absolute
     * patternsUrl recorded inside it, and that ordering is the whole point: a
     * manifest copied to a new home still names the OLD patternsUrl, so trusting
     * the file would send the app straight back to the host it just moved off.
     * The recorded URL stays as a fallback for a manifest served from somewhere
     * its patterns file is not.
     */
    fun patternUrls(base: String, patternsUrl: String): List<String> =
        listOf("${base.trimEnd('/')}/library/patterns.json", patternsUrl)
            .filter { it.isNotBlank() }
            .distinct()
}

/**
 * Keeps the app's pattern library up to date from a hosted manifest.
 *
 * Flow: fetch the tiny manifest.json → if its version is newer than what we
 * already applied, download patterns.json, hand it to PatternStore (which
 * caches + merges it), and record the new version. Cheap to call on every
 * launch; only downloads the big file when something actually changed.
 */
class RemoteLibraryService private constructor(context: Context) {

    private val sources = LibrarySources.BASES

    private val prefs: SharedPreferences =
        context.getSharedPreferences("remote_library", Context.MODE_PRIVATE)
    private val store = PatternStore.getInstance(context)
    private val json = Json { ignoreUnknownKeys = true; isLenient = true }
    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    var appliedVersion: Int
        get() = prefs.getInt("appliedVersion", 0)
        private set(v) { prefs.edit().putInt("appliedVersion", v).apply() }

    // Emits the new pattern count when an update is applied; UI shows a snackbar.
    private val _updateApplied = MutableStateFlow<Int?>(null)
    val updateApplied: StateFlow<Int?> = _updateApplied.asStateFlow()
    fun clearUpdateNotice() { _updateApplied.value = null }

    /**
     * Check for and apply a newer library. Returns the number of patterns in
     * the new library if an update was applied, or null if already current /
     * offline (both silent, non-fatal).
     */
    suspend fun syncIfNeeded(): Int? {
        for (base in sources) {
            val manifest = try {
                json.decodeFromString<LibraryManifest>(get(LibrarySources.manifestUrl(base)))
            } catch (e: CancellationException) {
                throw e       // the caller went away; not this source's fault
            } catch (_: Exception) {
                continue      // offline, 404, or malformed: try the next source
            }
            // The app already ships library version BUNDLED_LIBRARY_VERSION as
            // an asset, so only download when the hosted library is strictly
            // newer. A source that answered and is not newer means we are up to
            // date - stop, rather than asking the others the same question.
            if (manifest.version <= maxOf(appliedVersion, BUNDLED_LIBRARY_VERSION)) return null

            val body = fetchPatterns(base, manifest) ?: continue
            val remote = try {
                json.decodeFromString<RemotePatterns>(body)
            } catch (e: CancellationException) {
                throw e
            } catch (_: Exception) {
                continue
            }
            store.applyRemoteLibrary(remote.patterns, body)  // caches raw text + merges
            appliedVersion = manifest.version
            _updateApplied.value = remote.patterns.size
            return remote.patterns.size
        }
        return null
    }

    /** Downloads the patterns file, trying each candidate in turn. */
    private suspend fun fetchPatterns(base: String, manifest: LibraryManifest): String? {
        for (url in LibrarySources.patternUrls(base, manifest.patternsUrl)) {
            try {
                return get(url)
            } catch (e: CancellationException) {
                throw e
            } catch (_: Exception) {
                // try the next candidate
            }
        }
        return null
    }

    private suspend fun get(url: String): String =
        suspendCancellableCoroutine { cont ->
            val call = client.newCall(Request.Builder().url(url).build())
            cont.invokeOnCancellation { call.cancel() }
            call.enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    if (!call.isCanceled()) cont.resumeWithException(e)
                }
                override fun onResponse(call: Call, response: Response) {
                    response.use {
                        if (!it.isSuccessful) {
                            cont.resumeWithException(IOException("HTTP ${it.code}"))
                        } else {
                            cont.resume(it.body?.string() ?: "")
                        }
                    }
                }
            })
        }

    companion object {
        // Version of library.json shipped in the app's assets. Keep in sync with
        // the "version" field of the bundled asset when you refresh it.
        const val BUNDLED_LIBRARY_VERSION = 52

        @Volatile private var instance: RemoteLibraryService? = null
        fun getInstance(context: Context): RemoteLibraryService =
            instance ?: synchronized(this) {
                instance ?: RemoteLibraryService(context.applicationContext).also { instance = it }
            }
    }
}
