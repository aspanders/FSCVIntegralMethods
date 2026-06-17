import Foundation

enum SeedPatterns {

    static let all: [FusePattern] = [
        heart, star, smiley, diamond, cupcake,
        cat, dog, fish, bee, butterfly, bird,
        flower, sun, mushroom, tree, rainbow,
        rocket, car,
        pumpkin, christmasTree, snowflake
    ]

    // MARK: - ASCII helper

    private static func cells(
        _ rows: [String],
        _ map: [Character: String]
    ) -> [Cell] {
        var result: [Cell] = []
        for (y, row) in rows.enumerated() {
            for (x, ch) in row.enumerated() {
                if let id = map[ch] {
                    result.append(Cell(x: x, y: y, colorId: id))
                }
            }
        }
        return result
    }

    private static func pal(_ pairs: (String, String, String)...) -> [PaletteColor] {
        pairs.map { PaletteColor(id: $0.0, name: $0.1, hex: $0.2) }
    }

    // MARK: - Icons

    static let heart = FusePattern(
        id: "seed-heart", title: "Heart",
        category: .icons, createdBy: .system,
        grid: GridSize(width: 12, height: 9),
        palette: pal(("red","Red","#CC1122"), ("dark_red","Dark Red","#8B0000"),
                     ("pink","Pink","#FF69B4"), ("white","White","#FFFFFF")),
        cells: cells([
            "............",
            ".RRRR..RRRR.",
            "RRRRRRRRRRRR",
            "RRRRRRRRRRRR",
            ".RRRRRRRRRR.",
            "..RRRRRRRR..",
            "...RRRRRR...",
            "....RRRR....",
            ".....RR.....",
        ], ["R": "red"]),
        difficulty: .easy, tags: ["heart","love","icon"],
        sourcePrompt: nil, version: 1
    )

    static let star = FusePattern(
        id: "seed-star", title: "Star",
        category: .icons, createdBy: .system,
        grid: GridSize(width: 11, height: 10),
        palette: pal(("yellow","Yellow","#F5D000"), ("banana","Banana","#FFE135"),
                     ("orange","Orange","#FF8C00"), ("white","White","#FFFFFF")),
        cells: cells([
            ".....Y.....",
            ".....Y.....",
            "...YYYYY...",
            "YYYYYYYYYYY",
            ".YYYYYYYYY.",
            "..YYYYYYY..",
            "...YYYYY...",
            "....YYY....",
            "....YYY....",
            ".....Y.....",
        ], ["Y": "yellow"]),
        difficulty: .easy, tags: ["star","icon","gold"],
        sourcePrompt: nil, version: 1
    )

    static let smiley = FusePattern(
        id: "seed-smiley", title: "Smiley Face",
        category: .icons, createdBy: .system,
        grid: GridSize(width: 12, height: 12),
        palette: pal(("yellow","Yellow","#F5D000"), ("black","Black","#000000"),
                     ("white","White","#FFFFFF"), ("banana","Banana","#FFE135")),
        cells: cells([
            "....YYYY....",
            "..YYYYYYYY..",
            ".YYYYYYYYYY.",
            "YYYYYYYYYYYY",
            "YYYYKYYYKYYY",
            "YYYYYYYYYYYY",
            "YYYYYYYYYYYY",
            "YK.......KYY",
            "YYK.....KYYY",
            ".YYYYYYYYYY.",
            "..YYYYYYYY..",
            "....YYYY....",
        ], ["Y": "yellow", "K": "black"]),
        difficulty: .easy, tags: ["smiley","face","happy","emoji"],
        sourcePrompt: nil, version: 1
    )

    static let diamond = FusePattern(
        id: "seed-diamond", title: "Diamond",
        category: .icons, createdBy: .system,
        grid: GridSize(width: 12, height: 11),
        palette: pal(("sky_blue","Sky Blue","#5BC8F5"), ("blue","Blue","#1553B0"),
                     ("light_blue","Light Blue","#87CEEB"), ("white","White","#FFFFFF")),
        cells: cells([
            ".....BB.....",
            "....BBBB....",
            "...BBBBBB...",
            "..BBBBBBBB..",
            ".BBBBBBBBBB.",
            "BBBBBBBBBBBB",
            ".BBBBBBBBBB.",
            "..BBBBBBBB..",
            "...BBBBBB...",
            "....BBBB....",
            ".....BB.....",
        ], ["B": "sky_blue"]),
        difficulty: .easy, tags: ["diamond","gem","jewel","icon"],
        sourcePrompt: nil, version: 1
    )

