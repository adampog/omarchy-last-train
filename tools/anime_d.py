"""Scene D, Signal roof, as a hand-painted animation background.

The roof, tank, mast, dishes, camera and far city are the ones in bg_d_signal_roof.py. The renderer writes only
data and anime.py paints it. This file says what is the key light and what glows, and draws the scene's own
things: the dishes as two flat tones with a rim, the tank's seam, ladder and shadow step, a narrow red pool under
the mast with smears, and windows on the nearest towers.

Original art from geometry, procedural shaders and seeded noise. Every colour is a colors.toml value or a mix.

    uv run tools/anime_d.py                    # .cache/anime/d.png at 3440x1440
    uv run tools/anime_d.py --percent 50
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
import bg_d_signal_roof as d  # noqa: E402

P = tk.palette()
RED, PALE = P["accent"], P["foreground"]
WIN_DARK = tk.mix(an.BG, an.SEL, 0.13)
WIN_EDGE = tk.mix(an.BODY, P["blue"], 0.32)
WIN_COOL = tk.mix(an.SEL, P["bright_blue"], 0.4)
WIN_WARM = tk.mix(P["orange"], PALE, 0.3)
DISH_FACE = tk.mix(tk.mix(an.BG, an.SEL, 0.45), P["blue"], 0.1)   # the face turned toward the beacon
DISH_BACK = tk.mix(an.BG, an.SEL, 0.22)
TANK_TOP = tk.mix(tk.mix(an.SEL, RED, 0.45), an.BG, 0.2)
TANK_MID = tk.mix(tk.mix(an.BG, an.SEL, 0.4), P["blue"], 0.08)
HAZE = tk.mix(tk.mix(an.BG, an.SEL, 0.5), P["blue"], 0.2)
DISH_RIM = tk.mix(tk.mix(an.BG, an.SEL, 0.5), RED, 0.3)
TANK_STEP = tk.mix(an.BG, an.SEL, 0.28)                          # the tank's shadow side
TANK_LIT = tk.mix(tk.mix(an.SEL, P["muted"], 0.25), RED, 0.2)
POOL = tk.mix(tk.mix(an.BG, an.SEL, 0.4), RED, 0.4)

rg.BODY, rg.GLASS, rg.ROAD, rg.DECK, rg.STEEL = an.BODY, an.GLASS, an.ROAD, an.PAVE, an.STEEL
an.no_air()

Z = d.ROOF_Z
BEACON = (d.MAST[0], d.MAST[1], d.TOP + 0.2)
BASE = (d.MAST[0], d.MAST[1] - 0.6, Z)


def build(rng):
    facade = city.facade  # the towers' windows are drawn by the painter
    city.facade = lambda name, body, *args, **kw: city.plain(name, body)
    try:
        d.build(rng)
    finally:
        city.facade = facade


def level(pic):
    return pic.solid & (pic.n[..., 2] > 0.7) & (abs(pic.pos[..., 2] - Z) < 0.3)


def dress(pic, rng):
    """Windows on the nearest towers drawn; the farther ones as small marks."""
    upright = an.walls(pic)[0]
    near = upright & ~pic.far & (pic.pos[..., 1] > 60) & (pic.pos[..., 2] > 5)
    an.windows(pic, rng, near, bay=4.0, floor_h=4.2, ground=Z - 8.0, part=0.35, warm=0.08, glass=WIN_DARK,
               edge=WIN_EDGE, lit=WIN_WARM)
    an.marks(pic, rng, upright & pic.far, cool=WIN_COOL, lit=WIN_WARM)


def under(pic, out, rng):
    k = pic.k
    x, y, z = pic.pos[..., 0], pic.pos[..., 1], pic.pos[..., 2]
    ones = np.ones(pic.shape, np.float32)
    # the tank: the top takes the beacon's red as one flat tone, the sides go two steps darker, a seam round the middle
    cyl = pic.solid & (np.hypot(x - d.TANK[0], y - d.TANK[1]) < 4.7) & (z > Z + 0.05) & (z < Z + 3.4)
    top = cyl & (pic.n[..., 2] > 0.5) & (z > Z + 2.9)
    tank = cyl & (pic.n[..., 2] < 0.5)
    shade = tank & (x - d.TANK[0] < -0.8)
    rim = tank & (z > Z + 2.85) & (x - d.TANK[0] > -2.0)
    out = np.where(tank[..., None], pt.rgb(TANK_MID), out)
    out = np.where(shade[..., None], pt.rgb(TANK_STEP), out)
    out = pt.mixa(out, pt.rgb(TANK_LIT), rim * 0.6)
    out = np.where(top[..., None], pt.rgb(TANK_TOP), out)
    seam = tank & (np.abs(z - (Z + 1.55)) < 0.04)
    out = pt.mixa(out, pt.rgb(an.LINE), pt.ink(seam, ones, k, rng, 0.8) * 0.7)
    topedge = (top != np.roll(top, 1, 0)) & (np.abs(z - (Z + 3.1)) < 0.4)
    out = pt.mixa(out, pt.rgb(an.LINE), pt.ink(topedge, ones, k, rng, 0.8) * 0.5)
    # the dishes: a face toward the beacon and a dark back, a lighter rim round each
    for cx, cy, cz in d.DISHES:
        r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2 + ((z - cz) / 0.5) ** 2)
        dish = pic.solid & (r < d.DISH_R * 1.1) & (z > cz - 0.5)
        face = dish & (r < d.DISH_R * 0.78)
        out = np.where(dish[..., None], pt.rgb(DISH_RIM), out)
        out = np.where(face[..., None], pt.rgb(DISH_FACE), out)
        back = face & ((x - cx) * 0.5 - (z - cz) * 0.6 < -0.12)  # one step of shadow on the side away from the beacon
        out = np.where(back[..., None], pt.rgb(DISH_BACK), out)
        edge = dish != np.roll(dish, 1, 1)
        out = pt.mixa(out, pt.rgb(an.LINE), pt.ink(edge, ones, k, rng, 0.7) * 0.6)
    # one flat red pool round the mast and tank foot, reaching forward, with the beacon's smears cut by bands
    roof = level(pic)
    rows = np.arange(pic.shape[0], dtype=np.float32)[:, None]
    cols = np.arange(pic.shape[1], dtype=np.float32)[None, :]
    wob = (pt.noise(pic.shape, (60 * k, 90 * k), rng) - 0.5) * 0.5
    u, v = (x - BASE[0] + 1.0) / 6.0, (y - BASE[1] + 3.0 + wob) / 4.2
    pool = roof & (u * u + v * v < 1)
    out = pt.mixa(out, pt.rgb(POOL), pt.blur(pool.astype(np.float32), 5 * k) * 0.6)
    r0 = pic.at(BASE)[0]
    strip = np.floor(np.log1p(np.maximum(rows - r0, 0) / (18 * k)) * 5).astype(int)
    gap = rng.random(64)[strip % 64] < 0.45
    c0 = pic.at(BASE)[1]
    col = np.clip(1 - np.abs(cols - c0) / (60 * k), 0, 1) * (rows > r0) * (1 - gap) * np.clip(1 - (rows - r0) / (420 * k), 0, 1)
    out = pt.mixa(out, pt.rgb(tk.mix(P["bright_red"], PALE, 0.15)), (pt.blur(col.astype(np.float32), 1.4 * k) * roof * 0.35).astype(np.float32))
    # the bottom strip of the roof a step darker
    out = pt.mixa(out, pt.rgb(an.BG), roof * np.clip((rows - 900 * k) / (400 * k), 0, 1) * 0.65)
    # the far city in depth bands: a haze band at the foot of each row, the nearest row a step darker
    wallf = pic.solid & ~roof & (pic.dist > 100)
    far_ = wallf & pic.far
    out = pt.mixa(out, pt.rgb(HAZE), far_ * np.clip(1 - z / 45.0, 0, 1) * 0.55)
    nearrow = wallf & ~pic.far
    out = pt.mixa(out, pt.rgb(an.BG), nearrow * 0.25)
    return out


LOOK = an.Look(
    name="d", seed=d.SEED, build=build, key_at=(BEACON[0], BEACON[1] - 0.6, BEACON[2]), key_colour=RED,
    rings=(5.0, 9.0, 15.0), amounts=(0.3, 0.14, 0.05),
    glows=(an.Glow(an.within((BEACON[0] - 0.4, BEACON[1] - 0.4, BEACON[2] - 0.4),
                             (BEACON[0] + 0.4, BEACON[1] + 0.4, BEACON[2] + 0.4)), "paper", core=2.5,
                   halo=((12, 1.2), (60, 1.6)), smear=1.6, colour=RED),),
    discs=((BEACON, (2.2, 8.0), (0.5, 0.2), RED),),
    tier_at=(150.0, 300.0, 520.0), veil=((60.0, 0.18), (120.0, 0.34)), wet=level, tint=0.2,
    dress=dress, under=under, wobble=1.8, hesitate=True, cut=3.0, ring_bands=0.5, body=(16.0, 0.34),
    shade_wobble=3.0, air=((130, 0.2), (70, 0.4), (30, 0.58)))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(tk.REPO, ".cache", "anime"))
    ap.add_argument("--percent", type=int, default=100)
    arg = ap.parse_args(argv)
    an.run(LOOK, arg.out, arg.percent)
