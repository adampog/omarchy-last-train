"""Scene C, Rider's stop, as a hand-painted animation background.

The road, rails, bike, camera and far city are the ones in bg_c_riders_stop.py. The renderer writes only data and
anime.py paints it. This file says what is the key light and what glows, and draws the scene's own things: a thin
cloud layer over the sky, the sign tower's windows, a cap and a line on the near post, and the lamp's pool.

Original art from geometry, procedural shaders and seeded noise. Every colour is a colors.toml value or a mix.

    uv run tools/anime_c.py                    # .cache/anime/c.png at 3440x1440
    uv run tools/anime_c.py --percent 50
"""

import argparse
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import city  # noqa: E402
import paint as pt  # noqa: E402
import anime as an  # noqa: E402
import roughs as rg  # noqa: E402
import bg_c_riders_stop as c  # noqa: E402

P = tk.palette()
RED, ORANGE, CYAN, PALE = P["accent"], P["orange"], P["cyan"], P["foreground"]
DARK = tk.mix(an.BG, an.SEL, 0.09)  # the bike, one flat dark shape
WIN_DARK = tk.mix(an.BG, an.SEL, 0.13)
WIN_EDGE = tk.mix(an.BODY, P["blue"], 0.32)
WIN_COOL = tk.mix(an.SEL, P["bright_blue"], 0.4)
WIN_WARM = tk.mix(ORANGE, PALE, 0.3)
CLOUD = tk.mix(an.SEL, P["blue"], 0.34)
CLOUD_EDGE = tk.mix(tk.mix(an.SEL, P["blue"], 0.5), ORANGE, 0.12)
CAP = tk.mix(an.BODY, P["blue"], 0.28)

# the scene's own local colours, lifted from near-black to painted blues; its air is painted, not rendered
rg.BODY, rg.GLASS, rg.ROAD, rg.DECK, rg.STEEL, rg.BIKE = an.BODY, an.GLASS, an.ROAD, an.PAVE, an.STEEL, DARK
an.no_air()

Z = c.ROAD_Z
BIKE_BOX = ((-3.7, 4.2, Z + 0.02), (-1.2, 7.1, Z + 1.7))
POST = (-1.95, 2.65)
TOWER = ((11.0, 239.0, 0.0), (27.0, 263.0, 62.0))


def build(rng):
    facade = city.facade  # the towers' windows are drawn by the painter
    city.facade = lambda name, body, *args, **kw: city.plain(name, body)
    try:
        c.build()
    finally:
        city.facade = facade


def level(pic):
    return pic.solid & (pic.n[..., 2] > 0.7) & (abs(pic.pos[..., 2] - Z) < 0.3)


def dress(pic, rng):
    """The near row: drawn uneven windows, few lit, most dark. The middle row and the sign tower: a few marks. The far
    rows: none."""
    upright = an.walls(pic)[0]
    nearest = upright & (pic.dist < 205) & ~an.inbox(pic.pos, *TOWER)
    an.windows(pic, rng, nearest, bay=3.6, floor_h=4.0, ground=3.0, part=0.3, warm=0.08, glass=WIN_DARK,
               edge=WIN_EDGE, lit=WIN_WARM)
    middle = upright & (pic.dist >= 205) & (pic.dist < 330) & ~an.inbox(pic.pos, *TOWER)
    an.marks(pic, rng, middle, bay=4.6, floor_h=4.2, ground=2.0, part=0.25, warm=0.2, cool=WIN_COOL, lit=WIN_WARM)
    tower = an.inbox(pic.pos, *TOWER) & (np.abs(pic.n[..., 1]) > 0.5)
    an.marks(pic, rng, tower, bay=3.4, floor_h=3.6, ground=2.0, part=0.5, warm=0.22, cool=WIN_COOL, lit=WIN_WARM)


