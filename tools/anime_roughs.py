"""Scenes B to G and the wordmark as hand-painted animation backgrounds: roughs through the painter in anime.py.

The compositions are the committed ones: cameras, masses and light placement come unchanged from roughs.py and
bg6_wordmark.py. Their mist, haze and cloud are not rendered; each becomes a painted halo, a flat tinted field
or a drawn shape here. Scene A has its own file, anime_a.py.

Original art from geometry, procedural shaders and seeded noise. Every colour is a colors.toml value or a mix.

    uv run tools/anime_roughs.py --scene B                 # .cache/anime/rough-b.png at 1720x720
    uv run tools/anime_roughs.py --scene all --out /tmp/x
"""

import argparse
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import city  # noqa: E402
import paint as pt  # noqa: E402
import anime as an  # noqa: E402
import roughs as rg  # noqa: E402
import bg6_wordmark as w6  # noqa: E402
from anime import Glow, Look, within  # noqa: E402

P = tk.palette()
RED, ORANGE, CYAN, PALE = P["accent"], P["orange"], P["cyan"], P["foreground"]
WARM = tk.mix(ORANGE, P["bright_yellow"], 0.4)
DARK = tk.mix(an.BG, an.SEL, 0.09)  # a thing kept as a dark flat shape

# the scenes' own local colours, lifted from near-black to painted blues; their air is painted, not rendered
rg.BODY, rg.GLASS, rg.ROAD, rg.DECK, rg.STEEL, rg.BIKE = an.BODY, an.GLASS, an.ROAD, an.PAVE, an.STEEL, DARK
an.no_air()
w6.air = lambda: None


def level(z):
    """Flat ground at this height: the roof deck, the road, the water."""
    return lambda pic: pic.solid & (pic.n[..., 2] > 0.7) & (abs(pic.pos[..., 2] - z) < 0.3)


def shapes(pic, rng, rows, cell=(26, 300), cover=0.5):
    """Flat ragged shapes lying in a band of rows, for cloud and haze drawn as cut paper."""
    k = pic.k
    lo, hi = rows
    y = np.arange(pic.shape[0], dtype=np.float32)[:, None]
    band = pt.step(lo, lo + (hi - lo) * 0.3, y) * (1 - pt.step(hi - (hi - lo) * 0.3, hi, y))
    n = pt.noise(pic.shape, (cell[0] * k, cell[1] * k), rng)
    return pt.step(1 - cover, 1 - cover + 0.03, n * (0.55 + 0.45 * band)) * (band > 0.02)


def near_to(pic, place, reach):
    """1 at a place in the picture falling to 0 `reach` pixels (of the 3440 picture) away."""
    row, col = pic.at(place)
    yy, xx = np.ogrid[:pic.shape[0], :pic.shape[1]]
    return np.clip(1 - np.hypot(yy - row, xx - col) / (reach * pic.k), 0, 1).astype(np.float32)


# ---------- B, moored lantern ----------

B_AT = (4.24, 21.4, 62.0)


def b_under(pic, out, rng):
    """Low cloud among the towers as flat shapes, lit toward the lantern."""
    hz = pic.horizon
    glow = near_to(pic, B_AT, 1500)
    for rows, cover, tone in (((hz - 250 * pic.k, hz - 40 * pic.k), 0.42, 0.35),
                              ((hz - 120 * pic.k, hz + 60 * pic.k), 0.5, 0.5)):
        m = shapes(pic, rng, rows, cover=cover) * (pic.dist > 150)
        colour = pt.mixa(np.broadcast_to(pt.rgb(tk.mix(an.SEL, P["muted"], 0.3)), out.shape),
                         pt.rgb(tk.mix(ORANGE, P["muted"], 0.3)), glow ** 1.5)
        out = out + (colour - out) * (m * tone)[..., None]
    return out


