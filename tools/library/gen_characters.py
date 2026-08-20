"""Retro rubber-hose cartoon characters, headlined by Steamboat Willie.

COPYRIGHT NOTE - read before adding anything here.

The 1928 short *Steamboat Willie* entered the United States public domain on
1 January 2024, and with it that specific 1928 depiction of the mouse: black
and white, pie-cut eyes, no gloves, bare rubber-hose limbs, oversized shoes.
Everything drawn for him below is deliberately held to that version. What is
NOT in the public domain, and must never be drawn here, is the modern
character - colour clothes, white gloves, jointed limbs, expressive pupils -
and the name "Mickey Mouse" remains a live trademark, so the patterns are
titled after the short and never after him.

Every other character in this file is an original design in the same 1920s
house style, invented for this library. They are not caricatures of anyone.

The style is what makes the category work as bead art: solid black masses, one
pale face patch, no midtones. That reads at 28x28 far better than a shaded
subject does.
"""
import math

from canvas import Grid
from gen_creatures import S, _emit, _frame, _pick_bg

# 1928 film stock, not 1935 Technicolor. The "fur" is always near-black, the
# face patch always near-white, and the only real choice is the backdrop.
BACKDROPS = ["sky_blue", "aqua", "banana", "peach", "light_lavender",
             "toothpaste", "light_pink", "cream", "silver", "light_gray"]

INK = "black"
DARK = "dark_gray"
PALE = "cream"
PALER = "white"


# ── the cast ────────────────────────────────────────────────────────────────
# name              ears      earsz head  muzzle  eyes   body    feet   prop
CAST = [
    ("Steamboat Willie", "round", 0.62, 1.00, "wide", "pie", "shorts", "big", "wheel"),
    ("Deckhand Mouse",   "round", 0.55, 0.95, "wide", "pie", "shorts", "big", "rope"),
    ("Riverboat Cat",    "point", 0.48, 1.00, "wide", "dot", "vest",   "big", "none"),
    ("Whistle Pup",      "flop",  0.52, 0.98, "long", "dot", "collar", "mid", "whistle"),
    ("Bandstand Bear",   "round", 0.50, 1.05, "round","dot", "bowtie", "big", "horn"),
    ("Sailor Duck",      "none",  0.00, 0.95, "bill", "dot", "sailor", "web", "none"),
    ("Ragtime Rabbit",   "long",  0.85, 0.92, "round","pie", "vest",   "mid", "none"),
    ("Barrel Bulldog",   "flop",  0.45, 1.10, "wide", "dot", "collar", "big", "none"),
    ("Piano Pig",        "point", 0.42, 1.05, "snout","dot", "shorts", "mid", "none"),
    ("Tugboat Toad",     "none",  0.00, 1.08, "wide", "pie", "vest",   "web", "none"),
    ("Clockwork Kid",    "none",  0.00, 0.90, "round","dot", "sailor", "mid", "key"),
    ("Top Hat Toon",     "none",  0.00, 0.92, "round","pie", "bowtie", "mid", "hat"),
    ("Deckhand Goat",    "horn",  0.55, 0.98, "long", "dot", "vest",   "mid", "none"),
    ("Galley Mouse",     "round", 0.58, 0.95, "wide", "dot", "shorts", "big", "pan"),
    ("Bosun Bird",       "none",  0.00, 0.90, "bill", "pie", "collar", "web", "none"),
    ("Stoker Cat",       "point", 0.46, 1.00, "wide", "pie", "shorts", "big", "shovel"),
]

# pose 3 is a scene rather than a figure, so it only makes sense for the
# characters that actually carry a prop.
POSES = ["bust", "full", "wave", "tall"]


