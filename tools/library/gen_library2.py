"""Procedural generators for 10 more categories (animals, birds, fish, bugs,
food, sweets, trees, vehicles, snowflakes, holidays).

Same approach and quality bar as gen_library.py: parametric compositions with
genuine variety, drawn as touching "fused" beads. Each generate_<cat>() returns
100 FusePattern dicts.
"""
import math
import random

from beadlib import make_pattern, stable_id
from canvas import Grid, star_points, reg_polygon, heart_points

# Contrast helper shared shape: pale subjects get a darker backdrop.
PALE = {"white", "cream", "ivory", "light_gray", "silver", "lemon",
        "toothpaste", "periwinkle", "light_lavender", "light_pink",
        "light_green", "light_blue", "light_teal", "peach", "blush", "clear"}


def _finish(cat, title, g, tags, key=None):
    return make_pattern(stable_id(cat, key or title), title, cat,
                        g.w, g.h, g.cells(), tags)


def _eyes(g, lx, ly, rx, ry, r, pupil="black", white=True):
    if white:
        g.disc(lx, ly, r * 1.5, "white")
        g.disc(rx, ry, r * 1.5, "white")
    g.disc(lx, ly, r, pupil)
    g.disc(rx, ry, r, pupil)
    if white:
        g.set(int(lx - r * 0.4), int(ly - r * 0.4), "white")
        g.set(int(rx - r * 0.4), int(ry - r * 0.4), "white")


# ── ANIMALS: cute faces (round face + ears + features) ───────────────────────

def _animal(g, cc, s, face, ear, ear_col, nose_col, kind):
    R = s * 0.4
    er = s * 0.17
    # lion mane behind the face
    if kind == "lion":
        for k in range(14):
            a = 2 * math.pi * k / 14
            g.disc(cc + R * 1.05 * math.cos(a), cc + R * 1.05 * math.sin(a), s * 0.09, "orange")
    # ears (frog eyes are drawn on top instead)
    if kind != "frog":
        for sgn in (-1, 1):
            ex, ey = cc + sgn * s * 0.27, cc - s * 0.3
            if kind == "cow":
                g.ellipse(cc + sgn * R * 0.95, cc - s * 0.14, er * 0.5, er * 0.7, ear_col)
                g.poly([(cc + sgn * s * 0.18, cc - s * 0.34), (cc + sgn * s * 0.24, cc - s * 0.5),
                        (cc + sgn * s * 0.1, cc - s * 0.36)], "cream")   # horn
                continue
            if ear == "pointy":
                g.poly([(ex - er * 0.75, ey + er), (ex, ey - er), (ex + er * 0.75, ey + er)], ear_col)
            elif ear == "round":
                rr = er * (1.15 if kind == "koala" else 0.85)
                g.disc(ex, ey, rr, ear_col)
            elif ear == "tall":
                g.ellipse(ex - sgn * er * 0.2, ey - er * 0.4, er * 0.42, er * 1.25, ear_col)
            elif ear == "floppy":
                g.ellipse(ex + sgn * er * 0.2, ey + er * 0.5, er * 0.55, er * 0.95, ear_col)
    g.disc(cc, cc, R, face)
    if ear in ("pointy", "tall") and kind not in ("cow",):
        for sgn in (-1, 1):
            g.disc(cc + sgn * s * 0.27, cc - s * 0.28, er * 0.32, nose_col)
    ex, ey_ = s * 0.15, -0.02
    if kind == "frog":
        for sgn in (-1, 1):                              # eyes bulge on top
            g.disc(cc + sgn * s * 0.16, cc - s * 0.34, s * 0.12, face)
            g.disc(cc + sgn * s * 0.16, cc - s * 0.36, s * 0.06, "white")
            g.disc(cc + sgn * s * 0.16, cc - s * 0.35, s * 0.035, "black")
        g.line(cc - s * 0.22, cc + s * 0.14, cc + s * 0.22, cc + s * 0.14, "dark_green")  # wide mouth
        g.disc(cc - s * 0.22, cc + s * 0.14, s * 0.02, "dark_green")
        g.disc(cc + s * 0.22, cc + s * 0.14, s * 0.02, "dark_green")
        return
    _eyes(g, cc - s * ex, cc + s * ey_, cc + s * ex, cc + s * ey_, s * 0.05)
    g.disc(cc, cc + s * 0.1, s * (0.08 if kind == "koala" else 0.05), nose_col)
    g.line(cc, cc + s * 0.15, cc, cc + s * 0.2, "dark_brown")
    if kind in ("dog", "monkey"):                        # muzzle + tongue
        g.disc(cc, cc + s * 0.16, s * 0.13, "cream" if kind == "dog" else "tan")
        g.disc(cc, cc + s * 0.1, s * 0.05, nose_col)
        if kind == "dog":
            g.disc(cc, cc + s * 0.24, s * 0.05, "hot_pink")
    if kind == "cat":
        for sgn in (-1, 1):
            g.line(cc + sgn * s * 0.16, cc + s * 0.1, cc + sgn * s * 0.36, cc + s * 0.06, "dark_gray")
            g.line(cc + sgn * s * 0.16, cc + s * 0.14, cc + sgn * s * 0.36, cc + s * 0.16, "dark_gray")
    if kind == "panda":
        g.ellipse(cc - s * 0.15, cc - s * 0.02, s * 0.1, s * 0.12, "black")
        g.ellipse(cc + s * 0.15, cc - s * 0.02, s * 0.1, s * 0.12, "black")
        _eyes(g, cc - s * 0.15, cc - s * 0.02, cc + s * 0.15, cc - s * 0.02, s * 0.04)
    if kind == "raccoon":                                # bandit mask
        g.ellipse(cc - s * 0.15, cc - s * 0.02, s * 0.11, s * 0.09, "black")
        g.ellipse(cc + s * 0.15, cc - s * 0.02, s * 0.11, s * 0.09, "black")
        g.rect(cc - s * 0.24, cc - s * 0.08, cc + s * 0.24, cc + s * 0.02, "black")
        _eyes(g, cc - s * 0.15, cc - s * 0.02, cc + s * 0.15, cc - s * 0.02, s * 0.04)
    if kind == "fox":
        g.disc(cc, cc + s * 0.18, s * 0.15, "white")
        g.disc(cc, cc + s * 0.1, s * 0.05, nose_col)
    if kind == "cow":
        for (dx, dy, r) in [(-0.22, -0.18, 0.1), (0.2, 0.2, 0.12)]:
            g.disc(cc + s * dx, cc + s * dy, s * r, "dark_gray")
        g.ellipse(cc, cc + s * 0.16, s * 0.16, s * 0.11, "pink")   # snout
        g.disc(cc - s * 0.06, cc + s * 0.16, s * 0.03, "hot_pink")
        g.disc(cc + s * 0.06, cc + s * 0.16, s * 0.03, "hot_pink")
    if kind == "tiger":
        for yy in (-0.22, 0.0):
            g.line(cc - s * 0.3, cc + s * yy, cc - s * 0.16, cc + s * (yy + 0.05), "dark_gray")
            g.line(cc + s * 0.3, cc + s * yy, cc + s * 0.16, cc + s * (yy + 0.05), "dark_gray")


def generate_animals():
    out = []
    # (kind, face, ear, ear_col, nose_col)
    A = [
        ("cat", "orange", "pointy", "orange", "pink"),
        ("cat", "light_gray", "pointy", "light_gray", "pink"),
        ("dog", "caramel", "floppy", "brown", "black"),
        ("dog", "cream", "floppy", "caramel", "black"),
        ("bear", "brown", "round", "brown", "black"),
        ("bunny", "white", "tall", "white", "pink"),
        ("bunny", "light_pink", "tall", "light_pink", "hot_pink"),
        ("panda", "white", "round", "black", "black"),
        ("fox", "orange", "pointy", "orange", "black"),
        ("pig", "pink", "pointy", "pink", "hot_pink"),
        ("frog", "green", "round", "green", "dark_green"),
        ("koala", "gray", "round", "gray", "dark_gray"),
        ("mouse", "light_gray", "round", "light_gray", "pink"),
        ("lion", "cheddar", "round", "cheddar", "brown"),
        ("tiger", "orange", "pointy", "orange", "pink"),
        ("cow", "white", "side", "pink", "black"),
        ("sheep", "cream", "floppy", "tan", "black"),
        ("monkey", "brown", "round", "brown", "tan"),
        ("raccoon", "gray", "pointy", "gray", "black"),
        ("bear", "caramel", "round", "caramel", "black"),
    ]
    bgs = ["light_blue", "light_green", "lemon", "light_pink", "periwinkle"]
    i = 0
    while len(out) < 100:
        kind, face, ear, ear_col, nose = A[i % len(A)]
        v = i // len(A)
        s = 26
        g = Grid(s, s)
        g.fill(bgs[v % len(bgs)])
        cc = (s - 1) / 2
        _animal(g, cc, s, face, ear, ear_col, nose, kind)
        # small accessory to differentiate variants (kept subtle, on the ear)
        acc = v % 5
        if acc == 1:
            _fill_bow(g, cc - s * 0.27, cc - s * 0.36, s * 0.09, "hot_pink")
        elif acc == 2:
            _fill_bow(g, cc + s * 0.27, cc - s * 0.36, s * 0.09, "red")
        title = kind.title()
        out.append(_finish("animals", f"{title} {len(out)+1}", g,
                           ["animal", kind, "cute"], f"animal-{kind}-{i}"))
        i += 1
    return out


def _fill_bow(g, x, y, r, col):
    g.poly([(x - r, y - r * 0.7), (x, y), (x - r, y + r * 0.7)], col)
    g.poly([(x + r, y - r * 0.7), (x, y), (x + r, y + r * 0.7)], col)
    g.disc(x, y, r * 0.35, col)


