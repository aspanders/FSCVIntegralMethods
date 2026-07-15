import Foundation

enum SeedPatterns {

    static let all: [FusePattern] = [
        heart, star, smiley, diamond, cupcake, cat, dog, fish, bee, butterfly, bird, flower, sun, mushroom, tree, rainbow, rocket, car, pumpkin, christmasTree, snowflake, dragon, unicorn, crystalBall, wizardHat
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
        grid: GridSize(width: 12, height: 10),
        palette: pal(("red","Red","#CC1122"), ("dark_red","Dark Red","#8B0000")),
        cells: cells([
            "....RR..RR..",
            "...RRRR.RRR.",
            "..RRRRRRRRR.",
            "..RRRRRRRRR.",
            "...RRRRRRRR.",
            "....RRRRRR..",
            ".....RRRR...",
            "......RR....",
            "............",
            "............",
        ], ["R": "red", "r": "dark_red"]),
        difficulty: .easy, tags: ["heart","love","valentine"],
        sourcePrompt: nil, version: 1
    )

    static let star = FusePattern(
        id: "seed-star", title: "Star",
        category: .icons, createdBy: .system,
        grid: GridSize(width: 12, height: 12),
        palette: pal(("yellow","Yellow","#F5D000"), ("cheddar","Cheddar","#FF9900")),
        cells: cells([
            ".....YY.....",
            ".....YY.....",
            "....YYYY....",
            "YYYYYYYYYYYY",
            ".YYYYYYYYYY.",
            "..YYYYYYYY..",
            "...YYYYYYY..",
            "...YYYYYYYY.",
            "..YY.....YY.",
            "..YY.....YY.",
            ".YYY.....YYY",
            "............",
        ], ["Y": "yellow"]),
        difficulty: .easy, tags: ["star","classic"],
        sourcePrompt: nil, version: 1
    )

    static let smiley = FusePattern(
        id: "seed-smiley", title: "Smiley Face",
        category: .icons, createdBy: .system,
        grid: GridSize(width: 12, height: 12),
        palette: pal(("yellow","Yellow","#F5D000"), ("black","Black","#000000")),
        cells: cells([
            "....YYYY....",
            "...YYYYYY...",
            "..YYYYYYYY..",
            "..YBYYBBYY..",
            "..YYYYYYYY..",
            "..YYYYYYYY..",
            "..YBYYYYBY..",
            "..YYBBBBYY..",
            "..YYYYYYYY..",
            "...YYYYYY...",
            "....YYYY....",
            "............",
        ], ["Y": "yellow", "B": "black"]),
        difficulty: .easy, tags: ["smiley","face","happy"],
        sourcePrompt: nil, version: 1
    )

    static let diamond = FusePattern(
        id: "seed-diamond", title: "Diamond",
        category: .icons, createdBy: .system,
        grid: GridSize(width: 12, height: 10),
        palette: pal(("sky_blue","Sky Blue","#5BC8F5"), ("blue","Blue","#1553B0")),
        cells: cells([
            ".....BB.....",
            "....BBBB....",
            "...BBSSBB...",
            "..BBSSSSBB..",
            ".BBSSSSSSBB.",
            "BBSSSSSSSSBB",
            ".BBSSSSSSBB.",
            "..BBSSSSBB..",
            "...BBSSBB...",
            "....BBBB....",
        ], ["B": "blue", "S": "sky_blue"]),
        difficulty: .easy, tags: ["diamond","gem"],
        sourcePrompt: nil, version: 1
    )

    static let cupcake = FusePattern(
        id: "seed-cupcake", title: "Cupcake",
        category: .icons, createdBy: .system,
        grid: GridSize(width: 12, height: 12),
        palette: pal(("pink","Pink","#FF69B4"), ("light_brown","Light Brown","#C8A278"),
                     ("brown","Brown","#8B5E3C"), ("red","Red","#CC1122")),
        cells: cells([
            "....PPPP....",
            "...PPPPPP...",
            "..PPPPPPPP..",
            "..PPRPPRPP..",
            "..PPPPPPPP..",
            "..LLLLLLLL..",
            "..LBBBBBBL..",
            "..LBBBBBBL..",
            "..LBBBBBBL..",
            "...LBBBBBL..",
            "...LLLLLL...",
            "............",
        ], ["P": "pink", "R": "red", "L": "light_brown", "B": "brown"]),
        difficulty: .medium, tags: ["cupcake","food","sweet"],
        sourcePrompt: nil, version: 1
    )

    // MARK: - Animals

