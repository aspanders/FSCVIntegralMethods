package com.beadsnap.app.data.model

object SeedPatterns {

    val all: List<FusePattern> by lazy {
        listOf(heart, star, smiley, diamond, cupcake, cat, dog, fish, bee,
               butterfly, bird, flower, sun, mushroom, tree, rainbow, rocket, car,
               pumpkin, christmasTree, snowflake, dragon, unicorn, crystalBall, wizardHat)
    }

    // ─── Helpers ───────────────────────────────────────────────────────────────

    private fun cells(rows: List<String>, map: Map<Char, String>): List<Cell> =
        rows.flatMapIndexed { y, row ->
            row.mapIndexedNotNull { x, ch ->
                map[ch]?.let { Cell(x, y, it) }
            }
        }

    private fun pal(vararg pairs: Triple<String, String, String>): List<BeadColor> =
        pairs.map { (id, name, hex) -> BeadColor(id, name, hex) }

    // ─── Icons ──────────────────────────────────────────────────────────────────

    private val heart = FusePattern(
        id = "seed-heart", title = "Heart",
        category = PatternCategory.icons, createdBy = CreatorType.system,
        grid = GridSize(12, 10), difficulty = Difficulty.easy,
        palette = pal(Triple("red","Red","#CC1122"), Triple("dark_red","Dark Red","#8B0000")),
        tags = listOf("heart","love","valentine"),
        cells = cells(
            listOf(
                "....RR..RR..",
                "...RRRR.RRR.",  // fixed to 12 wide
                "..RRRRRRRRR.",  // 12
                "..RRRRRRRRR.",
                "...RRRRRRRR.",  // last dot fills to 12
                "....RRRRRR..",
                ".....RRRR...",
                "......RR....",
                "............",
                "............"
            ).map { it.padEnd(12, '.') },
            mapOf('R' to "red", 'r' to "dark_red")
        ), version = 1, sourcePrompt = null
    )

    private val star = FusePattern(
        id = "seed-star", title = "Star",
        category = PatternCategory.icons, createdBy = CreatorType.system,
        grid = GridSize(12, 12), difficulty = Difficulty.easy,
        palette = pal(Triple("yellow","Yellow","#F5D000"), Triple("cheddar","Cheddar","#FF9900")),
        tags = listOf("star","classic"),
        cells = cells(
            listOf(
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
                "............"
            ),
            mapOf('Y' to "yellow")
        ), version = 1, sourcePrompt = null
    )

    private val smiley = FusePattern(
        id = "seed-smiley", title = "Smiley Face",
        category = PatternCategory.icons, createdBy = CreatorType.system,
        grid = GridSize(12, 12), difficulty = Difficulty.easy,
        palette = pal(Triple("yellow","Yellow","#F5D000"), Triple("black","Black","#000000")),
        tags = listOf("smiley","face","happy"),
        cells = cells(
            listOf(
                "....YYYY....",
                "...YYYYYY...",
                "..YYYYYYYY..",
                "..YBYYBBYY..",  // B = black eyes
                "..YYYYYYYY..",
                "..YYYYYYYY..",
                "..YBYYYYBY..",
                "..YYBBBBYY..",
                "..YYYYYYYY..",
                "...YYYYYY...",
                "....YYYY....",
                "............"
            ),
            mapOf('Y' to "yellow", 'B' to "black")
        ), version = 1, sourcePrompt = null
    )

    private val diamond = FusePattern(
        id = "seed-diamond", title = "Diamond",
        category = PatternCategory.icons, createdBy = CreatorType.system,
        grid = GridSize(12, 10), difficulty = Difficulty.easy,
        palette = pal(Triple("sky_blue","Sky Blue","#5BC8F5"), Triple("blue","Blue","#1553B0")),
        tags = listOf("diamond","gem"),
        cells = cells(
            listOf(
                ".....BB.....",
                "....BBBB....",
                "...BBSSBB...",
                "..BBSSSSBB..",
                ".BBSSSSSSBB.",
                "BBSSSSSSSSBB",
                ".BBSSSSSSBB.",
                "..BBSSSSBB..",
                "...BBSSBB...",
                "....BBBB...."
            ).map { it.padEnd(12, '.') },
            mapOf('B' to "blue", 'S' to "sky_blue")
        ), version = 1, sourcePrompt = null
    )

