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


def under(pic, out, rng):
    """The right wall: one flat warm tone where the lanterns reach, a darker step beyond, a hand-cut edge between.
    The counter's front: its lit tone, a shelf line and the cloth."""
    k = pic.k
    wall = right_wall(pic)
    z, y = pic.pos[..., 2], pic.pos[..., 1]
    wob = (pt.noise(pic.shape, (160 * k, 220 * k), rng) - 0.5) * 0.7
    reach = np.hypot(y - G_AT[1], (z - G_AT[2]) * 0.8) + wob
    rows = np.arange(pic.shape[0], dtype=np.float32)[:, None]
    fade = np.clip((rows - 80 * k) / (400 * k), 0, 1)  # the painter keeps the top of the picture dark
    near, step = wall & (reach < 4.0), wall & (reach >= 4.0) & (reach < 7.5)
    out = pt.mixa(out, pt.rgb(WARM_WALL), near * 0.8 * fade)
    out = pt.mixa(out, pt.rgb(WARM_STEP), step * 0.6 * fade)
    front = pic.solid & (np.abs(y - FRONT_Y) < 0.06) & (pic.n[..., 1] < -0.5) & an.inbox(
        pic.pos, (1.1, 13.4, -0.1), (3.9, 13.7, 1.05))
    out = np.where(front[..., None], pt.mixa(pt.rgb(COUNTER), pt.rgb(COUNTER_LIT), 0.5), out)
    shelf = front & (np.abs(z - 0.64) < 0.035)
    out = np.where(shelf[..., None], pt.rgb(SHELF), out)
    cloth = front & (pic.pos[..., 0] > 1.85) & (pic.pos[..., 0] < 2.55) & (z > 0.22) & (z < 1.0)
    out = np.where(cloth[..., None], pt.rgb(CLOTH), out)
    edge = (cloth != np.roll(cloth, 1, 1)) | (shelf != np.roll(shelf, 1, 0))
    return pt.mixa(out, pt.rgb(an.LINE), pt.ink(edge, np.ones(pic.shape, np.float32), k, rng, 0.8) * 0.7)


def over(pic, out, rng):
    """Steam off the kettle: one low wide puff, lighter toward the lanterns."""
    k = pic.k
    row, col = pic.at(KETTLE)
    per_m = pic.f / KETTLE[1]
    body, lit, inner = pt.puff(pic.shape, (row, col), 0.55 * per_m, 0.8 * per_m, rng)
    soft = 0.8 * k
    out = pt.mixa(out, pt.rgb(STEAM), pt.blur(body, soft) * 0.5)
    return pt.mixa(out, pt.rgb(STEAM_LIT), pt.blur(body * lit, soft) * 0.4)


LOOK = an.Look(
    name="g", seed=g.SEED, build=build, key_at=(2.3, 12.6, 1.9), key_colour=ORANGE,
    rings=(2.6, 4.6, 7.5), amounts=(0.3, 0.1, 0.03),
    glows=(an.Glow(an.within((1.2, 13.0, 2.0), (3.5, 13.5, 2.6)), "paper", core=9.0, halo=((30, 0.35),), smear=1.4),
           an.Glow(an.within((-4.6, 17.9, 0.3), (-4.3, 19.0, 1.8)), halo=((14, 0.8), (60, 1.2)), smear=1.0)),
    discs=((G_AT, (1.6, 4.0), (0.3, 0.14), ORANGE),),
    tier_at=(500.0, 700.0, 900.0), veil=((28.0, 0.14), (50.0, 0.28)), tint=0.4, under=under, over=over,
    rain=0.45, rain_colour=tk.mix(PALE, ORANGE, 0.3), stars=False, wobble=1.4, hesitate=True, cut=3.0,
    ring_bands=0.5, body=(4.0, 0.1), shade_wobble=3.0)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(tk.REPO, ".cache", "anime"))
    ap.add_argument("--percent", type=int, default=100)
    arg = ap.parse_args(argv)
    an.run(LOOK, arg.out, arg.percent)
