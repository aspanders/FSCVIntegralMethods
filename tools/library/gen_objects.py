"""Structurally-unique generators for the object categories.

Same principle as gen_creatures: an item's identity lives in its PARTS and
their proportions, so a spec of a few numbers spans a real range of objects
instead of one drawing in different colours. The categories replaced here were
the library's most repetitive - sports shipped 85 byte-identical boards out of
100, food 80.

Shares _frame / _pick_bg / _outline with gen_creatures so every category gets
the same treatment: draw roomy, scale up to fill the board, centre the ink,
contrast the background against the subject, and give the subject an edge.
"""
import math

from beadlib import make_pattern, stable_id
from canvas import Grid
from gen_creatures import S, _emit, _frame, _outline, _pick_bg

PALE = ["cream", "ivory", "light_gray", "sky_blue", "toothpaste",
        "light_lavender", "banana", "peach", "light_pink", "silver"]


# ── VEHICLES ─────────────────────────────────────────────────────────────────

VEHICLES = [
    # name          plan     len  hgt  cab   wheels wsize extra
    ("Car",         "road",  9.0, 3.4, "mid",   2,  0.95, "none"),
    # Was 10.5 x 2.6: a long flat slab with a token window on top, which is
    # the "bizarre long car" of the review. Shorter and taller reads as a car.
    ("Sports Car",  "road",  9.4, 3.2, "low",   2,  0.90, "none"),
    ("Taxi",        "road",  9.0, 3.6, "mid",   2,  0.95, "sign"),
    ("Police Car",  "road",  9.5, 3.4, "mid",   2,  0.95, "siren"),
    ("Van",         "road",  9.0, 5.0, "front", 2,  0.70, "none"),
    ("Ambulance",   "road",  9.5, 5.2, "front", 2,  0.70, "cross"),
    ("Bus",         "road", 12.0, 6.0, "none",  3,  0.55, "windows"),
    ("School Bus",  "road", 12.0, 6.2, "front", 3,  0.55, "windows"),
    ("Truck",       "road", 12.5, 4.6, "front", 4,  0.70, "box"),
    ("Pickup",      "road", 10.0, 3.4, "front", 2,  0.95, "bed"),
    ("Tanker",      "road", 12.5, 4.4, "front", 4,  0.70, "tank"),
    ("Fire Engine", "road", 12.0, 4.8, "front", 3,  0.70, "ladder"),
    ("Tractor",     "road",  8.0, 4.0, "front", 2,  1.35, "none"),
    ("Digger",      "road",  8.5, 3.8, "front", 2,  1.10, "arm"),
    ("Bulldozer",   "road",  8.5, 3.8, "front", 2,  1.10, "blade"),
    ("Monster Truck","road", 9.0, 3.6, "mid",   2,  1.55, "none"),
    ("Train",       "rail", 11.0, 5.6, "front", 4,  0.55, "funnel"),
    ("Tram",        "rail", 11.0, 6.0, "none",  4,  0.50, "pole"),
    ("Motorbike",   "two",   7.0, 2.0, "low",   2,  1.00, "none"),
    # Wheel size was 1.55, so two big thin rings dominated a hairline frame
    # and the whole thing read as a pair of spectacles. Smaller wheels and a
    # taller frame box; the stroke width is raised in _draw_vehicle too.
    ("Bicycle",     "two",   7.5, 1.6, "none",  2,  1.00, "none"),
    ("Scooter",     "two",   6.0, 1.8, "low",   2,  0.90, "none"),
    ("Boat",        "water", 10.0, 3.0, "mid",  0,  0.0, "none"),
    ("Sailboat",    "water",  9.0, 2.6, "none", 0,  0.0, "sail"),
    ("Ship",        "water", 12.0, 3.6, "front",0,  0.0, "funnel"),
    ("Submarine",   "water", 11.0, 5.0, "none", 0,  0.0, "periscope"),
    ("Plane",       "air",  11.0, 3.6, "none",  0,  0.0, "wings"),
    ("Helicopter",  "air",   7.0, 3.4, "mid",   0,  0.0, "rotor"),
    ("Rocket",      "air",   3.2,11.0, "none",  0,  0.0, "fins"),
    ("Balloon",     "air",   6.0, 7.0, "none",  0,  0.0, "basket"),
]

VEH_COLOURS = [
    ("red", "sky_blue", "black"), ("blue", "aqua", "dark_gray"),
    ("yellow", "sky_blue", "black"), ("green", "toothpaste", "dark_gray"),
    ("orange", "banana", "dark_brown"), ("purple", "lavender", "black"),
    ("teal", "toothpaste", "navy"), ("magenta", "light_pink", "dark_gray"),
    ("navy", "sky_blue", "black"), ("dark_red", "peach", "black"),
]


# A taxi is yellow, a fire engine is red, an ambulance is white with a red
# cross. Rotating a palette across the vehicle list threw all of that away, and
# a vehicle's colour convention is doing as much identifying work as its
# silhouette.  (body, glass, trim)
VEHICLE_PALETTE = {
    "Car":           ("red", "sky_blue", "black"),
    "Sports Car":    ("yellow", "sky_blue", "black"),
    "Taxi":          ("yellow", "sky_blue", "black"),
    "Police Car":    ("white", "sky_blue", "navy"),
    "Van":           ("silver", "sky_blue", "dark_gray"),
    "Ambulance":     ("white", "sky_blue", "red"),
    "Bus":           ("red", "sky_blue", "dark_gray"),
    "School Bus":    ("yellow", "sky_blue", "black"),
    "Truck":         ("blue", "sky_blue", "dark_gray"),
    "Pickup":        ("teal", "sky_blue", "dark_gray"),
    "Tanker":        ("silver", "sky_blue", "dark_gray"),
    "Fire Engine":   ("red", "sky_blue", "silver"),
    "Tractor":       ("green", "sky_blue", "yellow"),
    "Digger":        ("yellow", "sky_blue", "dark_gray"),
    "Bulldozer":     ("orange", "sky_blue", "dark_gray"),
    "Monster Truck": ("magenta", "sky_blue", "black"),
    "Train":         ("dark_red", "banana", "black"),
    "Tram":          ("green", "sky_blue", "dark_gray"),
    "Motorbike":     ("red", "black", "silver"),
    "Bicycle":       ("teal", "black", "silver"),
    "Scooter":       ("aqua", "white", "dark_gray"),
    "Boat":          ("white", "blue", "dark_brown"),
    "Sailboat":      ("white", "sky_blue", "navy"),
    "Ship":          ("navy", "white", "dark_red"),
    "Submarine":     ("banana", "sky_blue", "dark_gray"),
    "Plane":         ("silver", "sky_blue", "navy"),
    "Helicopter":    ("navy", "sky_blue", "red"),
    "Rocket":        ("white", "red", "dark_gray"),
    "Balloon":       ("red", "banana", "dark_brown"),
}


def _draw_vehicle(g, spec, cx, cy, scale):
    plan, ln, hg, cab, nw, ws, extra = spec["parts"]
    body, glass, trim = spec["cols"]
    u = scale
    ln *= u; hg *= u
    # ws arrives as a multiplier on body height, not an absolute radius. As an
    # absolute it produced wheels bigger than the vehicle: the auto-scaler
    # fills the board, so anything sized independently of the body ends up
    # dominating it.
    wr = hg * 0.42 * ws

    if plan in ("road", "rail"):
        top = cy - hg / 2
        bot = cy + hg / 2
        g.rect(cx - ln / 2, top, cx + ln / 2, bot, body)
        if cab == "mid":
            g.poly([(cx - ln * 0.22, top), (cx - ln * 0.10, top - hg * 0.75),
                    (cx + ln * 0.16, top - hg * 0.75), (cx + ln * 0.26, top)], body)
            g.rect(cx - ln * 0.12, top - hg * 0.6, cx + ln * 0.18, top - 1, glass)
        elif cab == "front":
            g.rect(cx + ln * 0.12, top - hg * 0.7, cx + ln * 0.48, top, body)
            g.rect(cx + ln * 0.18, top - hg * 0.55, cx + ln * 0.42, top - 1, glass)
        elif cab == "low":
            # A wider, squarer greenhouse. The old triangle spanned 0.37 of the
            # body and peaked at 0.55 of its height, which on a long body is a
            # token bump - the "tiny window" of the review.
            g.poly([(cx - ln * 0.26, top), (cx - ln * 0.12, top - hg * 0.72),
                    (cx + ln * 0.16, top - hg * 0.72), (cx + ln * 0.30, top)], glass)
        for k in range(nw):
            wx = cx - ln / 2 + ln * (k + 0.5) / max(1, nw)
            g.disc(wx, bot + wr * 0.35, wr, "dark_gray")
            g.disc(wx, bot + wr * 0.35, wr * 0.42, trim)
        if extra == "windows":
            for k in range(4):
                g.rect(cx - ln * 0.42 + k * ln * 0.22, top + hg * 0.15,
                       cx - ln * 0.42 + k * ln * 0.22 + ln * 0.14, top + hg * 0.55, glass)
        elif extra == "siren":
            g.rect(cx - ln * 0.08, top - hg * 1.05, cx + ln * 0.10, top - hg * 0.78, "red")
        elif extra == "sign":
            g.rect(cx - ln * 0.06, top - hg * 1.05, cx + ln * 0.12, top - hg * 0.80, "banana")
        elif extra == "cross":
            g.rect(cx - ln * 0.30, cy - 0.6 * u, cx - ln * 0.02, cy + 0.6 * u, "red")
            g.rect(cx - ln * 0.18, cy - 2.2 * u, cx - ln * 0.14, cy + 2.2 * u, "red")
        elif extra == "box":
            g.rect(cx - ln * 0.5, top - hg * 0.9, cx + ln * 0.05, top, glass)
        elif extra == "bed":
            g.rect(cx - ln * 0.5, top - hg * 0.3, cx - ln * 0.05, top, trim)
        elif extra == "tank":
            g.ellipse(cx - ln * 0.20, top - hg * 0.35, ln * 0.30, hg * 0.62, glass)
        elif extra == "ladder":
            for k in range(6):
                g.rect(cx - ln * 0.45 + k * ln * 0.15, top - hg * 0.55,
                       cx - ln * 0.45 + k * ln * 0.15 + 0.8 * u, top - hg * 0.2, trim)
            g.rect(cx - ln * 0.48, top - hg * 0.72, cx + ln * 0.05, top - hg * 0.48, trim)
        elif extra == "arm":
            g.line(cx - ln * 0.1, top, cx - ln * 0.55, top - hg * 1.5, trim, t=1)
            g.poly([(cx - ln * 0.55, top - hg * 1.5), (cx - ln * 0.75, top - hg * 0.7),
                    (cx - ln * 0.45, top - hg * 0.8)], trim)
        elif extra == "blade":
            g.rect(cx - ln * 0.72, cy - hg * 0.2, cx - ln * 0.52, bot + wr * 0.6, trim)
        elif extra == "funnel":
            g.rect(cx + ln * 0.02, top - hg * 1.1, cx + ln * 0.16, top, trim)
        elif extra == "pole":
            g.limb(cx, top, cx, top - hg * 1.3, trim)
            g.limb(cx, top - hg * 1.3, cx + ln * 0.3, top - hg * 1.45, trim)
        if plan == "rail":
            g.rect(cx - ln * 0.62, bot + wr * 1.5, cx + ln * 0.62, bot + wr * 2.0, trim)
    elif plan == "two":
        bot = cy + hg
        wr = max(2.0 * u, hg * 1.6 * ws)
        for sgn in (-1, 1):
            g.ring(cx + sgn * ln * 0.36, bot, wr, "dark_gray", t=1.2 * u)
        # Frame strokes have to be thick enough to survive at bead scale, or a
        # bike is two wheels with a smudge between them.
        # HAIRLINE. tk was 1.1*u, about two beads, inside a frame only six
        # beads tall - so the tubes merged and the whole triangle filled solid.
        # That is the blob between two rings that read as spectacles. A bicycle
        # frame is one bead wide at this scale, and has to be.
        tk = 0
        top = bot - wr * 1.5
        g.line(cx - ln * 0.36, bot, cx - ln * 0.06, top, body, t=tk)
        g.line(cx - ln * 0.06, top, cx + ln * 0.36, bot, body, t=tk)
        g.line(cx - ln * 0.36, bot, cx + ln * 0.36, bot, body, t=tk)
        g.line(cx - ln * 0.06, top, cx + ln * 0.30, top, body, t=tk)
        g.rect(cx - ln * 0.22, top - 2.2 * u, cx + ln * 0.02, top - 0.6 * u, trim)   # seat
        g.line(cx + ln * 0.30, top, cx + ln * 0.36, bot, trim, t=tk)                 # forks
        g.line(cx + ln * 0.20, top - 2.6 * u, cx + ln * 0.46, top - 2.6 * u, trim, t=tk)
        g.line(cx + ln * 0.30, top - 2.6 * u, cx + ln * 0.30, top, trim, t=tk)
    elif plan == "water":
        if extra != "periscope":
            g.poly([(cx - ln / 2, cy - hg / 2), (cx + ln / 2, cy - hg / 2),
                    (cx + ln * 0.34, cy + hg / 2), (cx - ln * 0.34, cy + hg / 2)], body)
        if cab in ("mid", "front"):
            off = 0 if cab == "mid" else ln * 0.2
            g.rect(cx - ln * 0.16 + off, cy - hg * 1.3, cx + ln * 0.14 + off, cy - hg / 2, glass)
        if extra == "sail":
            g.limb(cx, cy - hg / 2, cx, cy - hg / 2 - 11 * u, trim)
            g.poly([(cx + 0.6 * u, cy - hg / 2 - 11 * u), (cx + 6.5 * u, cy - hg / 2 - 1),
                    (cx + 0.6 * u, cy - hg / 2 - 1)], glass)
            g.poly([(cx - 0.6 * u, cy - hg / 2 - 10 * u), (cx - 4.5 * u, cy - hg / 2 - 1),
                    (cx - 0.6 * u, cy - hg / 2 - 1)], trim)
        elif extra == "funnel":
            g.rect(cx - 1.2 * u, cy - hg * 1.9, cx + 1.2 * u, cy - hg * 1.2, trim)
        elif extra == "periscope":
            # A submarine is a capsule, not a boat hull with a stick on top.
            g.ellipse(cx, cy, ln / 2, hg / 2, body)
            g.rect(cx - ln * 0.14, cy - hg * 1.05, cx + ln * 0.10, cy, body)
            g.rect(cx - 0.9 * u, cy - hg * 1.75, cx + 0.9 * u, cy - hg * 0.9, trim)
            g.rect(cx - 0.9 * u, cy - hg * 1.95, cx + 3.2 * u, cy - hg * 1.55, trim)
            for k in (-0.26, -0.02, 0.22):
                g.disc(cx + ln * k, cy + hg * 0.05, 1.5 * u, glass)
            g.poly([(cx - ln * 0.48, cy - hg * 0.1), (cx - ln * 0.66, cy - hg * 0.7),
                    (cx - ln * 0.66, cy + hg * 0.7), (cx - ln * 0.48, cy + hg * 0.1)], trim)
    else:   # air
        if extra == "wings":
            # Top-down. A side-on airliner at 28 beads is a sliver with two
            # slivers crossing it; from above the silhouette is unmistakable.
            fl = ln * 1.5          # fuselage length runs vertically here
            fw = hg * 0.62
            g.poly([(cx - fw * 0.9, cy - fl * 0.02), (cx - fl * 0.62, cy + fl * 0.30),
                    (cx - fl * 0.62, cy + fl * 0.44), (cx - fw * 0.9, cy + fl * 0.22)], glass)
            g.poly([(cx + fw * 0.9, cy - fl * 0.02), (cx + fl * 0.62, cy + fl * 0.30),
                    (cx + fl * 0.62, cy + fl * 0.44), (cx + fw * 0.9, cy + fl * 0.22)], glass)
            g.poly([(cx - fw * 0.8, cy + fl * 0.30), (cx - fl * 0.26, cy + fl * 0.46),
                    (cx - fl * 0.26, cy + fl * 0.54), (cx - fw * 0.8, cy + fl * 0.44)], trim)
            g.poly([(cx + fw * 0.8, cy + fl * 0.30), (cx + fl * 0.26, cy + fl * 0.46),
                    (cx + fl * 0.26, cy + fl * 0.54), (cx + fw * 0.8, cy + fl * 0.44)], trim)
            g.ellipse(cx, cy + fl * 0.06, fw, fl * 0.52, body)
            g.disc(cx, cy - fl * 0.40, fw * 0.85, glass)
            for sgn in (-1, 1):
                g.disc(cx + sgn * fl * 0.30, cy + fl * 0.26, fw * 0.45, trim)
        elif extra == "rotor":
            g.ellipse(cx, cy, ln / 2, hg / 2, body)
            g.poly([(cx - ln * 0.4, cy), (cx - ln * 1.05, cy - hg * 0.25),
                    (cx - ln * 1.05, cy + hg * 0.1), (cx - ln * 0.4, cy + hg * 0.3)], body)
            g.rect(cx - ln * 1.15, cy - hg * 0.75, cx - ln * 0.95, cy + hg * 0.1, trim)
            g.rect(cx - ln * 0.75, cy - hg * 1.35, cx + ln * 0.75, cy - hg * 1.15, trim)
            g.rect(cx - 0.6 * u, cy - hg * 1.3, cx + 0.6 * u, cy - hg / 2, trim)
            g.disc(cx + ln * 0.18, cy - hg * 0.1, 2.2 * u, glass)
            g.rect(cx - ln * 0.3, cy + hg * 0.75, cx + ln * 0.35, cy + hg * 0.95, trim)
        elif extra == "fins":
            g.poly([(cx, cy - hg / 2), (cx + ln, cy - hg * 0.12),
                    (cx - ln, cy - hg * 0.12)], body)
            g.rect(cx - ln, cy - hg * 0.12, cx + ln, cy + hg * 0.36, body)
            g.disc(cx, cy - hg * 0.02, ln * 0.62, glass)
            for sgn in (-1, 1):
                g.poly([(cx + sgn * ln, cy + hg * 0.10), (cx + sgn * ln * 2.1, cy + hg * 0.45),
                        (cx + sgn * ln, cy + hg * 0.45)], trim)
            g.poly([(cx - ln * 0.7, cy + hg * 0.36), (cx, cy + hg * 0.62),
                    (cx + ln * 0.7, cy + hg * 0.36)], trim)
        elif extra == "basket":
            # A hot air balloon is a teardrop: round and wide at the crown,
            # pinched to a neck above the basket. Drawn as a plain ellipse it
            # is a ball on strings, which is what "deflated" was describing.
            crown = ln * 0.66
            g.disc(cx, cy - hg * 0.62, crown, body)
            g.poly([(cx - crown, cy - hg * 0.62), (cx + crown, cy - hg * 0.62),
                    (cx + ln * 0.24, cy + hg * 0.30),
                    (cx - ln * 0.24, cy + hg * 0.30)], body)
            for k in (-0.5, 0.0, 0.5):
                g.limb(cx + ln * k * 0.9, cy - hg * 0.6, cx + ln * k * 0.35, cy + hg * 0.36, glass)
            g.limb(cx - ln * 0.2, cy + hg * 0.36, cx - ln * 0.2, cy + hg * 0.62, trim)
            g.limb(cx + ln * 0.2, cy + hg * 0.36, cx + ln * 0.2, cy + hg * 0.62, trim)
            g.rect(cx - ln * 0.26, cy + hg * 0.62, cx + ln * 0.26, cy + hg * 0.95, trim)

    _outline(g, "black" if body != "black" else "dark_gray", None)


