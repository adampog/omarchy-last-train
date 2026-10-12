"""Scene A, Rain gate, as a hand-painted animation background.

The street, sign, camera and far city are the ones in bg_a_rain_gate.py. The renderer writes only data and the
picture is painted from it by anime.py; this file says what in the scene is the key light, what glows and how,
and adds the scene's own drawn things: the steam over the grate and the rain.

Original art from geometry, procedural shaders and seeded noise. Every colour is a colors.toml value or a mix.

    uv run tools/anime_a.py                    # .cache/anime/a.png at 3440x1440
    uv run tools/anime_a.py --percent 50
"""

import argparse
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import paint as pt  # noqa: E402
import anime as an  # noqa: E402
import bg_a_rain_gate as a  # noqa: E402

P = tk.palette()
RED = P["accent"]
STEAM, STEAM_LIT = tk.mix(an.SEL, P["muted"], 0.4), tk.mix(P["muted"], P["bright_red"], 0.4)

# the scene's own local colours, lifted from near-black to painted blues
a.BODY, a.GLASS, a.ROAD, a.PAVE, a.STEEL = an.BODY, an.GLASS, an.ROAD, an.PAVE, an.STEEL

LAMP_AT = ((a.SIGN_X[0] + a.SIGN_X[1] - 0.05) / 2, a.SIGN_Y - 0.9, 5.2)
GRATE = (3.4, 28.0, 0.0)


def build(rng):
    sc = bpy.context.scene
    a.buildings(rng)
    a.street()
    a.sign()
    a.rain(rng)  # drawn in 2D instead; called so the far city after it stands where it stood
    for ob in list(sc.objects):
        if ob.name.startswith("rain"):
            bpy.data.objects.remove(ob)
    a.far_city(rng)
    cam = tk.camera(a.CAM, (a.CAM[0], 100.0, a.CAM[2] + 100.0 * math.tan(a.PITCH)), a.LENS)
    cam.data.clip_end = 3000


def on_sign(pic):
    x, y = pic.pos[..., 0], pic.pos[..., 1]
    return (abs(y - a.SIGN_Y) < 0.6) & (x < a.SIGN_X[1] + 0.4) & (x > -5.6)


def red_tubes(pic):
    x, z = pic.pos[..., 0], pic.pos[..., 2]
    return on_sign(pic) & (((z > 3.8) & (z < 7.0)) | (x > a.SIGN_X[1]))


def steam(pic, out, rng):
    """Steam over the grate: tall flat shapes cut by hand, lighter on the side toward the sign."""
    k = pic.k
    row, col = pic.at(GRATE)
    top = pic.at((GRATE[0], GRATE[1], 7.5))[0]
    behind = pic.dist > GRATE[1] - 0.5
    for height, width, lean, shift, amount in ((row - top, 62 * k, 0.22, 0, 0.5), ((row - top) * 0.62, 40 * k, 0.1,
                                                                                    70 * k, 0.4)):
        body, lit = pt.plume(pic.shape, (row, col + shift), height, width, rng, lean=lean, toward=-1)
        out = pt.mixa(out, pt.rgb(STEAM), pt.blur(body, 0.7 * k) * amount * behind)
        out = pt.mixa(out, pt.rgb(STEAM_LIT), pt.blur(body * lit, 0.7 * k) * amount * 0.7 * behind)
    return out


LOOK = an.Look(
    name="a", seed=a.SEED, build=build, key_at=LAMP_AT, key_colour=RED,
    glows=(
        an.Glow(red_tubes, "tube", halo=((26, 1.6), (130, 8.0), (420, 20.0)), smear=1.4, colour=RED),
        an.Glow(lambda pic: on_sign(pic) & ~red_tubes(pic), "tube", halo=((26, 0.48),)),
        an.Glow(an.within((1.0, 87.3, -1.0), (3.6, 88.5, 3.2)), "flat", halo=((20, 2.0), (80, 6.0)), smear=1.2),
    ),
    over=steam, rain=1.0, rain_colour=tk.mix(P["foreground"], P["bright_red"], 0.35))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(tk.REPO, ".cache", "anime"))
    ap.add_argument("--percent", type=int, default=100)
    arg = ap.parse_args(argv)
    an.run(LOOK, arg.out, arg.percent)