    // ─── Animals ──────────────────────────────────────────────────────────────

    private val cupcake = FusePattern(
        id = "seed-cupcake", title = "Cupcake",
        category = PatternCategory.icons, createdBy = CreatorType.system,
        grid = GridSize(12, 12), difficulty = Difficulty.medium,
        palette = pal(Triple("pink","Pink","#FF69B4"), Triple("light_brown","Light Brown","#C8A278"),
            Triple("brown","Brown","#8B5E3C"), Triple("red","Red","#CC1122")),
        tags = listOf("cupcake","food","sweet"),
        cells = cells(
            listOf(
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
                "............"
            ),
            mapOf('P' to "pink", 'R' to "red", 'L' to "light_brown", 'B' to "brown")
        ), version = 1, sourcePrompt = null
    )

    private val cat = FusePattern(
        id = "seed-cat", title = "Cat",
        category = PatternCategory.animals, createdBy = CreatorType.system,
        grid = GridSize(14, 12), difficulty = Difficulty.medium,
        palette = pal(Triple("light_gray","Light Gray","#C8C8C8"), Triple("black","Black","#000000"),
            Triple("pink","Pink","#FF69B4")),
        tags = listOf("cat","animal","pet"),
        cells = cells(
            listOf(
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
                ".............."
            ),
            mapOf('G' to "light_gray", 'B' to "black", 'P' to "pink")
        ), version = 1, sourcePrompt = null
    )

    private val dog = FusePattern(
        id = "seed-dog", title = "Dog",
        category = PatternCategory.animals, createdBy = CreatorType.system,
        grid = GridSize(14, 12), difficulty = Difficulty.medium,
        palette = pal(Triple("tan","Tan","#D2B48C"), Triple("black","Black","#000000"),
            Triple("pink","Pink","#FF69B4"), Triple("brown","Brown","#8B5E3C")),
        tags = listOf("dog","animal","puppy"),
        cells = cells(
            listOf(
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
                ".............."
            ),
            mapOf('T' to "tan", 'B' to "black", 'P' to "pink")
        ), version = 1, sourcePrompt = null
    )

    private val fish = FusePattern(
        id = "seed-fish", title = "Fish",
        category = PatternCategory.animals, createdBy = CreatorType.system,
        grid = GridSize(14, 10), difficulty = Difficulty.easy,
        palette = pal(Triple("orange","Orange","#FF8C00"), Triple("yellow","Yellow","#F5D000"),
            Triple("black","Black","#000000")),
        tags = listOf("fish","sea","ocean"),
        cells = cells(
            listOf(
                "..............","..OOOOOOOOO...",
                "OOOOOOOOOOOOO.","OOOOOOBOOOOOOO",
                "OOOOOOOOOOOOO.","..OOOOOOOOO...",
                "..............",
                "..............",
                "..............",
                ".............."
            ),
            mapOf('O' to "orange", 'B' to "black")
        ), version = 1, sourcePrompt = null
    )

    private val bee = FusePattern(
        id = "seed-bee", title = "Bee",
        category = PatternCategory.animals, createdBy = CreatorType.system,
        grid = GridSize(12, 12), difficulty = Difficulty.medium,
        palette = pal(Triple("yellow","Yellow","#F5D000"), Triple("black","Black","#000000"),
            Triple("white","White","#FFFFFF")),
        tags = listOf("bee","insect","nature"),
        cells = cells(
            listOf(
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
                "............"
            ),
            mapOf('Y' to "yellow", 'B' to "black", 'W' to "white")
        ), version = 1, sourcePrompt = null
    )

