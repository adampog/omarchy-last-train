"""Background 6, the floating word: the Omarchy wordmark as solid letters floating high over a night megacity,
lit only by the city below.

    ../dont-panic/.venv/bin/python tools/bg6_wordmark.py [--out DIR] [--percent P] [--samples S]

The wordmark is read from /usr/share/omarchy/logo.svg at render time and is not altered: one 2D curve of its
loops, extruded, so its counters stay open. It is the only file the scene reads besides this theme's colors.toml.
The city is boxes with windows in rows. The light on the word is the city's: a blue-white uplight from the
rooftops and a red rim from the lamps, both standing in for the city's glow. Fixed seed. Every colour is the
theme palette's, or a mix of two of its colours. Every render holds ~/Projects/omarchy-themes/.gpu.lock.
"""

import argparse
import fcntl
import math
import os
import random
import re
import sys
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "..", "_toolkit"))

import bpy  # noqa: E402
from mathutils import Euler, Vector  # noqa: E402

import scenes as tk  # noqa: E402  (_toolkit/scenes.py)
from scenes import srgb, node, link  # noqa: E402

NAME = "06-neo-tokyo-omarchy-skyline"
LOGO = "/usr/share/omarchy/logo.svg"
GPU_LOCK = os.path.expanduser("~/Projects/omarchy-themes/.gpu.lock")

# palette: colors.toml, and mixes of its colours
with open(os.path.join(REPO, "colors.toml"), "rb") as _fh:
    P = tomllib.load(_fh)


def mix(a, b, t):
    """The colour t of the way from a to b, as hex."""
    ca, cb = (tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in (a, b))
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


SKY = P["background"]                                    # the top strip
LETTER = mix(P["muted"], P["dark_foreground"], 0.5)      # the word's paint, a pale grey that takes the city's colours
UPLIGHT = mix(P["bright_blue"], P["bright_cyan"], 0.5)   # the city's light from below, blue-white
LAMP = P["accent"]                                       # the city's red lamps
CITY_BODY = mix(P["background"], P["selection"], 0.08)   # towers
CITY_WIN = mix(P["bright_blue"], P["muted"], 0.3)        # lit windows
CITY_WIN2 = mix(P["blue"], P["background"], 0.45)        # dimmer windows
CITY_DEEP = P["selection"]                               # the deepest blue, in the haze band
CITY_WARM = mix(P["orange"], P["foreground"], 0.5)       # a few warm windows
HAZE = mix(P["foreground"], P["bright_blue"], 0.15)      # near white, so the colours come from the light

# the view: from high up, over the city, looking a little up at the word
CAM = Vector((0.0, 0.0, 300.0))
PITCH = math.radians(6.0)
LENS = 28
RES = (3440, 1440)
# the word: where its centre sits in the frame (px), how wide it is (px), its distance (m, along the ground)
WORD_PX, WORD_W_PX, WORD_D = (1900, 650), 2200, 400.0
DEPTH, BEVEL = 6.0, 0.5   # letter thickness and edge bevel, m
UP_W, RIM_W = 9.0e5, 2.5e6  # uplight and red rim, watts
HAZE_D, GLOW = 0.0004, 0.00012  # haze at the ground (per m), the city's light in it


# ---------- the wordmark ----------

def logo_loops(path=LOGO):
    """The SVG's subpaths as lists of (x, y) corners in the file's own units (y down), one list of loops per
    <path>. The file uses M/L/H/V/Z only; its .002 slivers are rounded away (its grid is 15 units)."""
    svg = open(path).read()
    shapes = []
    for d in re.findall(r'\sd="([^"]+)"', svg):
        toks = re.findall(r"[MmLlHhVvZz]|-?(?:\d+\.?\d*|\.\d+)", d)
        loops, cur, x, y, cmd, i = [], [], 0.0, 0.0, None, 0
        while i < len(toks):
            t = toks[i]
            if t.isalpha():
                cmd = t
                i += 1
                if cmd in "Zz":
                    loops.append(cur)
                    cur = []
                    x, y = (loops[-1][0] if loops[-1] else (x, y))
                continue
            if cmd in "Mm":
                dx, dy = float(toks[i]), float(toks[i + 1])
                i += 2
                x, y = (x + dx, y + dy) if cmd == "m" else (dx, dy)
                if cur:
                    loops.append(cur)
                cur = [(x, y)]
                cmd = "l" if cmd == "m" else "L"
                continue
            if cmd in "Ll":
                dx, dy = float(toks[i]), float(toks[i + 1])
                i += 2
                x, y = (x + dx, y + dy) if cmd == "l" else (dx, dy)
            elif cmd in "Hh":
                v = float(toks[i])
                i += 1
                x = x + v if cmd == "h" else v
            elif cmd in "Vv":
                v = float(toks[i])
                i += 1
                y = y + v if cmd == "v" else v
            cur.append((x, y))
        if cur:
            loops.append(cur)
        shapes.append([clean(lp) for lp in loops if len(lp) > 2])
    return shapes


