import Foundation
import Security

enum Keychain {
    /// Stores `value`, and says whether it actually landed.
    ///
    /// `SecItemAdd` reports failure through its OSStatus return, and discarding
    /// it meant a write that did not happen looked exactly like one that did:
    /// the key sheet closed, nothing was stored, and the next tap said "No API
    /// key set" again - so the user pasted it once more, and again. A write can
    /// genuinely fail (errSecInteractionNotAllowed on a locked device, a
    /// keychain the OS will not open), and the caller has to be able to say so.
    @discardableResult
    static func save(_ value: String, for account: String) -> Bool {
        let data = Data(value.utf8)
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: "com.beadsnap.app",
            kSecAttrAccount: account,
        ]
        SecItemDelete(query as CFDictionary)
        var attrs = query
        attrs[kSecValueData] = data
        // Device-only, and readable after the first unlock. Without an explicit
        // accessibility class the item defaults to WhenUnlocked, which is
        // included in encrypted iCloud backups - so the user's API key rode
        // along to every device restored from that backup.
        attrs[kSecAttrAccessible] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        return SecItemAdd(attrs as CFDictionary, nil) == errSecSuccess
    }

    static func load(for account: String) -> String? {
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: "com.beadsnap.app",
            kSecAttrAccount: account,
            kSecReturnData: true,
            kSecMatchLimit: kSecMatchLimitOne,
        ]
        var result: AnyObject?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess,
              let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    static func delete(for account: String) {
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: "com.beadsnap.app",
            kSecAttrAccount: account,
        ]
        SecItemDelete(query as CFDictionary)
    }
}
