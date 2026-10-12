"""Scene F, Tunnel mouth, as a hand-painted animation background.

The road, hill, portal, strips, lip lamps and camera are the ones in bg_f_tunnel_mouth.py. The renderer writes only
data and anime.py paints it. This file says what is the key light and what glows, and draws the scene's own things:
the wall in three depth tones with a drain seam and two drawn marks, the mouth's warm far end as a soft gradient,
a drawn arch over the mouth, the mouth's light on the wet road as vertical smears cut by bands, and windows on the
towers above.

Original art from geometry, procedural shaders and seeded noise. Every colour is a colors.toml value or a mix.

    uv run tools/anime_f.py                    # .cache/anime/f.png at 3440x1440
    uv run tools/anime_f.py --percent 50
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
import bg_f_tunnel_mouth as f  # noqa: E402

P = tk.palette()
RED, ORANGE, PALE = P["accent"], P["orange"], P["foreground"]
WARM = P["orange"]
WIN_GLASS = tk.mix(an.SEL, P["blue"], 0.1)
WIN_COOL = tk.mix(an.SEL, P["bright_blue"], 0.4)
WIN_EDGE = tk.mix(an.SEL, P["blue"], 0.3)
WIN_WARM = tk.mix(ORANGE, PALE, 0.3)
WALL_NEAR = tk.mix(tk.mix(an.BG, an.SEL, 0.16), ORANGE, 0.05)   # the pier: darkest, nearest
WALL_MID = tk.mix(tk.mix(an.BG, an.SEL, 0.3), P["blue"], 0.05)  # the mid wall
WALL_FAR = tk.mix(tk.mix(an.BG, an.SEL, 0.4), P["blue"], 0.12)  # the far wall, lighter and cooler with distance
INNER_A = tk.mix(tk.mix(an.BG, an.SEL, 0.4), ORANGE, 0.22)      # the tunnel's inner walls, lit
INNER_B = tk.mix(tk.mix(an.BG, an.SEL, 0.25), ORANGE, 0.08)     # and the shadow step
FAR_END = tk.mix(tk.mix(ORANGE, PALE, 0.3), WARM, 0.3)
HOUSING = tk.mix(an.BG, an.SEL, 0.18)

rg.BODY, rg.GLASS, rg.ROAD, rg.DECK, rg.STEEL = an.BODY, an.GLASS, an.ROAD, an.PAVE, an.STEEL
an.no_air()

F_AT = (-10.4, 46.0, 3.5)
MOUTH = ((-15.4, 46.0, 0.0), (-5.4, 46.0, 7.0))
PIER = ((-24.0, 41.0, 0.0), (-18.5, 46.0, 9.5))
HOUSE = ((-17.6, 45.2, 3.2), (-16.9, 46.0, 3.9))
BRACKET = ((-3.0, 44.6, 5.0), (-0.8, 46.0, 6.0))


def build(rng):
    facade = city.facade  # the towers' windows are drawn by the painter
    city.facade = lambda name, body, *args, **kw: city.plain(name, body)
    try:
        f.build(rng)
    finally:
        city.facade = facade


def road(pic):
    return pic.solid & (pic.n[..., 2] > 0.7) & (pic.pos[..., 2] < 0.3) & (pic.pos[..., 1] > 8)


def dress(pic, rng):
    """Windows on the two towers over the hill; marks on the far city."""
    upright = an.walls(pic)[0]
    near = upright & ~pic.far & (pic.pos[..., 2] > 14)
    an.windows(pic, rng, near, bay=3.2, floor_h=3.6, ground=15.0, part=0.45, warm=0.08, glass=WIN_GLASS,
               edge=WIN_EDGE, lit=WIN_WARM)
    an.marks(pic, rng, upright & pic.far, cool=WIN_COOL, lit=WIN_WARM)


def under(pic, out, rng):
    k = pic.k
    x, y, z = pic.pos[..., 0], pic.pos[..., 1], pic.pos[..., 2]
    ones = np.ones(pic.shape, np.float32)
    rows = np.arange(pic.shape[0], dtype=np.float32)[:, None]
    cols = np.arange(pic.shape[1], dtype=np.float32)[None, :]
    front = pic.solid & (pic.n[..., 1] < -0.5) & (z < 14.05)
    # three depth tones on the wall: far wall (cool, light), mid wall, near pier (dark)
    far_w = front & (y > 57)
    mid_w = front & (y > 45.9) & (y <= 57)
    pier = front & an.inbox(pic.pos, (PIER[0][0], PIER[0][1], 0), (PIER[1][0], 46.01, PIER[1][2]))
    out = np.where(far_w[..., None], pt.rgb(WALL_FAR), out)
    out = np.where(mid_w[..., None], pt.rgb(WALL_MID), out)
    out = np.where(pier[..., None], pt.rgb(WALL_NEAR), out)
    # the wall fades into haze toward its top edge: a wobbling band, not a hard cut
    top = pic.at((0.0, 46.0, 14.0))[0]
    wob = (pt.noise(pic.shape, (30 * k, 300 * k), rng) - 0.5) * 70 * k
    edge = np.clip(1 - np.abs(rows - top + wob) / (110 * k), 0, 1)
    hz = pt.rgb(tk.mix(tk.mix(an.BG, an.SEL, 0.55), P["blue"], 0.18))
    out = pt.mixa(out, hz, np.where(rows - wob < top + 60 * k, edge, 0) * front * 0.5)
    # a drain seam down the mid wall right of the mouth, and a seam line at the pier's edge
    seam = mid_w & (np.abs(x - 12.0) < 0.07) | (pier & (np.abs(x - PIER[1][0] + 0.12) < 0.06))
    out = pt.mixa(out, pt.rgb(an.LINE), pt.ink(seam, ones, k, rng, 0.8) * 0.6)
    # two marks: a lamp housing (dark box with a lit slot) and a sign bracket (arm and plate)
    house = pic.solid & an.inbox(pic.pos, *HOUSE)
    out = np.where(house[..., None], pt.rgb(HOUSING), out)
    slot = house & (np.abs(z - 3.55) < 0.07) & (pic.n[..., 1] < -0.5)
    out = np.where(slot[..., None], pt.rgb(WIN_WARM), out)
    br = pic.solid & an.inbox(pic.pos, *BRACKET)
    out = np.where(br[..., None], pt.rgb(HOUSING), out)
    edges = (house != np.roll(house, 1, 1)) | (br != np.roll(br, 1, 1)) | (br != np.roll(br, 1, 0))
    out = pt.mixa(out, pt.rgb(an.LINE), pt.ink(edges, ones, k, rng, 0.8) * 0.7)
    # the mouth's far end: a soft warm gradient, brightest low and in the middle, not a flat field
    (t0, l0), (b0, r0) = pic.at((-15.4, 46.0, 7.0)), pic.at((-5.4, 46.0, 0.0))
    mouth = (rows > t0) & (rows < b0) & (cols > l0) & (cols < r0) & (pic.dist > 150)
    cx = (l0 + r0) / 2
    g = np.clip(1 - np.abs(cols - cx) / ((r0 - l0) * 0.7), 0, 1) * np.clip((rows - t0) / ((b0 - t0) * 0.8), 0.25, 1)
    out = np.where(mouth[..., None], (pt.rgb(INNER_B) + (pt.rgb(FAR_END) - pt.rgb(INNER_B)) * (g[..., None] * 0.9 + 0.1)), out)
    # a drawn arch over the mouth: one line along the portal's top and one step below it
    lintel = front & (np.abs(z - 7.8) < 0.07) & (x > -16.3) & (x < -4.5)
    step = front & (z > 7.0) & (z < 7.8) & (x > -16.3) & (x < -4.5) & (y < 46.01)
    out = pt.mixa(out, pt.rgb(WALL_NEAR), step * 0.6)
    out = pt.mixa(out, pt.rgb(an.LINE), pt.ink(lintel, ones, k, rng, 0.8) * 0.7)
    # the dome's edge drawn as an arch: one wobbling line and a lighter step inside it
    ac, ar = pic.at((-5.4, 46.0, 0.0))[1] + 246 * k * 0.5 * 2 / 2, 0
    ax = cols - (1736 * k / 1.0) * 1.0
    ay = rows - 1020 * k
    inside = ((ax / (246 * k)) ** 2 + (ay / (470 * k)) ** 2 < 1) & (rows < 1020 * k) & (cols > pic.at((-5.4, 46.0, 0.0))[1] + 4)
    rim = inside & ~(((ax / (236 * k)) ** 2 + (ay / (452 * k)) ** 2) < 1)
    out = pt.mixa(out, pt.rgb(WALL_NEAR), rim * 0.0)  # the dome is dropped: no line, the shade is painted flat
    # the mouth's light on the wet road: vertical smears cut by bands of plain dark road
    wet = road(pic)
    r0r = pic.at((-10.4, 46.0, 0.0))[0]
    strip = np.floor(np.log1p(np.maximum(rows - r0r, 0) / (16 * k)) * 6).astype(int)
    gap = rng.random(64)[strip % 64] < 0.4
    edges_c = np.cumsum(rng.uniform(5, 18, 600)) * k
    col_id = np.searchsorted(edges_c, cols[0])[None, :]
    keep = rng.random(512)[col_id % 512] > 0.5
    reach = np.clip(1 - np.abs(cols - cx) / (520 * k), 0, 1) ** 0.7 * np.clip(1 - (rows - r0r) / (700 * k), 0, 1)
    smear = (np.clip(rows - r0r, 0, None) > 0) * (1 - gap * 0.7) * keep * reach
    smear = pt.blur(smear.astype(np.float32), 1.6 * k)
    out = pt.mixa(out, pt.rgb(tk.mix(ORANGE, PALE, 0.2)), (smear * wet * 0.4).astype(np.float32))
    return out


LOOK = an.Look(
    name="f", seed=f.SEED, build=build, key_at=(-10.4, 49.0, 5.0), key_colour=ORANGE,
    rings=(13.0, 28.0, 52.0), amounts=(0.42, 0.25, 0.1),
    glows=(an.Glow(an.within((-14.0, 50.0, 6.8), (-7.0, 201.0, 7.1)), "tube", halo=((24, 1.0), (110, 2.2)), smear=1.5,
                   colour=ORANGE),
           an.Glow(an.within((-14.2, 45.0, 7.9), (-6.6, 45.8, 8.5)), "paper", core=1.5, halo=((9, 2.5),), colour=RED)),
    discs=((F_AT, (9.0, 18.0), (0.34, 0.16), ORANGE),),
    tier_at=(250.0, 450.0, 650.0), veil=((80.0, 0.2), (130.0, 0.36)), tint=0.35, wet=road, dress=dress, under=under,
    rain=0.45, rain_colour=tk.mix(PALE, ORANGE, 0.3), wobble=1.6, hesitate=True, cut=3.0, ring_bands=0.5,
    body=(20.0, 0.34), shade_wobble=3.0, air=((130, 0.2), (70, 0.4), (30, 0.58)))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(tk.REPO, ".cache", "anime"))
    ap.add_argument("--percent", type=int, default=100)
    arg = ap.parse_args(argv)
    an.run(LOOK, arg.out, arg.percent)
