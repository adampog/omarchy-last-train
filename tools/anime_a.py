"""Scene A, Rain gate, as a hand-painted animation background: technique tests.

The street, sign, camera and far city are the ones in bg_a_rain_gate.py. What changes is how the picture is made:

    t1  cel in the renderer: Toon shading, Freestyle lines, flat emission, then value steps and 2D paint on top
    t2  the renderer writes only data (flat colour, lights, position, normal, a hard shadow mask) and the
        picture is painted from it in numpy: flat tones, pen lines, a painted sky, drawn halos, smears and rain
    t3  t2 taken further toward gouache: stepped halos, brush filter, uneven pigment in the flat fields

Original art from geometry, procedural shaders and seeded noise. Every colour is a colors.toml value or a mix.

    uv run tools/anime_a.py --treatment t2                 # .cache/anime/a-t2.png at 3440x1440
    uv run tools/anime_a.py --treatment t1 --percent 50
"""

import argparse
import math
import os
import random
import sys
import time

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import city  # noqa: E402
import paint as pt  # noqa: E402
import bg_a_rain_gate as a  # noqa: E402
from scenes import srgb, node, link  # noqa: E402

P = tk.palette()
SEED = a.SEED
SAMPLES = 16  # the data renders are flat emission; this only smooths their edges

# ---------- the painter's colours: night is blue, not black ----------

BG, SEL, BLUE = P["background"], P["selection"], P["blue"]
DEEP = tk.mix(BG, SEL, 0.3)              # the deepest large field
SHADE = tk.mix(BG, SEL, 0.14)            # what a surface in shadow is pulled toward
SKY_TOP, SKY_MID, SKY_LOW = tk.mix(BG, SEL, 0.1), tk.mix(BG, SEL, 0.55), tk.mix(SEL, BLUE, 0.4)
TIERS = (tk.mix(BG, SEL, 0.5), tk.mix(BG, SEL, 0.72), tk.mix(SEL, BLUE, 0.14))  # the far city, near to far
TIER_AT = (200.0, 400.0, 600.0)
HAZE = tk.mix(SEL, BLUE, 0.1)
LINE = tk.mix(BG, SEL, 0.06)
RED, RED_HOT = P["accent"], tk.mix(P["bright_red"], P["foreground"], 0.7)
RAIN = tk.mix(P["foreground"], P["bright_red"], 0.35)
STEAM, STEAM_EDGE = tk.mix(SEL, P["muted"], 0.55), tk.mix(P["muted"], P["bright_red"], 0.45)
SKYLIGHT = P["blue"]

# the scene's own local colours, lifted from near-black to painted blues
a.BODY = tk.mix(BG, SEL, 0.32)
a.GLASS = tk.mix(BG, SEL, 0.16)
a.ROAD = tk.mix(BG, SEL, 0.28)
a.PAVE = tk.mix(tk.mix(BG, SEL, 0.34), P["muted"], 0.14)
a.STEEL = tk.mix(tk.mix(BG, SEL, 0.3), P["muted"], 0.22)

FWD = Vector((0.0, 1.0, math.tan(a.PITCH))).normalized()
LAMP_AT = ((a.SIGN_X[0] + a.SIGN_X[1] - 0.05) / 2, a.SIGN_Y - 0.9, 5.2)
OFFSET = 1000.0  # added to positions so the data render holds no negative numbers


# ---------- the scene and its data renders ----------

def scene():
    sc = tk.reset()
    sc.cycles.seed = SEED
    rng = random.Random(SEED)
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
    return sc, cam


def sign_lamp(sc):
    lamps = [ob for ob in sc.objects if ob.type == "LIGHT"]
    key = min(lamps, key=lambda ob: (ob.location - Vector(LAMP_AT)).length)
    for ob in lamps:
        if ob is not key:
            bpy.data.objects.remove(ob)
    key.data.shadow_soft_size = 0.0  # a drawn shadow has a hard edge
    return key


def base_source(nt):
    p = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if p is None:
        return None, None
    sock = p.inputs["Base Color"]
    return p, (sock.links[0].from_socket if sock.is_linked else tuple(sock.default_value))