    private val butterfly = FusePattern(
        id = "seed-butterfly", title = "Butterfly",
        category = PatternCategory.animals, createdBy = CreatorType.system,
        grid = GridSize(14, 10), difficulty = Difficulty.medium,
        palette = pal(Triple("magenta","Magenta","#FF00CC"), Triple("purple","Purple","#800080"),
            Triple("yellow","Yellow","#F5D000"), Triple("black","Black","#000000")),
        tags = listOf("butterfly","insect","wings"),
        cells = cells(
            listOf(
                "MM....BB....MM",
                "MMMM.BBBB.MMMM",
                "MMMMMBBBBMMMMM",
                "MMMMYBBBBYMMMM",
                "MMMMBBBBBMMMMM",
                ".MMMBBBBMMMMM.",
                "..MMBBBBBMMM..",
                "...MBBBBBMM...",
                "....BBBBB.....",
                ".............."
            ),
            mapOf('M' to "magenta", 'B' to "black", 'Y' to "yellow")
        ), version = 1, sourcePrompt = null
    )

    private val bird = FusePattern(
        id = "seed-bird", title = "Bird",
        category = PatternCategory.animals, createdBy = CreatorType.system,
        grid = GridSize(12, 10), difficulty = Difficulty.easy,
        palette = pal(Triple("sky_blue","Sky Blue","#5BC8F5"), Triple("orange","Orange","#FF8C00")),
        tags = listOf("bird","animal","fly","wings"),
        cells = cells(
            listOf(
                "....SSS.....",
                "...SSSSS....",
                "..SSSSSSS...",
                ".SSSSSSSSSS.",
                "SSSSSSSSSSSS",
                "SSSSSSSSSOSS",
                ".SSSSSSSSOSS",
                "..SSSSSSSSS.",
                "....SSSS....",
                ".....SS....."
            ),
            mapOf('S' to "sky_blue", 'O' to "orange")
        ), version = 1, sourcePrompt = null
    )

    // ─── Nature ──────────────────────────────────────────────────────────────

    private val flower = FusePattern(
        id = "seed-flower", title = "Flower",
        category = PatternCategory.nature, createdBy = CreatorType.system,
        grid = GridSize(12, 12), difficulty = Difficulty.easy,
        palette = pal(Triple("pink","Pink","#FF69B4"), Triple("yellow","Yellow","#F5D000"),
            Triple("green","Green","#2E8B57")),
        tags = listOf("flower","nature","bloom"),
        cells = cells(
            listOf(
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
                "............"
            ),
            mapOf('P' to "pink", 'Y' to "yellow", 'G' to "green")
        ), version = 1, sourcePrompt = null
    )

    private val sun = FusePattern(
        id = "seed-sun", title = "Sun",
        category = PatternCategory.nature, createdBy = CreatorType.system,
        grid = GridSize(12, 12), difficulty = Difficulty.easy,
        palette = pal(Triple("yellow","Yellow","#F5D000"), Triple("cheddar","Cheddar","#FF9900")),
        tags = listOf("sun","weather","bright"),
        cells = cells(
            listOf(
                "..Y....Y.....",
                "...YYYYYY....",
                "....YYYY.....",
                "YYYYYYYYYYYYY",
                ".YYYYYYYYYY..",
                ".YYYYYYYYYY..",
                "YYYYYYYYYYYYY",
                "....YYYY.....",
                "...YYYYYY....",
                "..Y....Y.....",
                ".............",
                "............."
            ).map { it.take(12).padEnd(12, '.') },
            mapOf('Y' to "yellow")
        ), version = 1, sourcePrompt = null
    )

    private val mushroom = FusePattern(
        id = "seed-mushroom", title = "Mushroom",
        category = PatternCategory.nature, createdBy = CreatorType.system,
        grid = GridSize(12, 12), difficulty = Difficulty.easy,
        palette = pal(Triple("red","Red","#CC1122"), Triple("white","White","#FFFFFF"),
            Triple("light_brown","Light Brown","#C8A278")),
        tags = listOf("mushroom","mario","nature"),
        cells = cells(
            listOf(
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
                "............"
            ),
            mapOf('R' to "red", 'W' to "white", 'L' to "light_brown")
        ), version = 1, sourcePrompt = null
    )

    private val tree = FusePattern(
        id = "seed-tree", title = "Pine Tree",
        category = PatternCategory.nature, createdBy = CreatorType.system,
        grid = GridSize(12, 14), difficulty = Difficulty.easy,
        palette = pal(Triple("green","Green","#2E8B57"), Triple("dark_green","Dark Green","#006400"),
            Triple("brown","Brown","#8B5E3C")),
        tags = listOf("tree","pine","nature","christmas"),
        cells = cells(
            listOf(
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
                "............"
            ),
            mapOf('G' to "dark_green", 'B' to "brown")
        ), version = 1, sourcePrompt = null
    )

