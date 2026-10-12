"""Scene G, The counter, as a hand-painted animation background.

The alley, walls, counter, lanterns and camera are the ones in bg_g_the_counter.py. The renderer writes only data
and anime.py paints it. This file says what is the key light and what glows, and draws the scene's own things:
the lantern light on the right wall as one flat warm tone with a darker step, the counter's front (shelf line and
cloth) and a low puff of steam off the kettle.

Original art from geometry, procedural shaders and seeded noise. Every colour is a colors.toml value or a mix.

    uv run tools/anime_g.py                    # .cache/anime/g.png at 3440x1440
    uv run tools/anime_g.py --percent 50
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import paint as pt  # noqa: E402
import anime as an  # noqa: E402
import roughs as rg  # noqa: E402
import bg_g_the_counter as g  # noqa: E402

P = tk.palette()
RED, ORANGE, CYAN, PALE = P["accent"], P["orange"], P["cyan"], P["foreground"]
WARM_WALL = tk.mix(tk.mix(an.BG, an.SEL, 0.6), ORANGE, 0.26)     # the wall where the lanterns reach
WARM_STEP = tk.mix(tk.mix(an.BG, an.SEL, 0.45), ORANGE, 0.1)         # the step down beyond it
COUNTER = tk.mix(tk.mix(an.BG, an.SEL, 0.35), P["brown"], 0.3)
COUNTER_LIT = tk.mix(COUNTER, ORANGE, 0.28)
SHELF = tk.mix(an.BG, P["brown"], 0.35)
CLOTH = tk.mix(tk.mix(an.SEL, P["blue"], 0.3), ORANGE, 0.08)
LEFT_WALL = tk.mix(tk.mix(an.BG, an.SEL, 0.22), P["blue"], 0.06)
LEFT_DARK = tk.mix(an.BG, an.SEL, 0.02)
POOL = tk.mix(tk.mix(an.BG, an.SEL, 0.4), ORANGE, 0.3)
HAZE = tk.mix(tk.mix(an.BG, an.SEL, 0.55), P["blue"], 0.1)
STEAM = tk.mix(tk.mix(an.SEL, P["muted"], 0.42), ORANGE, 0.3)
STEAM_LIT = tk.mix(tk.mix(PALE, ORANGE, 0.4), P["muted"], 0.3)

rg.BODY, rg.GLASS, rg.ROAD, rg.DECK, rg.STEEL = an.BODY, an.GLASS, an.ROAD, an.PAVE, an.STEEL
an.no_air()

G_AT = (2.35, 13.25, 2.3)
KETTLE = (2.9, 13.9, 1.3)
COUNTER_BOX = ((1.2, 13.6, 0.0), (3.8, 14.4, 1.0))
FRONT_Y = 13.6


def build(rng):
    g.build(rng)


def right_wall(pic):
    return pic.solid & (pic.pos[..., 0] > 3.7) & (pic.n[..., 0] < -0.5) & (pic.pos[..., 1] < 60)


def left_wall(pic):
    return pic.solid & (pic.pos[..., 0] < -4.2) & (pic.n[..., 0] > 0.5) & (pic.pos[..., 1] < 60)


def ground(pic):
    return pic.solid & (pic.n[..., 2] > 0.7) & (pic.pos[..., 2] < 0.1) & (pic.pos[..., 1] < 60)


def knots(v, pts):
    """A straight-segment profile through (v, value) points."""
    xs, ys = zip(*pts)
    return np.interp(v, xs, ys).astype(np.float32)


def under(pic, out, rng):
    """The right wall: warm field ending two thirds up, edge in straight segments with a ragged awning cut.
    The left wall: drawn shutter, downpipe, bracket, drain. The floor: a warm pool with smeared lanterns.
    The counter's front, and the lantern paper with a bright centre."""
    k = pic.k
    x, y, z = pic.pos[..., 0], pic.pos[..., 1], pic.pos[..., 2]
    ones = np.ones(pic.shape, np.float32)
    rows = np.arange(pic.shape[0], dtype=np.float32)[:, None]
    cols = np.arange(pic.shape[1], dtype=np.float32)[None, :]
    wall = right_wall(pic)
    wob = (pt.noise(pic.shape, (200 * k, 300 * k), rng) - 0.5) * 0.12  # nearly straight: a hand-cut cel edge
    # half width of the lit field along the alley, by height: a few straight segments, then a ragged top
    half = knots(z, ((0, 6.8), (6.0, 6.8), (10.0, 4.6), (14.5, 3.4), (16.0, 0.4)))
    dy = np.abs(y - G_AT[1] - 1.2)
    cut = np.where((z > 3.4) & (z < 4.6), 1.0, 0.0) * (np.abs(y - 12.0) < 1.6) * 0.0  # the awning's own shadow is the geometry
    near = wall & (dy + wob < half * 0.62)
    step = wall & (dy + wob < half) & ~near
    fade = np.clip((rows - 160 * k) / (480 * k), 0, 1)
    out = pt.mixa(out, pt.rgb(WARM_WALL), near * 0.6 * fade)
    out = pt.mixa(out, pt.rgb(WARM_STEP), step * 0.45 * fade)
    # the left wall: one flat dark tone, then the drawn things (nothing soft and round)
    lw = left_wall(pic)
    out = pt.mixa(out, pt.rgb(LEFT_WALL), lw * 0.85 * np.clip((rows - 60 * k) / (500 * k), 0, 1))
    shutter = lw & (y > 8.6) & (y < 10.8) & (z > 0.0) & (z < 2.4)
    slats = shutter & (np.mod(z, 0.16) < 0.06)
    out = pt.mixa(out, pt.rgb(LEFT_DARK), shutter * 0.3)
    out = pt.mixa(out, pt.rgb(LEFT_DARK), slats * 0.95)
    out = pt.mixa(out, pt.rgb(an.LINE), pt.ink(slats, ones, k, rng, 0.8) * 0.8)
    pipe = lw & (np.abs(y - 7.8) < 0.09)
    brk = lw & (y > 11.2) & (y < 12.4) & (z > 2.2) & (z < 2.9)
    brk_arm = lw & (y > 11.2) & (y < 12.4) & (np.abs(z - 2.9) < 0.05)
    out = pt.mixa(out, pt.rgb(LEFT_DARK), (pipe | brk) * 0.9)
    edges = (shutter != np.roll(shutter, 1, 1)) | (pipe != np.roll(pipe, 1, 1)) | (brk != np.roll(brk, 1, 0)) | (
        brk != np.roll(brk, 1, 1)) | brk_arm
    out = pt.mixa(out, pt.rgb(an.LINE), pt.ink(edges, ones, k, rng, 0.8) * 0.6)
    drain = ground(pic) & (x < -2.0) & (x > -3.0) & (y > 4.0) & (y < 6.0)
    out = pt.mixa(out, pt.rgb(an.LINE), pt.ink(drain != np.roll(drain, 1, 0), ones, k, rng, 0.8) * 0.6)
    # the floor: darker near strip, then one warm pool under the counter with the lanterns smeared in it
    gd = ground(pic)
    near_strip = gd & (y < 6.0)
    out = pt.mixa(out, pt.rgb(an.BG), near_strip * 0.4)
    pw = (pt.noise(pic.shape, (50 * k, 80 * k), rng) - 0.5) * 0.7
    pool = gd & (((x - 2.3 + pw) / 2.6) ** 2 + ((y - 11.0 + pw) / 2.4) ** 2 < 1)
    out = pt.mixa(out, pt.rgb(POOL), pt.blur(pool.astype(np.float32), 5 * k) * 0.4)
    r0 = pic.at((2.3, 13.6, 0.0))[0]
    strip = np.floor(np.log1p(np.maximum(rows - r0, 0) / (14 * k)) * 4).astype(int)
    gap = rng.random(64)[strip % 64] < 0.4
    smear = np.zeros(pic.shape, np.float32)
    sid = strip % 64
    for i, (lx, power, reach_px) in enumerate(((1.45, 0.4, 560), (2.05, 0.4, 620), (2.65, 0.3, 330), (3.25, 0.4, 480))):
        c = pic.at((lx, 13.25, 0.0))[1]
        width = rng.uniform(12, 26, 64)[sid] * k
        shift = rng.uniform(-10, 10, 64)[sid] * k
        short = rng.uniform(0.5, 1.0, 64)[sid]
        m = (np.abs(cols - c - shift) < width) * (rows > r0) * (1 - gap * 0.9) * np.clip(1.2 - (rows - r0) / (reach_px * k * short), 0, 1)
        smear = np.maximum(smear, pt.blur(m.astype(np.float32), 1.6 * k) * (power / 0.4))
    out = pt.mixa(out, pt.rgb(tk.mix(ORANGE, PALE, 0.25)), (smear * gd * 0.55).astype(np.float32))
    # the alley's far end: one faint paler haze band at the foot of the end wall
    endw = pic.solid & (y > 60) & (pic.n[..., 1] < -0.5) & (z < 6.0)
    out = pt.mixa(out, pt.rgb(HAZE), (endw * np.clip(1 - z / 6.0, 0, 1) * 0.5).astype(np.float32))
    # the left half's wet field one step darker and flat
    out = pt.mixa(out, pt.rgb(an.BG), (gd & (x < 0.0)) * 0.18)
    # the counter's front
    front = pic.solid & (np.abs(y - FRONT_Y) < 0.06) & (pic.n[..., 1] < -0.5) & an.inbox(
        pic.pos, (1.1, 13.4, -0.1), (3.9, 13.7, 1.05))
    out = np.where(front[..., None], pt.mixa(pt.rgb(COUNTER), pt.rgb(COUNTER_LIT), 0.5), out)
    shelf = front & (np.abs(z - 0.64) < 0.035)
    out = np.where(shelf[..., None], pt.rgb(SHELF), out)
    cloth = front & (pic.pos[..., 0] > 1.85) & (pic.pos[..., 0] < 2.55) & (z > 0.22) & (z < 1.0)
    out = np.where(cloth[..., None], pt.rgb(CLOTH), out)
    edge = (cloth != np.roll(cloth, 1, 1)) | (shelf != np.roll(shelf, 1, 0))
    # lantern paper: bright centre, orange edge
    for k_i, lx in enumerate((1.45, 2.05, 2.65, 3.25)):
        paper = pic.solid & an.inbox(pic.pos, (lx - 0.18, 13.05, 2.08), (lx + 0.18, 13.45, 2.52)) & (pic.n[..., 1] < -0.2)
        r = np.maximum(np.abs(x - lx) / 0.17, np.abs(z - 2.3) / 0.21)
        w = np.clip(1.25 - r * 1.2, 0, 1)
        base = RED if k_i == 2 else ORANGE
        centre = tk.mix(base, PALE, 0.3 if k_i == 2 else 0.55)
        col3 = pt.rgb(base) + (pt.rgb(centre) - pt.rgb(base)) * w[..., None]
        out = np.where(paper[..., None], col3, out)
    return pt.mixa(out, pt.rgb(an.LINE), pt.ink(edge, ones, k, rng, 0.8) * 0.7)