def _head(g, cx, cy, r, spec):
    """The head: ears first so the skull overlaps them, then the face patch."""
    ears, earsz, hr, muzzle, eyes = spec
    er = r * earsz
    if ears == "round":
        # Just far enough apart that the two ears clear each other over the
        # top of the skull. Pushed out further they stop reading as ears on a
        # head and start reading as a bat.
        g.disc(cx - r * 0.88, cy - r * 0.88, er * 0.98, INK)
        g.disc(cx + r * 0.88, cy - r * 0.88, er * 0.98, INK)
    elif ears == "point":
        for s in (-1, 1):
            g.poly([(cx + s * r * 0.30, cy - r * 0.70),
                    (cx + s * r * 0.95, cy - r * 1.55),
                    (cx + s * r * 1.02, cy - r * 0.45)], INK)
    elif ears == "flop":
        for s in (-1, 1):
            g.ellipse(cx + s * r * 0.92, cy + r * 0.10, er * 0.62, er * 1.15, INK)
    elif ears == "long":
        for s in (-1, 1):
            g.ellipse(cx + s * r * 0.42, cy - r * 1.35, er * 0.42, er * 1.05, INK)
    elif ears == "horn":
        for s in (-1, 1):
            g.limb(cx + s * r * 0.55, cy - r * 0.85,
                   cx + s * r * 1.05, cy - r * 1.45, PALE, width=2)

    g.disc(cx, cy, r, INK)

    # The pale patch is the whole point of the 1928 face: one light shape
    # holding both eyes and the snout, with no shading anywhere else.
    if muzzle == "wide":
        g.ellipse(cx, cy + r * 0.16, r * 0.86, r * 0.74, PALE)
    elif muzzle == "round":
        g.ellipse(cx, cy + r * 0.10, r * 0.70, r * 0.70, PALE)
    elif muzzle == "long":
        g.ellipse(cx, cy + r * 0.30, r * 0.62, r * 0.86, PALE)
    elif muzzle == "snout":
        g.ellipse(cx, cy + r * 0.10, r * 0.80, r * 0.62, PALE)
        g.ellipse(cx, cy + r * 0.62, r * 0.34, r * 0.26, "light_pink")
    elif muzzle == "bill":
        g.ellipse(cx, cy - r * 0.05, r * 0.72, r * 0.58, PALE)
        g.ellipse(cx, cy + r * 0.68, r * 0.62, r * 0.30, "orange")

    ey = cy - r * 0.16
    ex = r * 0.30
    if eyes == "pie":
        # Pie-cut eyes: a solid black oval with a pale wedge bitten out of the
        # lower inside corner. That wedge is the whole 1928 signature.
        for s in (-1, 1):
            g.ellipse(cx + s * ex, ey, r * 0.20, r * 0.30, INK)
            g.set(cx + s * ex, ey + r * 0.22, PALE)
    else:
        for s in (-1, 1):
            g.ellipse(cx + s * ex, ey, r * 0.16, r * 0.24, INK)

    if muzzle in ("wide", "round", "long"):
        g.ellipse(cx, cy + r * 0.52, r * 0.22, r * 0.17, INK)     # nose
        for k in range(-1, 2):                                     # smile
            g.set(cx + k * r * 0.30, cy + r * 0.80 + abs(k) * -r * 0.10, INK)


def _body(g, cx, cy, u, spec, pose):
    """Torso, rubber-hose arms and legs, and the shoes they end in."""
    body, feet, prop = spec
    torso_h = u * 3.4
    g.ellipse(cx, cy + torso_h * 0.45, u * 1.9, torso_h * 0.62, INK)

    if body == "shorts":
        # The shorts are black in the film. On a bead board black shorts on a
        # black torso are one shape, so they get the next tone down and the
        # buttons get big enough to survive a 15x15 reduction.
        g.ellipse(cx, cy + torso_h * 0.95, u * 1.9, u * 1.20, DARK)
        for s in (-1, 1):
            g.disc(cx + s * u * 0.95, cy + torso_h * 0.92, u * 0.50, PALE)
    elif body == "vest":
        g.rect(cx - u * 1.4, cy + torso_h * 0.15, cx + u * 1.4, cy + torso_h * 0.85, PALE)
        g.rect(cx - u * 0.25, cy + torso_h * 0.15, cx + u * 0.25, cy + torso_h * 0.85, INK)
    elif body == "sailor":
        g.poly([(cx - u * 1.7, cy + torso_h * 0.05), (cx + u * 1.7, cy + torso_h * 0.05),
                (cx, cy + torso_h * 0.75)], PALE)
    elif body == "collar":
        g.rect(cx - u * 1.7, cy + torso_h * 0.05, cx + u * 1.7, cy + torso_h * 0.35, PALE)
    elif body == "bowtie":
        for s in (-1, 1):
            g.poly([(cx, cy + torso_h * 0.15), (cx + s * u * 1.1, cy - u * 0.15),
                    (cx + s * u * 1.1, cy + torso_h * 0.45)], PALE)

    # arms
    up = pose == "wave"
    g.limb(cx - u * 1.6, cy + torso_h * 0.30,
           cx - u * 3.0, cy + (torso_h * 0.85 if not up else -u * 1.2), INK, width=2)
    g.limb(cx + u * 1.6, cy + torso_h * 0.30,
           cx + u * 3.0, cy + torso_h * 0.85, INK, width=2)
    g.disc(cx - u * 3.0, cy + (torso_h * 0.85 if not up else -u * 1.2), u * 0.7, PALE)
    g.disc(cx + u * 3.0, cy + torso_h * 0.85, u * 0.7, PALE)

    # legs and shoes
    for s in (-1, 1):
        g.limb(cx + s * u * 0.8, cy + torso_h * 1.25,
               cx + s * u * 1.3, cy + torso_h * 2.05, INK, width=2)
        if feet == "big":
            # Shoes a tone lighter than the legs, or the leg-and-shoe reads as
            # one straight black stick.
            g.ellipse(cx + s * u * 1.9, cy + torso_h * 2.20, u * 1.35, u * 0.72, DARK)
        elif feet == "web":
            g.ellipse(cx + s * u * 1.6, cy + torso_h * 2.15, u * 1.05, u * 0.55, "orange")
        else:
            g.ellipse(cx + s * u * 1.5, cy + torso_h * 2.15, u * 0.95, u * 0.60, DARK)


