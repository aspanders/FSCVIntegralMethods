"""Background detection and physical buildability for fuse-bead patterns.

A pattern with no background is only makeable if every bead touches another:
fused beads bond where their edges meet, so a piece hanging off a corner is
held by one weld and a piece touching nothing at all falls on the floor. That
makes connectivity a correctness property, not an aesthetic one, and it only
starts to matter once the background is gone - a full board is trivially
connected, which is why nobody noticed.

Definitions used here:
  background   one colour covering the whole board edge to edge
  connected    4-connectivity (up/down/left/right). Two beads meeting only at
               a corner touch at a point, not along an edge.
  bridge       a bead whose removal splits the piece - a one-bead-wide neck
  diagonal-only pair of beads joined solely at a corner, i.e. a hinge
"""
import sys
from collections import deque

from compact import from_rows


def grid_of(p):
    cells = p.get("cells") or from_rows(p.get("rows", []), p["palette"])
    w, h = p["grid"]["width"], p["grid"]["height"]
    g = [[None] * w for _ in range(h)]
    for c in cells:
        cid = c.get("colorId")
        if cid is not None and 0 <= c["x"] < w and 0 <= c["y"] < h:
            g[c["y"]][c["x"]] = cid
    return g, w, h


def has_background(p, edge_frac=0.92):
    """True when one colour occupies almost the whole border of the board.

    Testing the BORDER rather than the total area is what distinguishes a
    backdrop from a big subject: a full-bleed pattern like a stripe fill has a
    solid border, and so does a bird on a sky, but a bird alone does not.
    """
    g, w, h = grid_of(p)
    border = ([g[0][x] for x in range(w)] + [g[h - 1][x] for x in range(w)] +
              [g[y][0] for y in range(h)] + [g[y][w - 1] for y in range(h)])
    filled = [c for c in border if c is not None]
    if len(filled) < len(border) * edge_frac:
        return False
    top = max(set(filled), key=filled.count)
    return filled.count(top) >= len(border) * edge_frac


def components(g, w, h, diagonal=False):
    """Connected groups of beads. 4-connected unless `diagonal`."""
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diagonal:
        steps += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    seen = [[False] * w for _ in range(h)]
    out = []
    for sy in range(h):
        for sx in range(w):
            if g[sy][sx] is None or seen[sy][sx]:
                continue
            comp = []
            q = deque([(sx, sy)])
            seen[sy][sx] = True
            while q:
                x, y = q.popleft()
                comp.append((x, y))
                for dx, dy in steps:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] \
                            and g[ny][nx] is not None:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            out.append(comp)
    out.sort(key=len, reverse=True)
    return out


def bridges(g, w, h):
    """Beads whose removal disconnects the piece (articulation points).

    Iterative Hopcroft-Tarjan; recursion overflows on an 868-bead board.
    """
    idx = {}
    for y in range(h):
        for x in range(w):
            if g[y][x] is not None:
                idx[(x, y)] = len(idx)
    n = len(idx)
    if n < 3:
        return []
    adj = [[] for _ in range(n)]
    for (x, y), i in idx.items():
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            j = idx.get((x + dx, y + dy))
            if j is not None:
                adj[i].append(j)
    disc = [-1] * n
    low = [0] * n
    parent = [-1] * n
    art = set()
    timer = 0
    for root in range(n):
        if disc[root] != -1:
            continue
        stack = [(root, iter(adj[root]))]
        disc[root] = low[root] = timer
        timer += 1
        children = 0
        while stack:
            v, it = stack[-1]
            advanced = False
            for to in it:
                if disc[to] == -1:
                    parent[to] = v
                    disc[to] = low[to] = timer
                    timer += 1
                    if v == root:
                        children += 1
                    stack.append((to, iter(adj[to])))
                    advanced = True
                    break
                if to != parent[v]:
                    low[v] = min(low[v], disc[to])
            if not advanced:
                stack.pop()
                if stack:
                    u = stack[-1][0]
                    low[u] = min(low[u], low[v])
                    if parent[u] != -1 and low[v] >= disc[u]:
                        art.add(u)
        if children > 1:
            art.add(root)
    rev = {i: xy for xy, i in idx.items()}
    return [rev[i] for i in art]