def remake(mode):
    """Rewrite every material: 'col' shows only its flat local colour, 'emit' only what glows, 'toon' cel shades."""
    for mat in bpy.data.materials:
        nt = mat.node_tree
        if nt is None:
            continue
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        if "grime" in nt.nodes:
            nt.nodes.remove(nt.nodes["grime"])
        p, src = base_source(nt)
        glow = [n for n in nt.nodes if n.type == "EMISSION"]

        def flat(strength):
            em = node(nt, "ShaderNodeEmission", Strength=strength)
            if src is None:
                em.inputs["Strength"].default_value = 0.0
            elif isinstance(src, tuple):
                em.inputs["Color"].default_value = src
            else:
                link(nt, src, em.inputs["Color"])
            return em

        if mode == "col":
            link(nt, flat(1.0).outputs[0], out.inputs["Surface"])
        elif mode == "emit":
            if p is None:
                glow[0].inputs["Strength"].default_value = 1.0
            elif glow:
                link(nt, glow[0].outputs[0], out.inputs["Surface"])
            else:
                link(nt, node(nt, "ShaderNodeEmission", Strength=0.0).outputs[0], out.inputs["Surface"])
        elif mode == "toon" and p is not None:
            toon = node(nt, "ShaderNodeBsdfToon", Size=0.9, Smooth=0.0)
            toon.component = "DIFFUSE"
            toon.inputs["Color"].default_value = (0.8, 0.8, 0.8, 1.0)
            add = node(nt, "ShaderNodeAddShader")
            link(nt, toon.outputs[0], add.inputs[0])
            link(nt, flat(1.0).outputs[0], add.inputs[1])
            for ln in list(p.outputs[0].links):
                link(nt, add.outputs[0], ln.to_socket)


def override(kind):
    mat = bpy.data.materials.new(kind)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial")
    geo = node(nt, "ShaderNodeNewGeometry")
    if kind == "pos":
        v = city.vec_node(nt, "ADD", geo.outputs["Position"], (OFFSET, OFFSET, OFFSET))
    elif kind == "nrm":
        v = city.vec_node(nt, "MULTIPLY_ADD", geo.outputs["Normal"], (0.5, 0.5, 0.5))
        v.inputs[2].default_value = (0.5, 0.5, 0.5)
    if kind == "lit":
        sh = node(nt, "ShaderNodeBsdfDiffuse")
        sh.inputs["Color"].default_value = (1, 1, 1, 1)
    else:
        sh = node(nt, "ShaderNodeEmission")
        link(nt, v.outputs[0], sh.inputs["Color"])
    link(nt, sh.outputs[0], out.inputs["Surface"])
    return mat


def data_render(sc, path, samples, sharp=False):
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "32"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = False
    sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 0
    sc.cycles.filter_width = 0.01 if sharp else 1.5
    tk.render(sc, path)
    return pt.load(path)


def marks(sc, cam, shape):
    """Where a few things of the scene fall in the picture, as (row, column)."""
    h, w = shape

    def at(p):
        v = world_to_camera_view(sc, cam, Vector(p))
        return ((1 - v.y) * h, v.x * w)
    return {"grate": at((3.4, 28.0, 0.0)), "steam_top": at((3.4, 28.0, 7.5)), "sign": at(a.SIGN_MID),
            "door": at((2.4, 87.9, 1.9)), "horizon": at((a.CAM[0], 5000.0, a.CAM[2]))}


def passes(folder, percent, want=("col", "emit", "pos", "nrm", "lit")):
    """Render the data the painter works from. Each is a few seconds: nothing in them is lit but 'lit'."""
    d = {}
    for kind in want:
        sc, cam = scene()
        sc.render.resolution_percentage = percent
        if kind in ("col", "emit"):
            remake(kind)
        else:
            if kind == "lit":
                sign_lamp(sc)
                tk.set_world((0, 0, 0, 1), 0.0)
            bpy.context.view_layer.material_override = override(kind)
        d[kind] = data_render(sc, os.path.join(folder, f"a-{kind}.exr"), 1 if kind in ("pos", "nrm") else SAMPLES,
                              sharp=kind in ("pos", "nrm"))
        if "marks" not in d:
            bpy.context.view_layer.update()
            d["marks"] = marks(sc, cam, d[kind].shape[:2])
    return d


# ---------- the painter ----------

