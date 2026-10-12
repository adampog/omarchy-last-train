"""The city kit the scenes share: building boxes with windows, the wet road, neon tubes, mist, haze and steam.

All of it is geometry and procedural shaders. Colours are passed in by the scenes, which take them from
colors.toml.
"""

import argparse
import math
import os
import sys

import bpy
import bmesh

import scenes as tk
from scenes import srgb, node, link


def math_node(nt, op, a=None, b=None, c=None):
    """A Math node; a, b and c are sockets or numbers."""
    n = node(nt, "ShaderNodeMath")
    n.operation = op
    for k, v in enumerate((a, b, c)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[k].default_value = v
        else:
            link(nt, v, n.inputs[k])
    return n.outputs[0]


def vec_node(nt, op, a=None, b=None):
    n = node(nt, "ShaderNodeVectorMath")
    n.operation = op
    for k, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, tuple):
            n.inputs[k].default_value = v
        else:
            link(nt, v, n.inputs[k])
    return n


def mix_rgb(nt, fac, a, b):
    """Mix of two colours; fac, a and b are sockets or values."""
    n = node(nt, "ShaderNodeMix")
    n.data_type = "RGBA"
    for key, v in (("Factor", fac), ("A", a), ("B", b)):
        if isinstance(v, (int, float, tuple)):
            n.inputs[key].default_value = v
        else:
            link(nt, v, n.inputs[key])
    return n.outputs["Result"]


# ---------- geometry ----------

class Boxes:
    """Many axis-aligned boxes in one mesh."""

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