    private val rainbow = FusePattern(
        id = "seed-rainbow", title = "Rainbow",
        category = PatternCategory.nature, createdBy = CreatorType.system,
        grid = GridSize(16, 10), difficulty = Difficulty.easy,
        palette = pal(Triple("red","Red","#CC1122"), Triple("orange","Orange","#FF8C00"),
            Triple("yellow","Yellow","#F5D000"), Triple("green","Green","#2E8B57"),
            Triple("blue","Blue","#1553B0"), Triple("purple","Purple","#800080")),
        tags = listOf("rainbow","colorful","nature"),
        cells = cells(
            listOf(
                ".......RR.......",
                "......ROORR.....",
                ".....ROYYOOR....",
                "....ROYYGOOR....",
                "...ROYYGGBOOR...",
                "..ROYYGGBBPOOR..",
                ".ROYYGGBBPPOOR..",
                "ROYYGGBBPPOOORR.",
                "................",
                "................"
            ),
            mapOf('R' to "red", 'O' to "orange", 'Y' to "yellow",
                  'G' to "green", 'B' to "blue", 'P' to "purple")
        ), version = 1, sourcePrompt = null
    )

    // ─── Vehicles ────────────────────────────────────────────────────────────

    private val rocket = FusePattern(
        id = "seed-rocket", title = "Rocket",
        category = PatternCategory.vehicles, createdBy = CreatorType.system,
        grid = GridSize(10, 16), difficulty = Difficulty.medium,
        palette = pal(Triple("light_gray","Light Gray","#C8C8C8"), Triple("red","Red","#CC1122"),
            Triple("blue","Blue","#1553B0"), Triple("orange","Orange","#FF8C00")),
        tags = listOf("rocket","space","vehicle"),
        cells = cells(
            listOf(
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
                "............",
                "............"
            ).map { it.take(10).padEnd(10, '.') },
            mapOf('G' to "light_gray", 'R' to "red", 'B' to "blue", 'O' to "orange")
        ), version = 1, sourcePrompt = null
    )

    private val car = FusePattern(
        id = "seed-car", title = "Car",
        category = PatternCategory.vehicles, createdBy = CreatorType.system,
        grid = GridSize(16, 8), difficulty = Difficulty.easy,
        palette = pal(Triple("red","Red","#CC1122"), Triple("sky_blue","Sky Blue","#5BC8F5"),
            Triple("black","Black","#000000"), Triple("light_gray","Light Gray","#C8C8C8")),
        tags = listOf("car","vehicle","transport"),
        cells = cells(
            listOf(
                "....RRRRRRR.....",
                "...RRRSSSSRRR...",
                "..RRSSSSSSSSRR..",
                "RRRRRRRRRRRRRRR.",
                "RRRRRRRRRRRRRRRR",
                "RRRRRRRRRRRRRRR.",
                "..RR.BBBB..RR...",
                "...GBBBBBBG....."
            ).map { it.take(16).padEnd(16, '.') },
            mapOf('R' to "red", 'S' to "sky_blue", 'B' to "black", 'G' to "light_gray")
        ), version = 1, sourcePrompt = null
    )

    // ─── Holidays ─────────────────────────────────────────────────────────────

    private val pumpkin = FusePattern(
        id = "seed-pumpkin", title = "Pumpkin",
        category = PatternCategory.holidays, createdBy = CreatorType.system,
        grid = GridSize(12, 12), difficulty = Difficulty.medium,
        palette = pal(Triple("pumpkin","Pumpkin","#FF6600"), Triple("orange","Orange","#FF8C00"),
            Triple("green","Green","#2E8B57"), Triple("black","Black","#000000")),
        tags = listOf("pumpkin","halloween","fall"),
        cells = cells(
            listOf(
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
                "............"
            ),
            mapOf('P' to "pumpkin", 'G' to "green", 'B' to "black")
        ), version = 1, sourcePrompt = null
    )

