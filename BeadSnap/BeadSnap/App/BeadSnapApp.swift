import SwiftUI

@main
struct BeadSnapApp: App {
    @StateObject private var persistence = PersistenceService.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(persistence)
        }
    }
}