def vehicles():
    specs = []
    # " Compact" shrank the whole vehicle to 0.72 of the board, which the size
    # boards now do properly; " Tall" scaled the body height by 1.7 and turned
    # a taxi into a tower and a motorbike into a pink smear. What is left
    # changes the vehicle without breaking it, plus a line drawing.
    poses = [("", 0.96, {}), (" Long", 0.96, {"len": 1.30}),
             (" Big Wheels", 0.96, {"ws": 1.55}),
             (" Outline", 0.96, {"line": True})]
    for pi, (suffix, sc, tw) in enumerate(poses):
        for si, (name, plan, ln, hg, cab, nw, ws, extra) in enumerate(VEHICLES):
            specs.append(dict(
                name=f"{name}{suffix}",
                parts=(plan, ln * tw.get("len", 1.0), hg * tw.get("hgt", 1.0),
                       cab, nw, ws * tw.get("ws", 1.0), extra),
                cols=VEHICLE_PALETTE.get(
                    name, VEH_COLOURS[(si * 3 + pi) % len(VEH_COLOURS)]),
                bg=_pick_bg(VEHICLE_PALETTE.get(
                    name, VEH_COLOURS[(si * 3 + pi) % len(VEH_COLOURS)])[0],
                    PALE, si + pi),
                tags=["vehicle", name.lower()], fill=sc, scale=1.0,
                line=tw.get("line", False)))

    def build(sp):
        out = _frame(lambda g, s, x, y, k: _draw_vehicle(g, s, x, y, k),
                     sp, sp["bg"], fill=sp["fill"])
        if sp.get("line"):
            _hollow(out, sp["bg"])
        return out
    return _emit("vehicles", specs, build, 100)


GENERATORS = {"vehicles": vehicles}


# ── FLOWERS ──────────────────────────────────────────────────────────────────

FLOWERS = [
    # name          petals shape     layers centre stem leaves base
    ("Daisy",         12, "oval",    1, 0.34, 0, 0, "none"),
    ("Sunflower",     16, "point",   2, 0.46, 0, 0, "none"),
    ("Rose",           0, "spiral",  4, 0.00, 0, 0, "none"),
    ("Tulip",          3, "cup",     1, 0.00, 1, 2, "none"),
    ("Lily",           6, "point",   1, 0.22, 0, 0, "none"),
    ("Lotus",         10, "point",   2, 0.26, 0, 0, "pad"),
    ("Poppy",          5, "round",   1, 0.34, 0, 0, "none"),
    ("Cherry Blossom", 5, "notch",   1, 0.24, 0, 0, "twig"),
    ("Orchid",         5, "spoon",   1, 0.28, 0, 0, "none"),
    ("Iris",           6, "droop",   2, 0.18, 0, 0, "none"),
    ("Daffodil",       6, "oval",    1, 0.40, 0, 0, "trumpet"),
    ("Hyacinth",       0, "spike",   6, 0.00, 1, 2, "none"),
    ("Carnation",     14, "frill",   3, 0.16, 0, 0, "none"),
    ("Pansy",          5, "round",   1, 0.22, 0, 0, "face"),
    ("Bluebell",       0, "bell",    3, 0.00, 1, 1, "none"),
    ("Thistle",        0, "tuft",    1, 0.30, 1, 2, "none"),
    ("Dandelion",     24, "needle",  1, 0.24, 0, 0, "none"),
    ("Hibiscus",       5, "wide",    1, 0.18, 0, 0, "stamen"),
    ("Marigold",      18, "oval",    3, 0.22, 0, 0, "none"),
    ("Chrysanthemum", 22, "needle",  3, 0.18, 0, 0, "none"),
    ("Bouquet",        8, "oval",    1, 0.30, 3, 2, "wrap"),
    ("Potted Plant",   6, "round",   1, 0.28, 1, 3, "pot"),
    ("Water Lily",     8, "spoon",   2, 0.30, 0, 0, "pad"),
    ("Peony",         20, "frill",   4, 0.14, 0, 0, "none"),
    ("Zinnia",        16, "point",   2, 0.28, 0, 0, "none"),
    ("Aster",         26, "needle",  2, 0.20, 0, 0, "none"),
    ("Buttercup",      5, "round",   1, 0.30, 0, 0, "none"),
    ("Snowdrop",       0, "bell",    2, 0.00, 1, 1, "none"),
    ("Foxglove",       0, "bell",    5, 0.00, 1, 2, "none"),
    ("Lavender",       0, "spike",   8, 0.00, 1, 2, "none"),
    ("Clover",         3, "notch",   1, 0.18, 1, 1, "none"),
    ("Camellia",      12, "oval",    4, 0.12, 0, 0, "none"),
]

FLOWER_COLOURS = [
    ("red", "yellow", "dark_green"), ("hot_pink", "banana", "green"),
    ("purple", "lemon", "dark_green"), ("orange", "dark_red", "forest"),
    ("white", "yellow", "green"), ("magenta", "cream", "dark_green"),
    ("blue", "banana", "forest"), ("yellow", "dark_brown", "green"),
    ("light_pink", "cheddar", "green"), ("lavender", "banana", "dark_green"),
]


# Colour belongs to the SPECIES, exactly as it does for food and for the
# creature categories. Rotating a palette across the flower list produced a
# blue sunflower, a red clover and a cream orchid on a cream board - and a
# sunflower that is not yellow with a dark middle is not a sunflower, however
# good its petals are.  (petals, centre / secondary, foliage)
FLOWER_PALETTE = {
    "Daisy":          ("white", "yellow", "green"),
    "Sunflower":      ("yellow", "dark_brown", "green"),
    "Rose":           ("red", "dark_red", "dark_green"),
    "Tulip":          ("red", "banana", "green"),
    "Lily":           ("white", "orange", "green"),
    "Lotus":          ("light_pink", "banana", "dark_green"),
    "Poppy":          ("red", "black", "green"),
    "Cherry Blossom": ("light_pink", "blush", "dark_brown"),
    "Orchid":         ("magenta", "banana", "green"),
    "Iris":           ("purple", "banana", "green"),
    "Daffodil":       ("banana", "orange", "green"),
    "Hyacinth":       ("purple", "lavender", "green"),
    "Carnation":      ("hot_pink", "light_pink", "green"),
    "Pansy":          ("purple", "banana", "green"),
    "Bluebell":       ("blue", "sky_blue", "green"),
    "Thistle":        ("purple", "lavender", "dark_green"),
    "Dandelion":      ("banana", "yellow", "green"),
    "Hibiscus":       ("red", "banana", "dark_green"),
    "Marigold":       ("orange", "banana", "green"),
    "Chrysanthemum":  ("banana", "orange", "green"),
    "Bouquet":        ("magenta", "banana", "green"),
    "Potted Plant":   ("green", "light_green", "dark_green"),
    "Water Lily":     ("light_pink", "banana", "dark_green"),
    "Peony":          ("light_pink", "hot_pink", "dark_green"),
    "Zinnia":         ("hot_pink", "banana", "green"),
    "Aster":          ("purple", "banana", "green"),
    "Buttercup":      ("yellow", "banana", "green"),
    "Snowdrop":       ("white", "light_green", "green"),
    "Foxglove":       ("light_pink", "magenta", "dark_green"),
    "Lavender":       ("lavender", "purple", "dark_green"),
    "Clover":         ("light_green", "white", "dark_green"),
    "Camellia":       ("red", "light_pink", "dark_green"),
}


def _petal(g, cx, cy, a, r, w, shape, col):
    px, py = cx + math.cos(a) * r, cy + math.sin(a) * r
    if shape in ("oval", "wide", "frill"):
        g.ellipse(px, py, w * (1.4 if shape == "wide" else 1.0), w, col)
    elif shape == "round":
        g.disc(px, py, w, col)
    elif shape in ("point", "needle"):
        tip = (cx + math.cos(a) * (r + w * 1.7), cy + math.sin(a) * (r + w * 1.7))
        g.poly([(cx + math.cos(a + 0.5) * r * 0.6, cy + math.sin(a + 0.5) * r * 0.6),
                tip,
                (cx + math.cos(a - 0.5) * r * 0.6, cy + math.sin(a - 0.5) * r * 0.6)], col)
    elif shape == "spoon":
        g.ellipse(px, py, w * 0.7, w * 1.5, col)
    elif shape == "notch":
        g.disc(px, py, w, col)
        g.disc(px + math.cos(a) * w * 0.9, py + math.sin(a) * w * 0.9, w * 0.42, None)
    elif shape == "droop":
        g.ellipse(px, py + w * 0.6, w * 0.8, w * 1.3, col)
    elif shape == "cup":
        g.poly([(px - w * 1.5, py + w * 1.6), (px - w * 1.7, py - w * 1.2),
                (px, py - w * 2.2), (px + w * 1.7, py - w * 1.2),
                (px + w * 1.5, py + w * 1.6)], col)