def under(pic, out, rng):
    """A dim pool on the road ahead of the lamp, the sky's thin cloud, and a light line down the post's cap."""
    k = pic.k
    a = math.radians(26.0)
    at = (-2.4 + 2.6 * math.sin(a), 5.6 + 2.6 * math.cos(a))
    u = (pic.pos[..., 0] - at[0]) * math.sin(a) + (pic.pos[..., 1] - at[1]) * math.cos(a)
    v = (pic.pos[..., 0] - at[0]) * math.cos(a) - (pic.pos[..., 1] - at[1]) * math.sin(a)
    pool = ((u / 1.5) ** 2 + (v / 0.6) ** 2 < 1) & level(pic)
    out = pt.mixa(out, pt.rgb(tk.mix(P["muted"], PALE, 0.4)), pool * 0.2)
    # thin cloud: two long flat bands in the sky, a paler body with a warmer lower edge, lying behind the far city
    sky = ~pic.solid & ~pic.far
    y = np.arange(pic.shape[0], dtype=np.float32)[:, None]
    for lo, hi, cover, amount in ((300, 360, 0.42, 0.22),):
        band = pt.step(lo * k, (lo + 30) * k, y) * (1 - pt.step((hi - 30) * k, hi * k, y))
        n = pt.noise(pic.shape, (16 * k, 260 * k), rng)
        body = pt.step(1 - cover, 1 - cover + 0.03, n * (0.55 + 0.45 * band)) * (band > 0.02)
        under_edge = body * (1 - np.roll(body, int(-9 * k), 1))  # lit on the city side, to the right
        out = pt.mixa(out, pt.rgb(CLOUD), pt.blur(body, 0.8 * k) * amount * sky)
        out = pt.mixa(out, pt.rgb(CLOUD_EDGE), pt.blur(under_edge, 0.8 * k) * amount * 1.2 * sky)
    # the midground a step darker, so the city's glow owns the picture
    near_ground = pic.solid & ~pic.flat & (pic.dist < 150)
    out = pt.mixa(out, pt.rgb(an.BG), near_ground * 0.28)
    # the near row of city a step darker than the rows behind it
    row_near = pic.solid & (pic.dist > 150) & (pic.dist < 205) & ~pic.flat
    out = pt.mixa(out, pt.rgb(an.BG), row_near * 0.55)
    # the city's warm light in the road's right half: broad faint smears, lower in tone than the red column
    rows = np.arange(pic.shape[0], dtype=np.float32)[:, None]
    cols = np.arange(pic.shape[1], dtype=np.float32)[None, :]
    W = pic.shape[1]
    hz = pic.at((15.0, 400.0, Z))[0]
    strip = np.floor(np.maximum(rows - hz, 0) / (15 * k)).astype(int)
    gap = rng.random(64)[strip % 64] < 0.35
    edges = np.cumsum(rng.uniform(70, 220, 300)) * k
    cid = np.searchsorted(edges, cols[0])[None, :]
    keep = rng.random((64, 300))[strip % 64, cid % 300] > 0.45
    fade = np.clip((cols - 0.58 * W) / (0.2 * W), 0, 1) * np.clip(1 - np.maximum(rows - hz, 0) / (300 * k), 0, 1)
    sm = (keep * (1 - gap) * fade).astype(np.float32)
    wide = sm.copy()
    for sh in range(6, int(70 * k) + 1, 6):
        wide = np.maximum(wide, np.maximum(np.roll(sm, sh, 1), np.roll(sm, -sh, 1)))
    field = pt.blur(wide, 2.0 * k)
    out = pt.mixa(out, pt.rgb(tk.mix(ORANGE, an.SEL, 0.35)), (field * level(pic) * 0.24).astype(np.float32))
    # the post: a cap a step lighter, and a line a third of the way down
    row, col = pic.at((POST[0], POST[1], Z + 0.2))
    post = pic.solid & an.inbox(pic.pos, (POST[0] - 0.12, POST[1] - 0.12, Z), (POST[0] + 0.12, POST[1] + 0.12, Z + 0.56))
    cap = post & (pic.pos[..., 2] > Z + 0.5)
    out = pt.mixa(out, pt.rgb(CAP), cap * 0.9)
    seam = post & (np.abs(pic.pos[..., 2] - (Z + 0.33)) < 0.012)
    return pt.mixa(out, pt.rgb(an.LINE), pt.ink(seam, np.ones(pic.shape, np.float32), k, rng, 0.8) * 0.6)


