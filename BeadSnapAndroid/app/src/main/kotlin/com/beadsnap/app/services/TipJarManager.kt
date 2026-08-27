package com.beadsnap.app.services

import android.app.Activity
import android.content.Context
import android.content.SharedPreferences
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingClientStateListener
import com.android.billingclient.api.BillingFlowParams
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.ConsumeParams
import com.android.billingclient.api.PendingPurchasesParams
import com.android.billingclient.api.ProductDetails
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.PurchasesUpdatedListener
import com.android.billingclient.api.QueryProductDetailsParams
import com.android.billingclient.api.QueryPurchasesParams
import java.util.Collections
import java.util.concurrent.ConcurrentHashMap
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Wikipedia-style tip jar. BeadSnap is free with no ads; after 10 uses we show
 * a single friendly in-app prompt. Tips are Play Billing consumables: Play
 * policy requires Play Billing for tips, not external payment links.
 *
 * Prompt decision logic lives in [TipPromptLogic] so it is unit-testable.
 */
object TipPromptLogic {
    const val PROMPT_THRESHOLD = 10   // first ask after 10 uses
    const val LATER_RETRY_USES = 15   // "Maybe later" re-asks after 15 more

    fun shouldPrompt(useCount: Int, dismissedForever: Boolean, hasTipped: Boolean, nextPromptAt: Int): Boolean {
        if (dismissedForever || hasTipped) return false
        return useCount >= nextPromptAt
    }
}

class TipJarManager private constructor(context: Context) : PurchasesUpdatedListener {

    // Consumable product IDs: must exist in Play Console (same IDs as the
    // App Store). small/medium/large are the headline tips; the remaining
    // tiers back the "Custom amount" picker. Neither Play nor the App Store
    // allows a truly free-form amount, so "custom" = a wider set of preset
    // price points the user chooses from.
    val headlineProductIds = listOf("tip_small", "tip_medium", "tip_large")
    val customProductIds = listOf("tip_custom_20", "tip_custom_50", "tip_custom_100")
    val productIds = headlineProductIds + customProductIds

    private val prefs: SharedPreferences =
        context.getSharedPreferences("tipjar", Context.MODE_PRIVATE)

    private val _products = MutableStateFlow<List<ProductDetails>>(emptyList())
    val products: StateFlow<List<ProductDetails>> = _products.asStateFlow()

    private val _showThanks = MutableStateFlow(false)
    val showThanks: StateFlow<Boolean> = _showThanks.asStateFlow()

    private val _shouldShowPrompt = MutableStateFlow(false)
    val shouldShowPrompt: StateFlow<Boolean> = _shouldShowPrompt.asStateFlow()

    /**
     * Whatever went wrong last, in words a person can act on, or null.
     *
     * Every billing call can fail, and until this existed all of them failed
     * silently: the sheet went on saying "Loading tip options..." forever and
     * the tip buttons did nothing at all when tapped. Someone trying to give
     * money was told nothing.
     */
    private val _lastError = MutableStateFlow<String?>(null)
    val lastError: StateFlow<String?> = _lastError.asStateFlow()

    /**
     * A tip that is authorised but not yet paid for - cash at a kiosk, or a
     * parent's approval still pending. We enable those (see
     * [PendingPurchasesParams] below), so we have to say something about them:
     * nothing has been charged yet and no thank-you is due until it clears.
     */
    private val _pendingTip = MutableStateFlow(false)
    val pendingTip: StateFlow<Boolean> = _pendingTip.asStateFlow()

    /**
     * Tokens currently being consumed.
     *
     * [onPurchasesUpdated] and [refreshPurchases] can both hand us the same
     * purchase within a moment of each other - the live callback and the
     * reconciliation query see the same token - and consuming a token twice
     * makes the second call fail with ITEM_NOT_OWNED for no reason.
     */
    private val consuming: MutableSet<String> =
        Collections.newSetFromMap(ConcurrentHashMap<String, Boolean>())

    // Play Billing Library 9. Two things here are v8+ API and not optional:
    //
    // enablePendingPurchases() with no arguments was removed - it now takes a
    // PendingPurchasesParams, and enableOneTimeProducts() on that builder is
    // the app stating that it handles a purchase that is authorised but not
    // yet paid for (cash at a kiosk, a parent's approval). Tips are one-time
    // products, so that is the only flag we need.
    //
    // enableAutoServiceReconnection() is new in v8 and worth taking: the old
    // onBillingServiceDisconnected callback below did nothing, so a dropped
    // connection left the tip jar dead until something happened to call
    // connect() again.
    private val billingClient = BillingClient.newBuilder(context)
        .setListener(this)
        .enablePendingPurchases(
            PendingPurchasesParams.newBuilder()
                .enableOneTimeProducts()
                .build()
        )
        .enableAutoServiceReconnection()
        .build()

