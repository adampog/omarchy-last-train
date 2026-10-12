"""Scene A, Rain gate: a wet street at night under one red sign stack, the street bending away to the right.

Original art from geometry and procedural shaders. Every colour is a colors.toml value or a mix of two.

    uv run tools/bg_a_rain_gate.py                       # backgrounds/a-rain-gate.png at 3440x1440
    uv run tools/bg_a_rain_gate.py --percent 25 --samples 48 --out /tmp/x
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import city  # noqa: E402
from scenes import srgb  # noqa: E402

P = tk.palette()
NAME = "a-rain-gate"
SEED = 7
SAMPLES = 160

SKY = tk.mix(P["background"], P["selection"], 0.5)
BODY = tk.mix(P["background"], P["selection"], 0.12)
BODY_FAR = tk.mix(P["background"], P["selection"], 0.3)
GLASS = tk.mix(P["background"], P["blue"], 0.1)
WIN_A = tk.mix(P["bright_blue"], P["muted"], 0.3)
WIN_B = tk.mix(P["blue"], P["background"], 0.4)
WIN_WARM = tk.mix(P["orange"], P["foreground"], 0.3)
ROAD = tk.mix(P["background"], P["muted"], 0.16)
PAVE = tk.mix(P["background"], P["muted"], 0.24)
STEEL = tk.mix(P["background"], P["muted"], 0.3)
RED = P["accent"]
RED_BLOOM = P["bright_red"]
SODIUM = P["orange"]
DIM_BLUE = P["blue"]
DIM_ORANGE = P["yellow"]
MIST = P["foreground"]
HAZE_GLOW = tk.mix(P["selection"], P["blue"], 0.3)

CAM = (0.5, 0.0, 1.4)
LENS = 24
PITCH = math.atan(230 / 2293)  # puts the horizon 230 px below the middle of the frame, at y 950
SIGN_Y = 24.0  # the sign stack hangs over the left pavement, this far from the camera
SIGN_X = (-5.5, -2.9)
SIGN_MID = (-4.2, SIGN_Y, 5.35)


def buildings(rng):
    near = city.facade("near", BODY, GLASS, WIN_A, WIN_B, WIN_WARM, bay=2.2, floor_h=3.3, lit=0.045, strength=1.2,
                       warm_part=0.35, ground=3.6)
    B = city.Boxes()
    # left row, its face at x -5.6
    for y0, y1, h in ((3.0, 20.0, 7.0), (20.5, 36.0, 30.0), (36.5, 55.0, 23.0), (55.5, 82.0, 36.0)):
        B.box((-26, y0, 0), (-5.6, y1, h))
    # right row, its face at x 12, ending where the street turns
    for y0, y1, h in ((-4.0, 17.0, 13.0), (17.5, 33.0, 20.0), (33.5, 50.0, 16.5)):
        B.box((12, y0, 0), (34, y1, h))
    # the block that closes the street, and what stands along the turn beyond it
    B.box((-26, 88, 0), (4.0, 112, 21.0))
    for x0, x1, y0, y1, h in ((10, 30, 118, 140, 15), (34, 60, 96, 120, 19), (20, 44, 150, 176, 22),
                              (50, 80, 140, 170, 28)):
        B.box((x0, y0, 0), (x1, y1, h))
    # roof clutter: tanks and plant on the lower roofs
    for x, y, z, s in ((-9, 44, 23, 1.6), (-12, 50, 23, 1.1), (-10, 96, 21, 1.8), (16, 40, 16.5, 1.4),
                       (20, 24, 20, 1.2), (-3, 100, 21, 1.0)):
        B.box((x - s, y - s, z), (x + s, y + s, z + s * 1.5))
    B.done("blocks", near)

    # shopfront details at street level: shutters, awnings, air conditioners, door frames
    dark = city.plain("trim", STEEL, roughness=0.45, metallic=0.6)
    D = city.Boxes()
    for y in (5.0, 9.5, 14.0, 26.5, 31.0, 40.0, 46.0):  # left shutters, proud of the wall
        D.box((-5.6, y, 0.15), (-5.52, y + 3.4, 2.9))
        D.box((-5.6, y - 0.2, 2.9), (-4.6, y + 3.6, 3.05))  # awning
    for y in (1.0, 7.0, 13.0, 19.5, 26.0, 37.0, 44.0):  # right shopfront posts and awnings
        D.box((11.9, y, 0.15), (12.0, y + 0.3, 3.3))
        D.box((10.9, y, 3.1), (12.0, y + 5.2, 3.25))
    for _ in range(26):  # air conditioners on both rows
        left = rng.random() < 0.5
        y, z = rng.uniform(6, 80 if left else 48), rng.uniform(4.2, 17)
        if left:
            D.box((-5.6, y, z), (-5.15, y + 0.9, z + 0.6))
        else:
            D.box((11.55, y, z), (12.0, y + 0.9, z + 0.6))
    D.done("trim", dark)

    # two shopfronts on the right with a faint orange window, and the sodium light at the end of the street
    faint = tk.emissive("faint", srgb(tk.mix(SODIUM, P["background"], 0.25)), 0.16)
    F = city.Boxes()
    F.box((11.93, 21.6, 1.0), (11.97, 23.2, 2.6))
    F.box((11.93, 38.2, 0.9), (11.97, 40.4, 2.6))
    F.box((11.93, 27.5, 3.9), (11.97, 29.0, 5.2))
    F.done("faint_windows", faint)
    shop = tk.emissive("sodium", srgb(SODIUM), 14.0)
    S = city.Boxes()
    S.box((1.6, 87.9, 0.7), (3.2, 87.98, 3.0))
    S.done("sodium_shop", shop)
    tk.light("POINT", (2.4, 85.5, 2.4), 1800, srgb(SODIUM), size=1.0)


def street():
    road = city.wet_road("road", ROAD, puddle=0.52, size=1.0, rough=0.2)
    pave = city.wet_road("pave", PAVE, puddle=0.6, size=0.6, rough=0.22)
    G = city.Boxes()
    G.box((-400, -60, -1.0), (400, 1200, 0.0))
    G.done("ground", road)
    K = city.Boxes()
    K.box((-5.6, -30, 0.0), (-0.6, 88, 0.16))  # left pavement
    K.box((9.4, -30, 0.0), (12.0, 50, 0.16))   # right pavement
    K.box((-26, 80, 0.0), (4.0, 88, 0.16))
    K.done("pavements", pave)

    steel = city.plain("steel", STEEL, roughness=0.35, metallic=0.8)
    # the near layer: a pair of bollards on the kerb, bottom left, in shadow
    for x, y in ((-1.0, 3.0), (-1.0, 3.9)):
        tk.cylinder("bollard", 0.11, 0.78, (x, y, 0.16 + 0.39), steel, segments=24)
        tk.sphere("bollard_cap", 0.125, (x, y, 0.16 + 0.78), steel, seg=20)
    # a kerb rail further on, lamp-less posts, and the grate the steam comes from
    posts = [[(-0.9, y, 0.16), (-0.9, y, 1.05)] for y in range(34, 60, 3)]
    city.tube("rail_posts", posts, 0.04, steel)
    city.tube("rail", [[(-0.9, 34, 1.05), (-0.9, 58, 1.05)], [(-0.9, 34, 0.6), (-0.9, 58, 0.6)]], 0.035, steel)
    Gr = city.Boxes()
    for k in range(7):
        Gr.box((2.9 + k * 0.16, 27.4, 0.0), (2.97 + k * 0.16, 28.6, 0.02))
    Gr.done("grate", steel)
    # cables across the street
    rngc = random.Random(SEED + 1)
    cables = [city.sag((-5.6, y, z), (12.0, y + rngc.uniform(-3, 3), z + rngc.uniform(-1, 1)), rngc.uniform(0.6, 1.4))
              for y, z in ((31.0, 10.5), (44.0, 12.0), (52.0, 9.0), (66.0, 13.5))]
    city.tube("cables", cables, 0.025, steel)


def sign():
    """A stack of three lit frames on one post. The middle one is red and is the light of the picture."""
    x0, x1 = SIGN_X
    y = SIGN_Y
    steel = city.plain("sign_steel", STEEL, roughness=0.4, metallic=0.8)
    board = city.plain("sign_board", tk.mix(P["background"], P["selection"], 0.06), roughness=0.25)
    B = city.Boxes()
    B.box((x1, y + 0.02, 0.16), (x1 + 0.16, y + 0.2, 8.6))  # the post
    for z in (2.6, 5.4, 8.3):  # brackets back to the wall
        B.box((-5.6, y + 0.06, z), (x1, y + 0.16, z + 0.08))
    B.done("sign_post", steel)
    panels = ((7.15, 8.25), (3.95, 6.85), (2.45, 3.65))
    Bd = city.Boxes()
    for z0, z1 in panels:
        Bd.box((x0, y + 0.05, z0), (x1 - 0.05, y + 0.2, z1))
    Bd.done("sign_boards", board)
    f = y - 0.02  # the tubes stand just proud of the boards

    def frame(z0, z1, inset=0.12):
        return [(x0 + inset, f, z0 + inset), (x1 - 0.05 - inset, f, z0 + inset), (x1 - 0.05 - inset, f, z1 - inset),
                (x0 + inset, f, z1 - inset)]

    # top: dim blue, a frame and three bars
    z0, z1 = panels[0]
    city.tube("sign_top_frame", [frame(z0, z1)], 0.022, tk.emissive("dim_blue", srgb(DIM_BLUE), 1.6), cyclic=True)
    city.tube("sign_top_bars", [[(x0 + 0.4, f, z), (x1 - 0.5, f, z)] for z in (7.45, 7.7, 7.95)], 0.02,
              tk.emissive("dim_blue2", srgb(DIM_BLUE), 1.0))
    # middle: red, a double frame, a ring and two bars
    z0, z1 = panels[1]
    red = tk.emissive("red", srgb(RED), 16.0)
    city.tube("sign_red_frame", [frame(z0, z1), frame(z0, z1, 0.3)], 0.035, red, cyclic=True)
    cx = (x0 + x1 - 0.05) / 2
    city.tube("sign_red_ring", [city.ring((cx, f, 5.85), 0.52)], 0.04, red, cyclic=True)
    city.tube("sign_red_bars", [[(x0 + 0.62, f, z), (x1 - 0.67, f, z)] for z in (4.62, 4.95)], 0.04, red)
    # and a red tube down the post to the pavement, so the light reaches the street
    city.tube("sign_red_drop", [[(x1 + 0.08, f, 3.75), (x1 + 0.08, f, 0.45)]], 0.035, red)
    # bottom: dim orange, a frame and upright bars
    z0, z1 = panels[2]
    city.tube("sign_low_frame", [frame(z0, z1)], 0.022, tk.emissive("dim_orange", srgb(DIM_ORANGE), 1.3), cyclic=True)
    city.tube("sign_low_bars", [[(x, f, z0 + 0.32), (x, f, z1 - 0.32)] for x in (-5.0, -4.6, -4.2, -3.8, -3.4)],
              0.02, tk.emissive("dim_orange2", srgb(DIM_ORANGE), 0.8))
    # the throw of the red sign onto street, wall and mist
    lamp = tk.light("POINT", (cx, y - 0.9, 5.2), 8000, srgb(RED), size=0.9)
    lamp.visible_camera = False
    lamp.visible_glossy = False  # the tubes are what the wet street and the glass mirror


def rain(rng):
    """Fine streaks, only where the sign lights them."""
    cx, cy, cz = SIGN_MID
    bins = [[], [], []]
    for _ in range(900):
        r = 1.5 + rng.random() ** 0.7 * 8.0
        a, e = rng.uniform(0, 2 * math.pi), rng.uniform(-0.9, 0.9)
        x, y, z = cx + r * math.cos(a) * math.cos(e), cy - abs(r * math.sin(a) * math.cos(e)) - 0.5, cz + r * math.sin(e)
        if z < 0.4 or z > 8.6 or x < -5.5:
            continue
        ln = rng.uniform(0.25, 0.6)
        bins[min(2, int((r - 1.5) / 2.7))].append([(x, y, z), (x + 0.04, y, z - ln)])
    for k, (pts, s) in enumerate(zip(bins, (2.4, 1.1, 0.45))):
        if pts:
            city.tube(f"rain{k}", pts, 0.003, tk.emissive(f"rain{k}", srgb(RED_BLOOM), s))


def air():
    tk.set_world(srgb(SKY), 0.08)
    # rain mist round the sign, densest at the tubes and carrying their colour
    city.mist("sign_mist", SIGN_MID, 13.0, 0.07, MIST, anisotropy=0.55, squash=(1.0, 1.0, 0.9), glow=RED_BLOOM,
              glow_strength=0.06, power=2.2)
    # a thinner pool of it down the street round the sodium light
    city.mist("shop_mist", (2.3, 84.0, 2.6), 16.0, 0.03, MIST, anisotropy=0.5, glow=SODIUM, glow_strength=0.02)
    city.steam("steam", (3.4, 28.0, 0.02), 7.5, 2.4, 2.6, MIST, glow=tk.mix(MIST, RED_BLOOM, 0.45), glow_strength=0.1)
    # the far city stands in blue haze
    city.haze_layer("far_haze", (0, 760, 90), (1700, 1000, 220), 150.0, 0.003, MIST, HAZE_GLOW, 0.014, base=0.0)


def far_city(rng):
    far = city.facade("far", BODY_FAR, GLASS, WIN_A, WIN_B, WIN_WARM, bay=3.5, floor_h=4.0, lit=0.07, strength=0.9,
                      warm_part=0.15, ground=8.0)
    city.skyline(rng, far, None, 230, 230, 900, 34, (22, 52), tall=0.0)
    T = city.Boxes()
    # the towers seen down the street, over the block that closes it
    for x, y, w, h in ((-14, 300, 30, 78), (22, 330, 26, 96), (58, 310, 30, 70), (2, 430, 34, 128),
                       (44, 470, 30, 112), (88, 450, 36, 140), (-22, 560, 38, 150), (30, 620, 34, 176),
                       (84, 640, 40, 150), (130, 600, 36, 168), (10, 760, 40, 190), (70, 800, 44, 215),
                       (150, 820, 40, 180)):
        T.box((x - w / 2, y - w / 2, 0), (x + w / 2, y + w / 2, h))
        T.box((x - w / 4, y - w / 4, h), (x + w / 4, y + w / 4, h + 10))
    T.done("far_towers", far)


def build():
    sc = tk.reset()
    sc.cycles.seed = SEED
    sc.cycles.volume_bounces = 2
    sc.cycles.volume_step_rate = 1.0
    sc.view_settings.look = "AgX - Punchy"
    rng = random.Random(SEED)
    buildings(rng)
    street()
    sign()
    rain(rng)
    far_city(rng)
    air()
    cam = tk.camera(CAM, (CAM[0], 100.0, CAM[2] + 100.0 * math.tan(PITCH)), LENS)
    cam.data.clip_end = 3000
    return sc


if __name__ == "__main__":
    city.run(build, NAME, samples=SAMPLES)