def tube(name, loops, radius, mat, cyclic=False):
    """Round tubes along lists of points: neon, cables, rails."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    for pts in loops:
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for k, p in enumerate(pts):
            sp.points[k].co = (*p, 1)
        sp.use_cyclic_u = cyclic
    return tk.add_object(name, cu, mat)


def ring(centre, r, n=48, axis="y"):
    """Points of a circle in the plane facing along axis."""
    cx, cy, cz = centre
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        if axis == "y":
            pts.append((cx + r * math.cos(a), cy, cz + r * math.sin(a)))
        else:
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a), cz))
    return pts


def sag(a, b, drop, n=16):
    """A hanging cable from a to b."""
    return [tuple(a[i] + (b[i] - a[i]) * t - (drop * 4 * t * (1 - t) if i == 2 else 0) for i in range(3))
            for t in (k / n for k in range(n + 1))]


# ---------- materials ----------

def plain(name, colour, roughness=0.6, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = srgb(colour)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = metallic
    return mat


def facade(name, body, glass, cool_a, cool_b, warm, bay=2.0, floor_h=3.3, lit=0.1, strength=2.0, warm_part=0.3,
           ground=0.0):
    """A building face: concrete with rows of glossy dark windows, a few of them lit, cool or warm. Works on any
    face of an axis-aligned box. Nothing is lit below `ground` metres."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial")
    geo = node(nt, "ShaderNodeNewGeometry")
    sep = node(nt, "ShaderNodeSeparateXYZ")
    link(nt, geo.outputs["Position"], sep.inputs[0])
    along = math_node(nt, "ADD", sep.outputs["X"], sep.outputs["Y"])  # runs along any vertical face
    uv = node(nt, "ShaderNodeCombineXYZ")
    link(nt, along, uv.inputs["X"])
    link(nt, sep.outputs["Z"], uv.inputs["Y"])
    brick = node(nt, "ShaderNodeTexBrick", Scale=1.0, **{"Mortar Size": 0.3, "Brick Width": bay,
                                                         "Row Height": floor_h, "Mortar Smooth": 0.0})
    brick.offset = 0.0
    brick.inputs["Color1"].default_value = (1, 1, 1, 1)
    brick.inputs["Color2"].default_value = (1, 1, 1, 1)
    brick.inputs["Mortar"].default_value = (0, 0, 0, 1)
    link(nt, uv.outputs[0], brick.inputs["Vector"])
    # the window sits between sill and head in each floor
    f = math_node(nt, "FRACT", math_node(nt, "DIVIDE", sep.outputs["Z"], floor_h))
    band = math_node(nt, "MULTIPLY", math_node(nt, "GREATER_THAN", f, 0.3), math_node(nt, "LESS_THAN", f, 0.85))
    wall = math_node(nt, "GREATER_THAN", math_node(nt, "ABSOLUTE", node_normal_z(nt, geo)), 0.5)  # roofs: no windows
    win = math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", brick.outputs["Color"], band),
                    math_node(nt, "SUBTRACT", 1.0, wall))
    win = math_node(nt, "MULTIPLY", win, math_node(nt, "GREATER_THAN", sep.outputs["Z"], ground))
    # which windows are lit: white noise per bay and floor, and whole floors now and then
    cell = vec_node(nt, "SNAP", uv.outputs[0], (bay, floor_h, 1.0))
    block = vec_node(nt, "SNAP", geo.outputs["Position"], (30.0, 30.0, 10000.0))
    cid = vec_node(nt, "ADD", cell.outputs[0], block.outputs[0])
    wn = node(nt, "ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    link(nt, cid.outputs[0], wn.inputs["Vector"])
    rgb = node(nt, "ShaderNodeSeparateColor")
    link(nt, wn.outputs["Color"], rgb.inputs[0])
    on = math_node(nt, "GREATER_THAN", wn.outputs["Value"], 1.0 - lit)
    cool = mix_rgb(nt, rgb.outputs[0], srgb(cool_a), srgb(cool_b))
    colour = mix_rgb(nt, math_node(nt, "LESS_THAN", rgb.outputs[1], warm_part), cool, srgb(warm))
    level = math_node(nt, "MULTIPLY_ADD", rgb.outputs[2], 0.7, 0.3)
    em = node(nt, "ShaderNodeEmission")
    link(nt, colour, em.inputs["Color"])
    link(nt, math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", win, on), math_node(nt, "MULTIPLY", level, strength)),
         em.inputs["Strength"])
    # concrete with grime, glass where the windows are
    grime = node(nt, "ShaderNodeTexNoise", Scale=0.35, Detail=6.0, Roughness=0.6)
    link(nt, geo.outputs["Position"], grime.inputs["Vector"])
    shade = mix_rgb(nt, grime.outputs["Fac"], tk.scale(srgb(body), 0.55), srgb(body))
    bsdf = node(nt, "ShaderNodeBsdfPrincipled")
    link(nt, mix_rgb(nt, win, shade, srgb(glass)), bsdf.inputs["Base Color"])
    link(nt, math_node(nt, "MULTIPLY_ADD", win, -0.62, 0.7), bsdf.inputs["Roughness"])
    add = node(nt, "ShaderNodeAddShader")
    link(nt, bsdf.outputs[0], add.inputs[0])
    link(nt, em.outputs[0], add.inputs[1])
    link(nt, add.outputs[0], out.inputs["Surface"])
    return mat


def node_normal_z(nt, geo):
    sep = node(nt, "ShaderNodeSeparateXYZ")
    link(nt, geo.outputs["Normal"], sep.inputs[0])
    return sep.outputs["Z"]


def wet_road(name, colour, puddle=0.5, size=1.0, rough=0.32, lines=None, slick=None):
    """Wet asphalt: mirror puddles with broken edges, rougher grain between them. `slick(nt, geo)` gives a 0 to 1
    socket for where a film of water smooths the grain, so lights smear down it."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial")
    geo = node(nt, "ShaderNodeNewGeometry")
    big = node(nt, "ShaderNodeTexNoise", Scale=0.22 / size, Detail=5.0, Roughness=0.55)
    link(nt, geo.outputs["Position"], big.inputs["Vector"])
    ramp = node(nt, "ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = puddle - 0.04
    ramp.inputs["From Max"].default_value = puddle + 0.04
    link(nt, big.outputs["Fac"], ramp.inputs["Value"])  # 0 in a puddle, 1 on the grain
    dry = ramp.outputs["Result"]
    keep = 1.0 if slick is None else math_node(nt, "SUBTRACT", 1.0, slick(nt, geo))
    grain = node(nt, "ShaderNodeTexNoise", Scale=60.0, Detail=3.0, Roughness=0.7)
    link(nt, geo.outputs["Position"], grain.inputs["Vector"])
    ripple = node(nt, "ShaderNodeTexNoise", Scale=9.0, Detail=2.0, Roughness=0.5)
    link(nt, geo.outputs["Position"], ripple.inputs["Vector"])
    bsdf = node(nt, "ShaderNodeBsdfPrincipled")
    base = mix_rgb(nt, dry, tk.scale(srgb(colour), 0.5), srgb(colour))
    if lines is not None:
        base = lines(nt, geo, base)
    link(nt, base, bsdf.inputs["Base Color"])
    if slick is None:
        link(nt, math_node(nt, "MULTIPLY_ADD", dry, rough - 0.04, 0.04), bsdf.inputs["Roughness"])
        grit = math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", grain.outputs["Fac"], dry), 0.004)
    else:
        link(nt, math_node(nt, "MULTIPLY_ADD", math_node(nt, "MULTIPLY", dry, keep), rough - 0.04, 0.04),
             bsdf.inputs["Roughness"])
        grit = math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", grain.outputs["Fac"], dry),
                                                   keep), 0.004)
    height = math_node(nt, "ADD", grit,
                       math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", 1.0, dry),
                                 math_node(nt, "MULTIPLY", ripple.outputs["Fac"], 0.0015)))
    bump = node(nt, "ShaderNodeBump", Strength=1.0, Distance=1.0)
    link(nt, height, bump.inputs["Height"])
    link(nt, bump.outputs[0], bsdf.inputs["Normal"])
    link(nt, bsdf.outputs[0], out.inputs["Surface"])
    return mat


def water(name, colour, roughness=0.05, waves=1.0):
    """Black water with small ripples."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial")
    geo = node(nt, "ShaderNodeNewGeometry")
    n1 = node(nt, "ShaderNodeTexNoise", Scale=0.8, Detail=4.0, Roughness=0.6)
    link(nt, vec_node(nt, "MULTIPLY", geo.outputs["Position"], (1.0, 0.25, 1.0)).outputs[0], n1.inputs["Vector"])
    bump = node(nt, "ShaderNodeBump", Strength=waves, Distance=0.05)
    link(nt, n1.outputs["Fac"], bump.inputs["Height"])
    bsdf = node(nt, "ShaderNodeBsdfPrincipled", Roughness=roughness)
    bsdf.inputs["Base Color"].default_value = srgb(colour)
    link(nt, bump.outputs[0], bsdf.inputs["Normal"])
    link(nt, bsdf.outputs[0], out.inputs["Surface"])
    return mat