    static let cat = FusePattern(
        id: "seed-cat", title: "Cat",
        category: .animals, createdBy: .system,
        grid: GridSize(width: 14, height: 12),
        palette: pal(("light_gray","Light Gray","#C8C8C8"), ("black","Black","#000000"),
                     ("pink","Pink","#FF69B4")),
        cells: cells([
            "GG..........GG",
            "GGG........GGG",
            "GGGG......GGGG",
            "GGGGGGGGGGGGG.",
            "GGBGGGGGGBGGG.",
            "GGGGGPGGGGGGG.",
            "GGGGGGGGGGGGG.",
            "GGGBBBBBGGGGG.",
            "GGGGGGGGGGGGG.",
            "..GGG...GGGGG.",
            "..GGG...GGGGG.",
            "..............",
        ], ["G": "light_gray", "B": "black", "P": "pink"]),
        difficulty: .medium, tags: ["cat","animal","pet"],
        sourcePrompt: nil, version: 1
    )

    static let dog = FusePattern(
        id: "seed-dog", title: "Dog",
        category: .animals, createdBy: .system,
        grid: GridSize(width: 14, height: 12),
        palette: pal(("tan","Tan","#D2B48C"), ("black","Black","#000000"),
                     ("pink","Pink","#FF69B4"), ("brown","Brown","#8B5E3C")),
        cells: cells([
            "TT..........TT",
            "TTT..TTTTT..TT",
            "TTTTTTTTTTTTT.",
            "TTBTTTTTTTBTTT",
            "TTTTTPTTTTTTT.",
            "TTTTTTTTTTTTT.",
            "TTTBBBBBBTTTT.",
            "TTTTTTTTTTTTT.",
            "..TTT...TTT...",
            "..TTT...TTT...",
            "..TTT...TTT...",
            "..............",
        ], ["T": "tan", "B": "black", "P": "pink"]),
        difficulty: .medium, tags: ["dog","animal","puppy"],
        sourcePrompt: nil, version: 1
    )

    static let fish = FusePattern(
        id: "seed-fish", title: "Fish",
        category: .animals, createdBy: .system,
        grid: GridSize(width: 14, height: 10),
        palette: pal(("orange","Orange","#FF8C00"), ("yellow","Yellow","#F5D000"),
                     ("black","Black","#000000")),
        cells: cells([
            "..............",
            "..OOOOOOOOO...",
            "OOOOOOOOOOOOO.",
            "OOOOOOBOOOOOOO",
            "OOOOOOOOOOOOO.",
            "..OOOOOOOOO...",
            "..............",
            "..............",
            "..............",
            "..............",
        ], ["O": "orange", "B": "black"]),
        difficulty: .easy, tags: ["fish","sea","ocean"],
        sourcePrompt: nil, version: 1
    )

    static let bee = FusePattern(
        id: "seed-bee", title: "Bee",
        category: .animals, createdBy: .system,
        grid: GridSize(width: 12, height: 12),
        palette: pal(("yellow","Yellow","#F5D000"), ("black","Black","#000000"),
                     ("white","White","#FFFFFF")),
        cells: cells([
            "....YYYY....",
            "...YYYYYY...",
            "..YBYYYBYY..",
            "..YYYYYYYY..",
            "WWYYYYYYYWW.",
            "WWBBBBBBWWW.",
            "WWYYYYYYYWW.",
            "WWBBBBBBWWW.",
            "..YYYYYYYY..",
            "...YYYYYY...",
            "....YYYY....",
            "............",
        ], ["Y": "yellow", "B": "black", "W": "white"]),
        difficulty: .medium, tags: ["bee","insect","nature"],
        sourcePrompt: nil, version: 1
    )

    static let butterfly = FusePattern(
        id: "seed-butterfly", title: "Butterfly",
        category: .animals, createdBy: .system,
        grid: GridSize(width: 14, height: 10),
        palette: pal(("magenta","Magenta","#FF00CC"), ("purple","Purple","#800080"),
                     ("yellow","Yellow","#F5D000"), ("black","Black","#000000")),
        cells: cells([
            "MM....BB....MM",
            "MMMM.BBBB.MMMM",
            "MMMMMBBBBMMMMM",
            "MMMMYBBBBYMMMM",
            "MMMMBBBBBMMMMM",
            ".MMMBBBBMMMMM.",
            "..MMBBBBBMMM..",
            "...MBBBBBMM...",
            "....BBBBB.....",
            "..............",
        ], ["M": "magenta", "B": "black", "Y": "yellow"]),
        difficulty: .medium, tags: ["butterfly","insect","wings"],
        sourcePrompt: nil, version: 1
    )