class Picture:
    """What the data renders say about each pixel, in the terms the painter needs."""

    def __init__(self, d):
        self.marks = d["marks"]
        self.solid = d["pos"][..., 3] > 0.5
        self.shape = self.solid.shape
        self.k = self.shape[1] / tk.RES[0]  # sizes below are in pixels of the 3440-wide picture
        pos = d["pos"][..., :3] - OFFSET
        rel = pos - np.array(a.CAM, np.float32)
        self.pos = pos
        self.depth = np.where(self.solid, rel @ np.array(FWD, np.float32), 1e5).astype(np.float32)
        self.dist = np.where(self.solid, np.linalg.norm(rel, axis=-1), 1e5).astype(np.float32)
        self.n = d["nrm"][..., :3] * 2 - 1
        self.ground = self.solid & (self.n[..., 2] > 0.7) & (pos[..., 2] < 0.3)
        self.far = self.solid & (self.dist >= TIER_AT[0])
        self.col = pt.oetf(d["col"][..., :3])
        self.emit = pt.oetf(d["emit"][..., :3])
        self.glow = pt.step(0.02, 0.1, d["emit"][..., :3].max(-1)) * d["emit"][..., 3]
        on_sign = (np.abs(pos[..., 1] - a.SIGN_Y) < 0.6) & (pos[..., 0] < a.SIGN_X[1] + 0.4) & (pos[..., 0] > -5.6)
        self.sign = self.glow * on_sign
        red = on_sign & (((pos[..., 2] > 3.8) & (pos[..., 2] < 7.0)) | (pos[..., 0] > a.SIGN_X[1]))
        self.red = self.glow * red
        self.door = self.glow * ((np.abs(pos[..., 1] - 87.9) < 0.6) & (pos[..., 2] < 3.2) & (pos[..., 0] > 1.0)
                                 & (pos[..., 0] < 3.6))
        to = np.array(LAMP_AT, np.float32) - pos
        self.r = np.linalg.norm(to, axis=-1)
        self.ndl = (self.n * to).sum(-1) / np.maximum(self.r, 1e-3)
        self.lit = (d["lit"][..., 0] > 1e-5) & (self.ndl > 0.06) & self.solid if "lit" in d else None


def sky(pic, rng, stars=True):
    """A painter's gradient, darkest at the top, lifting toward where the street turns; a few stars as dots."""
    h, w = pic.shape
    hz = pic.marks["horizon"][0] / h
    yy, xx = np.linspace(0, 1, h, dtype=np.float32)[:, None], np.linspace(0, 1, w, dtype=np.float32)[None, :]
    t = np.clip(yy / hz + 0.16 * (xx - 0.5), 0, 1)
    t = t * t * (3 - 2 * t)
    top, mid, low = pt.rgb(SKY_TOP), pt.rgb(SKY_MID), pt.rgb(SKY_LOW)
    lo = np.clip(t * 2, 0, 1)[..., None]
    hi = np.clip(t * 2 - 1, 0, 1)[..., None]
    out = top + (mid - top) * lo + (low - mid) * hi
    if stars:
        n = int(260 * pic.k * pic.k)
        y, x = rng.integers(int(160 * pic.k), int(hz * h), n), rng.integers(0, w, n)
        dots = np.zeros(pic.shape, np.float32)
        dots[y, x] = rng.uniform(0.25, 0.9, n) ** 2
        dots = np.clip(pt.blur(dots, 0.9 * pic.k) * 7, 0, 1)
        out = pt.mixa(out, pt.rgb(P["bright_blue"]), dots * 0.8)
    return out


def far_city(pic, out):
    """The far city as stepped flat silhouettes: distance is a colour step, not fog. Its lit windows stay as marks."""
    lamb = pic.n @ np.array((-0.5, -0.6, 0.62), np.float32)
    for k, colour in enumerate(TIERS):
        hi = TIER_AT[k + 1] if k + 1 < len(TIERS) else 1e4
        m = pic.solid & (pic.dist >= TIER_AT[k]) & (pic.dist < hi)
        tone = pt.mixa(np.broadcast_to(pt.rgb(colour), out.shape), pt.rgb(SKYLIGHT), np.where(lamb > 0.4, 0.1, 0.0))
        out = np.where(m[..., None], tone, out)
    return out


