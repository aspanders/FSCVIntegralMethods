"""Generate BeadSnap's app icon: a single glossy 3D fuse bead on a purple-to-
pink brand gradient. Produces the iOS 1024 master and Android adaptive-icon
foreground/background layers at every mipmap density, all from one shared
render function so they stay pixel-consistent.

No numpy available, so gradients are built with Pillow's linear_gradient()
resized/rotated per target size (cheap, and Pillow's resampling keeps them
smooth since there's no fine detail to alias).
"""
import math
import os
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

# Brand gradient: deep indigo -> vivid magenta (BeadSnap's purple identity,
# warmed toward the hot_pink already used throughout the bead palette).
BG_A = (59, 15, 92)      # deep indigo, top-left
BG_B = (230, 45, 145)    # hot magenta, bottom-right

# Bead: golden amber (complementary to the purple bg = maximum pop), a real
# color from the app's own bead palette (cheddar/banana family).
BEAD_LIGHT = (255, 240, 176)   # highlight
BEAD_BASE = (255, 179, 0)      # base
BEAD_DARK = (196, 116, 0)      # shaded edge / side wall
HOLE_COLOR = (61, 36, 21)      # warm dark brown, not flat black


def diagonal_gradient(size, color_a, color_b, angle=45):
    big = int(size * 1.6)
    grad = Image.linear_gradient("L").resize((big, big), Image.BICUBIC)
    grad = grad.rotate(angle, resample=Image.BICUBIC)
    left = (big - size) // 2
    grad = grad.crop((left, left, left + size, left + size))
    a = Image.new("RGB", (size, size), color_a)
    b = Image.new("RGB", (size, size), color_b)
    return Image.composite(b, a, grad)


def circle_mask(size, d):
    m = Image.new("L", (size, size), 0)
    dd = ImageDraw.Draw(m)
    r = d / 2
    cx = cy = size / 2
    dd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    return m


def render_bead(canvas_size, bead_ratio, transparent_bg):
    """Render the bead (optionally on the brand gradient, or alone with a
    transparent background for the Android foreground layer)."""
    ss = 3  # supersample for crisp anti-aliasing, then downscale
    S = canvas_size * ss
    cx = cy = S / 2
    bead_d = S * bead_ratio
    r = bead_d / 2

    if transparent_bg:
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    else:
        img = diagonal_gradient(S, BG_A, BG_B).convert("RGBA")

    # --- drop shadow, grounding the bead against the background ---
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    soff = r * 0.10
    sd.ellipse([cx - r * 1.02, cy - r * 0.96 + soff * 2,
               cx + r * 1.02, cy + r * 1.08 + soff * 2], fill=(20, 5, 30, 130))
    shadow = shadow.filter(ImageFilter.GaussianBlur(S * 0.018))
    img = Image.alpha_composite(img, shadow)

    # --- cylinder side wall (peeks out beneath the top face -> thickness) ---
    wall_off = r * 0.13
    wall = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wall)
    wd.ellipse([cx - r, cy - r + wall_off, cx + r, cy + r + wall_off],
               fill=BEAD_DARK + (255,))
    img = Image.alpha_composite(img, wall)

    # --- top face: diagonal gradient dome (light upper-left -> dark lower-right) ---
    top_grad = diagonal_gradient(S, BEAD_LIGHT, BEAD_DARK, angle=35).convert("RGBA")
    mid_tint = diagonal_gradient(S, BEAD_LIGHT, BEAD_BASE, angle=35)
    top_grad = Image.blend(mid_tint.convert("RGBA"), top_grad, 0.55)
    mask = circle_mask(S, bead_d)
    img.paste(top_grad, (0, 0), mask)

    # --- specular highlight (glossy plastic catch-light), pushed well clear
    # of the hole so the two don't merge into a smear ---
    hl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hlx, hly = cx - r * 0.44, cy - r * 0.48
    hd.ellipse([hlx - r * 0.24, hly - r * 0.15, hlx + r * 0.24, hly + r * 0.15],
               fill=(255, 255, 255, 175))
    hl = hl.filter(ImageFilter.GaussianBlur(S * 0.013))
    img = Image.alpha_composite(img, hl)

    # --- the hole: a tight ambient-occlusion ring, then the recessed hole ---
    hole_d = bead_d * 0.34
    hr = hole_d / 2
    ao = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ad = ImageDraw.Draw(ao)
    ad.ellipse([cx - hr * 1.16, cy - hr * 1.16, cx + hr * 1.16, cy + hr * 1.16],
               fill=(60, 20, 10, 75))
    ao = ao.filter(ImageFilter.GaussianBlur(S * 0.007))
    img = Image.alpha_composite(img, ao)

    hole = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hd2 = ImageDraw.Draw(hole)
    hd2.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=HOLE_COLOR + (255,))
    img = Image.alpha_composite(img, hole)

    # thin inner-rim highlight catching the light, upper-left of the hole
    rim = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    rd.arc([cx - hr, cy - hr, cx + hr, cy + hr], start=170, end=280,
           fill=(255, 220, 150, 160), width=max(2, int(S * 0.006)))
    rim = rim.filter(ImageFilter.GaussianBlur(S * 0.004))
    img = Image.alpha_composite(img, rim)

    img = img.resize((canvas_size, canvas_size), Image.LANCZOS)
    return img


def save_ios(path):
    img = render_bead(1024, bead_ratio=0.60, transparent_bg=False).convert("RGB")
    img.save(path, "PNG")
    print("iOS:", path, img.size, img.mode)


# Android adaptive icon: 108dp canvas, ~66dp safe-zone diameter recommended.
DENSITIES = {"mdpi": 1.0, "hdpi": 1.5, "xhdpi": 2.0, "xxhdpi": 3.0, "xxxhdpi": 4.0}
FG_RATIO = 0.50   # bead diameter as a fraction of the 108dp canvas


def save_android(res_dir):
    for name, scale in DENSITIES.items():
        canvas = int(round(108 * scale))
        d = os.path.join(res_dir, f"mipmap-{name}")
        os.makedirs(d, exist_ok=True)
        fg = render_bead(canvas, bead_ratio=FG_RATIO, transparent_bg=True)
        fg.save(os.path.join(d, "ic_launcher_foreground.png"), "PNG")
        bg = diagonal_gradient(canvas, BG_A, BG_B)
        bg.save(os.path.join(d, "ic_launcher_background.png"), "PNG")
        print("Android:", name, canvas)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/icon_preview.png"
        render_bead(1024, bead_ratio=0.60, transparent_bg=False).convert("RGB").save(out)
        print("wrote", out)
    else:
        save_ios(os.path.join(REPO, "BeadSnap", "BeadSnap", "Resources",
                              "Assets.xcassets", "AppIcon.appiconset", "AppIcon-1024.png"))
        save_android(os.path.join(REPO, "BeadSnapAndroid", "app", "src", "main", "res"))