def _prop(g, cx, cy, u, prop):
    """The thing that names the pose - a wheel, a whistle, a shovel."""
    if prop == "wheel":
        import math
        # A rim, a hub, six spokes and six handles. Eight of each at this size
        # closes the gaps between them and the whole thing reads as a grey
        # asterisk; six leaves daylight between the spokes, which is what makes
        # it a wheel.
        g.ring(cx, cy, u * 3.6, DARK, t=u * 0.9)
        g.disc(cx, cy, u * 1.1, DARK)
        for k in range(6):
            a = k * math.pi / 3 + math.pi / 6
            g.limb(cx + math.cos(a) * u * 1.2, cy + math.sin(a) * u * 1.2,
                   cx + math.cos(a) * u * 2.9, cy + math.sin(a) * u * 2.9,
                   DARK, width=1)
            g.limb(cx + math.cos(a) * u * 3.9, cy + math.sin(a) * u * 3.9,
                   cx + math.cos(a) * u * 4.8, cy + math.sin(a) * u * 4.8,
                   DARK, width=2)
    elif prop == "whistle":
        for k, dx in enumerate((-1.6, 0.0, 1.6)):
            g.rect(cx + dx * u - u * 0.5, cy - u * (2.0 + k % 2),
                   cx + dx * u + u * 0.5, cy + u * 2.2, DARK)
        g.disc(cx - u * 2.6, cy - u * 3.8, u * 1.2, PALER)
        g.disc(cx + u * 0.2, cy - u * 4.6, u * 1.5, PALER)
        g.disc(cx + u * 2.8, cy - u * 3.6, u * 1.1, PALER)
    elif prop == "rope":
        g.ring(cx, cy, u * 2.6, PALE, t=u * 0.7)
        g.ring(cx, cy, u * 1.4, PALE, t=u * 0.6)
    elif prop == "horn":
        g.poly([(cx - u * 3.0, cy - u * 1.4), (cx + u * 2.2, cy - u * 2.6),
                (cx + u * 2.2, cy + u * 2.6), (cx - u * 3.0, cy + u * 1.4)], "banana")
        g.rect(cx - u * 4.4, cy - u * 0.7, cx - u * 2.8, cy + u * 0.7, "banana")
    elif prop == "key":
        g.ring(cx, cy - u * 1.6, u * 1.8, DARK, t=u * 0.7)
        g.rect(cx - u * 0.5, cy - u * 1.6, cx + u * 0.5, cy + u * 3.0, DARK)
    elif prop == "hat":
        g.rect(cx - u * 3.2, cy + u * 1.4, cx + u * 3.2, cy + u * 2.2, INK)
        g.rect(cx - u * 2.0, cy - u * 2.6, cx + u * 2.0, cy + u * 1.4, INK)
        g.rect(cx - u * 2.0, cy + u * 0.4, cx + u * 2.0, cy + u * 1.2, "dark_red")
    elif prop == "pan":
        g.disc(cx, cy, u * 2.2, DARK)
        g.rect(cx + u * 2.0, cy - u * 0.4, cx + u * 5.2, cy + u * 0.4, DARK)
    elif prop == "shovel":
        g.limb(cx, cy - u * 3.4, cx, cy + u * 1.6, "dark_brown", width=2)
        g.poly([(cx - u * 1.6, cy + u * 1.4), (cx + u * 1.6, cy + u * 1.4),
                (cx + u * 1.2, cy + u * 3.4), (cx - u * 1.2, cy + u * 3.4)], DARK)


