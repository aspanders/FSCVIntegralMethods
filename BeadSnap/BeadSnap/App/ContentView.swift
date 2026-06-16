import SwiftUI

struct ContentView: View {
    @State private var selectedTab: Tab = .create

    enum Tab {
        case create, draw, gallery
    }

    var body: some View {
        TabView(selection: $selectedTab) {
            HomeView()
                .tabItem {
                    Label("Create", systemImage: "camera.fill")
                }
                .tag(Tab.create)

            DrawView()
                .tabItem {
                    Label("Draw", systemImage: "pencil.and.outline")
                }
                .tag(Tab.draw)

            GalleryView()
                .tabItem {
                    Label("Gallery", systemImage: "photo.stack.fill")
                }
                .tag(Tab.gallery)
        }
        .tint(.purple)
    }
}