    static let cupcake = FusePattern(
        id: "seed-cupcake", title: "Cupcake",
        category: .icons, createdBy: .system,
        grid: GridSize(width: 12, height: 13),
        palette: pal(("pink","Pink","#FF69B4"), ("brown","Brown","#8B5E3C"),
                     ("light_brown","Light Brown","#C8A278"), ("white","White","#FFFFFF"),
                     ("yellow","Yellow","#F5D000"), ("red","Red","#CC1122")),
        cells: cells([
            "....PPPP....",
            "...PPPPPP...",
            "..PPPPPPPP..",
            "..PPPPPPPP..",
            ".PPPPPPPPPP.",
            ".PPPPPPPPPP.",
            "NNNNNNNNNNNN",
            "NNNNNNNNNNNN",
            ".LLLLLLLLLL.",
            ".LLLLLLLLLL.",
            ".LLLLLLLLLL.",
            "..LLLLLLLL..",
            "...LLLLLL...",
        ], ["P": "pink", "N": "brown", "L": "light_brown"]),
        difficulty: .easy, tags: ["cupcake","cake","food","sweet"],
        sourcePrompt: nil, version: 1
    )

    // MARK: - Animals

    static let cat = FusePattern(
        id: "seed-cat", title: "Cat",
        category: .animals, createdBy: .system,
        grid: GridSize(width: 14, height: 14),
        palette: pal(("gray","Gray","#808080"), ("black","Black","#000000"),
                     ("white","White","#FFFFFF"), ("pink","Pink","#FF69B4"),
                     ("light_gray","Light Gray","#C8C8C8")),
        cells: cells([
            "..AA....AA..",
            ".AAAA..AAAA.",
            ".AAAAAAAAAAA.",
            "AAAAAAAAAAAAAA",
            "AAAAAAAAAAAAAA",
            "AAWAA..AAWAAA",
            "AA.AKAKAK.AAA",
            "AAAKAAAKAKAAA",
            "AAAPPPPPAAAAA",
            ".AAAAAAAAAA..",
            ".AAAAAAAAAA..",
            "..AAAAAAAA...",
            "..AAA..AAA...",
            "..AA....AA...",
        ], ["A": "gray", "K": "black", "W": "white", "P": "pink"]),
        difficulty: .medium, tags: ["cat","animal","pet","kitten"],
        sourcePrompt: nil, version: 1
    )

    static let dog = FusePattern(
        id: "seed-dog", title: "Dog",
        category: .animals, createdBy: .system,
        grid: GridSize(width: 14, height: 13),
        palette: pal(("brown","Brown","#8B5E3C"), ("dark_brown","Dark Brown","#4B2C20"),
                     ("white","White","#FFFFFF"), ("black","Black","#000000"),
                     ("light_brown","Light Brown","#C8A278")),
        cells: cells([
            "N..........N..",
            "NN.........NN.",
            "NNNNNNNNNNNN..",
            "NNNNNNNNNNNNNN",
            "NNNNNNNNNNNNNN",
            "NNWWNNNNWWNNNN",
            "NNWKWNNWKWNNN.",
            "NNNNNNNNNNNN..",
            "NNNNNLLNNNNN..",
            "NNNNLLLNNNNNN.",
            ".NNNNNNNNNNNN.",
            "..NNNNN.NNNNN.",
            "..NNN...NNN...",
        ], ["N": "brown", "W": "white", "K": "black", "L": "light_brown"]),
        difficulty: .medium, tags: ["dog","animal","pet","puppy"],
        sourcePrompt: nil, version: 1
    )

    static let fish = FusePattern(
        id: "seed-fish", title: "Fish",
        category: .animals, createdBy: .system,
        grid: GridSize(width: 14, height: 10),
        palette: pal(("sky_blue","Sky Blue","#5BC8F5"), ("blue","Blue","#1553B0"),
                     ("light_blue","Light Blue","#87CEEB"), ("white","White","#FFFFFF"),
                     ("black","Black","#000000")),
        cells: cells([
            "SS..........",
            "SSSS........",
            ".SSSSSSSSS..",
            "BBBBBBBBBBBSS",
            "BBBBBBBBBBBBB",
            "BBBBBBBBBBBBB",
            "BBBBBBBBBBBSS",
            ".SSSSSSSSS..",
            "SSSS........",
            "SS..........",
        ], ["S": "sky_blue", "B": "blue"]),
        difficulty: .easy, tags: ["fish","animal","sea","ocean"],
        sourcePrompt: nil, version: 1
    )