def b_over(pic, out, rng):
    """The lantern as a flat disc in three steps: bright core, orange, darker rim."""
    m = pic.masks[0]
    row, col = pic.at(B_AT)
    radius = pic.f * 2.0 / float(np.linalg.norm(np.array(B_AT) - pic.eye))
    yy, xx = np.ogrid[:pic.shape[0], :pic.shape[1]]
    r = np.hypot(yy - row + 0.08 * radius, xx - col).astype(np.float32) / radius
    r = r * (1 + 0.1 * (pt.noise(pic.shape, 60 * pic.k, rng) - 0.5))
    rim, core = pt.rgb(tk.mix(ORANGE, P["brown"], 0.6)), pt.rgb(tk.mix(P["bright_yellow"], PALE, 0.35))
    disc = np.where((r > 0.8)[..., None], rim, np.where((r < 0.48)[..., None], core, pt.rgb(ORANGE)))
    return out + (disc - out) * m[..., None]


LOOK_B = Look(
    name="b", seed=rg.SEEDS["B"], build=rg.scene_b, key_at=(B_AT[0], B_AT[1] - 2.6, B_AT[2]), key_colour=ORANGE,
    rings=(5.0, 9.0, 15.0), amounts=(0.3, 0.14, 0.05),
    glows=(Glow(within((2.1, 19.2, 59.9), (6.4, 23.6, 64.1)), smear=0.3),
           Glow(within((9.0, 25.5, 64.0), (12.0, 26.5, 66.0)), halo=((9, 3.0),), colour=RED)),
    discs=((B_AT, (4.6, 11.0), (0.36, 0.15), ORANGE),),
    tier_at=(85.0, 280.0, 520.0), veil=(), wet=level(58.4), under=b_under, over=b_over, tint=0.65,
    sky=(an.SKY_TOP, tk.mix(an.BG, an.SEL, 0.42), tk.mix(an.SEL, an.BLUE, 0.16)))


# ---------- C, rider's stop ----------

C_Z = 28.0
C_BIKE = ((-3.7, 4.2, C_Z + 0.02), (-1.2, 7.1, C_Z + 1.7))


def c_under(pic, out, rng):
    """A dim pool on the road ahead of the bike's lamp."""
    a = math.radians(26.0)
    at = (-2.4 + 2.6 * math.sin(a), 5.6 + 2.6 * math.cos(a))
    u = (pic.pos[..., 0] - at[0]) * math.sin(a) + (pic.pos[..., 1] - at[1]) * math.cos(a)
    v = (pic.pos[..., 0] - at[0]) * math.cos(a) - (pic.pos[..., 1] - at[1]) * math.sin(a)
    pool = ((u / 1.5) ** 2 + (v / 0.6) ** 2 < 1) & pic.wet
    return pt.mixa(out, pt.rgb(tk.mix(P["muted"], PALE, 0.4)), pool * 0.22)


def c_over(pic, out, rng):
    """The blue light behind the bike drawn as a thin edge down its left side."""
    s = max(1, int(round(3 * pic.k)))
    edge = pic.flat & ~np.roll(pic.flat, s, 1)
    return pt.mixa(out, pt.rgb(tk.mix(P["blue"], P["bright_blue"], 0.5)), pt.blur(edge.astype(np.float32), 0.6) * 0.8)


LOOK_C = Look(
    name="c", seed=rg.SEEDS["C"], build=rg.scene_c, key_at=(-9.0, 1.0, C_Z + 3.5), key_colour=P["blue"],
    rings=(9.0, 15.0, 24.0), amounts=(0.3, 0.17, 0.07),
    glows=(Glow(within((12.9, 239.0, 43.9), (17.1, 240.6, 56.1)), halo=((16, 1.2), (90, 2.4)), colour=RED),
           Glow(within(*C_BIKE), halo=((7, 3.0),), colour=CYAN)),
    discs=(((52.0, 225.0, 30.0), (45.0, 100.0), (0.3, 0.18), ORANGE),),
    tier_at=(230.0, 420.0, 640.0), veil=((90.0, 0.2), (160.0, 0.36)), wet=level(C_Z),
    flats=((*C_BIKE, DARK),), under=c_under, over=c_over)


# ---------- D, signal roof ----------

D_AT = (8.9, 45.0, 69.45)