def clean(loop):
    pts = []
    for x, y in loop:
        p = (round(x), round(y))
        if not pts or pts[-1] != p:
            pts.append(p)
    if pts[0] == pts[-1]:
        pts.pop()
    out = []
    n = len(pts)
    for k in range(n):  # drop corners that lie on a straight run
        a, b, c = pts[k - 1], pts[k], pts[(k + 1) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
            out.append(b)
    return out


def pixel_ray(px, py):
    """The world direction through a pixel of the final frame."""
    t = 18.0 / LENS  # half the sensor over the lens
    sx = (px - RES[0] / 2) / (RES[0] / 2) * t
    sy = (RES[1] / 2 - py) / (RES[0] / 2) * t
    d = Vector((sx, sy, -1.0))
    d.rotate(Euler((math.pi / 2 + PITCH, 0, 0)))
    return d.normalized()


def word():
    """The letters, solid, upright, square to the view, centred on WORD_PX at WORD_D."""
    shapes = logo_loops()
    ray = pixel_ray(*WORD_PX)
    centre = CAM + ray * (WORD_D / ray.y)
    t = 18.0 / LENS
    width = WORD_W_PX / (RES[0] / 2) * t * (centre - CAM).length
    s = width / 1215.0
    cu = bpy.data.curves.new("word", "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    cu.extrude = DEPTH / 2
    cu.bevel_depth = BEVEL
    cu.bevel_resolution = 2
    for loops in shapes:
        for lp in loops:
            sp = cu.splines.new("POLY")
            sp.points.add(len(lp) - 1)
            for k, (x, y) in enumerate(lp):
                sp.points[k].co = ((x - 607.5) * s, (142.5 - y) * s, 0, 1)
            sp.use_cyclic_u = True
    mat = bpy.data.materials.new("letter")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb(LETTER)
    bsdf.inputs["Roughness"].default_value = 0.4
    ob = tk.add_object("word", cu, mat, centre)
    yaw = math.atan2(-(centre.x - CAM.x), centre.y - CAM.y)
    ob.rotation_euler = (math.radians(90), 0, yaw)
    return centre, width, width * 285 / 1215


# ---------- the city ----------

def city_material():
    """Dark towers with windows in rows: whole floors dark, a few lit, mostly blue, now and then warm."""
    mat = bpy.data.materials.new("city")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial")
    geo = node(nt, "ShaderNodeNewGeometry")
    sep = node(nt, "ShaderNodeSeparateXYZ")
    link(nt, geo.outputs["Position"], sep.inputs[0])
    along = node(nt, "ShaderNodeMath")  # x + y runs along any face of an axis-aligned box
    along.operation = "ADD"
    link(nt, sep.outputs["X"], along.inputs[0])
    link(nt, sep.outputs["Y"], along.inputs[1])
    uv = node(nt, "ShaderNodeCombineXYZ")
    link(nt, along.outputs[0], uv.inputs["X"])
    link(nt, sep.outputs["Z"], uv.inputs["Y"])
    brick = node(nt, "ShaderNodeTexBrick", Scale=0.3, **{"Mortar Size": 0.1, "Brick Width": 0.6,
                                                         "Row Height": 1.0, "Mortar Smooth": 0.0})
    brick.offset = 0.0
    brick.inputs["Color1"].default_value = (1, 1, 1, 1)
    brick.inputs["Color2"].default_value = (1, 1, 1, 1)
    brick.inputs["Mortar"].default_value = (0, 0, 0, 1)
    link(nt, uv.outputs[0], brick.inputs["Vector"])
    # a floor is lit or not: white noise per tower (coarse x, y) and floor (z every 3.3 m)
    snap = node(nt, "ShaderNodeVectorMath")
    snap.operation = "SNAP"
    snap.inputs[1].default_value = (40.0, 40.0, 3.3)
    link(nt, geo.outputs["Position"], snap.inputs[0])
    floor = node(nt, "ShaderNodeTexWhiteNoise")
    floor.noise_dimensions = "3D"
    link(nt, snap.outputs[0], floor.inputs["Vector"])
    floor_on = node(nt, "ShaderNodeMath")
    floor_on.operation = "GREATER_THAN"
    floor_on.inputs[1].default_value = 0.8
    link(nt, floor.outputs["Value"], floor_on.inputs[0])
    snap2 = node(nt, "ShaderNodeVectorMath")
    snap2.operation = "SNAP"
    snap2.inputs[1].default_value = (2.0, 2.0, 3.3)
    link(nt, geo.outputs["Position"], snap2.inputs[0])
    cell = node(nt, "ShaderNodeTexWhiteNoise")
    cell.noise_dimensions = "3D"
    link(nt, snap2.outputs[0], cell.inputs["Vector"])
    cell_on = node(nt, "ShaderNodeMath")
    cell_on.operation = "GREATER_THAN"
    cell_on.inputs[1].default_value = 0.35
    link(nt, cell.outputs["Value"], cell_on.inputs[0])
    lit = node(nt, "ShaderNodeMath")
    lit.operation = "MULTIPLY"
    link(nt, floor_on.outputs[0], lit.inputs[0])
    link(nt, cell_on.outputs[0], lit.inputs[1])
    lit2 = node(nt, "ShaderNodeMath")
    lit2.operation = "MULTIPLY"
    link(nt, lit.outputs[0], lit2.inputs[0])
    link(nt, brick.outputs["Color"], lit2.inputs[1])
    tint = node(nt, "ShaderNodeMix")
    tint.data_type = "RGBA"
    link(nt, cell.outputs["Value"], tint.inputs["Factor"])
    tint.inputs["A"].default_value = srgb(CITY_WIN2)
    tint.inputs["B"].default_value = srgb(CITY_WIN)
    warm = node(nt, "ShaderNodeMath")
    warm.operation = "GREATER_THAN"
    warm.inputs[1].default_value = 0.93
    link(nt, floor.outputs["Value"], warm.inputs[0])
    tint2 = node(nt, "ShaderNodeMix")
    tint2.data_type = "RGBA"
    link(nt, warm.outputs[0], tint2.inputs["Factor"])
    link(nt, tint.outputs["Result"], tint2.inputs["A"])
    tint2.inputs["B"].default_value = srgb(CITY_WARM)
    em = node(nt, "ShaderNodeEmission")
    link(nt, tint2.outputs["Result"], em.inputs["Color"])
    strength = node(nt, "ShaderNodeMath")
    strength.operation = "MULTIPLY"
    strength.inputs[1].default_value = 5.0
    link(nt, lit2.outputs[0], strength.inputs[0])
    link(nt, strength.outputs[0], em.inputs["Strength"])
    body = node(nt, "ShaderNodeBsdfPrincipled")
    body.inputs["Base Color"].default_value = srgb(CITY_BODY)
    body.inputs["Roughness"].default_value = 0.6
    add = node(nt, "ShaderNodeAddShader")
    link(nt, body.outputs[0], add.inputs[0])
    link(nt, em.outputs[0], add.inputs[1])
    link(nt, add.outputs[0], out.inputs["Surface"])
    return mat


class Boxes:
    def __init__(self):
        self.v, self.f = [], []

    def box(self, lo, hi):
        n = len(self.v)
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        self.v += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                   (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        self.f += [(n, n + 3, n + 2, n + 1), (n + 4, n + 5, n + 6, n + 7), (n, n + 1, n + 5, n + 4),
                   (n + 1, n + 2, n + 6, n + 5), (n + 2, n + 3, n + 7, n + 6), (n + 3, n, n + 4, n + 7)]

    def done(self, name, mat):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        me.update()
        return tk.add_object(name, me, mat)


def city(rng):
    """Blocks from 600 m out to the horizon: taller and sparser near, a dense low sprawl far, a few very tall
    towers well left of the word, red lamps on the tall roofs."""
    B, L = Boxes(), Boxes()
    for _ in range(5000):
        d = 600 + rng.random() ** 0.7 * 9000
        bearing = math.radians(rng.uniform(-62, 62))
        x, y = d * math.sin(bearing), d * math.cos(bearing)
        near = max(0.0, 1.0 - (d - 600) / 3000)
        h = rng.uniform(15, 50) + near * rng.random() ** 2 * 150
        if rng.random() < 0.04:
            h *= 1.8
        w, dp = rng.uniform(20, 55), rng.uniform(20, 55)
        B.box((x - w / 2, y - dp / 2, 0), (x + w / 2, y + dp / 2, h))
        if h > 110 and rng.random() < 0.7:
            for sx in (-1, 1):
                L.box((x + sx * w / 2 - 1.5, y - dp / 2 - 1.5, h), (x + sx * w / 2 + 1.5, y - dp / 2 + 1.5, h + 3))
    for bearing, d, h in [(-48, 2600, 360), (-41, 3400, 330), (-55, 2200, 300)]:  # the tall ones, left of the word
        x, y = d * math.sin(math.radians(bearing)), d * math.cos(math.radians(bearing))
        B.box((x - 35, y - 35, 0), (x + 35, y + 35, h))
        B.box((x - 15, y - 15, h), (x + 15, y + 15, h + 30))
        L.box((x - 2, y - 2, h + 30), (x + 2, y + 2, h + 34))
    B.done("city", city_material())
    L.done("lamps", tk.emissive("lamp", srgb(LAMP), 60.0))


# ---------- air and light ----------

def air():
    """Haze over the city, densest at the ground and gone by 320 m, so the sky round the word stays clean, with
    the city's own light in it: a blue band brightest at the rooftops, fading upward."""
    mat = bpy.data.materials.new("air")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial")
    geo = node(nt, "ShaderNodeNewGeometry")
    sep = node(nt, "ShaderNodeSeparateXYZ")
    link(nt, geo.outputs["Position"], sep.inputs[0])
    fall = node(nt, "ShaderNodeMapRange")
    fall.interpolation_type = "SMOOTHSTEP"
    link(nt, sep.outputs["Z"], fall.inputs["Value"])
    fall.inputs["From Min"].default_value, fall.inputs["From Max"].default_value = 0.0, 320.0
    fall.inputs["To Min"].default_value, fall.inputs["To Max"].default_value = 1.0, 0.0
    sq = node(nt, "ShaderNodeMath")
    sq.operation = "POWER"
    sq.inputs[1].default_value = 2.0
    link(nt, fall.outputs["Result"], sq.inputs[0])
    dens = node(nt, "ShaderNodeMath")
    dens.operation = "MULTIPLY"
    dens.inputs[1].default_value = HAZE_D
    link(nt, sq.outputs[0], dens.inputs[0])
    glow = node(nt, "ShaderNodeMath")
    glow.operation = "MULTIPLY"
    glow.inputs[1].default_value = GLOW
    link(nt, sq.outputs[0], glow.inputs[0])
    vol = node(nt, "ShaderNodeVolumePrincipled", Anisotropy=0.4)
    vol.inputs["Color"].default_value = srgb(HAZE)
    vol.inputs["Emission Color"].default_value = srgb(CITY_DEEP)
    link(nt, dens.outputs[0], vol.inputs["Density"])
    link(nt, glow.outputs[0], vol.inputs["Emission Strength"])
    link(nt, vol.outputs[0], out.inputs["Volume"])
    me = tk.bm_mesh("air", lambda bm: __import__("bmesh").ops.create_cube(bm, size=1.0))
    ob = tk.add_object("air", me, mat, (0, 5000, 160))
    ob.scale = (24000, 11000, 320)


def lights(centre, width, height):
    """The city's light on the word: blue-white from the rooftops below and in front, red from the lamps low
    on the left, on the side faces the view sees."""
    below = centre + Vector((0, -12, -height * 0.5 - 28))  # steep: the faces graze it, so it falls off upward
    up = tk.light("AREA", below, UP_W, srgb(UPLIGHT),
                  rotation=(centre - below).to_track_quat("-Z", "Y").to_euler())
    up.data.shape = "RECTANGLE"
    up.data.size, up.data.size_y = width * 1.1, 24
    rimsrc = centre + Vector((-width * 0.75, 60, -height * 0.5 - 60))  # left: the side faces in view
    rim = tk.light("AREA", rimsrc, RIM_W, srgb(LAMP),
                   rotation=(centre - rimsrc).to_track_quat("-Z", "Y").to_euler())
    rim.data.size = 150
    for ob in (up, rim):
        ob.visible_camera = False


def build():
    sc = tk.reset()
    sc.view_settings.look = "AgX - Punchy"
    sc.render.resolution_x, sc.render.resolution_y = RES
    rng = random.Random(1)
    tk.set_world(srgb(SKY), 1.0)
    centre, width, height = word()
    city(rng)
    air()
    lights(centre, width, height)
    cam = tk.camera(CAM, CAM + Vector((0, math.cos(PITCH), math.sin(PITCH))), LENS)
    cam.data.clip_end = 12000
    return sc


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "backgrounds"))
    ap.add_argument("--percent", type=int, default=100)
    ap.add_argument("--samples", type=int, default=64)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    sc = build()
    sc.render.resolution_percentage = a.percent
    sc.cycles.samples = a.samples
    sc.render.filepath = os.path.join(a.out, f"{NAME}.png")
    with open(GPU_LOCK, "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        bpy.ops.render.render(write_still=True)
    print("wrote", sc.render.filepath, flush=True)


if __name__ == "__main__":
    main()
