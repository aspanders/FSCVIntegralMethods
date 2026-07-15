import SwiftUI

struct BeadColor: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let hex: String

    var uiColor: UIColor {
        UIColor(hex: hex)
    }

    var swiftUIColor: Color {
        Color(uiColor)
    }

    var rgb: (r: Double, g: Double, b: Double) {
        let c = UIColor(hex: hex)
        var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
        c.getRed(&r, green: &g, blue: &b, alpha: &a)
        return (Double(r), Double(g), Double(b))
    }

    var lab: (l: Double, a: Double, b: Double) {
        let (r, g, b) = rgb
        return BeadColor.rgbToLAB(r: r, g: g, b: b)
    }

    func distance(to other: BeadColor) -> Double {
        let l1 = lab, l2 = other.lab
        let dl = l1.l - l2.l
        let da = l1.a - l2.a
        let db = l1.b - l2.b
        return sqrt(dl * dl + da * da + db * db)
    }

    static func rgbToLAB(r: Double, g: Double, b: Double) -> (l: Double, a: Double, b: Double) {
        func linearize(_ c: Double) -> Double {
            c > 0.04045 ? pow((c + 0.055) / 1.055, 2.4) : c / 12.92
        }
        let rl = linearize(r), gl = linearize(g), bl = linearize(b)
        let x = (rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375) / 0.95047
        let y = (rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750) / 1.00000
        let z = (rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041) / 1.08883
        func f(_ t: Double) -> Double {
            t > 0.008856 ? pow(t, 1.0 / 3.0) : (7.787 * t + 16.0 / 116.0)
        }
        let L = 116.0 * f(y) - 16.0
        let A = 500.0 * (f(x) - f(y))
        let B = 200.0 * (f(y) - f(z))
        return (L, A, B)
    }
}

extension UIColor {
    convenience init(hex: String) {
        var hexSanitized = hex.trimmingCharacters(in: .alphanumerics.inverted)
        if hexSanitized.hasPrefix("#") { hexSanitized.removeFirst() }
        var rgb: UInt64 = 0
        Scanner(string: hexSanitized).scanHexInt64(&rgb)
        let r = CGFloat((rgb >> 16) & 0xFF) / 255
        let g = CGFloat((rgb >> 8) & 0xFF) / 255
        let b = CGFloat(rgb & 0xFF) / 255
        self.init(red: r, green: g, blue: b, alpha: 1)
    }
}