def _draw(g, spec, cx, cy, scale):
    ears, earsz, hr, muzzle, eyes, body, feet, prop = spec["parts"]
    pose = spec["pose"]
    u = scale * 1.7
    if pose == "bust":
        _head(g, cx, cy, u * 4.6 * hr, (ears, earsz, hr, muzzle, eyes))
        return
    if pose == "prop" and prop != "none":
        _head(g, cx, cy - u * 4.6, u * 3.1 * hr, (ears, earsz, hr, muzzle, eyes))
        _prop(g, cx, cy + u * 3.4, u, prop)
        return
    head_r = u * (2.4 if pose != "tall" else 2.1) * hr
    top = cy - u * 6.2
    _head(g, cx, top, head_r, (ears, earsz, hr, muzzle, eyes))
    _body(g, cx, top + head_r * 0.95, u, (body, feet, prop), pose)


# ── the boat itself ─────────────────────────────────────────────────────────

def _radial(rim0, rim1, hub, hlen, spoke, diag, cols):
    """A wheel-like object drawn on odd coordinates so it is exactly symmetric.

    Working in dx = 2x - (S-1) instead of x - S/2 is the whole trick: the
    doubled coordinate of a bead is always an odd integer, so a shape defined
    by |dx| is symmetric bead-for-bead with no rounding to disagree about. The
    float version of the same wheel came out lopsided and read as an asterisk.
    """
    rim_col, spoke_col, hub_col = cols
    g = Grid(S, S)
    for y in range(S):
        for x in range(S):
            dx, dy = 2 * x - (S - 1), 2 * y - (S - 1)
            d = math.hypot(dx, dy) / 2.0
            arm = abs(dx) <= spoke or abs(dy) <= spoke \
                or abs(abs(dx) - abs(dy)) <= diag
            if d <= hub:
                g.set(x, y, hub_col)
            elif rim0 <= d <= rim1:
                g.set(x, y, rim_col)
            elif d < rim0 and arm:
                g.set(x, y, spoke_col)
            elif rim1 < d <= rim1 + hlen and arm:
                g.set(x, y, rim_col)
    return g


# name             rim0 rim1 hub hlen spoke diag  colours
OBJECTS = [
    ("Ship's Wheel",  8.0, 10.2, 3.0, 2.2, 1, 1, (DARK, DARK, DARK)),
    ("Pilot Wheel",   7.4,  9.4, 2.6, 3.0, 1, 1, ("dark_brown", "dark_brown",
                                                  "banana")),
    ("Life Ring",     7.6, 11.0, 0.0, 0.0, 0, 0, ("white", "white", "white")),
    ("Deck Capstan",  5.0,  9.0, 3.6, 1.6, 3, 3, (DARK, INK, DARK)),
]


def _build_object(spec):
    name, r0, r1, hub, hlen, sp, dg, cols = spec["parts"]
    g = _radial(r0, r1, hub, hlen, sp, dg, cols)
    if name == "Life Ring":
        # Four red quarters is what makes a white ring a LIFE ring rather than
        # a plain donut.
        for y in range(S):
            for x in range(S):
                if g.g[y][x] is None:
                    continue
                dx, dy = 2 * x - (S - 1), 2 * y - (S - 1)
                if (dx > 0) == (dy > 0) and abs(dx) > 3 and abs(dy) > 3:
                    g.set(x, y, "red")
    out = Grid(S, S)
    out.fill(spec["bg"])
    for y in range(S):
        for x in range(S):
            if g.g[y][x] is not None:
                out.set(x, y, g.g[y][x])
    return out


