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
                        Text("BeadSnap is free, has no ads, and never sells your data. If it's brought you a little joy, a tip helps keep it that way.")
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
                        ForEach(tipJar.products, id: \.id) { product in
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
                    }
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
        .presentationDetents([.medium])
    }

    private func tipEmoji(for id: String) -> String {
        switch id {
        case "tip_small":  return "🍬"
        case "tip_medium": return "☕️"
        default:           return "🧁"
        }
    }

    private func tipName(for id: String) -> String {
        switch id {
        case "tip_small":  return "Small tip"
        case "tip_medium": return "Nice tip"
        default:           return "Amazing tip"
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
            Text("You've opened BeadSnap 10 times! It's free with no ads — if it's earned a place in your craft kit, consider leaving a small tip.")
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
