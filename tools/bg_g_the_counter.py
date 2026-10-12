"""Scene G, The counter: a night food stall under paper lanterns at the end of a rain-wet alley.

Geometry and camera as signed off in roughs.py, with a shelf line and a cloth added to the counter's front.
Original art from geometry and procedural shaders; every colour is a colors.toml value or a mix.

    uv run tools/bg_g_the_counter.py                # backgrounds/g-the-counter.png at 3440x1440
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import city  # noqa: E402
from scenes import srgb  # noqa: E402
from roughs import P, ROAD, STEEL, RED, ORANGE, CYAN, MIST, SKY, SEEDS, look  # noqa: E402

NAME = "g-the-counter"
SEED = SEEDS["G"]
SAMPLES = 160


def build(rng):
    eye = (0.0, 0.0, 1.5)
    ground = city.wet_road("alley", ROAD, puddle=0.55, size=0.5, rough=0.22)
    G = city.Boxes()
    G.box((-40, -20, -1), (40, 200, 0))
    G.done("ground", ground)
    wall = city.plain("wall", tk.mix(P["background"], P["muted"], 0.14), roughness=0.75)
    W = city.Boxes()
    W.box((-30, -5, 0), (-4.5, 60, 28))   # left wall
    W.box((3.8, -5, 0), (30, 60, 24))     # right wall
    W.box((-30, 64, 0), (30, 90, 34))     # the end of the alley
    W.box((-4.5, 1.2, 0), (-4.3, 4.6, 3.0))  # a shutter edge on the left, near
    W.done("walls", wall)
    D = city.Boxes()
    D.box((-2.6, -5, -0.05), (-2.3, 60, 0.01))
    D.done("drain", city.plain("drain", P["background"], roughness=0.2, metallic=0.6))
    # the counter under its canopy, with a stool and a kettle; nobody there
    wood = city.plain("wood", tk.mix(P["background"], P["brown"], 0.3), roughness=0.6)
    C = city.Boxes()
    C.box((1.2, 13.6, 0), (3.8, 14.4, 1.0))
    C.box((0.9, 12.9, 2.75), (3.8, 15.0, 2.85))
    C.box((1.0, 13.0, 0), (1.08, 13.08, 2.75))
    C.done("counter", wood)
    # the counter's front: a shelf line under the top and a cloth hung over the edge
    F = city.Boxes()
    F.box((1.15, 13.52, 0.62), (3.85, 13.6, 0.66))   # the shelf, a thin ledge
    F.done("shelf", city.plain("shelf", tk.mix(P["background"], P["brown"], 0.5), roughness=0.6))
    K = city.Boxes()
    K.box((1.85, 13.52, 0.22), (2.55, 13.57, 1.0))   # the cloth
    K.done("cloth", city.plain("cloth", tk.mix(P["background"], P["blue"], 0.35), roughness=0.9))
    steel = city.plain("steel", STEEL, roughness=0.35, metallic=0.8)
    tk.cylinder("stool", 0.19, 0.06, (1.75, 12.9, 0.66), steel, segments=20)
    city.tube("stool_leg", [[(1.75, 12.9, 0), (1.75, 12.9, 0.66)]], 0.03, steel)
    tk.cylinder("kettle", 0.13, 0.2, (2.9, 13.9, 1.1), steel, segments=20)
    tk.sphere("kettle_lid", 0.12, (2.9, 13.9, 1.2), steel, seg=14)
    city.steam("kettle_steam", (2.9, 13.9, 1.3), 1.4, 0.35, 2.5, MIST, glow=tk.mix(MIST, ORANGE, 0.5),
               glow_strength=0.5)
    for k, x in enumerate((1.45, 2.05, 2.65, 3.25)):  # paper lanterns: three orange, one red
        col, s = (RED, 3.0) if k == 2 else (ORANGE, 2.4)
        tk.cylinder("lantern", 0.17, 0.42, (x, 13.25, 2.3), tk.emissive(f"lantern{k}", srgb(col), s), segments=20)
    tk.light("POINT", (2.3, 12.6, 1.9), 650, srgb(ORANGE), size=0.6).visible_camera = False
    city.mist("counter_mist", (2.3, 13.3, 1.8), 5.4, 0.09, MIST, glow=ORANGE, glow_strength=0.05)
    # a vending machine far down on the left, cyan
    V = city.Boxes()
    V.box((-4.5, 18.0, 0.35), (-4.42, 18.9, 1.75))
    V.done("vending", tk.emissive("vending", srgb(tk.mix(CYAN, P["background"], 0.3)), 1.6))
    tk.set_world(srgb(SKY), 0.1)
    look(eye, 35, 720)


def scene(rng=None):
    sc = tk.reset()
    sc.cycles.seed = SEED
    sc.cycles.volume_bounces = 2
    sc.view_settings.look = "AgX - Punchy"
    build(random.Random(SEED))
    return sc


if __name__ == "__main__":
    city.run(scene, NAME, samples=SAMPLES)