def _draw_flower(g, spec, cx, cy, scale):
    petals, shape, layers, centre, stem, leaves, base = spec["parts"]
    petal, mid, green = spec["cols"]
    u = scale
    head_y = cy - (4 * u if stem else 0)
    R = (6.0 if stem else 8.5) * u

    # A bloom drawn on its own, seen from directly above, is a rosette - and a
    # rosette on a 28x28 board is a mandala. The stem and the pair of leaves
    # are what say "flower" before the petal shape says which flower, so every
    # species that does not sit in a pot or on a lily pad gets them.
    if stem:
        for k in range(stem):
            sx = cx + (k - (stem - 1) / 2) * 4 * u
            g.limb(sx, head_y + 2 * u, cx, cy + 12 * u, green,
                   width=max(2, int(1.4 * u)))
    for k in range(leaves):
        sgn = -1 if k % 2 == 0 else 1
        g.ellipse(cx + sgn * 3.4 * u, cy + (5 + k * 2.4) * u, 3.2 * u, 1.5 * u, green)

    if shape == "spiral":
        # Overlapping petals wound inward. Concentric rings, which is what this
        # was, is a dartboard.
        g.disc(cx, head_y, R, petal)
        n = layers * 5
        for k in range(n):
            t = k / n
            rr = R * (0.92 - 0.72 * t)
            a = -math.pi / 2 + k * 2.4
            g.ellipse(cx + math.cos(a) * rr * 0.55, head_y + math.sin(a) * rr * 0.55,
                      rr * 0.62, rr * 0.52, mid if k % 2 else petal)
        g.disc(cx, head_y, R * 0.16, mid)
    elif shape == "spike":
        for k in range(layers * 2):
            yy = head_y - 5 * u + k * 2.2 * u
            g.ellipse(cx, yy, (2.2 + k * 0.35) * u, 1.4 * u, petal if k % 2 else mid)
    elif shape == "bell":
        for k in range(layers):
            sgn = -1 if k % 2 == 0 else 1
            bx = cx + sgn * 3 * u
            by = head_y - 3 * u + k * 3.2 * u
            g.limb(cx, head_y - 6 * u, bx, by, green)
            g.poly([(bx - 2.2 * u, by), (bx + 2.2 * u, by),
                    (bx + 1.4 * u, by + 3.4 * u), (bx - 1.4 * u, by + 3.4 * u)], petal)
    elif shape == "tuft":
        g.ellipse(cx, head_y + 2 * u, 3.0 * u, 2.6 * u, green)
        for k in range(11):
            a = -math.pi * 0.9 + k * math.pi * 0.8 / 10
            g.limb(cx, head_y, cx + math.cos(a) * 5 * u, head_y + math.sin(a) * 5 * u, petal)
    else:
        if shape == "cup":
            # A tulip is ONE cup sitting on the stem; three of them arranged
            # radially is a triffid.
            _petal(g, cx, head_y - R * 0.2, -math.pi / 2, 0.0, R * 0.55, "cup", petal)
            _petal(g, cx, head_y - R * 0.2, -math.pi / 2, 0.0, R * 0.30, "cup", mid)
            layers = 0
        for L in range(layers):
            rr = R * (1.0 - L * 0.26)
            # A petal is half a bloom's identity and it only reads if there is
            # BOARD between it and the next one. Twenty-six needles at 0.30 of
            # the radius overlap into a solid annulus, which is what turned
            # every daisy, marigold and camellia into a dartboard. Eight petals
            # at a third of the radius leave a gap you can see.
            n = max(3, min(8, petals - L * 2))
            w = max(1.2 * u, min(rr * 0.34, math.pi * rr / n * 0.62))
            for k in range(n):
                a = -math.pi / 2 + k * 2 * math.pi / n + L * 0.4
                _petal(g, cx, head_y, a, rr, w, shape, petal if L % 2 == 0 else mid)
    if centre > 0:
        g.disc(cx, head_y, R * centre, mid)

    if base == "pot":
        g.poly([(cx - 5 * u, cy + 8 * u), (cx + 5 * u, cy + 8 * u),
                (cx + 3.6 * u, cy + 14 * u), (cx - 3.6 * u, cy + 14 * u)], "rust")
        g.rect(cx - 5.6 * u, cy + 7 * u, cx + 5.6 * u, cy + 9 * u, "rust")
    elif base == "pad":
        g.ellipse(cx, cy + 9 * u, 9 * u, 2.4 * u, green)
    elif base == "twig":
        g.line(cx - 9 * u, cy + 9 * u, cx + 9 * u, cy + 5 * u, "dark_brown", t=max(1, 0.8 * u))
    elif base == "wrap":
        g.poly([(cx - 5 * u, cy + 4 * u), (cx + 5 * u, cy + 4 * u),
                (cx + 2.6 * u, cy + 13 * u), (cx - 2.6 * u, cy + 13 * u)], mid)
    elif base == "trumpet":
        g.disc(cx, head_y, R * 0.42, mid)
        g.ring(cx, head_y, R * 0.42, petal, t=1.1 * u)
    elif base == "stamen":
        for k in range(4):
            g.limb(cx, head_y, cx + (k - 1.5) * 1.6 * u, head_y - 5.5 * u, mid)
    elif base == "face":
        g.ellipse(cx, head_y + 1.4 * u, R * 0.34, R * 0.26, mid)

    # No outline. Outlining a ring of petals draws a dark edge round the whole
    # ring - petals and the gaps between them alike - and the bloom comes back
    # as a wheel. The petal colour is chosen to contrast with the backdrop, so
    # the silhouette holds on its own.


def flowers():
    specs = []
    poses = [("", 0.96, {}),
             (" Double", 0.96, {"layers": +2}), (" Simple", 0.96, {"layers": -1}),
             (" Tall", 0.96, {"stem": 1, "leaves": 3}),
             (" Spray", 0.96, {"stem": 3, "leaves": 2})]
    for pi, (suffix, sc, tw) in enumerate(poses):
        for si, (name, pet, shape, lay, ctr, stem, lv, base) in enumerate(FLOWERS):
            specs.append(dict(
                name=f"{name}{suffix}",
                parts=(pet, shape, max(1, lay + tw.get("layers", 0)), ctr,
                       # A species with its own base (a pot, a lily pad, a
                       # twig) already stands on something; everything else
                       # gets a stem whether its spec asked for one or not.
                       tw.get("stem", stem if base != "none" else 1),
                       tw.get("leaves", max(2, lv)), base),
                cols=FLOWER_PALETTE.get(
                    name, FLOWER_COLOURS[(si * 3 + pi) % len(FLOWER_COLOURS)]),
                bg=_pick_bg(FLOWER_PALETTE.get(
                    name, FLOWER_COLOURS[(si * 3 + pi) % len(FLOWER_COLOURS)])[0],
                    PALE, si + pi),
                tags=["flower", name.lower()], fill=sc, scale=1.0))
    return _emit("flowers", specs,
                 lambda sp: _frame(lambda g, s, x, y, k: _draw_flower(g, s, x, y, k),
                                   sp, sp["bg"], fill=sp["fill"]), 100)


GENERATORS["flowers"] = flowers


# ── Shape-recipe interpreter ─────────────────────────────────────────────────
# The remaining categories are collections of distinct objects rather than one
# object with parameters, so each item is a short recipe: a list of primitives
# in a -10..10 unit box, with colours referenced by index into the item's own
# palette. Compact enough to author twenty items per category without twenty
# bespoke draw functions, explicit enough that each one is a real drawing.

def _run_ops(g, ops, cx, cy, u, cols):
    def C(i):
        return None if i is None else cols[i % len(cols)]
    for op in ops:
        k = op[0]
        if k == "d":                                     # disc x y r c
            g.disc(cx + op[1] * u, cy + op[2] * u, op[3] * u, C(op[4]))
        elif k == "e":                                   # ellipse x y rx ry c
            g.ellipse(cx + op[1] * u, cy + op[2] * u, op[3] * u, op[4] * u, C(op[5]))
        elif k == "r":                                   # rect x0 y0 x1 y1 c
            g.rect(cx + op[1] * u, cy + op[2] * u, cx + op[3] * u, cy + op[4] * u, C(op[5]))
        elif k == "p":                                   # poly [(x,y)...] c
            g.poly([(cx + px * u, cy + py * u) for px, py in op[1]], C(op[2]))
        elif k == "o":                                   # ring x y r t c
            g.ring(cx + op[1] * u, cy + op[2] * u, op[3] * u, C(op[5]), t=op[4] * u)
        elif k == "l":                                   # line x0 y0 x1 y1 t c
            g.line(cx + op[1] * u, cy + op[2] * u, cx + op[3] * u, cy + op[4] * u,
                   C(op[6]), t=op[5] * u)
        elif k == "rad":                                 # radial n r0 r1 t c
            n, r0, r1, t, c = op[1], op[2], op[3], op[4], op[5]
            for i in range(n):
                a = -math.pi / 2 + i * 2 * math.pi / n
                g.line(cx + math.cos(a) * r0 * u, cy + math.sin(a) * r0 * u,
                       cx + math.cos(a) * r1 * u, cy + math.sin(a) * r1 * u, C(c), t=t * u)
        elif k == "clip":                                # clip r  - erase outside
            # Seams drawn as rings centred outside the ball are the natural way
            # to get a curve, but they leave arc fragments beyond the ball that
            # the auto-scaler then treats as part of the subject, shrinking the
            # ball to a dot surrounded by specks.
            rr = op[1] * u
            for yy in range(g.h):
                for xx in range(g.w):
                    if g.g[yy][xx] is not None and \
                            (xx - cx) ** 2 + (yy - cy) ** 2 > rr * rr:
                        g.g[yy][xx] = None
        elif k == "ring_of":                             # ring_of n r rr c
            n, r, rr, c = op[1], op[2], op[3], op[4]
            for i in range(n):
                a = -math.pi / 2 + i * 2 * math.pi / n
                g.disc(cx + math.cos(a) * r * u, cy + math.sin(a) * r * u, rr * u, C(c))


def _recipe_category(cat, items, variants, target=100):
    """items: [(name, colours, ops)].

    Colour belongs to the ITEM here, not to the variant: an apple that is not
    red and a banana that is not yellow stop being identifiable, which is the
    whole point. Variants change shape.
    """
    specs = []
    for vi, variant in enumerate(variants):
        suffix, fill, mut, border = variant[:4]
        line = variant[4] if len(variant) > 4 else False
        for si, (name, cols, ops) in enumerate(items):
            specs.append(dict(name=f"{name}{suffix}", ops=mut(ops) if mut else ops,
                              cols=cols, fill=fill, border=border, line=line,
                              bg=_pick_bg(cols[0], PALE, si + vi),
                              tags=[cat, name.lower()]))

    def build(sp):
        def draw(g, spec, cx, cy, k):
            _run_ops(g, spec["ops"], cx, cy, k, spec["cols"])
            _outline(g, "black" if spec["cols"][0] != "black" else "dark_gray", None)
        out = _frame(draw, sp, sp["bg"], fill=sp["fill"])
        if sp.get("line") and _hollow(out, sp["bg"]) is None:
            return out
        if sp.get("border"):
            out.frame(0, 0, out.w - 1, out.h - 1, sp["cols"][1], t=1)
            out.frame(1, 1, out.w - 2, out.h - 2, sp["cols"][0], t=1)
        return out
    return _emit(cat, specs, build, target)


def _hollow(g, bg):
    """Turn a filled subject into a line drawing of itself.

    Keeps a bead only where it borders something DIFFERENT - the background, or
    another colour - so the silhouette and the internal boundaries survive and
    the flat fills drop out. This is what replaced the squash variants: " Wide"
    and " Tall" scaled every y coordinate by 0.62 and 1.55, which is a change
    of shape rather than of size, and it turned a motorbike into a pink blob
    and a helicopter into nothing recognisable at all. A line drawing of a
    motorbike is still a motorbike.

    The result is one bead wide nearly everywhere, which is fine: a strand of
    beads fuses into solid material. It is a mass hanging off a mass by a
    single weld that breaks, and connectivity.thicken_necks handles that case
    downstream.
    """
    keep = [[False] * g.w for _ in range(g.h)]
    for y in range(g.h):
        for x in range(g.w):
            c = g.g[y][x]
            if c is None or c == bg:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                n = g.g[ny][nx] if g.inb(nx, ny) else None
                if n != c:
                    keep[y][x] = True
                    break
    solid = sum(1 for y in range(g.h) for x in range(g.w)
                if g.g[y][x] not in (None, bg))
    left = sum(1 for y in range(g.h) for x in range(g.w) if keep[y][x])
    # A line drawing of something that was already thin is a scribble. A bat, a
    # shuttlecock and a whistle are mostly edge to begin with, so hollowing
    # them leaves a handful of scattered beads and nothing to recognise.
    # Refuse, and the caller ships the solid board instead - which _emit then
    # drops as a duplicate of the base pattern, so the category simply has one
    # fewer variant rather than one more bad one.
    if left < 55 or left > solid * 0.75:
        return None
    for y in range(g.h):
        for x in range(g.w):
            if not keep[y][x] and g.g[y][x] not in (None, bg):
                g.g[y][x] = bg
    return g

def _squash(f):
    """Scale every y coordinate - a real change of shape, not of size."""
    def m(ops):
        out = []
        for op in ops:
            op = list(op)
            if op[0] in ("d",):
                op[2] *= f
            elif op[0] == "e":
                op[2] *= f; op[4] *= f
            elif op[0] == "r":
                op[2] *= f; op[4] *= f
            elif op[0] == "p":
                op[1] = [(x, y * f) for x, y in op[1]]
            elif op[0] in ("o",):
                op[2] *= f
            elif op[0] == "l":
                op[2] *= f; op[4] *= f
            out.append(tuple(op))
        return out
    return m


# ── FOOD ─────────────────────────────────────────────────────────────────────

