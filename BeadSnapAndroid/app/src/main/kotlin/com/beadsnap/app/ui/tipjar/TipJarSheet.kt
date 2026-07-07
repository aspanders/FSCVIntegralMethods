package com.beadsnap.app.ui.tipjar

import android.app.Activity
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.android.billingclient.api.ProductDetails
import com.beadsnap.app.services.TipJarManager

// ─── Tip jar sheet (reachable anytime from the Library toolbar) ────────────────

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TipJarSheet(
    tipJar: TipJarManager,
    onDismiss: () -> Unit
) {
    val products   by tipJar.products.collectAsState()
    val showThanks by tipJar.showThanks.collectAsState()
    val context    = LocalContext.current

    LaunchedEffect(Unit) { tipJar.connect() }
    DisposableEffect(Unit) { onDispose { tipJar.clearThanks() } }

    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp)
                .padding(bottom = 40.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Icon(
                Icons.Default.Favorite, contentDescription = null,
                modifier = Modifier.size(52.dp),
                tint = MaterialTheme.colorScheme.error
            )
            Text("Support BeadSnap", style = MaterialTheme.typography.titleLarge)
            Text(
                "BeadSnap is free, has no ads, and never sells your data. " +
                "If it's brought you a little joy, a tip helps keep it that way.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center
            )
            Spacer(Modifier.height(4.dp))

            when {
                showThanks -> {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(Icons.Default.CheckCircle, contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary)
                        Text("Thank you so much! 💜", style = MaterialTheme.typography.titleMedium)
                    }
                }
                products.isEmpty() -> {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        CircularProgressIndicator(modifier = Modifier.size(20.dp))
                        Text("Loading tip options…",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
                else -> {
                    products.forEach { product ->
                        TipOptionRow(product = product) {
                            (context as? Activity)?.let { tipJar.purchase(it, product) }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun TipOptionRow(product: ProductDetails, onClick: () -> Unit) {
    val (emoji, name) = when (product.productId) {
        "tip_small"  -> "🍬" to "Small tip"
        "tip_medium" -> "☕️" to "Nice tip"
        else         -> "🧁" to "Amazing tip"
    }
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(emoji, style = MaterialTheme.typography.titleMedium)
            Text(name, style = MaterialTheme.typography.bodyLarge, modifier = Modifier.weight(1f))
            Text(
                product.oneTimePurchaseOfferDetails?.formattedPrice ?: "",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

// ─── One-time prompt banner (Wikipedia-style, in-app) ─────────────────────────

@Composable
fun TipPromptBanner(
    tipJar: TipJarManager,
    onDonate: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier.padding(horizontal = 16.dp),
        shape = RoundedCornerShape(16.dp),
        tonalElevation = 6.dp,
        shadowElevation = 8.dp
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Icon(Icons.Default.Favorite, contentDescription = null,
                    tint = MaterialTheme.colorScheme.error)
                Text("Enjoying BeadSnap?", style = MaterialTheme.typography.titleMedium)
            }
            Text(
                "You've opened BeadSnap 10 times! It's free with no ads — if it's earned a place in your craft kit, consider leaving a small tip.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Button(onClick = { tipJar.promptDonateNow(); onDonate() }) {
                    Text("Leave a tip")
                }
                TextButton(onClick = { tipJar.promptMaybeLater() }) {
                    Text("Maybe later")
                }
                TextButton(onClick = { tipJar.promptDismissForever() }) {
                    Text("No thanks", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}