# ---------- air ----------

def _volume_box(name, mat, centre, dims):
    me = tk.bm_mesh(name, lambda bm: bmesh.ops.create_cube(bm, size=1.0))
    ob = tk.add_object(name, me, mat, centre)
    ob.scale = dims
    return ob


def mist(name, centre, radius, density, colour, anisotropy=0.5, squash=(1, 1, 1), glow=None, glow_strength=0.0,
         power=2.0):
    """Mist round a lamp: densest at `centre`, gone at `radius`, so the light has a body and the rest of the frame
    stays black. `glow` adds the lamp's own colour to the air close to it."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial")
    geo = node(nt, "ShaderNodeNewGeometry")
    rel = vec_node(nt, "SUBTRACT", geo.outputs["Position"], tuple(centre))
    rel = vec_node(nt, "DIVIDE", rel.outputs[0], tuple(squash))
    dist = vec_node(nt, "LENGTH", rel.outputs[0]).outputs["Value"]
    fall = node(nt, "ShaderNodeMapRange")
    fall.inputs["From Min"].default_value, fall.inputs["From Max"].default_value = 0.0, radius
    fall.inputs["To Min"].default_value, fall.inputs["To Max"].default_value = 1.0, 0.0
    link(nt, dist, fall.inputs["Value"])
    f = math_node(nt, "POWER", fall.outputs["Result"], power)
    vol = node(nt, "ShaderNodeVolumePrincipled", Anisotropy=anisotropy)
    vol.inputs["Color"].default_value = srgb(colour)
    link(nt, math_node(nt, "MULTIPLY", f, density), vol.inputs["Density"])
    if glow is not None:
        vol.inputs["Emission Color"].default_value = srgb(glow)
        link(nt, math_node(nt, "MULTIPLY", math_node(nt, "POWER", f, 2.0), glow_strength),
             vol.inputs["Emission Strength"])
    link(nt, vol.outputs[0], out.inputs["Volume"])
    d = tuple(2 * radius * s for s in squash)
    return _volume_box(name, mat, centre, d)


def haze_layer(name, centre, dims, top, density, colour, glow, glow_strength, anisotropy=0.4, base=0.0):
    """Haze over the far city: densest at `base` metres, gone at `top`, with the city's own light in it."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial")
    geo = node(nt, "ShaderNodeNewGeometry")
    sep = node(nt, "ShaderNodeSeparateXYZ")
    link(nt, geo.outputs["Position"], sep.inputs[0])
    fall = node(nt, "ShaderNodeMapRange")
    fall.interpolation_type = "SMOOTHSTEP"
    fall.inputs["From Min"].default_value, fall.inputs["From Max"].default_value = base, top
    fall.inputs["To Min"].default_value, fall.inputs["To Max"].default_value = 1.0, 0.0
    link(nt, sep.outputs["Z"], fall.inputs["Value"])
    f = math_node(nt, "POWER", fall.outputs["Result"], 2.0)
    vol = node(nt, "ShaderNodeVolumePrincipled", Anisotropy=anisotropy)
    vol.inputs["Color"].default_value = srgb(colour)
    vol.inputs["Emission Color"].default_value = srgb(glow)
    link(nt, math_node(nt, "MULTIPLY", f, density), vol.inputs["Density"])
    link(nt, math_node(nt, "MULTIPLY", f, glow_strength), vol.inputs["Emission Strength"])
    link(nt, vol.outputs[0], out.inputs["Volume"])
    return _volume_box(name, mat, centre, dims)