    private val christmasTree = FusePattern(
        id = "seed-xmas-tree", title = "Christmas Tree",
        category = PatternCategory.holidays, createdBy = CreatorType.system,
        grid = GridSize(14, 14), difficulty = Difficulty.medium,
        palette = pal(Triple("green","Green","#2E8B57"), Triple("yellow","Yellow","#F5D000"),
            Triple("red","Red","#CC1122"), Triple("brown","Brown","#8B5E3C")),
        tags = listOf("christmas","holiday","tree"),
        cells = cells(
            listOf(
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
                ".............."
            ),
            mapOf('G' to "green", 'Y' to "yellow", 'R' to "red", 'B' to "brown")
        ), version = 1, sourcePrompt = null
    )

    private val snowflake = FusePattern(
        id = "seed-snowflake", title = "Snowflake",
        category = PatternCategory.holidays, createdBy = CreatorType.system,
        grid = GridSize(13, 13), difficulty = Difficulty.hard,
        palette = pal(Triple("sky_blue","Sky Blue","#5BC8F5"), Triple("white","White","#FFFFFF")),
        tags = listOf("snowflake","winter","holiday"),
        cells = cells(
            listOf(
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
                "............."
            ),
            mapOf('B' to "sky_blue", 'W' to "white")
        ), version = 1, sourcePrompt = null
    )

    // ─── Fantasy ─────────────────────────────────────────────────────────────

    private val dragon = FusePattern(
        id = "seed-dragon", title = "Dragon",
        category = PatternCategory.fantasy, createdBy = CreatorType.system,
        grid = GridSize(12, 14), difficulty = Difficulty.hard,
        palette = pal(Triple("green","Green","#2E8B57"), Triple("red","Red","#CC1122"),
            Triple("white","White","#FFFFFF"), Triple("black","Black","#000000")),
        tags = listOf("dragon","fantasy","mythical"),
        cells = cells(
            listOf(
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
                "............"
            ),
            mapOf('G' to "green", 'R' to "red", 'W' to "white", 'K' to "black")
        ), version = 1, sourcePrompt = null
    )

    private val unicorn = FusePattern(
        id = "seed-unicorn", title = "Unicorn",
        category = PatternCategory.fantasy, createdBy = CreatorType.system,
        grid = GridSize(12, 14), difficulty = Difficulty.hard,
        palette = pal(Triple("white","White","#FFFFFF"), Triple("yellow","Yellow","#F5D000"),
            Triple("black","Black","#000000"), Triple("pink","Pink","#FF69B4")),
        tags = listOf("unicorn","fantasy","magical"),
        cells = cells(
            listOf(
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
                "............"
            ),
            mapOf('W' to "white", 'Y' to "yellow", 'B' to "black", 'P' to "pink")
        ), version = 1, sourcePrompt = null
    )

    private val crystalBall = FusePattern(
        id = "seed-crystal-ball", title = "Crystal Ball",
        category = PatternCategory.fantasy, createdBy = CreatorType.system,
        grid = GridSize(12, 12), difficulty = Difficulty.medium,
        palette = pal(Triple("sky_blue","Sky Blue","#5BC8F5"), Triple("white","White","#FFFFFF"),
            Triple("gray","Gray","#808080")),
        tags = listOf("crystal","magic","fantasy"),
        cells = cells(
            listOf(
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
                "............"
            ),
            mapOf('B' to "sky_blue", 'W' to "white", 'G' to "gray")
        ), version = 1, sourcePrompt = null
    )

    private val wizardHat = FusePattern(
        id = "seed-wizard-hat", title = "Wizard Hat",
        category = PatternCategory.fantasy, createdBy = CreatorType.system,
        grid = GridSize(10, 12), difficulty = Difficulty.easy,
        palette = pal(Triple("dark_purple","Dark Purple","#4B0082"), Triple("yellow","Yellow","#F5D000"),
            Triple("white","White","#FFFFFF")),
        tags = listOf("wizard","hat","magic","fantasy"),
        cells = cells(
            listOf(
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
                "PPPPPPPPPP"
            ),
            mapOf('P' to "dark_purple", 'Y' to "yellow", 'W' to "white")
        ), version = 1, sourcePrompt = null
    )
}