LOOK_D = Look(
    name="d", seed=rg.SEEDS["D"], build=rg.scene_d, key_at=(D_AT[0], D_AT[1] - 0.6, D_AT[2]), key_colour=RED,
    rings=(13.0, 22.0, 38.0), amounts=(0.42, 0.22, 0.09),
    glows=(Glow(within((8.5, 44.6, 69.0), (9.3, 45.4, 69.9)), "paper", core=2.5, smear=1.6),),
    discs=((D_AT, (2.2, 8.0), (0.6, 0.3), RED),),
    tier_at=(105.0, 300.0, 540.0), veil=(), wet=level(58.4))


# ---------- E, last train ----------

E_Y, E_Z = 90.0, 6.55

LOOK_E = Look(
    name="e", seed=rg.SEEDS["E"], build=rg.scene_e, key_at=(5.0, E_Y - 5.0, E_Z + 2.4), key_colour=ORANGE,
    rings=(14.0, 24.0, 34.0), amounts=(0.3, 0.15, 0.06),
    glows=(Glow(within((-21.0, E_Y - 2.0, E_Z + 1.6), (31.0, E_Y - 1.0, E_Z + 2.9)), halo=((12, 0.9), (70, 1.3)),
                smear=1.6, colour=ORANGE),
           Glow(within((-20.7, E_Y - 2.0, E_Z + 0.8), (-19.8, E_Y - 0.7, E_Z + 1.3)), halo=((7, 3.0),), colour=RED,
                smear=1.0)),
    tier_at=(190.0, 380.0, 600.0), veil=((150.0, 0.3),), wet=level(-1.2), tint=0.3)


# ---------- F, tunnel mouth ----------

F_AT = (-10.4, 46.0, 3.5)


def f_under(pic, out, rng):
    """The inside of the tunnel is the light: its far end is a flat warm field, not a view through the hill."""
    (top, left), (bottom, right) = pic.at((-15.4, 46.0, 7.0)), pic.at((-5.4, 46.0, 0.0))
    yy, xx = np.ogrid[:pic.shape[0], :pic.shape[1]]
    mouth = (yy > top) & (yy < bottom) & (xx > left) & (xx < right) & (pic.dist > 150)
    return np.where(mouth[..., None], pt.rgb(tk.mix(WARM, PALE, 0.25)), out)


LOOK_F = Look(
    name="f", seed=rg.SEEDS["F"], build=rg.scene_f, key_at=(-10.4, 49.0, 5.0), key_colour=ORANGE,
    rings=(13.0, 28.0, 52.0), amounts=(0.62, 0.34, 0.13),
    glows=(Glow(within((-14.0, 50.0, 6.8), (-7.0, 201.0, 7.1)), "tube", halo=((24, 1.0), (110, 2.2)), smear=1.5,
                colour=ORANGE),
           Glow(within((-14.2, 45.0, 7.9), (-6.6, 45.8, 8.5)), "paper", core=1.5, halo=((9, 2.5),), colour=RED)),
    discs=((F_AT, (9.0, 18.0), (0.34, 0.16), ORANGE),),
    tier_at=(250.0, 450.0, 650.0), veil=((80.0, 0.2), (130.0, 0.36)), tint=0.35, under=f_under, rain=0.45,
    rain_colour=tk.mix(PALE, ORANGE, 0.3))


# ---------- G, the counter ----------

G_AT = (2.35, 13.25, 2.3)
KETTLE = (2.9, 13.9, 1.3)


def g_over(pic, out, rng):
    """Steam off the kettle: one small flat shape, lighter toward the lanterns above it."""
    row, col = pic.at(KETTLE)
    top = pic.at((KETTLE[0], KETTLE[1], 2.5))[0]
    body, lit = pt.plume(pic.shape, (row, col), row - top, 26 * pic.k, rng, lean=-0.12, toward=-1)
    out = pt.mixa(out, pt.rgb(tk.mix(P["muted"], ORANGE, 0.3)), pt.blur(body, 0.7 * pic.k) * 0.5)
    return pt.mixa(out, pt.rgb(tk.mix(PALE, ORANGE, 0.4)), pt.blur(body * lit, 0.7 * pic.k) * 0.3)


