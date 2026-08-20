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
POSES = ["bust", "full", "wave", "prop", "tall"]


def _head(g, cx, cy, r, spec):
    """The head: ears first so the skull overlaps them, then the face patch."""
    ears, earsz, hr, muzzle, eyes = spec
    er = r * earsz
    if ears == "round":
        g.disc(cx - r * 0.78, cy - r * 0.82, er, INK)
        g.disc(cx + r * 0.78, cy - r * 0.82, er, INK)
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
        g.ellipse(cx, cy + torso_h * 0.95, u * 1.8, u * 1.15, INK)
        for s in (-1, 1):                                          # two buttons
            g.disc(cx + s * u * 0.85, cy + torso_h * 0.90, u * 0.36, PALE)
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
            g.ellipse(cx + s * u * 1.9, cy + torso_h * 2.20, u * 1.35, u * 0.72, INK)
        elif feet == "web":
            g.ellipse(cx + s * u * 1.6, cy + torso_h * 2.15, u * 1.05, u * 0.55, "orange")
        else:
            g.ellipse(cx + s * u * 1.5, cy + torso_h * 2.15, u * 0.95, u * 0.60, INK)


def _prop(g, cx, cy, u, prop):
    """The thing that names the pose - a wheel, a whistle, a shovel."""
    if prop == "wheel":
        import math
        g.ring(cx, cy, u * 3.4, DARK, t=u * 0.55)
        g.disc(cx, cy, u * 0.9, DARK)
        for k in range(8):
            a = k * math.pi / 4
            # Spokes stop at the rim; handles carry on past it. Running one
            # stroke from hub to handle tip fills the wheel in solid at this
            # scale and the whole thing reads as a dark disc.
            g.limb(cx + math.cos(a) * u * 1.0, cy + math.sin(a) * u * 1.0,
                   cx + math.cos(a) * u * 3.0, cy + math.sin(a) * u * 3.0,
                   DARK, width=1)
            g.limb(cx + math.cos(a) * u * 3.6, cy + math.sin(a) * u * 3.6,
                   cx + math.cos(a) * u * 4.4, cy + math.sin(a) * u * 4.4,
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

def _draw_boat(g, spec, cx, cy, scale):
    """The steamboat: hull, deckhouse, twin stacks, steam.

    Drawn as its own subject rather than as a prop, because at 28x28 a boat
    with a figure on it is two unreadable things instead of one readable one.
    """
    u = scale * 1.5
    stacks, deck, puffs = spec["parts"]
    hull_w = u * 8.5
    g.poly([(cx - hull_w, cy + u * 2.0), (cx + hull_w, cy + u * 2.0),
            (cx + hull_w * 0.78, cy + u * 5.0), (cx - hull_w * 0.78, cy + u * 5.0)], PALE)
    g.rect(cx - hull_w, cy + u * 2.0, cx + hull_w, cy + u * 2.9, INK)
    if deck >= 1:
        g.rect(cx - hull_w * 0.62, cy - u * 1.6, cx + hull_w * 0.62, cy + u * 2.0, PALE)
        for k in range(-2, 3):                                    # portholes
            g.disc(cx + k * u * 2.0, cy + u * 0.3, u * 0.62, INK)
    if deck >= 2:
        g.rect(cx - hull_w * 0.34, cy - u * 4.2, cx + hull_w * 0.34, cy - u * 1.6, PALE)
    for k in range(stacks):
        sx = cx + (k - (stacks - 1) / 2.0) * u * 2.8
        g.rect(sx - u * 0.9, cy - u * 8.2, sx + u * 0.9, cy - u * 4.2, INK)
        g.rect(sx - u * 0.9, cy - u * 7.2, sx + u * 0.9, cy - u * 6.4, PALE)
    for k in range(puffs):
        g.disc(cx - u * 3.0 + k * u * 2.6, cy - u * (10.0 + (k % 2) * 1.2),
               u * (1.6 - k * 0.18), PALER)
    g.rect(cx - hull_w * 1.25, cy + u * 5.0, cx + hull_w * 1.25, cy + u * 6.4, "blue")


BOATS = [
    ("Willie's Steamboat", 2, 2, 3),
    ("Riverboat", 3, 2, 4),
    ("Little Tug", 1, 1, 2),
    ("Paddle Steamer", 2, 1, 3),
    ("Ferry", 1, 2, 2),
    ("Packet Boat", 3, 1, 4),
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
    for i, (name, stacks, deck, puffs) in enumerate(BOATS):
        for j, (suffix, fill) in enumerate((("", 0.96), (" Small", 0.74))):
            specs.append(dict(
                name=name + suffix, pose="boat",
                parts=(stacks, deck, puffs), fill=fill,
                bg=_pick_bg(INK, BACKDROPS, nth=i + j),
                tags=["boat", "retro", "character"]))

    def build(spec):
        draw = _draw_boat if spec["pose"] == "boat" else _draw
        # No outline pass here. Every subject in this category is already a
        # solid black mass on a pale backdrop - the darkest thing on the board
        # by a wide margin - and outlining it only wraps it in a grey halo that
        # eats the rubber-hose limbs it is supposed to define.
        return _frame(draw, spec, spec["bg"], fill=spec["fill"])

    return _emit("characters", specs, build, target=100)


GENERATORS = {"characters": generate}
