package com.beadsnap.app.services

import android.app.Activity
import android.content.Context
import android.content.SharedPreferences
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingClientStateListener
import com.android.billingclient.api.BillingFlowParams
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.ConsumeParams
import com.android.billingclient.api.ProductDetails
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.PurchasesUpdatedListener
import com.android.billingclient.api.QueryProductDetailsParams
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

    private val billingClient = BillingClient.newBuilder(context)
        .setListener(this)
        .enablePendingPurchases()
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

    private fun scheduleRetry() {
        val count = prefs.getInt(KEY_USE_COUNT, 0)
        prefs.edit().putInt(KEY_NEXT_PROMPT_AT, count + TipPromptLogic.LATER_RETRY_USES).apply()
    }

    // ─── Billing ──────────────────────────────────────────────────────────────

    fun connect() {
        if (billingClient.isReady) return
        billingClient.startConnection(object : BillingClientStateListener {
            override fun onBillingSetupFinished(result: BillingResult) {
                if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                    queryProducts()
                }
            }
            override fun onBillingServiceDisconnected() { /* retried on next connect() */ }
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
        billingClient.queryProductDetailsAsync(params) { result, details ->
            if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                _products.value = details.sortedBy {
                    it.oneTimePurchaseOfferDetails?.priceAmountMicros ?: 0
                }
            }
        }
    }

    fun purchase(activity: Activity, product: ProductDetails) {
        val flowParams = BillingFlowParams.newBuilder()
            .setProductDetailsParamsList(listOf(
                BillingFlowParams.ProductDetailsParams.newBuilder()
                    .setProductDetails(product)
                    .build()
            ))
            .build()
        billingClient.launchBillingFlow(activity, flowParams)
    }

    override fun onPurchasesUpdated(result: BillingResult, purchases: MutableList<Purchase>?) {
        if (result.responseCode != BillingClient.BillingResponseCode.OK || purchases == null) return
        for (purchase in purchases) {
            if (purchase.purchaseState == Purchase.PurchaseState.PURCHASED) {
                // Consume so the same tip can be given again later
                val consumeParams = ConsumeParams.newBuilder()
                    .setPurchaseToken(purchase.purchaseToken)
                    .build()
                billingClient.consumeAsync(consumeParams) { consumeResult, _ ->
                    if (consumeResult.responseCode == BillingClient.BillingResponseCode.OK) {
                        prefs.edit().putBoolean(KEY_HAS_TIPPED, true).apply()
                        _showThanks.value = true
                    }
                }
            }
        }
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