    val hasTipped: Boolean get() = prefs.getBoolean(KEY_HAS_TIPPED, false)

    // ─── Usage counting ───────────────────────────────────────────────────────

    /** Call once per app launch. */
    fun recordUse() {
        val count = prefs.getInt(KEY_USE_COUNT, 0) + 1
        prefs.edit().putInt(KEY_USE_COUNT, count).apply()
        val nextAt = prefs.getInt(KEY_NEXT_PROMPT_AT, TipPromptLogic.PROMPT_THRESHOLD)
        if (TipPromptLogic.shouldPrompt(count, prefs.getBoolean(KEY_DISMISSED, false), hasTipped, nextAt)) {
            _shouldShowPrompt.value = true
        }
    }

    fun promptDonateNow() {
        _shouldShowPrompt.value = false
        scheduleRetry()
    }

    fun promptMaybeLater() {
        _shouldShowPrompt.value = false
        scheduleRetry()
    }

    fun promptDismissForever() {
        _shouldShowPrompt.value = false
        prefs.edit().putBoolean(KEY_DISMISSED, true).apply()
    }

    fun clearThanks() { _showThanks.value = false }

    fun clearError() { _lastError.value = null }

    private fun scheduleRetry() {
        val count = prefs.getInt(KEY_USE_COUNT, 0)
        prefs.edit().putInt(KEY_NEXT_PROMPT_AT, count + TipPromptLogic.LATER_RETRY_USES).apply()
    }

    // ─── Billing ──────────────────────────────────────────────────────────────