FOOD_ITEMS = [
    ("Apple", ("red", "dark_green", "dark_brown", "blush"), [
        ("d", -2.2, 1, 5.4, 0), ("d", 2.2, 1, 5.4, 0), ("e", 0, 2, 6.4, 5.6, 0),
        ("r", -0.6, -8, 0.6, -4, 2), ("e", 3, -6.5, 3.2, 1.6, 1),
        ("e", -2.6, -1, 1.4, 2.2, 3)]),
    ("Pear", ("light_green", "dark_green", "dark_brown", "banana"), [
        ("e", 0, 4, 5.6, 5.0, 0), ("e", 0, -3, 3.6, 4.2, 0),
        ("r", -0.6, -9, 0.6, -6, 2), ("e", 2.6, -7.5, 2.8, 1.4, 1),
        ("e", -2.2, 3, 1.4, 2.0, 3)]),
    ("Banana", ("yellow", "dark_brown", "cheddar", "cream"), [
        # Fatter. The old crescent was about two beads thick at its widest, so
        # it read as a thin sad line rather than as fruit - the outer and inner
        # arcs were nearly on top of each other.
        ("p", [(-8.4, -3.0), (-5.4, 5.2), (2.0, 8.8), (9.0, 3.4), (7.2, 0.2),
               (2.0, 4.6), (-3.0, 2.0), (-5.4, -3.4)], 0),
        ("r", -9.0, -4.6, -6.6, -2.2, 1), ("l", 8.2, 3.2, 9.4, 1.4, 1.0, 1)]),
    ("Orange", ("orange", "cheddar", "dark_green", "cream"), [
        ("d", 0, 1, 7.6, 0), ("rad", 8, 1.2, 7.0, 0.6, 3),
        ("d", 0, 1, 1.4, 1), ("e", 2.4, -7, 3.0, 1.4, 2)]),
    ("Strawberry", ("red", "dark_green", "banana", "blush"), [
        ("p", [(-6.4, -2), (6.4, -2), (0, 8.6)], 0), ("e", 0, -2.4, 6.4, 3.4, 0),
        ("ring_of", 5, 3.6, 0.8, 2), ("d", 0, 1.2, 0.8, 2),
        ("p", [(-5, -3.4), (5, -3.4), (0, -8)], 1)]),
    ("Watermelon", ("red", "dark_green", "light_green", "black"), [
        ("p", [(-9, 5), (9, 5), (0, -8)], 1), ("p", [(-7.6, 4), (7.6, 4), (0, -6)], 2),
        ("p", [(-6.6, 3.2), (6.6, 3.2), (0, -5)], 0),
        ("d", -2.6, 0.6, 0.9, 3), ("d", 2.6, 0.6, 0.9, 3), ("d", 0, -2.2, 0.9, 3)]),
    ("Grapes", ("purple", "dark_green", "lavender", "dark_brown"), [
        ("ring_of", 6, 4.4, 2.4, 0), ("d", 0, 1.5, 2.4, 0), ("d", 0, 6.4, 2.4, 0),
        ("d", -2.6, -3.6, 2.4, 0), ("d", 2.6, -3.6, 2.4, 0),
        ("r", -0.6, -9.5, 0.6, -6.5, 3), ("e", 3, -8.5, 2.8, 1.4, 1)]),
    ("Cherry", ("dark_red", "dark_green", "red", "dark_brown"), [
        ("d", -3.6, 4, 4.0, 0), ("d", 3.6, 4, 4.0, 2),
        ("l", -3.6, 1, -0.5, -8, 0.7, 1), ("l", 3.6, 1, 0.5, -8, 0.7, 1),
        ("e", 3.4, -8.6, 3.2, 1.5, 1)]),
    ("Lemon", ("yellow", "cheddar", "dark_green", "cream"), [
        ("e", 0, 0, 7.6, 5.0, 0), ("p", [(-9.4, 0), (-7, -1.6), (-7, 1.6)], 0),
        ("p", [(9.4, 0), (7, -1.6), (7, 1.6)], 0), ("e", -2.6, -2, 2.6, 1.4, 1)]),
    ("Pineapple", ("cheddar", "dark_green", "orange", "banana"), [
        ("e", 0, 3.5, 5.6, 6.0, 0),
        ("p", [(-1.6, -2), (1.6, -2), (0, -10)], 1),
        ("p", [(-1.6, -2), (-4.6, -3), (-2.6, -8)], 1),
        ("p", [(1.6, -2), (4.6, -3), (2.6, -8)], 1),
        ("p", [(-1.6, -2), (-6.4, -1), (-4.2, -5.4)], 1),
        ("p", [(1.6, -2), (6.4, -1), (4.2, -5.4)], 1),
        ("l", -5, 0, 5, 7.5, 0.5, 2), ("l", -5, 7.5, 5, 0, 0.5, 2),
        ("l", -5, 3.5, 5, 3.5, 0.5, 2)]),
    ("Carrot", ("orange", "dark_green", "cheddar", "green"), [
        ("p", [(-4.0, -3), (4.0, -3), (0, 9.5)], 0),
        ("p", [(-1.2, -3), (1.2, -3), (0, -10)], 1),
        ("p", [(-1.2, -3), (-5.0, -8.6), (-1.0, -5.4)], 1),
        ("p", [(1.2, -3), (5.0, -8.6), (1.0, -5.4)], 1),
        ("l", -2.8, 0, 2.8, 0.6, 0.6, 2), ("l", -1.8, 3.4, 1.8, 3.8, 0.6, 2)]),
    ("Broccoli", ("dark_green", "green", "light_green", "olive"), [
        ("r", -1.8, 1, 1.8, 9, 3), ("d", 0, -3, 5.2, 0), ("d", -4.6, -1, 3.6, 1),
        ("d", 4.6, -1, 3.6, 1), ("d", -2.2, -6.4, 3.0, 2), ("d", 2.6, -6, 3.0, 2)]),
    ("Corn", ("banana", "dark_green", "cheddar", "green"), [
        ("e", 0, 0, 4.2, 8.4, 0), ("l", -3, -6, -3, 6, 0.5, 2),
        ("l", 0, -7, 0, 7, 0.5, 2), ("l", 3, -6, 3, 6, 0.5, 2),
        ("p", [(-4, 6), (-8.6, 0), (-4.6, -3)], 1), ("p", [(4, 6), (8.6, 0), (4.6, -3)], 1)]),
    ("Tomato", ("red", "dark_green", "green", "blush"), [
        ("d", 0, 1.5, 7.2, 0), ("rad", 5, 0, 5.2, 1.2, 1),
        ("r", -0.6, -8.5, 0.6, -5.5, 2), ("e", -2.6, -1.5, 1.6, 2.2, 3)]),
    ("Pepper", ("green", "dark_green", "olive", "light_green"), [
        ("e", -3.4, 2, 4.0, 6.4, 0), ("e", 3.4, 2, 4.0, 6.4, 0),
        ("e", 0, 2.6, 4.0, 6.0, 0),
        ("r", -0.8, -9.5, 0.8, -5.5, 1), ("e", 0, -5.5, 4.6, 1.8, 1)]),
    ("Mushroom", ("red", "cream", "white", "dark_gray"), [
        ("p", [(-8.6, 0), (8.6, 0), (6, -5), (-6, -5)], 0), ("e", 0, 0, 8.6, 5.6, 0),
        ("d", -4, -1.6, 1.6, 2), ("d", 3.4, -2.2, 1.4, 2), ("d", 0, -3.4, 1.2, 2),
        ("p", [(-3.4, 0.5), (3.4, 0.5), (2.4, 8.5), (-2.4, 8.5)], 1)]),
    ("Bread", ("caramel", "tan", "dark_brown", "cream"), [
        ("p", [(-8.6, 6), (8.6, 6), (7.6, -2), (-7.6, -2)], 0),
        ("e", -4, -2, 4.2, 4.0, 1), ("e", 0.4, -2.6, 4.2, 4.0, 1),
        ("e", 4.8, -2, 4.2, 4.0, 1), ("l", -8, 6, 8, 6, 0.6, 2)]),
    ("Cheese", ("banana", "cheddar", "cream", "orange"), [
        ("p", [(-9, 6), (9, 6), (9, -1), (-3, -6)], 0),
        ("d", 2, 2.5, 2.0, 2), ("d", -3.6, 3.6, 1.5, 2), ("d", 5.6, -0.4, 1.2, 2)]),
    ("Fried Egg", ("white", "yellow", "cream", "silver"), [
        ("e", -1, 1, 8.6, 6.4, 0), ("d", 5, -2.4, 3.4, 0), ("d", -6.4, 4, 3.0, 0),
        ("d", -0.6, 0.4, 3.6, 1)]),
    ("Pizza", ("cheddar", "red", "dark_red", "cream"), [
        ("p", [(-8.6, 7.5), (8.6, 7.5), (0, -8.5)], 0),
        ("p", [(-7.4, 6.2), (7.4, 6.2), (0, -6.5)], 1),
        ("r", -8.6, 6.4, 8.6, 8.6, 3),
        ("d", -3, 3.4, 1.6, 2), ("d", 3.2, 3, 1.6, 2), ("d", 0, -1, 1.5, 2)]),
    ("Burger", ("caramel", "dark_green", "dark_brown", "red"), [
        ("p", [(-8.6, -1), (8.6, -1), (7, -7), (-7, -7)], 0), ("e", 0, -2, 8.6, 5.0, 0),
        ("r", -8.6, 0, 8.6, 2, 1), ("r", -8.2, 2, 8.2, 4.6, 2),
        ("r", -8.6, 4.6, 8.6, 6, 3),
        ("p", [(-8.4, 6), (8.4, 6), (7, 9), (-7, 9)], 0),
        ("ring_of", 5, 4.0, 0.7, 2)]),
    ("Hot Dog", ("caramel", "rust", "banana", "dark_brown"), [
        ("e", 0, 2, 9.4, 4.0, 0), ("e", 0, -1.5, 8.6, 3.0, 1),
        ("l", -6, -2.4, 6, -0.6, 0.7, 2), ("l", -6, -0.4, 6, -2.4, 0.7, 2)]),
    ("Taco", ("banana", "dark_green", "red", "cheddar"), [
        ("p", [(-9, 6), (9, 6), (7, -3), (-7, -3)], 0), ("e", 0, -3, 9, 6, 0),
        ("e", 0, -1.5, 7.4, 4.4, 1), ("d", -3.4, -2.6, 1.6, 2),
        ("d", 3, -3.2, 1.6, 2), ("e", 0, 5, 8.6, 2.6, 3)]),
    ("Sushi", ("white", "black", "red", "light_green"), [
        ("e", 0, 1, 6.6, 6.4, 0),
        ("r", -2.2, -6.4, 2.2, 8.4, 1),
        ("e", 0, -6.4, 7.6, 2.6, 2), ("e", -3.2, -6.6, 2.0, 1.0, 3)]),
    ("Fries", ("red", "banana", "cheddar", "cream"), [
        ("r", -5.4, -8, -3.4, 2, 1), ("r", -2.4, -9.5, -0.4, 2, 1),
        ("r", 0.6, -8.5, 2.6, 2, 1), ("r", 3.6, -7, 5.6, 2, 1),
        ("p", [(-7, 0), (7, 0), (5.4, 9), (-5.4, 9)], 0),
        ("r", -4, 3, 4, 6, 3)]),
    ("Avocado", ("dark_green", "light_green", "caramel", "green"), [
        ("e", 0, 1, 6.6, 8.4, 0), ("e", 0, 1, 5.2, 7.0, 1), ("d", 0, 3, 3.0, 2)]),
    ("Ice Lolly", ("hot_pink", "cream", "light_pink", "dark_brown"), [
        ("p", [(-4.6, -8), (4.6, -8), (4.6, 4), (0, 7), (-4.6, 4)], 0),
        ("r", -4.6, -5, 4.6, -3, 2), ("r", -1.4, 7, 1.4, 10, 3)]),
    ("Cupcake", ("light_pink", "caramel", "red", "cream"), [
        ("e", 0, -3, 6.4, 4.6, 0), ("d", -3.4, -5, 3.4, 0), ("d", 3.4, -5, 3.4, 0),
        ("d", 0, -7, 3.4, 0),
        ("p", [(-6.4, -1), (6.4, -1), (4.4, 8.5), (-4.4, 8.5)], 1),
        ("l", -4.6, 0, -3, 8, 0.6, 3), ("l", 0, 0, 0, 8, 0.6, 3),
        ("l", 4.6, 0, 3, 8, 0.6, 3), ("d", 0, -9.4, 1.4, 2)]),
]


def food():
    return _recipe_category("food", FOOD_ITEMS, [
        ("", 0.96, None, False),
        (" Outline", 0.96, None, False, True),
        (" Framed", 0.80, None, True)])


GENERATORS["food"] = food


# ── SWEETS ───────────────────────────────────────────────────────────────────

SWEET_ITEMS = [
    ("Lollipop", ("hot_pink", "white", "cream", "light_pink"), [
        ("d", 0, -3, 7.0, 0), ("o", 0, -3, 5.0, 1.2, 1), ("o", 0, -3, 2.4, 1.2, 1),
        ("r", -1.0, 3, 1.0, 10, 2)]),
    ("Swirl Pop", ("red", "white", "cream", "banana"), [
        ("d", 0, -3, 7.0, 1), ("rad", 6, 0, 7.0, 1.5, 0),
        ("r", -1.0, 3, 1.0, 10, 2)]),
    ("Wrapped Candy", ("magenta", "light_pink", "cream", "white"), [
        ("e", 0, 0, 5.4, 4.6, 0), ("p", [(-5, 0), (-10, -4), (-10, 4)], 1),
        ("p", [(5, 0), (10, -4), (10, 4)], 1), ("e", -1.6, -1.4, 1.8, 1.4, 2)]),
    ("Gumball", ("blue", "white", "aqua", "cream"), [
        ("d", 0, 0, 8.4, 0), ("d", -3, -3.4, 2.4, 1), ("d", 3.4, 3, 1.4, 2)]),
    ("Jelly Bean", ("green", "light_green", "cream", "banana"), [
        ("e", 0, 0, 8.0, 5.2, 0), ("e", -3, -1.4, 2.6, 1.6, 1)]),
    ("Chocolate Bar", ("dark_brown", "brown", "caramel", "cream"), [
        ("r", -8.4, -6, 8.4, 6, 0),
        ("l", -8.4, -2, 8.4, -2, 0.5, 1), ("l", -8.4, 2, 8.4, 2, 0.5, 1),
        ("l", -2.8, -6, -2.8, 6, 0.5, 1), ("l", 2.8, -6, 2.8, 6, 0.5, 1),
        ("r", -8.4, -8.4, 8.4, -6, 2)]),
    ("Truffle", ("dark_brown", "caramel", "cream", "brown"), [
        ("d", 0, 1, 7.4, 0), ("e", 0, -5.4, 8.0, 2.4, 1), ("d", -2.6, -1.4, 1.6, 2)]),
    ("Donut", ("light_pink", "banana", "hot_pink", "caramel"), [
        ("d", 0, 0, 9.0, 3), ("d", 0, 0, 7.6, 0), ("d", 0, 0, 2.6, None),
        ("d", -3.6, -3.6, 1.0, 1), ("d", 3.4, -2.6, 1.0, 2),
        ("d", 2.4, 4, 1.0, 1), ("d", -4, 3, 1.0, 2)]),
    ("Cookie", ("caramel", "dark_brown", "tan", "brown"), [
        ("d", 0, 0, 8.6, 0), ("d", -3.4, -3, 1.5, 1), ("d", 3.4, -2, 1.5, 1),
        ("d", 0, 3.4, 1.5, 1), ("d", -2, 4.4, 1.2, 1), ("d", 4, 4, 1.2, 1),
        ("d", 0, -5.4, 1.2, 1)]),
    ("Macaron", ("lavender", "cream", "purple", "white"), [
        ("e", 0, -3.4, 8.4, 3.4, 0), ("e", 0, 3.4, 8.4, 3.4, 0),
        ("r", -8.0, -1.0, 8.0, 1.0, 1)]),
    ("Cake Slice", ("light_pink", "cream", "red", "caramel"), [
        ("p", [(-8, 8), (8, 8), (8, -4), (-8, -4)], 1),
        ("r", -8, -2, 8, 0, 0), ("r", -8, 3, 8, 5, 0),
        ("p", [(-8, -4), (8, -4), (8, -7), (-8, -7)], 0), ("d", 0, -8.4, 2.0, 2)]),
    ("Layer Cake", ("cream", "light_pink", "red", "caramel"), [
        ("r", -9, 2, 9, 8, 0), ("r", -7.4, -3, 7.4, 2, 1), ("r", -5.6, -7, 5.6, -3, 0),
        ("r", -0.7, -10, 0.7, -7, 3), ("d", 0, -10.6, 1.2, 2)]),
    ("Ice Cream Cone", ("caramel", "light_pink", "cream", "red"), [
        ("p", [(-5.4, -1), (5.4, -1), (0, 10)], 0),
        ("l", -3.4, 1.4, 2.6, 7.4, 0.5, 3), ("l", 3.4, 1.4, -2.6, 7.4, 0.5, 3),
        ("d", 0, -4, 5.4, 1), ("d", -3.4, -6.4, 3.6, 2), ("d", 3.4, -6.4, 3.6, 1),
        ("d", 0, -9, 3.2, 2)]),
    ("Sundae", ("white", "red", "light_pink", "banana"), [
        ("p", [(-6, -2), (6, -2), (3.4, 8), (-3.4, 8)], 3),
        ("e", 0, 9, 6.4, 1.8, 3),
        ("d", 0, -4, 5.0, 0), ("d", -3.6, -5.6, 3.4, 2), ("d", 3.6, -5.6, 3.4, 0),
        ("d", 0, -8.6, 1.8, 1)]),
    ("Popsicle", ("aqua", "white", "toothpaste", "caramel"), [
        ("p", [(-5, -8), (5, -8), (5, 5), (0, 8), (-5, 5)], 0),
        ("r", -5, -4, 5, -2, 1), ("r", -1.4, 8, 1.4, 11, 3)]),
    ("Marshmallow", ("white", "light_pink", "cream", "silver"), [
        ("e", 0, -5, 6.4, 2.6, 0), ("r", -6.4, -5, 6.4, 5, 0),
        ("e", 0, 5, 6.4, 2.6, 1)]),
    ("Candy Cane", ("white", "red", "cream", "light_pink"), [
        ("l", 3, -4, 3, 10, 2.4, 0), ("l", -3, -4, 3, -4, 2.4, 0),
        ("d", -3, -1.4, 2.4, 0),
        ("l", 1.4, 2, 4.6, 1, 0.9, 1), ("l", 1.4, 6, 4.6, 5, 0.9, 1),
        ("l", -4.4, -5.4, -1.6, -6.6, 0.9, 1)]),
    ("Gingerbread", ("caramel", "white", "red", "dark_brown"), [
        ("d", 0, -6, 3.6, 0), ("r", -3.4, -3, 3.4, 4, 0),
        ("p", [(-3.4, -2), (-9, 1), (-9, 3), (-3.4, 1)], 0),
        ("p", [(3.4, -2), (9, 1), (9, 3), (3.4, 1)], 0),
        ("p", [(-3.4, 4), (-5.4, 10), (-2.4, 10), (-0.6, 4)], 0),
        ("p", [(3.4, 4), (5.4, 10), (2.4, 10), (0.6, 4)], 0),
        ("d", -1.4, -6.6, 0.7, 3), ("d", 1.4, -6.6, 0.7, 3),
        ("l", -2, 0, 2, 0, 0.7, 1), ("d", 0, 2.4, 0.9, 2)]),
    ("Pie Slice", ("caramel", "cheddar", "cream", "tan"), [
        ("p", [(-9, 7), (9, 7), (0, -8)], 0), ("p", [(-7.4, 5.6), (7.4, 5.6), (0, -5.4)], 1),
        ("r", -9, 5.4, 9, 8, 2),
        ("l", -4, 1, 4, 1, 0.7, 0), ("l", -2.4, -3, 2.4, -3, 0.7, 0)]),
    ("Waffle", ("caramel", "dark_brown", "banana", "red"), [
        ("d", 0, 0, 8.6, 0),
        ("l", -8, -4, 8, -4, 0.6, 1), ("l", -8, 0, 8, 0, 0.6, 1),
        ("l", -8, 4, 8, 4, 0.6, 1), ("l", -4, -8, -4, 8, 0.6, 1),
        ("l", 0, -8, 0, 8, 0.6, 1), ("l", 4, -8, 4, 8, 0.6, 1),
        ("d", 0, -1, 2.2, 2)]),
    ("Pretzel", ("caramel", "cream", "dark_brown", "tan"), [
        ("o", -4, 1, 4.4, 1.6, 0), ("o", 4, 1, 4.4, 1.6, 0), ("o", 0, -4.4, 4.0, 1.6, 0),
        ("d", -6, 6, 1.6, 0), ("d", 6, 6, 1.6, 0),
        ("d", -3, -5, 0.8, 1), ("d", 3, -5, 0.8, 1)]),
    ("Gummy Bear", ("orange", "cheddar", "dark_brown", "banana"), [
        ("d", 0, -5, 3.8, 0), ("d", -3.4, -8, 2.0, 0), ("d", 3.4, -8, 2.0, 0),
        ("e", 0, 3, 5.0, 5.4, 0),
        ("e", -5.6, 1, 2.2, 2.6, 0), ("e", 5.6, 1, 2.2, 2.6, 0),
        ("e", -3.4, 8.4, 2.4, 2.2, 0), ("e", 3.4, 8.4, 2.4, 2.2, 0),
        ("d", -1.4, -5.4, 0.7, 2), ("d", 1.4, -5.4, 0.7, 2)]),
]