def low_cloud(name, centre, dims, base, top, density, colour, anisotropy=0.5, size=9.0, frame=0.0):
    """Low cloud lying on a roof: thickest at `base` metres, a soft ceiling at `top`, in billows `size` metres
    across. It has no light of its own; whatever lamp stands in it gives it its colour."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial")
    geo = node(nt, "ShaderNodeNewGeometry")
    sep = node(nt, "ShaderNodeSeparateXYZ")
    link(nt, geo.outputs["Position"], sep.inputs[0])
    fall = node(nt, "ShaderNodeMapRange")
    fall.interpolation_type = "SMOOTHSTEP"
    fall.inputs["From Min"].default_value, fall.inputs["From Max"].default_value = base, top
    fall.inputs["To Min"].default_value, fall.inputs["To Max"].default_value = 1.0, 0.0
    link(nt, sep.outputs["Z"], fall.inputs["Value"])
    billow = node(nt, "ShaderNodeTexNoise", Scale=1.0 / size, Detail=2.0, Roughness=0.55)
    billow.noise_dimensions = "4D"
    billow.inputs["W"].default_value = frame
    link(nt, vec_node(nt, "MULTIPLY", geo.outputs["Position"], (1.0, 1.0, 2.2)).outputs[0], billow.inputs["Vector"])
    part = node(nt, "ShaderNodeMapRange")
    part.interpolation_type = "SMOOTHSTEP"
    part.inputs["From Min"].default_value, part.inputs["From Max"].default_value = 0.42, 0.62
    part.inputs["To Min"].default_value, part.inputs["To Max"].default_value = 0.03, 1.0
    link(nt, billow.outputs["Fac"], part.inputs["Value"])
    vol = node(nt, "ShaderNodeVolumePrincipled", Anisotropy=anisotropy)
    vol.inputs["Color"].default_value = srgb(colour)
    link(nt, math_node(nt, "MULTIPLY", math_node(nt, "POWER", fall.outputs["Result"], 1.6),
                       math_node(nt, "MULTIPLY", part.outputs["Result"], density)), vol.inputs["Density"])
    link(nt, vol.outputs[0], out.inputs["Volume"])
    return _volume_box(name, mat, centre, dims)


def steam(name, base, height, radius, density, colour, anisotropy=0.6, glow=None, glow_strength=0.0, broken=0.0,
          frame=0.0):
    """A column of steam from `base`: wider and thinner as it rises, broken by noise. `glow` is the light it has
    caught, for steam that stands far from any lamp. `broken` above 0 tears it into billows with two octaves of
    noise and thins the top; `frame` is the fixed moment of that noise."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial")
    geo = node(nt, "ShaderNodeNewGeometry")
    rel = vec_node(nt, "SUBTRACT", geo.outputs["Position"], tuple(base))
    sep = node(nt, "ShaderNodeSeparateXYZ")
    link(nt, rel.outputs[0], sep.inputs[0])
    up = math_node(nt, "DIVIDE", sep.outputs["Z"], height)  # 0 at the grate, 1 at the top
    drift = math_node(nt, "MULTIPLY", math_node(nt, "POWER", up, 1.5), radius * 1.2)  # leans as it rises
    dx = math_node(nt, "SUBTRACT", sep.outputs["X"], drift)
    dy = sep.outputs["Y"]
    if broken:
        # the column wanders: a slow noise pushes it sideways, more as it rises
        wander = node(nt, "ShaderNodeTexNoise", Scale=0.3, Detail=1.0, Roughness=0.5)
        wander.noise_dimensions = "4D"
        wander.inputs["W"].default_value = frame
        link(nt, geo.outputs["Position"], wander.inputs["Vector"])
        w = node(nt, "ShaderNodeSeparateColor")
        link(nt, wander.outputs["Color"], w.inputs[0])
        push = math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY_ADD", up, 1.0, 0.25), broken * radius * 1.6)
        dx = math_node(nt, "SUBTRACT", dx, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", w.outputs[0], 0.5), push))
        dy = math_node(nt, "SUBTRACT", dy, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", w.outputs[1], 0.5), push))
    r = math_node(nt, "SQRT", math_node(nt, "ADD", math_node(nt, "POWER", dx, 2.0), math_node(nt, "POWER", dy, 2.0)))
    width = math_node(nt, "MULTIPLY_ADD", up, radius * 0.8, radius * 0.2)
    core = math_node(nt, "SUBTRACT", 1.0, math_node(nt, "DIVIDE", r, width))
    core = math_node(nt, "MAXIMUM", core, 0.0)
    fade = math_node(nt, "MAXIMUM", math_node(nt, "SUBTRACT", 1.0, up), 0.0)
    noise = node(nt, "ShaderNodeTexNoise", Scale=1.3, Detail=5.0, Roughness=0.65)
    link(nt, vec_node(nt, "MULTIPLY", geo.outputs["Position"], (1.0, 1.0, 0.45)).outputs[0], noise.inputs["Vector"])
    puff = node(nt, "ShaderNodeMapRange")
    puff.inputs["From Min"].default_value, puff.inputs["From Max"].default_value = 0.36, 0.62
    link(nt, noise.outputs["Fac"], puff.inputs["Value"])
    if broken:
        # two octaves, the billows and the wisps on them, eat into the column from its edge
        octs = []
        for scale, squeeze in ((0.55, 0.6), (1.9, 0.5)):
            n = node(nt, "ShaderNodeTexNoise", Scale=scale, Detail=0.0, Roughness=0.5)
            n.noise_dimensions = "4D"
            n.inputs["W"].default_value = frame
            link(nt, vec_node(nt, "MULTIPLY", geo.outputs["Position"], (1.0, 1.0, squeeze)).outputs[0],
                 n.inputs["Vector"])
            octs.append(n.outputs["Fac"])
        both = math_node(nt, "ADD", math_node(nt, "MULTIPLY", octs[0], 0.62), math_node(nt, "MULTIPLY", octs[1], 0.38))
        gap = node(nt, "ShaderNodeMapRange")
        gap.interpolation_type = "SMOOTHSTEP"
        gap.inputs["From Min"].default_value, gap.inputs["From Max"].default_value = 0.4, 0.62
        link(nt, both, gap.inputs["Value"])
        eaten = math_node(nt, "SUBTRACT", core, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", 1.0,
                                                                                    gap.outputs["Result"]), broken))
        core = math_node(nt, "MAXIMUM", eaten, 0.0)
        fade = math_node(nt, "POWER", fade, 1.8)
        d = math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", core, fade), density)
    else:
        d = math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", core, fade),
                      math_node(nt, "MULTIPLY", puff.outputs["Result"], density))
    vol = node(nt, "ShaderNodeVolumePrincipled", Anisotropy=anisotropy)
    vol.inputs["Color"].default_value = srgb(colour)
    link(nt, d, vol.inputs["Density"])
    if glow is not None:
        vol.inputs["Emission Color"].default_value = srgb(glow)
        link(nt, math_node(nt, "MULTIPLY", d, glow_strength), vol.inputs["Emission Strength"])
    link(nt, vol.outputs[0], out.inputs["Volume"])
    bx, by, bz = base
    return _volume_box(name, mat, (bx + radius * 0.6, by, bz + height / 2), (radius * 4.4, radius * 2.2, height))


