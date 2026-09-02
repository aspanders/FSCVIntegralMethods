import SwiftUI

enum AppTab: Hashable {
    // The AI studio is deliberately NOT a tab. It is reached from Create,
    // which is where somebody looking to make something goes, and the slot it
    // held now belongs to the user's own work - far more useful in one tap
    // than a second door to a screen Create already opens. Matches Android.
    case library, create, mine
}

struct ContentView: View {
    @ObservedObject private var store = PatternStore.shared
    @ObservedObject private var tipJar = TipJarManager.shared
    @ObservedObject private var library = RemoteLibraryService.shared
    @State private var selectedTab: AppTab = .library
    @State private var showTipJar = false
    @State private var showStudio = false

    var body: some View {
        TabView(selection: $selectedTab) {
            LibraryView()
                .tabItem {
                    Label("Library", systemImage: "square.grid.2x2.fill")
                }
                .tag(AppTab.library)

            CreateView(onOpenAIStudio: { showStudio = true })
                .tabItem {
                    Label("Create", systemImage: "plus.circle.fill")
                }
                .tag(AppTab.create)

            MyCreationsView()
                .tabItem {
                    Label("Mine", systemImage: "paintbrush.pointed.fill")
                }
                .tag(AppTab.mine)
        }
        .tint(.purple)
        // A sheet rather than a tab. Presented this way it is dismissible by
        // swipe as well as by its own Close button, so there is no way to end
        // up stranded on it - which is exactly what removing it from the tab
        // bar risked, and what caught out the Android side.
        .sheet(isPresented: $showStudio) {
            AIStudioView(onClose: { showStudio = false })
        }
        .onAppear { tipJar.recordUse() }
        .task { await library.syncIfNeeded() }
        .overlay(alignment: .bottom) {
            if tipJar.shouldShowPrompt {
                TipPromptBanner(onDonate: { showTipJar = true })
                    .padding(.bottom, 60)   // clear the tab bar
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .overlay(alignment: .top) {
            if let count = library.updateApplied {
                libraryUpdateBanner(count)
                    .transition(.move(edge: .top).combined(with: .opacity))
                    .onAppear {
                        DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                            withAnimation { library.updateApplied = nil }
                        }
                    }
            }
        }
        .animation(.spring(duration: 0.4), value: tipJar.shouldShowPrompt)
        .animation(.easeInOut(duration: 0.25), value: library.updateApplied)
        .sheet(isPresented: $showTipJar) {
            TipJarView()
        }
        .alert("Save Error", isPresented: Binding(
            get: { store.lastError != nil },
            set: { if !$0 { store.clearLastError() } }
        )) {
            Button("OK", role: .cancel) { store.clearLastError() }
        } message: {
            Text(store.lastError ?? "")
        }
    }

    private func libraryUpdateBanner(_ count: Int) -> some View {
        HStack(spacing: 8) {
            Image(systemName: "square.grid.2x2.fill").foregroundStyle(.purple)
            Text("Pattern library updated: \(count) patterns")
                .font(.subheadline.bold())
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 10)
        .background(.regularMaterial, in: Capsule())
        .shadow(radius: 4, y: 2)
        .padding(.top, 8)
    }
}
