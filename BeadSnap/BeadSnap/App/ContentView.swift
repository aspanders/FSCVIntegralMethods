import SwiftUI

struct ContentView: View {
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
    }
}
