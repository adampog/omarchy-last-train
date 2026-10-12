"""Scene A, Rain gate, as a hand-painted animation background.

The street, sign, camera and far city are the ones in bg_a_rain_gate.py. The renderer writes only data and the
picture is painted from it by anime.py; this file says what in the scene is the key light, what glows and how,
and adds the scene's own drawn things: the windows, the steam over the grate, the bollards as two flat tones,
and a little incident near the sign (a downpipe, a blank blade sign, pavement seams, a drain, a puddle's edge).

Original art from geometry, procedural shaders and seeded noise. Every colour is a colors.toml value or a mix.

    uv run tools/anime_a.py                    # .cache/anime/a.png at 3440x1440
    uv run tools/anime_a.py --percent 50
"""

import argparse
import math
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import city  # noqa: E402
import paint as pt  # noqa: E402
import anime as an  # noqa: E402
import bg_a_rain_gate as a  # noqa: E402

P = tk.palette()
RED = P["accent"]
STEAM = tk.mix(an.SEL, P["muted"], 0.42)                      # the body of the steam
STEAM_IN = tk.mix(an.SEL, P["muted"], 0.2)                    # its darker inner tone
STEAM_LIT = tk.mix(tk.mix(P["muted"], P["bright_red"], 0.5), P["foreground"], 0.25)  # the side toward the sign
WIN_DARK = tk.mix(an.BG, an.SEL, 0.13)
WIN_EDGE = tk.mix(an.BODY, P["blue"], 0.32)
WIN_COOL = tk.mix(an.SEL, P["bright_blue"], 0.4)
BOLLARD, BOLLARD_LIT = tk.mix(an.BG, an.SEL, 0.2), tk.mix(tk.mix(an.BG, an.SEL, 0.4), RED, 0.3)
PLATE = tk.mix(an.BG, an.SEL, 0.1)

# the scene's own local colours, lifted from near-black to painted blues
a.BODY, a.GLASS, a.ROAD, a.PAVE, a.STEEL = an.BODY, an.GLASS, an.ROAD, an.PAVE, an.STEEL

LAMP_AT = ((a.SIGN_X[0] + a.SIGN_X[1] - 0.05) / 2, a.SIGN_Y - 0.9, 5.2)
GRATE = (3.4, 28.0, 0.0)
BOLLARDS = ((-1.2, 2.7, 0.17), (-0.8, 4.2, 1.2))
DRAIN = ((-0.56, 17.0), (-0.04, 18.3))    # in the road against the left kerb, short of the sign
PUDDLE = (3.6, 15.5, 1.5, 1.7)            # centre x, y and half sizes, on the road this side of the sign


def incident():
    """Small plain things near the sign: a downpipe on the wall, and a blank blade sign of plain shapes."""
    steel = city.plain("pipe", an.STEEL, roughness=0.5)
    city.tube("pipe", [[(-5.47, 21.3, 0.16), (-5.47, 21.3, 11.0), (-5.6, 21.3, 11.3)]], 0.075, steel)
    B = city.Boxes()
    for z in (1.4, 4.6, 7.8, 10.4):  # its brackets
        B.box((-5.6, 21.18, z), (-5.36, 21.42, z + 0.08))
    B.box((-5.6, 15.02, 4.55), (-4.8, 15.06, 4.63))  # the blade sign's arm
    B.done("incident_steel", steel)
    S = city.Boxes()
    S.box((-5.5, 15.0, 3.55), (-4.85, 15.08, 4.5))
    S.done("blade", city.plain("blade", PLATE, roughness=0.5))
    M = city.Boxes()  # what is on it: a square and two bars, no word
    M.box((-5.36, 14.99, 4.05), (-4.99, 15.0, 4.36))
    for z in (3.86, 3.72):
        M.box((-5.36, 14.99, z), (-4.99, 15.0, z + 0.06))
    M.done("blade_marks", city.plain("blade_marks", an.STEEL, roughness=0.5))


def build(rng):
    sc = bpy.context.scene
    facade = city.facade  # the walls are left plain: their windows are drawn by the painter
    city.facade = lambda name, body, *args, **kw: city.plain(name, body)
    try:
        a.buildings(rng)
        a.street()
        a.sign()
        a.rain(rng)  # drawn in 2D instead; called so the far city after it stands where it stood
        for ob in list(sc.objects):
            if ob.name.startswith("rain"):
                bpy.data.objects.remove(ob)
        a.far_city(rng)
    finally:
        city.facade = facade
    incident()
    cam = tk.camera(a.CAM, (a.CAM[0], 100.0, a.CAM[2] + 100.0 * math.tan(a.PITCH)), a.LENS)
    cam.data.clip_end = 3000


def on_sign(pic):
    x, y = pic.pos[..., 0], pic.pos[..., 1]
    return (abs(y - a.SIGN_Y) < 0.6) & (x < a.SIGN_X[1] + 0.4) & (x > -5.6)


def red_tubes(pic):
    x, z = pic.pos[..., 0], pic.pos[..., 2]
    return on_sign(pic) & (((z > 3.8) & (z < 7.0)) | (x > a.SIGN_X[1]))


def dress(pic, rng):
    """The windows, drawn: on the street's walls and, as small marks, on the far towers."""
    upright = an.walls(pic)[0]
    wall = upright & ~pic.far & (np.abs(pic.col - pt.rgb(an.BODY)).max(-1) < 0.02)
    an.windows(pic, rng, wall, part=0.64, glass=WIN_DARK, edge=WIN_EDGE, lit=a.WIN_WARM)
    an.marks(pic, rng, upright & pic.far, cool=WIN_COOL, lit=a.WIN_WARM)