def hinges(g, w, h):
    """Bead pairs touching ONLY at a corner - a hinge, not a weld.

    Counted per pair of 4-connected components that a diagonal step would
    join: those are the places where the piece is held together by geometry
    the plastic does not actually provide.
    """
    comp_id = {}
    for i, comp in enumerate(components(g, w, h)):
        for xy in comp:
            comp_id[xy] = i
    out = []
    for (x, y), a in comp_id.items():
        for dx, dy in ((1, 1), (1, -1)):
            for sx, sy in ((x + dx, y + dy), (x - dx, y - dy)):
                b = comp_id.get((sx, sy))
                if b is not None and b != a:
                    out.append(((x, y), (sx, sy)))
    return out


def report(p):
    g, w, h = grid_of(p)
    bg = has_background(p)
    comps = components(g, w, h)
    d = dict(background=bg, pieces=len(comps),
             largest=len(comps[0]) if comps else 0,
             beads=sum(len(c) for c in comps))
    if not bg:
        d["loose"] = sum(len(c) for c in comps[1:])
        d["hinges"] = len(hinges(g, w, h))
        d["bridges"] = len(bridges(g, w, h))
    return d


if __name__ == "__main__":
    import json
    from audit import PATTERNS
    ps = json.load(open(sys.argv[1] if len(sys.argv) > 1 else PATTERNS))["patterns"]
    from collections import Counter
    bg = Counter()
    broken = []
    for p in ps:
        r = report(p)
        bg[(p["category"], r["background"])] += 1
        if not r["background"] and (r["pieces"] > 1 or r["hinges"]):
            broken.append((p["category"], p["title"], r["pieces"], r["hinges"]))
    tot = len(ps)
    nobg = sum(v for (c, b), v in bg.items() if not b)
    print(f"{tot} patterns, {nobg} without a background ({100*nobg/tot:.1f}%)")
    print(f"of those, {len(broken)} are not physically buildable")
    print(f"\n{'category':<12}{'total':>7}{'noBG':>7}{'noBG%':>7}{'broken':>8}")
    cats = sorted({c for c, _ in bg})
    for c in cats:
        t = bg[(c, True)] + bg[(c, False)]
        n = bg[(c, False)]
        b = sum(1 for x in broken if x[0] == c)
        print(f"{c:<12}{t:>7}{n:>7}{100*n/t:>6.0f}%{b:>8}")


# ── Making a pattern buildable ───────────────────────────────────────────────

