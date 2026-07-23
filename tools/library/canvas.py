"""A small pixel canvas with the shape primitives the generators need.

Everything writes bead color ids into a width x height grid; call cells() to get
the (x, y, color_id) list make_pattern expects. Coordinates are grid cells.
"""
import math


class Grid:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.g = [[None] * w for _ in range(h)]

    def inb(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def set(self, x, y, cid):
        xi, yi = int(round(x)), int(round(y))
        if cid is not None and self.inb(xi, yi):
            self.g[yi][xi] = cid

    def get(self, x, y):
        return self.g[y][x] if self.inb(x, y) else None

    def fill(self, cid):
        for y in range(self.h):
            for x in range(self.w):
                self.g[y][x] = cid

    def rect(self, x0, y0, x1, y1, cid):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.set(x, y, cid)

    def frame(self, x0, y0, x1, y1, cid, t=1):
        for i in range(t):
            self.rect(x0 + i, y0 + i, x1 - i, y0 + i, cid)
            self.rect(x0 + i, y1 - i, x1 - i, y1 - i, cid)
            self.rect(x0 + i, y0 + i, x0 + i, y1 - i, cid)
            self.rect(x1 - i, y0 + i, x1 - i, y1 - i, cid)

    def disc(self, cx, cy, r, cid):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, cid)

    def ring(self, cx, cy, r, cid, t=1.0):
        r0 = r - t
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if r0 * r0 <= d2 <= r * r:
                    self.set(x, y, cid)

    def ellipse(self, cx, cy, rx, ry, cid):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if rx > 0 and ry > 0 and ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.set(x, y, cid)

    def line(self, x0, y0, x1, y1, cid, t=0):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            if t <= 0:
                self.set(x0, y0, cid)
            else:
                self.disc(x0, y0, t, cid)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def poly(self, pts, cid):
        """Scanline fill of a polygon given as [(x,y), ...]."""
        if not pts:
            return
        ys = [p[1] for p in pts]
        ymin, ymax = int(math.floor(min(ys))), int(math.ceil(max(ys)))
        n = len(pts)
        for y in range(ymin, ymax + 1):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(math.ceil(xs[i])), int(math.floor(xs[i + 1])) + 1):
                    self.set(x, y, cid)

    def poly_outline(self, pts, cid, t=0):
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            self.line(x0, y0, x1, y1, cid, t=t)

    def cells(self):
        return [(x, y, self.g[y][x]) for y in range(self.h)
                for x in range(self.w) if self.g[y][x] is not None]


# ── Parametric shape point sets ──────────────────────────────────────────────

def star_points(cx, cy, r_out, r_in, n, rot=-math.pi / 2):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def reg_polygon(cx, cy, r, n, rot=-math.pi / 2):
    return [(cx + r * math.cos(rot + i * 2 * math.pi / n),
             cy + r * math.sin(rot + i * 2 * math.pi / n)) for i in range(n)]


def heart_points(cx, cy, size, steps=72):
    """A smooth heart centered at (cx, cy), spanning about `size` cells wide."""
    pts = []
    s = size / 32.0
    for i in range(steps):
        t = 2 * math.pi * i / steps
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * s, cy - y * s))
    return pts


def crescent(grid, cx, cy, r, cid, offset):
    """Filled disc minus an offset disc = crescent moon."""
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r and \
               (x - (cx + offset)) ** 2 + (y - cy) ** 2 > r * r:
                grid.set(x, y, cid)