    /**
     * Connect, list the tiers, and reconcile anything Play already holds.
     *
     * Safe to call repeatedly; the app calls it on every launch as well as
     * whenever the tip sheet opens, and [refreshPurchases] is the reason for
     * the launch call.
     */
    fun connect() {
        if (billingClient.isReady) {
            queryProducts()
            refreshPurchases()
            return
        }
        billingClient.startConnection(object : BillingClientStateListener {
            override fun onBillingSetupFinished(result: BillingResult) {
                if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                    _lastError.value = null
                    queryProducts()
                    refreshPurchases()
                } else {
                    _lastError.value = "Tips aren't available right now: ${describe(result)}"
                }
            }
            // The client reconnects itself now (enableAutoServiceReconnection
            // above); this stays because the interface requires it.
            override fun onBillingServiceDisconnected() { }
        })
    }

    private fun queryProducts() {
        val params = QueryProductDetailsParams.newBuilder()
            .setProductList(productIds.map { id ->
                QueryProductDetailsParams.Product.newBuilder()
                    .setProductId(id)
                    .setProductType(BillingClient.ProductType.INAPP)
                    .build()
            })
            .build()
        // v8 changed this callback: the second argument is a
        // QueryProductDetailsResult rather than a bare List<ProductDetails>,
        // because a query can now come back with some products fetched and
        // others not. We only need the ones that came back - a tier missing
        // from Play Console simply does not appear in the sheet.
        billingClient.queryProductDetailsAsync(params) { result, productDetailsResult ->
            if (result.responseCode != BillingClient.BillingResponseCode.OK) {
                _lastError.value = "Couldn't load the tip options: ${describe(result)}"
                return@queryProductDetailsAsync
            }
            val fetched = productDetailsResult.productDetailsList.sortedBy {
                it.oneTimePurchaseOfferDetails?.priceAmountMicros ?: 0
            }
            _products.value = fetched
            // An OK response with nothing in it is the case that used to spin
            // forever: the sheet's only "not loaded yet" state is an empty
            // list, so a query that succeeds and returns no tiers - none
            // configured, or a country they are not sold in - looked exactly
            // like a query still in flight.
            _lastError.value = if (fetched.isEmpty()) {
                "Tips aren't available on this device right now."
            } else {
                null
            }
        }
    }

    /**
     * Deliver and consume anything Play is still holding for this user.
     *
     * A consumable that is bought but never consumed is refunded automatically
     * after three days, so a tip paid while the app was killed mid-checkout -
     * or one whose consume call failed - came back to the user as a refund and
     * we never even said thank you. Play's own guidance is to query on every
     * launch and on returning to the foreground, which is why the app calls
     * [connect] at startup and not only when the sheet opens.
     */
    fun refreshPurchases() {
        val params = QueryPurchasesParams.newBuilder()
            .setProductType(BillingClient.ProductType.INAPP)
            .build()
        billingClient.queryPurchasesAsync(params) { result, purchases ->
            if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                handlePurchases(purchases, authoritative = true)
            }
            // A failed reconciliation query is deliberately silent: the user
            // did not ask for it, nothing is lost, and the next launch retries.
        }
    }

    fun purchase(activity: Activity, product: ProductDetails) {
        if (!billingClient.isReady) {
            // Tapping a tier before the connection is up used to do literally
            // nothing. Say so, and start connecting so the retry works.
            _lastError.value = "Not connected to the Play Store yet - try again in a moment."
            connect()
            return
        }
        val flowParams = BillingFlowParams.newBuilder()
            .setProductDetailsParamsList(listOf(
                BillingFlowParams.ProductDetailsParams.newBuilder()
                    .setProductDetails(product)
                    .build()
            ))
            .build()
        // launchBillingFlow REPORTS FAILURE BY RETURN VALUE. Discarding it
        // meant that when the checkout sheet did not open - stale
        // ProductDetails, a device with no Play account, a broken service
        // binding - the button was simply dead: no dialog, no message, no
        // state change, nothing in the log.
        val result = billingClient.launchBillingFlow(activity, flowParams)
        _lastError.value = if (result.responseCode == BillingClient.BillingResponseCode.OK) {
            null
        } else {
            "Couldn't open the Play Store checkout: ${describe(result)}"
        }
    }

    override fun onPurchasesUpdated(result: BillingResult, purchases: MutableList<Purchase>?) {
        when (result.responseCode) {
            BillingClient.BillingResponseCode.OK -> {
                _lastError.value = null
                handlePurchases(purchases.orEmpty())
            }
            // Backing out of the sheet is a choice, not a failure.
            BillingClient.BillingResponseCode.USER_CANCELED -> _lastError.value = null
            // An earlier tip was paid for and never consumed, so Play thinks
            // they still own it. Reconciling clears it and thanks them.
            BillingClient.BillingResponseCode.ITEM_ALREADY_OWNED -> refreshPurchases()
            else -> _lastError.value = "That tip didn't go through: ${describe(result)}"
        }
    }

    /**
     * [authoritative] means this is Play's full list of what the user owns, not
     * a single update, so it can clear [_pendingTip] as well as set it. A tip
     * left pending and then abandoned would otherwise pin the sheet on "waiting
     * to be completed" for good, with no way to tip again.
     */
    private fun handlePurchases(purchases: List<Purchase>, authoritative: Boolean = false) {
        if (authoritative) {
            _pendingTip.value = purchases.any { it.purchaseState == Purchase.PurchaseState.PENDING }
        }
        for (purchase in purchases) {
            when (purchase.purchaseState) {
                Purchase.PurchaseState.PURCHASED -> consume(purchase)
                Purchase.PurchaseState.PENDING -> _pendingTip.value = true
            }
        }
    }

    /** Consume so the same tip can be given again later. */
    private fun consume(purchase: Purchase) {
        if (!consuming.add(purchase.purchaseToken)) return
        val consumeParams = ConsumeParams.newBuilder()
            .setPurchaseToken(purchase.purchaseToken)
            .build()
        billingClient.consumeAsync(consumeParams) { consumeResult, _ ->
            consuming.remove(purchase.purchaseToken)
            if (consumeResult.responseCode == BillingClient.BillingResponseCode.OK) {
                prefs.edit().putBoolean(KEY_HAS_TIPPED, true).apply()
                _pendingTip.value = false
                _showThanks.value = true
                _lastError.value = null
            }
            // A failed consume is not worth an error message: the money is
            // paid, the token is still owned, and the next refreshPurchases()
            // picks it up. Telling someone who just tipped that it failed
            // would be both alarming and wrong.
        }
    }

    /** Billing response codes as something a person can read. */
    private fun describe(result: BillingResult): String = when (result.responseCode) {
        BillingClient.BillingResponseCode.USER_CANCELED -> "cancelled"
        BillingClient.BillingResponseCode.SERVICE_DISCONNECTED,
        BillingClient.BillingResponseCode.SERVICE_UNAVAILABLE -> "the Play Store isn't reachable"
        BillingClient.BillingResponseCode.BILLING_UNAVAILABLE -> "this device can't make Play purchases"
        BillingClient.BillingResponseCode.ITEM_UNAVAILABLE -> "that tip isn't available here"
        BillingClient.BillingResponseCode.ITEM_ALREADY_OWNED -> "a previous tip is still being processed"
        BillingClient.BillingResponseCode.NETWORK_ERROR -> "no connection"
        BillingClient.BillingResponseCode.FEATURE_NOT_SUPPORTED -> "this device doesn't support it"
        else -> result.debugMessage.ifBlank { "error ${result.responseCode}" }
    }

    companion object {
        private const val KEY_USE_COUNT = "useCount"
        private const val KEY_DISMISSED = "dismissedForever"
        private const val KEY_NEXT_PROMPT_AT = "nextPromptAt"
        private const val KEY_HAS_TIPPED = "hasTipped"

        @Volatile private var instance: TipJarManager? = null

        fun getInstance(context: Context): TipJarManager =
            instance ?: synchronized(this) {
                instance ?: TipJarManager(context.applicationContext).also { instance = it }
            }
    }
}
