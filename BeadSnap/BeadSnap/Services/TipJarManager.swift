import Foundation
import StoreKit

/// Wikipedia-style tip jar. BeadSnap is free with no ads; after 10 uses we
/// show a single friendly in-app prompt. Tips are StoreKit consumables —
/// App Store policy (3.1.1) requires IAP for tips, not external links.
@MainActor
final class TipJarManager: ObservableObject {
    static let shared = TipJarManager()

    // Consumable product IDs — must exist in App Store Connect
    // (same IDs as Google Play for shared store copy)
    static let productIDs = ["tip_small", "tip_medium", "tip_large"]

    private static let promptThreshold = 10   // first ask after 10 uses
    private static let laterRetryUses = 15    // "Maybe later" re-asks after 15 more

    @Published private(set) var products: [Product] = []
    @Published private(set) var isPurchasing = false
    @Published var showThanks = false
    @Published var shouldShowPrompt = false

    private let defaults = UserDefaults.standard
    private var updatesTask: Task<Void, Never>?

    private enum Keys {
        static let useCount = "tipJar.useCount"
        static let dismissed = "tipJar.dismissedForever"
        static let nextPromptAt = "tipJar.nextPromptAt"
        static let hasTipped = "tipJar.hasTipped"
    }

    private init() {
        // Finish any transactions delivered while the app was closed
        updatesTask = Task { [weak self] in
            for await update in Transaction.updates {
                if case .verified(let txn) = update {
                    await txn.finish()
                    self?.markTipped()
                }
            }
        }
    }

    deinit { updatesTask?.cancel() }

    var hasTipped: Bool { defaults.bool(forKey: Keys.hasTipped) }

    // MARK: - Usage counting

    /// Call once per app launch. Flips shouldShowPrompt on the 10th use
    /// (or the retry point after "Maybe later").
    func recordUse() {
        let count = defaults.integer(forKey: Keys.useCount) + 1
        defaults.set(count, forKey: Keys.useCount)

        guard !defaults.bool(forKey: Keys.dismissed), !hasTipped else { return }
        let nextAt = defaults.object(forKey: Keys.nextPromptAt) as? Int ?? Self.promptThreshold
        if count >= nextAt {
            shouldShowPrompt = true
        }
    }

    func promptDonateNow() {
        shouldShowPrompt = false
        // Re-ask later only if they don't complete a tip
        defaults.set(currentUseCount + Self.laterRetryUses, forKey: Keys.nextPromptAt)
    }

    func promptMaybeLater() {
        shouldShowPrompt = false
        defaults.set(currentUseCount + Self.laterRetryUses, forKey: Keys.nextPromptAt)
    }

    func promptDismissForever() {
        shouldShowPrompt = false
        defaults.set(true, forKey: Keys.dismissed)
    }

    private var currentUseCount: Int { defaults.integer(forKey: Keys.useCount) }

    // MARK: - StoreKit

    func loadProducts() async {
        guard products.isEmpty else { return }
        do {
            let loaded = try await Product.products(for: Self.productIDs)
            products = loaded.sorted { $0.price < $1.price }
        } catch {
            // Store unreachable — the tip jar UI shows a graceful empty state
            products = []
        }
    }

    func purchase(_ product: Product) async {
        guard !isPurchasing else { return }
        isPurchasing = true
        defer { isPurchasing = false }
        do {
            let result = try await product.purchase()
            switch result {
            case .success(.verified(let txn)):
                await txn.finish()
                markTipped()
                showThanks = true
            case .success(.unverified), .userCancelled, .pending:
                break
            @unknown default:
                break
            }
        } catch {
            // Purchase failed — StoreKit surfaces its own error UI
        }
    }

    private func markTipped() {
        defaults.set(true, forKey: Keys.hasTipped)
    }
}