LOOK_G = Look(
    name="g", seed=rg.SEEDS["G"], build=rg.scene_g, key_at=(2.3, 12.6, 1.9), key_colour=ORANGE,
    rings=(2.6, 4.6, 7.5), amounts=(0.36, 0.17, 0.06),
    glows=(Glow(within((1.2, 13.0, 2.0), (3.5, 13.5, 2.6)), "paper", core=9.0, halo=((30, 0.35),), smear=1.4),
           Glow(within((-4.6, 17.9, 0.3), (-4.3, 19.0, 1.8)), halo=((14, 0.8), (60, 1.2)), smear=1.0)),
    discs=((G_AT, (1.6, 4.0), (0.3, 0.14), ORANGE),),
    tier_at=(500.0, 700.0, 900.0), veil=((28.0, 0.14), (50.0, 0.28)), tint=0.4, over=g_over, rain=0.45,
    rain_colour=tk.mix(PALE, ORANGE, 0.3), stars=False)


# ---------- 06, the Omarchy wordmark over the city ----------

LIT_TO = 0.2                                   # how far up a letter's face the city's light reaches, of its height
CITY_HAZE = tk.mix(tk.mix(ORANGE, P["brown"], 0.45), an.SEL, 0.25)  # the city's light in the air
CITY_BAND = tk.mix(ORANGE, an.SEL, 0.3)                            # a lit band low on a tower's face
HAZE_BANDS = ((1700.0, 0.05), (2600.0, 0.16), (4200.0, 0.3), (6200.0, 0.46))  # beyond this far, this much haze
CARPET = tuple(tk.mix(an.BG, an.SEL, t) for t in (0.4, 0.5, 0.6, 0.7))  # the far city's tone in each of those
GLOW_OVER = ((480.0, 620.0, 0.75), (2350.0, 380.0, 0.25))  # the glow's swells: column of 3440, width, amount
CARPET_HAZE = 0.42                            # the towers take less of the glow than the air behind them
LIT_WARM = tk.mix(tk.mix(CITY_HAZE, ORANGE, 0.2), PALE, 0.55)     # the letters' lit field takes the glow's tint
LIT_TINT = 0.6
BANDS = ((176.0, 185.0), (146.0, 152.0), (107.0, 113.0))  # each one's lit band, the lowest part of it in the frame
# the nearest tall block at the bottom left and its two neighbours, as the city script places them with seed 1
BLOCKS = (((-436.7, 862.1, 0.0), (-381.8, 913.8, 254.7)),
          ((-528.6, 930.4, 0.0), (-477.0, 968.4, 170.9)),
          ((-429.7, 1168.3, 0.0), (-382.8, 1195.1, 126.4)))