def make_buildable(g, w, h, drop_below=3, max_gap=5):
    """Weld a pattern into ONE 4-connected piece, in place.

    Repeatedly takes the largest piece as the body and bridges the nearest
    loose piece to it along the shortest run of empty cells, using the loose
    piece's own colour so a leg stays leg-coloured and a ring stays ring-
    coloured. Pieces smaller than `drop_below` beads that are further than
    `max_gap` away are removed instead - a stray highlight bead is not worth a
    spoke across the board.

    The search is a multi-source BFS out from the body rather than a pairwise
    scan: on a 32x32 board with twenty concentric rings the pairwise version is
    a million comparisons per weld.
    """
    welded = dropped = 0
    while True:
        comps = components(g, w, h)
        if len(comps) <= 1:
            break
        body = comps[0]
        rest = comps[1:]
        owner = {}
        for i, comp in enumerate(rest):
            for xy in comp:
                owner[xy] = i

        # BFS out from the body through empty cells only.
        INF = 10 ** 9
        dist = [[INF] * w for _ in range(h)]
        prev = [[None] * w for _ in range(h)]
        q = deque()
        for x, y in body:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and g[ny][nx] is None \
                        and dist[ny][nx] == INF:
                    dist[ny][nx] = 1
                    prev[ny][nx] = (x, y)
                    q.append((nx, ny))
        target = None
        while q and target is None:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h):
                    continue
                if (nx, ny) in owner:
                    target = (x, y, owner[(nx, ny)])
                    break
                if g[ny][nx] is None and dist[ny][nx] == INF:
                    dist[ny][nx] = dist[y][x] + 1
                    prev[ny][nx] = (x, y)
                    q.append((nx, ny))
        if target is None:
            # Nothing reachable: everything left is walled off. Drop it.
            for comp in rest:
                for x, y in comp:
                    g[y][x] = None
                dropped += len(comp)
            break

        tx, ty, ci = target
        comp = rest[ci]
        gap = dist[ty][tx]
        if len(comp) < drop_below and gap > max_gap:
            for x, y in comp:
                g[y][x] = None
            dropped += len(comp)
            continue
        colour = g[comp[0][1]][comp[0][0]]
        cx, cy = tx, ty
        while cx is not None and g[cy][cx] is None:
            g[cy][cx] = colour
            welded += 1
            nxt = prev[cy][cx]
            if nxt is None:
                break
            cx, cy = nxt
    return welded, dropped


def strip_background(g, w, h, colour=None):
    """Remove the backdrop. Defaults to whichever colour owns the border."""
    if colour is None:
        border = ([g[0][x] for x in range(w)] + [g[h - 1][x] for x in range(w)] +
                  [g[y][0] for y in range(h)] + [g[y][w - 1] for y in range(h)])
        filled = [c for c in border if c is not None]
        if not filled:
            return None
        colour = max(set(filled), key=filled.count)
    for y in range(h):
        for x in range(w):
            if g[y][x] == colour:
                g[y][x] = None
    return colour


def weak_necks(g, w, h, min_load=6):
    """One-bead joins that carry real weight.

    Not every articulation point matters. Every bead along a one-bead-wide
    lace ring is one, and a fused strand of that kind holds perfectly well -
    ironing melts edge-touching beads into a solid run. What breaks is a
    SUBSTANTIAL part hanging off the body by a single bead: a cherry on a stem,
    a pom-pom on a hat, a wheel under a frame. So a neck counts only when
    removing it would strand at least `min_load` beads.

    Stranded sizes come from the DFS subtree sizes in the same pass that finds
    the articulation points. Re-running a component scan per candidate is
    O(bridges x cells), which on a lacy mandala is 135k operations per pattern
    and far too slow to iterate on.

    Returns [(x, y, stranded_beads)], worst first.
    """
    idx = {}
    for y in range(h):
        for x in range(w):
            if g[y][x] is not None:
                idx[(x, y)] = len(idx)
    n = len(idx)
    if n < 3:
        return []
    adj = [[] for _ in range(n)]
    for (x, y), i in idx.items():
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            j = idx.get((x + dx, y + dy))
            if j is not None:
                adj[i].append(j)
    rev = {i: xy for xy, i in idx.items()}
    disc = [-1] * n
    low = [0] * n
    size = [1] * n
    parent = [-1] * n
    timer = 0
    found = {}
    for root in range(n):
        if disc[root] != -1:
            continue
        comp_root = root
        order = []
        stack = [(root, iter(adj[root]))]
        disc[root] = low[root] = timer
        timer += 1
        order.append(root)
        root_children = 0
        while stack:
            v, it = stack[-1]
            advanced = False
            for to in it:
                if disc[to] == -1:
                    parent[to] = v
                    disc[to] = low[to] = timer
                    timer += 1
                    order.append(to)
                    if v == comp_root:
                        root_children += 1
                    stack.append((to, iter(adj[to])))
                    advanced = True
                    break
                if to != parent[v]:
                    low[v] = min(low[v], disc[to])
            if not advanced:
                stack.pop()
                if stack:
                    u = stack[-1][0]
                    low[u] = min(low[u], low[v])
                    size[u] += size[v]
                    if parent[u] != -1 and low[v] >= disc[u]:
                        # cutting u strands v's subtree
                        found[u] = max(found.get(u, 0), size[v])
        total = size[comp_root]
        if root_children > 1:
            # the root separates its children; the smallest side is what falls
            sides = [size[c] for c in adj[comp_root] if parent[c] == comp_root]
            if sides:
                found[comp_root] = max(found.get(comp_root, 0),
                                       total - 1 - max(sides))
    out = [(rev[i][0], rev[i][1], s) for i, s in found.items() if s >= min_load]
    out.sort(key=lambda t: -t[2])
    return out