def sweets():
    return _recipe_category("sweets", SWEET_ITEMS, [
        ("", 0.96, None, False),
        (" Outline", 0.96, None, False, True),
        (" Framed", 0.80, None, True)])


# ── SPORTS ───────────────────────────────────────────────────────────────────

SPORT_ITEMS = [
    ("Soccer Ball", ("white", "black", "silver", "light_gray"), [
        ("d", 0, 0, 9.0, 0), ("p", [(0, -4.4), (4.2, -1.4), (2.6, 3.4), (-2.6, 3.4), (-4.2, -1.4)], 1),
        ("d", 0, -8.4, 2.0, 1), ("d", -7.4, -3, 2.0, 1), ("d", 7.4, -3, 2.0, 1),
        ("d", -4.6, 7.4, 2.0, 1), ("d", 4.6, 7.4, 2.0, 1),
        ("clip", 9.0)]),
    ("Basketball", ("orange", "black", "cheddar", "dark_brown"), [
        ("d", 0, 0, 9.0, 0), ("l", 0, -9, 0, 9, 0.6, 1), ("l", -9, 0, 9, 0, 0.6, 1),
        ("o", -9.4, 0, 7.4, 0.6, 1), ("o", 9.4, 0, 7.4, 0.6, 1),
        ("clip", 9.0)]),
    ("Baseball", ("white", "red", "silver", "light_gray"), [
        ("d", 0, 0, 9.0, 0), ("o", -8.4, 0, 5.6, 0.6, 1), ("o", 8.4, 0, 5.6, 0.6, 1),
        ("l", -4.6, -4, -3.4, -2.6, 0.5, 1), ("l", -4.6, 0, -3.4, 1.4, 0.5, 1),
        ("l", 4.6, -4, 3.4, -2.6, 0.5, 1), ("l", 4.6, 0, 3.4, 1.4, 0.5, 1),
        ("clip", 9.0)]),
    ("Tennis Ball", ("neon_green", "white", "light_green", "cream"), [
        ("d", 0, 0, 9.0, 0), ("o", -9.6, 0, 6.4, 1.0, 1), ("o", 9.6, 0, 6.4, 1.0, 1),
        ("clip", 9.0)]),
    ("Volleyball", ("white", "blue", "sky_blue", "silver"), [
        ("d", 0, 0, 9.0, 0), ("o", 0, -11, 7.0, 1.0, 1), ("o", -9, 6, 7.0, 1.0, 1),
        ("o", 9, 6, 7.0, 1.0, 1),
        ("clip", 9.0)]),
    ("Football", ("dark_brown", "white", "brown", "cream"), [
        ("e", 0, 0, 9.4, 5.6, 0), ("l", -3.4, 0, 3.4, 0, 0.7, 1),
        ("l", -2.4, -1.4, -2.4, 1.4, 0.5, 1), ("l", 0, -1.6, 0, 1.6, 0.5, 1),
        ("l", 2.4, -1.4, 2.4, 1.4, 0.5, 1),
        ("l", -8, -1.6, -6.6, 1.6, 0.5, 1), ("l", 8, -1.6, 6.6, 1.6, 0.5, 1)]),
    ("Rugby Ball", ("white", "dark_green", "silver", "green"), [
        ("e", 0, 0, 9.4, 5.6, 0), ("r", -9.4, -1.4, 9.4, 1.4, 1),
        ("l", -6, -3.4, -6, 3.4, 0.6, 1), ("l", 6, -3.4, 6, 3.4, 0.6, 1)]),
    ("Golf", ("white", "dark_green", "silver", "red"), [
        ("d", 0, -4, 5.4, 0), ("ring_of", 6, 3.0, 0.7, 2),
        ("p", [(-3.4, 2), (3.4, 2), (0.9, 6)], 1), ("r", -0.9, 5, 0.9, 9.4, 1)]),
    ("Bowling Ball", ("purple", "black", "lavender", "dark_purple"), [
        ("d", 0, 0, 9.0, 0), ("d", -3, -3.4, 1.6, 1), ("d", 1, -4.4, 1.6, 1),
        ("d", -0.6, -0.6, 1.6, 1),
        ("clip", 9.0)]),
    ("Bowling Pin", ("white", "red", "silver", "light_gray"), [
        ("d", 0, -6.4, 3.0, 0), ("e", 0, -2, 2.2, 3.4, 0), ("e", 0, 5.4, 5.0, 5.0, 0),
        ("r", -3.0, -4.4, 3.0, -2.6, 1), ("r", -2.6, -1.4, 2.6, 0.4, 1)]),
    ("Ping Pong", ("red", "dark_brown", "black", "caramel"), [
        ("d", 0, -3, 7.4, 0), ("o", 0, -3, 7.4, 1.0, 2), ("r", -1.4, 3.4, 1.4, 10, 1)]),
    ("Tennis Racket", ("navy", "white", "banana", "silver"), [
        ("o", 0, -4, 6.6, 1.4, 0), ("r", -1.4, 2, 1.4, 10, 0),
        ("l", -4.6, -4, 4.6, -4, 0.4, 1), ("l", -4.6, -7.4, 4.6, -7.4, 0.4, 1),
        ("l", -4.6, -0.6, 4.6, -0.6, 0.4, 1),
        ("l", -3.4, -9.4, -3.4, 1.4, 0.4, 1), ("l", 0, -10, 0, 2, 0.4, 1),
        ("l", 3.4, -9.4, 3.4, 1.4, 0.4, 1), ("r", -1.8, 7, 1.8, 10.4, 2)]),
    ("Shuttlecock", ("white", "silver", "red", "light_gray"), [
        ("d", 0, 6, 3.6, 2), ("p", [(-3.6, 6), (3.6, 6), (7.4, -8), (-7.4, -8)], 0),
        ("l", -5.4, -8, -1.6, 5, 0.5, 1), ("l", 0, -8.4, 0, 5, 0.5, 1),
        ("l", 5.4, -8, 1.6, 5, 0.5, 1)]),
    ("Hockey", ("dark_brown", "black", "caramel", "silver"), [
        ("l", -6, -9, 4, 4, 1.4, 0), ("p", [(4, 3), (9, 7), (9, 9), (2.4, 5.4)], 0),
        ("e", -6, 8, 4.4, 2.0, 1)]),
    ("Ice Skate", ("white", "silver", "sky_blue", "light_gray"), [
        ("p", [(-6, -6), (2, -6), (4, 0), (6, 4), (-6, 4)], 0),
        ("r", -7.4, 4, 7.4, 6, 1), ("l", -6, 8.4, 6, 8.4, 0.9, 1),
        ("l", -6, 6, -6, 8.4, 0.7, 1), ("l", 6, 6, 6, 8.4, 0.7, 1),
        ("l", -4, -4.4, 1, -4.4, 0.5, 2), ("l", -4, -1.4, 1.6, -1.4, 0.5, 2)]),
    ("Ski", ("red", "dark_gray", "banana", "silver"), [
        ("p", [(-3.4, -10), (0.6, -10), (2.6, 8), (-1.4, 8)], 0),
        ("p", [(-1.4, 8), (2.6, 8), (4.6, 10), (0.6, 10.4)], 0),
        ("r", -4.4, -1, 3.4, 1, 1),
        ("l", 6, -8, 6, 8, 0.7, 1), ("d", 6, 8, 2.0, 1), ("l", 4, -8.4, 8, -8.4, 0.7, 1)]),
    ("Skateboard", ("caramel", "black", "red", "silver"), [
        ("p", [(-9.4, -2), (9.4, -2), (7.4, 2), (-7.4, 2)], 0),
        ("e", -9.6, -0.4, 2.0, 2.4, 0), ("e", 9.6, -0.4, 2.0, 2.4, 0),
        ("d", -5, 4, 2.2, 1), ("d", 5, 4, 2.2, 1),
        ("r", -5.6, 1.6, -4.4, 3, 3), ("r", 4.4, 1.6, 5.6, 3, 3)]),
    ("Surfboard", ("banana", "red", "toothpaste", "white"), [
        ("e", 0, 0, 4.4, 10.4, 0), ("r", -1.0, -8, 1.0, 8, 1),
        ("e", 0, -6, 3.0, 2.4, 2)]),
    ("Boxing Glove", ("red", "white", "dark_red", "cream"), [
        ("e", -1, -1, 7.4, 6.4, 0), ("e", 5.4, 1.4, 3.0, 3.4, 0),
        ("r", -4.4, 5, 4.4, 9.4, 1), ("l", -7.4, -3.4, -2, -5.4, 0.7, 2),
        ("l", -8, 0, -7, 0, 0.9, 2)]),
    ("Dumbbell", ("dark_gray", "black", "silver", "light_gray"), [
        ("r", -3.4, -1.6, 3.4, 1.6, 2), ("r", -8, -5.4, -5, 5.4, 0),
        ("r", 5, -5.4, 8, 5.4, 0), ("r", -9.6, -3.4, -8, 3.4, 1),
        ("r", 8, -3.4, 9.6, 3.4, 1)]),
    ("Medal", ("banana", "red", "cheddar", "blue"), [
        ("p", [(-4.4, -10), (-1, -10), (1.4, -1), (-2.4, -1)], 1),
        ("p", [(4.4, -10), (1, -10), (-1.4, -1), (2.4, -1)], 3),
        ("d", 0, 4, 6.4, 0), ("o", 0, 4, 6.4, 1.0, 2), ("d", 0, 4, 2.4, 2)]),
    ("Trophy", ("banana", "cheddar", "caramel", "cream"), [
        ("p", [(-6, -8), (6, -8), (4, 1), (-4, 1)], 0),
        ("o", -7.4, -5, 3.4, 1.1, 1), ("o", 7.4, -5, 3.4, 1.1, 1),
        ("r", -1.6, 1, 1.6, 5, 1), ("r", -5.4, 5, 5.4, 7.4, 1),
        ("r", -7, 7.4, 7, 9.6, 2), ("d", 0, -4.4, 2.0, 2)]),
    ("Whistle", ("silver", "dark_gray", "light_gray", "red"), [
        ("e", -2, 0, 6.4, 5.0, 0), ("r", 3, -2.6, 9.4, 1.4, 0),
        ("d", -4.4, -4.4, 1.4, 1), ("l", 9.4, -2.6, 9.4, 1.4, 0.7, 1),
        ("d", -2, 0.6, 1.4, 1)]),
    ("Dartboard", ("dark_green", "cream", "red", "black"), [
        ("d", 0, 0, 9.4, 0), ("o", 0, 0, 9.4, 1.4, 2), ("d", 0, 0, 6.4, 1),
        ("o", 0, 0, 6.4, 1.2, 2), ("d", 0, 0, 3.4, 0), ("d", 0, 0, 1.4, 2)]),
]


def sports():
    return _recipe_category("sports", SPORT_ITEMS, [
        ("", 0.96, None, False),
        (" Outline", 0.96, None, False, True),
        (" Framed", 0.80, None, True)])


GENERATORS.update({"sweets": sweets, "sports": sports})


# ── HOLIDAYS ─────────────────────────────────────────────────────────────────

