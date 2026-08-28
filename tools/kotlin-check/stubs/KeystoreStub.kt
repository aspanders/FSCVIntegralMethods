@file:Suppress("unused", "UNUSED_PARAMETER")

// In-memory stand-in for the EncryptedSharedPreferences-backed store, so the AI
// pattern service can be driven off-device. Real keys never come near this.
package com.beadsnap.app.services

object KeystoreHelper {
    private val values = HashMap<String, String>()

    /** Whether the harness should pretend secure storage came up. */
    var available: Boolean = true

    val isAvailable: Boolean get() = available

    fun load(account: String): String? = if (available) values[account] else null

    /**
     * Returns whether the value was stored - the real one can fail, on a device
     * whose keystore is damaged, and a caller that ignores the answer leaves
     * the user pasting a key that goes nowhere.
     */
    fun save(account: String, value: String): Boolean {
        if (!available) return false
        values[account] = value
        return true
    }

    fun delete(account: String) { values.remove(account) }
}