    static let bird = FusePattern(
        id: "seed-bird", title: "Bird",
        category: .animals, createdBy: .system,
        grid: GridSize(width: 12, height: 10),
        palette: pal(("sky_blue","Sky Blue","#5BC8F5"), ("orange","Orange","#FF8C00")),
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
        grid: GridSize(width: 12, height: 12),
        palette: pal(("pink","Pink","#FF69B4"), ("yellow","Yellow","#F5D000"),
                     ("green","Green","#2E8B57")),
        cells: cells([
            "....PP.PP...",
            "...PPPPPPP..",
            "..PPPYYPPP..",
            "..PPYYYYPP..",
            "..PPPYYPPP..",
            "...PPPPPPP..",
            "....GGGGG...",
            ".....GGG....",
            ".....GGG....",
            ".....GGG....",
            "....GGGGG...",
            "............",
        ], ["P": "pink", "Y": "yellow", "G": "green"]),
        difficulty: .easy, tags: ["flower","nature","bloom"],
        sourcePrompt: nil, version: 1
    )

    static let sun = FusePattern(
        id: "seed-sun", title: "Sun",
        category: .nature, createdBy: .system,
        grid: GridSize(width: 12, height: 12),
        palette: pal(("yellow","Yellow","#F5D000"), ("cheddar","Cheddar","#FF9900")),
        cells: cells([
            "..Y....Y....",
            "...YYYYYY...",
            "....YYYY....",
            "YYYYYYYYYYYY",
            ".YYYYYYYYYY.",
            ".YYYYYYYYYY.",
            "YYYYYYYYYYYY",
            "....YYYY....",
            "...YYYYYY...",
            "..Y....Y....",
            "............",
            "............",
        ], ["Y": "yellow"]),
        difficulty: .easy, tags: ["sun","weather","bright"],
        sourcePrompt: nil, version: 1
    )

    static let mushroom = FusePattern(
        id: "seed-mushroom", title: "Mushroom",
        category: .nature, createdBy: .system,
        grid: GridSize(width: 12, height: 12),
        palette: pal(("red","Red","#CC1122"), ("white","White","#FFFFFF"),
                     ("light_brown","Light Brown","#C8A278")),
        cells: cells([
            "....RRRR....",
            "...RRRRRR...",
            "..RRRRRRRR..",
            ".RRWRRRRWRR.",
            "RRRRRRRRRRR.",
            "RRWRRRRRRWR.",
            "RRRRRRRRRRRR",
            ".LLLLLLLLLL.",
            "..LLLLLLLL..",
            "..LLLLLLLL..",
            "...LLLLLL...",
            "............",
        ], ["R": "red", "W": "white", "L": "light_brown"]),
        difficulty: .easy, tags: ["mushroom","mario","nature"],
        sourcePrompt: nil, version: 1
    )

    static let tree = FusePattern(
        id: "seed-tree", title: "Pine Tree",
        category: .nature, createdBy: .system,
        grid: GridSize(width: 12, height: 14),
        palette: pal(("green","Green","#2E8B57"), ("dark_green","Dark Green","#006400"),
                     ("brown","Brown","#8B5E3C")),
        cells: cells([
            ".....GG.....",
            "....GGGG....",
            "...GGGGGG...",
            "..GGGGGGGG..",
            ".GGGGGGGGGG.",
            "GGGGGGGGGGGG",
            "...GGGGGG...",
            "..GGGGGGGG..",
            ".GGGGGGGGGG.",
            "GGGGGGGGGGGG",
            "....BBBB....",
            "....BBBB....",
            "....BBBB....",
            "............",
        ], ["G": "dark_green", "B": "brown"]),
        difficulty: .easy, tags: ["tree","pine","nature","christmas"],
        sourcePrompt: nil, version: 1
    )

    static let rainbow = FusePattern(
        id: "seed-rainbow", title: "Rainbow",
        category: .nature, createdBy: .system,
        grid: GridSize(width: 16, height: 10),
        palette: pal(("red","Red","#CC1122"), ("orange","Orange","#FF8C00"),
                     ("yellow","Yellow","#F5D000"), ("green","Green","#2E8B57"),
                     ("blue","Blue","#1553B0"), ("purple","Purple","#800080")),
        cells: cells([
            ".......RR.......",
            "......ROORR.....",
            ".....ROYYOOR....",
            "....ROYYGOOR....",
            "...ROYYGGBOOR...",
            "..ROYYGGBBPOOR..",
            ".ROYYGGBBPPOOR..",
            "ROYYGGBBPPOOORR.",
            "................",
            "................",
        ], ["R": "red", "O": "orange", "Y": "yellow", "G": "green", "B": "blue", "P": "purple"]),
        difficulty: .easy, tags: ["rainbow","colorful","nature"],
        sourcePrompt: nil, version: 1
    )