def surfaces(pic, rng, rings=(6.0, 12.5, 23.0), reds=(0.4, 0.2, 0.08)):
    """Every near surface as flat tones: its local colour, a shadow tone, a sky-lit tone, and where the sign's light
    falls on it a red field in stepped rings with a hard cast shadow."""
    k = pic.k
    lamb = pic.n @ np.array((-0.45, -0.55, 0.7), np.float32)
    col = pic.col
    tone = np.where((lamb > 0.5)[..., None], pt.mixa(col, pt.rgb(SKYLIGHT), 0.1),
                    np.where((lamb > -0.05)[..., None], col, pt.mixa(col, pt.rgb(SHADE), 0.55)))
    # haze laid over the middle distance as flat fields by depth band
    veil = np.where(pic.dist > 130, 0.42, np.where(pic.dist > 80, 0.24, 0.0)).astype(np.float32)
    tone = pt.mixa(tone, pt.rgb(HAZE), veil)
    wobble = 1 + 0.16 * (pt.noise(pic.shape, 150 * k, rng) - 0.5)  # the rings are cut by hand, not by compass
    r = pic.r * wobble
    f = np.zeros(pic.shape, np.float32)
    for edge, amount in zip(reversed(rings), reversed(reds)):
        f = np.where(pic.lit & (r < edge), amount, f)
    f = pt.blur(f, 1.2 * k)
    return pt.mixa(tone, pt.rgb(RED), f)


def lights(pic, out, far_dim=0.45):
    """Windows and lamps as flat shapes of their own colour; far ones sit back in the haze."""
    dim = np.where(pic.far, far_dim, 0.0).astype(np.float32)
    colour = pt.mixa(pic.emit, pt.rgb(TIERS[1]), dim)
    return pt.mixa(out, colour, pic.glow)


def neon(pic, out, stepped=False):
    """A tube is a near-white core line, a wider line of its colour and a halo round it."""
    k = pic.k
    m = pic.sign
    wide = pt.blur(m, 2.2 * k)
    colour = pt.blur(pic.emit * m[..., None], 2.2 * k) / np.maximum(wide, 1e-4)[..., None]
    out = pt.mixa(out, colour, pt.step(0.1, 0.3, wide))
    core = pt.step(0.42, 0.7, pt.blur(m, 1.0 * k))
    out = pt.mixa(out, pt.mixa(colour, pt.rgb(P["foreground"]), 0.75), core)
    halo = halo_field(pic)
    if stepped:  # three concentric flat tones
        v = halo.max(-1)
        q = np.where(v > 0.5, 0.4, np.where(v > 0.24, 0.22, np.where(v > 0.09, 0.09, 0.0))).astype(np.float32)
        q = pt.blur(q, 2.0 * k)
        return pt.mixa(out, pt.rgb(RED), q * (1 - core))
    return pt.screen(out, halo)


def halo_field(pic):
    k = pic.k
    red = pic.red[..., None] * pt.rgb(RED)
    rest = (pic.sign - pic.red)[..., None] * pic.emit * 0.3
    door = pic.door[..., None] * pic.emit
    return (pt.blur(red + rest, 26 * k) * 1.6 + pt.blur(red, 130 * k) * 8.0 + pt.blur(red, 420 * k) * 20.0
            + pt.blur(door, 20 * k) * 2.0 + pt.blur(door, 80 * k) * 6.0)


def smears(pic, out, rng, src=None):
    """Wet ground: each light pulled straight down into a soft smear of its colour, broken by dark bands where
    the puddles end. No mirror image of anything."""
    k = pic.k
    h, w = pic.shape
    hz = pic.marks["horizon"][0]
    lightmap = pic.emit * (pic.glow * (1.0 + 1.4 * pic.red + 1.2 * pic.door))[..., None] if src is None else src
    lightmap = lightmap + np.clip(halo_field(pic), 0, 1) * 0.35
    rows = np.arange(h)
    from_row = np.round(hz - (rows - hz) * 1.7).astype(int)  # squeezed, so tall lights reach the near road
    ok = (from_row >= 0) & (rows > hz)
    r = np.where(ok[:, None, None], lightmap[np.clip(from_row, 0, h - 1)], 0.0).astype(np.float32)
    r = pt.blur(pt.blur(r, 60 * k, axes=(0,)), 2.5 * k, axes=(1,))
    bands = 0.3 + 0.7 * pt.step(0.38, 0.56, pt.noise(pic.shape, (7 * k, 300 * k), rng))
    local = pt.luma(pic.col)
    puddle = local < pt.blur(local, 40 * k) * 0.93  # the darker patches of the road are standing water
    wet = bands * np.where(puddle, 1.0, 0.6)
    near = pic.ground & (pic.dist < TIER_AT[0])
    return pt.screen(out, r * (wet * near * 2.2)[..., None])