HOLIDAY_ITEMS = [
    ("Christmas Tree", ("dark_green", "banana", "dark_brown", "red"), [
        ("p", [(-8, 8), (8, 8), (0, 0)], 0), ("p", [(-6.4, 2), (6.4, 2), (0, -4.4)], 0),
        ("p", [(-4.6, -3), (4.6, -3), (0, -8.4)], 0), ("r", -1.6, 8, 1.6, 10.4, 2),
        ("d", 0, -9.6, 1.8, 1), ("d", -4, 5, 1.2, 3), ("d", 3.4, 4, 1.2, 1),
        ("d", -2.4, -0.6, 1.2, 1), ("d", 2.4, -1.4, 1.2, 3)]),
    ("Wreath", ("dark_green", "red", "banana", "green"), [
        ("o", 0, 0, 9.0, 3.4, 0), ("ring_of", 6, 8.4, 1.4, 3),
        ("d", -3.4, 8.6, 1.4, 1), ("d", 3.4, 8.6, 1.4, 1),
        ("p", [(-4, 8), (0, 6), (4, 8), (0, 10)], 1)]),
    ("Bauble", ("red", "banana", "dark_gray", "cream"), [
        ("d", 0, 2, 8.0, 0), ("r", -2.0, -8.4, 2.0, -5.4, 2),
        ("o", -0.6, 3.4, 5.4, 1.0, 1), ("l", -7, 0.6, 7, 0.6, 0.9, 1),
        ("o", 0, -9.4, 1.8, 0.7, 2)]),
    ("Stocking", ("red", "white", "dark_green", "cream"), [
        ("r", -5, -8, 5, 2, 0), ("p", [(-5, 2), (5, 2), (8.4, 7), (8.4, 9.6), (-5, 9.6)], 0),
        ("r", -5.6, -9.6, 5.6, -6.4, 1), ("d", 6.4, 8, 2.4, 0)]),
    ("Santa Hat", ("red", "white", "blush", "cream"), [
        ("p", [(-8, 5), (8, 5), (4, -6), (-2, -8)], 0),
        ("r", -9, 5, 9, 9, 1), ("d", -3.4, -8.4, 2.6, 1)]),
    ("Gift", ("blue", "banana", "sky_blue", "red"), [
        ("r", -8, -2, 8, 9, 0), ("r", -9, -5.4, 9, -2, 2),
        ("r", -1.6, -5.4, 1.6, 9, 1),
        ("o", -3.6, -7.4, 3.0, 1.2, 1), ("o", 3.6, -7.4, 3.0, 1.2, 1)]),
    ("Bell", ("banana", "cheddar", "dark_brown", "cream"), [
        ("d", 0, -8.4, 1.6, 2), ("p", [(-7.4, 5), (7.4, 5), (4, -3), (-4, -3)], 0),
        ("d", 0, -3.4, 4.0, 0), ("r", -8.4, 5, 8.4, 7, 1), ("d", 0, 8.4, 1.8, 1)]),
    ("Snowman", ("white", "black", "orange", "red"), [
        ("d", 0, 6, 6.4, 0), ("d", 0, -0.6, 4.6, 0), ("d", 0, -6, 3.4, 0),
        ("r", -4.4, -9.4, 4.4, -8.4, 1), ("r", -2.6, -12.4, 2.6, -9.4, 1),
        ("d", -1.2, -6.6, 0.7, 1), ("d", 1.2, -6.6, 0.7, 1),
        ("p", [(0, -5.4), (4, -4.6), (0, -4)], 2), ("r", -4.6, -3.4, 4.6, -2.2, 3)]),
    ("Candy Cane", ("white", "red", "cream", "light_pink"), [
        ("l", 3, -4, 3, 10, 2.4, 0), ("l", -3, -4, 3, -4, 2.4, 0),
        ("d", -3, -1.4, 2.4, 0), ("l", 1.4, 2, 4.6, 1, 0.9, 1),
        ("l", 1.4, 6, 4.6, 5, 0.9, 1), ("l", -4.4, -5.4, -1.6, -6.6, 0.9, 1)]),
    ("Menorah", ("banana", "cheddar", "orange", "dark_brown"), [
        ("r", -1.2, -2, 1.2, 8, 0), ("r", -6, 8, 6, 10, 0),
        ("l", -7.4, -2, 7.4, -2, 1.0, 0),
        ("l", -7.4, -2, -7.4, -5, 1.0, 0), ("l", -3.8, -2, -3.8, -5, 1.0, 0),
        ("l", 3.8, -2, 3.8, -5, 1.0, 0), ("l", 7.4, -2, 7.4, -5, 1.0, 0),
        ("d", -7.4, -7, 1.4, 2), ("d", -3.8, -7, 1.4, 2), ("d", 0, -4.4, 1.4, 2),
        ("d", 3.8, -7, 1.4, 2), ("d", 7.4, -7, 1.4, 2)]),
    ("Dreidel", ("blue", "banana", "sky_blue", "white"), [
        ("r", -6.4, -6, 6.4, 3, 0), ("p", [(-6.4, 3), (6.4, 3), (0, 10)], 0),
        ("r", -1.4, -10, 1.4, -6, 1), ("r", -2.4, -3.4, 2.4, 0.6, 1)]),
    ("Pumpkin", ("orange", "dark_green", "black", "cheddar"), [
        ("e", 0, 2, 9.0, 7.4, 0), ("e", -5, 2, 3.4, 7.0, 3), ("e", 5, 2, 3.4, 7.0, 3),
        ("r", -1.2, -8.4, 1.2, -4.4, 1),
        ("p", [(-5.4, -1), (-1.6, -1), (-3.4, 2.4)], 2),
        ("p", [(5.4, -1), (1.6, -1), (3.4, 2.4)], 2),
        # A grin with teeth. This was one filled trapezoid, which reads as a
        # dark slab stuck on the pumpkin rather than as a mouth - the carved
        # look comes entirely from the gaps between the teeth.
        ("p", [(-6.0, 4.4), (6.0, 4.4), (4.6, 8.2), (-4.6, 8.2)], 2),
        ("p", [(-3.4, 4.4), (-1.8, 4.4), (-2.4, 6.6)], 0),
        ("p", [(1.8, 4.4), (3.4, 4.4), (2.4, 6.6)], 0),
        ("p", [(-1.0, 8.2), (1.0, 8.2), (0, 6.2)], 0)]),
    ("Ghost", ("white", "black", "silver", "light_gray"), [
        ("d", 0, -2, 7.4, 0), ("r", -7.4, -2, 7.4, 6, 0),
        ("p", [(-7.4, 6), (-4.4, 9.4), (-1.4, 6), (1.4, 9.4), (4.4, 6), (7.4, 9.4), (7.4, 6)], 0),
        ("d", -3, -3, 1.6, 1), ("d", 3, -3, 1.6, 1), ("e", 0, 1.4, 1.8, 2.4, 1)]),
    ("Bat", ("black", "red", "dark_gray", "dark_purple"), [
        ("e", 0, 0, 3.4, 4.4, 0), ("d", 0, -4.4, 2.8, 0),
        ("p", [(-2.4, -6.4), (-3.4, -9.4), (-0.6, -7)], 0),
        ("p", [(2.4, -6.4), (3.4, -9.4), (0.6, -7)], 0),
        ("p", [(-3, -2), (-10.4, -4), (-8, 1), (-10.4, 3), (-3, 3)], 0),
        ("p", [(3, -2), (10.4, -4), (8, 1), (10.4, 3), (3, 3)], 0),
        ("d", -1.2, -4.6, 0.6, 1), ("d", 1.2, -4.6, 0.6, 1)]),
    ("Witch Hat", ("dark_purple", "banana", "purple", "black"), [
        ("p", [(-4.4, 2), (4.4, 2), (1.4, -10.4)], 0),
        ("e", 0, 4, 10.4, 3.0, 0), ("r", -4.8, 0.6, 4.8, 3.4, 1),
        ("d", 3.4, 2, 1.4, 1)]),
    ("Candle", ("cream", "orange", "banana", "silver"), [
        ("r", -3.4, -2, 3.4, 8.4, 0), ("l", -1.2, -6, -1.2, -2, 0.6, 3),
        ("e", -1.2, -8, 2.0, 3.4, 1), ("e", -1.2, -8.4, 1.0, 1.8, 2),
        ("e", 0, 9.4, 6.4, 1.8, 3)]),
    ("Easter Egg", ("light_pink", "toothpaste", "banana", "lavender"), [
        ("e", 0, 2, 6.4, 8.4, 0), ("e", 0, -2, 5.4, 5.4, 0),
        ("l", -6, -1, 6, -1, 1.2, 1), ("l", -6.4, 4, 6.4, 4, 1.2, 3),
        ("ring_of", 6, 6.4, 1.0, 2)]),
    ("Heart", ("red", "blush", "hot_pink", "white"), [
        ("d", -4.2, -3, 5.0, 0), ("d", 4.2, -3, 5.0, 0),
        ("p", [(-8.6, -1), (8.6, -1), (0, 9.6)], 0), ("d", -3.4, -4.4, 1.6, 3)]),
    ("Shamrock", ("dark_green", "green", "light_green", "caramel"), [
        ("d", 0, -5.4, 4.2, 0), ("d", -5, 0, 4.2, 0), ("d", 5, 0, 4.2, 0),
        ("p", [(-1.4, 1), (1.4, 1), (0.6, 10)], 3), ("d", 0, -0.6, 2.0, 1)]),
    ("Firework", ("banana", "hot_pink", "aqua", "white"), [
        ("rad", 12, 2.4, 9.6, 0.8, 0), ("rad", 12, 2.4, 6.4, 0.8, 1),
        ("d", 0, 0, 2.4, 3), ("ring_of", 12, 9.6, 1.0, 2)]),
    ("Turkey", ("dark_brown", "caramel", "red", "banana"), [
        ("ring_of", 9, 8.0, 2.6, 1), ("e", 0, 3, 5.4, 5.0, 0),
        ("d", 0, -3.4, 3.2, 0), ("p", [(0, -3.4), (4.4, -2.4), (0, -1.4)], 3),
        ("d", -1.2, -4, 0.7, 2), ("d", 1.2, -4, 0.7, 2), ("d", -1.6, -1, 1.2, 2)]),
    ("Lantern", ("red", "banana", "dark_red", "cheddar"), [
        ("e", 0, 0, 7.4, 8.0, 0), ("r", -5, -9.4, 5, -7, 1), ("r", -5, 7, 5, 9.4, 1),
        ("l", -3.4, -7, -3.4, 7, 0.6, 2), ("l", 0, -8, 0, 8, 0.6, 2),
        ("l", 3.4, -7, 3.4, 7, 0.6, 2), ("r", -1.0, 9.4, 1.0, 12, 3)]),
    ("Diya Lamp", ("caramel", "orange", "banana", "rust"), [
        ("p", [(-9, 2), (9, 2), (6, 8), (-6, 8)], 0), ("e", 0, 2, 9, 2.6, 3),
        ("p", [(7, 1), (10.4, 2), (7, 3)], 0),
        ("e", 9.4, -1.4, 1.8, 3.0, 1), ("e", 9.4, -2, 0.9, 1.6, 2)]),
    ("Star of David", ("blue", "sky_blue", "white", "navy"), [
        ("p", [(0, -9.6), (8.4, 4.8), (-8.4, 4.8)], 0),
        ("p", [(0, 9.6), (8.4, -4.8), (-8.4, -4.8)], 0),
        ("p", [(0, -5.4), (4.6, 2.6), (-4.6, 2.6)], 1),
        ("p", [(0, 5.4), (4.6, -2.6), (-4.6, -2.6)], 1)]),
]


def holidays():
    return _recipe_category("holidays", HOLIDAY_ITEMS, [
        ("", 0.96, None, False),
        (" Outline", 0.96, None, False, True),
        (" Framed", 0.80, None, True)])


# ── VIDEOGAME ────────────────────────────────────────────────────────────────

VG_ITEMS = [
    ("Controller", ("dark_gray", "black", "red", "silver"), [
        ("e", -6, 1, 5.0, 5.4, 0), ("e", 6, 1, 5.0, 5.4, 0), ("r", -6, -3, 6, 5, 0),
        ("r", -7.4, -0.6, -3.4, 0.6, 1), ("r", -5.8, -2.2, -5.0, 2.2, 1),
        ("d", 5.4, -1.4, 1.2, 2), ("d", 7.4, 0.6, 1.2, 2), ("d", 3.4, 0.6, 1.2, 2),
        ("d", 5.4, 2.6, 1.2, 2), ("r", -1.6, -1, 1.6, 1, 3)]),
    ("D-Pad", ("dark_gray", "black", "silver", "light_gray"), [
        ("r", -3, -9, 3, 9, 0), ("r", -9, -3, 9, 3, 0),
        ("p", [(-1.6, -6), (1.6, -6), (0, -8)], 1), ("p", [(-1.6, 6), (1.6, 6), (0, 8)], 1),
        ("p", [(-6, -1.6), (-6, 1.6), (-8, 0)], 1), ("p", [(6, -1.6), (6, 1.6), (8, 0)], 1)]),
    ("Joystick", ("red", "dark_gray", "black", "silver"), [
        ("d", 0, -6, 4.4, 0), ("r", -1.6, -6, 1.6, 3, 1),
        ("e", 0, 5, 9.0, 4.4, 2), ("e", 0, 3.4, 3.4, 1.4, 1)]),
    ("Arcade Cabinet", ("blue", "black", "aqua", "red"), [
        ("r", -7.4, -10, 7.4, 10, 0), ("r", -5.4, -8, 5.4, -1, 2),
        ("r", -5.4, 1, 5.4, 4, 1), ("d", -3, 2.4, 1.0, 3), ("d", 0, 2.4, 1.0, 3),
        ("d", 3, 2.4, 1.0, 3), ("r", -7.4, 6, 7.4, 8, 1)]),
    ("Coin", ("banana", "cheddar", "orange", "cream"), [
        ("d", 0, 0, 9.0, 0), ("o", 0, 0, 9.0, 1.4, 1), ("e", 0, 0, 4.0, 6.4, 1),
        ("e", 0, 0, 2.2, 4.6, 0)]),
    ("Heart", ("red", "hot_pink", "white", "dark_red"), [
        ("d", -4.2, -3, 5.0, 0), ("d", 4.2, -3, 5.0, 0),
        ("p", [(-8.6, -1), (8.6, -1), (0, 9.6)], 0), ("d", -3.6, -4.6, 1.6, 2)]),
    ("Star", ("banana", "cheddar", "white", "orange"), [
        ("p", [(0, -10), (2.4, -3.2), (9.6, -3.2), (3.8, 1.2), (5.9, 8.2),
               (0, 4), (-5.9, 8.2), (-3.8, 1.2), (-9.6, -3.2), (-2.4, -3.2)], 0),
        ("d", -2.2, -1.4, 1.2, 2), ("d", 2.2, -1.4, 1.2, 2)]),
    ("Power Mushroom", ("red", "white", "caramel", "black"), [
        ("d", 0, -2, 8.6, 0), ("r", -8.6, -2, 8.6, 0, 0),
        ("d", -4, -4.4, 2.4, 1), ("d", 4, -4.4, 2.4, 1), ("d", 0, -7, 2.0, 1),
        ("r", -4.4, 0, 4.4, 7.4, 1), ("d", -2.2, 3, 1.0, 3), ("d", 2.2, 3, 1.0, 3)]),
    # The blade used to be a rectangle with a FLAT top and a point at y=5 -
    # which is inside the crossguard. So it was blunt at the tip and pointed
    # into its own handle: that is the "sad and limp" sword. Point at the top
    # now, with a fuller down the middle, a chunky guard and a square pommel,
    # which is the blocky look the rest of these items are going for.
    ("Sword", ("silver", "banana", "dark_gray", "caramel"), [
        ("p", [(0, -11.4), (2.8, -7.6), (2.8, 3), (-2.8, 3), (-2.8, -7.6)], 0),
        ("r", -1.0, -7.0, 1.0, 2.4, 2),
        ("r", -7.0, 3, 7.0, 5.6, 1),
        ("r", -1.8, 5.6, 1.8, 9.8, 3),
        ("r", -3.2, 9.8, 3.2, 11.6, 1)]),
    ("Pickaxe", ("dark_gray", "caramel", "silver", "black"), [
        ("p", [(-11.6, -2.6), (-7.0, -8.2), (0, -9.4), (7.0, -8.2), (11.6, -2.6),
               (8.0, -4.0), (0, -5.2), (-8.0, -4.0)], 0),
        ("p", [(-8.0, -6.0), (0, -7.8), (8.0, -6.0), (0, -5.8)], 2),
        ("r", -1.8, -5.0, 1.8, 11.4, 1)]),
    ("Axe", ("silver", "caramel", "dark_gray", "black"), [
        ("r", -1.8, -8.0, 1.8, 11.4, 1),
        ("p", [(1.8, -9.4), (9.6, -7.0), (10.6, 0.6), (1.8, 2.6)], 0),
        ("p", [(1.8, -7.4), (7.4, -5.6), (8.0, -0.4), (1.8, 1.0)], 2)]),
    ("Torch", ("caramel", "orange", "banana", "dark_brown"), [
        ("r", -1.8, -2.0, 1.8, 11.4, 0),
        ("r", -1.8, 2.0, 1.8, 4.0, 3),
        ("r", -3.0, -7.0, 3.0, -2.0, 1),
        ("r", -1.8, -9.4, 1.8, -7.0, 2)]),
    ("Ore Block", ("dark_gray", "silver", "aqua", "black"), [
        ("r", -10, -10, 10, 10, 0),
        ("r", -10, -10, 10, -7.6, 1),
        ("d", -4.6, -3.4, 2.4, 2), ("d", 4.2, -1.0, 2.0, 2),
        ("d", -2.2, 4.6, 2.2, 2), ("d", 5.4, 6.0, 1.8, 2)]),
    ("Shield", ("blue", "banana", "silver", "white"), [
        ("p", [(-7.4, -8), (7.4, -8), (7.4, 2), (0, 10), (-7.4, 2)], 0),
        ("p", [(-5.4, -6), (5.4, -6), (5.4, 1.4), (0, 7.4), (-5.4, 1.4)], 2),
        ("r", -1.2, -5, 1.2, 5, 1), ("r", -4.4, -1.6, 4.4, 0.8, 1)]),
    ("Potion", ("magenta", "silver", "caramel", "white"), [
        ("p", [(-2.2, -8), (2.2, -8), (2.2, -4), (6.4, 3), (6.4, 8), (-6.4, 8),
               (-6.4, 3), (-2.2, -4)], 1),
        ("p", [(-5.4, 2), (5.4, 2), (5.4, 7), (-5.4, 7)], 0),
        ("r", -2.8, -10, 2.8, -7.4, 2), ("d", -2.4, 4.4, 1.0, 3)]),
    ("Key", ("banana", "cheddar", "dark_brown", "cream"), [
        ("o", -5, 0, 4.4, 1.6, 0), ("r", -1, -1.2, 8.4, 1.2, 0),
        ("r", 5.4, 1.2, 6.6, 4.4, 0), ("r", 7.6, 1.2, 8.6, 3.4, 0)]),
    ("Chest", ("caramel", "banana", "dark_brown", "cheddar"), [
        ("r", -8.4, -1, 8.4, 8, 0), ("d", 0, -1, 8.4, 0), ("r", -8.4, -1, 8.4, 1.4, 1),
        ("r", -1.8, 0.6, 1.8, 4.4, 1), ("d", 0, 2.6, 1.0, 2),
        ("l", -8.4, 5, 8.4, 5, 0.7, 2)]),
    ("Bomb", ("black", "red", "banana", "dark_gray"), [
        ("d", 0, 2, 8.0, 0), ("r", -2, -7, 2, -5, 3),
        ("l", 0, -7, 4.4, -10.4, 1.0, 2), ("d", 5, -10.6, 2.0, 1),
        ("d", -3.4, -1.4, 1.8, 3)]),
    ("Ghost Sprite", ("magenta", "white", "blue", "light_pink"), [
        ("d", 0, -2, 7.4, 0), ("r", -7.4, -2, 7.4, 5, 0),
        ("p", [(-7.4, 5), (-5, 9), (-2.4, 5), (0, 9), (2.4, 5), (5, 9), (7.4, 5)], 0),
        ("d", -3.4, -3, 2.4, 1), ("d", 3.4, -3, 2.4, 1),
        ("d", -3.0, -3, 1.2, 2), ("d", 3.8, -3, 1.2, 2)]),
    ("Alien Sprite", ("neon_green", "black", "green", "white"), [
        ("r", -7.4, -3, 7.4, 3, 0), ("r", -4.4, -6, 4.4, 6, 0),
        ("r", -9.4, 0, -7.4, 6, 0), ("r", 7.4, 0, 9.4, 6, 0),
        ("r", -6.4, -8.4, -4.4, -6, 0), ("r", 4.4, -8.4, 6.4, -6, 0),
        ("r", -6.4, 6, -3.4, 8.4, 0), ("r", 3.4, 6, 6.4, 8.4, 0),
        ("d", -2.4, -1.4, 1.4, 1), ("d", 2.4, -1.4, 1.4, 1)]),
    ("Block", ("caramel", "banana", "dark_brown", "cheddar"), [
        ("r", -9, -9, 9, 9, 0), ("r", -9, -9, 9, -6.6, 2), ("r", -9, 6.6, 9, 9, 2),
        ("r", -9, -9, -6.6, 9, 2), ("r", 6.6, -9, 9, 9, 2),
        ("p", [(-2.4, -3), (2.4, -3), (2.4, 0), (0.8, 2), (0.8, 3.4), (-0.8, 3.4),
               (-0.8, 1.4), (0.8, -0.6), (0.8, -1.4), (-2.4, -1.4)], 1)]),
    ("Pipe", ("dark_green", "green", "light_green", "black"), [
        ("r", -9.4, -9, 9.4, -4, 0), ("r", -7, -4, 7, 9.4, 0),
        ("r", -9.4, -9, -5.4, -4, 1), ("r", -7, -4, -4, 9.4, 1)]),
    ("Flag", ("dark_gray", "red", "white", "silver"), [
        ("r", -7.4, -10, -5.4, 10, 0), ("p", [(-5.4, -9), (7.4, -6), (-5.4, -2)], 1),
        ("d", -6.4, -11, 1.8, 2), ("r", -9.4, 8, -3.4, 10.4, 0)]),
    ("Gem", ("aqua", "white", "teal", "toothpaste"), [
        ("p", [(-9, -2.4), (-4.4, -8), (4.4, -8), (9, -2.4), (0, 9.4)], 0),
        ("p", [(-4.4, -8), (4.4, -8), (6, -2.4), (-6, -2.4)], 1),
        ("l", -9, -2.4, 9, -2.4, 0.7, 2), ("l", -6, -2.4, 0, 9.4, 0.7, 2),
        ("l", 6, -2.4, 0, 9.4, 0.7, 2)]),
    ("Tetromino T", ("purple", "lavender", "dark_purple", "white"), [
        ("r", -9, -6, 9, -1, 0), ("r", -3, -1, 3, 4.4, 0),
        ("l", -3, -6, -3, -1, 0.5, 2), ("l", 3, -6, 3, -1, 0.5, 2)]),
    ("Tetromino L", ("orange", "cheddar", "dark_red", "banana"), [
        ("r", -6, -9, -1, 6, 0), ("r", -1, 1, 8, 6, 0),
        ("l", -6, -4, -1, -4, 0.5, 2), ("l", -6, 1, -1, 1, 0.5, 2),
        ("l", 3, 1, 3, 6, 0.5, 2)]),
    ("Tetromino S", ("neon_green", "light_green", "dark_green", "white"), [
        ("r", -8, 0, 3, 5, 0), ("r", -3, -5, 8, 0, 0),
        ("l", -3, 0, -3, 5, 0.5, 2), ("l", 3, -5, 3, 0, 0.5, 2)]),
    ("Tetromino O", ("banana", "cream", "cheddar", "white"), [
        ("r", -6, -6, 6, 6, 0), ("l", 0, -6, 0, 6, 0.5, 2), ("l", -6, 0, 6, 0, 0.5, 2)]),
]


