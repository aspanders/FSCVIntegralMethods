// Play Billing Library 8 stubs, written from the public API reference at
// developer.android.com/reference/com/android/billingclient/api/*.
//
// The point is NOT to emulate billing - nothing here does anything. It is to
// let a plain kotlinc type-check TipJarManager against the v8 signatures
// without an Android SDK, so a migration mistake (calling the removed no-arg
// enablePendingPurchases, or treating the queryProductDetailsAsync callback's
// second argument as a List) fails here instead of in Play Console.
//
// If a signature below disagrees with the real library, this file is wrong -
// fix it against the reference, not against the app.
package com.android.billingclient.api

import android.app.Activity
import android.content.Context

class BillingResult {
    val responseCode: Int = 0
    val debugMessage: String = ""
}

interface PurchasesUpdatedListener {
    fun onPurchasesUpdated(result: BillingResult, purchases: MutableList<Purchase>?)
}

interface BillingClientStateListener {
    fun onBillingSetupFinished(result: BillingResult)
    fun onBillingServiceDisconnected()
}

class ProductDetails {
    class OneTimePurchaseOfferDetails {
        val formattedPrice: String = ""
        val priceAmountMicros: Long = 0
    }
    val oneTimePurchaseOfferDetails: OneTimePurchaseOfferDetails? = null
    val productId: String = ""
    val title: String = ""
    val name: String = ""
    val description: String = ""
}

/** v8+: a query can return some products fetched and others not. */
class UnfetchedProduct {
    val productId: String = ""
    val productType: String = ""
    val statusCode: Int = 0
}

class QueryProductDetailsResult {
    val productDetailsList: List<ProductDetails> = emptyList()
    val unfetchedProductList: List<UnfetchedProduct> = emptyList()
}

class Purchase {
    object PurchaseState { const val PURCHASED = 1; const val PENDING = 2 }
    val purchaseState: Int = 0
    val purchaseToken: String = ""
    val products: List<String> = emptyList()
}

/** v8+: replaces the removed no-argument enablePendingPurchases(). */
class PendingPurchasesParams private constructor() {
    class Builder internal constructor() {
        fun enableOneTimeProducts(): Builder = this
        fun enablePrepaidPlans(): Builder = this
        fun build(): PendingPurchasesParams = PendingPurchasesParams()
    }
    companion object { @JvmStatic fun newBuilder(): Builder = Builder() }
}

class QueryProductDetailsParams private constructor() {
    class Product private constructor() {
        class Builder internal constructor() {
            fun setProductId(id: String): Builder = this
            fun setProductType(type: String): Builder = this
            fun build(): Product = Product()
        }
        companion object { @JvmStatic fun newBuilder(): Builder = Builder() }
    }
    class Builder internal constructor() {
        fun setProductList(products: List<Product>): Builder = this
        fun build(): QueryProductDetailsParams = QueryProductDetailsParams()
    }
    companion object { @JvmStatic fun newBuilder(): Builder = Builder() }
}

class BillingFlowParams private constructor() {
    class ProductDetailsParams private constructor() {
        class Builder internal constructor() {
            fun setProductDetails(details: ProductDetails): Builder = this
            fun setOfferToken(token: String): Builder = this
            fun build(): ProductDetailsParams = ProductDetailsParams()
        }
        companion object { @JvmStatic fun newBuilder(): Builder = Builder() }
    }
    class Builder internal constructor() {
        fun setProductDetailsParamsList(list: List<ProductDetailsParams>): Builder = this
        fun build(): BillingFlowParams = BillingFlowParams()
    }
    companion object { @JvmStatic fun newBuilder(): Builder = Builder() }
}

/** The v5+ shape: purchases are queried per product type. */
class QueryPurchasesParams private constructor() {
    class Builder internal constructor() {
        fun setProductType(type: String): Builder = this
        fun build(): QueryPurchasesParams = QueryPurchasesParams()
    }
    companion object { @JvmStatic fun newBuilder(): Builder = Builder() }
}

/**
 * A Java interface in the real library, so a Kotlin lambda reaches it by SAM
 * conversion. Modelled as a fun interface rather than a function type so the
 * call site here is the same one the real library accepts. The list is
 * non-null: "no purchases" is an empty list, not null.
 */
fun interface PurchasesResponseListener {
    fun onQueryPurchasesResponse(result: BillingResult, purchases: List<Purchase>)
}

class ConsumeParams private constructor() {
    class Builder internal constructor() {
        fun setPurchaseToken(token: String): Builder = this
        fun build(): ConsumeParams = ConsumeParams()
    }
    companion object { @JvmStatic fun newBuilder(): Builder = Builder() }
}

class BillingClient private constructor() {
    // The real values, from the reference. The negatives are client-side
    // states (the service binding), the positives come back from Play.
    object BillingResponseCode {
        const val SERVICE_TIMEOUT = -3
        const val FEATURE_NOT_SUPPORTED = -2
        const val SERVICE_DISCONNECTED = -1
        const val OK = 0
        const val USER_CANCELED = 1
        const val SERVICE_UNAVAILABLE = 2
        const val BILLING_UNAVAILABLE = 3
        const val ITEM_UNAVAILABLE = 4
        const val DEVELOPER_ERROR = 5
        const val ERROR = 6
        const val ITEM_ALREADY_OWNED = 7
        const val ITEM_NOT_OWNED = 8
        const val NETWORK_ERROR = 12
    }
    object ProductType { const val INAPP = "inapp"; const val SUBS = "subs" }

    class Builder internal constructor() {
        fun setListener(listener: PurchasesUpdatedListener): Builder = this
        // v8 REMOVED the no-argument form; this is the only overload.
        fun enablePendingPurchases(params: PendingPurchasesParams): Builder = this
        fun enableAutoServiceReconnection(): Builder = this
        fun build(): BillingClient = BillingClient()
    }

    val isReady: Boolean = false
    fun startConnection(listener: BillingClientStateListener) {}
    fun endConnection() {}
    // v8 CHANGED the callback's second argument from List<ProductDetails>.
    fun queryProductDetailsAsync(
        params: QueryProductDetailsParams,
        listener: (BillingResult, QueryProductDetailsResult) -> Unit
    ) {}
    fun launchBillingFlow(activity: Activity, params: BillingFlowParams): BillingResult =
        BillingResult()
    fun queryPurchasesAsync(params: QueryPurchasesParams, listener: PurchasesResponseListener) {}
    fun consumeAsync(params: ConsumeParams, listener: (BillingResult, String) -> Unit) {}

    companion object {
        @JvmStatic fun newBuilder(context: Context): Builder = Builder()
    }
}
