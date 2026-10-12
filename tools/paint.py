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

def edges(inv_depth, normal, solid, thr_depth=0.02, thr_normal=0.2):
    """Where a line belongs: silhouettes (a jump in depth), creases (a turn of the surface) and the skyline.
    Uses the second difference of 1/depth, which is zero across any flat surface however steeply it is seen."""
    e = np.zeros(inv_depth.shape, bool)
    for ax in (0, 1):
        a, b, c = np.roll(inv_depth, 1, ax), inv_depth, np.roll(inv_depth, -1, ax)
        e |= np.abs(a + c - 2 * b) > thr_depth * b
        e |= (1 - (normal * np.roll(normal, 1, ax)).sum(-1)) > thr_normal
        e |= solid != np.roll(solid, 1, ax)
    e[0], e[-1], e[:, 0], e[:, -1] = False, False, False, False
    return e


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


def grain(a, amount, rng):
    """One even grain over the whole picture, the same everywhere, so it reads as paper."""
    g = rng.standard_normal(a.shape[:2], dtype=np.float32)
    g = (g + blur(g, 0.8) * 1.5) / 2.0
    return a + g[..., None] * amount