    // MARK: - Vehicles

    static let rocket = FusePattern(
        id: "seed-rocket", title: "Rocket",
        category: .vehicles, createdBy: .system,
        grid: GridSize(width: 10, height: 16),
        palette: pal(("light_gray","Light Gray","#C8C8C8"), ("red","Red","#CC1122"),
                     ("blue","Blue","#1553B0"), ("orange","Orange","#FF8C00")),
        cells: cells([
            "....GG....",
            "...GGGG...",
            "..GGGGGG..",
            "..GRRRGG..",
            "..GBBBBG..",
            "..GBBBBG..",
            "..GRRRGG..",
            ".GGGGGGGG.",
            "GGGGGGGGGG",
            ".GGGGGGGG.",
            "..GGGGGG..",
            "..GGGGGG..",
            ".OGG..GGO.",
            "OOG....GOO",
            "..........",
            "..........",
        ], ["G": "light_gray", "R": "red", "B": "blue", "O": "orange"]),
        difficulty: .medium, tags: ["rocket","space","vehicle"],
        sourcePrompt: nil, version: 1
    )

    static let car = FusePattern(
        id: "seed-car", title: "Car",
        category: .vehicles, createdBy: .system,
        grid: GridSize(width: 16, height: 8),
        palette: pal(("red","Red","#CC1122"), ("sky_blue","Sky Blue","#5BC8F5"),
                     ("black","Black","#000000"), ("light_gray","Light Gray","#C8C8C8")),
        cells: cells([
            "....RRRRRRR.....",
            "...RRRSSSSRRR...",
            "..RRSSSSSSSSRR..",
            "RRRRRRRRRRRRRRR.",
            "RRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRR.",
            "..RR.BBBB..RR...",
            "...GBBBBBBG.....",
        ], ["R": "red", "S": "sky_blue", "B": "black", "G": "light_gray"]),
        difficulty: .easy, tags: ["car","vehicle","transport"],
        sourcePrompt: nil, version: 1
    )

    // MARK: - Holidays

    static let pumpkin = FusePattern(
        id: "seed-pumpkin", title: "Pumpkin",
        category: .holidays, createdBy: .system,
        grid: GridSize(width: 12, height: 12),
        palette: pal(("pumpkin","Pumpkin","#FF6600"), ("orange","Orange","#FF8C00"),
                     ("green","Green","#2E8B57"), ("black","Black","#000000")),
        cells: cells([
            "....GGGG....",
            "....GGGG....",
            "..PPPPPPPP..",
            ".PPPPPPPPPP.",
            "PPPPBBPPBBPP",
            "PPPPPPPPPPPP",
            "PPBPPPPPPBPP",
            "PPPBBBBBBPPP",
            ".PPPPPPPPPP.",
            "..PPPPPPPP..",
            "............",
            "............",
        ], ["P": "pumpkin", "G": "green", "B": "black"]),
        difficulty: .medium, tags: ["pumpkin","halloween","fall"],
        sourcePrompt: nil, version: 1
    )

    static let christmasTree = FusePattern(
        id: "seed-xmas-tree", title: "Christmas Tree",
        category: .holidays, createdBy: .system,
        grid: GridSize(width: 14, height: 14),
        palette: pal(("green","Green","#2E8B57"), ("yellow","Yellow","#F5D000"),
                     ("red","Red","#CC1122"), ("brown","Brown","#8B5E3C")),
        cells: cells([
            "......YY......",
            ".....GGGG.....",
            "....GGGGGG....",
            "...GRGGRGGG...",
            "..GGGGGGGGGG..",
            ".GGRGGGGGRGG..",
            "GGGGGGGGGGGGGG",
            "...GGGGGGGG...",
            "..GGRGGGRGG...",
            ".GGGGGGGGGGGG.",
            "GGGGGGGGGGGGGG",
            "....BBBBB.....",
            "....BBBBB.....",
            "..............",
        ], ["G": "green", "Y": "yellow", "R": "red", "B": "brown"]),
        difficulty: .medium, tags: ["christmas","holiday","tree"],
        sourcePrompt: nil, version: 1
    )

