import SwiftUI
import StoreKit

// MARK: - Tip jar sheet (reachable anytime from the Library toolbar)

struct TipJarView: View {
    @ObservedObject private var tipJar = TipJarManager.shared
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    VStack(spacing: 12) {
                        Image(systemName: "heart.circle.fill")
                            .font(.system(size: 52))
                            .foregroundStyle(.pink)
                        Text("Support BeadSnap")
                            .font(.title3.bold())
                        Text("BeadSnap is a father-and-son project, built just to be a fun, safe place to design fuse beads.\n\nIt's free forever: no ads, no accounts, no subscriptions, no fees, no premium features locked behind a paywall. We don't collect or share your data, and we never ask for your email.\n\nIf it's brought your family a little joy, a tip helps us keep building it. Every donation goes right back into the app.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                    .listRowBackground(Color.clear)
                }

                if tipJar.showThanks {
                    Section {
                        Label("Thank you so much! 💜", systemImage: "checkmark.circle.fill")
                            .foregroundStyle(.green)
                            .font(.headline)
                            .frame(maxWidth: .infinity)
                    }
                } else if tipJar.products.isEmpty {
                    Section {
                        HStack {
                            Spacer()
                            ProgressView()
                            Text("Loading tip options…")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                            Spacer()
                        }
                    }
                } else {
                    Section("Leave a tip") {
                        ForEach(headlineProducts, id: \.id) { product in
                            tipButton(product)
                        }
                    }
                    if !customProducts.isEmpty {
                        Section("Custom amount") {
                            ForEach(customProducts, id: \.id) { product in
                                tipButton(product)
                            }
                        }
                    }
                }

                // Feedback: opens Mail. No account, no data collection.
                Section {
                    if let url = URL(string: "mailto:andersjasp@gmail.com?subject=BeadSnap%20feedback") {
                        Link(destination: url) {
                            Label("Leave a comment", systemImage: "bubble.left")
                        }
                    }
                } footer: {
                    Text("Got an idea or a bug? We read every message.")
                }
            }
            .navigationTitle("Tip Jar")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .task { await tipJar.loadProducts() }
            .onDisappear { tipJar.showThanks = false }
        }
        .presentationDetents([.medium, .large])
    }

    private var headlineProducts: [Product] {
        tipJar.products.filter { TipJarManager.headlineProductIDs.contains($0.id) }
    }
    private var customProducts: [Product] {
        tipJar.products
            .filter { TipJarManager.customProductIDs.contains($0.id) }
            .sorted { $0.price < $1.price }
    }

    @ViewBuilder
    private func tipButton(_ product: Product) -> some View {
        Button {
            Task { await tipJar.purchase(product) }
        } label: {
            HStack {
                Text(tipEmoji(for: product.id))
                Text(tipName(for: product.id))
                Spacer()
                Text(product.displayPrice)
                    .foregroundStyle(.secondary)
                    .monospacedDigit()
            }
        }
        .disabled(tipJar.isPurchasing)
    }

    private func tipEmoji(for id: String) -> String {
        switch id {
        case "tip_small":       return "🍬"
        case "tip_medium":      return "☕️"
        case "tip_large":       return "🧁"
        case "tip_custom_20":   return "🎁"
        case "tip_custom_50":   return "🌟"
        case "tip_custom_100":  return "💎"
        default:                return "💜"
        }
    }

    private func tipName(for id: String) -> String {
        switch id {
        case "tip_small":       return "Small tip"
        case "tip_medium":      return "Nice tip"
        case "tip_large":       return "Amazing tip"
        case "tip_custom_20":   return "Generous tip"
        case "tip_custom_50":   return "Incredible tip"
        case "tip_custom_100":  return "Legendary tip"
        default:                return "Tip"
        }
    }
}

// MARK: - One-time prompt banner (Wikipedia-style, in-app)

struct TipPromptBanner: View {
    @ObservedObject private var tipJar = TipJarManager.shared
    var onDonate: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 10) {
                Image(systemName: "heart.circle.fill")
                    .font(.title2)
                    .foregroundStyle(.pink)
                Text("Enjoying BeadSnap?")
                    .font(.headline)
                Spacer()
            }
            Text("You've opened BeadSnap 10 times! It's free with no ads. If it's earned a place in your craft kit, consider leaving a small tip.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)
            HStack(spacing: 10) {
                Button {
                    tipJar.promptDonateNow()
                    onDonate()
                } label: {
                    Text("Leave a tip")
                        .font(.subheadline.bold())
                        .padding(.horizontal, 14)
                        .padding(.vertical, 7)
                        .background(Color.pink, in: Capsule())
                        .foregroundStyle(.white)
                }
                Button("Maybe later") {
                    withAnimation { tipJar.promptMaybeLater() }
                }
                .font(.subheadline)
                Button("No thanks") {
                    withAnimation { tipJar.promptDismissForever() }
                }
                .font(.subheadline)
                .foregroundStyle(.secondary)
                Spacer()
            }
        }
        .padding(16)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
        .shadow(color: .black.opacity(0.15), radius: 10, y: 4)
        .padding(.horizontal, 16)
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Tip jar: enjoying BeadSnap? Leave a tip, maybe later, or no thanks.")
    }
}
