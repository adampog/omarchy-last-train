"""Scene D, Signal roof: a water tank and a lattice mast with a red beacon on a wet rooftop above the city.

Geometry and camera as signed off in roughs.py. The tank gets a ladder, the dishes a rim ring and a feed arm, and
the roof is plain wet deck. Original art from geometry and procedural shaders; every colour is a colors.toml value
or a mix.

    uv run tools/bg_d_signal_roof.py                # backgrounds/d-signal-roof.png at 3440x1440
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import city  # noqa: E402
from scenes import srgb  # noqa: E402
from roughs import P, STEEL, DECK, RED, MIST, SKY, SEEDS, far, look  # noqa: E402

NAME = "d-signal-roof"
SEED = SEEDS["D"]
SAMPLES = 160
ROOF_Z = 58.4
TANK = (8.7, 40.0)        # centre x, y; radius 4.5, 3.1 high
TOP = 69.25               # the mast's top
MAST = (8.9, 45.0)
DISHES = ((-3.6, 34.0, 59.6), (1.8, 34.0, 59.9))   # centres
DISH_R = 0.75


def build(rng):
    eye = (0.0, 0.0, 60.0)
    deck = city.wet_road("deck", DECK, puddle=0.5, size=1.2, rough=0.3)
    B = city.Boxes()
    B.box((-40, -12, 0), (40, 52.0, ROOF_Z))
    B.done("roof", deck)
    K = city.Boxes()
    K.box((-40, 51.6, ROOF_Z), (40, 52.0, ROOF_Z + 0.5))
    K.done("parapet", city.plain("parapet", STEEL, roughness=0.5))
    steel = city.plain("steel", STEEL, roughness=0.4, metallic=0.7)
    tk.cylinder("tank", 4.5, 3.1, (TANK[0], TANK[1], ROOF_Z + 1.55), steel, segments=48)
    # a ladder up the tank's front, two rails and rungs, a shallow cap on the lid
    x0 = TANK[0] - 3.2
    yf = TANK[1] - math.sqrt(4.5 ** 2 - 3.2 ** 2) - 0.12
    city.tube("ladder", [[(x0 + dx, yf, ROOF_Z), (x0 + dx, yf, ROOF_Z + 3.4)] for dx in (-0.25, 0.25)]
              + [[(x0 - 0.25, yf, ROOF_Z + 0.4 + 0.45 * k), (x0 + 0.25, yf, ROOF_Z + 0.4 + 0.45 * k)]
                 for k in range(7)], 0.03, steel)
    legs = [[(MAST[0] + dx, MAST[1] + dy, ROOF_Z), (MAST[0] + dx * 0.15, MAST[1] + dy * 0.15, TOP)]
            for dx, dy in ((-0.7, -0.5), (0.7, -0.5), (0.0, 0.7))]
    bars = [[(MAST[0] - 0.7 * (1 - k / 9), 44.5, ROOF_Z + k * 1.2), (MAST[0] + 0.7 * (1 - (k + 1) / 9), 44.5,
                                                                    ROOF_Z + 1.2 + k * 1.2)] for k in range(8)]
    city.tube("mast", legs + bars, 0.05, steel)
    b = (MAST[0], MAST[1], TOP + 0.2)
    tk.sphere("beacon", 0.28, b, tk.emissive("beacon", srgb(RED), 40.0), seg=16)
    tk.light("POINT", (b[0], b[1] - 0.6, b[2]), 11000, srgb(RED), size=0.5).visible_camera = False
    small = [[(x, 35.0, ROOF_Z), (x, 35.0, ROOF_Z + h)] for x, h in ((-5.0, 4.5), (-2.2, 6.0), (0.6, 3.2), (3.0, 5.0))]
    city.tube("small_masts", small, 0.04, steel)
    for x, y, zz in DISHES:
        d = tk.cylinder("dish", DISH_R, 0.12, (x, y, zz), steel, segments=32)
        d.rotation_euler = (math.radians(-34), 0, math.radians(18))  # face turned up and to the beacon, three-quarter
        city.tube("dish_rim", [[(x + DISH_R * math.cos(2 * math.pi * k / 40) * math.cos(math.radians(20)),
                                 y + 0.06, zz + DISH_R * math.sin(2 * math.pi * k / 40) * 0.5)
                                for k in range(40)]], 0.03, steel, cyclic=True)
        city.tube("dish_post", [[(x, y + 0.2, ROOF_Z), (x, y + 0.2, zz)]], 0.04, steel)
        city.tube("dish_arm", [[(x, y + 0.2, zz), (x + 0.1, y - 0.6, zz + 0.3)]], 0.02, steel)
    far(rng, count=420, near=110, heights=(30, 76), spread=65, top=110.0, glow_strength=0.036, tall=0.0)
    tk.set_world(srgb(SKY), 0.1)
    look(eye, 28, 900)


def scene(rng=None):
    sc = tk.reset()
    sc.cycles.seed = SEED
    sc.cycles.volume_bounces = 2
    sc.view_settings.look = "AgX - Punchy"
    build(random.Random(SEED))
    return sc


if __name__ == "__main__":
    city.run(scene, NAME, samples=SAMPLES)