def videogame():
    return _recipe_category("videogame", VG_ITEMS, [
        ("", 0.96, None, False),
        (" Outline", 0.96, None, False, True),
        (" Framed", 0.80, None, True)])


GENERATORS.update({"holidays": holidays, "videogame": videogame})


# ── RAINBOWS ─────────────────────────────────────────────────────────────────
# A rainbow is defined by colour, so the colour-blind uniqueness signature is
# an unusually harsh test here - which is exactly why the old category scored
# 44%. Variety therefore has to come from the FORM: arcs, rings, waves,
# chevrons, spirals and stripes, each with its own band count and thickness.

BOWS = [
    ("red", "orange", "yellow", "green", "blue", "purple"),
    ("magenta", "hot_pink", "orange", "banana", "light_green", "aqua"),
    ("dark_red", "rust", "cheddar", "olive", "teal", "navy"),
    ("purple", "blue", "teal", "green", "yellow", "orange"),
    ("hot_pink", "purple", "blue", "aqua", "light_green", "banana"),
]


def _erase_below(g, y):
    """Grid.set ignores None, so an arc cannot be cut out by drawing over it."""
    for yy in range(max(0, int(y)), g.h):
        for xx in range(g.w):
            g.g[yy][xx] = None


def _draw_bow(g, spec, cx, cy, scale):
    form, bands, t, extra = spec["parts"]
    cols = spec["cols"]
    u = scale

    def band(i):
        return cols[i % len(cols)]

    if form in ("arc", "double", "ring"):
        top = cy + (5 * u if form != "ring" else 0)
        for i in range(bands):
            r = (10.5 - i * t) * u
            if r <= 1:
                break
            g.ring(cx, top, r, band(i), t=t * u + 0.4)
        if form != "ring":
            _erase_below(g, top + 1)
        if form == "double":
            for i in range(bands):
                r = (5.4 - i * t * 0.6) * u
                if r <= 1:
                    break
                g.ring(cx, top, r, band(bands - 1 - i), t=t * u + 0.4)
            _erase_below(g, top + 1)
    elif form == "wave":
        for i in range(bands):
            yy = cy - (bands - 1) * t * u / 2 + i * t * u
            for x in range(-11, 12):
                g.rect(cx + x * u, yy + math.sin(x * 0.55) * 3.2 * u,
                       cx + (x + 1) * u, yy + math.sin(x * 0.55) * 3.2 * u + t * u, band(i))
    elif form == "chevron":
        for i in range(bands):
            off = -(bands - 1) * t * u / 2 + i * t * u
            g.poly([(cx - 11 * u, cy + 5 * u + off), (cx, cy - 5 * u + off),
                    (cx + 11 * u, cy + 5 * u + off),
                    (cx + 11 * u, cy + 5 * u + off + t * u), (cx, cy - 5 * u + off + t * u),
                    (cx - 11 * u, cy + 5 * u + off + t * u)], band(i))
    elif form == "stripe":
        for i in range(bands):
            x0 = cx - 11 * u + i * 22 * u / bands
            g.rect(x0, cy - 11 * u, x0 + 22 * u / bands, cy + 11 * u, band(i))
    elif form == "diag":
        for i in range(bands * 2):
            g.poly([(cx - 14 * u + i * 3.2 * t * u, cy - 12 * u),
                    (cx - 14 * u + (i + 1) * 3.2 * t * u, cy - 12 * u),
                    (cx - 2 * u + (i + 1) * 3.2 * t * u, cy + 12 * u),
                    (cx - 2 * u + i * 3.2 * t * u, cy + 12 * u)], band(i))
    elif form == "spiral":
        steps = bands * 26
        for i in range(steps, 0, -1):
            a = i * 0.13
            r = (1.2 + i * 0.115) * u
            g.disc(cx + math.cos(a) * r, cy + math.sin(a) * r, 2.4 * u,
                   band(int(i / 26)))
    elif form == "fan":
        n = bands * 2
        for i in range(n):
            a0 = math.pi + i * math.pi / n
            a1 = math.pi + (i + 1) * math.pi / n
            g.poly([(cx, cy + 6 * u),
                    (cx + math.cos(a0) * 13 * u, cy + 6 * u + math.sin(a0) * 13 * u),
                    (cx + math.cos(a1) * 13 * u, cy + 6 * u + math.sin(a1) * 13 * u)], band(i))
    elif form == "target":
        for i in range(bands):
            g.disc(cx, cy, (11 - i * t) * u, band(i))
    elif form == "heart":
        for i in range(bands):
            k = 1.0 - i * 0.16
            g.disc(cx - 4.4 * u * k, cy - 3 * u * k, 5.2 * u * k, band(i))
            g.disc(cx + 4.4 * u * k, cy - 3 * u * k, 5.2 * u * k, band(i))
            g.poly([(cx - 9 * u * k, cy - 1 * u * k), (cx + 9 * u * k, cy - 1 * u * k),
                    (cx, cy + 10 * u * k)], band(i))
    elif form == "steps":
        for i in range(bands):
            g.rect(cx - 11 * u + i * 22 * u / bands, cy + 10 * u - (i + 1) * 20 * u / bands,
                   cx - 11 * u + (i + 1) * 22 * u / bands, cy + 10 * u, band(i))

    if extra == "cloud":
        for sgn in (-1, 1):
            bx = cx + sgn * 9.5 * u
            g.disc(bx, cy + 7 * u, 3.4 * u, "white")
            g.disc(bx + 2.6 * u, cy + 7.6 * u, 2.6 * u, "white")
            g.disc(bx - 2.6 * u, cy + 7.6 * u, 2.6 * u, "white")
    elif extra == "sun":
        g.disc(cx, cy - 9 * u, 3.4 * u, "banana")
    elif extra == "drops":
        for k in range(5):
            g.disc(cx - 8 * u + k * 4 * u, cy + 9 * u, 1.2 * u, "sky_blue")


def rainbows():
    forms = [("arc", 6, 1.7, "none"), ("arc", 4, 2.4, "cloud"), ("arc", 7, 1.4, "sun"),
             ("double", 5, 1.6, "none"), ("double", 3, 2.2, "cloud"),
             ("ring", 6, 1.7, "none"), ("ring", 4, 2.4, "none"),
             ("wave", 5, 2.0, "none"), ("wave", 3, 3.0, "drops"),
             ("chevron", 6, 1.8, "none"), ("chevron", 4, 2.6, "none"),
             ("stripe", 6, 0, "none"), ("stripe", 4, 0, "cloud"), ("stripe", 8, 0, "none"),
             ("diag", 5, 1.1, "none"), ("diag", 3, 1.7, "none"),
             ("spiral", 5, 0, "none"), ("spiral", 7, 0, "none"),
             ("fan", 5, 0, "cloud"), ("fan", 3, 0, "sun"),
             ("target", 6, 1.7, "none"), ("target", 4, 2.4, "none"),
             ("heart", 5, 0, "none"), ("steps", 6, 0, "none"), ("steps", 4, 0, "drops")]
    specs = []
    for vi, (suffix, sc) in enumerate([("", 0.96), (" Bold", 0.96), (" Fine", 0.96),
                                       (" Small", 0.72), (" Wide", 0.84)]):
        for si, (form, bands, t, extra) in enumerate(forms):
            b = bands + (2 if suffix == " Fine" else (-1 if suffix == " Bold" else 0))
            tt = t * (0.75 if suffix == " Fine" else (1.35 if suffix == " Bold" else 1.0))
            specs.append(dict(
                name=f"{form.title()} {b}{suffix}",
                parts=(form, max(2, b), tt, extra),
                cols=BOWS[(si + vi) % len(BOWS)],
                bg=_pick_bg("white", PALE, si + vi),
                tags=["rainbow", form], fill=sc, scale=1.0))
    return _emit("rainbows", specs,
                 lambda sp: _frame(lambda g, s, x, y, k: _draw_bow(g, s, x, y, k),
                                   sp, sp["bg"], fill=sp["fill"]), 100)


GENERATORS["rainbows"] = rainbows


# ── ICONS ────────────────────────────────────────────────────────────────────
# The old icons were 5x7 glyphs drawn one bead per pixel: 13 to 25 beads on a
# 28x28 board, which is a hollow outline of a letter rather than a pattern
# anyone would sit down and make. These are the same glyphs at 4x, so a letter
# is 20x28 of solid bead, plus variants that change the STRUCTURE (outlined,
# knocked out of a tile, shadowed) rather than the colour.

FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10101", "10011", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    "Heart": ["01010", "11111", "11111", "11111", "01110", "00100", "00000"],
    "Star": ["00100", "00100", "11111", "01110", "01010", "01010", "00000"],
    "Plus": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "Cross": ["10001", "01010", "00100", "00100", "00100", "01010", "10001"],
    "Check": ["00000", "00001", "00010", "10100", "01000", "00000", "00000"],
    "Arrow": ["00100", "01110", "10101", "00100", "00100", "00100", "00100"],
    "Note": ["00111", "00101", "00101", "01101", "11100", "11100", "01000"],
    "Smile": ["01110", "10001", "10101", "10001", "11011", "10001", "01110"],
    "Bang": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "Query": ["01110", "10001", "00001", "00110", "00100", "00000", "00100"],
    "Anchor": ["00100", "01110", "00100", "11111", "00100", "10101", "01110"],
    "Sun": ["10101", "01110", "01110", "11111", "01110", "01110", "10101"],
}

ICON_COLOURS = [
    ("navy", "banana"), ("dark_red", "cream"), ("forest", "banana"),
    ("purple", "lemon"), ("black", "white"), ("teal", "cream"),
    ("magenta", "white"), ("orange", "navy"), ("dark_blue", "aqua"),
    ("rust", "cream"),
]


