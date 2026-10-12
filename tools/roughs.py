"""Roughs of scenes B to G at 860x360: camera, light position and masses, no detail.

Original art from geometry and procedural shaders. Every colour is a colors.toml value or a mix of two.

    uv run tools/roughs.py --scene B                 # .cache/roughs/rough-b.png
    uv run tools/roughs.py --scene all --out /tmp/x
"""

import argparse
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import city  # noqa: E402
from scenes import srgb  # noqa: E402

P = tk.palette()
SAMPLES = 64
SEEDS = {"B": 11, "C": 12, "D": 13, "E": 14, "F": 15, "G": 16}

SKY = tk.mix(P["background"], P["selection"], 0.5)
BODY = tk.mix(P["background"], P["selection"], 0.12)
BODY_FAR = tk.mix(P["background"], P["selection"], 0.3)
GLASS = tk.mix(P["background"], P["blue"], 0.1)
WIN_A = tk.mix(P["bright_blue"], P["muted"], 0.3)
WIN_B = tk.mix(P["blue"], P["background"], 0.4)
WIN_WARM = tk.mix(P["orange"], P["foreground"], 0.3)
ROAD = tk.mix(P["background"], P["muted"], 0.16)
DECK = tk.mix(P["background"], P["muted"], 0.24)
STEEL = tk.mix(P["background"], P["muted"], 0.3)
BIKE = tk.mix(P["background"], P["selection"], 0.25)
RED = P["accent"]
ORANGE = P["orange"]
CYAN = P["cyan"]
MIST = P["foreground"]
HAZE_BLUE = tk.mix(P["selection"], P["blue"], 0.3)
HAZE_ORANGE = tk.mix(P["orange"], P["background"], 0.35)


def look(eye, lens, horizon, yaw=0.0):
    """A camera at `eye` with the horizon on row `horizon` of the 1440; yaw in degrees, left is negative."""
    pitch = math.atan((horizon - 720) / (1720 / (18 / lens)))
    a = math.radians(yaw)
    cam = tk.camera(eye, (eye[0] + 100 * math.sin(a), eye[1] + 100 * math.cos(a), eye[2] + 100 * math.tan(pitch)),
                    lens)
    cam.data.clip_end = 3000
    return cam


def far(rng, count=320, near=120, far_=900, spread=60, heights=(18, 55), glow=HAZE_BLUE, glow_strength=0.012,
        top=150.0, lit=0.08, start=None, turn=0.0, tall=0.03):
    mat = city.facade("far", BODY_FAR, GLASS, WIN_A, WIN_B, WIN_WARM, bay=3.5, floor_h=4.0, lit=lit, strength=0.9,
                      warm_part=0.2, ground=6.0)
    city.skyline(rng, mat, None, count, near, far_, spread, heights, tall=tall, turn=turn)
    y0 = near if start is None else start
    city.haze_layer("far_haze", (0, y0 + 600, top / 2 + 5), (2400, 1200, top + 30), top, 0.003, MIST, glow,
                    glow_strength, base=0.0)


def roof(z, edge):
    """The roof we stand on: a deck `z` metres up, ending `edge` metres ahead."""
    deck = city.wet_road("deck", DECK, puddle=0.5, size=1.2, rough=0.3)
    B = city.Boxes()
    B.box((-40, -12, 0), (40, edge, z))
    B.done("roof", deck)
    K = city.Boxes()
    K.box((-40, edge - 0.4, z), (40, edge, z + 0.5))  # the far parapet
    K.done("parapet", city.plain("parapet", STEEL, roughness=0.5))


# ---------- B, moored lantern ----------

