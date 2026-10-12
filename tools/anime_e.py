"""Scene E, Last train, as a hand-painted animation background.

The canal, quay, viaduct, train, towers and camera are the ones in bg_e_last_train.py. The renderer writes only
data and anime.py paints it. This file says what is the key light and what glows, and draws the scene's own
things: windows on the near towers, the bollard's line, and the train's reflection as vertical smears cut by
horizontal bands of dark water.

Original art from geometry, procedural shaders and seeded noise. Every colour is a colors.toml value or a mix.

    uv run tools/anime_e.py                    # .cache/anime/e.png at 3440x1440
    uv run tools/anime_e.py --percent 50
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import city  # noqa: E402
import paint as pt  # noqa: E402
import anime as an  # noqa: E402
import roughs as rg  # noqa: E402
import bg_e_last_train as e  # noqa: E402

P = tk.palette()
RED, ORANGE, PALE = P["accent"], P["orange"], P["foreground"]
WIN_GLASS = tk.mix(an.SEL, P["blue"], 0.1)  # a step lighter than the wall it is in
WIN_COOL = tk.mix(an.SEL, P["bright_blue"], 0.4)
WIN_EDGE = tk.mix(an.SEL, P["blue"], 0.3)
WIN_WARM = tk.mix(ORANGE, PALE, 0.3)
BOLLARD_LIT = tk.mix(tk.mix(an.BG, an.SEL, 0.45), ORANGE, 0.18)

rg.BODY, rg.GLASS, rg.ROAD, rg.DECK, rg.STEEL = an.BODY, an.GLASS, an.ROAD, an.PAVE, an.STEEL
an.no_air()

VY, VZ = e.VY, e.VZ
BOLLARD = ((-4.65, 7.85, 0.0), (-3.95, 8.55, 0.72))
WATER_Z = -1.2


def build(rng):
    facade = city.facade  # the walls' windows are drawn by the painter
    city.facade = lambda name, body, *args, **kw: city.plain(name, body)
    try:
        e.build(rng)
    finally:
        city.facade = facade


def water(pic):
    return pic.solid & (pic.n[..., 2] > 0.7) & (abs(pic.pos[..., 2] - WATER_Z) < 0.3)


def dress(pic, rng):
    """Windows on the four near towers, drawn; marks on the far city."""
    upright = an.walls(pic)[0]
    wall = upright & ~pic.far & (pic.pos[..., 1] > 95)
    an.windows(pic, rng, wall, bay=3.3, floor_h=3.6, ground=2.0, part=0.5, warm=0.1, glass=WIN_GLASS, edge=WIN_COOL,
               lit=WIN_WARM)
    an.marks(pic, rng, upright & pic.far, cool=WIN_COOL, lit=WIN_WARM)


def under(pic, out, rng):
    """The train's light in the water as long vertical smears cut across by bands of plain dark water, and the
    bollard's lit side with a line round its collar."""
    k = pic.k
    rows = np.arange(pic.shape[0], dtype=np.float32)[:, None]
    cols = np.arange(pic.shape[1], dtype=np.float32)[None, :]
    wet = water(pic)
    # bands: rows grouped into strips of uneven height; some strips are dark water with no light in them
    r0 = pic.at((0.0, VY, WATER_Z))[0]
    strip = np.floor(np.log1p(np.maximum(rows - r0, 0) / (14 * k)) * 7).astype(int)
    gap = rng.random(64)[strip % 64] < 0.4
    # columns: smears the width of a window, each its own length
    edges = np.cumsum(rng.uniform(8, 34, 400)) * k
    col_id = np.searchsorted(edges, cols[0])[None, :]
    keep = rng.random(512)[col_id % 512] > 0.4
    near = np.clip(1 - np.abs(rows - r0) / (150 * k), 0, 1) * (1 - gap) * keep
    x0, x1 = pic.at((-21.0, VY, 0))[1], pic.at((31.0, VY, 0))[1]
    inside = ((cols > x0) & (cols < x1)).astype(np.float32)
    smear = (near * inside).astype(np.float32)
    out = pt.mixa(out, pt.rgb(tk.mix(ORANGE, PALE, 0.25)), smear * wet * 0.34)
    # the bollard
    bol = pic.solid & an.inbox(pic.pos, *BOLLARD)
    lit = bol & (pic.n[..., 0] > 0.2)
    out = np.where(lit[..., None], pt.rgb(BOLLARD_LIT), out)
    collar = bol & (np.abs(pic.pos[..., 2] - 0.42) < 0.025)
    return pt.mixa(out, pt.rgb(an.LINE), pt.ink(collar, np.ones(pic.shape, np.float32), k, rng, 0.8) * 0.7)


LOOK = an.Look(
    name="e", seed=e.SEED, build=build, key_at=(5.0, VY - 5.0, VZ + 2.4), key_colour=ORANGE,
    rings=(14.0, 24.0, 34.0), amounts=(0.3, 0.15, 0.06),
    glows=(an.Glow(an.within((-21.0, VY - 2.0, VZ + 1.6), (31.0, VY - 1.0, VZ + 2.9)), halo=((12, 0.9), (70, 1.3)),
                   smear=1.6, colour=ORANGE),
           an.Glow(an.within((-20.7, VY - 2.0, VZ + 0.8), (-19.8, VY - 0.7, VZ + 1.3)), halo=((7, 3.0),), colour=RED,
                   smear=1.0)),
    tier_at=(190.0, 380.0, 600.0), veil=((150.0, 0.3),), wet=water, tint=0.3,
    dress=dress, under=under, wobble=1.4, hesitate=True, cut=3.0, ring_bands=0.6, body=(18.0, 0.18),
    shade_wobble=3.0, air=((130, 0.2), (70, 0.4), (30, 0.58)))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(tk.REPO, ".cache", "anime"))
    ap.add_argument("--percent", type=int, default=100)
    arg = ap.parse_args(argv)
    an.run(LOOK, arg.out, arg.percent)