    static let bee = FusePattern(
        id: "seed-bee", title: "Bee",
        category: .animals, createdBy: .system,
        grid: GridSize(width: 12, height: 13),
        palette: pal(("yellow","Yellow","#F5D000"), ("black","Black","#000000"),
                     ("white","White","#FFFFFF"), ("light_blue","Light Blue","#87CEEB")),
        cells: cells([
            "....YYYY....",
            "...YYYYYY...",
            "SSSSYYYYSSSS",
            "SSSSYYYYSSSS",
            "...KKKKKK...",
            "..YYYYYYYYYY",
            "..KKKKKKKK..",
            "..YYYYYYYYYY",
            "..KKKKKKKK..",
            "...YYYYYY...",
            "....YYYY....",
            ".....YY.....",
            ".....YY.....",
        ], ["Y": "yellow", "K": "black", "S": "light_blue"]),
        difficulty: .medium, tags: ["bee","insect","animal","honey"],
        sourcePrompt: nil, version: 1
    )

    static let butterfly = FusePattern(
        id: "seed-butterfly", title: "Butterfly",
        category: .animals, createdBy: .system,
        grid: GridSize(width: 16, height: 12),
        palette: pal(("orange","Orange","#FF8C00"), ("black","Black","#000000"),
                     ("yellow","Yellow","#F5D000"), ("white","White","#FFFFFF")),
        cells: cells([
            "OOOO....OOOOOOOO",
            "OOOOO..OOOOOOOO.",
            "OOOOOO.OOOOOOO..",
            "OOOOOOKOOOOOO...",
            "OOOOOOKOOOOOO...",
            ".OOOOOKOOOOO....",
            ".OOOOOOOOOOOO...",
            "..OOOOKOOOOO....",
            "..OOOOKOOOO.....",
            "...OOOO.OOOO....",
            "....OO...OOO....",
            ".....O....OO....",
        ], ["O": "orange", "K": "black"]),
        difficulty: .medium, tags: ["butterfly","insect","animal","wings"],
        sourcePrompt: nil, version: 1
    )

    static let bird = FusePattern(
        id: "seed-bird", title: "Bird",
        category: .animals, createdBy: .system,
        grid: GridSize(width: 12, height: 10),
        palette: pal(("sky_blue","Sky Blue","#5BC8F5"), ("yellow","Yellow","#F5D000"),
                     ("white","White","#FFFFFF"), ("black","Black","#000000"),
                     ("orange","Orange","#FF8C00")),
        cells: cells([
            "....SSS.....",
            "...SSSSS....",
            "..SSSSSSS...",
            ".SSSSSSSSSS.",
            "SSSSSSSSSSSS",
            "SSSSSSSSSOSS",
            ".SSSSSSSSOSS",
            "..SSSSSSSSS.",
            "....SSSS....",
            ".....SS.....",
        ], ["S": "sky_blue", "O": "orange"]),
        difficulty: .easy, tags: ["bird","animal","fly","wings"],
        sourcePrompt: nil, version: 1
    )

    // MARK: - Nature

    static let flower = FusePattern(
        id: "seed-flower", title: "Flower",
        category: .nature, createdBy: .system,
        grid: GridSize(width: 13, height: 14),
        palette: pal(("pink","Pink","#FF69B4"), ("yellow","Yellow","#F5D000"),
                     ("green","Green","#2E8B57"), ("light_green","Light Green","#90EE90"),
                     ("white","White","#FFFFFF")),
        cells: cells([
            "....PPP......",
            "...PPPPP.....",
            "...PPPPP.....",
            ".PPPYYYPPP...",
            ".PPYYYYYPP...",
            ".PPPYYYPPP...",
            "...PPPPP.....",
            "...PPPPP.....",
            "....PPP......",
            ".....G.......",
            "....GGG......",
            "....G.G......",
            "....G........",
            "....G........",
        ], ["P": "pink", "Y": "yellow", "G": "green"]),
        difficulty: .easy, tags: ["flower","nature","plant","bloom"],
        sourcePrompt: nil, version: 1
    )

    static let sun = FusePattern(
        id: "seed-sun", title: "Sun",
        category: .nature, createdBy: .system,
        grid: GridSize(width: 13, height: 13),
        palette: pal(("yellow","Yellow","#F5D000"), ("orange","Orange","#FF8C00"),
                     ("banana","Banana","#FFE135"), ("white","White","#FFFFFF")),
        cells: cells([
            "..Y.....Y....",
            "...YY.YY.....",
            ".YYYYYYYYYYY.",
            "YYYYYYYYYYYYY",
            "YYYYYYYYYYYYY",
            "Y.YYYYYYYYY.Y",
            "YYYYYYYYYYYYY",
            "YYYYYYYYYYYYY",
            ".YYYYYYYYYYY.",
            "...YY.YY.....",
            "..Y.....Y....",
            ".............",
            ".............",
        ], ["Y": "yellow"]),
        difficulty: .easy, tags: ["sun","nature","sky","weather"],
        sourcePrompt: nil, version: 1
    )

