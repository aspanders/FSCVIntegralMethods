package com.beadsnap.app.services

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

object KeystoreHelper {
    private const val PREFS_FILE = "beadsnap_secure_prefs"

    private var prefs: SharedPreferences? = null

    fun init(context: Context) {
        if (prefs != null) return
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        prefs = EncryptedSharedPreferences.create(
            context,
            PREFS_FILE,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    fun save(key: String, value: String) {
        prefs?.edit()?.putString(key, value)?.apply()
    }

    fun load(key: String): String? = prefs?.getString(key, null)

    fun delete(key: String) {
        prefs?.edit()?.remove(key)?.apply()
    }
}
