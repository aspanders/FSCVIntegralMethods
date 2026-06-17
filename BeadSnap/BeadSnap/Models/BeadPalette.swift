import Foundation

extension PaletteColor {
    static let beadSafe: [PaletteColor] = [
        .init(id: "white",        name: "White",        hex: "#FFFFFF"),
        .init(id: "cream",        name: "Cream",        hex: "#FFFDD0"),
        .init(id: "yellow",       name: "Yellow",       hex: "#F5D000"),
        .init(id: "banana",       name: "Banana",       hex: "#FFE135"),
        .init(id: "orange",       name: "Orange",       hex: "#FF8C00"),
        .init(id: "pumpkin",      name: "Pumpkin",      hex: "#FF6600"),
        .init(id: "red",          name: "Red",          hex: "#CC1122"),
        .init(id: "dark_red",     name: "Dark Red",     hex: "#8B0000"),
        .init(id: "pink",         name: "Pink",         hex: "#FF69B4"),
        .init(id: "hot_pink",     name: "Hot Pink",     hex: "#FF1493"),
        .init(id: "magenta",      name: "Magenta",      hex: "#FF00CC"),
        .init(id: "purple",       name: "Purple",       hex: "#800080"),
        .init(id: "dark_purple",  name: "Dark Purple",  hex: "#4B0082"),
        .init(id: "lavender",     name: "Lavender",     hex: "#9370DB"),
        .init(id: "periwinkle",   name: "Periwinkle",   hex: "#CCCCFF"),
        .init(id: "dark_blue",    name: "Dark Blue",    hex: "#00008B"),
        .init(id: "blue",         name: "Blue",         hex: "#1553B0"),
        .init(id: "sky_blue",     name: "Sky Blue",     hex: "#5BC8F5"),
        .init(id: "light_blue",   name: "Light Blue",   hex: "#87CEEB"),
        .init(id: "toothpaste",   name: "Toothpaste",   hex: "#B2FFFF"),
        .init(id: "teal",         name: "Teal",         hex: "#008080"),
        .init(id: "turquoise",    name: "Turquoise",    hex: "#40E0D0"),
        .init(id: "dark_green",   name: "Dark Green",   hex: "#006400"),
        .init(id: "green",        name: "Green",        hex: "#2E8B57"),
        .init(id: "light_green",  name: "Light Green",  hex: "#90EE90"),
        .init(id: "neon_green",   name: "Neon Green",   hex: "#39FF14"),
        .init(id: "olive",        name: "Olive",        hex: "#808000"),
        .init(id: "tan",          name: "Tan",          hex: "#D2B48C"),
        .init(id: "peach",        name: "Peach",        hex: "#FFCBA4"),
        .init(id: "skin",         name: "Skin",         hex: "#F4C2A1"),
        .init(id: "light_brown",  name: "Light Brown",  hex: "#C8A278"),
        .init(id: "brown",        name: "Brown",        hex: "#8B5E3C"),
        .init(id: "dark_brown",   name: "Dark Brown",   hex: "#4B2C20"),
        .init(id: "rust",         name: "Rust",         hex: "#8B3A2A"),
        .init(id: "caramel",      name: "Caramel",      hex: "#C68642"),
        .init(id: "black",        name: "Black",        hex: "#000000"),
        .init(id: "dark_gray",    name: "Dark Gray",    hex: "#444444"),
        .init(id: "gray",         name: "Gray",         hex: "#808080"),
        .init(id: "light_gray",   name: "Light Gray",   hex: "#C8C8C8"),
        .init(id: "silver",       name: "Silver",       hex: "#AAAAAA"),
    ]

    static let beadSafeByID: [String: PaletteColor] = {
        Dictionary(uniqueKeysWithValues: beadSafe.map { ($0.id, $0) })
    }()
}
