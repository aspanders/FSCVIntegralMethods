@file:Suppress("unused", "UNUSED_PARAMETER")

// In-memory stand-in for the EncryptedSharedPreferences-backed store, so the AI
// pattern service can be driven off-device. Real keys never come near this.
package com.beadsnap.app.services

object KeystoreHelper {
    private val values = HashMap<String, String>()
    fun load(account: String): String? = values[account]
    fun save(account: String, value: String) { values[account] = value }
    fun delete(account: String) { values.remove(account) }
}
