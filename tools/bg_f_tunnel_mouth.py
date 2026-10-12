"""Scene F, Tunnel mouth: a wet road bending into a lit tunnel under a hill and its retaining wall.

Geometry and camera as signed off in roughs.py. The wall steps back in three depths (a near pier, the mid wall, the
far wall) and carries a lamp housing and a sign bracket. Original art from geometry and procedural shaders; every
colour is a colors.toml value or a mix.

    uv run tools/bg_f_tunnel_mouth.py               # backgrounds/f-tunnel-mouth.png at 3440x1440
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import city  # noqa: E402
from scenes import srgb  # noqa: E402
from roughs import P, STEEL, ROAD, RED, ORANGE, MIST, SKY, BODY, GLASS, WIN_A, WIN_B, WIN_WARM, SEEDS, far, look  # noqa: E402

NAME = "f-tunnel-mouth"
SEED = SEEDS["F"]
SAMPLES = 160


def build(rng):
    eye = (0.0, 0.0, 1.4)
    road = city.wet_road("road", ROAD, puddle=0.52, size=1.0, rough=0.2)
    G = city.Boxes()
    G.box((-400, -60, -1), (400, 46, 0))
    G.box((-15.4, 46, -1), (-5.4, 220, 0))  # the road on into the tunnel
    G.done("ground", road)
    wall = city.plain("wall", tk.mix(P["background"], P["muted"], 0.2), roughness=0.7)
    Wl = city.Boxes()
    Wl.box((-200, 58, 0), (-40, 240, 14))       # the far wall, left
    Wl.box((-40, 46, 0), (-15.4, 240, 14))      # the mid wall, left of the mouth
    Wl.box((-24, 41, 0), (-18.5, 46, 9.5))      # a near pier
    Wl.box((-5.4, 46, 0), (26, 240, 14))        # the mid wall, right of it
    Wl.box((26, 58, 0), (200, 240, 14))         # the far wall, right
    Wl.box((-17.6, 45.2, 3.2), (-16.9, 46, 3.9))  # a lamp housing
    Wl.box((-3.0, 44.6, 5.0), (-2.9, 46, 6.0))     # a sign bracket, arm
    Wl.box((-3.0, 44.6, 5.9), (-0.8, 46, 6.0))
    Wl.box((-15.4, 46, 7.0), (-5.4, 240, 14))   # over the mouth
    Wl.box((-16.2, 45.5, 0), (-15.4, 46, 7.8))  # the portal frame
    Wl.box((-5.4, 45.5, 0), (-4.6, 46, 7.8))
    Wl.box((-16.2, 45.5, 7.0), (-4.6, 46, 7.8))
    Wl.done("portal", wall)
    # the inside is the light: orange strips along the roof, and the air in the mouth
    S = city.Boxes()
    for y in range(52, 200, 9):
        S.box((-13.4, y, 6.9), (-12.9, y + 5, 6.98))
        S.box((-7.9, y, 6.9), (-7.4, y + 5, 6.98))
    S.done("strips", tk.emissive("strips", srgb(ORANGE), 20.0))
    tk.light("POINT", (-10.4, 49, 5.0), 26000, srgb(ORANGE), size=1.5).visible_camera = False
    city.mist("mouth_mist", (-10.4, 46, 3.5), 28.0, 0.035, MIST, glow=ORANGE, glow_strength=0.045, power=2.6)
    for x in (-13.8, -7.0):  # the red lamp pair at the lip
        tk.sphere("lip_lamp", 0.16, (x, 45.4, 8.2), tk.emissive("lip_lamp", srgb(RED), 14.0), seg=12)
    # the road sweeps in from bottom right: a guard rail on the outside of the bend
    steel = city.plain("steel", STEEL, roughness=0.4, metallic=0.7)
    bend = [(9.5 - 14.1 * t ** 1.7, 2.0 + 43.5 * t) for t in (k / 24 for k in range(25))]
    city.tube("rail", [[(x, y, 0.75) for x, y in bend], [(x, y, 0.45) for x, y in bend]], 0.05, steel)
    city.tube("rail_posts", [[(x, y, 0), (x, y, 0.75)] for x, y in bend[::2]], 0.05, steel)
    # a tower on the hill above the mouth
    near = city.facade("near", BODY, GLASS, WIN_A, WIN_B, WIN_WARM, bay=3.0, floor_h=3.6, lit=0.05, strength=0.9,
                       ground=15.0)
    B = city.Boxes()
    B.box((-22, 90, 14), (-2, 112, 40))
    B.box((30, 110, 14), (56, 136, 30))
    B.done("towers", near)
    far(rng, near=260, heights=(40, 90), spread=40, top=170.0, glow_strength=0.01)
    tk.set_world(srgb(SKY), 0.07)
    look(eye, 24, 950)


def scene(rng=None):
    sc = tk.reset()
    sc.cycles.seed = SEED
    sc.cycles.volume_bounces = 2
    sc.view_settings.look = "AgX - Punchy"
    build(random.Random(SEED))
    return sc


if __name__ == "__main__":
    city.run(scene, NAME, samples=SAMPLES)