    static let snowflake = FusePattern(
        id: "seed-snowflake", title: "Snowflake",
        category: .holidays, createdBy: .system,
        grid: GridSize(width: 13, height: 13),
        palette: pal(("sky_blue","Sky Blue","#5BC8F5"), ("white","White","#FFFFFF")),
        cells: cells([
            "......B......",
            "......B......",
            ".B....B....B.",
            "..BB..B..BB..",
            "....BBBBB....",
            "BBBBBWBBBBBBB",
            "....BBBBB....",
            "..BB..B..BB..",
            ".B....B....B.",
            "......B......",
            "......B......",
            ".............",
            ".............",
        ], ["B": "sky_blue", "W": "white"]),
        difficulty: .hard, tags: ["snowflake","winter","holiday"],
        sourcePrompt: nil, version: 1
    )

    // MARK: - Fantasy

    static let dragon = FusePattern(
        id: "seed-dragon", title: "Dragon",
        category: .fantasy, createdBy: .system,
        grid: GridSize(width: 12, height: 14),
        palette: pal(("green","Green","#2E8B57"), ("red","Red","#CC1122"),
                     ("white","White","#FFFFFF"), ("black","Black","#000000")),
        cells: cells([
            "GG.RRRR.GGGG",
            "GGGRRRRRGGG.",
            "GGGGGGGGGGGG",
            "GGWGGGGGWGGG",
            "GGGGGGGGGGGG",
            "RGGGGGGGGGGR",
            "RRGGGGGGGGR.",
            "GGGGGGGGGGG.",
            "GGGGGGGGGG..",
            ".GGGGGGGGG..",
            "..GGG.GGGGG.",
            "..GGG.GGGGG.",
            "..GG...GGGG.",
            "............",
        ], ["G": "green", "R": "red", "W": "white", "K": "black"]),
        difficulty: .hard, tags: ["dragon","fantasy","mythical"],
        sourcePrompt: nil, version: 1
    )

    static let unicorn = FusePattern(
        id: "seed-unicorn", title: "Unicorn",
        category: .fantasy, createdBy: .system,
        grid: GridSize(width: 12, height: 14),
        palette: pal(("white","White","#FFFFFF"), ("yellow","Yellow","#F5D000"),
                     ("black","Black","#000000"), ("pink","Pink","#FF69B4")),
        cells: cells([
            "...YYYYYYY..",
            "...WYWWWWW..",
            "..WWWWWWWWW.",
            ".WWBWWWBWWW.",
            ".WWWWWWWWWW.",
            ".WWWWPWWWWW.",
            "WWWWWWWWWWW.",
            ".WWWWWWWWW..",
            "..WWWWWWWW..",
            "..WW....WW..",
            "..WW....WW..",
            "..WW....WW..",
            "..WW....WW..",
            "............",
        ], ["W": "white", "Y": "yellow", "B": "black", "P": "pink"]),
        difficulty: .hard, tags: ["unicorn","fantasy","magical"],
        sourcePrompt: nil, version: 1
    )

    static let crystalBall = FusePattern(
        id: "seed-crystal-ball", title: "Crystal Ball",
        category: .fantasy, createdBy: .system,
        grid: GridSize(width: 12, height: 12),
        palette: pal(("sky_blue","Sky Blue","#5BC8F5"), ("white","White","#FFFFFF"),
                     ("gray","Gray","#808080")),
        cells: cells([
            "....BBBB....",
            "...BBWBBB...",
            "..BBWWWBBB..",
            "..BWWWWBBB..",
            "..BBBBBBBB..",
            "..BBBBBBBB..",
            "..BBBBBBBB..",
            "...BBBBBB...",
            "....BBBB....",
            "....GGGG....",
            "...GGGGGG...",
            "............",
        ], ["B": "sky_blue", "W": "white", "G": "gray"]),
        difficulty: .medium, tags: ["crystal","magic","fantasy"],
        sourcePrompt: nil, version: 1
    )

    static let wizardHat = FusePattern(
        id: "seed-wizard-hat", title: "Wizard Hat",
        category: .fantasy, createdBy: .system,
        grid: GridSize(width: 10, height: 12),
        palette: pal(("dark_purple","Dark Purple","#4B0082"), ("yellow","Yellow","#F5D000"),
                     ("white","White","#FFFFFF")),
        cells: cells([
            "....P.....",
            "...PPP....",
            "..PPPPP...",
            ".PPPPPPP..",
            ".PPYPPPYP.",
            "PPPPPPPPP.",
            "PPPPPPPPPP",
            "PPPPPPPPPP",
            ".PPWWWWPP.",
            ".PPWWWWPP.",
            "PPPPPPPPPP",
            "PPPPPPPPPP",
        ], ["P": "dark_purple", "Y": "yellow", "W": "white"]),
        difficulty: .easy, tags: ["wizard","hat","magic","fantasy"],
        sourcePrompt: nil, version: 1
    )

}