// MARK: - Full Perler Bead Palette
extension BeadColor {
    static let palette: [BeadColor] = [
        BeadColor(id: "white",          name: "White",          hex: "#FFFFFF"),
        BeadColor(id: "cream",          name: "Cream",          hex: "#FFFDD0"),
        BeadColor(id: "ivory",          name: "Ivory",          hex: "#FFFFF0"),
        BeadColor(id: "yellow",         name: "Yellow",         hex: "#F5D000"),
        BeadColor(id: "banana",         name: "Banana",         hex: "#FFE135"),
        BeadColor(id: "lemon",          name: "Lemon",          hex: "#FFF44F"),
        BeadColor(id: "neon_yellow",    name: "Neon Yellow",    hex: "#FCFC2C"),
        BeadColor(id: "orange",         name: "Orange",         hex: "#FF8C00"),
        BeadColor(id: "pumpkin",        name: "Pumpkin",        hex: "#FF6600"),
        BeadColor(id: "neon_orange",    name: "Neon Orange",    hex: "#FF5500"),
        BeadColor(id: "red",            name: "Red",            hex: "#CC1122"),
        BeadColor(id: "dark_red",       name: "Dark Red",       hex: "#8B0000"),
        BeadColor(id: "cheddar",        name: "Cheddar",        hex: "#FF9900"),
        BeadColor(id: "light_pink",     name: "Light Pink",     hex: "#FFB6C1"),
        BeadColor(id: "pink",           name: "Pink",           hex: "#FF69B4"),
        BeadColor(id: "hot_pink",       name: "Hot Pink",       hex: "#FF1493"),
        BeadColor(id: "magenta",        name: "Magenta",        hex: "#FF00CC"),
        BeadColor(id: "blush",          name: "Blush",          hex: "#FF9E9E"),
        BeadColor(id: "light_lavender", name: "Light Lavender", hex: "#E6E6FA"),
        BeadColor(id: "lavender",       name: "Lavender",       hex: "#9370DB"),
        BeadColor(id: "purple",         name: "Purple",         hex: "#800080"),
        BeadColor(id: "dark_purple",    name: "Dark Purple",    hex: "#4B0082"),
        BeadColor(id: "plum",           name: "Plum",           hex: "#8B008B"),
        BeadColor(id: "light_blue",     name: "Light Blue",     hex: "#87CEEB"),
        BeadColor(id: "sky_blue",       name: "Sky Blue",       hex: "#5BC8F5"),
        BeadColor(id: "periwinkle",     name: "Periwinkle",     hex: "#CCCCFF"),
        BeadColor(id: "blue",           name: "Blue",           hex: "#1553B0"),
        BeadColor(id: "dark_blue",      name: "Dark Blue",      hex: "#00008B"),
        BeadColor(id: "navy",           name: "Navy",           hex: "#001F5B"),
        BeadColor(id: "toothpaste",     name: "Toothpaste",     hex: "#B2FFFF"),
        BeadColor(id: "aqua",           name: "Aqua",           hex: "#00FFFF"),
        BeadColor(id: "light_teal",     name: "Light Teal",     hex: "#7FFFD4"),
        BeadColor(id: "teal",           name: "Teal",           hex: "#008080"),
        BeadColor(id: "turquoise",      name: "Turquoise",      hex: "#40E0D0"),
        BeadColor(id: "light_green",    name: "Light Green",    hex: "#90EE90"),
        BeadColor(id: "neon_green",     name: "Neon Green",     hex: "#39FF14"),
        BeadColor(id: "green",          name: "Green",          hex: "#2E8B57"),
        BeadColor(id: "dark_green",     name: "Dark Green",     hex: "#006400"),
        BeadColor(id: "army_green",     name: "Army Green",     hex: "#4B5320"),
        BeadColor(id: "forest",         name: "Forest",         hex: "#228B22"),
        BeadColor(id: "olive",          name: "Olive",          hex: "#808000"),
        BeadColor(id: "tan",            name: "Tan",            hex: "#D2B48C"),
        BeadColor(id: "peach",          name: "Peach",          hex: "#FFCBA4"),
        BeadColor(id: "skin",           name: "Skin",           hex: "#F4C2A1"),
        BeadColor(id: "light_brown",    name: "Light Brown",    hex: "#C8A278"),
        BeadColor(id: "brown",          name: "Brown",          hex: "#8B5E3C"),
        BeadColor(id: "dark_brown",     name: "Dark Brown",     hex: "#4B2C20"),
        BeadColor(id: "rust",           name: "Rust",           hex: "#8B3A2A"),
        BeadColor(id: "caramel",        name: "Caramel",        hex: "#C68642"),
        BeadColor(id: "black",          name: "Black",          hex: "#000000"),
        BeadColor(id: "dark_gray",      name: "Dark Gray",      hex: "#444444"),
        BeadColor(id: "gray",           name: "Gray",           hex: "#808080"),
        BeadColor(id: "light_gray",     name: "Light Gray",     hex: "#C8C8C8"),
        BeadColor(id: "silver",         name: "Silver",         hex: "#AAAAAA"),
        BeadColor(id: "clear",          name: "Clear",          hex: "#E8F4F8"),
    ]

    static let paletteByID: [String: BeadColor] = {
        Dictionary(uniqueKeysWithValues: palette.map { ($0.id, $0) })
    }()
}
