package com.beadsnap.app.data.store

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File
import java.util.UUID

/** One pattern derived from a project's photo, with the settings that made it. */
@Serializable
data class PhotoVariant(
    val patternId: String,
    val label: String,
    val createdAt: Long
)

/**
 * A photo and every pattern made from it.
 *
 * The photo is the parent; the variants are the different boards, colour
 * counts, shapes and background cut-outs tried against it. Only the photo
 * lives here - the patterns themselves stay ordinary user patterns in
 * PatternStore, so opening a variant in the editor, autosaving it, exporting
 * it and sharing it all work with no special cases.
 */
@Serializable
data class PhotoProject(
    val id: String,
    val title: String,
    val createdAt: Long,
    val variants: List<PhotoVariant> = emptyList(),
    /**
     * Whether a background-removed copy was kept alongside the original.
     *
     * Both are stored on purpose. Keeping only the cut-out would make the
     * removal permanent - "different background removals" is one of the things
     * a variant is supposed to be able to differ in, and a cut-out cannot be
     * un-cut. Keeping only the original would throw away brushwork the user
     * did by hand.
     */
    val hasCutout: Boolean = false
)

/**
 * Keeps the source photos so a pattern can be re-derived from the original
 * months later, instead of the photo being thrown away the moment the first
 * conversion finished.
 *
 * The photo is written as PNG, not JPEG, because a background-removed source
 * carries an alpha channel and JPEG would silently flatten it onto black.
 */
class PhotoProjectStore private constructor(context: Context) {

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val json = Json { prettyPrint = true; ignoreUnknownKeys = true; isLenient = true }

    private val dir: File = File(context.filesDir, "projects").apply { mkdirs() }
    private val indexFile = File(dir, "projects.json")

    private val _projects = MutableStateFlow<List<PhotoProject>>(emptyList())
    val projects: StateFlow<List<PhotoProject>> = _projects.asStateFlow()

    private val _lastError = MutableStateFlow<String?>(null)
    val lastError: StateFlow<String?> = _lastError.asStateFlow()

    init { scope.launch { load() } }

    private suspend fun load() {
        _projects.value = withContext(Dispatchers.IO) {
            if (!indexFile.exists()) return@withContext emptyList()
            try { json.decodeFromString<List<PhotoProject>>(indexFile.readText()) }
            catch (_: Exception) { emptyList() }
        }.sortedByDescending { it.createdAt }
    }

    fun sourceFile(projectId: String): File =
        File(File(dir, projectId).apply { mkdirs() }, "source.png")

    fun cutoutFile(projectId: String): File =
        File(File(dir, projectId).apply { mkdirs() }, "cutout.png")

    /** [cutout] true loads the background-removed copy, if the project has one. */
    suspend fun loadSource(projectId: String, cutout: Boolean = false): Bitmap? =
        withContext(Dispatchers.IO) {
            val f = if (cutout) cutoutFile(projectId) else sourceFile(projectId)
            // Our own PNG, written upright and already size-bounded, so there
            // is no EXIF to re-apply here - unlike a photo from the picker.
            if (!f.exists()) null else try { BitmapFactory.decodeFile(f.absolutePath) }
            catch (_: Exception) { null }
        }

    /**
     * Start a project from [source]. Returns immediately; the PNG is written on
     * this store's own scope so navigating away from the screen that called
     * this cannot cancel the write half-finished.
     */
    fun createProject(title: String, source: Bitmap, cutout: Bitmap? = null): PhotoProject {
        val project = PhotoProject(
            id = UUID.randomUUID().toString(),
            title = title,
            createdAt = System.currentTimeMillis(),
            hasCutout = cutout != null
        )
        persist(_projects.value + project)
        // Detached copies: the caller is free to drop or recycle its bitmaps
        // the moment this returns.
        val srcCopy = detach(source)
        val cutCopy = cutout?.let { detach(it) }
        scope.launch(Dispatchers.IO) {
            try {
                writePng(srcCopy ?: source, sourceFile(project.id))
                if (cutout != null) writePng(cutCopy ?: cutout, cutoutFile(project.id))
                _lastError.value = null
            } catch (e: Exception) {
                _lastError.value = "Could not save the photo for \"$title\": ${e.message}"
            } finally {
                srcCopy?.recycle()
                cutCopy?.recycle()
            }
        }
        return project
    }

    private fun detach(bmp: Bitmap): Bitmap? =
        try { bmp.copy(bmp.config ?: Bitmap.Config.ARGB_8888, false) } catch (_: Exception) { null }

    private fun writePng(bmp: Bitmap, target: File) {
        target.outputStream().use { bmp.compress(Bitmap.CompressFormat.PNG, 100, it) }
    }

    fun addVariant(projectId: String, patternId: String, label: String) {
        persist(_projects.value.map { p ->
            if (p.id != projectId) p
            else p.copy(
                // Re-saving the same pattern updates its label rather than
                // adding a second row for it.
                variants = p.variants.filter { it.patternId != patternId } +
                    PhotoVariant(patternId, label, System.currentTimeMillis())
            )
        })
    }

    fun removeVariant(projectId: String, patternId: String) {
        persist(_projects.value.map { p ->
            if (p.id != projectId) p
            else p.copy(variants = p.variants.filter { it.patternId != patternId })
        })
    }

    fun rename(projectId: String, title: String) {
        persist(_projects.value.map { if (it.id == projectId) it.copy(title = title) else it })
    }

    /** Drops the project and its photo. Variant patterns are the caller's call. */
    fun delete(projectId: String) {
        persist(_projects.value.filter { it.id != projectId })
        scope.launch(Dispatchers.IO) {
            try { File(dir, projectId).deleteRecursively() } catch (_: Exception) { }
        }
    }

    fun clearLastError() { _lastError.value = null }

    private fun persist(next: List<PhotoProject>) {
        val sorted = next.sortedByDescending { it.createdAt }
        _projects.value = sorted
        scope.launch(Dispatchers.IO) {
            try {
                val tmp = File(dir, "projects.json.tmp")
                tmp.writeText(json.encodeToString(sorted))
                if (!tmp.renameTo(indexFile)) {
                    tmp.delete()
                    _lastError.value = "Could not save your photo projects"
                    return@launch
                }
                _lastError.value = null
            } catch (e: Exception) {
                _lastError.value = "Could not save your photo projects: ${e.message}"
            }
        }
    }

    companion object {
        @Volatile private var instance: PhotoProjectStore? = null

        fun getInstance(context: Context): PhotoProjectStore =
            instance ?: synchronized(this) {
                instance ?: PhotoProjectStore(context.applicationContext).also { instance = it }
            }

        /** "32×32 · 12 colours · Circle · No background" - what makes it differ. */
        fun labelFor(
            pattern: com.beadsnap.app.data.model.FusePattern,
            cutout: Boolean = false
        ): String =
            "${pattern.grid.width}×${pattern.grid.height} · " +
            "${pattern.palette.size} colours · ${pattern.shape.displayName}" +
            if (cutout) " · No background" else ""
    }
}