def w_under(pic, out, rng):
    """The ground between the towers as stepped blues, the far city as a few flat masses under an uneven glow,
    and the letters flat in two tones: a warm pale field where the city's light reaches up them and a dark
    tone above, with their undersides pale."""
    k = pic.k
    rows = np.arange(pic.shape[0], dtype=np.float32)[:, None]
    away = float(w6.CAM.z) * pic.f / np.maximum(rows - pic.horizon, 1.0)  # how far off the ground in a row is
    ground = np.broadcast_to(pt.rgb(an.TIERS[0]), out.shape).copy()
    for at, colour in zip(pic.look.tier_at[1:], an.TIERS[1:]):
        ground = np.where((away > at)[..., None], pt.rgb(colour), ground)
    out = np.where((~pic.solid & (rows > pic.horizon))[..., None], pt.mixa(ground, pt.rgb(an.SHADE), 0.3), out)
    # past the last towers the ground is lost in the air: it takes the sky's own colour where the two meet
    lost = ~pic.solid & (rows > pic.horizon) & (away > HAZE_BANDS[-1][0])
    out = np.where(lost[..., None], out[max(int(pic.horizon) - 1, 0)][None], out)
    word =pic.solid & (pic.dist < 550)
    # the nearest tall block and its two neighbours: one lit band low on their faces
    for (lo, hi), (z0, z1), amount in zip(BLOCKS, BANDS, (0.5, 0.25, 0.25)):
        band = pic.solid & an.inbox(pic.pos, (lo[0] - 1, lo[1] - 1, z0), (hi[0] + 1, hi[1] + 1, z1)) \
            & (np.abs(pic.n[..., 2]) < 0.5)
        out = pt.mixa(out, pt.rgb(CITY_BAND), band * amount)
    # the city's own light in the air: a warm band lying on the horizon. The far city sinks into it in depth
    # bands, and it fades up into the blue of the sky.
    far = np.where(pic.solid, pic.dist, away)
    edge = 1 + 0.25 * (pt.noise(pic.shape, (30 * k, 500 * k), rng) - 0.5)
    # the far carpet as a few large flat masses, dark near and paler far, with no pale roof tops: beyond the
    # middle distance each depth band is one tone and the blocks in it run together
    carpet = pic.solid & ~word
    for (beyond, _), tone, amount in zip(HAZE_BANDS, CARPET, (0.45, 0.8, 0.92, 1.0)):
        out = np.where((carpet & (far * edge > beyond))[..., None], pt.mixa(out, pt.rgb(tone), amount), out)
    haze = np.zeros(pic.shape, np.float32)
    for beyond, amount in HAZE_BANDS:
        haze = np.where(far * edge > beyond, amount, haze)
    haze = pt.blur(haze * np.where(carpet, CARPET_HAZE, 1.0), 3 * k)
    # the glow is the city's, so it is uneven along the horizon: brightest over the big tower and the dense
    # cluster at the left, thinner elsewhere, and its upper edge is ragged
    cols = np.arange(pic.shape[1], dtype=np.float32)[None, :] / k
    over = sum(amount * np.exp(-((cols - at) / wide) ** 2) for at, wide, amount in GLOW_OVER)
    uneven = pt.noise(pic.shape, (400 * k, 260 * k), rng)[:1] - 0.5
    ragged = pt.noise(pic.shape, (18 * k, 120 * k), rng) - 0.5
    strength = np.clip(0.45 + over + 0.3 * uneven, 0.2, 1.45)
    reach = 95 * k * np.clip(0.5 + 0.8 * over + 0.5 * uneven + 0.7 * ragged, 0.15, None)
    up = HAZE_BANDS[-1][1] * strength * np.exp(-np.maximum(pic.horizon - rows, 0) / reach)
    # below the horizon the swell fades in with distance, so the air and the last of the ground meet unseen
    swell = 1 + (strength - 1) * np.clip((far - HAZE_BANDS[1][0]) / (HAZE_BANDS[-1][0] - HAZE_BANDS[1][0]), 0, 1)
    haze = np.where(rows < pic.horizon, up, haze * swell)
    haze = np.clip(haze + 0.16 * strength * np.exp(-np.abs(rows - pic.horizon) / (70 * k)), 0, 1) * ~word
    out = pt.mixa(out, pt.rgb(CITY_HAZE), haze)
    z = pic.pos[..., 2]
    lo, hi = z[word].min(), z[word].max()
    # one level shadow line at the same height on every letter: the city's light from below reaches a little
    # way up the face
    lit = (z - lo) / (hi - lo) < LIT_TO
    cool = pt.rgb(tk.mix(tk.mix(tk.mix(w6.UPLIGHT, w6.LETTER, 0.3), an.SEL, 0.3), LIT_WARM, LIT_TINT))
    dark = pt.rgb(tk.mix(tk.mix(w6.LETTER, an.SEL, 0.5), an.BG, 0.45))
    tone = np.where(lit[..., None], cool, dark)
    # sides are one darker tone on every letter: the middle letters show no side, so none of them is red
    tone = np.where((np.abs(pic.n[..., 0]) > 0.5)[..., None], pt.rgb(tk.mix(tk.mix(w6.LETTER, an.SEL, 0.5), an.BG, 0.7)),
                    tone)
    tone = np.where((pic.n[..., 2] < -0.5)[..., None], pt.rgb(tk.mix(w6.UPLIGHT, PALE, 0.5)), tone)
    return np.where(word[..., None], tone, out)


