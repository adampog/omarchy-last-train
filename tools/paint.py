"""The 2D paint kit for the animated look: numpy helpers that turn flat data renders into a painted picture.

Nothing is loaded but the data renders the scene scripts make themselves. Brush, grain, lines, halos, smears and
rain are all made here from seeded noise. Colours are passed in by the scenes, which take them from colors.toml.
"""

import numpy as np

import bpy


# ---------- files ----------

def load(path):
    """A float image written by a data render, as (rows, columns, 4), top row first."""
    img = bpy.data.images.load(path)
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[::-1].copy()


def save(path, rgb):
    """Write display values (0 to 1, top row first) as an 8-bit PNG."""
    h, w, _ = rgb.shape
    img = bpy.data.images.new("painted", w, h, alpha=False)
    a = np.ones((h, w, 4), np.float32)
    a[..., :3] = np.clip(rgb[::-1], 0, 1)
    img.pixels.foreach_set(a.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    print("wrote", path, flush=True)


# ---------- colour ----------

def rgb(h):
    """'#rrggbb' as display values."""
    return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


def oetf(lin):
    """Linear to display values."""
    lin = np.clip(lin, 0, None)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055).astype(np.float32)


def luma(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def mixa(a, colour, t):
    """Picture a mixed toward a colour by t, a number or a per-pixel field."""
    t = t[..., None] if isinstance(t, np.ndarray) else t
    return a + (colour - a) * t


def screen(a, b):
    return 1 - (1 - a) * (1 - np.clip(b, 0, 1))


def step(lo, hi, x):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


# ---------- filters ----------

def box(a, r, axis):
    r = int(round(r))
    if r < 1:
        return a
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
    n = a.shape[axis]
    hi = [slice(None)] * a.ndim
    lo = [slice(None)] * a.ndim
    hi[axis], lo[axis] = slice(2 * r + 1, 2 * r + 1 + n), slice(0, n)
    return ((c[tuple(hi)] - c[tuple(lo)]) / (2 * r + 1)).astype(np.float32)


def blur(a, sigma, axes=(0, 1)):
    """Close to a Gaussian of this sigma: three box passes each way."""
    r = int(round((np.sqrt(4 * sigma * sigma + 1) - 1) / 2))
    for ax in axes:
        for _ in range(3):
            a = box(a, r, ax)
    return a


def noise(shape, cell, rng):
    """Smooth value noise, 0 to 1; cell is the size of one lump in pixels, (down, across) or one number."""
    cy, cx = cell if isinstance(cell, tuple) else (cell, cell)
    h, w = shape
    g = rng.random((int(h / cy) + 3, int(w / cx) + 3), dtype=np.float32)
    y, x = np.arange(h) / cy, np.arange(w) / cx
    y0, x0 = y.astype(int), x.astype(int)
    fy, fx = y - y0, x - x0
    fy, fx = (fy * fy * (3 - 2 * fy))[:, None], (fx * fx * (3 - 2 * fx))[None, :]
    top = g[np.ix_(y0, x0)] * (1 - fx) + g[np.ix_(y0, x0 + 1)] * fx
    bot = g[np.ix_(y0 + 1, x0)] * (1 - fx) + g[np.ix_(y0 + 1, x0 + 1)] * fx
    return (top * (1 - fy) + bot * fy).astype(np.float32)


def kuwahara(a, r):
    """The brush filter: each pixel takes the mean of whichever of its four quarters is the most even."""
    h = max(1, r // 2)
    grey = luma(a)
    mean = box(box(a, h, 0), h, 1)
    var = box(box(grey * grey, h, 0), h, 1) - box(box(grey, h, 0), h, 1) ** 2
    best, out = None, None
    for dy in (-h, h):
        for dx in (-h, h):
            m = np.roll(mean, (dy, dx), (0, 1))
            v = np.roll(var, (dy, dx), (0, 1))
            if best is None:
                best, out = v, m
            else:
                pick = v < best
                best = np.where(pick, v, best)
                out = np.where(pick[..., None], m, out)
    return out


# ---------- drawn things ----------

def edges(inv_depth, normal, solid, thr_depth=0.02, thr_normal=0.2, parts=False):
    """Where a line belongs: silhouettes (a jump in depth), creases (a turn of the surface) and the skyline.
    Uses the second difference of 1/depth, which is zero across any flat surface however steeply it is seen.
    With `parts`, the lines that run across and the lines that run down are given separately."""
    both = []
    for ax in (0, 1):
        a, b, c = np.roll(inv_depth, 1, ax), inv_depth, np.roll(inv_depth, -1, ax)
        e = np.abs(a + c - 2 * b) > thr_depth * b
        e |= (1 - (normal * np.roll(normal, 1, ax)).sum(-1)) > thr_normal
        e |= solid != np.roll(solid, 1, ax)
        e[0], e[-1], e[:, 0], e[:, -1] = False, False, False, False
        both.append(e)
    return tuple(both) if parts else both[0] | both[1]


def corners(e, k):
    """Where lines meet at an angle: both directions of slope are present close by."""
    g = blur(e.astype(np.float32), 1.5 * k)
    gy, gx = g - np.roll(g, 1, 0), g - np.roll(g, 1, 1)
    a, b, c = blur(gx * gx, 3 * k), blur(gy * gy, 3 * k), blur(gx * gy, 3 * k)
    return ((a * b - c * c) > 0.13 * (a + b) ** 2) & (a + b > 2e-4)


def hesitate(across, down, k, rng):
    """A hand's hesitation at corners: here a line runs a few pixels past the corner, there it stops short."""
    e = across | down
    c = corners(e, k).astype(np.float32)
    choice = noise(e.shape, 70 * k, rng)
    n = max(2, int(round(5 * k)))
    grow = np.zeros(e.shape, bool)
    for ax, own, other in ((1, across, down), (0, down, across)):
        near = other.copy()
        for s in (-1, 1):
            near |= np.roll(other, s, 0) | np.roll(other, s, 1)
        pure = own & ~near  # a run that is all one direction carries on the way it was going
        for s in range(1, n + 1):
            grow |= np.roll(pure, s, ax) | np.roll(pure, -s, ax)
    e = e | (grow & (blur(c, 2.5 * k) > 0.04) & (choice > 0.6))
    return e & ~((blur(c, 1.3 * k) > 0.2) & (choice < 0.34))


def warp(a, dy, dx):
    """The picture with every pixel taken from a little way off: (dy, dx) in pixels, smoothly sampled."""
    h, w = a.shape[:2]
    y = np.clip(np.arange(h, dtype=np.float32)[:, None] + dy, 0, h - 1.001)
    x = np.clip(np.arange(w, dtype=np.float32)[None, :] + dx, 0, w - 1.001)
    y0, x0 = y.astype(int), x.astype(int)
    fy, fx = (y - y0)[..., None], (x - x0)[..., None]
    return ((a[y0, x0] * (1 - fx) + a[y0, x0 + 1] * fx) * (1 - fy)
            + (a[y0 + 1, x0] * (1 - fx) + a[y0 + 1, x0 + 1] * fx) * fy)


def ink(e, weight, k, rng, width=1.0):
    """Edges as a pen line of uneven weight, 0 to 1. `weight` (0 to 1 per pixel) thins and drops far lines."""
    f = blur(e.astype(np.float32) * weight, 1.0 * k * width)
    wobble = noise(e.shape, 46 * k, rng)
    thr = 0.2 + 0.16 * (wobble - 0.5)
    return step(thr, thr + 0.16, f)


def streaks(shape, density, count, length, slope, rng):
    """Rain: thin straight strokes all leaning one way, more of them where `density` is high."""
    h, w = shape
    y, x = rng.integers(0, h, count * 4), rng.integers(0, w, count * 4)
    keep = rng.random(count * 4) < density[y, x]
    dots = np.zeros(shape, np.float32)
    dots[y[keep], x[keep]] = rng.uniform(0.5, 1.0, int(keep.sum()))
    out = np.zeros(shape, np.float32)
    for i in range(int(length)):
        dx = int(round(i * slope))
        fade = 1 - abs(i / length - 0.5) * 1.2  # each stroke is strongest in its middle
        out[i:, dx:] += dots[:h - i, :w - dx] * fade
    return np.clip(out, 0, 1)


def puffs(shape, at, height, width, count, rng, lean=0.35):
    """Steam as a drawn shape: overlapping discs climbing from `at` (row, column), widening and leaning."""
    h, w = shape
    y0, x0 = at
    lo_y, hi_y = max(0, int(y0 - height * 1.3)), min(h, int(y0 + width))
    lo_x, hi_x = max(0, int(x0 - width * 2)), min(w, int(x0 + width * 3 + height * lean))
    yy, xx = np.mgrid[lo_y:hi_y, lo_x:hi_x].astype(np.float32)
    f = np.zeros(yy.shape, np.float32)
    for i in range(count):
        t = (i + rng.uniform(0, 0.6)) / count
        cy = y0 - t * height
        cx = x0 + t * height * lean + rng.uniform(-0.35, 0.35) * width * (0.4 + t)
        r = width * (0.28 + 0.75 * t) * rng.uniform(0.8, 1.15)
        f = np.maximum(f, 1 - np.hypot(yy - cy, xx - cx) / r)
    out = np.zeros(shape, np.float32)
    out[lo_y:hi_y, lo_x:hi_x] = np.clip(f, 0, 1)
    return out


def plume(shape, at, height, width, rng, lean=0.2, toward=-1, points=9):
    """Steam as one tall flat shape cut by hand: straight cuts between a few displaced points, widening as it
    climbs, thinner at the very top and fading to nothing. Returns the shape (0 to 1, with its fade) and the part
    of it on the side toward the light (`toward` is -1 for left, 1 for right)."""
    h, w = shape
    y0, x0 = at
    t = np.linspace(0, 1, points)
    full = (0.3 + 0.9 * t) * np.where(t > 0.7, 1 - 0.8 * (t - 0.7) / 0.3, 1.0)
    centre = x0 + lean * height * t + rng.uniform(-0.3, 0.3, points) * width * t
    left = centre - width * full * rng.uniform(0.65, 1.3, points)
    right = centre + width * full * rng.uniform(0.65, 1.3, points)
    part = left + (right - left) * rng.uniform(0.22, 0.42, points) if toward < 0 else \
        right - (right - left) * rng.uniform(0.22, 0.42, points)
    rows = np.arange(h, dtype=np.float32)
    tt = (y0 - rows) / max(height, 1.0)
    inside = (tt >= 0) & (tt <= 1)
    lo, hi, cut = (np.interp(tt, t, v).astype(np.float32)[:, None] for v in (left, right, part))
    xx = np.arange(w, dtype=np.float32)[None, :]
    body = ((xx > lo) & (xx < hi) & inside[:, None]).astype(np.float32)
    fade = np.clip(1 - tt, 0, 1) ** 1.3 * np.clip(tt * 12, 0, 1)
    lit = body * ((xx < cut) if toward < 0 else (xx > cut))
    return body * fade[:, None].astype(np.float32), lit


def puff(shape, at, width, height, rng, lobes=3, toward=-1, points=11):
    """Steam as a low wide puff cut by hand: a few lobes rising and spreading from `at` (row, column), each a
    ragged many-sided shape. It is never drawn taller than twice its width, so it cannot read as a figure.
    Returns the shape (0 to 1, thinner toward the top), its edge on the side toward the light (`toward` is -1 for
    left, 1 for right) and a smaller inner shape on the side away from it."""
    h, w = shape
    y0, x0 = at
    height = min(height, 2 * width)
    lo_y, hi_y = max(0, int(y0 - height * 1.25)), min(h, int(y0) + 1)
    lo_x, hi_x = max(0, int(x0 - width)), min(w, int(x0 + width))
    out = [np.zeros(shape, np.float32) for _ in range(3)]
    if hi_y <= lo_y or hi_x <= lo_x:
        return out
    yy, xx = np.mgrid[lo_y:hi_y, lo_x:hi_x].astype(np.float32)
    body, inner = np.zeros(yy.shape, bool), np.zeros(yy.shape, bool)
    for i in range(lobes):
        t = i / max(lobes - 1, 1)                      # the first lobe sits on the ground, the last is the top
        side = (i % 2 * 2 - 1) * (0.1 + 0.22 * t)      # they step to one side and the other as they climb
        cx = x0 + width * (side + rng.uniform(-0.06, 0.06))
        cy = y0 - height * (0.2 + 0.5 * t)
        rx, ry = width * (0.3 + 0.18 * t), height * (0.26 + 0.14 * t)
        cut = rng.uniform(0.66, 1.24, points)
        turn = (np.arctan2(yy - cy, xx - cx) / (2 * np.pi) + 0.5) * points
        j = turn.astype(int) % points
        edge = cut[j] + (cut[(j + 1) % points] - cut[j]) * (turn - np.floor(turn))
        reach = np.hypot((xx - cx) / rx, (yy - cy) / ry) / edge
        body |= reach < 1
    d = max(2, int(width * 0.2))
    lit = body & ~np.roll(body, -toward * d, 1)        # a strip of even width along the edge that faces the light
    # the inner tone is the whole shape again, set in from the light and down: one shadow, not a spot per lobe
    inner = np.roll(body, (int(height * 0.16), toward * -2 * d), (0, 1)) & (yy < y0 - 1)
    fade = np.clip(1 - 0.6 * (y0 - yy) / max(height, 1.0), 0, 1)
    for a, part in zip(out, (body * fade, lit, inner & body)):
        a[lo_y:hi_y, lo_x:hi_x] = part
    return out


def grain(a, amount, rng):
    """One even grain over the whole picture, the same everywhere, so it reads as paper."""
    g = rng.standard_normal(a.shape[:2], dtype=np.float32)
    g = (g + blur(g, 0.8) * 1.5) / 2.0
    return a + g[..., None] * amount
