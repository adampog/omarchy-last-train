"""Shared plumbing for the scenes in this folder: palette, Cycles setup, meshes, lights, camera and the render call.

Everything is modelled, lit and textured from geometry and procedural shaders. No images, textures, environment
maps or models are loaded. Colours come from the theme's colors.toml.
"""

import fcntl
import os
import tomllib

import bpy  # noqa: E402  (bmesh and mathutils load with bpy)
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RES = (3440, 1440)


# ---------- palette ----------

def palette():
    """The theme's colors.toml as a dict of '#rrggbb'."""
    with open(os.path.join(REPO, "colors.toml"), "rb") as fh:
        return tomllib.load(fh)


def mix(a, b, t):
    """The colour t of the way from a to b, as '#rrggbb'."""
    ca, cb = (tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in (a, b))
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def srgb(h):
    """'#rrggbb' -> linear RGBA for Blender."""
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(lin(int(h[i:i + 2], 16)) for i in (1, 3, 5)) + (1.0,)


def mixc(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def scale(a, k):
    return tuple(x * k for x in a[:3]) + (1.0,)


# ---------- scene plumbing ----------

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    sc.cycles.device = "GPU"
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPTIX"
    sc.cycles.seed = 1
    sc.cycles.max_bounces = 8
    sc.cycles.volume_bounces = 1
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.color_depth = "8"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    world = bpy.data.worlds.new("world")
    sc.world = world
    world.use_nodes = True
    return sc


def node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n


def link(nt, a, b):
    nt.links.new(a, b)


def set_world(colour, strength=1.0):
    nt = bpy.context.scene.world.node_tree
    bg = nt.nodes.get("Background") or node(nt, "ShaderNodeBackground")
    bg.inputs["Color"].default_value = colour
    bg.inputs["Strength"].default_value = strength
    out = nt.nodes.get("World Output") or node(nt, "ShaderNodeOutputWorld")
    link(nt, bg.outputs[0], out.inputs["Surface"])


def add_object(name, mesh, material=None, location=(0, 0, 0), smooth=False):
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = location
    if material:
        mesh.materials.append(material)
    if smooth:
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    return ob


def bm_mesh(name, build):
    bm = bmesh.new()
    build(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def box(name, size, location, material, bevel=0.0):
    me = bm_mesh(name, lambda bm: bmesh.ops.create_cube(bm, size=1.0))
    ob = add_object(name, me, material, location)
    ob.scale = size
    if bevel:
        m = ob.modifiers.new("bevel", "BEVEL")
        m.width = bevel
        m.segments = 2
    return ob


def cylinder(name, radius, depth, location, material, segments=48, radius2=None):
    me = bm_mesh(name, lambda bm: bmesh.ops.create_cone(
        bm, cap_ends=True, segments=segments, radius1=radius, radius2=radius if radius2 is None else radius2,
        depth=depth))
    return add_object(name, me, material, location, smooth=True)


def sphere(name, radius, location, material, seg=32):
    me = bm_mesh(name, lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=radius))
    return add_object(name, me, material, location, smooth=True)


def plane(name, size, location, material, rotation=(0, 0, 0)):
    me = bm_mesh(name, lambda bm: bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2))
    ob = add_object(name, me, material, location)
    ob.rotation_euler = rotation
    return ob


def light(kind, location, energy, colour, size=0.1, rotation=(0, 0, 0), angle=None):
    ld = bpy.data.lights.new(kind.lower(), type=kind)
    ld.energy = energy
    ld.color = colour[:3]
    if kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = size
    elif kind == "AREA":
        ld.size = size
    elif kind == "SUN" and angle is not None:
        ld.angle = angle
    ob = bpy.data.objects.new(kind.lower(), ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = location
    ob.rotation_euler = rotation
    return ob


def fog(density, colour, size=60, centre=(0, 0, 0), anisotropy=0.3, dims=None):
    mat = bpy.data.materials.new("fog")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    vol = node(nt, "ShaderNodeVolumePrincipled", Density=density, Anisotropy=anisotropy)
    vol.inputs["Color"].default_value = colour
    out = node(nt, "ShaderNodeOutputMaterial")
    link(nt, vol.outputs[0], out.inputs["Volume"])
    me = bm_mesh("fog", lambda bm: bmesh.ops.create_cube(bm, size=1.0))
    ob = add_object("fog", me, mat, centre)
    ob.scale = dims or (size, size, size)  # a shallow layer lets a low sun reach the scene
    return ob


def camera(location, target, lens, focus=None, fstop=2.8):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36
    cd.clip_end = 2000
    ob = bpy.data.objects.new("cam", cd)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = location
    d = Vector(target) - Vector(location)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if focus is not None:
        cd.dof.use_dof = True
        cd.dof.focus_distance = focus if isinstance(focus, (int, float)) else (Vector(focus) - Vector(location)).length
        cd.dof.aperture_fstop = fstop
    bpy.context.scene.camera = ob
    return ob


def emissive(name, colour, strength):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial")
    em = node(nt, "ShaderNodeEmission", Strength=strength)
    em.inputs["Color"].default_value = colour
    link(nt, em.outputs[0], out.inputs["Surface"])
    return mat


# ---------- render ----------

def gpu_lock():
    """The lock file that keeps renders one at a time: $GPU_LOCK, or .gpu.lock beside the repo if there is one."""
    path = os.environ.get("GPU_LOCK") or os.path.join(REPO, "..", ".gpu.lock")
    return path if os.environ.get("GPU_LOCK") or os.path.exists(path) else None


def render(sc, path):
    sc.render.filepath = path
    lock = gpu_lock()
    if lock:
        with open(lock, "a") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(write_still=True)
    print("wrote", path, flush=True)
