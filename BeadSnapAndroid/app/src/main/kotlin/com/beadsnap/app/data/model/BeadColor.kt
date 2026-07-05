package com.beadsnap.app.data.model

import android.graphics.Color as AndroidColor
import androidx.compose.ui.graphics.Color
import kotlinx.serialization.Serializable
import kotlin.math.pow
import kotlin.math.sqrt

@Serializable
data class BeadColor(val id: String, val name: String, val hex: String) {

    val androidColor: Int get() = AndroidColor.parseColor(hex)
    val composeColor: Color get() = Color(androidColor)

    fun lab(): Triple<Double, Double, Double> {
        val c = androidColor
        val r = AndroidColor.red(c) / 255.0
        val g = AndroidColor.green(c) / 255.0
        val b = AndroidColor.blue(c) / 255.0
        return rgbToLab(r, g, b)
    }

    fun distanceTo(other: BeadColor): Double {
        val (l1, a1, b1) = lab()
        val (l2, a2, b2) = other.lab()
        return sqrt((l1 - l2).pow(2) + (a1 - a2).pow(2) + (b1 - b2).pow(2))
    }

    companion object {
        fun rgbToLab(r: Double, g: Double, b: Double): Triple<Double, Double, Double> {
            fun linearize(c: Double) = if (c > 0.04045) ((c + 0.055) / 1.055).pow(2.4) else c / 12.92
            val rl = linearize(r); val gl = linearize(g); val bl = linearize(b)
            val x = (rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375) / 0.95047
            val y = (rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750) / 1.00000
            val z = (rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041) / 1.08883
            fun f(t: Double) = if (t > 0.008856) t.pow(1.0 / 3.0) else 7.787 * t + 16.0 / 116.0
            return Triple(116.0 * f(y) - 16.0, 500.0 * (f(x) - f(y)), 200.0 * (f(y) - f(z)))
        }

        val palette: List<BeadColor> = listOf(
            BeadColor("white",          "White",          "#FFFFFF"),
            BeadColor("cream",          "Cream",          "#FFFDD0"),
            BeadColor("ivory",          "Ivory",          "#FFFFF0"),
            BeadColor("yellow",         "Yellow",         "#F5D000"),
            BeadColor("banana",         "Banana",         "#FFE135"),
            BeadColor("lemon",          "Lemon",          "#FFF44F"),
            BeadColor("neon_yellow",    "Neon Yellow",    "#FCFC2C"),
            BeadColor("orange",         "Orange",         "#FF8C00"),
            BeadColor("pumpkin",        "Pumpkin",        "#FF6600"),
            BeadColor("neon_orange",    "Neon Orange",    "#FF5500"),
            BeadColor("red",            "Red",            "#CC1122"),
            BeadColor("dark_red",       "Dark Red",       "#8B0000"),
            BeadColor("cheddar",        "Cheddar",        "#FF9900"),
            BeadColor("light_pink",     "Light Pink",     "#FFB6C1"),
            BeadColor("pink",           "Pink",           "#FF69B4"),
            BeadColor("hot_pink",       "Hot Pink",       "#FF1493"),
            BeadColor("magenta",        "Magenta",        "#FF00CC"),
            BeadColor("blush",          "Blush",          "#FF9E9E"),
            BeadColor("light_lavender", "Light Lavender", "#E6E6FA"),
            BeadColor("lavender",       "Lavender",       "#9370DB"),
            BeadColor("purple",         "Purple",         "#800080"),
            BeadColor("dark_purple",    "Dark Purple",    "#4B0082"),
            BeadColor("plum",           "Plum",           "#8B008B"),
            BeadColor("light_blue",     "Light Blue",     "#87CEEB"),
            BeadColor("sky_blue",       "Sky Blue",       "#5BC8F5"),
            BeadColor("periwinkle",     "Periwinkle",     "#CCCCFF"),
            BeadColor("blue",           "Blue",           "#1553B0"),
            BeadColor("dark_blue",      "Dark Blue",      "#00008B"),
            BeadColor("navy",           "Navy",           "#001F5B"),
            BeadColor("toothpaste",     "Toothpaste",     "#B2FFFF"),
            BeadColor("aqua",           "Aqua",           "#00FFFF"),
            BeadColor("light_teal",     "Light Teal",     "#7FFFD4"),
            BeadColor("teal",           "Teal",           "#008080"),
            BeadColor("turquoise",      "Turquoise",      "#40E0D0"),
            BeadColor("light_green",    "Light Green",    "#90EE90"),
            BeadColor("neon_green",     "Neon Green",     "#39FF14"),
            BeadColor("green",          "Green",          "#2E8B57"),
            BeadColor("dark_green",     "Dark Green",     "#006400"),
            BeadColor("army_green",     "Army Green",     "#4B5320"),
            BeadColor("forest",         "Forest",         "#228B22"),
            BeadColor("olive",          "Olive",          "#808000"),
            BeadColor("tan",            "Tan",            "#D2B48C"),
            BeadColor("peach",          "Peach",          "#FFCBA4"),
            BeadColor("skin",           "Skin",           "#F4C2A1"),
            BeadColor("light_brown",    "Light Brown",    "#C8A278"),
            BeadColor("brown",          "Brown",          "#8B5E3C"),
            BeadColor("dark_brown",     "Dark Brown",     "#4B2C20"),
            BeadColor("rust",           "Rust",           "#8B3A2A"),
            BeadColor("caramel",        "Caramel",        "#C68642"),
            BeadColor("black",          "Black",          "#000000"),
            BeadColor("dark_gray",      "Dark Gray",      "#444444"),
            BeadColor("gray",           "Gray",           "#808080"),
            BeadColor("light_gray",     "Light Gray",     "#C8C8C8"),
            BeadColor("silver",         "Silver",         "#AAAAAA"),
            BeadColor("clear",          "Clear",          "#E8F4F8"),
        )

        val paletteById: Map<String, BeadColor> by lazy { palette.associateBy { it.id } }

        // Subset used as a default starting palette
        val defaultPalette: List<BeadColor> get() = palette.take(8)
    }
}