def drawn(pic, out, rng):
    """Under the lines: the bollards' lit side, the pavement's seams, the drain and the puddle's edge."""
    k = pic.k
    x, y, z = pic.pos[..., 0], pic.pos[..., 1], pic.pos[..., 2]
    bollard = pic.solid & an.inbox(pic.pos, *BOLLARDS)
    out = np.where((bollard & ((pic.n[..., 0] < -0.3) | (pic.n[..., 2] > 0.75)))[..., None], pt.rgb(BOLLARD_LIT), out)

    pave = pic.solid & (np.abs(z - 0.16) < 0.03) & (x > -5.6) & (x < -0.6) & (y < 60)
    slab, strip = np.floor(y / 1.6), x > -3.2
    seam = np.zeros(pic.shape, bool)
    for ax in (0, 1):
        seam |= (slab != np.roll(slab, 1, ax)) | (strip != np.roll(strip, 1, ax))
    seam &= pave & np.roll(pave, 1, 0) & np.roll(pave, 1, 1) & (pt.noise(pic.shape, 70 * k, rng) > 0.36)
    line = pt.ink(seam, np.clip((48 - pic.dist) / 30, 0, 1), k, rng, 0.7)
    out = pt.mixa(out, pt.rgb(an.LINE), line * 0.55)

    road = pic.solid & (z < 0.05) & (pic.n[..., 2] > 0.7)
    (x0, y0), (x1, y1) = DRAIN
    drain = road & (x > x0) & (x < x1) & (y > y0) & (y < y1)
    slot = drain & (((x - x0) / 0.13) % 1.0 < 0.5) & (y > y0 + 0.12) & (y < y1 - 0.12)
    out = np.where(drain[..., None], pt.rgb(an.STEEL), out)
    out = np.where(slot[..., None], pt.rgb(an.LINE), out)
    rim = drain != np.roll(drain, 1, 0)
    rim |= drain != np.roll(drain, 1, 1)
    out = pt.mixa(out, pt.rgb(an.LINE), pt.ink(rim, np.ones(pic.shape, np.float32), k, rng, 0.8) * 0.8)

    cx, cy, rx, ry = PUDDLE
    reach = np.hypot((x - cx) / rx, (y - cy) / ry) * (1 + 0.5 * (pt.noise(pic.shape, 130 * k, rng) - 0.5))
    puddle = road & (reach < 1)
    out = pt.mixa(out, pt.rgb(an.SHADE), puddle * 0.14)
    edge = (puddle != np.roll(puddle, 1, 0)) & road
    far_side = edge & (y > cy + 0.3) & (x < cx + 0.6)  # only the far edge shows, where it catches the sign
    out = pt.mixa(out, pt.rgb(tk.mix(P["bright_red"], P["foreground"], 0.3)),
                  pt.blur(far_side.astype(np.float32), 0.8 * k) * 1.6 * (pt.noise(pic.shape, 50 * k, rng) > 0.4))
    return out


def steam(pic, out, rng):
    """Steam over the grate: two tall flat shapes cut by hand, a darker inner tone, lighter on the side toward
    the sign, thinner as they climb and gone at the top. No rim."""
    k = pic.k
    row, col = pic.at(GRATE)
    top = pic.at((GRATE[0], GRATE[1], 8.2))[0]
    behind = pic.dist > GRATE[1] - 0.5
    for height, width, lean, shift, amount in ((row - top, 50 * k, 0.2, 0, 0.58), ((row - top) * 0.55, 34 * k, 0.1,
                                                                                  34 * k, 0.45)):
        body, lit = pt.plume(pic.shape, (row, col + shift), height, width, rng, lean=lean, toward=-1, points=11)
        inner, _ = pt.plume(pic.shape, (row, col + shift + 8 * k), height * 0.8, width * 0.45, rng, lean=lean,
                            toward=-1, points=8)
        soft = 0.8 * k
        out = pt.mixa(out, pt.rgb(STEAM), pt.blur(body, soft) * amount * behind)
        out = pt.mixa(out, pt.rgb(STEAM_LIT), pt.blur(body * lit, soft) * amount * 0.85 * behind)
        out = pt.mixa(out, pt.rgb(STEAM_IN), pt.blur(inner * (body > 0) * (lit < 0.5), soft) * amount * 0.5 * behind)
    return out


LOOK = an.Look(
    name="a", seed=a.SEED, build=build, key_at=LAMP_AT, key_colour=RED,
    glows=(
        an.Glow(red_tubes, "tube", halo=((26, 1.6), (90, 3.0)), smear=1.4, colour=RED),
        an.Glow(lambda pic: on_sign(pic) & ~red_tubes(pic), "tube", halo=((26, 0.48),)),
        an.Glow(an.within((1.0, 87.3, -1.0), (3.6, 88.5, 3.2)), "flat", halo=((20, 2.0), (80, 6.0)), smear=1.2),
    ),
    # the sign's light in the air: a wide tinted field and a tighter one, both soft-edged
    discs=((a.SIGN_MID, (4.6, 12.5), (0.3, 0.16), RED),),
    flats=((*BOLLARDS, BOLLARD),),
    dress=dress, under=drawn, over=steam, wobble=2.2, hesitate=True, cut=4.0, ring_bands=0.55,
    air=((130, 0.2), (70, 0.4), (30, 0.58)), rain=0.85, rain_far=45.0, rain_colour=tk.mix(P["foreground"], P["bright_red"], 0.35))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(tk.REPO, ".cache", "anime"))
    ap.add_argument("--percent", type=int, default=100)
    arg = ap.parse_args(argv)
    an.run(LOOK, arg.out, arg.percent)