def thin_rain(pic):
    """A third of the rain over the lanterns and the warm body round the stall."""
    rows = np.arange(pic.shape[0], dtype=np.float32)[:, None]
    cols = np.arange(pic.shape[1], dtype=np.float32)[None, :]
    r, c = pic.at((2.5, 13.25, 1.6))
    d = np.hypot((cols - c) / (520 * pic.k), (rows - r) / (400 * pic.k))
    return np.clip(1.15 - d, 0, 1) * 0.67


def over(pic, out, rng):
    """Steam off the kettle: a thin veil, low and wide."""
    return an.steam(pic, out, rng, (2.9, 13.9, 1.35), (0.5, 0.9), STEAM_LIT, opacity=0.4)


LOOK = an.Look(
    name="g", seed=g.SEED, build=build, key_at=(2.3, 12.6, 1.9), key_colour=ORANGE,
    rings=(2.6, 4.6, 7.5), amounts=(0.3, 0.1, 0.03),
    glows=(an.Glow(an.within((1.2, 13.0, 2.0), (3.5, 13.5, 2.6)), "paper", core=9.0, halo=((30, 0.35),), smear=1.4),
           an.Glow(an.within((-4.6, 17.9, 0.3), (-4.3, 19.0, 1.8)), halo=((14, 0.8), (60, 1.2)), smear=1.0)),
    discs=((G_AT, (1.6, 4.0), (0.3, 0.14), ORANGE),),
    tier_at=(500.0, 700.0, 900.0), veil=((28.0, 0.14), (50.0, 0.28)), tint=0.4, under=under, over=over, rain_thin=thin_rain,
    rain=0.45, rain_colour=tk.mix(PALE, ORANGE, 0.3), stars=False, wobble=1.4, hesitate=True, cut=3.0,
    ring_bands=0.5, body=(4.0, 0.1), shade_wobble=3.0)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(tk.REPO, ".cache", "anime"))
    ap.add_argument("--percent", type=int, default=100)
    arg = ap.parse_args(argv)
    an.run(LOOK, arg.out, arg.percent)
