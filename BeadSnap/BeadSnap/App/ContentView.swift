import SwiftUI

struct ContentView: View {
    @ObservedObject private var store = PatternStore.shared

    var body: some View {
        TabView {
            LibraryView()
                .tabItem {
                    Label("Library", systemImage: "square.grid.2x2.fill")
                }

            CreateView()
                .tabItem {
                    Label("Create", systemImage: "plus.circle.fill")
                }

            SavedPatternsView()
                .tabItem {
                    Label("My Patterns", systemImage: "heart.fill")
                }
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