def over(pic, out, rng):
    """The blue light behind the bike drawn as a thin edge down its left side; the lamp a dark disc with a rim line and a
    thin bright edge on its city side."""
    k = pic.k
    rows = np.arange(pic.shape[0], dtype=np.float32)[:, None]
    cols = np.arange(pic.shape[1], dtype=np.float32)[None, :]
    cx, cy = 1372 * k / 1.0 * 0.5 * 2, 608 * k
    r = np.hypot((cols - cx) / (50 * k), (rows - cy) / (41 * k))
    disc = (r < 1.0).astype(np.float32)
    rim = ((r > 0.88) & (r < 1.0)).astype(np.float32)
    out = pt.mixa(out, pt.rgb(DARK), pt.blur(disc, 0.5 * k) * 0.97)
    out = pt.mixa(out, pt.rgb(an.LINE), pt.blur(rim, 0.5 * k) * 0.6)
    edge = ((r > 0.93) & (r < 1.0) & (cols > cx + 0.4 * 50 * k)).astype(np.float32)
    out = pt.mixa(out, pt.rgb(tk.mix(P["bright_blue"], PALE, 0.4)), pt.blur(edge, 0.6 * k) * 0.7)
    # the instrument dot on the handlebar goes: the bar's dark shape closes over it
    dot = np.hypot((cols - 1320 * k) / (14 * k), (rows - 492 * k) / (10 * k)) < 1
    out = pt.mixa(out, pt.rgb(DARK), pt.blur(dot.astype(np.float32), 0.8 * k) * 0.97)
    # the nearest block at right: one lit top-edge line and one drawn vent
    x, y, z = pic.pos[..., 0], pic.pos[..., 1], pic.pos[..., 2]
    blk = pic.solid & ~pic.far & (np.abs(y - 190.5) < 0.6) & (np.abs(pic.n[..., 1]) > 0.5) & (x > 25) & (x < 80)
    zt = z[blk].max()
    xs = x[blk]
    edge_t = blk & (z > zt - 0.45)
    out = pt.mixa(out, pt.rgb(tk.mix(ORANGE, an.SEL, 0.45)), pt.blur(edge_t.astype(np.float32), 0.6 * k) * 0.8)
    vx0 = xs.min() + (xs.max() - xs.min()) * 0.3
    (r1, c1), (r0, c0) = pic.at((vx0 + 3.2, 190.5, zt)), pic.at((vx0, 190.5, zt + 1.7))
    vent = ((rows >= r0) & (rows < r1) & (cols >= c0) & (cols < c1)).astype(np.float32)
    vedge = ((vent > 0) & ((rows < r0 + 2 * k) | (cols < c0 + 2 * k))).astype(np.float32)
    out = pt.mixa(out, pt.rgb(DARK), pt.blur(vent, 0.5 * k) * 0.95)
    out = pt.mixa(out, pt.rgb(tk.mix(ORANGE, an.SEL, 0.45)), pt.blur(vedge, 0.5 * k) * 0.5)
    s = max(1, int(round(3 * pic.k)))
    edge = pic.flat & ~np.roll(pic.flat, s, 1)
    return pt.mixa(out, pt.rgb(tk.mix(P["blue"], P["bright_blue"], 0.5)), pt.blur(edge.astype(np.float32), 0.6 * pic.k) * 0.8)


LOOK = an.Look(
    name="c", seed=c.SEED, build=build, key_at=(-9.0, 1.0, Z + 3.5), key_colour=P["blue"],
    rings=(9.0, 15.0, 24.0), amounts=(0.3, 0.17, 0.07),
    glows=(an.Glow(an.within((12.9, 239.0, 43.9), (17.1, 240.6, 56.1)), halo=((16, 1.2), (90, 2.4)), colour=RED),),
    discs=(((52.0, 225.0, 30.0), (45.0, 100.0), (0.3, 0.18), ORANGE),),
    tier_at=(205.0, 330.0, 520.0), veil=((90.0, 0.2), (160.0, 0.36)), wet=level,
    flats=((*BIKE_BOX, DARK),), dress=dress, under=under, over=over, wobble=1.6, hesitate=True, cut=3.0,
    ring_bands=0.5, body=(12.0, 0.16), shade_wobble=3.0, air=((130, 0.2), (70, 0.4), (30, 0.58)))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(tk.REPO, ".cache", "anime"))
    ap.add_argument("--percent", type=int, default=100)
    arg = ap.parse_args(argv)
    an.run(LOOK, arg.out, arg.percent)
