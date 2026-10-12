"""Scene E, Last train: a three-car train crossing a viaduct over a canal at night, seen from the quay.

Geometry and camera as signed off in roughs.py, with the near block on the quay made a mooring bollard. Original
art from geometry and procedural shaders; every colour is a colors.toml value or a mix.

    uv run tools/bg_e_last_train.py                 # backgrounds/e-last-train.png at 3440x1440
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import city  # noqa: E402
from scenes import srgb  # noqa: E402
from roughs import (P, BODY, GLASS, WIN_A, WIN_B, WIN_WARM, STEEL, RED, ORANGE, MIST, SKY, SEEDS, far,  # noqa: E402
                    look)

NAME = "e-last-train"
SEED = SEEDS["E"]
SAMPLES = 160
VY, VZ = 90.0, 6.55   # the viaduct: its distance and deck height


def build(rng):
    eye = (0.0, 0.0, 1.5)
    W = city.Boxes()
    W.box((-900, -40, -6), (900, 160, -1.2))
    W.done("canal", city.water("canal", tk.mix(P["background"], P["selection"], 0.1)))
    stone = city.plain("stone", STEEL, roughness=0.6)
    Q = city.Boxes()
    Q.box((-40, -10, -3), (-3.0, 9.0, 0.0))      # the quay we stand on, bottom left
    Q.box((-900, 150, -3), (900, 1000, 0.3))     # the far bank
    Q.done("quay", stone)
    # the mooring bollard on the quay edge: a squat post with a collar and a flared head
    tk.cylinder("bollard", 0.2, 0.55, (-4.3, 8.2, 0.275), stone, segments=24)
    tk.cylinder("bollard_collar", 0.26, 0.07, (-4.3, 8.2, 0.42), stone, segments=24)
    tk.cylinder("bollard_head", 0.3, 0.1, (-4.3, 8.2, 0.6), stone, segments=24)
    # the viaduct across the frame, its deck 6.55 m up, 90 m away
    vy, vz = VY, VZ
    V = city.Boxes()
    V.box((-60, vy - 3.5, vz - 1.0), (60, vy + 3.5, vz))
    for x in range(-54, 60, 14):
        V.box((x - 0.9, vy - 2.2, -3), (x + 0.9, vy + 2.2, vz - 1.0))
    V.done("viaduct", stone)
    # the train: three flat-nosed box cars with warm windows, a red lamp on the tail
    car = city.plain("car", tk.mix(P["background"], P["muted"], 0.35), roughness=0.35, metallic=0.5)
    T, G, L = city.Boxes(), city.Boxes(), city.Boxes()
    for k in range(3):
        x0 = -20.5 + k * 17.0
        T.box((x0, vy - 1.45, vz + 0.4), (x0 + 16.4, vy + 1.45, vz + 3.7))
        for j in range(9):
            wx = x0 + 0.9 + j * 1.68
            G.box((wx, vy - 1.47, vz + 1.75), (wx + 1.25, vy - 1.45, vz + 2.75))
    L.box((-20.52, vy - 1.2, vz + 0.9), (-20.5, vy - 0.8, vz + 1.2))
    L.box((-20.3, vy - 1.47, vz + 0.9), (-19.9, vy - 1.45, vz + 1.2))
    T.done("train", car)
    G.done("train_windows", tk.emissive("train_windows", srgb(WIN_WARM), 10.0))
    L.done("tail_lamp", tk.emissive("tail_lamp", srgb(RED), 18.0))
    city.mist("train_mist", (5, vy - 6, vz + 2.2), 34.0, 0.014, MIST, squash=(1.0, 0.5, 0.45), glow=ORANGE,
              glow_strength=0.03)
    # towers on both banks, behind the ends of the viaduct
    near = city.facade("near", BODY, GLASS, WIN_A, WIN_B, WIN_WARM, bay=3.0, floor_h=3.6, lit=0.05, strength=0.9,
                       ground=5.0)
    B = city.Boxes()
    for x0, x1, y0, h in ((-50, -38, 100, 21), (-40, -31, 104, 27), (32, 43, 108, 26), (42, 54, 112, 19)):
        B.box((x0, y0, -3), (x1, y0 + 18, h))
    B.done("towers", near)
    far(rng, near=200, heights=(16, 40), spread=50, top=80.0, start=170, glow_strength=0.016, tall=0.0)
    tk.set_world(srgb(SKY), 0.1)
    look(eye, 28, 850)


def scene(rng=None):
    import random
    sc = tk.reset()
    sc.cycles.seed = SEED
    sc.cycles.volume_bounces = 2
    sc.view_settings.look = "AgX - Punchy"
    build(random.Random(SEED))
    return sc


if __name__ == "__main__":
    city.run(scene, NAME, samples=SAMPLES)
