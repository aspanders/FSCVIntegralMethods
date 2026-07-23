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
 * Keeps the app's pattern library up to date from a hosted manifest.
 *
 * Flow: fetch the tiny manifest.json → if its version is newer than what we
 * already applied, download patterns.json, hand it to PatternStore (which
 * caches + merges it), and record the new version. Cheap to call on every
 * launch; only downloads the big file when something actually changed.
 */
class RemoteLibraryService private constructor(context: Context) {

    // Point this at wherever manifest.json is hosted (raw GitHub, Pages, CDN…).
    private val manifestUrl =
        "https://raw.githubusercontent.com/aspanders/FSCVIntegralMethods/" +
        "claude/fuse-bead-converter-app-706h2s/library/manifest.json"

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
        val manifest = try {
            json.decodeFromString<LibraryManifest>(get(manifestUrl))
        } catch (_: Exception) {
            return null   // offline or malformed: keep whatever we already have
        }
        // The app already ships library version BUNDLED_LIBRARY_VERSION as an
        // asset, so only download when the hosted library is strictly newer.
        if (manifest.version <= maxOf(appliedVersion, BUNDLED_LIBRARY_VERSION)) return null

        val body = try {
            get(manifest.patternsUrl)
        } catch (_: Exception) {
            return null   // couldn't download the patterns file: try again next launch
        }
        val remote = try {
            json.decodeFromString<RemotePatterns>(body)
        } catch (_: Exception) {
            return null
        }
        store.applyRemoteLibrary(remote.patterns, body)  // caches the raw text + merges
        appliedVersion = manifest.version
        _updateApplied.value = remote.patterns.size
        return remote.patterns.size
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
        const val BUNDLED_LIBRARY_VERSION = 2

        @Volatile private var instance: RemoteLibraryService? = null
        fun getInstance(context: Context): RemoteLibraryService =
            instance ?: synchronized(this) {
                instance ?: RemoteLibraryService(context.applicationContext).also { instance = it }
            }
    }
}
