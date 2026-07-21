"""Generate the '3D' category: constructions made from multiple bead panels.

Each pattern's grid shows a build layout (for cube-family items, an unfolded
cross net of the six faces). Every 3D pattern carries a buildGuide (how to make
the panels) and an assemblyGuide (how to join them into the finished object),
which the app shows on an Instructions sheet.
"""
from beadlib import make_pattern, cells_from_ascii, stable_id

DOT = "‧"  # empty cell marker used in the ascii art

def _blank(w, h):
    return [[DOT] * w for _ in range(h)]

def _place(grid, ox, oy, rows):
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            grid[oy + y][ox + x] = ch

def cube_net(size, faces, fill):
    """Unfolded cross net of a cube.

        [top]
   [left][front][right][back]
        [bottom]

    `faces` maps face name -> list[str] overlay (chars over the fill), or None
    for a plain face. `fill` is the base color char for every face cell.
    """
    w, h = 4 * size, 3 * size
    g = _blank(w, h)
    face_solid = [[fill] * size for _ in range(size)]
    pos = {
        "top":    (size, 0),
        "left":   (0, size),
        "front":  (size, size),
        "right":  (2 * size, size),
        "back":   (3 * size, size),
        "bottom": (size, 2 * size),
    }
    for name, (ox, oy) in pos.items():
        _place(g, ox, oy, ["".join(r) for r in face_solid])
        overlay = faces.get(name)
        if overlay:
            _place(g, ox, oy, overlay)
    return ["".join(r) for r in g], w, h

def net_pattern(key, title, tags, size, faces, fill, cmap, build, assembly,
                difficulty="medium"):
    rows, w, h = cube_net(size, faces, fill)
    cells = cells_from_ascii(rows, cmap)
    return make_pattern(stable_id("3d", key), title, "threeD", w, h, cells,
                        tags=tags + ["3d", "construction"],
                        difficulty=difficulty, build_guide=build,
                        assembly_guide=assembly)

def panel_pattern(key, title, tags, rows, cmap, build, assembly,
                  difficulty="medium"):
    """A 3D item shown as its main panel; the guide describes the other panels."""
    w = max(len(r) for r in rows)
    h = len(rows)
    cells = cells_from_ascii(rows, cmap)
    return make_pattern(stable_id("3d", key), title, "threeD", w, h, cells,
                        tags=tags + ["3d", "construction"],
                        difficulty=difficulty, build_guide=build,
                        assembly_guide=assembly)

# pip overlays for dice faces (on a 5x5 face)
PIP = "O"
DICE = {
 1: ["‧‧‧‧‧","‧‧‧‧‧","‧‧O‧‧","‧‧‧‧‧","‧‧‧‧‧"],
 2: ["O‧‧‧‧","‧‧‧‧‧","‧‧‧‧‧","‧‧‧‧‧","‧‧‧‧O"],
 3: ["O‧‧‧‧","‧‧‧‧‧","‧‧O‧‧","‧‧‧‧‧","‧‧‧‧O"],
 4: ["O‧‧‧O","‧‧‧‧‧","‧‧‧‧‧","‧‧‧‧‧","O‧‧‧O"],
 5: ["O‧‧‧O","‧‧‧‧‧","‧‧O‧‧","‧‧‧‧‧","O‧‧‧O"],
 6: ["O‧‧‧O","‧‧‧‧‧","O‧‧‧O","‧‧‧‧‧","O‧‧‧O"],
}

