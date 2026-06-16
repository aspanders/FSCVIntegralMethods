import SwiftUI

struct ProjectDetailView: View {
    let project: Project
    @State private var selectedPatternIndex: Int = 0
    @State private var originalImage: UIImage?
    @State private var maskedImage: UIImage?
    @State private var showingPatternEditor = false
    @State private var showingAddSize = false

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Original photo
                photoSection

                // Pattern list
                if project.patterns.isEmpty {
                    emptyPatternsCard
                } else {
                    patternCarousel
                    selectedPatternDetail
                }

                // Add size button
                addSizeButton
            }
            .padding(16)
        }
        .navigationTitle(project.name)
        .navigationBarTitleDisplayMode(.large)
        .onAppear { loadImages() }
    }

    private func loadImages() {
        originalImage = PersistenceService.shared.loadImage(named: project.originalImageFilename)
        if let masked = project.maskedImageFilename {
            maskedImage = PersistenceService.shared.loadImage(named: masked)
        }
    }

    private var photoSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Original Photo")
                .font(.headline)
                .padding(.horizontal, 4)

            HStack(spacing: 12) {
                if let orig = originalImage {
                    imageCard(orig, label: "Original")
                }
                if let masked = maskedImage {
                    imageCard(masked, label: "Background Removed")
                }
            }
        }
    }

    private func imageCard(_ image: UIImage, label: String) -> some View {
        VStack(spacing: 6) {
            Image(uiImage: image)
                .resizable()
                .scaledToFit()
                .frame(maxHeight: 160)
                .clipShape(RoundedRectangle(cornerRadius: 10))
                .background(CheckerboardView().clipShape(RoundedRectangle(cornerRadius: 10)))
            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
    }

    private var patternCarousel: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Patterns (\(project.patterns.count))")
                .font(.headline)
                .padding(.horizontal, 4)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    ForEach(Array(project.patterns.enumerated()), id: \.element.id) { idx, pattern in
                        PatternThumbCard(
                            pattern: pattern,
                            isSelected: idx == selectedPatternIndex
                        )
                        .onTapGesture { selectedPatternIndex = idx }
                    }
                }
            }
        }
    }

    private var selectedPatternDetail: some View {
        let safeIdx = min(selectedPatternIndex, project.patterns.count - 1)
        let pattern = project.patterns[safeIdx]
        return VStack(spacing: 16) {
            // Pattern preview
            BeadPatternCanvas(pattern: pattern)
                .frame(height: 280)
                .background(Color(.secondarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 12))

            // Stats
            HStack(spacing: 20) {
                statBadge(
                    value: "\(pattern.cols)×\(pattern.rows)",
                    label: "Size",
                    icon: "square.grid.2x2"
                )
                statBadge(
                    value: "\(pattern.totalBeads)",
                    label: "Beads",
                    icon: "circle.fill"
                )
                statBadge(
                    value: "\(pattern.colorCount.count)",
                    label: "Colors",
                    icon: "paintpalette"
                )
            }

            // Action buttons
            HStack(spacing: 12) {
                if let img = originalImage {
                    NavigationLink(
                        destination: PatternEditorView(
                            vm: PatternViewModel(image: maskedImage ?? img, project: project)
                        )
                    ) {
                        Label("Edit Beads", systemImage: "pencil.circle.fill")
                            .font(.subheadline.bold())
                            .padding(.horizontal, 16)
                            .padding(.vertical, 10)
                            .background(Color.blue.opacity(0.1))
                            .foregroundColor(.blue)
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                    }
                }

                Button {
                    let rendered = PatternConverter.shared.renderPatternImage(pattern: pattern)
                    let av = UIActivityViewController(
                        activityItems: [rendered],
                        applicationActivities: nil
                    )
                    if let scene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
                       let vc = scene.windows.first?.rootViewController {
                        vc.present(av, animated: true)
                    }
                } label: {
                    Label("Share / Print", systemImage: "square.and.arrow.up")
                        .font(.subheadline.bold())
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .background(Color.green.opacity(0.1))
                        .foregroundColor(.green)
                        .clipShape(RoundedRectangle(cornerRadius: 10))
                }
            }
        }
    }

    private func statBadge(value: String, label: String, icon: String) -> some View {
        VStack(spacing: 4) {
            Image(systemName: icon)
                .foregroundColor(.purple)
            Text(value)
                .font(.headline.monospacedDigit())
            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 12)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var emptyPatternsCard: some View {
        VStack(spacing: 12) {
            Image(systemName: "wand.and.stars")
                .font(.largeTitle)
                .foregroundColor(.purple)
            Text("No patterns yet")
                .font(.headline)
            Text("Tap below to generate your first pattern")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .padding(24)
        .frame(maxWidth: .infinity)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }

    private var addSizeButton: some View {
        Group {
            if let img = maskedImage ?? originalImage {
                NavigationLink(
                    destination: PatternView(
                        image: img,
                        originalImage: originalImage ?? img,
                        project: project
                    )
                ) {
                    addSizeLabel
                }
            } else {
                addSizeLabel.opacity(0.5)
            }
        }
    }

    private var addSizeLabel: some View {
        HStack {
            Image(systemName: "plus.circle.fill")
            Text("Generate New Size")
                .font(.headline)
        }
        .foregroundColor(.white)
        .padding(.vertical, 14)
        .frame(maxWidth: .infinity)
        .background(Color.purple.gradient)
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }
}

struct PatternThumbCard: View {
    let pattern: BeadPattern
    let isSelected: Bool

    var body: some View {
        VStack(spacing: 6) {
            BeadPatternCanvas(pattern: pattern)
                .frame(width: 100, height: 100)
                .background(Color(.secondarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 8))
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .strokeBorder(isSelected ? Color.purple : Color.clear, lineWidth: 2)
                )

            Text(pattern.config.size.displayName)
                .font(.caption2.bold())
                .foregroundColor(isSelected ? .purple : .secondary)

            Text(pattern.config.layout.displayName)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
    }
}
