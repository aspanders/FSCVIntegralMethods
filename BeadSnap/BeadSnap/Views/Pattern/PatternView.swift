import SwiftUI

struct PatternView: View {
    let image: UIImage
    let originalImage: UIImage
    var existingProject: Project? = nil

    @StateObject private var vm: PatternViewModel
    @State private var showEditor = false
    @State private var showInventory = false
    @State private var showShareSheet = false
    @State private var shareImage: UIImage?

    init(image: UIImage, originalImage: UIImage, project: Project? = nil) {
        self.image = image
        self.originalImage = originalImage
        self.existingProject = project
        self._vm = StateObject(wrappedValue: PatternViewModel(image: image, project: project))
    }

    var body: some View {
        ZStack {
            Color(.systemGroupedBackground).ignoresSafeArea()

            VStack(spacing: 0) {
                patternCanvas
                configPanel
            }
        }
        .navigationTitle("Your Pattern")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                HStack(spacing: 16) {
                    if vm.pattern != nil {
                        Button {
                            showInventory.toggle()
                        } label: {
                            Image(systemName: "list.bullet.clipboard")
                        }
                        Button {
                            if let img = vm.renderedImage {
                                shareImage = img
                                showShareSheet = true
                            }
                        } label: {
                            Image(systemName: "square.and.arrow.up")
                        }
                    }
                }
            }
        }
        .task {
            if vm.pattern == nil {
                await vm.generatePattern()
            }
        }
        .navigationDestination(isPresented: $showEditor) {
            PatternEditorView(vm: vm)
        }
        .sheet(isPresented: $showInventory) {
            InventorySheet(vm: vm)
        }
        .sheet(isPresented: $showShareSheet) {
            if let img = shareImage {
                ShareSheet(activityItems: [img])
            }
        }
    }

    private var patternCanvas: some View {
        GeometryReader { geo in
            ZStack {
                if vm.isConverting {
                    VStack(spacing: 16) {
                        ProgressView()
                            .scaleEffect(2)
                        Text("Creating your pattern...")
                            .font(.headline)
                        Text("✨ Almost ready! ✨")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let pattern = vm.pattern {
                    ScrollView([.horizontal, .vertical]) {
                        BeadPatternCanvas(pattern: pattern, interactive: false)
                            .frame(
                                width: CGFloat(pattern.cols) * beadSize(geo: geo, pattern: pattern),
                                height: CGFloat(pattern.rows) * beadSize(geo: geo, pattern: pattern)
                            )
                    }
                    .background(Color(.secondarySystemBackground))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .padding(16)
                }
            }
        }
    }

    private func beadSize(geo: GeometryProxy, pattern: BeadPattern) -> CGFloat {
        let available = min(geo.size.width, geo.size.height) - 32
        let maxBeads = CGFloat(max(pattern.cols, pattern.rows))
        return max(4, available / maxBeads)
    }

    private var configPanel: some View {
        VStack(spacing: 0) {
            Divider()
            VStack(spacing: 16) {
                // Size picker
                VStack(alignment: .leading, spacing: 8) {
                    Text("Size")
                        .font(.caption.bold())
                        .foregroundColor(.secondary)
                        .padding(.horizontal)

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 10) {
                            ForEach(PatternSize.allCases) { size in
                                SizeChip(
                                    size: size,
                                    isSelected: vm.config.size == size
                                ) {
                                    vm.updateConfig(PatternConfig(size: size, layout: vm.config.layout))
                                }
                            }
                        }
                        .padding(.horizontal)
                    }
                }

                // Layout picker
                VStack(alignment: .leading, spacing: 8) {
                    Text("Board Shape")
                        .font(.caption.bold())
                        .foregroundColor(.secondary)
                        .padding(.horizontal)

                    HStack(spacing: 10) {
                        ForEach(PatternLayout.allCases) { layout in
                            LayoutChip(
                                layout: layout,
                                isSelected: vm.config.layout == layout
                            ) {
                                vm.updateConfig(PatternConfig(size: vm.config.size, layout: layout))
                            }
                        }
                        Spacer()
                    }
                    .padding(.horizontal)
                }

                // Edit button
                if vm.pattern != nil {
                    KidButton(
                        title: "Edit Beads",
                        icon: "pencil.circle.fill",
                        color: .blue,
                        size: .regular
                    ) {
                        showEditor = true
                    }
                    .padding(.horizontal)
                    .padding(.bottom, 8)
                }
            }
            .padding(.vertical, 16)
            .background(.regularMaterial)
        }
    }
}

struct SizeChip: View {
    let size: PatternSize
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Text(size.emoji)
                    .font(.title3)
                Text(size.displayName)
                    .font(.caption.bold())
                Text(size.subtitle)
                    .font(.caption2)
                    .foregroundColor(isSelected ? .white.opacity(0.8) : .secondary)
                    .multilineTextAlignment(.center)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(isSelected ? Color.blue : Color(.secondarySystemBackground))
            )
            .foregroundColor(isSelected ? .white : .primary)
        }
        .buttonStyle(.plain)
        .fixedSize()
    }
}

struct LayoutChip: View {
    let layout: PatternLayout
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Text(layout.emoji)
                Text(layout.displayName)
                    .font(.subheadline.bold())
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(
                RoundedRectangle(cornerRadius: 10)
                    .fill(isSelected ? Color.purple : Color(.secondarySystemBackground))
            )
            .foregroundColor(isSelected ? .white : .primary)
        }
        .buttonStyle(.plain)
    }
}

struct BeadPatternCanvas: View {
    let pattern: BeadPattern
    var interactive: Bool = false
    var onTap: ((Int, Int) -> Void)?

    var body: some View {
        Canvas { context, size in
            let beadW = size.width / CGFloat(pattern.cols)
            let beadH = size.height / CGFloat(pattern.rows)
            let bead = min(beadW, beadH)

            for row in 0..<pattern.rows {
                for col in 0..<pattern.cols {
                    let x = CGFloat(col) * bead
                    let y = CGFloat(row) * bead
                    let rect = CGRect(x: x, y: y, width: bead, height: bead)
                    let inset = bead * 0.06
                    let ovalRect = rect.insetBy(dx: inset, dy: inset)

                    if let color = pattern.color(row: row, col: col) {
                        context.fill(Path(ellipseIn: ovalRect), with: .color(color.swiftUIColor))
                        context.stroke(
                            Path(ellipseIn: ovalRect),
                            with: .color(.black.opacity(0.15)),
                            lineWidth: 0.4
                        )
                    } else if pattern.isInsideCircle(row: row, col: col) {
                        context.fill(
                            Path(ellipseIn: ovalRect),
                            with: .color(Color(.systemGray5))
                        )
                    }
                }
            }
        }
        .gesture(
            interactive ? TapGesture().onEnded({ _ in }) : nil
        )
    }
}

struct InventorySheet: View {
    @ObservedObject var vm: PatternViewModel
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationStack {
            List {
                Section("Total Beads: \(vm.pattern?.totalBeads ?? 0)") {
                    ForEach(vm.colorInventory, id: \.color.id) { item in
                        HStack(spacing: 12) {
                            Circle()
                                .fill(item.color.swiftUIColor)
                                .frame(width: 28, height: 28)
                                .shadow(radius: 2)
                            Text(item.color.name)
                                .font(.body)
                            Spacer()
                            Text("\(item.count)")
                                .font(.headline.monospacedDigit())
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
            .navigationTitle("Bead Inventory")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}

struct ShareSheet: UIViewControllerRepresentable {
    let activityItems: [Any]

    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: activityItems, applicationActivities: nil)
    }

    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}