def generate():
    out = []

    # 1) Dice: classic 6-face cube, opposite faces sum to 7
    out.append(net_pattern(
        "dice", "Dice (Cube)", ["dice", "cube", "game"],
        size=5,
        faces={"front": DICE[1], "back": DICE[6], "top": DICE[2],
               "bottom": DICE[5], "left": DICE[3], "right": DICE[4]},
        fill="W", cmap={"W": "white", PIP: "black"},
        build=(
            "Make six 5x5 white panels, one for each face of the cube.\n"
            "Add black pips to each panel using the net layout:\n"
            "  • Front = 1, Back = 6, Top = 2, Bottom = 5, Left = 3, Right = 4.\n"
            "Opposite faces always add up to 7, like a real die."
        ),
        assembly=(
            "1. Fuse (iron) each of the six panels so the beads set solid.\n"
            "2. Lay them out in the cross shown, pips facing up.\n"
            "3. Fold the four side panels up around the front panel to form walls.\n"
            "4. Fold the top panel over to close the cube.\n"
            "5. Join touching edges with clear-drying craft glue or by melting\n"
            "   the edge beads together with a low iron. Hold each seam ~20s.\n"
            "6. Add the bottom panel last so you can reach inside while gluing."
        ),
    ))

    # 2) Gift box with lid
    out.append(net_pattern(
        "gift-box", "Gift Box", ["gift", "box", "present", "holiday"],
        size=6,
        faces={"front": ["‧‧RR‧‧"] * 6, "back": ["‧‧RR‧‧"] * 6,
               "left": ["‧‧RR‧‧"] * 6, "right": ["‧‧RR‧‧"] * 6,
               "top": ["RRRRRR", "R‧‧‧‧R", "R‧YY‧R", "R‧YY‧R", "R‧‧‧‧R", "RRRRRR"],
               "bottom": None},
        fill="G", cmap={"G": "green", "R": "red", "Y": "cheddar"},
        build=(
            "Make five 6x6 green panels for the four walls and the base, plus\n"
            "one 6x6 lid panel. Add the red ribbon stripes down each wall and\n"
            "the red border + gold bow on the lid, following the net."
        ),
        assembly=(
            "1. Iron all six panels solid.\n"
            "2. Stand the four wall panels around the base and glue the vertical\n"
            "   seams to form an open box.\n"
            "3. Glue the base panel underneath.\n"
            "4. Leave the lid loose so the box actually opens, or hinge one edge\n"
            "   of the lid to a wall with a short length of clear thread."
        ),
    ))

    # 3) Creeper head (Minecraft-style cube)
    out.append(net_pattern(
        "creeper", "Creeper Head", ["creeper", "cube", "game", "minecraft"],
        size=6,
        faces={"front": ["‧‧‧‧‧‧", "‧KK‧KK", "‧KK‧KK", "‧‧KK‧‧", "‧KKKK‧", "‧K‧‧K‧"],
               "back": None, "left": None, "right": None, "top": None, "bottom": None},
        fill="G", cmap={"G": "green", "K": "black"},
        build=(
            "Make six 6x6 panels in green.\n"
            "On ONE panel (the front) add the black face: two square eyes and the\n"
            "classic frown, as shown in the net. The other five faces stay plain\n"
            "green. Mix two greens if you have them for the blocky look."
        ),
        assembly=(
            "1. Iron every panel.\n"
            "2. Build a cube: glue the four side panels around the front, then add\n"
            "   the top and bottom.\n"
            "3. Keep the face pointing out. Leave the bottom removable if you want\n"
            "   to wear it or set it over something."
        ),
    ))

    # 4) Small house
    out.append(panel_pattern(
        "house", "Little House", ["house", "home", "building"],
        rows=["‧‧RRR‧‧", "‧RRRRR‧", "RRRRRRR", "WWWWWWW", "W‧BB‧DW", "W‧BB‧DW", "WWWWWWW"],
        cmap={"R": "red", "W": "cream", "B": "sky_blue", "D": "brown"},
        build=(
            "Panels needed:\n"
            "  • 4 wall panels (7 wide): use the wall design shown (cream walls,\n"
            "    a blue window and a brown door). Put the door on the front wall\n"
            "    only; give the others two windows.\n"
            "  • 2 roof panels (7 x 4) in red.\n"
            "The pattern grid shows the front wall plus the red roof slope above it."
        ),
        assembly=(
            "1. Iron all panels.\n"
            "2. Glue the four walls into a square tube (door facing front).\n"
            "3. Lean the two red roof panels together into a triangle and glue the\n"
            "   ridge, then glue the roof down onto the walls.\n"
            "4. Optional: leave the roof removable to store little things inside."
        ),
    ))

    # 5) Planter / cup
    out.append(panel_pattern(
        "planter", "Bead Planter", ["planter", "cup", "pot"],
        rows=["TTTTTT", "TGGGGT", "TGGGGT", "TGGGGT", "TGGGGT", "TTTTTT"],
        cmap={"T": "toothpaste", "G": "green"},
        build=(
            "Make 4 identical wall panels (6x6) and 1 base panel (6x6) using the\n"
            "two-tone design shown, a light rim with a green body. All five\n"
            "panels are the same size."
        ),
        assembly=(
            "1. Iron the panels.\n"
            "2. Glue the four walls into an open square tube.\n"
            "3. Glue the base panel on the bottom.\n"
            "4. Line the inside with a small plastic cup before adding a real\n"
            "   plant, so water never touches the beads."
        ),
    ))

    # 6) Treasure chest
    out.append(panel_pattern(
        "treasure-chest", "Treasure Chest", ["treasure", "chest", "box", "pirate"],
        rows=["YYYYYYYY", "YBBBBBBY", "YYYYYYYY", "NNNNNNNN", "N‧‧YY‧‧N", "N‧‧YY‧‧N", "NNNNNNNN"],
        cmap={"N": "brown", "Y": "cheddar", "B": "dark_brown"},
        build=(
            "Panels:\n"
            "  • Body: 2 long sides + 2 short ends + 1 base, in brown with gold\n"
            "    trim (use the lower design).\n"
            "  • Lid: 1 panel with the gold band + lock (use the upper design).\n"
            "The grid shows the curved lid stripe above a front panel with its\n"
            "gold lock plate."
        ),
        assembly=(
            "1. Iron everything.\n"
            "2. Glue the four body walls onto the base to form an open chest.\n"
            "3. Hinge the back edge of the lid to the back wall with clear thread\n"
            "   so it opens and closes.\n"
            "4. Fill it with your smaller bead creations."
        ),
    ))

    # 7) 3D heart box
    out.append(panel_pattern(
        "heart-box", "Heart Box", ["heart", "box", "valentine", "love"],
        rows=["‧PP‧PP‧", "PPPPPPP", "PPPPPPP", "PPPPPPP", "‧PPPPP‧", "‧‧PPP‧‧", "‧‧‧P‧‧‧"],
        cmap={"P": "pink"},
        build=(
            "Cut two heart panels (top and bottom) using the shape shown, plus a\n"
            "long thin 'wall strip' about 3 beads tall that wraps around the whole\n"
            "outline of the heart. Make the strip in the same pink."
        ),
        assembly=(
            "1. Iron the two heart panels and the wall strip.\n"
            "2. Glue the wall strip on its edge all the way around the bottom\n"
            "   heart, curving it to follow the outline.\n"
            "3. Set the second heart on top as a lift-off lid.\n"
            "4. A great little box for a ring or a note."
        ),
    ))

    # 8) Pencil / brush holder
    out.append(panel_pattern(
        "pencil-holder", "Pencil Holder", ["pencil", "holder", "desk", "cup"],
        rows=["BBBBBB", "B‧‧‧‧B", "BYYYYB", "B‧‧‧‧B", "BOOOOB", "BBBBBB"],
        cmap={"B": "blue", "Y": "yellow", "O": "orange"},
        build=(
            "Make 4 tall wall panels (6 wide, 8+ tall works well) with fun\n"
            "horizontal stripes, and 1 base panel (6x6). The grid shows a short\n"
            "version of a wall panel, so make yours taller for real pencils."
        ),
        assembly=(
            "1. Iron the panels.\n"
            "2. Glue the four walls into a square tube.\n"
            "3. Glue on the base.\n"
            "4. Stand it on your desk and fill with pencils and markers."
        ),
    ))

    return out

if __name__ == "__main__":
    ps = generate()
    print(f"3D: {len(ps)} patterns")
    for p in ps:
        print(f"  {p['title']:16s} {p['grid']['width']}x{p['grid']['height']} "
              f"build={'y' if p['buildGuide'] else 'n'} assembly={'y' if p['assemblyGuide'] else 'n'}")