def lines(pic, out, rng, width=1.0, windows=0.45):
    """Pen lines on silhouettes and creases, heaviest on the nearest things, gone on the far city."""
    k = pic.k
    e = pt.edges(1.0 / np.maximum(pic.depth, 0.1), pic.n, pic.solid)
    near = np.minimum(pic.dist, np.minimum(np.roll(pic.dist, 1, 0), np.roll(pic.dist, 1, 1)))
    weight = np.clip((TIER_AT[0] + 20 - near) / 170.0, 0, 1) ** 0.7
    line = pt.ink(e, weight, k, rng, width)
    if windows:  # window frames and painted joints: lighter lines where the local colour changes, near only
        g = pt.luma(pic.col)
        ce = (np.abs(g - np.roll(g, 1, 0)) > 0.012) | (np.abs(g - np.roll(g, 1, 1)) > 0.012)
        ce &= pic.solid & ~pic.ground
        line = np.maximum(line, pt.ink(ce, np.clip((70 - near) / 50.0, 0, 1), k, rng, width * 0.7) * windows)
    line *= 1 - np.clip(pic.sign * 2, 0, 1)
    return pt.mixa(out, pt.rgb(LINE), line * 0.9)


def weather(pic, out, rng, steam_edge=True):
    """Steam as a flat soft shape with a lighter edge toward the sign, then rain as pale streaks of two lengths."""
    k = pic.k
    g, top = pic.marks["grate"], pic.marks["steam_top"]
    puff = pt.puffs(pic.shape, g, (g[0] - top[0]) * 0.8, 120 * k, 11, rng)
    body = pt.step(0.0, 0.22, pt.blur(puff, 5 * k)) * (pic.dist > 27.5)
    body *= 0.25 + 0.4 * pt.step(0.0, 0.5, puff)
    out = pt.mixa(out, pt.rgb(STEAM), body)
    if steam_edge:  # the sign is to the left: that edge is lighter
        shifted = np.roll(body, int(14 * k), 1)
        out = pt.mixa(out, pt.rgb(STEAM_EDGE), np.clip(body - shifted, 0, 1) * 1.6)
    halo = np.clip(halo_field(pic).max(-1), 0, 1)
    density = 0.04 + 0.96 * np.clip(halo * 2.5, 0, 1)
    n = int(9000 * k * k)
    rain = (pt.streaks(pic.shape, density, n, 30 * k, 0.16, rng)
            + pt.streaks(pic.shape, density, n // 2, 64 * k, 0.16, rng))
    rain = pt.blur(np.clip(rain, 0, 1), 0.5 * k) * (0.2 + 0.6 * halo)
    return pt.mixa(out, pt.rgb(RAIN), np.clip(rain * 1.2, 0, 0.5))


def finish(pic, out, rng, amount=0.014):
    """Darken the top under the bar, then one even grain."""
    h = pic.shape[0]
    y = np.arange(h, dtype=np.float32)[:, None] / pic.k
    out = out * (0.3 + 0.7 * pt.step(30, 480, y))[..., None]
    return pt.grain(out, amount, rng)


def paint_t2(d, gouache=False):
    rng = np.random.default_rng(SEED)
    pic = Picture(d)
    out = sky(pic, rng)
    out = np.where(pic.solid[..., None], surfaces(pic, rng), out)
    out = far_city(pic, out)
    out = lights(pic, out)
    if gouache:  # uneven pigment in the fields, then the brush, before anything drawn goes on
        wash = pt.noise(pic.shape, (90 * pic.k, 220 * pic.k), rng) - 0.5
        out = out * (1 + 0.16 * wash)[..., None]
        out = pt.kuwahara(out, int(round(6 * pic.k)))
    out = smears(pic, out, rng)
    out = lines(pic, out, rng, width=1.25 if gouache else 1.0, windows=0.3 if gouache else 0.45)
    out = neon(pic, out, stepped=gouache)
    out = weather(pic, out, rng)
    return finish(pic, out, rng, amount=0.02 if gouache else 0.014), pic


# ---------- t1: cel in the renderer ----------

LEVELS = (0.0, 0.07, 0.13, 0.2, 0.3, 0.44, 0.62, 0.82, 1.0)  # the value steps the render is cut into


def render_t1(folder, percent):
    sc, cam = scene()
    sc.render.resolution_percentage = percent
    remake("toon")
    lamp = sign_lamp(sc)
    lamp.data.color = srgb(tk.mix(P["bright_red"], P["foreground"], 0.2))[:3]
    lamp.data.energy = 1300
    sun = tk.light("SUN", (0, 0, 50), 0.12, srgb(P["bright_blue"]), rotation=(math.radians(50), 0, math.radians(-35)),
                   angle=0.0)
    sun.data.use_shadow = False
    tk.set_world((0, 0, 0, 1), 0.0)
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = "ABSOLUTE"
    fs = bpy.context.view_layer.freestyle_settings
    fs.crease_angle = math.radians(140)
    ls = fs.linesets.new("pen")
    ls.select_silhouette, ls.select_border, ls.select_crease = True, True, True
    style = ls.linestyle
    style.color = srgb(LINE)[:3]
    style.thickness = 2.6 * percent / 100
    far = style.thickness_modifiers.new("far", "DISTANCE_FROM_CAMERA")
    far.range_min, far.range_max, far.value_min, far.value_max = 20.0, 230.0, 1.0, 0.0
    fade = style.alpha_modifiers.new("far", "DISTANCE_FROM_CAMERA")
    fade.range_min, fade.range_max = 60.0, 230.0
    fade.invert = True
    wob = style.thickness_modifiers.new("hand", "NOISE")
    wob.amplitude, wob.period = 0.9 * percent / 100, 30.0
    return data_render(sc, os.path.join(folder, "a-t1-beauty.exr"), 128)


def paint_t1(d):
    rng = np.random.default_rng(SEED)
    pic = Picture(d)
    lin = d["beauty"][..., :3]
    alpha = d["beauty"][..., 3:4]
    v = pt.oetf(lin.max(-1))
    q = np.array(LEVELS, np.float32)[np.clip(np.searchsorted(LEVELS, v), 0, len(LEVELS) - 1)]
    cel = pt.oetf(lin) * (q / np.maximum(v, 1e-4))[..., None]
    out = sky(pic, rng) * (1 - alpha) + cel * alpha
    out = smears(pic, out, rng)
    out = neon(pic, out, stepped=True)
    out = weather(pic, out, rng, steam_edge=False)
    return finish(pic, out, rng), pic


# ---------- running ----------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--treatment", choices=("t1", "t2", "t3"), default="t2")
    ap.add_argument("--out", default=os.path.join(tk.REPO, ".cache", "anime"))
    ap.add_argument("--percent", type=int, default=100)
    arg = ap.parse_args(argv)
    data = os.path.join(arg.out, "data")
    os.makedirs(data, exist_ok=True)
    t0 = time.time()
    if arg.treatment == "t1":
        d = passes(data, arg.percent, want=("emit", "pos", "nrm", "col"))
        d["beauty"] = render_t1(data, arg.percent)
    else:
        d = passes(data, arg.percent)
    t1 = time.time()
    out, pic = paint_t1(d) if arg.treatment == "t1" else paint_t2(d, gouache=arg.treatment == "t3")
    pt.save(os.path.join(arg.out, f"a-{arg.treatment}.png"), out)
    grey = pt.luma(np.clip(out, 0, 1)) * 255
    print(f"{arg.treatment}: render {t1 - t0:.1f} s, paint {time.time() - t1:.1f} s, mean {grey.mean():.1f}, "
          f"top strip {grey[:int(150 * pic.k)].mean():.1f}", flush=True)


if __name__ == "__main__":
    main()