# ── the boat ────────────────────────────────────────────────────────────────
#
# Hand-authored, unlike everything above it. The parametric version drew the
# hull, the deckhouse and the upper cabin as three stacked shapes on a canvas
# it then rescaled to fit, and at 28x28 the result was a stepped pyramid with
# candles on it - a wedding cake, not a steamboat. Nothing about the parts was
# wrong; the problem is that a boat is READ from its proportions, and float
# coordinates run through an auto-fit do not land where a 28-bead board needs
# them to. So the board is written out bead by bead.
#
#   K black   D hull   C deck   B water   . empty
#
# Rows 0-7 are left to _build_boat, which places the funnels: their number is
# the only thing that makes one boat structurally different from another, and
# a recolour is not a new pattern - the distinctness filter drops it, correctly.
BOAT_ART = [
    "......KKKKKKKKKKKKKKKK......",
    "......KCCCCCCCCCCCCCCK......",
    "......KCKKCCCKKCCCKKCK......",
    "......KCKKCCCKKCCCKKCK......",
    "......KCCCCCCCCCCCCCCK......",
    "...KKKKKKKKKKKKKKKKKKKKKK...",
    "..KDDDDDDDDDDDDDDDDDDDDDDK..",
    "..KDDDDDDDDDDDDDDDDDDDDDDK..",
    "..KDCCCCCCCCCCCCCCCCCCCCDK..",
    "..KDDDDDDDDDDDDDDDDDDDDDDK..",
    "..KDDDDDDDDDDDDDDDDDDDDDDK..",
    "...KDDDDDDDDDDDDDDDDDDDDK...",
    "....KKDDDDDDDDDDDDDDDDKK....",
    "......KKKKKKKKKKKKKKKK......",
    "..BBBBBBBBBBBBBBBBBBBBBBBB..",
    "..BBBBBBBBBBBBBBBBBBBBBBBB..",
]
ART_TOP = 8          # board row the art starts on

# Funnel columns per count, each block symmetric about the board's centre line.
FUNNELS = {1: [(12, 15)], 2: [(9, 11), (16, 18)], 3: [(6, 8), (12, 15), (19, 21)]}


def _build_boat(spec):
    stacks, hull_col, water_col = spec["parts"]
    g = Grid(S, S)
    g.fill(spec["bg"])
    paint = {"K": INK, "D": hull_col, "C": PALE, "B": water_col}
    for y, row in enumerate(BOAT_ART):
        for x, ch in enumerate(row):
            if ch != ".":
                g.set(x, ART_TOP + y, paint[ch])
    for x0, x1 in FUNNELS[stacks]:
        for x in range(x0, x1 + 1):
            for y in range(3, ART_TOP):
                g.set(x, y, INK)
            g.set(x, 5, PALE)                      # the funnel's band
        for x in range(x0 - 1, x1 + 2):            # steam, sitting on the rim
            g.set(x, 1, PALER)
            g.set(x, 2, PALER)
    return g


# name              stacks  hull colour   water colour
BOATS = [
    ("Willie's Steamboat", 2, DARK,         "blue"),
    ("Little Tug",         1, "dark_green", "aqua"),
    ("River Packet",       3, "dark_red",   "teal"),
]


def generate():
    specs = []
    for pose in POSES:
        for i, c in enumerate(CAST):
            name, ears, earsz, hr, muzzle, eyes, body, feet, prop = c
            if pose == "prop" and prop == "none":
                continue
            if pose == "wave" and prop != "none":
                continue          # a waving figure holding a shovel reads as neither
            title = name if pose == "bust" else f"{name} {pose.title()}"
            specs.append(dict(
                name=title, pose=pose,
                parts=(ears, earsz, hr, muzzle, eyes, body, feet, prop),
                fill=0.94 if pose != "tall" else 0.99,
                bg=_pick_bg(INK, BACKDROPS, nth=i),
                tags=["retro", "cartoon", "character"]))
    for i, o in enumerate(OBJECTS):
        specs.append(dict(name=o[0], pose="object", parts=o,
                          bg=_pick_bg(o[7][0], BACKDROPS, nth=i),
                          tags=["deck", "retro", "character"]))
    for i, (name, stacks, hull, water) in enumerate(BOATS):
        specs.append(dict(name=name, pose="boat",
                          parts=(stacks, hull, water),
                          bg=_pick_bg(hull, BACKDROPS, nth=i),
                          tags=["boat", "retro", "character"]))

    def build(spec):
        if spec["pose"] == "object":
            return _build_object(spec)
        if spec["pose"] == "boat":
            return _build_boat(spec)
        draw = _draw
        # No outline pass here. Every subject in this category is already a
        # solid black mass on a pale backdrop - the darkest thing on the board
        # by a wide margin - and outlining it only wraps it in a grey halo that
        # eats the rubber-hose limbs it is supposed to define.
        return _frame(draw, spec, spec["bg"], fill=spec["fill"])

    return _emit("characters", specs, build, target=100)


GENERATORS = {"characters": generate}
