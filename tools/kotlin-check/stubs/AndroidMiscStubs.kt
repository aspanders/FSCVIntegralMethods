@file:Suppress("unused", "UNUSED_PARAMETER")

package android.content

class Context {
    val contentResolver: ContentResolver = ContentResolver()
    val applicationContext: Context get() = this
    fun getSharedPreferences(name: String, mode: Int): SharedPreferences = SharedPreferences()
    companion object { const val MODE_PRIVATE = 0 }
}

class ContentResolver { fun openInputStream(uri: android.net.Uri): java.io.InputStream? = null }

class SharedPreferences {
    class Editor {
        fun putInt(key: String, value: Int): Editor = this
        fun putBoolean(key: String, value: Boolean): Editor = this
        fun putString(key: String, value: String?): Editor = this
        fun apply() {}
        fun commit(): Boolean = true
    }
    fun getInt(key: String, def: Int): Int = def
    fun getBoolean(key: String, def: Boolean): Boolean = def
    fun getString(key: String, def: String?): String? = def
    fun edit(): Editor = Editor()
}