    static let mushroom = FusePattern(
        id: "seed-mushroom", title: "Mushroom",
        category: .nature, createdBy: .system,
        grid: GridSize(width: 12, height: 12),
        palette: pal(("red","Red","#CC1122"), ("white","White","#FFFFFF"),
                     ("dark_red","Dark Red","#8B0000"), ("light_gray","Light Gray","#C8C8C8"),
                     ("cream","Cream","#FFFDD0")),
        cells: cells([
            "....RRRR....",
            "..RRRRRRRR..",
            ".RRRWRRWRRR.",
            "RRRRRRRRRRRR",
            "RRRWRRRRRWRR",
            "RRRRRRRRRRRR",
            ".RRRRRRRRRR.",
            "..WWWWWWWW..",
            "..WWWWWWWW..",
            "...WWWWWW...",
            "....WWWW....",
            ".....WW.....",
        ], ["R": "red", "W": "white"]),
        difficulty: .easy, tags: ["mushroom","nature","forest","fungi"],
        sourcePrompt: nil, version: 1
    )

    static let tree = FusePattern(
        id: "seed-tree", title: "Pine Tree",
        category: .nature, createdBy: .system,
        grid: GridSize(width: 13, height: 15),
        palette: pal(("green","Green","#2E8B57"), ("dark_green","Dark Green","#006400"),
                     ("brown","Brown","#8B5E3C"), ("light_green","Light Green","#90EE90"),
                     ("white","White","#FFFFFF")),
        cells: cells([
            "......G......",
            ".....GGG.....",
            "....GGGGG....",
            "...GGGGGGG...",
            "..GGGGGGGGG..",
            "....GGGGG....",
            "...GGGGGGG...",
            "..GGGGGGGGG..",
            ".GGGGGGGGGGG.",
            "...GGGGGGG...",
            "..GGGGGGGGG..",
            ".GGGGGGGGGGG.",
            "GGGGGGGGGGGGG",
            ".....NNN.....",
            ".....NNN.....",
        ], ["G": "green", "N": "brown"]),
        difficulty: .medium, tags: ["tree","pine","nature","forest","christmas"],
        sourcePrompt: nil, version: 1
    )

    static let rainbow = FusePattern(
        id: "seed-rainbow", title: "Rainbow",
        category: .nature, createdBy: .system,
        grid: GridSize(width: 16, height: 6),
        palette: pal(("red","Red","#CC1122"), ("orange","Orange","#FF8C00"),
                     ("yellow","Yellow","#F5D000"), ("green","Green","#2E8B57"),
                     ("blue","Blue","#1553B0"), ("purple","Purple","#800080"),
                     ("white","White","#FFFFFF"), ("sky_blue","Sky Blue","#5BC8F5")),
        cells: cells([
            "RRRRRRRRRRRRRRRR",
            "OOOOOOOOOOOOOOOO",
            "YYYYYYYYYYYYYYYY",
            "GGGGGGGGGGGGGGGG",
            "BBBBBBBBBBBBBBBB",
            "VVVVVVVVVVVVVVVV",
        ], ["R": "red", "O": "orange", "Y": "yellow", "G": "green", "B": "blue", "V": "purple"]),
        difficulty: .medium, tags: ["rainbow","nature","colorful","weather"],
        sourcePrompt: nil, version: 1
    )

    // MARK: - Vehicles

    static let rocket = FusePattern(
        id: "seed-rocket", title: "Rocket",
        category: .vehicles, createdBy: .system,
        grid: GridSize(width: 10, height: 16),
        palette: pal(("red","Red","#CC1122"), ("white","White","#FFFFFF"),
                     ("gray","Gray","#808080"), ("yellow","Yellow","#F5D000"),
                     ("sky_blue","Sky Blue","#5BC8F5"), ("orange","Orange","#FF8C00")),
        cells: cells([
            "....RR....",
            "...RRRR...",
            "..RRRRRR..",
            "..RWWWWR..",
            ".RWWWWWWR.",
            ".RWWSWWR..",
            ".RWSSSWR..",
            ".RWWSWWR..",
            ".RWWWWWWR.",
            "RRRWWWRRR.",
            "RRRRRRRRR.",
            "RRRRRRRRR.",
            ".RRRRRRRR.",
            "..OYYYOY..",
            "..OYYYOY..",
            "...OOOOO..",
        ], ["R": "red", "W": "white", "S": "sky_blue", "O": "orange", "Y": "yellow"]),
        difficulty: .medium, tags: ["rocket","space","vehicle","launch"],
        sourcePrompt: nil, version: 1
    )

