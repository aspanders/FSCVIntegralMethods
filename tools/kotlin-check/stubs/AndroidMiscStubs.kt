@file:Suppress("unused", "UNUSED_PARAMETER")

package android.content
class Context { val contentResolver: ContentResolver = ContentResolver() }
class ContentResolver { fun openInputStream(uri: android.net.Uri): java.io.InputStream? = null }