# ---------- the far city ----------

def skyline(rng, mat, lamp_mat, count, near, far, spread, heights, tall=0.04, x0=0.0, turn=0.0):
    """Towers from `near` to `far` metres out, `spread` degrees either side of `turn` degrees right of ahead."""
    B, L = Boxes(), Boxes()
    for _ in range(count):
        d = near + rng.random() ** 0.8 * (far - near)
        a = math.radians(turn + rng.uniform(-spread, spread))
        x, y = x0 + d * math.sin(a), d * math.cos(a)
        h = rng.uniform(*heights)
        if rng.random() < tall:
            h *= 1.9
        w, dp = rng.uniform(18, 46), rng.uniform(18, 46)
        B.box((x - w / 2, y - dp / 2, 0), (x + w / 2, y + dp / 2, h))
        if rng.random() < 0.35:  # a set-back top
            B.box((x - w / 4, y - dp / 4, h), (x + w / 4, y + dp / 4, h + rng.uniform(4, 14)))
        if h > heights[1] * 0.8 and lamp_mat is not None:
            L.box((x - 1.2, y - dp / 2 - 1.2, h), (x + 1.2, y - dp / 2 + 1.2, h + 2.4))
    B.done("skyline", mat)
    if L.v:
        L.done("skyline_lamps", lamp_mat)


# ---------- running a scene ----------

def run(build, name, res=tk.RES, samples=128):
    """Parse the usual arguments, build the scene and render it to <out>/<name>.png."""
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(tk.REPO, "backgrounds"))
    ap.add_argument("--percent", type=int, default=100)
    ap.add_argument("--samples", type=int, default=samples)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    sc = build()
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = a.percent
    sc.cycles.samples = a.samples
    tk.render(sc, os.path.join(a.out, f"{name}.png"))