def red_lamps(pic):
    return (pic.emit[..., 0] > 0.8) & (pic.emit[..., 1] < 0.45)


def w_build(rng):
    """The scene as committed, with the towers left plain: their windows are drawn by the painter."""
    import city
    material = w6.city_material
    w6.city_material = lambda: city.plain("city", w6.CITY_BODY)
    try:
        w6.build()
    finally:
        w6.city_material = material
    # the nearest tall block gets a stepped top, a roof tank and a mast; its neighbours a smaller step each
    T = city.Boxes()
    (x0, y0, _), (x1, y1, h) = BLOCKS[0]
    T.box((x0 + 9, y0 + 8, h), (x1 - 14, y1 - 8, h + 16))
    T.box((x0 + 14, y0 + 12, h + 16), (x1 - 26, y1 - 14, h + 24))
    T.box((x1 - 11, y0 + 5, h), (x1 - 3, y0 + 13, h + 7))        # the tank
    T.box((x0 + 17, y0 + 16, h + 24), (x0 + 18.4, y0 + 17.4, h + 60))  # the mast
    for (x0, y0, _), (x1, y1, h) in BLOCKS[1:]:
        T.box((x0 + 6, y0 + 6, h), (x1 - 10, y1 - 6, h + 8))
        T.box((x1 - 8, y0 + 4, h), (x1 - 3, y0 + 9, h + 4))
    T.done("city_tops", city.plain("city_tops", w6.CITY_BODY))


def w_dress(pic, rng):
    """Windows on the towers as loose clusters of marks: few, large and warm on the nearest blocks, small on
    the middle distance, none on the far carpet."""
    upright = an.walls(pic)[0] & pic.far
    front = upright & (pic.dist < 1150)
    near = upright & ~front & (pic.dist < 1700)
    rest = upright & ~front & ~near & (pic.dist < HAZE_BANDS[1][0])
    an.marks(pic, rng, front, bay=11.0, floor_h=8.0, ground=6.0, part=0.5, warm=0.55, cool=w6.CITY_WIN,
             lit=w6.CITY_WARM)
    an.marks(pic, rng, near, bay=7.0, floor_h=5.0, ground=4.0, part=0.6, warm=0.4, cool=w6.CITY_WIN, lit=w6.CITY_WARM)
    an.marks(pic, rng, rest, bay=10.0, floor_h=5.5, ground=4.0, part=0.75, warm=0.28, cool=w6.CITY_WIN,
             lit=w6.CITY_WARM)


LOOK_06 = Look(
    name="06", seed=1, build=w_build, key_at=(0.0, 380.0, 250.0), key_colour=w6.UPLIGHT,
    amounts=(0.0, 0.0, 0.0), glows=(Glow(red_lamps, halo=((7, 2.5),), colour=RED),),
    tier_at=(560.0, 2600.0, 5200.0), veil=(), under=w_under, far_dim=0.15, dress=w_dress,
    air=((60.0, 0.1), (30.0, 0.2), (12.0, 0.3)),
    sky=(an.SKY_TOP, tk.mix(an.BG, an.SEL, 0.34), tk.mix(an.SEL, an.BLUE, 0.08)), window_lines=0.0, offset=20000.0)


LOOKS = {"B": LOOK_B, "C": LOOK_C, "D": LOOK_D, "E": LOOK_E, "F": LOOK_F, "G": LOOK_G, "06": LOOK_06}


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", default="all", choices=[*LOOKS, "all"])
    ap.add_argument("--out", default=os.path.join(tk.REPO, ".cache", "anime"))
    ap.add_argument("--percent", type=int, default=50)
    arg = ap.parse_args(argv)
    for key in (LOOKS if arg.scene == "all" else [arg.scene]):
        an.run(LOOKS[key], arg.out, arg.percent, name=f"rough-{key.lower()}")