def _draw_glyph(g, spec, cx, cy, scale):
    rows, style = spec["parts"]
    ink, tile = spec["cols"]
    px = max(2, int(round(3.4 * scale)))          # bead size of one font pixel
    w = 5 * px
    h = 7 * px
    x0 = cx - w / 2
    y0 = cy - h / 2

    if style in ("tile", "knockout"):
        g.rect(x0 - px, y0 - px, x0 + w + px - 1, y0 + h + px - 1,
               tile if style == "tile" else ink)
    for ry, row in enumerate(rows):
        for rx, ch in enumerate(row):
            if ch != "1":
                continue
            fill = ink
            if style == "knockout":
                fill = tile
            g.rect(x0 + rx * px, y0 + ry * px,
                   x0 + (rx + 1) * px - 1, y0 + (ry + 1) * px - 1, fill)
    if style == "shadow":
        for ry, row in enumerate(rows):
            for rx, ch in enumerate(row):
                if ch == "1":
                    g.rect(x0 + rx * px + px * 0.5, y0 + ry * px + px * 0.5,
                           x0 + (rx + 1) * px - 1 + px * 0.5,
                           y0 + (ry + 1) * px - 1 + px * 0.5, tile)
        for ry, row in enumerate(rows):
            for rx, ch in enumerate(row):
                if ch == "1":
                    g.rect(x0 + rx * px, y0 + ry * px,
                           x0 + (rx + 1) * px - 1, y0 + (ry + 1) * px - 1, ink)


def icons():
    styles = [("", "solid", 0.96), (" Small", "solid", 0.72),
              (" Knockout", "knockout", 0.96), (" Shadow", "shadow", 0.86)]
    specs = []
    for vi, (suffix, style, fill) in enumerate(styles):
        for si, (name, rows) in enumerate(FONT.items()):
            title = name if len(name) > 1 else f"Letter {name}" if name.isalpha() \
                else f"Number {name}"
            cols = ICON_COLOURS[(si + vi * 3) % len(ICON_COLOURS)]
            specs.append(dict(
                name=f"{title}{suffix}", parts=(rows, style), cols=cols,
                bg=_pick_bg(cols[0], PALE, si + vi), fill=fill,
                tags=["icon", name.lower()], scale=1.0))
    # near=1.0: only exact duplicates are dropped. Letters are supposed to
    # look like each other - the category's job is to have all of them.
    return _emit("icons", specs,
                 lambda sp: _frame(lambda g, s, x, y, k: _draw_glyph(g, s, x, y, k),
                                   sp, sp["bg"], fill=sp["fill"]), 140, near=1.0)


GENERATORS["icons"] = icons


# ── SPACE ────────────────────────────────────────────────────────────────────
# The old category was planets and suns: parameter sweeps of a disc, which the
# distinctness filter cut to 75. These are the other things in the sky.

SPACE_ITEMS = [
    ("Rocket", ("white", "red", "sky_blue", "dark_gray"), [
        ("p", [(-3.4, -4), (3.4, -4), (0, -11)], 0), ("r", -3.4, -4, 3.4, 6, 0),
        ("r", -3.4, -1.6, 3.4, 0.6, 1), ("d", 0, 3, 2.2, 2),
        ("p", [(-3.4, 2), (-7.4, 8), (-3.4, 8)], 1), ("p", [(3.4, 2), (7.4, 8), (3.4, 8)], 1),
        ("p", [(-2.4, 6), (2.4, 6), (0, 11)], 1)]),
    ("Saturn", ("cheddar", "banana", "caramel", "cream"), [
        ("e", 0, 0, 11.0, 2.6, 1), ("d", 0, 0, 6.6, 0),
        ("e", 0, -2.4, 5.6, 1.4, 2), ("e", 0, 2, 5.0, 1.2, 2),
        ("clip", 12.0)]),
    ("UFO", ("silver", "neon_green", "dark_gray", "aqua"), [
        ("e", 0, 0, 10.4, 3.0, 0), ("d", 0, -3.4, 5.0, 1),
        ("d", -5.4, 0.6, 1.4, 1), ("d", 0, 1.2, 1.4, 1), ("d", 5.4, 0.6, 1.4, 1),
        ("p", [(-5, 3), (5, 3), (8, 9), (-8, 9)], 3)]),
    ("Astronaut", ("white", "sky_blue", "silver", "red"), [
        ("d", 0, -2, 7.4, 0), ("d", 0, -2, 5.4, 1),
        ("r", -5.4, 4, 5.4, 10, 0), ("r", -8.4, 5, -5.4, 9, 0),
        ("r", 5.4, 5, 8.4, 9, 0), ("r", -2, 4.4, 2, 6, 3)]),
    ("Satellite", ("silver", "sky_blue", "dark_gray", "banana"), [
        ("r", -2.6, -4, 2.6, 4, 0), ("r", -10.4, -3, -3, 3, 1),
        ("r", 3, -3, 10.4, 3, 1), ("l", -10.4, 0, 10.4, 0, 0.5, 2),
        ("d", 0, -7.4, 2.6, 2), ("l", 0, -5, 0, -4, 0.7, 2)]),
    ("Comet", ("sky_blue", "white", "aqua", "banana"), [
        ("d", 5, -4, 4.4, 1), ("p", [(2, -7), (-11, 6), (-6, 8), (4, -1)], 0),
        ("p", [(4, -1), (-8, 9), (-3, 9), (6, 1)], 2)]),
    ("Moon Phase", ("cream", "silver", "light_gray", "banana"), [
        ("d", 0, 0, 9.4, 0), ("d", 5.4, 0, 8.0, None), ("d", 0, 0, 9.4, None),
        ("d", 0, 0, 9.4, 0), ("d", 5.6, 0, 8.2, None),
        ("d", -3.4, -3.4, 1.6, 1), ("d", -1.4, 3, 1.2, 1)]),
    ("Telescope", ("dark_gray", "banana", "silver", "sky_blue"), [
        ("p", [(-9, 4), (2, -7), (6, -3), (-5, 8)], 0),
        ("e", 4, -5, 3.4, 2.6, 1), ("l", -2, 6, -2, 11, 1.0, 2),
        ("l", -7, 11, 3, 11, 1.0, 2)]),
    ("Galaxy", ("purple", "hot_pink", "aqua", "white"), [
        ("d", 0, 0, 2.6, 3),
        ("d", 4, -2, 2.2, 1), ("d", 7, 1, 1.8, 0), ("d", 6, 5, 1.5, 2),
        ("d", -4, 2, 2.2, 1), ("d", -7, -1, 1.8, 0), ("d", -6, -5, 1.5, 2),
        ("d", 1, -6, 1.5, 0), ("d", -1, 6, 1.5, 0),
        ("d", 9, 4, 1.1, 2), ("d", -9, -4, 1.1, 2)]),
    ("Space Station", ("silver", "sky_blue", "dark_gray", "red"), [
        ("o", 0, 0, 9.0, 1.8, 0), ("r", -1.6, -9, 1.6, 9, 0),
        ("r", -9, -1.6, 9, 1.6, 0), ("d", 0, 0, 3.4, 1),
        ("d", 0, -9, 1.8, 3), ("d", 0, 9, 1.8, 3)]),
    ("Asteroid", ("dark_gray", "light_gray", "black", "silver"), [
        ("p", [(-9, -2), (-4, -8), (4, -7), (9, -1), (7, 6), (-2, 9), (-8, 5)], 0),
        ("d", -3, -2, 2.2, 2), ("d", 3.4, 2, 1.8, 2), ("d", 1, -4.4, 1.4, 2)]),
    ("Earth", ("blue", "dark_green", "white", "aqua"), [
        ("d", 0, 0, 9.4, 0),
        ("p", [(-6, -5), (-1, -6), (1, -1), (-4, 1), (-7, -1)], 1),
        ("p", [(2, 1), (7, -1), (8, 4), (3, 6)], 1),
        ("p", [(-5, 4), (-1, 3), (-2, 7), (-6, 7)], 1), ("clip", 9.4)]),
    ("Constellation", ("banana", "white", "sky_blue", "navy"), [
        ("l", -8, -6, -2, -2, 0.5, 2), ("l", -2, -2, 3, -7, 0.5, 2),
        ("l", 3, -7, 8, -3, 0.5, 2), ("l", -2, -2, 0, 4, 0.5, 2),
        ("l", 0, 4, 6, 7, 0.5, 2), ("l", 0, 4, -6, 8, 0.5, 2),
        ("d", -8, -6, 1.8, 0), ("d", -2, -2, 2.2, 0), ("d", 3, -7, 1.8, 0),
        ("d", 8, -3, 1.8, 0), ("d", 0, 4, 2.2, 0), ("d", 6, 7, 1.6, 0),
        ("d", -6, 8, 1.6, 0)]),
    ("Shooting Star", ("banana", "white", "cheddar", "sky_blue"), [
        ("p", [(4, -7), (6.2, -1.4), (11.6, -1.4), (7.2, 2), (9, 7.4),
               (4, 4), (-1, 7.4), (0.8, 2), (-3.6, -1.4), (1.8, -1.4)], 0),
        ("p", [(-1, -2), (-11, 5), (-8, 7), (0, 1)], 1),
        ("p", [(0, 1), (-9, 9), (-5, 9), (2, 3)], 2)]),
    ("Black Hole", ("black", "orange", "banana", "dark_purple"), [
        ("o", 0, 0, 10.4, 1.6, 1), ("o", 0, 0, 8.4, 1.4, 2),
        ("o", 0, 0, 6.6, 1.2, 1), ("d", 0, 0, 5.0, 0)]),
    ("Alien Ship", ("neon_green", "silver", "dark_green", "aqua"), [
        ("e", 0, 2, 10.4, 3.4, 1), ("d", 0, -2.4, 5.6, 0),
        ("o", 0, -2.4, 5.6, 1.0, 2), ("r", -1, 5, 1, 11, 3),
        ("p", [(-5, 11), (5, 11), (7, 13), (-7, 13)], 3)]),
]


def space():
    return _recipe_category("space", SPACE_ITEMS, [
        ("", 0.96, None, False),
        (" Outline", 0.96, None, False, True),
        (" Framed", 0.80, None, True)], target=60)


GENERATORS["space"] = space


# ── GEMS ─────────────────────────────────────────────────────────────────────
# The old gems were discs and ovals with a highlight: identifiable as "a shiny
# blob", not as a cut stone. A cut stone reads from its FACETS - a table, a
# crown and a girdle - so these are drawn as facet polygons rather than as an
# outline with a sparkle inside.

def _facets(top, bot, w, table, col_a, col_b, girdle):
    """Standard brilliant-style facet set for a stone of half-width w."""
    return [
        ("p", [(-table, top), (table, top), (w, girdle), (-w, girdle)], 0),
        ("p", [(-w, girdle), (w, girdle), (0, bot)], 1),
        ("p", [(-table, top), (0, top - 0.1), (0, girdle), (-w * 0.45, girdle)], 2),
        ("p", [(table, top), (0, top - 0.1), (0, girdle), (w * 0.45, girdle)], 3),
        ("l", -w, girdle, w, girdle, 0.5, 2),
        ("l", -w * 0.45, girdle, 0, bot, 0.4, 3),
        ("l", w * 0.45, girdle, 0, bot, 0.4, 3),
    ]


GEM_CUTS = [
    ("Round Brilliant", (-8.5, 9.5, 9.0, 4.5, -3.0)),
    ("Emerald Cut",     (-9.5, 9.0, 6.5, 5.5, -5.0)),
    ("Princess Cut",    (-9.0, 9.5, 8.0, 7.5, -6.0)),
    ("Marquise",        (-9.5, 9.5, 5.5, 2.0, -1.0)),
    ("Pear Cut",        (-9.5, 9.5, 7.0, 2.5, 1.0)),
    ("Oval Cut",        (-9.0, 9.0, 7.0, 4.0, -2.0)),
    ("Cushion Cut",     (-8.5, 9.0, 8.5, 6.0, -4.0)),
    ("Trillion",        (-9.0, 8.0, 9.5, 8.0, -7.0)),
    ("Baguette",        (-9.5, 9.5, 4.5, 4.2, -6.5)),
    ("Asscher",         (-9.0, 9.0, 7.5, 6.5, -5.5)),
    ("Radiant",         (-9.0, 9.5, 8.5, 6.5, -5.0)),
    ("Heart Cut",       (-8.0, 9.5, 8.5, 3.0, -2.0)),
]

GEM_COLOURS = [
    ("red", "dark_red", "hot_pink", "blush"),
    ("blue", "navy", "sky_blue", "aqua"),
    ("green", "dark_green", "light_green", "toothpaste"),
    ("purple", "dark_purple", "lavender", "light_lavender"),
    ("aqua", "teal", "toothpaste", "white"),
    ("banana", "cheddar", "cream", "white"),
    ("magenta", "purple", "light_pink", "blush"),
    ("orange", "rust", "cheddar", "banana"),
    ("light_gray", "silver", "white", "cream"),
    ("dark_red", "black", "red", "blush"),
]


def gems():
    items = []
    # Colour is invisible to the distinctness test, so cycling ten colours per
    # cut produced ten identical boards. Proportion is what actually varies a
    # stone: table width, girdle height and half-width, which is also what
    # separates a real Asscher from a real Emerald cut.
    PROPS = [(1.00, 1.00, 0.0), (0.72, 1.00, 0.0), (1.28, 1.00, 0.0),
             (1.00, 0.80, 0.0), (1.00, 1.18, 0.0), (1.00, 1.00, -2.5),
             (1.00, 1.00, 2.5), (0.80, 1.15, -1.5)]
    for name, (top, bot, w, table, girdle) in GEM_CUTS:
        for ci, (ts, ws, gs) in enumerate(PROPS):
            cols = GEM_COLOURS[(len(items) + ci) % len(GEM_COLOURS)]
            table_i = table * ts
            w_i = w * ws
            girdle_i = girdle + gs
            ops = _facets(top, bot, w_i, table_i, cols[0], cols[1], girdle_i)
            if name == "Heart Cut":
                ops = [("d", -w_i * 0.48, top + 2.4, w_i * 0.55, 0),
                       ("d", w_i * 0.48, top + 2.4, w_i * 0.55, 0),
                       ("p", [(-w_i, top + 3.2), (w_i, top + 3.2), (0, bot)], 0),
                       ("l", 0, top + 2.0, 0, bot, 0.5, 2),
                       ("p", [(-w_i * 0.62, top + 3.2), (0, top + 3.2), (0, bot * 0.7)], 1)]
            elif name == "Marquise":
                ops = [("e", 0, 0.5, w_i, 9.4 * ts, 0),
                       ("e", 0, 0.5, w_i * 0.55, 6.4 * ts, 2),
                       ("l", -w_i, 0.5, w_i, 0.5, 0.5, 1),
                       ("l", 0, -9, 0, 10, 0.5, 1)]
            elif name == "Pear Cut":
                ops = [("d", 0, 3.4, w_i, 0),
                       ("p", [(-w_i, 3.4), (w_i, 3.4), (0, top)], 0),
                       ("l", -w_i, 3.4, w_i, 3.4, 0.5, 1),
                       ("p", [(-w_i * 0.5, 3.4), (w_i * 0.5, 3.4), (0, top * 0.55)], 2),
                       ("d", 0, 4.4, w_i * 0.42, 1)]
            items.append((f"{name} {ci + 1}", cols, ops))
    return _recipe_category("gems", items, [
        ("", 0.94, None, False),
        (" Outline", 0.94, None, False, True),
        (" Framed", 0.80, None, True)],
        target=120)


GENERATORS["gems"] = gems
