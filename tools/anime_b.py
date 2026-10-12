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
CLOUD_FAR = tk.mix(an.BG, an.SEL, 0.3)   # cloud the lantern does not reach: a step darker than the sky behind it
ROOF_DARK = tk.mix(an.BG, an.SEL, 0.12)
DRUM = tk.mix(an.BG, P["brown"], 0.3)
DRUM_AT, DRUM_YAW = (-1.6, 17.0, b.DECK_Z + 0.46), np.radians(52)
TIER_AT = (85.0, 300.0, 9e5)   # the far city in two depth tones only
TOWER =((-150.0, 235.0), (-124.0, 262.0), 96.0)  # the one taller mass of the left group: two corners and its top
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
    (x0, y0), (x1, y1), top = TOWER
    T = city.Boxes()
    T.box((x0, y0, 0), (x1, y1, top))
    T.box((x0 + 7, y0 + 7, top), (x1 - 9, y1 - 7, top + 5))
    T.done("tall_tower", city.plain("tall_tower", rg.BODY_FAR))


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


def clouds(pic):
    """The two bands of low cloud, each with how strongly it is painted."""
    k, hz = pic.k, pic.horizon
    rng = np.random.default_rng(pic.look.seed + 500)
    return [(cloud(pic, rng, rows, cover) & (pic.dist > 150), tone)
            for rows, cover, tone in (((hz - 250 * k, hz - 40 * k), 0.42, 0.42), ((hz - 120 * k, hz + 60 * k), 0.5, 0.58))]


def dress(pic, rng):
    """Windows on the far towers, drawn as a few loose clusters of marks, and none where cloud lies over a wall."""
    clear = ~np.any([m for m, _ in clouds(pic)], axis=0)
    an.marks(pic, rng, pic.far & an.walls(pic)[0] & clear, bay=3.0, floor_h=3.2, ground=2.0, part=0.2, warm=0.16,
             cool=WIN_COOL, lit=WIN_WARM)


def drum(pic, out, rng):
    """The cable drum as two flat tones, with a drawn line inside each rim and round the axle."""
    k = pic.k
    ax = np.array((np.cos(DRUM_YAW), np.sin(DRUM_YAW), 0.0), np.float32)
    p = pic.pos - np.array(DRUM_AT, np.float32)
    along = p @ ax
    r = np.linalg.norm(p - along[..., None] * ax, axis=-1)
    m = pic.solid & (r < 0.5) & (np.abs(along) < 0.42) & ~level(pic)  # never the roof under it
    face = m & (np.abs(pic.n @ ax) > 0.7)
    out = np.where(m[..., None], pt.rgb(tk.mix(DRUM, an.BG, 0.45)), out)
    out = np.where(face[..., None], pt.rgb(tk.mix(DRUM, P["muted"], 0.12)), out)
    line = face & ((np.abs(r - 0.39) < 0.012) | (np.abs(r - 0.09) < 0.012))
    return pt.mixa(out, pt.rgb(an.LINE), pt.ink(line, np.ones(pic.shape, np.float32), k, rng, 0.8) * 0.75)


def under(pic, out, rng):
    """Low cloud among the towers in two tones and a lit edge, warmer toward the lantern; then the parapet's
    stain and joint."""
    k = pic.k
    hz = pic.horizon
    glow = near_to(pic, AT, 1500)
    side = np.where(np.arange(pic.shape[1])[None, :] < pic.at(AT)[1], 1, -1)  # which way the lantern lies
    d = max(2, int(round(7 * k)))
    reach = pt.step(0.1, 0.45, glow)   # 1 inside the body of the lantern's light, 0 beyond it
    for m, tone in clouds(pic):
        belly = m & ~np.roll(m, -d, 0)                                  # the underside, a step darker
        top = m & ~np.roll(m, d, 0)                                     # the upper edge, a step lighter
        facing = m & ~np.where(side > 0, np.roll(m, -2 * d, 1), np.roll(m, 2 * d, 1))  # the edge toward the lantern
        colour = pt.mixa(np.broadcast_to(pt.rgb(CLOUD_FAR), out.shape), pt.rgb(CLOUD), reach)
        colour = pt.mixa(colour, pt.rgb(CLOUD_LIT), glow)
        tone = tone * (0.75 + 0.55 * glow)
        # beyond the light the cloud is thin against the sky but covers a tower it crosses with its own flat tone
        tone = np.where(pic.solid, np.maximum(tone, 0.9 * (1 - reach)), tone)
        out = pt.mixa(out, colour, pt.blur(m.astype(np.float32), 0.7 * k) * tone)
        out = pt.mixa(out, pt.rgb(CLOUD_DARK), pt.blur(belly.astype(np.float32), 0.7 * k) * tone * 0.5 * reach)
        lit = pt.blur((top | facing).astype(np.float32), 0.7 * k) * glow * reach  # lit edges only in the light
        out = pt.mixa(out, pt.mixa(colour, pt.rgb(PALE), 0.3), lit * tone * 0.9)
    # the roof away from the lantern is a step darker and cooler, and darkest along the bottom of the picture;
    # the lantern's own pool is left as it is
    pool = near_to(pic, (AT[0], AT[1], Z), 1150)
    low = pt.step(0.72, 1.0, np.arange(pic.shape[0], dtype=np.float32)[:, None] / pic.shape[0])
    away = np.clip(1 - pt.step(0.0, 0.5, pool) + 0.5 * low, 0, 1)
    out = pt.mixa(out, pt.rgb(ROOF_DARK), level(pic) * away * 0.68)
    # and so are the far parapet and the city beyond the lantern's reach, so nothing out there reads as lit
    beyond = (pic.solid & (pic.pos[..., 1] > 33.0)) * (1 - reach)
    out = pt.mixa(out, pt.rgb(ROOF_DARK), beyond * 0.45)
    out = drum(pic, out, rng)
    # the near parapet block stands in shadow, a step darker than the roof, so the lantern owns the picture
    block = pic.solid & (pic.pos[..., 1] < FACE_Y + 3.0)
    out = pt.mixa(out, pt.rgb(an.BG), block * (0.56 + 0.2 * low))
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
    tier_at=TIER_AT, veil=(), wet=level, under=under, over=over, tint=0.4,
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
