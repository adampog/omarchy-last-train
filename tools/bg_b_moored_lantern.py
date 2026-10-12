"""Scene B, Moored lantern: a paper sphere lit from inside, tethered in its cradle on a roof, glowing through low cloud.

Original art from geometry and procedural shaders. Every colour is a colors.toml value or a mix of two.

    uv run tools/bg_b_moored_lantern.py                       # backgrounds/b-moored-lantern.png at 3440x1440
    uv run tools/bg_b_moored_lantern.py --percent 25 --samples 48 --out /tmp/x
"""

import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import city  # noqa: E402
import roughs as rg  # noqa: E402  (the camera, roof and far city the rough was signed off with)
from scenes import srgb, node, link  # noqa: E402

P = tk.palette()
NAME = "b-moored-lantern"
SEED = rg.SEEDS["B"]
SAMPLES = 160

DECK_Z = 58.4
C = (4.24, 21.4, 62.0)  # the lantern's centre
CORE = tk.mix(P["bright_yellow"], P["foreground"], 0.3)


def paper():
    """Lantern paper lit from inside: the hot core shows through the middle, the rim is deeper orange."""
    mat = bpy.data.materials.new("lantern")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial")
    lw = node(nt, "ShaderNodeLayerWeight", Blend=0.42)
    em = node(nt, "ShaderNodeEmission")
    link(nt, city.mix_rgb(nt, lw.outputs["Facing"], srgb(CORE), srgb(rg.ORANGE)), em.inputs["Color"])
    link(nt, city.math_node(nt, "MULTIPLY_ADD", lw.outputs["Facing"], -0.9, 2.0), em.inputs["Strength"])
    link(nt, em.outputs[0], out.inputs["Surface"])
    return mat


def lantern(steel):
    c = C
    tk.sphere("lantern", 2.0, c, paper(), seg=64)
    city.tube("seam", [city.ring(c, 2.01, axis="z")], 0.035, steel, cyclic=True)
    city.tube("cradle", [city.ring((c[0], c[1], 59.6), 1.2, axis="z")], 0.07, steel, cyclic=True)
    legs = [[(c[0] + 1.2 * math.cos(a), c[1] + 1.2 * math.sin(a), 59.6),
             (c[0] + 1.7 * math.cos(a), c[1] + 1.7 * math.sin(a), DECK_Z)] for a in (0.6, 2.2, 3.8, 5.4)]
    city.tube("legs", legs, 0.06, steel)
    ties = [[(c[0] + 2.0 * math.cos(a), c[1] + 2.0 * math.sin(a), 62.0),
             (c[0] + 6.5 * math.cos(a), c[1] + 6.5 * math.sin(a), DECK_Z)] for a in (0.3, 2.5, 4.4)]
    city.tube("cables", ties, 0.025, steel)
    tk.light("POINT", (c[0], c[1] - 2.6, c[2]), 2500, srgb(rg.ORANGE), size=1.5).visible_camera = False
    city.mist("lantern_mist", c, 9.0, 0.05, rg.MIST, glow=rg.ORANGE, glow_strength=0.03)
    # the cradle's base: a low plinth under the legs, and a block where each cable is made fast
    conc = city.plain("plinth", rg.DECK, roughness=0.7)
    tk.cylinder("plinth", 2.15, 0.2, (c[0], c[1], DECK_Z + 0.1), conc, segments=48)
    A = city.Boxes()
    for a in (0.3, 2.5, 4.4):
        x, y = c[0] + 6.5 * math.cos(a), c[1] + 6.5 * math.sin(a)
        A.box((x - 0.3, y - 0.3, DECK_Z), (x + 0.3, y + 0.3, DECK_Z + 0.28))
    A.done("anchors", conc)


def deck_things(steel):
    """The near layer: the parapet with its coping, and a cable drum left on the deck."""
    wall = city.plain("near_parapet", rg.STEEL, roughness=0.5)
    B = city.Boxes()
    B.box((1.5, 5.6, DECK_Z), (14, 6.0, 59.45))
    B.box((1.42, 5.52, 59.45), (14, 6.08, 59.53))    # coping
    B.done("near_parapet", wall)
    # a cable drum on its side, left of the cradle
    at, yaw = (-1.6, 17.0, DECK_Z + 0.46), math.radians(52)
    ax = (math.cos(yaw), math.sin(yaw))
    wood = city.plain("drum", tk.mix(P["background"], P["brown"], 0.3), roughness=0.7)
    for off, r, d, mat in ((-0.33, 0.46, 0.06, wood), (0.33, 0.46, 0.06, wood), (0.0, 0.26, 0.6, steel)):
        ob = tk.cylinder("drum", r, d, (at[0] + off * ax[0], at[1] + off * ax[1], at[2]), mat, segments=40)
        ob.rotation_euler = (0, math.radians(90), yaw)
    # two masts behind, a red dot on each
    for x in (9.5, 11.5):
        top = 64.4 + (x - 9.5) * 0.45
        city.tube("mast", [[(x, 26.0, DECK_Z), (x, 26.0, top)]], 0.05, steel)
        tk.sphere("dot", 0.09, (x, 26.0, top + 0.1), tk.emissive("dot", srgb(rg.RED), 6.0), seg=12)


def build():
    sc = tk.reset()
    sc.cycles.seed = SEED
    sc.cycles.volume_bounces = 2
    sc.view_settings.look = "AgX - Punchy"
    rng = random.Random(SEED)
    rg.roof(DECK_Z, 34.0)
    steel = city.plain("steel", rg.STEEL, roughness=0.4, metallic=0.7)
    lantern(steel)
    deck_things(steel)
    # the low cloud the lantern glows through: thickest on the deck, a soft ceiling below the sphere's top
    city.low_cloud("cloud", (2.0, 27.0, 61.0), (150.0, 30.0, 12.0), DECK_Z, 64.6, CLOUD, rg.MIST, size=4.5,
                   frame=float(SEED))
    rg.far(rng, count=420, near=90, heights=(30, 74), spread=65, top=110.0, glow_strength=0.008, tall=0.0,
           bay=1.75, floor_h=3.0)
    tk.set_world(srgb(rg.SKY), 0.05)
    rg.look((0.0, 0.0, 60.0), 28, 850)
    return sc


CLOUD = 0.11  # the cloud's density on the deck

if __name__ == "__main__":
    city.run(build, NAME, samples=SAMPLES)
