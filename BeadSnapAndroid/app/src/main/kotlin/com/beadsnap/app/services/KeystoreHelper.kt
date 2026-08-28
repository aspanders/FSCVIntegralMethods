package com.beadsnap.app.services

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import java.security.KeyStore

/**
 * The only place an API key is stored: EncryptedSharedPreferences, backed by a
 * hardware master key in the Android Keystore. Never plain SharedPreferences.
 *
 * Everything here refuses to throw. [init] is called from
 * `Application.onCreate`, so an escaping exception is a crash before any UI
 * exists at all - the app simply will not start - and both calls it makes can
 * throw for reasons that have nothing to do with this app: a damaged keystore
 * entry, an OEM ROM with a broken StrongBox, or a restore that brought the
 * encrypted file back without the key that opens it. Losing a stored API key
 * costs the user one paste. Losing the app costs them the app.
 */
object KeystoreHelper {
    private const val PREFS_FILE = "beadsnap_secure_prefs"

    @Volatile private var prefs: SharedPreferences? = null

    /** Whether secure storage came up. False means keys cannot be kept. */
    val isAvailable: Boolean get() = prefs != null

    fun init(context: Context) {
        if (prefs != null) return
        prefs = open(context) ?: run {
            // A damaged keystore entry cannot be repaired, only replaced, and
            // anything stored under it is unreadable either way. Throw both
            // away and try once with a fresh key.
            reset(context)
            open(context)
        }
    }

    private fun open(context: Context): SharedPreferences? = try {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        EncryptedSharedPreferences.create(
            context,
            PREFS_FILE,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    } catch (_: Throwable) {
        null
    }

    private fun reset(context: Context) {
        try {
            KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
                .deleteEntry(MasterKey.DEFAULT_MASTER_KEY_ALIAS)
        } catch (_: Throwable) { }
        try {
            context.deleteSharedPreferences(PREFS_FILE)
        } catch (_: Throwable) { }
    }

    /** Returns whether the value was actually stored. */
    fun save(key: String, value: String): Boolean {
        val p = prefs ?: return false
        return try {
            // commit(), not apply(): the caller is told whether it worked, and
            // an API key the user just typed is worth waiting a millisecond for.
            p.edit().putString(key, value).commit()
        } catch (_: Throwable) {
            false
        }
    }

    fun load(key: String): String? = try {
        prefs?.getString(key, null)
    } catch (_: Throwable) {
        null
    }

    fun delete(key: String) {
        try {
            prefs?.edit()?.remove(key)?.apply()
        } catch (_: Throwable) { }
    }
}