def scene_b(rng):
    eye = (0.0, 0.0, 60.0)
    roof(58.4, 34.0)
    steel = city.plain("steel", STEEL, roughness=0.4, metallic=0.7)
    c = (4.24, 21.4, 62.0)
    # the lantern: a matte sphere lit from inside, with a seam round its middle, in a cradle, held by three cables
    tk.sphere("lantern", 2.0, c, tk.emissive("lantern", srgb(ORANGE), 1.7), seg=48)
    city.tube("seam", [city.ring(c, 2.01, axis="z")], 0.035, steel, cyclic=True)
    city.tube("cradle", [city.ring((c[0], c[1], 59.6), 1.2, axis="z")], 0.07, steel, cyclic=True)
    legs = [[(c[0] + 1.2 * math.cos(a), c[1] + 1.2 * math.sin(a), 59.6),
             (c[0] + 1.7 * math.cos(a), c[1] + 1.7 * math.sin(a), 58.4)] for a in (0.6, 2.2, 3.8, 5.4)]
    city.tube("legs", legs, 0.06, steel)
    ties = [[(c[0] + 2.0 * math.cos(a), c[1] + 2.0 * math.sin(a), 62.0),
             (c[0] + 6.5 * math.cos(a), c[1] + 6.5 * math.sin(a), 58.4)] for a in (0.3, 2.5, 4.4)]
    city.tube("cables", ties, 0.025, steel)
    tk.light("POINT", (c[0], c[1] - 2.6, c[2]), 2500, srgb(ORANGE), size=1.5).visible_camera = False
    city.mist("lantern_mist", c, 9.0, 0.05, MIST, glow=ORANGE, glow_strength=0.03)
    # the near layer: parapet at bottom right, and two masts with a red dot each
    B = city.Boxes()
    B.box((1.5, 5.6, 58.4), (14, 6.0, 59.45))
    B.done("near_parapet", city.plain("near_parapet", STEEL, roughness=0.5))
    for x in (9.5, 11.5):
        top = 64.4 + (x - 9.5) * 0.45
        city.tube("mast", [[(x, 26.0, 58.4), (x, 26.0, top)]], 0.05, steel)
        tk.sphere("dot", 0.09, (x, 26.0, top + 0.1), tk.emissive("dot", srgb(RED), 6.0), seg=12)
    far(rng, count=420, near=90, heights=(30, 74), spread=65, top=110.0, glow_strength=0.008, tall=0.0)
    tk.set_world(srgb(SKY), 0.05)
    look(eye, 28, 850)


# ---------- C, rider's stop ----------

def bike(at, heading):
    """A tall upright trail bike on its stand: long forks, round lamp, high seat, short tail, a pannier."""
    a = math.radians(heading)
    f, r = (math.sin(a), math.cos(a)), (math.cos(a), -math.sin(a))
    body = city.plain("bike", BIKE, roughness=0.35, metallic=0.7)
    tyre = city.plain("tyre", P["background"], roughness=0.7)

    def T(u, w, z):
        return (at[0] + u * f[0] + w * r[0], at[1] + u * f[1] + w * r[1], at[2] + z)

    def part(size, u, w, z):
        ob = tk.box("bike_part", size, T(u, w, z), body)
        ob.rotation_euler = (0, 0, -a)
        return ob

    for u in (0.75, -0.75):
        ob = tk.cylinder("wheel", 0.34, 0.11, T(u, 0, 0.34), tyre, segments=40)
        ob.rotation_euler = (0, math.radians(90), -a)
    part((0.26, 0.62, 0.5), 0.03, 0, 0.55)    # engine and frame (size is across, along, up)
    part((0.3, 0.44, 0.26), 0.2, 0, 0.93)     # tank
    part((0.26, 0.62, 0.1), -0.32, 0, 0.95)   # high seat
    part((0.2, 0.16, 0.07), -0.7, 0, 0.94)    # short tail
    part((0.14, 0.4, 0.3), -0.62, 0.22, 0.68)  # pannier
    part((0.5, 0.4, 0.03), -0.72, 0, 1.0)     # rack
    part((0.14, 0.36, 0.04), 0.75, 0, 0.74)   # high front guard
    tubes = [[T(0.75, w, 0.34), T(0.42, w, 1.2)] for w in (-0.09, 0.09)]          # long forks
    tubes += [[T(-0.75, w, 0.34), T(-0.1, w, 0.48)] for w in (-0.1, 0.1)]         # swingarm, both sides
    tubes += [[T(0.4, -0.38, 1.22), T(0.4, 0.38, 1.22)]]                          # bars
    tubes += [[T(0.4, w, 1.22), T(0.36, w * 1.1, 1.42)] for w in (-0.3, 0.3)]     # mirror stalks
    tubes += [[T(-0.1, -0.12, 0.3), T(-0.2, -0.36, 0.0)]]                         # stand
    city.tube("bike_tubes", tubes, 0.028, body)
    tk.sphere("headlamp", 0.1, T(0.55, 0, 1.04), body, seg=16)
    tk.sphere("instrument", 0.03, T(0.36, 0, 1.2), tk.emissive("instrument", srgb(CYAN), 8.0), seg=10)
    lamp = tk.light("SPOT", T(0.66, 0, 1.04), 60, srgb(MIST), size=0.05,
                    rotation=(math.radians(72), 0, -a))
    lamp.data.spot_size = math.radians(50)