def _candy_cane(g, cc, s, c1="red", c2="white"):
    """A centered candy cane: a vertical stem with a hook curving up-left."""
    r = s * 0.055
    cx = cc + s * 0.09
    idx = 0
    hr = s * 0.15
    for k in range(17):                 # hook: upper half circle, right end -> left
        a = math.pi * k / 16
        x = (cx - hr) + hr * math.cos(a)
        y = s * 0.3 - hr * math.sin(a)
        g.disc(x, y, r, c1 if (idx // 2) % 2 else c2)
        idx += 1
    for t in range(int(s * 0.52)):      # stem straight down from top of hook
        g.disc(cx, s * 0.3 + t, r, c1 if ((t + idx) // 3) % 2 else c2)


# ── BIRDS ────────────────────────────────────────────────────────────────────

def generate_birds():
    out = []
    B = [("robin", "brown", "orange"), ("bluebird", "sky_blue", "banana"),
         ("cardinal", "red", "orange"), ("parrot", "neon_green", "red"),
         ("canary", "yellow", "orange"), ("dove", "white", "cheddar"),
         ("bluejay", "blue", "navy"), ("flamingo", "hot_pink", "orange"),
         ("sparrow", "tan", "brown"), ("magpie", "black", "orange"),
         ("finch", "cheddar", "brown"), ("kingfisher", "turquoise", "orange"),
         ("penguin", "black", "orange"), ("owl", "brown", "cheddar"),
         ("toucan", "black", "yellow"), ("peacock", "teal", "navy")]
    bgs = ["light_blue", "toothpaste", "cream", "light_green", "periwinkle"]
    i = 0
    while len(out) < 100:
        name, body, beak = B[i % len(B)]
        v = i // len(B)
        s = 26
        g = Grid(s, s)
        g.fill(bgs[v % len(bgs)])
        cx, cy = s * 0.46, s * 0.55
        crest = (name in ("cardinal", "bluejay", "parrot", "peacock"))
        g.ellipse(cx, cy, s * 0.2, s * 0.26, body)       # body
        g.disc(cx + s * 0.02, cy - s * 0.26, s * 0.13, body)  # head
        if name == "owl":
            _eyes(g, cx - s * 0.06, cy - s * 0.26, cx + s * 0.1, cy - s * 0.26, s * 0.06)
        else:
            g.disc(cx + s * 0.08, cy - s * 0.28, s * 0.03, "black")
            g.set(int(cx + s * 0.07), int(cy - s * 0.29), "white")
        g.poly([(cx + s * 0.12, cy - s * 0.28), (cx + s * 0.32, cy - s * 0.24),
                (cx + s * 0.12, cy - s * 0.2)], beak)     # beak
        g.ellipse(cx - s * 0.04, cy, s * 0.1, s * 0.18, _shade(body))  # wing
        g.poly([(cx - s * 0.18, cy + s * 0.05), (cx - s * 0.36, cy + s * 0.16),
                (cx - s * 0.16, cy + s * 0.22)], body)    # tail
        if crest:
            g.poly([(cx - s * 0.02, cy - s * 0.36), (cx + s * 0.06, cy - s * 0.5),
                    (cx + s * 0.12, cy - s * 0.34)], body)
        g.disc(cx + s * 0.16, cy + s * 0.3, s * 0.03, beak)  # foot hint
        out.append(_finish("birds", f"{name.title()} {len(out)+1}", g,
                           ["bird", name], f"bird-{name}-{i}"))
        i += 1
    return out


_SHADE = {"orange": "pumpkin", "red": "dark_red", "sky_blue": "blue", "blue": "dark_blue",
          "neon_green": "green", "yellow": "cheddar", "white": "light_gray",
          "hot_pink": "magenta", "tan": "brown", "black": "dark_gray", "cheddar": "orange",
          "turquoise": "teal", "brown": "dark_brown", "teal": "dark_green", "green": "forest",
          "pink": "hot_pink", "aqua": "teal", "purple": "dark_purple", "magenta": "purple",
          "banana": "cheddar", "caramel": "brown", "gray": "dark_gray", "cream": "tan",
          "light_blue": "sky_blue", "lavender": "purple", "peach": "orange"}


def _shade(c):
    return _SHADE.get(c, "dark_gray")


# ── FISH ─────────────────────────────────────────────────────────────────────

def generate_fish():
    out = []
    hues = ["orange", "red", "yellow", "hot_pink", "aqua", "sky_blue", "purple",
            "neon_green", "magenta", "turquoise", "cheddar", "blue", "teal",
            "pumpkin", "lavender", "light_blue"]
    patterns = ["plain", "stripes", "spots", "twotone"]
    i = 0
    while len(out) < 100:
        body = hues[i % len(hues)]
        pat = patterns[(i // len(hues)) % len(patterns)]
        s = 24
        g = Grid(s, s)
        g.fill(["navy", "dark_blue", "blue", "teal"][i % 4])
        cx, cy = s * 0.44, (s - 1) / 2
        g.ellipse(cx, cy, s * 0.3, s * 0.2, body)         # body
        g.poly([(cx + s * 0.28, cy), (cx + s * 0.46, cy - s * 0.16),
                (cx + s * 0.46, cy + s * 0.16)], body)    # tail
        g.poly([(cx - s * 0.05, cy - s * 0.18), (cx + s * 0.08, cy - s * 0.32),
                (cx + s * 0.12, cy - s * 0.16)], _shade(body))  # top fin
        if pat == "stripes":
            for dx in (-0.12, 0.0, 0.12):
                g.line(cx + s * dx, cy - s * 0.16, cx + s * dx, cy + s * 0.16, _shade(body))
        elif pat == "spots":
            for (dx, dy) in [(-0.1, -0.05), (0.02, 0.06), (0.12, -0.03)]:
                g.disc(cx + s * dx, cy + s * dy, s * 0.04, _shade(body))
        elif pat == "twotone":
            g.poly([(cx - s * 0.3, cy), (cx + s * 0.1, cy - s * 0.18),
                    (cx + s * 0.1, cy + s * 0.18)], _shade(body))
        g.disc(cx - s * 0.16, cy - s * 0.05, s * 0.045, "white")
        g.disc(cx - s * 0.16, cy - s * 0.05, s * 0.02, "black")
        g.line(cx - s * 0.28, cy + s * 0.04, cx - s * 0.22, cy + s * 0.04, "dark_gray")  # mouth
        # bubbles
        g.disc(cx - s * 0.34, cy - s * 0.24, 1.2, "toothpaste")
        out.append(_finish("fish", f"Fish {len(out)+1}", g,
                           ["fish", "ocean", body, pat], f"fish-{body}-{pat}-{i}"))
        i += 1
    return out


# ── BUGS ─────────────────────────────────────────────────────────────────────

def _butterfly(g, cc, s, wing, accent):
    for sgn in (-1, 1):
        # upper + lower wings mirrored
        g.ellipse(cc + sgn * s * 0.2, cc - s * 0.12, s * 0.16, s * 0.2, wing)
        g.ellipse(cc + sgn * s * 0.18, cc + s * 0.16, s * 0.12, s * 0.14, wing)
        g.disc(cc + sgn * s * 0.2, cc - s * 0.12, s * 0.06, accent)
        g.disc(cc + sgn * s * 0.18, cc + s * 0.16, s * 0.04, accent)
    g.ellipse(cc, cc, s * 0.045, s * 0.28, "dark_brown")   # body
    g.disc(cc, cc - s * 0.28, s * 0.05, "dark_brown")      # head
    for sgn in (-1, 1):                                     # antennae
        g.line(cc, cc - s * 0.3, cc + sgn * s * 0.1, cc - s * 0.42, "dark_brown")


def generate_bugs():
    out = []
    wingcols = ["hot_pink", "sky_blue", "orange", "purple", "yellow", "aqua",
                "red", "magenta", "neon_green", "turquoise", "lavender", "cheddar"]
    i = 0
    # ~40 butterflies
    while len([o for o in out if o["tags"][0] == "butterfly"]) < 40:
        wing = wingcols[i % len(wingcols)]
        acc = wingcols[(i + 4) % len(wingcols)]
        s = 24
        g = Grid(s, s)
        g.fill(["light_green", "light_blue", "cream", "lemon", "periwinkle"][i % 5])
        _butterfly(g, (s - 1) / 2, s, wing, acc)
        out.append(_finish("bugs", f"Butterfly {i+1}", g,
                           ["butterfly", "bug", wing], f"bfly-{wing}-{acc}-{i}"))
        i += 1
    # ladybugs (10)
    for j, (dome, spot) in enumerate([("red", "black"), ("orange", "black"),
                                      ("hot_pink", "dark_purple"), ("yellow", "black"),
                                      ("red", "dark_red"), ("magenta", "black"),
                                      ("pumpkin", "black"), ("neon_green", "dark_green"),
                                      ("sky_blue", "navy"), ("purple", "dark_purple")]):
        s = 22
        g = Grid(s, s)
        g.fill("light_green")
        cc = (s - 1) / 2
        g.disc(cc, cc + s * 0.05, s * 0.32, dome)
        g.disc(cc, cc - s * 0.22, s * 0.14, "black")
        g.line(cc, cc - s * 0.1, cc, cc + s * 0.34, "black")
        for (dx, dy) in [(-0.14, -0.05), (0.14, -0.05), (-0.12, 0.16), (0.12, 0.16)]:
            g.disc(cc + s * dx, cc + s * dy, s * 0.05, spot)
        out.append(_finish("bugs", f"Ladybug {j+1}", g, ["ladybug", "bug"], f"lady-{j}"))
    # bees (6)
    for j, bg in enumerate(["light_blue", "lemon", "light_green", "periwinkle", "cream", "toothpaste"]):
        s = 22
        g = Grid(s, s)
        g.fill(bg)
        cc = (s - 1) / 2
        g.ellipse(cc - s * 0.2, cc - s * 0.14, s * 0.13, s * 0.09, "white")   # wings first
        g.ellipse(cc + s * 0.2, cc - s * 0.14, s * 0.13, s * 0.09, "white")
        g.ellipse(cc, cc, s * 0.22, s * 0.3, "banana")
        for yy in (-0.16, 0.0, 0.16):
            g.line(cc - s * 0.2, cc + s * yy, cc + s * 0.2, cc + s * yy, "black")
        g.disc(cc, cc - s * 0.34, s * 0.1, "black")
        g.disc(cc - s * 0.03, cc - s * 0.34, 1.0, "white")
        out.append(_finish("bugs", f"Bee {j+1}", g, ["bee", "bug"], f"bee-{j}"))
    # snails (8): clear spiral shell + body + eyestalks
    for j, (shell, ring, body) in enumerate([("orange", "dark_red", "light_green"),
                                             ("hot_pink", "purple", "peach"),
                                             ("purple", "lavender", "light_green"),
                                             ("cheddar", "brown", "tan"),
                                             ("aqua", "teal", "peach"),
                                             ("red", "dark_red", "light_green"),
                                             ("sky_blue", "blue", "cream"),
                                             ("magenta", "dark_purple", "tan")]):
        s = 22
        g = Grid(s, s)
        g.fill("light_green")
        cc = (s - 1) / 2
        g.ellipse(cc + s * 0.02, cc + s * 0.3, s * 0.34, s * 0.09, body)      # foot
        g.ellipse(cc - s * 0.32, cc + s * 0.1, s * 0.08, s * 0.15, body)       # head
        for sgn in (-1, 1):                                                    # eyestalks
            g.line(cc - s * 0.34, cc + s * 0.02, cc - s * 0.4 + sgn * 0.05, cc - s * 0.18, body)
            g.disc(cc - s * 0.42 + sgn * 0.4, cc - s * 0.18, 1.2, "black")
        g.disc(cc + s * 0.06, cc, s * 0.28, shell)                            # shell
        for r in (0.24, 0.17, 0.1, 0.04):
            g.ring(cc + s * 0.06, cc, s * r, ring, 1.6)
        out.append(_finish("bugs", f"Snail {j+1}", g, ["snail", "bug"], f"snail-{j}"))
    # spiders (8)
    for j, col in enumerate(["black", "dark_purple", "dark_red", "brown",
                             "dark_gray", "navy", "purple", "dark_green"]):
        s = 22
        g = Grid(s, s)
        g.fill("lemon")
        cc = (s - 1) / 2
        for sgn in (-1, 1):
            for k, yy in enumerate((-0.14, -0.02, 0.1, 0.22)):
                g.line(cc + sgn * s * 0.12, cc, cc + sgn * s * 0.34, cc + s * (yy - 0.06), col)
                g.line(cc + sgn * s * 0.34, cc + s * (yy - 0.06), cc + sgn * s * 0.34, cc + s * yy, col)
        g.disc(cc, cc + s * 0.05, s * 0.2, col)
        g.disc(cc, cc - s * 0.18, s * 0.11, col)
        g.disc(cc - s * 0.04, cc - s * 0.18, 1.2, "white")
        g.disc(cc + s * 0.04, cc - s * 0.18, 1.2, "white")
        out.append(_finish("bugs", f"Spider {j+1}", g, ["spider", "bug"], f"spider-{j}"))
    # dragonflies (12): visible wings on a soft backdrop
    for j in range(12):
        s = 22
        g = Grid(s, s)
        g.fill(["cream", "light_pink", "lemon"][j % 3])
        cc = (s - 1) / 2
        body = ["sky_blue", "turquoise", "purple", "magenta", "aqua", "blue"][j % 6]
        for sgn in (-1, 1):
            g.ellipse(cc + sgn * s * 0.18, cc - s * 0.12, s * 0.16, s * 0.07, "sky_blue")
            g.ellipse(cc + sgn * s * 0.18, cc + s * 0.1, s * 0.16, s * 0.07, "aqua")
            g.ring(cc + sgn * s * 0.18, cc - s * 0.12, s * 0.16, _shade(body), 1)
        g.ellipse(cc, cc, s * 0.05, s * 0.36, body)
        g.disc(cc, cc - s * 0.36, s * 0.07, body)
        out.append(_finish("bugs", f"Dragonfly {len(out)+1}", g, ["dragonfly", "bug"], f"dfly-{j}"))
    # caterpillars fill the rest
    j = 0
    while len(out) < 100:
        s = 22
        g = Grid(s, s)
        g.fill(["light_blue", "cream", "toothpaste"][j % 3])
        cc = (s - 1) / 2
        col = ["neon_green", "hot_pink", "orange", "aqua", "yellow", "magenta"][j % 6]
        for k in range(6):
            g.disc(3 + k * (s - 6) / 5, cc + (2 if k % 2 else -2), s * 0.11, col)
        g.disc(3, cc - 2, s * 0.12, _shade(col))
        g.disc(2, cc - 4, 1.0, "black")
        g.line(3, cc - 6, 2, cc - 9, _shade(col))
        out.append(_finish("bugs", f"Caterpillar {len(out)+1}", g,
                           ["caterpillar", "bug"], f"cat-{j}"))
        j += 1
    return out


# ── FOOD (fruit & veg) ───────────────────────────────────────────────────────

def generate_food():
    out = []

    def add(title, g, tags, key):
        out.append(_finish("food", f"{title} {len(out)+1}", g, tags, key))

    reds = ["red", "dark_red"]
    i = 0
    specs = ["apple", "cherry", "watermelon", "orange", "strawberry", "grapes",
             "banana", "pear", "lemon", "pineapple", "carrot", "tomato",
             "peach", "plum", "kiwi", "blueberry"]
    while len(out) < 100:
        kind = specs[i % len(specs)]
        s = 22
        g = Grid(s, s)
        g.fill("cream")
        cc = (s - 1) / 2
        if kind == "apple":
            col = ["red", "neon_green", "cheddar"][i // len(specs) % 3]
            g.disc(cc - s * 0.1, cc + s * 0.05, s * 0.24, col)
            g.disc(cc + s * 0.12, cc + s * 0.05, s * 0.24, col)
            g.line(cc, cc - s * 0.2, cc, cc - s * 0.34, "brown")
            g.poly([(cc, cc - s * 0.3), (cc + s * 0.16, cc - s * 0.38), (cc + s * 0.04, cc - s * 0.24)], "green")
            add("Apple", g, ["food", "fruit", "apple"], f"apple-{i}")
        elif kind == "cherry":
            for dx in (-0.12, 0.12):
                g.disc(cc + s * dx, cc + s * 0.18, s * 0.15, "red")
                g.line(cc + s * dx, cc + s * 0.05, cc, cc - s * 0.28, "brown")
            g.poly([(cc, cc - s * 0.28), (cc + s * 0.18, cc - s * 0.34), (cc + s * 0.04, cc - s * 0.2)], "green")
            add("Cherries", g, ["food", "fruit", "cherry"], f"cherry-{i}")
        elif kind == "watermelon":
            g.poly([(cc - s * 0.34, cc - s * 0.28), (cc + s * 0.34, cc - s * 0.28), (cc, cc + s * 0.36)], "green")
            g.poly([(cc - s * 0.3, cc - s * 0.22), (cc + s * 0.3, cc - s * 0.22), (cc, cc + s * 0.3)], "light_green")
            g.poly([(cc - s * 0.26, cc - s * 0.16), (cc + s * 0.26, cc - s * 0.16), (cc, cc + s * 0.24)], "red")
            for (dx, dy) in [(-0.1, 0.0), (0.1, 0.0), (0.0, 0.1), (-0.05, -0.08), (0.05, -0.08)]:
                g.disc(cc + s * dx, cc + s * dy, 0.9, "black")
            add("Watermelon", g, ["food", "fruit", "watermelon"], f"melon-{i}")
        elif kind == "orange":
            g.disc(cc, cc, s * 0.3, "orange")
            for k in range(6):
                a = 2 * math.pi * k / 6
                g.line(cc, cc, cc + s * 0.28 * math.cos(a), cc + s * 0.28 * math.sin(a), "cheddar")
            add("Orange", g, ["food", "fruit", "orange"], f"orange-{i}")
        elif kind == "strawberry":
            g.poly([(cc - s * 0.22, cc - s * 0.1), (cc + s * 0.22, cc - s * 0.1), (cc, cc + s * 0.34)], "red")
            g.poly([(cc - s * 0.2, cc - s * 0.14), (cc + s * 0.2, cc - s * 0.14), (cc, cc - s * 0.3)], "green")
            for (dx, dy) in [(-0.08, 0.02), (0.08, 0.02), (0.0, 0.14), (-0.04, -0.06), (0.04, -0.06)]:
                g.set(int(cc + s * dx), int(cc + s * dy), "lemon")
            add("Strawberry", g, ["food", "fruit", "strawberry"], f"straw-{i}")
        elif kind == "grapes":
            col = ["purple", "neon_green"][i // len(specs) % 2]
            for row, n in enumerate([3, 2, 1]):
                for k in range(n):
                    g.disc(cc - (n - 1) * s * 0.09 + k * s * 0.18, cc - s * 0.15 + row * s * 0.16, s * 0.08, col)
            g.line(cc, cc - s * 0.28, cc, cc - s * 0.36, "brown")
            add("Grapes", g, ["food", "fruit", "grapes"], f"grape-{i}")
        elif kind == "banana":
            g.poly([(cc - s * 0.28, cc - s * 0.2), (cc + s * 0.24, cc + s * 0.28),
                    (cc + s * 0.3, cc + s * 0.18), (cc - s * 0.18, cc - s * 0.28)], "banana")
            add("Banana", g, ["food", "fruit", "banana"], f"banana-{i}")
        elif kind == "pear":
            g.disc(cc, cc + s * 0.12, s * 0.24, "neon_green")
            g.disc(cc, cc - s * 0.1, s * 0.15, "neon_green")
            g.line(cc, cc - s * 0.24, cc, cc - s * 0.34, "brown")
            add("Pear", g, ["food", "fruit", "pear"], f"pear-{i}")
        elif kind == "lemon":
            col = ["lemon", "neon_green"][i // len(specs) % 2]
            g.ellipse(cc, cc, s * 0.3, s * 0.22, col)
            add("Lemon", g, ["food", "fruit", "lemon"], f"lemon-{i}")
        elif kind == "pineapple":
            rx, ry = s * 0.2, s * 0.28
            cy0 = cc + s * 0.08
            g.ellipse(cc, cy0, rx, ry, "cheddar")
            for gy in range(-3, 4):                # clean diamond quilting inside body
                for gx in range(-3, 4):
                    px, py = cc + gx * (rx / 3), cy0 + gy * (ry / 3)
                    if ((px - cc) / rx) ** 2 + ((py - cy0) / ry) ** 2 <= 0.85:
                        g.set(px, py, "orange")
            for fx in (-0.16, -0.06, 0.06, 0.16):  # spiky crown
                g.poly([(cc + s * fx, cc - s * 0.16), (cc + s * fx - 2, cc - s * 0.42), (cc + s * fx + 3, cc - s * 0.2)], "green")
            add("Pineapple", g, ["food", "fruit", "pineapple"], f"pine-{i}")
        elif kind == "carrot":
            g.poly([(cc, cc + s * 0.36), (cc - s * 0.16, cc - s * 0.12), (cc + s * 0.16, cc - s * 0.12)], "orange")
            for dx in (-0.1, 0.0, 0.1):
                g.poly([(cc + s * dx, cc - s * 0.12), (cc + s * dx - 2, cc - s * 0.36), (cc + s * dx + 3, cc - s * 0.2)], "green")
            add("Carrot", g, ["food", "veg", "carrot"], f"carrot-{i}")
        elif kind == "tomato":
            g.disc(cc, cc + s * 0.04, s * 0.28, "red")
            for k in range(5):
                a = 2 * math.pi * k / 5 - math.pi / 2
                g.poly([(cc, cc - s * 0.18), (cc + s * 0.1 * math.cos(a), cc - s * 0.18 + s * 0.1 * math.sin(a)), (cc, cc - s * 0.1)], "green")
            add("Tomato", g, ["food", "veg", "tomato"], f"tomato-{i}")
        elif kind == "peach":
            g.fill("sky_blue")      # peach is pale; needs a contrasting backdrop
            g.disc(cc - s * 0.08, cc + s * 0.04, s * 0.22, "peach")
            g.disc(cc + s * 0.1, cc + s * 0.04, s * 0.22, "peach")
            g.line(cc - s * 0.02, cc, cc - s * 0.02, cc + s * 0.2, "rust")  # cleft
            g.line(cc, cc - s * 0.2, cc, cc - s * 0.3, "brown")
            g.poly([(cc, cc - s * 0.26), (cc + s * 0.14, cc - s * 0.32), (cc + s * 0.02, cc - s * 0.2)], "green")
            add("Peach", g, ["food", "fruit", "peach"], f"peach-{i}")
        elif kind == "plum":
            g.disc(cc, cc, s * 0.28, "dark_purple")
            g.disc(cc - s * 0.08, cc - s * 0.08, s * 0.08, "purple")
            add("Plum", g, ["food", "fruit", "plum"], f"plum-{i}")
        elif kind == "kiwi":
            g.disc(cc, cc, s * 0.3, "brown")
            g.disc(cc, cc, s * 0.24, "light_green")
            g.disc(cc, cc, s * 0.08, "cream")
            for k in range(8):
                a = 2 * math.pi * k / 8
                g.set(int(cc + s * 0.14 * math.cos(a)), int(cc + s * 0.14 * math.sin(a)), "black")
            add("Kiwi", g, ["food", "fruit", "kiwi"], f"kiwi-{i}")
        else:  # blueberry
            for (dx, dy) in [(-0.12, -0.06), (0.12, -0.06), (0.0, 0.06), (-0.06, 0.16), (0.14, 0.14)]:
                g.disc(cc + s * dx, cc + s * dy, s * 0.1, "dark_blue")
                g.disc(cc + s * dx - 1, cc + s * dy - 1, s * 0.03, "blue")
            add("Blueberries", g, ["food", "fruit", "blueberry"], f"blue-{i}")
        i += 1
    return out


# ── SWEETS ───────────────────────────────────────────────────────────────────

def generate_sweets():
    out = []
    specs = ["cupcake", "donut", "icecream", "lollipop", "candycane", "cookie",
             "cake", "popsicle", "macaron", "gummy"]
    frostings = ["hot_pink", "light_pink", "sky_blue", "lavender", "cheddar", "neon_green", "aqua"]
    i = 0
    while len(out) < 100:
        kind = specs[i % len(specs)]
        fr = frostings[(i // len(specs)) % len(frostings)]
        s = 22
        g = Grid(s, s)
        g.fill(["light_blue", "cream", "light_pink", "periwinkle"][i % 4])
        cc = (s - 1) / 2
        if kind == "cupcake":
            g.poly([(cc - s * 0.2, cc + s * 0.06), (cc + s * 0.2, cc + s * 0.06),
                    (cc + s * 0.14, cc + s * 0.34), (cc - s * 0.14, cc + s * 0.34)], "caramel")
            for x in range(int(cc - s * 0.18), int(cc + s * 0.18), 3):
                g.line(x, cc + s * 0.08, x + 2, cc + s * 0.32, "brown")
            g.disc(cc, cc - s * 0.06, s * 0.22, fr)
            g.disc(cc - s * 0.1, cc - s * 0.02, s * 0.12, fr)
            g.disc(cc + s * 0.1, cc - s * 0.02, s * 0.12, fr)
            g.disc(cc, cc - s * 0.24, s * 0.05, "red")
            add_sweet(out, "Cupcake", g, "cupcake", i)
        elif kind == "donut":
            g.disc(cc, cc, s * 0.3, "caramel")
            g.disc(cc, cc, s * 0.3, "caramel")
            g.ring(cc, cc, s * 0.26, fr, s * 0.14)
            g.disc(cc, cc, s * 0.11, g.get(0, 0) or "cream")
            for k in range(8):
                a = 2 * math.pi * k / 8
                g.set(int(cc + s * 0.2 * math.cos(a)), int(cc + s * 0.2 * math.sin(a)),
                      frostings[(k) % len(frostings)])
            add_sweet(out, "Donut", g, "donut", i)
        elif kind == "icecream":
            g.poly([(cc - s * 0.16, cc - s * 0.02), (cc + s * 0.16, cc - s * 0.02), (cc, cc + s * 0.36)], "caramel")
            for a in range(-1, 2):
                g.line(cc + a * 4, cc + s * 0.02, cc + a * 4 - 3, cc + s * 0.32, "brown")
            g.disc(cc, cc - s * 0.14, s * 0.16, fr)
            g.disc(cc - s * 0.1, cc - s * 0.06, s * 0.13, frostings[(i + 2) % len(frostings)])
            g.disc(cc + s * 0.1, cc - s * 0.06, s * 0.13, frostings[(i + 4) % len(frostings)])
            g.disc(cc, cc - s * 0.3, s * 0.04, "red")
            add_sweet(out, "Ice Cream", g, "icecream", i)
        elif kind == "lollipop":
            R = s * 0.24
            cy = cc - s * 0.06
            g.disc(cc, cy, R, "white")
            for t in range(0, 900, 5):          # solid swirl, no hollow center
                a = math.radians(t)
                rr = R * (t / 900.0)
                g.disc(cc + rr * math.cos(a), cy + rr * math.sin(a), 1.3, fr)
            g.line(cc, cy + R, cc, cc + s * 0.42, "light_gray")
            add_sweet(out, "Lollipop", g, "lollipop", i)
        elif kind == "candycane":
            _candy_cane(g, cc, s, "red", "white")
            add_sweet(out, "Candy Cane", g, "candycane", i)
        elif kind == "cookie":
            g.disc(cc, cc, s * 0.3, "caramel")
            for (dx, dy) in [(-0.12, -0.08), (0.1, -0.1), (0.14, 0.08), (-0.08, 0.14), (0.0, 0.02)]:
                g.disc(cc + s * dx, cc + s * dy, s * 0.05, "dark_brown")
            add_sweet(out, "Cookie", g, "cookie", i)
        elif kind == "cake":
            g.poly([(cc - s * 0.28, cc + s * 0.3), (cc + s * 0.28, cc + s * 0.3),
                    (cc + s * 0.28, cc - s * 0.05), (cc, cc - s * 0.28), (cc - s * 0.28, cc - s * 0.05)], "peach")
            g.rect(cc - s * 0.28, cc + s * 0.05, cc + s * 0.28, cc + s * 0.14, fr)
            g.disc(cc, cc - s * 0.26, s * 0.05, "red")
            add_sweet(out, "Cake Slice", g, "cake", i)
        elif kind == "popsicle":
            g.rect(cc - s * 0.16, cc - s * 0.3, cc + s * 0.16, cc + s * 0.18, fr)
            g.rect(cc - s * 0.16, cc - s * 0.02, cc + s * 0.16, cc + s * 0.06, frostings[(i + 3) % len(frostings)])
            g.rect(cc - s * 0.05, cc + s * 0.18, cc + s * 0.05, cc + s * 0.4, "tan")
            add_sweet(out, "Popsicle", g, "popsicle", i)
        elif kind == "macaron":
            g.ellipse(cc, cc - s * 0.12, s * 0.26, s * 0.14, fr)
            g.ellipse(cc, cc + s * 0.12, s * 0.26, s * 0.14, fr)
            g.rect(cc - s * 0.24, cc - s * 0.02, cc + s * 0.24, cc + s * 0.02, "cream")
            add_sweet(out, "Macaron", g, "macaron", i)
        else:  # gummy bear
            g.disc(cc, cc - s * 0.1, s * 0.14, fr)
            g.disc(cc, cc + s * 0.12, s * 0.2, fr)
            for sgn in (-1, 1):
                g.disc(cc + sgn * s * 0.16, cc - s * 0.22, s * 0.06, fr)
                g.disc(cc + sgn * s * 0.2, cc + s * 0.1, s * 0.07, fr)
            _eyes(g, cc - s * 0.06, cc - s * 0.1, cc + s * 0.06, cc - s * 0.1, s * 0.02, white=False)
            add_sweet(out, "Gummy Bear", g, "gummy", i)
        i += 1
    return out


def add_sweet(out, title, g, key, i):
    out.append(_finish("sweets", f"{title} {len(out)+1}", g, ["sweet", "dessert", key], f"{key}-{i}"))


# ── TREES & PLANTS ───────────────────────────────────────────────────────────

def generate_trees():
    out = []
    specs = ["round", "pine", "palm", "cactus", "bush", "potted", "autumn", "birch", "willow", "sprout"]
    greens = ["green", "forest", "dark_green", "neon_green", "light_green"]
    i = 0
    while len(out) < 100:
        kind = specs[i % len(specs)]
        gr = greens[(i // len(specs)) % len(greens)]
        s = 26
        g = Grid(s, s)
        g.fill(["light_blue", "toothpaste", "cream"][i % 3])
        cc = (s - 1) / 2
        if kind == "round":
            g.rect(cc - 2, cc + s * 0.14, cc + 2, cc + s * 0.42, "brown")
            g.disc(cc, cc - s * 0.06, s * 0.3, gr)
            add_tree(out, "Tree", g, "tree", i)
        elif kind == "pine":
            g.rect(cc - 2, cc + s * 0.24, cc + 2, cc + s * 0.42, "brown")
            for k, w in enumerate([0.34, 0.26, 0.16]):
                yy = cc - s * 0.28 + k * s * 0.22
                g.poly([(cc - s * w, yy + s * 0.18), (cc + s * w, yy + s * 0.18), (cc, yy - s * 0.1)], gr)
            add_tree(out, "Pine Tree", g, "pine", i)
        elif kind == "palm":
            g.rect(cc - 2, cc, cc + 3, cc + s * 0.42, "brown")
            for a in (-0.9, -0.4, 0.0, 0.4, 0.9):
                g.line(cc, cc - s * 0.02, cc + s * 0.34 * math.sin(a), cc - s * 0.02 - s * 0.28 * math.cos(a), gr)
                g.disc(cc + s * 0.34 * math.sin(a), cc - s * 0.02 - s * 0.28 * math.cos(a), s * 0.05, gr)
            add_tree(out, "Palm Tree", g, "palm", i)
        elif kind == "cactus":
            g.rect(cc - s * 0.08, cc - s * 0.28, cc + s * 0.08, cc + s * 0.4, gr)
            g.rect(cc - s * 0.28, cc, cc - s * 0.08, cc + s * 0.06, gr)
            g.rect(cc - s * 0.28, cc - s * 0.14, cc - s * 0.22, cc + s * 0.06, gr)
            g.rect(cc + s * 0.08, cc - s * 0.1, cc + s * 0.28, cc - s * 0.04, gr)
            g.rect(cc + s * 0.22, cc - s * 0.24, cc + s * 0.28, cc - s * 0.04, gr)
            g.disc(cc, cc - s * 0.3, s * 0.06, "hot_pink")   # flower
            add_tree(out, "Cactus", g, "cactus", i)
        elif kind == "bush":
            for (dx, dy, r) in [(-0.14, 0.06, 0.18), (0.14, 0.06, 0.18), (0.0, -0.08, 0.2)]:
                g.disc(cc + s * dx, cc + s * dy, s * r, gr)
            for (dx, dy) in [(-0.1, 0.0), (0.12, -0.04), (0.0, 0.08)]:
                g.disc(cc + s * dx, cc + s * dy, 1.2, ["red", "hot_pink", "yellow"][i % 3])
            add_tree(out, "Bush", g, "bush", i)
        elif kind == "potted":
            g.poly([(cc - s * 0.18, cc + s * 0.14), (cc + s * 0.18, cc + s * 0.14),
                    (cc + s * 0.14, cc + s * 0.4), (cc - s * 0.14, cc + s * 0.4)], "rust")
            g.disc(cc, cc - s * 0.02, s * 0.22, gr)
            g.disc(cc - s * 0.1, cc - s * 0.14, s * 0.06, "hot_pink")
            g.disc(cc + s * 0.1, cc - s * 0.12, s * 0.06, "yellow")
            add_tree(out, "Potted Plant", g, "potted", i)
        elif kind == "autumn":
            g.rect(cc - 2, cc + s * 0.14, cc + 2, cc + s * 0.42, "brown")
            g.disc(cc, cc - s * 0.06, s * 0.3, ["orange", "red", "cheddar"][i % 3])
            for (dx, dy) in [(-0.1, 0.0), (0.12, -0.08), (0.06, 0.1)]:
                g.disc(cc + s * dx, cc + s * dy, 1.4, "pumpkin")
            add_tree(out, "Autumn Tree", g, "autumn", i)
        elif kind == "birch":
            g.rect(cc - 2, cc - s * 0.1, cc + 2, cc + s * 0.42, "white")
            for yy in range(int(cc), int(cc + s * 0.4), 4):
                g.set(int(cc - 1), yy, "black")
            g.disc(cc, cc - s * 0.16, s * 0.24, gr)
            add_tree(out, "Birch", g, "birch", i)
        elif kind == "willow":
            g.rect(cc - 2, cc + s * 0.2, cc + 2, cc + s * 0.42, "brown")
            g.disc(cc, cc - s * 0.1, s * 0.26, gr)
            for dx in (-0.2, -0.1, 0.0, 0.1, 0.2):
                g.line(cc + s * dx, cc, cc + s * dx, cc + s * 0.24, gr)
            add_tree(out, "Willow", g, "willow", i)
        else:  # sprout: stem with two leaves angled up + a bud
            g.rect(cc - 1, cc + s * 0.04, cc + 1, cc + s * 0.36, gr)
            g.poly([(cc, cc + s * 0.08), (cc - s * 0.22, cc - s * 0.14), (cc - s * 0.02, cc)], gr)
            g.poly([(cc, cc + s * 0.08), (cc + s * 0.22, cc - s * 0.14), (cc + s * 0.02, cc)], gr)
            g.disc(cc, cc - s * 0.08, s * 0.05, "neon_green")
            add_tree(out, "Sprout", g, "sprout", i)
        i += 1
    return out


def add_tree(out, title, g, key, i):
    out.append(_finish("trees", f"{title} {len(out)+1}", g, ["plant", "tree", key], f"{key}-{i}"))


# ── VEHICLES ─────────────────────────────────────────────────────────────────

def generate_vehicles():
    out = []
    specs = ["car", "truck", "bus", "train", "boat", "sailboat", "plane", "rocket", "bike", "helicopter"]
    cols = ["red", "blue", "yellow", "hot_pink", "neon_green", "orange", "purple",
            "aqua", "cheddar", "turquoise"]
    i = 0
    while len(out) < 100:
        kind = specs[i % len(specs)]
        col = cols[(i // len(specs)) % len(cols)]
        s = 24
        g = Grid(s, s)
        g.fill(["light_blue", "cream", "toothpaste"][i % 3])
        cc = (s - 1) / 2
        if kind == "car":
            g.rect(cc - s * 0.34, cc, cc + s * 0.34, cc + s * 0.16, col)
            g.poly([(cc - s * 0.2, cc), (cc + s * 0.2, cc), (cc + s * 0.12, cc - s * 0.18), (cc - s * 0.12, cc - s * 0.18)], col)
            g.rect(cc - s * 0.14, cc - s * 0.14, cc + s * 0.14, cc - s * 0.02, "sky_blue")
            g.disc(cc - s * 0.2, cc + s * 0.18, s * 0.08, "dark_gray")
            g.disc(cc + s * 0.2, cc + s * 0.18, s * 0.08, "dark_gray")
            add_veh(out, "Car", g, "car", i)
        elif kind == "truck":
            g.rect(cc - s * 0.36, cc - s * 0.06, cc + s * 0.04, cc + s * 0.16, col)
            g.rect(cc + s * 0.04, cc - s * 0.2, cc + s * 0.32, cc + s * 0.16, _shade(col))
            g.rect(cc + s * 0.08, cc - s * 0.16, cc + s * 0.24, cc - s * 0.02, "sky_blue")
            g.disc(cc - s * 0.22, cc + s * 0.18, s * 0.08, "dark_gray")
            g.disc(cc + s * 0.18, cc + s * 0.18, s * 0.08, "dark_gray")
            add_veh(out, "Truck", g, "truck", i)
        elif kind == "bus":
            g.rect(cc - s * 0.38, cc - s * 0.2, cc + s * 0.38, cc + s * 0.16, col)
            for x in range(int(cc - s * 0.3), int(cc + s * 0.34), int(s * 0.16)):
                g.rect(x, cc - s * 0.14, x + int(s * 0.1), cc - s * 0.02, "sky_blue")
            g.disc(cc - s * 0.24, cc + s * 0.18, s * 0.08, "dark_gray")
            g.disc(cc + s * 0.24, cc + s * 0.18, s * 0.08, "dark_gray")
            add_veh(out, "Bus", g, "bus", i)
        elif kind == "train":
            g.rect(cc - s * 0.3, cc - s * 0.1, cc + s * 0.2, cc + s * 0.18, col)
            g.rect(cc + s * 0.2, cc - s * 0.24, cc + s * 0.34, cc + s * 0.18, _shade(col))
            g.rect(cc - s * 0.1, cc - s * 0.34, cc - s * 0.02, cc - s * 0.1, "dark_gray")  # smokestack
            g.disc(cc - s * 0.16, cc - s * 0.4, s * 0.08, "light_gray")   # smoke
            g.disc(cc - s * 0.18, cc + s * 0.2, s * 0.06, "black")
            g.disc(cc, cc + s * 0.2, s * 0.06, "black")
            g.disc(cc + s * 0.22, cc + s * 0.2, s * 0.06, "black")
            add_veh(out, "Train", g, "train", i)
        elif kind == "boat":
            g.poly([(cc - s * 0.34, cc + s * 0.08), (cc + s * 0.34, cc + s * 0.08),
                    (cc + s * 0.22, cc + s * 0.28), (cc - s * 0.22, cc + s * 0.28)], col)
            g.rect(cc - s * 0.16, cc - s * 0.1, cc + s * 0.16, cc + s * 0.08, _shade(col))
            g.rect(cc - s * 0.1, cc - s * 0.08, cc + s * 0.1, cc + s * 0.02, "sky_blue")
            add_veh(out, "Boat", g, "boat", i)
        elif kind == "sailboat":
            g.poly([(cc - s * 0.3, cc + s * 0.16), (cc + s * 0.3, cc + s * 0.16), (cc + s * 0.2, cc + s * 0.32), (cc - s * 0.2, cc + s * 0.32)], "brown")
            g.line(cc, cc - s * 0.36, cc, cc + s * 0.16, "dark_gray")
            g.poly([(cc + 1, cc - s * 0.34), (cc + s * 0.26, cc + s * 0.1), (cc + 1, cc + s * 0.1)], col)
            g.poly([(cc - 1, cc - s * 0.28), (cc - s * 0.2, cc + s * 0.1), (cc - 1, cc + s * 0.1)], _shade(col))
            add_veh(out, "Sailboat", g, "sailboat", i)
        elif kind == "plane":
            g.ellipse(cc, cc, s * 0.32, s * 0.09, col)
            g.poly([(cc - s * 0.05, cc), (cc + s * 0.1, cc - s * 0.26), (cc + s * 0.18, cc)], _shade(col))
            g.poly([(cc - s * 0.05, cc), (cc + s * 0.1, cc + s * 0.26), (cc + s * 0.18, cc)], _shade(col))
            g.poly([(cc - s * 0.3, cc), (cc - s * 0.36, cc - s * 0.14), (cc - s * 0.24, cc)], _shade(col))
            g.disc(cc + s * 0.22, cc, s * 0.05, "sky_blue")
            add_veh(out, "Plane", g, "plane", i)
        elif kind == "rocket":
            g.ellipse(cc, cc, s * 0.12, s * 0.34, col)
            g.poly([(cc, cc - s * 0.44), (cc - s * 0.12, cc - s * 0.2), (cc + s * 0.12, cc - s * 0.2)], "red")
            g.disc(cc, cc - s * 0.06, s * 0.06, "sky_blue")
            g.poly([(cc - s * 0.12, cc + s * 0.16), (cc - s * 0.26, cc + s * 0.32), (cc - s * 0.12, cc + s * 0.32)], _shade(col))
            g.poly([(cc + s * 0.12, cc + s * 0.16), (cc + s * 0.26, cc + s * 0.32), (cc + s * 0.12, cc + s * 0.32)], _shade(col))
            g.poly([(cc - s * 0.06, cc + s * 0.34), (cc, cc + s * 0.46), (cc + s * 0.06, cc + s * 0.34)], "orange")
            add_veh(out, "Rocket Ship", g, "rocket", i)
        elif kind == "bike":
            g.ring(cc - s * 0.2, cc + s * 0.08, s * 0.16, "dark_gray", 2)
            g.ring(cc + s * 0.2, cc + s * 0.08, s * 0.16, "dark_gray", 2)
            g.line(cc - s * 0.2, cc + s * 0.08, cc, cc - s * 0.1, col)
            g.line(cc, cc - s * 0.1, cc + s * 0.2, cc + s * 0.08, col)
            g.line(cc - s * 0.2, cc + s * 0.08, cc + s * 0.05, cc + s * 0.08, col)
            g.line(cc, cc - s * 0.1, cc + s * 0.08, cc - s * 0.16, "black")
            add_veh(out, "Bicycle", g, "bike", i)
        else:  # helicopter
            g.ellipse(cc, cc + s * 0.04, s * 0.22, s * 0.16, col)
            g.poly([(cc + s * 0.2, cc), (cc + s * 0.4, cc - s * 0.02), (cc + s * 0.4, cc + s * 0.08), (cc + s * 0.2, cc + s * 0.1)], _shade(col))
            g.disc(cc - s * 0.06, cc, s * 0.09, "sky_blue")
            g.line(cc - s * 0.34, cc - s * 0.2, cc + s * 0.34, cc - s * 0.2, "dark_gray")
            g.line(cc, cc - s * 0.2, cc, cc - s * 0.06, "dark_gray")
            g.disc(cc - s * 0.16, cc + s * 0.22, s * 0.03, "black")
            g.disc(cc + s * 0.12, cc + s * 0.22, s * 0.03, "black")
            add_veh(out, "Helicopter", g, "helicopter", i)
        i += 1
    return out


def add_veh(out, title, g, key, i):
    out.append(_finish("vehicles", f"{title} {len(out)+1}", g, ["vehicle", key], f"{key}-{i}"))


# ── SNOWFLAKES (6-fold crystalline symmetry) ─────────────────────────────────

def generate_snowflakes():
    out = []
    cols = ["white", "sky_blue", "toothpaste", "aqua", "light_blue", "periwinkle",
            "turquoise", "light_teal", "silver", "cream"]
    bgs = ["navy", "dark_blue", "blue", "dark_purple", "teal"]
    rnd = random.Random(11)
    i = 0
    while len(out) < 100:
        col = cols[i % len(cols)]
        s = [24, 27, 29][i % 3]
        g = Grid(s, s)
        g.fill(bgs[i % len(bgs)])
        cc = (s - 1) / 2.0
        maxr = s / 2.0 - 1
        # design one arm, replicate 6x
        branches = []
        nb = rnd.randint(2, 3)
        for _ in range(nb):
            branches.append((rnd.uniform(0.35, 0.8), rnd.uniform(0.12, 0.22)))
        tip = rnd.choice(["dot", "vee", "none"])
        for k in range(6):
            a = math.pi / 3 * k
            ux, uy = math.cos(a - math.pi / 2), math.sin(a - math.pi / 2)
            # main spine
            ex, ey = cc + maxr * ux, cc + maxr * uy
            g.line(cc, cc, ex, ey, col)
            for (frac, blen) in branches:
                bx, by = cc + maxr * frac * ux, cc + maxr * frac * uy
                for sgn in (-1, 1):
                    ba = a - math.pi / 2 + sgn * math.pi / 3
                    g.line(bx, by, bx + maxr * blen * math.cos(ba),
                           by + maxr * blen * math.sin(ba), col)
            if tip == "dot":
                g.disc(ex, ey, max(1.0, s * 0.05), col)
            elif tip == "vee":
                for sgn in (-1, 1):
                    ba = a - math.pi / 2 + sgn * math.pi / 4
                    g.line(ex, ey, ex + maxr * 0.14 * math.cos(ba), ey + maxr * 0.14 * math.sin(ba), col)
        g.disc(cc, cc, max(1.5, s * 0.08), col)
        out.append(_finish("snowflakes", f"Snowflake {len(out)+1}", g,
                           ["snowflake", "winter", "crystal"], f"snow-{i}-{s}"))
        i += 1
    return out


# ── HOLIDAYS ─────────────────────────────────────────────────────────────────

def generate_holidays():
    out = []
    specs = ["xmastree", "ornament", "gift", "snowman", "pumpkin", "candycane",
             "wreath", "bell", "stocking", "santahat"]
    i = 0
    while len(out) < 100:
        kind = specs[i % len(specs)]
        v = i // len(specs)
        s = 26
        g = Grid(s, s)
        g.fill(["light_blue", "cream", "light_pink", "periwinkle", "toothpaste"][v % 5])
        cc = (s - 1) / 2
        if kind == "xmastree":
            g.rect(cc - 2, cc + s * 0.28, cc + 2, cc + s * 0.42, "brown")
            for k, w in enumerate([0.32, 0.24, 0.15]):
                yy = cc - s * 0.26 + k * s * 0.2
                g.poly([(cc - s * w, yy + s * 0.16), (cc + s * w, yy + s * 0.16), (cc, yy - s * 0.08)], "dark_green")
            g.poly(star_points(cc, cc - s * 0.36, s * 0.08, s * 0.035, 5), "yellow")
            for (dx, dy, c) in [(-0.1, 0.0, "red"), (0.1, -0.06, "hot_pink"), (0.0, 0.12, "sky_blue"), (-0.06, 0.2, "yellow")]:
                g.disc(cc + s * dx, cc + s * dy, 1.4, c)
            add_hol(out, "Christmas Tree", g, "xmastree", i)
        elif kind == "ornament":
            col = ["red", "hot_pink", "blue", "purple", "gold" if False else "cheddar"][v % 5]
            g.rect(cc - s * 0.05, cc - s * 0.34, cc + s * 0.05, cc - s * 0.26, "cheddar")
            g.disc(cc, cc + s * 0.04, s * 0.3, col)
            g.ring(cc, cc + s * 0.04, s * 0.2, _shade(col), 1)
            for k in range(8):
                a = 2 * math.pi * k / 8
                g.set(int(cc + s * 0.26 * math.cos(a)), int(cc + s * 0.04 + s * 0.26 * math.sin(a)), "white")
            add_hol(out, "Ornament", g, "ornament", i)
        elif kind == "gift":
            col = ["red", "hot_pink", "purple", "teal", "blue"][v % 5]
            rib = ["yellow", "lemon", "cheddar", "white"][v % 4]
            g.rect(cc - s * 0.28, cc - s * 0.16, cc + s * 0.28, cc + s * 0.34, col)
            g.rect(cc - s * 0.05, cc - s * 0.16, cc + s * 0.05, cc + s * 0.34, rib)
            g.rect(cc - s * 0.28, cc + s * 0.06, cc + s * 0.28, cc + s * 0.12, rib)
            g.disc(cc - s * 0.08, cc - s * 0.22, s * 0.07, rib)
            g.disc(cc + s * 0.08, cc - s * 0.22, s * 0.07, rib)
            add_hol(out, "Gift", g, "gift", i)
        elif kind == "snowman":
            g.disc(cc, cc + s * 0.24, s * 0.2, "white")
            g.disc(cc, cc - s * 0.02, s * 0.15, "white")
            g.disc(cc, cc - s * 0.24, s * 0.11, "white")
            g.rect(cc - s * 0.12, cc - s * 0.42, cc + s * 0.12, cc - s * 0.32, "black")
            g.rect(cc - s * 0.16, cc - s * 0.32, cc + s * 0.16, cc - s * 0.28, "black")
            g.disc(cc - s * 0.04, cc - s * 0.26, 1.0, "black")
            g.disc(cc + s * 0.04, cc - s * 0.26, 1.0, "black")
            g.poly([(cc, cc - s * 0.2), (cc + s * 0.14, cc - s * 0.18), (cc, cc - s * 0.16)], "orange")
            g.disc(cc, cc - s * 0.02, 1.0, "black")
            g.disc(cc, cc + s * 0.1, 1.0, "black")
            add_hol(out, "Snowman", g, "snowman", i)
        elif kind == "pumpkin":
            g.ellipse(cc, cc + s * 0.04, s * 0.32, s * 0.26, "orange")
            g.ellipse(cc - s * 0.16, cc + s * 0.04, s * 0.1, s * 0.26, "pumpkin")
            g.ellipse(cc + s * 0.16, cc + s * 0.04, s * 0.1, s * 0.26, "pumpkin")
            g.rect(cc - s * 0.03, cc - s * 0.3, cc + s * 0.03, cc - s * 0.18, "dark_green")
            if v % 2 == 0:  # jack-o-lantern
                g.poly([(cc - s * 0.18, cc - s * 0.06), (cc - s * 0.06, cc - s * 0.06), (cc - s * 0.12, cc + s * 0.04)], "black")
                g.poly([(cc + s * 0.18, cc - s * 0.06), (cc + s * 0.06, cc - s * 0.06), (cc + s * 0.12, cc + s * 0.04)], "black")
                g.poly([(cc - s * 0.16, cc + s * 0.14), (cc + s * 0.16, cc + s * 0.14), (cc, cc + s * 0.22)], "black")
            add_hol(out, "Pumpkin", g, "pumpkin", i)
        elif kind == "candycane":
            _candy_cane(g, cc, s, "red", "white")
            add_hol(out, "Candy Cane", g, "candycane2", i)
        elif kind == "wreath":
            g.ring(cc, cc, s * 0.3, "dark_green", s * 0.1)
            for k in range(10):
                a = 2 * math.pi * k / 10
                g.disc(cc + s * 0.3 * math.cos(a), cc + s * 0.3 * math.sin(a), 1.4,
                       ["red", "hot_pink"][k % 2])
            _fill_bow(g, cc, cc + s * 0.32, s * 0.1, "red")
            add_hol(out, "Wreath", g, "wreath", i)
        elif kind == "bell":
            col = ["cheddar", "yellow", "banana"][v % 3]
            g.poly([(cc, cc - s * 0.3), (cc - s * 0.26, cc + s * 0.2), (cc + s * 0.26, cc + s * 0.2)], col)
            g.disc(cc, cc - s * 0.3, s * 0.05, col)
            g.rect(cc - s * 0.3, cc + s * 0.18, cc + s * 0.3, cc + s * 0.26, col)
            g.disc(cc, cc + s * 0.3, s * 0.06, "orange")
            _fill_bow(g, cc, cc - s * 0.34, s * 0.09, "red")
            add_hol(out, "Bell", g, "bell", i)
        elif kind == "stocking":
            col = ["red", "hot_pink", "green"][v % 3]
            g.rect(cc - s * 0.1, cc - s * 0.3, cc + s * 0.14, cc + s * 0.12, col)
            g.poly([(cc - s * 0.1, cc + s * 0.12), (cc + s * 0.14, cc + s * 0.12),
                    (cc - s * 0.28, cc + s * 0.34), (cc - s * 0.28, cc + s * 0.16)], col)
            g.rect(cc - s * 0.12, cc - s * 0.34, cc + s * 0.16, cc - s * 0.26, "white")
            add_hol(out, "Stocking", g, "stocking", i)
        else:  # santa hat
            g.poly([(cc - s * 0.28, cc + s * 0.1), (cc + s * 0.24, cc + s * 0.1), (cc + s * 0.02, cc - s * 0.32)], "red")
            g.rect(cc - s * 0.3, cc + s * 0.08, cc + s * 0.28, cc + s * 0.2, "white")
            g.disc(cc + s * 0.02, cc - s * 0.34, s * 0.08, "white")
            add_hol(out, "Santa Hat", g, "santahat", i)
        i += 1
    return out


def add_hol(out, title, g, key, i):
    out.append(_finish("holidays", f"{title} {len(out)+1}", g, ["holiday", key], f"{key}-{i}"))


# ── VIDEO GAME (retro pixel sprites) ─────────────────────────────────────────

def _ghost(g, cc, s, col):
    g.disc(cc, cc - s * 0.06, s * 0.28, col)
    g.rect(cc - s * 0.28, cc - s * 0.06, cc + s * 0.28, cc + s * 0.2, col)
    for k in range(4):
        g.disc(cc - s * 0.21 + k * s * 0.14, cc + s * 0.2, s * 0.07, col)
    for sgn in (-1, 1):
        g.disc(cc + sgn * s * 0.1, cc - s * 0.06, s * 0.075, "white")
        g.disc(cc + sgn * s * 0.1 + s * 0.03, cc - s * 0.04, s * 0.035, "navy")


def _invader(g, cc, s, col):
    rows = ["..X.....X..", "...X...X...", "..XXXXXXX..", ".XX.XXX.XX.",
            "XXXXXXXXXXX", "X.XXXXXXX.X", "X.X.....X.X", "...XX.XX..."]
    w = len(rows[0])
    px = cc - w * s * 0.036
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "X":
                g.disc(px + x * s * 0.072, cc - s * 0.28 + y * s * 0.072, s * 0.04, col)


def _mushroom(g, cc, s, cap):
    g.disc(cc, cc - s * 0.04, s * 0.3, cap)
    g.rect(cc - s * 0.3, cc - s * 0.04, cc + s * 0.3, cc + s * 0.04, cap)
    g.rect(cc - s * 0.17, cc + s * 0.04, cc + s * 0.17, cc + s * 0.34, "cream")
    g.disc(cc - s * 0.15, cc - s * 0.08, s * 0.07, "white")
    g.disc(cc + s * 0.15, cc - s * 0.08, s * 0.07, "white")
    g.disc(cc, cc - s * 0.2, s * 0.06, "white")
    g.disc(cc - s * 0.08, cc + s * 0.16, s * 0.03, "black")
    g.disc(cc + s * 0.08, cc + s * 0.16, s * 0.03, "black")


def generate_videogame():
    out = []

    def add(title, g, key, tag):
        out.append(_finish("videogame", f"{title} {len(out)+1}", g, ["game", "retro", tag], key))

    ghost_cols = ["red", "hot_pink", "aqua", "orange", "purple", "neon_green", "sky_blue", "magenta"]
    inv_cols = ["neon_green", "aqua", "hot_pink", "yellow", "orange", "purple", "red", "sky_blue"]
    cap_cols = ["red", "neon_green", "blue", "hot_pink", "orange", "purple", "yellow", "aqua"]
    i = 0
    kinds = ["ghost", "invader", "mushroom", "coin", "heart", "sword", "potion",
             "gem", "bomb", "star", "key", "shield", "controller", "skull"]
    while len(out) < 100:
        kind = kinds[i % len(kinds)]
        s = 24
        g = Grid(s, s)
        g.fill(["navy", "dark_blue", "black", "dark_purple"][i % 4])
        cc = (s - 1) / 2
        v = i // len(kinds)
        if kind == "ghost":
            _ghost(g, cc, s, ghost_cols[v % len(ghost_cols)]); add("Ghost", g, f"ghost-{i}", "ghost")
        elif kind == "invader":
            _invader(g, cc, s, inv_cols[v % len(inv_cols)]); add("Invader", g, f"inv-{i}", "invader")
        elif kind == "mushroom":
            _mushroom(g, cc, s, cap_cols[v % len(cap_cols)]); add("Mushroom", g, f"mush-{i}", "mushroom")
        elif kind == "coin":
            g.disc(cc, cc, s * 0.3, "cheddar")
            g.disc(cc, cc, s * 0.22, "yellow")
            g.poly(star_points(cc, cc, s * 0.14, s * 0.06, 5), "cheddar")
            add("Coin", g, f"coin-{i}", "coin")
        elif kind == "heart":
            heart_points  # ensure import used
            g.poly(__import__("canvas").heart_points(cc, cc - 1, s * 0.9), ["red", "hot_pink", "magenta"][v % 3])
            add("1-Up Heart", g, f"life-{i}", "heart")
        elif kind == "sword":
            g.poly([(cc, cc - s * 0.4), (cc - s * 0.06, cc + s * 0.1), (cc + s * 0.06, cc + s * 0.1)], "silver")
            g.rect(cc - s * 0.06, cc + s * 0.1, cc + s * 0.06, cc + s * 0.16, "silver")
            g.rect(cc - s * 0.2, cc + s * 0.14, cc + s * 0.2, cc + s * 0.2, "cheddar")  # guard
            g.rect(cc - s * 0.05, cc + s * 0.2, cc + s * 0.05, cc + s * 0.36, "brown")  # handle
            g.disc(cc, cc + s * 0.38, s * 0.05, "cheddar")
            add("Sword", g, f"sword-{i}", "sword")
        elif kind == "potion":
            col = ["hot_pink", "neon_green", "aqua", "purple", "red"][v % 5]
            g.rect(cc - s * 0.05, cc - s * 0.34, cc + s * 0.05, cc - s * 0.24, "silver")  # cork
            g.rect(cc - s * 0.1, cc - s * 0.24, cc + s * 0.1, cc - s * 0.1, "light_gray")  # neck
            g.disc(cc, cc + s * 0.1, s * 0.24, "light_gray")   # bottle glass
            g.disc(cc, cc + s * 0.16, s * 0.18, col)           # liquid
            g.disc(cc - s * 0.08, cc + s * 0.02, s * 0.05, "white")  # shine
            add("Potion", g, f"potion-{i}", "potion")
        elif kind == "gem":
            col = ["aqua", "hot_pink", "neon_green", "purple", "red", "yellow"][v % 6]
            g.poly([(cc, cc - s * 0.3), (cc + s * 0.26, cc - s * 0.06), (cc, cc + s * 0.34), (cc - s * 0.26, cc - s * 0.06)], col)
            g.poly([(cc, cc - s * 0.3), (cc + s * 0.26, cc - s * 0.06), (cc - s * 0.26, cc - s * 0.06)], _shade(col))
            g.line(cc, cc - s * 0.3, cc, cc + s * 0.34, "white")
            add("Gem", g, f"vgem-{i}", "gem")
        elif kind == "bomb":
            g.disc(cc, cc + s * 0.06, s * 0.28, "dark_gray")
            g.disc(cc - s * 0.1, cc - s * 0.04, s * 0.06, "silver")
            g.rect(cc + s * 0.14, cc - s * 0.2, cc + s * 0.2, cc - s * 0.12, "brown")  # fuse base
            g.line(cc + s * 0.2, cc - s * 0.16, cc + s * 0.3, cc - s * 0.34, "tan")
            g.poly(star_points(cc + s * 0.32, cc - s * 0.36, s * 0.1, s * 0.04, 5), "orange")
            add("Bomb", g, f"bomb-{i}", "bomb")
        elif kind == "star":
            g.poly(star_points(cc, cc, s * 0.4, s * 0.18, 5), "yellow")
            _eyes(g, cc - s * 0.1, cc + s * 0.02, cc + s * 0.1, cc + s * 0.02, s * 0.045, white=False)
            add("Power Star", g, f"pstar-{i}", "star")
        elif kind == "key":
            col = ["cheddar", "yellow", "silver"][v % 3]
            g.ring(cc, cc - s * 0.16, s * 0.13, col, s * 0.06)
            g.rect(cc - s * 0.03, cc - s * 0.04, cc + s * 0.03, cc + s * 0.3, col)
            g.rect(cc, cc + s * 0.2, cc + s * 0.14, cc + s * 0.26, col)
            g.rect(cc, cc + s * 0.28, cc + s * 0.1, cc + s * 0.34, col)
            add("Key", g, f"key-{i}", "key")
        elif kind == "shield":
            col = ["blue", "red", "neon_green", "purple", "cheddar"][v % 5]
            g.poly([(cc - s * 0.26, cc - s * 0.28), (cc + s * 0.26, cc - s * 0.28),
                    (cc + s * 0.26, cc + s * 0.06), (cc, cc + s * 0.36), (cc - s * 0.26, cc + s * 0.06)], col)
            g.poly([(cc - s * 0.16, cc - s * 0.18), (cc + s * 0.16, cc - s * 0.18),
                    (cc + s * 0.16, cc + s * 0.04), (cc, cc + s * 0.24), (cc - s * 0.16, cc + s * 0.04)], "cream")
            g.poly(star_points(cc, cc - s * 0.02, s * 0.12, s * 0.05, 5), col)
            add("Shield", g, f"shield-{i}", "shield")
        elif kind == "controller":
            col = ["dark_gray", "purple", "red", "blue", "neon_green"][v % 5]
            g.ellipse(cc, cc, s * 0.36, s * 0.18, col)
            g.disc(cc - s * 0.34, cc, s * 0.1, col)
            g.disc(cc + s * 0.34, cc, s * 0.1, col)
            g.rect(cc - s * 0.24, cc - s * 0.02, cc - s * 0.1, cc + s * 0.02, "silver")  # dpad h
            g.rect(cc - s * 0.19, cc - s * 0.08, cc - s * 0.15, cc + s * 0.08, "silver")  # dpad v
            g.disc(cc + s * 0.14, cc - s * 0.05, s * 0.04, "red")
            g.disc(cc + s * 0.24, cc + s * 0.03, s * 0.04, "neon_green")
            add("Controller", g, f"ctrl-{i}", "controller")
        else:  # skull
            g.disc(cc, cc - s * 0.04, s * 0.28, "white")
            g.rect(cc - s * 0.16, cc - s * 0.04, cc + s * 0.16, cc + s * 0.24, "white")
            g.disc(cc - s * 0.1, cc - s * 0.04, s * 0.07, "black")
            g.disc(cc + s * 0.1, cc - s * 0.04, s * 0.07, "black")
            g.poly([(cc, cc + s * 0.06), (cc - s * 0.05, cc + s * 0.16), (cc + s * 0.05, cc + s * 0.16)], "black")
            for dx in (-0.1, 0.0, 0.1):
                g.rect(cc + s * dx - 1, cc + s * 0.2, cc + s * dx + 1, cc + s * 0.3, "black")
            add("Skull", g, f"skull-{i}", "skull")
        i += 1
    return out


# ── SPORTS ───────────────────────────────────────────────────────────────────

def generate_sports():
    out = []

    def add(title, g, key, tag):
        out.append(_finish("sports", f"{title} {len(out)+1}", g, ["sport", tag], key))

    kinds = ["soccer", "basketball", "baseball", "tennis", "volleyball", "football",
             "eightball", "bowling", "beachball", "trophy", "medal", "goal"]
    i = 0
    while len(out) < 100:
        kind = kinds[i % len(kinds)]
        s = 24
        g = Grid(s, s)
        g.fill(["light_green", "light_blue", "cream", "toothpaste"][i % 4])
        cc = (s - 1) / 2
        R = s * 0.32
        if kind == "soccer":
            g.disc(cc, cc, R, "white")
            g.ring(cc, cc, R, "dark_gray", 1)
            g.poly(reg_polygon(cc, cc, s * 0.1, 5, rot=-math.pi / 2), "black")
            for k in range(5):
                a = 2 * math.pi * k / 5 - math.pi / 2
                g.poly(reg_polygon(cc + R * 0.72 * math.cos(a), cc + R * 0.72 * math.sin(a), s * 0.05, 5, rot=a), "black")
            add("Soccer Ball", g, f"soccer-{i}", "soccer")
        elif kind == "basketball":
            g.disc(cc, cc, R, "orange")
            g.line(cc - R, cc, cc + R, cc, "black")
            g.line(cc, cc - R, cc, cc + R, "black")
            g.ring(cc - R, cc, R * 0.9, "black", 1)
            g.ring(cc + R, cc, R * 0.9, "black", 1)
            add("Basketball", g, f"bball-{i}", "basketball")
        elif kind == "baseball":
            g.disc(cc, cc, R, "white")
            g.ring(cc, cc, R, "light_gray", 1)
            for sgn in (-1, 1):
                for t in range(-3, 4):
                    g.set(int(cc + sgn * R * 0.6), int(cc + t * 2), "red")
                    g.set(int(cc + sgn * R * 0.6 - sgn), int(cc + t * 2 + 1), "red")
            add("Baseball", g, f"baseball-{i}", "baseball")
        elif kind == "tennis":
            g.disc(cc, cc, R, "neon_green")
            for sgn in (-1, 1):
                for t in range(-4, 5):
                    y = cc + t * (R / 4)
                    x = cc + sgn * (R - abs(t) * (R / 6)) * 0.7
                    g.set(int(x), int(y), "white")
            add("Tennis Ball", g, f"tennis-{i}", "tennis")
        elif kind == "volleyball":
            g.disc(cc, cc, R, "white")
            g.ring(cc, cc, R, "sky_blue", 1)
            for k in range(3):
                a = 2 * math.pi * k / 3 - math.pi / 2
                g.line(cc, cc, cc + R * math.cos(a), cc + R * math.sin(a), "sky_blue")
            add("Volleyball", g, f"volley-{i}", "volleyball")
        elif kind == "football":
            g.ellipse(cc, cc, s * 0.34, s * 0.2, "brown")
            g.line(cc - s * 0.14, cc, cc + s * 0.14, cc, "white")
            for t in range(-2, 3):
                g.line(cc + t * 3, cc - s * 0.04, cc + t * 3, cc + s * 0.04, "white")
            add("Football", g, f"football-{i}", "football")
        elif kind == "eightball":
            g.disc(cc, cc, R, "black")
            g.disc(cc, cc - s * 0.06, s * 0.12, "white")
            g.set(int(cc), int(cc - s * 0.06), "black")
            g.set(int(cc - 1), int(cc - s * 0.06 - 1), "black")
            add("8-Ball", g, f"eight-{i}", "eightball")
        elif kind == "bowling":
            g.disc(cc, cc, R, ["dark_purple", "dark_blue", "dark_red"][i // len(kinds) % 3])
            for (dx, dy) in [(-0.06, -0.1), (0.06, -0.1), (0.0, 0.0)]:
                g.disc(cc + s * dx, cc + s * dy, s * 0.03, "black")
            add("Bowling Ball", g, f"bowl-{i}", "bowling")
        elif kind == "beachball":
            segcols = ["red", "yellow", "sky_blue", "neon_green", "hot_pink", "orange"]
            for k in range(6):
                a0 = 2 * math.pi * k / 6 - math.pi / 2
                a1 = 2 * math.pi * (k + 1) / 6 - math.pi / 2
                g.poly([(cc, cc), (cc + R * math.cos(a0), cc + R * math.sin(a0)),
                        (cc + R * math.cos((a0 + a1) / 2), cc + R * math.sin((a0 + a1) / 2)),
                        (cc + R * math.cos(a1), cc + R * math.sin(a1))], segcols[k])
            g.disc(cc, cc, s * 0.05, "white")
            add("Beach Ball", g, f"beach-{i}", "beachball")
        elif kind == "trophy":
            col = ["cheddar", "yellow"][i // len(kinds) % 2]
            g.disc(cc, cc - s * 0.08, s * 0.2, col)
            g.poly([(cc - s * 0.2, cc - s * 0.2), (cc + s * 0.2, cc - s * 0.2), (cc + s * 0.14, cc + s * 0.06), (cc - s * 0.14, cc + s * 0.06)], col)
            g.ring(cc - s * 0.24, cc - s * 0.1, s * 0.08, col, 1)
            g.ring(cc + s * 0.24, cc - s * 0.1, s * 0.08, col, 1)
            g.rect(cc - s * 0.04, cc + s * 0.06, cc + s * 0.04, cc + s * 0.2, col)
            g.rect(cc - s * 0.16, cc + s * 0.2, cc + s * 0.16, cc + s * 0.3, "brown")
            g.poly(star_points(cc, cc - s * 0.08, s * 0.1, s * 0.04, 5), "white")
            add("Trophy", g, f"trophy-{i}", "trophy")
        elif kind == "medal":
            g.poly([(cc - s * 0.14, cc - s * 0.34), (cc, cc - s * 0.05), (cc - s * 0.24, cc - s * 0.05)], "red")
            g.poly([(cc + s * 0.14, cc - s * 0.34), (cc, cc - s * 0.05), (cc + s * 0.24, cc - s * 0.05)], "blue")
            g.disc(cc, cc + s * 0.12, s * 0.22, "cheddar")
            g.disc(cc, cc + s * 0.12, s * 0.15, "yellow")
            g.poly(star_points(cc, cc + s * 0.12, s * 0.09, s * 0.04, 5), "cheddar")
            add("Medal", g, f"medal-{i}", "medal")
        else:  # goal net
            g.rect(cc - s * 0.34, cc - s * 0.24, cc + s * 0.34, cc + s * 0.28, "white")
            g.frame(cc - s * 0.34, cc - s * 0.24, cc + s * 0.34, cc + s * 0.28, "silver", 2)
            for x in range(int(cc - s * 0.3), int(cc + s * 0.32), 4):
                g.line(x, cc - s * 0.22, x, cc + s * 0.26, "light_gray")
            for y in range(int(cc - s * 0.22), int(cc + s * 0.28), 4):
                g.line(cc - s * 0.32, y, cc + s * 0.32, y, "light_gray")
            g.disc(cc, cc + s * 0.14, s * 0.09, "white")
            g.ring(cc, cc + s * 0.14, s * 0.09, "black", 1)
            add("Goal", g, f"goal-{i}", "goal")
        i += 1
    return out


GENERATORS = {
    "animals": generate_animals,
    "birds": generate_birds,
    "fish": generate_fish,
    "bugs": generate_bugs,
    "food": generate_food,
    "sweets": generate_sweets,
    "trees": generate_trees,
    "vehicles": generate_vehicles,
    "snowflakes": generate_snowflakes,
    "holidays": generate_holidays,
    "videogame": generate_videogame,
    "sports": generate_sports,
}


def generate():
    out = []
    for fn in GENERATORS.values():
        out += fn()
    return out


if __name__ == "__main__":
    import json
    import sys
    from collections import Counter
    if len(sys.argv) > 1 and sys.argv[1] in GENERATORS:
        pats = GENERATORS[sys.argv[1]]()
    else:
        pats = generate()
    json.dump({"version": 1, "patterns": pats}, open("/tmp/gen2.json", "w"))
    print("total", len(pats))
    print(Counter(p["category"] for p in pats))