    static let car = FusePattern(
        id: "seed-car", title: "Car",
        category: .vehicles, createdBy: .system,
        grid: GridSize(width: 16, height: 9),
        palette: pal(("red","Red","#CC1122"), ("black","Black","#000000"),
                     ("sky_blue","Sky Blue","#5BC8F5"), ("gray","Gray","#808080"),
                     ("white","White","#FFFFFF"), ("yellow","Yellow","#F5D000")),
        cells: cells([
            "....RRRRRRR.....",
            "...RRRRRRRRR....",
            "..RRSSSSSSSRR...",
            ".RRRSSSSSSRRRR..",
            "RRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRR.",
            ".KKK.RRRRRR.KKK.",
            "..K...RRRR...K..",
        ], ["R": "red", "K": "black", "S": "sky_blue"]),
        difficulty: .medium, tags: ["car","vehicle","drive","road"],
        sourcePrompt: nil, version: 1
    )

    // MARK: - Holidays

    static let pumpkin = FusePattern(
        id: "seed-pumpkin", title: "Pumpkin",
        category: .holidays, createdBy: .system,
        grid: GridSize(width: 14, height: 14),
        palette: pal(("orange","Orange","#FF8C00"), ("dark_green","Dark Green","#006400"),
                     ("black","Black","#000000"), ("pumpkin","Pumpkin","#FF6600"),
                     ("green","Green","#2E8B57")),
        cells: cells([
            ".....GG.......",
            ".....G........",
            "...OOOOOOO....",
            ".OOOOOOOOOOOO.",
            "OOOOOOOOOOOOOO",
            "OOKOOOOOOOOKOO",
            "OOOKOOOOKOOO..",
            "OOOOKOOKOOOO..",
            "OOOKOOOOKOOO..",
            "OOKOOOOOOOOKOO",
            "OOOOOOOOOOOOOO",
            ".OOOOOOOOOOOO.",
            "...OOOOOOO....",
            ".....OOO......",
        ], ["O": "orange", "G": "dark_green", "K": "black"]),
        difficulty: .medium, tags: ["pumpkin","halloween","holiday","fall"],
        sourcePrompt: nil, version: 1
    )

    static let christmasTree = FusePattern(
        id: "seed-xmas-tree", title: "Christmas Tree",
        category: .holidays, createdBy: .system,
        grid: GridSize(width: 13, height: 16),
        palette: pal(("green","Green","#2E8B57"), ("dark_green","Dark Green","#006400"),
                     ("red","Red","#CC1122"), ("yellow","Yellow","#F5D000"),
                     ("brown","Brown","#8B5E3C"), ("white","White","#FFFFFF")),
        cells: cells([
            "......Y......",
            ".....GGG.....",
            "....GRGGG....",
            "...GGGGGGG...",
            "..GGRGGGRGGG.",
            "....GGGGG....",
            "...GGGGGGG...",
            "..GGGRGGGGG..",
            ".GGGGGGGGGG..",
            "...GGGGGGG...",
            "..GGGGRGGGGG.",
            ".GGGGGGGGGGG.",
            "GGGGGGGGGGGGG",
            "....NNNNN....",
            "....NNNNN....",
            "...NNNNNNN...",
        ], ["G": "green", "Y": "yellow", "R": "red", "N": "brown"]),
        difficulty: .medium, tags: ["christmas","tree","holiday","winter"],
        sourcePrompt: nil, version: 1
    )

    static let snowflake = FusePattern(
        id: "seed-snowflake", title: "Snowflake",
        category: .holidays, createdBy: .system,
        grid: GridSize(width: 13, height: 13),
        palette: pal(("light_blue","Light Blue","#87CEEB"), ("white","White","#FFFFFF"),
                     ("toothpaste","Toothpaste","#B2FFFF"), ("sky_blue","Sky Blue","#5BC8F5")),
        cells: cells([
            "......B......",
            "......B......",
            "..B...B...B..",
            "...B.BBB.B...",
            "....BBBBB....",
            "BBBBBBBBBBBBB",
            "....BBBBB....",
            "...B.BBB.B...",
            "..B...B...B..",
            "......B......",
            "......B......",
            "......B......",
            ".............",
        ], ["B": "light_blue"]),
        difficulty: .easy, tags: ["snowflake","winter","holiday","snow","ice"],
        sourcePrompt: nil, version: 1
    )
}