def scene_c(rng):
    eye = (0.0, 0.0, 0.35)
    road = city.wet_road("road", ROAD, puddle=0.5, size=1.0, rough=0.22)
    B = city.Boxes()
    B.box((-4.4, -20, 28.0 - 1.2), (6.4, 900, 28.0))  # the elevated road, 28 m up
    B.done("deck", road)
    steel = city.plain("steel", STEEL, roughness=0.4, metallic=0.7)
    z = 28.0
    for x in (-4.2, 6.2):  # rails either side
        city.tube("rail", [[(x, -10, z + 0.95), (x, 600, z + 0.95)], [(x, -10, z + 0.55), (x, 600, z + 0.55)]], 0.04,
                  steel)
        city.tube("posts", [[(x, y, z), (x, y, z + 0.95)] for y in range(-8, 200, 4)], 0.045, steel)
    tk.box("near_post", (0.16, 0.16, 0.5), (-1.95, 2.65, z + 0.25), steel)  # the post at bottom left
    bike((-2.4, 5.6, z), 26.0)
    # the city fills the right third, orange in its haze; one red sign in it
    far(rng, count=200, near=260, spread=13, heights=(40, 110), glow=HAZE_ORANGE, glow_strength=0.009, top=100.0,
        lit=0.1, turn=14.0, tall=0.0)
    T = city.Boxes()
    T.box((11.0, 240, 0), (27.0, 262, 62))
    T.done("sign_tower", city.plain("sign_tower", BODY, roughness=0.5))
    S = city.Boxes()
    S.box((13.0, 239.5, 44), (17.0, 240, 56))
    S.done("red_sign", tk.emissive("red_sign", srgb(RED), 9.0))
    city.mist("sign_mist", (15, 236, 50), 26.0, 0.012, MIST, glow=RED, glow_strength=0.012)
    tk.light("POINT", (-9.0, 1.0, z + 3.5), 2600, srgb(P["blue"]), size=1.0)  # the blue rim, from behind and left
    tk.set_world(srgb(SKY), 0.05)
    look((eye[0], eye[1], z + eye[2]), 28, 900, yaw=-12.2)


# ---------- D, signal roof ----------

