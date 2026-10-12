"""Scene B, Moored lantern, as a hand-painted animation background.

The roof, lantern, cradle, cables, masts, far city and camera are the ones in bg_b_moored_lantern.py. The renderer
writes only data and anime.py paints it. This file says what is the key light and what glows, and draws the
scene's own things: the lantern as a flat disc in three steps, low cloud among the towers as ragged cut shapes in
two tones, windows on the far towers, and a vent, a cable and a joint on the near parapet.

Original art from geometry, procedural shaders and seeded noise. Every colour is a colors.toml value or a mix.

    uv run tools/anime_b.py                    # .cache/anime/b.png at 3440x1440
    uv run tools/anime_b.py --percent 50
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
import bg_b_moored_lantern as b  # noqa: E402

P = tk.palette()
RED, ORANGE, PALE = P["accent"], P["orange"], P["foreground"]
WIN_COOL = tk.mix(an.SEL, P["bright_blue"], 0.4)
WIN_WARM = tk.mix(ORANGE, PALE, 0.3)
CLOUD = tk.mix(an.SEL, P["muted"], 0.3)
CLOUD_LIT = tk.mix(ORANGE, P["muted"], 0.3)
CLOUD_DARK = tk.mix(an.BG, an.SEL, 0.6)
VENT_BODY = tk.mix(an.STEEL, P["muted"], 0.2)
STAIN = tk.mix(an.BG, an.SEL, 0.2)

# the scene's own local colours, lifted from near-black to painted blues; its air is painted, not rendered
rg.BODY, rg.GLASS, rg.ROAD, rg.DECK, rg.STEEL = an.BODY, an.GLASS, an.ROAD, tk.mix(an.PAVE, an.BG, 0.68), an.STEEL
an.no_air()

AT = b.C
Z = b.DECK_Z
FACE_Y = 5.6                      # the near parapet's face
VENT = ((2.0, 58.93), (2.55, 59.24))  # on that face: (x, z) of its low and high corners
JOINT_X = 3.05


def build(rng):
    facade = city.facade  # the far towers' windows are drawn by the painter
    city.facade = lambda name, body, *args, **kw: city.plain(name, body)
    try:
        b.build()
    finally:
        city.facade = facade
    # the near parapet's line of incident: a louvred vent set in its face and a cable clipped along under the coping
    (x0, z0), (x1, z1) = VENT
    V = city.Boxes()
    V.box((x0, FACE_Y - 0.05, z0), (x1, FACE_Y, z1))
    V.done("vent", city.plain("vent", VENT_BODY, roughness=0.5))
    S = city.Boxes()
    for i in range(4):
        z = z0 + 0.045 + i * 0.065
        S.box((x0 + 0.03, FACE_Y - 0.085, z), (x1 - 0.03, FACE_Y - 0.05, z + 0.03))
    S.done("vent_slats", city.plain("vent_slats", an.STEEL, roughness=0.5))
    steel = city.plain("cable", an.STEEL, roughness=0.5)
    y = FACE_Y - 0.03
    run = [(1.62, y, Z), (1.62, y, 59.3), (1.9, y, 59.36), (2.8, y, 59.33), (3.4, y, 59.37), (4.2, y, 59.34)]
    city.tube("parapet_cable", [run], 0.018, steel)
    K = city.Boxes()
    for x in (1.9, 2.8, 3.4):
        K.box((x - 0.03, FACE_Y - 0.06, 59.3), (x + 0.03, FACE_Y, 59.4))
    K.done("cable_clips", steel)


def level(pic):
    return pic.solid & (pic.n[..., 2] > 0.7) & (abs(pic.pos[..., 2] - Z) < 0.3)


def near_to(pic, place, reach):
    """1 at a place in the picture falling to 0 `reach` pixels (of the 3440 picture) away."""
    row, col = pic.at(place)
    yy, xx = np.ogrid[:pic.shape[0], :pic.shape[1]]
    return np.clip(1 - np.hypot(yy - row, xx - col) / (reach * pic.k), 0, 1).astype(np.float32)


def cloud(pic, rng, rows, cover):
    """Low cloud in a band of rows as one ragged cut shape: long slow edges with short sharp breaks in them."""
    k = pic.k
    lo, hi = rows
    y = np.arange(pic.shape[0], dtype=np.float32)[:, None]
    band = pt.step(lo, lo + (hi - lo) * 0.3, y) * (1 - pt.step(hi - (hi - lo) * 0.3, hi, y))
    n = pt.noise(pic.shape, (26 * k, 300 * k), rng) \
        + 0.26 * (pt.noise(pic.shape, (12 * k, 50 * k), rng) - 0.5) \
        + 0.16 * (np.round(pt.noise(pic.shape, (9 * k, 26 * k), rng) * 3) / 3 - 0.5)
    return (n * (0.55 + 0.45 * band) > 1 - cover) & (band > 0.02)


def dress(pic, rng):
    """Windows on the far towers, drawn as loose clusters of marks."""
    an.marks(pic, rng, pic.far & an.walls(pic)[0], bay=3.0, floor_h=3.2, ground=2.0, part=0.4, warm=0.16,
             cool=WIN_COOL, lit=WIN_WARM)


def under(pic, out, rng):
    """Low cloud among the towers in two tones and a lit edge, warmer toward the lantern; then the parapet's
    stain and joint."""
    k = pic.k
    hz = pic.horizon
    glow = near_to(pic, AT, 1500)
    side = np.where(np.arange(pic.shape[1])[None, :] < pic.at(AT)[1], 1, -1)  # which way the lantern lies
    d = max(2, int(round(7 * k)))
    for rows, cover, tone in (((hz - 250 * k, hz - 40 * k), 0.42, 0.42), ((hz - 120 * k, hz + 60 * k), 0.5, 0.58)):
        m = cloud(pic, rng, rows, cover) & (pic.dist > 150)
        belly = m & ~np.roll(m, -d, 0)                                  # the underside, a step darker
        top = m & ~np.roll(m, d, 0)                                     # the upper edge, a step lighter
        facing = m & ~np.where(side > 0, np.roll(m, -2 * d, 1), np.roll(m, 2 * d, 1))  # the edge toward the lantern
        out = np.where(m[..., None], pt.blur(out, 9 * k), out)          # what is behind it loses its marks
        colour = pt.mixa(np.broadcast_to(pt.rgb(CLOUD), out.shape), pt.rgb(CLOUD_LIT), glow)
        tone = tone * (0.55 + 0.75 * glow)                              # fainter away from the lantern
        out = pt.mixa(out, colour, pt.blur(m.astype(np.float32), 0.7 * k) * tone)
        out = pt.mixa(out, pt.rgb(CLOUD_DARK), pt.blur(belly.astype(np.float32), 0.7 * k) * tone * 0.5)
        lit = pt.blur((top | facing).astype(np.float32), 0.7 * k) * (0.25 + 0.75 * glow)
        out = pt.mixa(out, pt.mixa(colour, pt.rgb(PALE), 0.3), lit * tone * 0.9)
    # the near parapet block stands in shadow, a step darker than the roof, so the lantern owns the picture
    block = pic.solid & (pic.pos[..., 1] < FACE_Y + 3.0)
    out = pt.mixa(out, pt.rgb(an.BG), block * 0.4)
    # on it: a stain run down from the vent, and one joint in the wall
    face = pic.solid & (np.abs(pic.pos[..., 1] - FACE_Y) < 0.02) & (pic.n[..., 1] < -0.5)
    (x0, z0), (x1, _) = VENT
    x, z = pic.pos[..., 0], pic.pos[..., 2]
    run = pt.noise(pic.shape, (90 * k, 14 * k), rng)
    stain = face & (x > x0 + 0.04) & (x < x1 - 0.04) & (z < z0) & (z > z0 - 0.1 - 0.3 * run)
    out = pt.mixa(out, pt.rgb(STAIN), pt.blur(stain.astype(np.float32), 1.2 * k) * 0.4)
    joint = face & (np.abs(x - JOINT_X) < 0.005)
    return pt.mixa(out, pt.rgb(an.LINE), pt.ink(joint, np.ones(pic.shape, np.float32), k, rng, 0.8) * 0.6)


def over(pic, out, rng):
    """The lantern as a flat disc in three steps: bright core, orange, darker rim."""
    m = pic.masks[0]
    row, col = pic.at(AT)
    radius = pic.f * 2.0 / float(np.linalg.norm(np.array(AT) - pic.eye))
    yy, xx = np.ogrid[:pic.shape[0], :pic.shape[1]]
    r = np.hypot(yy - row + 0.08 * radius, xx - col).astype(np.float32) / radius
    r = r * (1 + 0.1 * (pt.noise(pic.shape, 60 * pic.k, rng) - 0.5))
    rim, core = pt.rgb(tk.mix(ORANGE, P["brown"], 0.6)), pt.rgb(tk.mix(P["bright_yellow"], PALE, 0.35))
    disc = np.where((r > 0.8)[..., None], rim, np.where((r < 0.48)[..., None], core, pt.rgb(ORANGE)))
    return out + (disc - out) * m[..., None]


LOOK = an.Look(
    name="b", seed=b.SEED, build=build, key_at=(AT[0], AT[1] - 2.6, AT[2]), key_colour=ORANGE,
    rings=(5.0, 9.0, 15.0), amounts=(0.3, 0.14, 0.05),
    glows=(an.Glow(an.within((2.1, 19.2, 59.9), (6.4, 23.6, 64.1)), smear=0.3),
           an.Glow(an.within((9.0, 25.5, 64.0), (12.0, 26.5, 66.0)), halo=((9, 3.0),), colour=RED)),
    discs=((AT, (4.6, 11.0), (0.36, 0.15), ORANGE),),
    tier_at=(85.0, 280.0, 520.0), veil=(), wet=level, under=under, over=over, tint=0.4,
    sky=(an.SKY_TOP, tk.mix(an.BG, an.SEL, 0.24), tk.mix(an.BG, an.SEL, 0.6)),
    dress=dress, wobble=1.4, hesitate=True, cut=3.0, ring_bands=0.6, body=(13.0, 0.1), shade_wobble=3.0,
    strokes=0.7)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(tk.REPO, ".cache", "anime"))
    ap.add_argument("--percent", type=int, default=100)
    arg = ap.parse_args(argv)
    an.run(LOOK, arg.out, arg.percent)
