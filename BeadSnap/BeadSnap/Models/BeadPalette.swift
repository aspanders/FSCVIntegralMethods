import Foundation

extension PaletteColor {
    /// The full 55-color bead palette, bridged from BeadColor.palette so both
    /// stay in lockstep (and identical to the Android palette).
    static let full: [PaletteColor] = BeadColor.palette.map {
        PaletteColor(id: $0.id, name: $0.name, hex: $0.hex)
    }

    static let fullByID: [String: PaletteColor] = {
        Dictionary(uniqueKeysWithValues: full.map { ($0.id, $0) })
    }()

    /// Starter palette for a new blank canvas: the classic 8 every kit has.
    /// Must match BeadColor.defaultPalette on Android.
    static let defaultPalette: [PaletteColor] = [
        "white", "black", "red", "blue", "green", "yellow", "orange", "brown"
    ].compactMap { fullByID[$0] }
}
