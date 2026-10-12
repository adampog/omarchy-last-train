"""Scene A, Rain gate, as a hand-painted animation background.

The street, sign, camera and far city are the ones in bg_a_rain_gate.py. The renderer writes only data and the
picture is painted from it by anime.py; this file says what in the scene is the key light, what glows and how,
and adds the scene's own drawn things: the windows, the steam over the grate, the bollards as two flat tones,
and a little incident near the sign (a downpipe, a blank blade sign, pavement seams, a drain, and on the left wall a vent, a pipe run, a flaked patch and a stain).

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
STEAM = tk.mix(tk.mix(an.SEL, P["muted"], 0.5), P["accent"], 0.14)                      # the body of the steam
STEAM_IN = tk.mix(STEAM, an.SEL, 0.4)                 # its darker inner tone
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
WALL_X = -5.6                             # the left wall's face
VENT = ((-5.6, 17.6, 5.9), (-5.46, 18.4, 6.4))
PATCH = (12.6, 5.3, 1.5, 0.75)            # a flaked patch on the left wall: centre y, z and half sizes
STEAM_SIZE = (3.0, 2.6)                   # the steam's half width and its height, in metres


def incident():
    """Small plain things near the sign: a downpipe on the wall, and a blank blade sign of plain shapes."""
    steel = city.plain("pipe", an.STEEL, roughness=0.5)
    city.tube("pipe", [[(-5.47, 21.3, 0.16), (-5.47, 21.3, 11.0), (-5.6, 21.3, 11.3)]], 0.075, steel)
    B = city.Boxes()
    for z in (1.4, 4.6, 7.8, 10.4):  # its brackets
        B.box((-5.6, 21.18, z), (-5.36, 21.42, z + 0.08))
    B.box((-5.6, 15.02, 4.55), (-4.8, 15.06, 4.63))  # the blade sign's arm
    for y in (16.4, 18.6, 20.6):  # clips of the pipe run
        B.box((-5.6, y - 0.05, 7.48), (-5.4, y + 0.05, 7.72))
    B.done("incident_steel", steel)
    # a pipe run along the left wall above the awnings, turning into the wall, and a vent under it
    city.tube("pipe_run", [[(-5.47, 21.3, 7.6), (-5.47, 15.6, 7.6), (-5.47, 15.6, 7.1), (-5.62, 15.6, 7.1)]], 0.06,
              steel)
    V = city.Boxes()
    V.box(*VENT)
    V.done("vent", city.plain("vent", PLATE, roughness=0.5))
    L = city.Boxes()  # its slats
    (x0, y0, z0), (x1, y1, z1) = VENT
    for i in range(3):
        z = z0 + 0.1 + 0.13 * i
        L.box((x1, y0 + 0.08, z), (x1 + 0.01, y1 - 0.08, z + 0.05))
    L.done("vent_slats", steel)
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
    """Under the lines: the bollards' lit side, the pavement's seams, the drain, and the left wall's patch and stain."""
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


    # on the left wall above the awnings: a flaked patch in two tones, and a stain run down from the vent
    wall = pic.solid & (np.abs(x - WALL_X) < 0.05) & (pic.n[..., 0] > 0.5)
    py, pz, ry, rz = PATCH
    ragged = 1 + 0.7 * (pt.noise(pic.shape, 26 * k, rng) - 0.5)
    reach = np.hypot((y - py) / ry, (z - pz) / rz) * ragged
    out = pt.mixa(out, pt.rgb(an.LINE), (wall & (reach < 1)) * 0.3)
    bare = np.hypot((y - py - 0.25) / ry, (z - pz + 0.1) / rz) * ragged < 0.5
    out = pt.mixa(out, pt.rgb(WIN_EDGE), (wall & bare) * 0.3)
    (_, v0, vz), (_, v1, _) = VENT
    run = (vz - z) / 2.2  # 0 under the vent to 1 where the stain gives out
    wide = 0.16 + 0.3 * run * pt.noise(pic.shape, (60 * k, 14 * k), rng)
    stain = wall & (run > 0) & (run < 0.55 + 0.45 * pt.noise(pic.shape, (400 * k, 10 * k), rng)) \
        & (np.abs(y - (v0 + v1) / 2) < wide)
    out = pt.mixa(out, pt.rgb(an.LINE), stain * 0.26)
    return out


def steam(pic, out, rng):
    """Steam over the grate: a low wide puff of three lobes cut by hand, a darker inner tone, pink on the side
    toward the sign, thinner toward the top. Wider than it is tall, so it never reads as a figure. No rim."""
    k = pic.k
    row, col = pic.at(GRATE)
    per_m = pic.f / GRATE[1]
    behind = pic.dist > GRATE[1] - 0.5
    body, lit, inner = pt.puff(pic.shape, (row, col), STEAM_SIZE[0] * per_m, STEAM_SIZE[1] * per_m, rng)
    soft = 1.0 * k
    out = pt.mixa(out, pt.rgb(STEAM), pt.blur(body, soft) * 0.55 * behind)
    out = pt.mixa(out, pt.rgb(STEAM_IN), pt.blur(inner * (lit < 0.5), soft) * 0.2 * behind)
    out = pt.mixa(out, pt.rgb(STEAM_LIT), pt.blur(body * lit, soft) * 0.5 * behind)
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
    body=(11.0, 0.24), shade_wobble=3.0,
    air=((130, 0.2), (70, 0.4), (30, 0.58)), rain=0.85, rain_far=45.0, rain_colour=tk.mix(P["foreground"], P["bright_red"], 0.35))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(tk.REPO, ".cache", "anime"))
    ap.add_argument("--percent", type=int, default=100)
    arg = ap.parse_args(argv)
    an.run(LOOK, arg.out, arg.percent)
