import SwiftUI

enum AppTab: Hashable {
    case library, create, studio
}

struct ContentView: View {
    @ObservedObject private var store = PatternStore.shared
    @ObservedObject private var tipJar = TipJarManager.shared
    @ObservedObject private var library = RemoteLibraryService.shared
    @State private var selectedTab: AppTab = .library
    @State private var showTipJar = false

    var body: some View {
        TabView(selection: $selectedTab) {
            LibraryView()
                .tabItem {
                    Label("Library", systemImage: "square.grid.2x2.fill")
                }
                .tag(AppTab.library)

            CreateView(onOpenAIStudio: { selectedTab = .studio })
                .tabItem {
                    Label("Create", systemImage: "plus.circle.fill")
                }
                .tag(AppTab.create)

            AIStudioView()
                .tabItem {
                    Label("Studio", systemImage: "wand.and.stars")
                }
                .tag(AppTab.studio)
        }
        .tint(.purple)
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
