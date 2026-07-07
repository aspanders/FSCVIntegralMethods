import SwiftUI

enum AppTab: Hashable {
    case library, create, studio
}

struct ContentView: View {
    @ObservedObject private var store = PatternStore.shared
    @State private var selectedTab: AppTab = .library

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
        .alert("Save Error", isPresented: Binding(
            get: { store.lastError != nil },
            set: { if !$0 { store.clearLastError() } }
        )) {
            Button("OK", role: .cancel) { store.clearLastError() }
        } message: {
            Text(store.lastError ?? "")
        }
    }
}