def scene_d(rng):
    eye = (0.0, 0.0, 60.0)
    roof(58.4, 52.0)
    steel = city.plain("steel", STEEL, roughness=0.4, metallic=0.7)
    tk.cylinder("tank", 4.5, 3.1, (8.7, 40.0, 58.4 + 1.55), steel, segments=40)
    top = 69.25
    legs = [[(8.9 + dx, 45.0 + dy, 58.4), (8.9 + dx * 0.15, 45.0 + dy * 0.15, top)]
            for dx, dy in ((-0.7, -0.5), (0.7, -0.5), (0.0, 0.7))]
    bars = [[(8.9 - 0.7 * (1 - k / 9), 44.5, 58.4 + k * 1.2), (8.9 + 0.7 * (1 - (k + 1) / 9), 44.5, 59.6 + k * 1.2)]
            for k in range(8)]
    city.tube("mast", legs + bars, 0.05, steel)
    b = (8.9, 45.0, top + 0.2)
    tk.sphere("beacon", 0.28, b, tk.emissive("beacon", srgb(RED), 40.0), seg=16)
    tk.light("POINT", (b[0], b[1] - 0.6, b[2]), 11000, srgb(RED), size=0.5).visible_camera = False
    city.mist("beacon_mist", b, 13.0, 0.06, MIST, squash=(2.2, 1.0, 0.62), glow=P["bright_red"], glow_strength=0.12,
              power=2.4)
    # smaller masts and dishes to the left of it
    small = [[(x, 35.0, 58.4), (x, 35.0, 58.4 + h)] for x, h in ((-5.0, 4.5), (-2.2, 6.0), (0.6, 3.2), (3.0, 5.0))]
    city.tube("small_masts", small, 0.04, steel)
    for x, zz in ((-3.6, 59.6), (1.8, 59.9)):
        d = tk.cylinder("dish", 0.75, 0.12, (x, 34.0, zz), steel, segments=24)
        d.rotation_euler = (math.radians(65), 0, math.radians(20))
        city.tube("dish_post", [[(x, 34.2, 58.4), (x, 34.2, zz)]], 0.04, steel)
    far(rng, count=420, near=110, heights=(30, 76), spread=65, top=110.0, glow_strength=0.036, tall=0.0)
    tk.set_world(srgb(SKY), 0.1)
    look(eye, 28, 900)


# ---------- E, last train ----------

def scene_e(rng):
    eye = (0.0, 0.0, 1.5)
    W = city.Boxes()
    W.box((-900, -40, -6), (900, 160, -1.2))
    W.done("canal", city.water("canal", tk.mix(P["background"], P["selection"], 0.1)))
    stone = city.plain("stone", STEEL, roughness=0.6)
    Q = city.Boxes()
    Q.box((-40, -10, -3), (-3.0, 9.0, 0.0))      # the quay we stand on, bottom left
    Q.box((-900, 150, -3), (900, 1000, 0.3))     # the far bank
    Q.done("quay", stone)
    tk.cylinder("bollard", 0.18, 0.6, (-4.3, 8.2, 0.3), stone, segments=20)
    # the viaduct across the frame, its deck 6.55 m up, 90 m away
    vy, vz = 90.0, 6.55
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


# ---------- F, tunnel mouth ----------

def scene_f(rng):
    eye = (0.0, 0.0, 1.4)
    road = city.wet_road("road", ROAD, puddle=0.52, size=1.0, rough=0.2)
    G = city.Boxes()
    G.box((-400, -60, -1), (400, 46, 0))
    G.box((-15.4, 46, -1), (-5.4, 220, 0))  # the road on into the tunnel
    G.done("ground", road)
    wall = city.plain("wall", tk.mix(P["background"], P["muted"], 0.2), roughness=0.7)
    Wl = city.Boxes()
    Wl.box((-200, 46, 0), (-15.4, 240, 14))     # the hill and its retaining wall, left of the mouth
    Wl.box((-5.4, 46, 0), (200, 240, 14))       # and right of it
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


# ---------- G, the counter ----------

def scene_g(rng):
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


SCENES = {"B": scene_b, "C": scene_c, "D": scene_d, "E": scene_e, "F": scene_f, "G": scene_g}


def render(key, out, samples, percent):
    sc = tk.reset()
    sc.cycles.seed = SEEDS[key]
    sc.cycles.volume_bounces = 2
    sc.view_settings.look = "AgX - Punchy"
    SCENES[key](random.Random(SEEDS[key]))
    sc.render.resolution_percentage = percent
    sc.cycles.samples = samples
    tk.render(sc, os.path.join(out, f"rough-{key.lower()}.png"))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", default="all", choices=[*SCENES, "all"])
    ap.add_argument("--out", default=os.path.join(tk.REPO, ".cache", "roughs"))
    ap.add_argument("--samples", type=int, default=SAMPLES)
    ap.add_argument("--percent", type=int, default=25)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    for key in (SCENES if a.scene == "all" else [a.scene]):
        render(key, a.out, a.samples, a.percent)
