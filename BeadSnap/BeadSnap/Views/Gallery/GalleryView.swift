import SwiftUI

struct GalleryView: View {
    @ObservedObject private var persistence = PersistenceService.shared
    @State private var selectedProject: Project?
    @State private var showingDeleteConfirm = false
    @State private var projectToDelete: Project?

    private let columns = [
        GridItem(.flexible(), spacing: 12),
        GridItem(.flexible(), spacing: 12),
    ]

    var body: some View {
        NavigationStack {
            Group {
                if persistence.projects.isEmpty {
                    emptyState
                } else {
                    ScrollView {
                        LazyVGrid(columns: columns, spacing: 12) {
                            ForEach(persistence.projects) { project in
                                ProjectCard(project: project)
                                    .onTapGesture {
                                        selectedProject = project
                                    }
                                    .contextMenu {
                                        Button(role: .destructive) {
                                            projectToDelete = project
                                            showingDeleteConfirm = true
                                        } label: {
                                            Label("Delete", systemImage: "trash")
                                        }
                                    }
                            }
                        }
                        .padding(16)
                    }
                }
            }
            .navigationTitle("My Patterns")
            .navigationBarTitleDisplayMode(.large)
            .navigationDestination(item: $selectedProject) { project in
                ProjectDetailView(project: project)
            }
            .confirmationDialog(
                "Delete this project?",
                isPresented: $showingDeleteConfirm,
                titleVisibility: .visible
            ) {
                Button("Delete", role: .destructive) {
                    if let proj = projectToDelete {
                        persistence.deleteProject(proj)
                    }
                }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("This will permanently remove the photo and all patterns.")
            }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 20) {
            Image(systemName: "photo.on.rectangle.angled")
                .font(.system(size: 72))
                .foregroundStyle(.secondary)

            Text("No Patterns Yet!")
                .font(.title2.bold())

            Text("Take a photo or draw something\nto create your first bead pattern")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
    }
}

struct ProjectCard: View {
    let project: Project
    @State private var thumbnail: UIImage?

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Thumbnail
            ZStack {
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(Color(.secondarySystemBackground))

                if let thumb = thumbnail {
                    Image(uiImage: thumb)
                        .resizable()
                        .scaledToFill()
                        .clipped()
                } else {
                    Image(systemName: project.sourceType == .drawing ? "pencil.and.outline" : "photo")
                        .font(.largeTitle)
                        .foregroundColor(.secondary)
                }
            }
            .frame(height: 140)
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))

            VStack(alignment: .leading, spacing: 4) {
                Text(project.name)
                    .font(.subheadline.bold())
                    .lineLimit(1)

                HStack(spacing: 4) {
                    Image(systemName: "circle.grid.3x3")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    Text("\(project.patterns.count) pattern\(project.patterns.count == 1 ? "" : "s")")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 10)
        }
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(Color(.systemBackground))
                .shadow(color: .black.opacity(0.06), radius: 6, x: 0, y: 3)
        )
        .onAppear {
            if let data = project.thumbnail {
                thumbnail = UIImage(data: data)
            } else {
                thumbnail = PersistenceService.shared.loadImage(named: project.originalImageFilename)
            }
        }
    }
}
