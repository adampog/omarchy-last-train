"""Scene C, Rider's stop: a tall trail bike parked on a wet elevated road, a dark shape against the city's orange haze.

Original art from geometry and procedural shaders. Every colour is a colors.toml value or a mix of two.

    uv run tools/bg_c_riders_stop.py                       # backgrounds/c-riders-stop.png at 3440x1440
    uv run tools/bg_c_riders_stop.py --percent 25 --samples 48 --out /tmp/x
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import city  # noqa: E402
import roughs as rg  # noqa: E402  (the camera and far city the rough was signed off with)
from scenes import srgb  # noqa: E402

P = tk.palette()
NAME = "c-riders-stop"
SEED = rg.SEEDS["C"]
SAMPLES = 160

ROAD_Z = 28.0
WHEEL_R = 0.34
AXLE = 0.75                    # each axle this far from the middle of the bike
RAKE = math.radians(25)        # the fork, from vertical
FORK = 0.98                    # its length, axle to the top clamp
HEAD = (AXLE - FORK * math.sin(RAKE), WHEEL_R + FORK * math.cos(RAKE))  # top of the fork: along, up


def bike(at, heading):
    """A tall upright trail bike on its stand, built from tubes and boxes: equal spoked wheels, a long upright
    fork, a round lamp, a slim tank, a flat seat, a short tail with a rack and one pannier. No fairing, no
    markings; its only light is the instrument dot and a dim lamp."""
    a = math.radians(heading)
    f, r = (math.sin(a), math.cos(a)), (math.cos(a), -math.sin(a))
    body = city.plain("bike", rg.BIKE, roughness=0.35, metallic=0.7)
    dull = city.plain("bike_dull", tk.mix(P["background"], P["selection"], 0.12), roughness=0.6)
    steel = city.plain("bike_steel", rg.STEEL, roughness=0.3, metallic=0.9)
    tyre = city.plain("tyre", P["background"], roughness=0.7)

    def T(u, w, z):  # along the bike, to its right, up
        return (at[0] + u * f[0] + w * r[0], at[1] + u * f[1] + w * r[1], at[2] + z)

    def part(size, u, w, z, mat=body, pitch=0.0, bevel=0.03):
        ob = tk.box("bike_part", size, T(u, w, z), mat, bevel=bevel)  # size is across, along, up
        ob.rotation_euler = (math.radians(pitch), 0, -a)
        return ob

    def across(radius, depth, u, w, z, mat, segments=32):
        ob = tk.cylinder("bike_round", radius, depth, T(u, w, z), mat, segments=segments)
        ob.rotation_euler = (0, math.radians(90), -a)
        return ob

    def circle(u0, rad, n=56):
        return [T(u0 + rad * math.cos(2 * math.pi * k / n), 0, WHEEL_R + rad * math.sin(2 * math.pi * k / n))
                for k in range(n)]

    # wheels: a tyre and a plain rim ring, open inside, no spokes
    for u in (AXLE, -AXLE):
        city.tube("tyre", [circle(u, WHEEL_R - 0.055)], 0.055, tyre, cyclic=True)
        city.tube("rim", [circle(u, WHEEL_R - 0.12)], 0.03, body, cyclic=True)
    across(0.125, 0.008, AXLE, -0.07, WHEEL_R, steel)    # front brake disc
    across(0.1, 0.008, -AXLE, 0.07, WHEEL_R, steel)      # rear sprocket

    hu, hz = HEAD
    # engine and frame
    part((0.24, 0.42, 0.3), 0.06, 0, 0.5, dull)
    part((0.2, 0.2, 0.24), 0.12, 0, 0.72, dull, pitch=-12)        # the cylinder, leaning forward
    part((0.26, 0.3, 0.05), 0.04, 0, 0.33, dull)                  # the plate under the engine
    frame = [[T(hu + 0.02, 0, hz - 0.14), T(0.3, w, 0.4), T(0.0, w, 0.31), T(-0.12, w, 0.45)] for w in (-0.1, 0.1)]
    frame += [[T(hu + 0.02, 0, hz - 0.08), T(-0.05, 0, 0.9), T(-0.12, 0, 0.45)]]
    frame += [[T(-0.05, w, 0.86), T(-0.82, w, 0.9)] for w in (-0.1, 0.1)]             # the subframe under the seat
    frame += [[T(-0.12, w, 0.45), T(-0.5, w, 0.86)] for w in (-0.1, 0.1)]
    city.tube("frame", frame, 0.018, body)
    part((0.2, 0.4, 0.19), 0.17, 0, 0.94, bevel=0.05)             # the slim tank
    part((0.22, 0.6, 0.07), -0.33, 0, 0.92, dull, bevel=0.025)    # the flat seat
    part((0.17, 0.2, 0.05), -0.72, 0, 0.9, bevel=0.0)            # the short tail, a straight line with the rack
    part((0.13, 0.3, 0.025), -0.7, 0, 0.74, dull, pitch=14, bevel=0.0)  # the rear guard under it
    # rack and pannier: a flat plate level with the seat line, two straight struts down to the subframe
    part((0.4, 0.4, 0.03), -0.75, 0, 0.935, body, bevel=0.0)
    city.tube("rack", [[T(-0.92, w, 0.92), T(-0.7, w * 0.6, 0.6)] for w in (-0.16, 0.16)], 0.012, body)
    part((0.14, 0.38, 0.29), -0.66, 0.24, 0.7, dull, bevel=0.03)
    # the fork: two long legs, thicker below, with clamps and a high guard over the wheel
    low, top, mid = [], [], 0.45
    for w in (-0.085, 0.085):
        m = (AXLE - FORK * mid * math.sin(RAKE), WHEEL_R + FORK * mid * math.cos(RAKE))
        low.append([T(AXLE, w, WHEEL_R), T(m[0], w, m[1])])
        top.append([T(m[0], w, m[1]), T(hu, w, hz)])
    city.tube("fork_low", low, 0.03, body)
    city.tube("fork_top", top, 0.02, steel)
    part((0.24, 0.07, 0.035), hu, 0, hz, bevel=0.01)
    part((0.24, 0.07, 0.035), hu + 0.09, 0, hz - 0.2, bevel=0.01)
    part((0.13, 0.4, 0.025), AXLE - 0.1, 0, 0.78, dull, pitch=-10, bevel=0.0)  # high front guard
    # bars, levers and mirrors
    bars = [[T(hu - 0.02, -0.4, hz + 0.1), T(hu, -0.14, hz + 0.05), T(hu, 0.14, hz + 0.05), T(hu - 0.02, 0.4, hz + 0.1)]]
    bars += [[T(hu, w, hz + 0.06), T(hu - 0.05, w * 1.15, hz + 0.26)] for w in (-0.27, 0.27)]
    city.tube("bars", bars, 0.014, body)
    for w in (-0.4, 0.4):
        city.tube("grip", [[T(hu - 0.02, w, hz + 0.1), T(hu - 0.02, w * 0.72, hz + 0.09)]], 0.02, tyre)
    for w in (-0.31, 0.31):
        ob = tk.cylinder("mirror", 0.05, 0.012, T(hu - 0.05, w, hz + 0.29), dull, segments=20)
        ob.rotation_euler = (math.radians(80), 0, -a)
    # exhaust, swept up along the right side
    city.tube("pipe", [[T(0.2, 0.1, 0.5), T(0.12, 0.14, 0.38), T(-0.15, 0.15, 0.4), T(-0.4, 0.16, 0.56)]], 0.022, steel)
    city.tube("silencer", [[T(-0.4, 0.16, 0.56), T(-0.82, 0.17, 0.8)]], 0.047, dull)
    # swingarm on both sides, twin shocks, the stand
    city.tube("swingarm", [[T(-AXLE, w, WHEEL_R), T(-0.12, w, 0.45)] for w in (-0.1, 0.1)], 0.026, body)
    city.tube("shocks", [[T(-0.58, w, 0.4), T(-0.46, w, 0.84)] for w in (-0.13, 0.13)], 0.022, steel)
    city.tube("stand", [[T(-0.08, -0.1, 0.32), T(-0.2, -0.36, 0.0)]], 0.016, body)
    # the round lamp in its shell, lit low, and the instrument dot
    lu, lz = hu + 0.2, hz - 0.18
    tk.sphere("lamp_shell", 0.1, T(lu, 0, lz), body, seg=24)
    ob = tk.cylinder("lamp_lens", 0.085, 0.02, T(lu + 0.075, 0, lz), tk.emissive("lamp", srgb(rg.MIST), 1.6),
                     segments=24)
    ob.rotation_euler = (math.radians(90), 0, -a)
    tk.sphere("instrument", 0.028, T(hu + 0.02, 0, hz + 0.07), tk.emissive("instrument", srgb(rg.CYAN), 8.0), seg=10)
    lamp = tk.light("SPOT", T(lu + 0.12, 0, lz), LAMP, srgb(tk.mix(rg.MIST, rg.ORANGE, 0.2)), size=0.06,
                    rotation=(math.radians(66), 0, -a))
    lamp.data.spot_size = math.radians(58)
    lamp.data.spot_blend = 0.7


LAMP = 260  # watts: a dim pool on the road in front of the bike


def build():
    sc = tk.reset()
    sc.cycles.seed = SEED
    sc.cycles.volume_bounces = 2
    sc.view_settings.look = "AgX - Punchy"
    rng = random.Random(SEED)
    z = ROAD_Z
    road = city.wet_road("road", rg.ROAD, puddle=0.5, size=1.0, rough=0.22)
    B = city.Boxes()
    B.box((-4.4, -20, z - 1.2), (6.4, 900, z))  # the elevated road
    B.done("deck", road)
    steel = city.plain("steel", rg.STEEL, roughness=0.4, metallic=0.7)
    for x in (-4.2, 6.2):  # rails either side
        city.tube("rail", [[(x, -10, z + 0.95), (x, 600, z + 0.95)], [(x, -10, z + 0.55), (x, 600, z + 0.55)]], 0.04,
                  steel)
        city.tube("posts", [[(x, y, z), (x, y, z + 0.95)] for y in range(-8, 200, 4)], 0.045, steel)
    tk.box("near_post", (0.16, 0.16, 0.5), (-1.95, 2.65, z + 0.25), steel)  # the post at bottom left
    tk.box("near_post_cap", (0.22, 0.22, 0.05), (-1.95, 2.65, z + 0.525), steel)  # its cap, a step wider
    bike((-2.4, 5.6, z), 26.0)
    # the city fills the right third, orange in its haze; one red window panel in it
    rg.far(rng, count=200, near=260, spread=13, heights=(40, 110), glow=rg.HAZE_ORANGE, glow_strength=0.009,
           top=100.0, lit=0.1, turn=14.0, tall=0.0, bay=2.2, floor_h=3.2)
    T = city.Boxes()
    T.box((11.0, 240, 0), (27.0, 262, 62))
    T.done("sign_tower", city.plain("sign_tower", rg.BODY, roughness=0.5))
    S = city.Boxes()
    S.box((13.0, 239.5, 44), (17.0, 240, 56))
    S.done("red_sign", tk.emissive("red_sign", srgb(rg.RED), 9.0))
    city.mist("sign_mist", (15, 236, 50), 26.0, 0.012, rg.MIST, glow=rg.RED, glow_strength=0.012)
    tk.light("POINT", (-9.0, 1.0, z + 3.5), 2600, srgb(P["blue"]), size=1.0)  # the blue rim, from behind and left
    tk.set_world(srgb(rg.SKY), 0.05)
    rg.look((0.0, 0.0, z + 0.35), 28, 900, yaw=-12.2)
    return sc


if __name__ == "__main__":
    city.run(build, NAME, samples=SAMPLES)