def thicken_necks(g, w, h, min_load=6, passes=3):
    """Widen every load-bearing one-bead join into a solid block.

    Fills the empty cells around the neck, which gives the join a second
    independent path and turns a single weld into a fused corner. Two earlier
    attempts were too clever and did not work:

    - Widening only the neck moves the break one bead along a one-bead-wide
      strand. Strands are fixed at the source now (canvas.Grid.limb), not here.
    - Handling only necks with exactly two orthogonal neighbours skipped most
      real cases: the worst mandala neck has THREE, because it sits where a
      ring meets its weld, and that shape is the common one.

    Anything still weak after `passes` is left alone rather than mangled - it
    is connected, just slender.
    """
    added = 0
    for _ in range(passes):
        necks = weak_necks(g, w, h, min_load)
        if not necks:
            break
        changed = False
        for x, y, _load in necks:
            colour = g[y][x]
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and g[ny][nx] is None:
                        g[ny][nx] = colour
                        added += 1
                        changed = True
        if not changed:
            break
    return added


# On a board with no backdrop an empty peg reads as pale grey, so a white or
# near-white bead is indistinguishable from "leave this one out" - and in the
# mandalas, hearts and circles those beads are the OUTER SILHOUETTE. Makers
# would build the piece a ring smaller than designed. Swap them for a tinted
# near-white that still reads as white beside real colours.
PALE_SWAP = {"white": "cream", "ivory": "cream", "clear": "toothpaste"}


def retint_pale(p):
    """Replace board-coloured beads on a backgroundless pattern."""
    if not any(c["id"] in PALE_SWAP for c in p["palette"]):
        return p, 0
    from beadlib import PALETTE
    byid = {c["id"]: c for c in PALETTE}
    n = 0
    cells = []
    for c in p.get("cells", []):
        cid = c.get("colorId")
        if cid in PALE_SWAP:
            cid = PALE_SWAP[cid]
            n += 1
        cells.append({"x": c["x"], "y": c["y"], "colorId": cid})
    used = {c["colorId"] for c in cells}
    q = dict(p)
    q["cells"] = cells
    q["palette"] = [byid[i] for i in [c["id"] for c in PALETTE] if i in used]
    return q, n


def repair(p, strip=False, drop_below=3, max_gap=5, thicken=True):
    """Return a copy of `p` that is buildable, optionally without its backdrop.

    Order matters: the backdrop goes FIRST, because a full board is trivially
    connected and hides every loose part underneath it. Then loose parts are
    welded on, then the joins that carry weight are widened. The palette is
    rebuilt afterwards so a removed backdrop does not linger in the shopping
    list.
    """
    g, w, h = grid_of(p)
    removed = strip_background(g, w, h) if strip else None
    welded, dropped = make_buildable(g, w, h, drop_below, max_gap)
    fattened = thicken_necks(g, w, h) if thicken else 0
    cells = [{"x": x, "y": y, "colorId": g[y][x]}
             for y in range(h) for x in range(w) if g[y][x] is not None]
    used = {c["colorId"] for c in cells}
    q = dict(p)
    q["cells"] = cells
    q.pop("rows", None)
    q["palette"] = [c for c in p["palette"] if c["id"] in used]
    return q, dict(removed=removed, welded=welded, dropped=dropped,
                   thickened=fattened)
