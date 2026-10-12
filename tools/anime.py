"""The animated look: a scene is rendered as flat data and the picture is painted from it in numpy.

The renderer writes five data images and no lighting: each surface's flat local colour, what glows, where each
pixel is in the world, which way it faces, and a hard shadow mask of the one key light. Everything seen is then
painted here: flat tones, pen lines, a gradient sky, a stepped far city, drawn lamps and halos, smears on wet
ground, rain, one even grain. Near edges are pulled a pixel or two off the ruler and lines hesitate at corners;
windows are drawn on the walls here, uneven, not taken from a computed grid. A scene describes itself with a `Look` and may add its own drawn things in hooks.

The painter darkens the top 480 px of every picture, to 30% at the top edge: a painter's vignette, which also
keeps the strip under the desktop bar quiet.

Original art from geometry, procedural shaders and seeded noise. Every colour is a colors.toml value or a mix.
No brush, texture or image is loaded.
"""

import os
import random
import sys
import time
from dataclasses import dataclass, field

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scenes as tk  # noqa: E402
import city  # noqa: E402
import paint as pt  # noqa: E402
from scenes import node, link  # noqa: E402

P = tk.palette()
SAMPLES = 16  # the data renders are flat emission; this only smooths their edges

# ---------- the painter's colours: night is blue, not black ----------

BG, SEL, BLUE = P["background"], P["selection"], P["blue"]
DEEP = tk.mix(BG, SEL, 0.3)              # the deepest large field
SHADE = tk.mix(BG, SEL, 0.14)            # what a surface in shadow is pulled toward
SKY_TOP, SKY_MID, SKY_LOW = tk.mix(BG, SEL, 0.1), tk.mix(BG, SEL, 0.55), tk.mix(SEL, BLUE, 0.4)
TIERS = (tk.mix(BG, SEL, 0.5), tk.mix(BG, SEL, 0.72), tk.mix(SEL, BLUE, 0.14))  # the far city, near to far
HAZE = tk.mix(SEL, BLUE, 0.1)
HAZE_FAR = tk.mix(SEL, BLUE, 0.45)
LINE = tk.mix(BG, SEL, 0.06)
SKYLIGHT = P["blue"]
RAIN = tk.mix(P["foreground"], P["bright_blue"], 0.35)
STEAM = tk.mix(SEL, P["muted"], 0.85)    # what steam lifts the ground's tone toward

# local colours for a scene's surfaces, lifted from near-black to painted blues
BODY = tk.mix(BG, SEL, 0.32)
GLASS = tk.mix(BG, SEL, 0.16)
ROAD = tk.mix(BG, SEL, 0.28)
PAVE = tk.mix(tk.mix(BG, SEL, 0.34), P["muted"], 0.14)
STEEL = tk.mix(tk.mix(BG, SEL, 0.3), P["muted"], 0.22)


@dataclass
class Glow:
    """A group of things that glow, and how they are drawn."""
    where: object                 # where(pic) gives the pixels it covers, as a rule from their world positions
    style: str = "flat"           # 'tube': pale core, coloured line; 'paper': bright centre; 'flat': as it is
    halo: tuple = ()              # soft light round it: (blur in px of the 3440 picture, gain) pairs
    smear: float = 0.0            # how much more than a plain light it reflects in wet ground
    core: float = 6.0             # paper: how far in from the edge the bright centre starts, in px
    colour: str = None            # halo colour, if not its own


@dataclass
class Look:
    """What the painter needs to know about a scene."""
    name: str
    seed: int
    build: object                 # build(rng) makes the scene and its camera, with no air in it
    key_at: tuple                 # where the one key light is
    key_colour: str
    rings: tuple = (6.0, 12.5, 23.0)   # the key's light on surfaces: flat fields out to these distances
    amounts: tuple = (0.4, 0.2, 0.08)
    glows: tuple = ()
    discs: tuple = ()             # painted halos: (place, (radius, radius) in metres, (amount, amount), colour)
    tier_at: tuple = (200.0, 400.0, 600.0)  # where the far city's three steps begin
    veil: tuple = ((80.0, 0.24), (130.0, 0.42))  # haze over the middle distance as flat fields
    wet: object = None            # wet(pic) gives the ground that reflects; flat ground near zero if not given
    flats: tuple = ()             # (low corner, high corner, colour): things kept as one flat dark shape
    tint: float = 0.0             # pull every local colour this far toward the painted blue
    under: object = None          # under(pic, out, rng): drawn things that go under the lines
    over: object = None           # over(pic, out, rng): drawn things that go on top, before the rain
    rain: float = 0.0
    rain_colour: str = RAIN
    stars: bool = True
    sky: tuple = (SKY_TOP, SKY_MID, SKY_LOW)  # top, middle and horizon of the sky's gradient
    far_dim: float = 0.45
    window_lines: float = 0.45
    dress: object = None          # dress(pic, rng): draw on the data before painting: windows, marks
    wobble: float = 0.0           # how far near edges wander from the ruler, in px
    hesitate: bool = False        # lines overshoot or stop short at corners
    cut: float = 1.2              # how soft the edge of the key's light on a surface is, in px
    ring_bands: float = 0.0       # how far wet ground breaks the rings of the key's light into bands
    air: tuple = ()               # the far city sinks into haze toward the ground: (below this height, amount)
    rain_far: float = 0.0         # beyond this distance there is a little less rain; 0 for the same everywhere
    body: tuple = ()              # the key's light in the air: (radius in metres, amount), a wide soft field
    shade_wobble: float = 0.0     # how far the key's cast shadows wander from the ruler, in px
    strokes: float = 0.0          # how far the smears on wet ground break into separate brush strokes
    unshaded: object = None       # unshaded(pic) gives where the key's cast shadow is left out: a mask
    no_ink: object = None         # no_ink(pic) gives how much of the pen line is taken off, 0 to 1 per pixel
    rain_thin: object = None      # rain_thin(pic) gives how much of the rain is taken off, 0 to 1 per pixel
    offset: float = 1000.0        # added to positions so the data render holds no negative numbers
    extra: dict = field(default_factory=dict)


def inbox(pos, lo, hi):
    return ((pos[..., 0] > lo[0]) & (pos[..., 0] < hi[0]) & (pos[..., 1] > lo[1]) & (pos[..., 1] < hi[1])
            & (pos[..., 2] > lo[2]) & (pos[..., 2] < hi[2]))


def within(lo, hi):
    """A Glow's `where`: everything inside a box in the world."""
    return lambda pic: inbox(pic.pos, lo, hi)


def no_air():
    """Volumes are not rendered: mist, haze, cloud and steam are painted instead."""
    for name in ("mist", "haze_layer", "low_cloud", "steam"):
        setattr(city, name, lambda *a, **k: None)


# ---------- the scene and its data renders ----------

def scene(look):
    sc = tk.reset()
    sc.cycles.seed = look.seed
    look.build(random.Random(look.seed))
    sc = bpy.context.scene  # a build may start its own scene
    bpy.context.view_layer.update()
    return sc, sc.camera


def key_lamp(sc, look):
    for ob in [ob for ob in sc.objects if ob.type == "LIGHT"]:
        bpy.data.objects.remove(ob)
    key = tk.light("POINT", look.key_at, 1e6, (1, 1, 1, 1), size=0.0)
    key.data.shadow_soft_size = 0.0  # a drawn shadow has a hard edge
    return key


def base_source(nt):
    p = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if p is None:
        return None, None
    sock = p.inputs["Base Color"]
    return p, (sock.links[0].from_socket if sock.is_linked else tuple(sock.default_value))


def remake(mode):
    """Rewrite every material: 'col' shows only its flat local colour, 'emit' only what glows."""
    for mat in bpy.data.materials:
        nt = mat.node_tree
        if nt is None:
            continue
        out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
        if out is None:
            continue
        if "grime" in nt.nodes:
            nt.nodes.remove(nt.nodes["grime"])
        p, src = base_source(nt)
        glow = [n for n in nt.nodes if n.type == "EMISSION"]
        if mode == "col":
            em = node(nt, "ShaderNodeEmission", Strength=1.0)
            if src is None:
                em.inputs["Strength"].default_value = 0.0
            elif isinstance(src, tuple):
                em.inputs["Color"].default_value = src
            else:
                link(nt, src, em.inputs["Color"])
            link(nt, em.outputs[0], out.inputs["Surface"])
        elif p is None and glow:
            glow[0].inputs["Strength"].default_value = 1.0
        elif glow:
            link(nt, glow[0].outputs[0], out.inputs["Surface"])
        else:
            link(nt, node(nt, "ShaderNodeEmission", Strength=0.0).outputs[0], out.inputs["Surface"])


def override(kind, offset):
    mat = bpy.data.materials.new(kind)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial")
    geo = node(nt, "ShaderNodeNewGeometry")
    if kind == "pos":
        v = city.vec_node(nt, "ADD", geo.outputs["Position"], (offset, offset, offset))
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


def passes(look, folder, percent):
    """Render the data the painter works from. Each is a few seconds: nothing in them is lit but 'lit'."""
    d = {}
    for kind in ("col", "emit", "pos", "nrm", "lit"):
        sc, cam = scene(look)
        sc.render.resolution_x, sc.render.resolution_y = tk.RES
        sc.render.resolution_percentage = percent
        if kind in ("col", "emit"):
            remake(kind)
        else:
            if kind == "lit":
                key_lamp(sc, look)
                tk.set_world((0, 0, 0, 1), 0.0)
            bpy.context.view_layer.material_override = override(kind, look.offset)
        d[kind] = data_render(sc, os.path.join(folder, f"{look.name}-{kind}.exr"),
                              1 if kind in ("pos", "nrm") else SAMPLES, sharp=kind in ("pos", "nrm"))
        m = cam.matrix_world
        d["cam"] = (np.array(m.translation, np.float32), np.array(m.to_3x3(), np.float32), cam.data.lens)
    return d


# ---------- the painter ----------

class Picture:
    """What the data renders say about each pixel, in the terms the painter needs."""

    def __init__(self, d, look):
        self.look = look
        self.eye, self.rot, lens = d["cam"]
        self.solid = d["pos"][..., 3] > 0.5
        self.shape = self.solid.shape
        self.k = self.shape[1] / tk.RES[0]  # sizes in the painter are in pixels of the 3440-wide picture
        self.f = self.shape[1] * lens / 36.0
        pos = d["pos"][..., :3] - look.offset
        rel = pos - self.eye
        self.pos = pos
        fwd = -self.rot[:, 2]
        self.depth = np.where(self.solid, rel @ fwd, 1e5).astype(np.float32)
        self.dist = np.where(self.solid, np.linalg.norm(rel, axis=-1), 1e5).astype(np.float32)
        self.n = d["nrm"][..., :3] * 2 - 1
        # how far off a thing is, for the steps of distance, is measured straight ahead: a wall that faces us is
        # then one step all over, where the distance from the eye would cut a round patch out of it
        self.away = self.depth
        self.far = self.solid & (self.away >= look.tier_at[0])
        flat = np.array((fwd[0], fwd[1], 0.0), np.float32)
        self.horizon = self.at(self.eye + flat / np.linalg.norm(flat) * 1e5)[0]
        lin = d["emit"][..., :3]
        peak = lin.max(-1)
        self.emit = pt.oetf(lin / np.maximum(peak, 1.0)[..., None])  # a strong lamp keeps its colour
        self.glow = pt.step(0.02, 0.1, peak) * d["emit"][..., 3]
        self.col = pt.oetf(d["col"][..., :3])
        if look.tint:
            self.col = pt.mixa(self.col, pt.rgb(BODY), look.tint)
        self.flat = np.zeros(self.shape, bool)
        for lo, hi, colour in look.flats:
            m = self.solid & inbox(pos, lo, hi)
            self.col = np.where(m[..., None], pt.rgb(colour), self.col)
            self.flat |= m
        self.wet = (look.wet(self) if look.wet else
                    self.solid & (self.n[..., 2] > 0.7) & (pos[..., 2] < 0.3)) & ~self.far
        to = np.array(look.key_at, np.float32) - pos
        self.r = np.linalg.norm(to, axis=-1)
        self.ndl = (self.n * to).sum(-1) / np.maximum(self.r, 1e-3)
        self.lit = (d["lit"][..., 0] > 1e-5) & (self.ndl > 0.06) & self.solid & ~self.flat
        self.masks = [self.glow * g.where(self) for g in look.glows]
        self.discs = [self.disc(*spec[:2]) for spec in look.discs]
        self.halo = self.halo_field()

    def at(self, p):
        """Where a place in the world falls in the picture, as (row, column)."""
        rel = (np.array(p, np.float32) - self.eye) @ self.rot
        h, w = self.shape
        return (h / 2 - self.f * rel[1] / -rel[2], w / 2 + self.f * rel[0] / -rel[2])

    def disc(self, place, radii):
        """A painted halo: two flat tones round a lamp, each with a soft edge. Things in front stay clear."""
        row, col = self.at(place)
        reach = float(np.linalg.norm(np.array(place, np.float32) - self.eye))
        yy, xx = np.ogrid[:self.shape[0], :self.shape[1]]
        r = np.hypot(yy - row, xx - col).astype(np.float32) * (reach / self.f)
        behind = self.dist > reach - 0.5
        return [(1 - pt.step(edge * 0.3, edge * 1.1, r)) * behind for edge in radii]

    def halo_field(self):
        k = self.k
        out = np.zeros(self.shape + (3,), np.float32)
        for g, m in zip(self.look.glows, self.masks):
            src = m[..., None] * (pt.rgb(g.colour) if g.colour else self.emit)
            for sigma, gain in g.halo:
                out += pt.blur(src, sigma * k) * gain
        return out

    def body(self):
        """The key's light in the air: one wide field with no edge, brightest at the lamp, reaching further down
        the picture (toward us, along the ground) than up into the sky. Things nearer than the lamp get less."""
        if not self.look.body:
            return np.zeros(self.shape, np.float32)
        radius, amount = self.look.body
        row, col = self.at(self.look.key_at)
        reach = float(np.linalg.norm(np.array(self.look.key_at, np.float32) - self.eye))
        yy, xx = np.ogrid[:self.shape[0], :self.shape[1]]
        dy = (yy - row).astype(np.float32)
        r = np.hypot(np.where(dy > 0, dy * 0.6, dy * 2.2), xx - col) * (reach / self.f) / radius
        return np.exp(-r * r).astype(np.float32) * amount * np.where(self.dist > reach - 0.5, 1.0, 0.55)

    def disc_light(self, body=1.0):
        out = self.body()[..., None] * pt.rgb(self.look.key_colour) * body
        for spec, fields in zip(self.look.discs, self.discs):
            for f, amount in zip(fields, spec[2]):
                out += f[..., None] * pt.rgb(spec[3]) * amount
        return out


def sky(pic, rng):
    """A painter's gradient, darkest at the top, lifting toward the horizon; a few stars as dots."""
    h, w = pic.shape
    hz = pic.horizon / h
    yy, xx = np.linspace(0, 1, h, dtype=np.float32)[:, None], np.linspace(0, 1, w, dtype=np.float32)[None, :]
    t = np.clip(yy / hz + 0.16 * (xx - 0.5), 0, 1)
    t = t * t * (3 - 2 * t)
    top, mid, low = (pt.rgb(c) for c in pic.look.sky)
    lo = np.clip(t * 2, 0, 1)[..., None]
    hi = np.clip(t * 2 - 1, 0, 1)[..., None]
    out = top + (mid - top) * lo + (low - mid) * hi
    if pic.look.stars:
        n = int(260 * pic.k * pic.k)
        y, x = rng.integers(int(160 * pic.k), int(min(hz, 0.95) * h), n), rng.integers(0, w, n)
        dots = np.zeros(pic.shape, np.float32)
        dots[y, x] = rng.uniform(0.25, 0.9, n) ** 2
        dots = np.clip(pt.blur(dots, 0.9 * pic.k) * 7, 0, 1)
        out = pt.mixa(out, pt.rgb(P["bright_blue"]), dots * 0.8)
    return out


def far_city(pic, out, rng):
    """The far city as stepped flat silhouettes: distance is a colour step, not fog. Its lit windows stay as marks."""
    lamb = pic.n @ np.array((-0.5, -0.6, 0.62), np.float32)
    at = pic.look.tier_at
    for k, colour in enumerate(TIERS):
        hi = at[k + 1] if k + 1 < len(TIERS) else 1e6
        m = pic.solid & (pic.away >= at[k]) & (pic.away < hi)
        tone = pt.mixa(np.broadcast_to(pt.rgb(colour), out.shape), pt.rgb(SKYLIGHT), np.where(lamb > 0.4, 0.1, 0.0))
        out = np.where(m[..., None], tone, out)
    if pic.look.air:  # air: the foot of the far city is lost in tinted haze that thickens toward the ground
        far = pic.far.astype(np.float32)
        beyond = pic.far & (pic.away >= at[1])  # only the nearest row keeps crisp stepped tops
        soft = pt.blur(out, 2.2 * pic.k)
        out = np.where(beyond[..., None], soft, out)
        # air is soft: it thickens evenly from one height to the next, and lies a little higher here and lower
        # there in long slow rises. No edge is cut in it; only drawn things have edges.
        lift = 0.5 * (pt.noise(pic.shape, (40 * pic.k, 420 * pic.k), rng) - 0.5)
        z = pic.pos[..., 2] * (1 + lift)
        heights, amounts = zip(*sorted(pic.look.air))
        lowest = heights[0]
        amount = np.interp(z, (lowest * 0.15, lowest * 0.8) + heights[1:] + (heights[-1] * 1.35,),
                           (0.92, amounts[0]) + amounts[1:] + (0.0,)).astype(np.float32)
        out = pt.mixa(out, pt.rgb(HAZE_FAR), pt.blur(amount * far, 1.5 * pic.k) * far)
    return out


def surfaces(pic, rng):
    """Every near surface as flat tones: its local colour, a shadow tone, a sky-lit tone, and where the key
    light falls on it a field of the key's colour in stepped rings with a hard cast shadow."""
    k = pic.k
    look = pic.look
    lamb = pic.n @ np.array((-0.45, -0.55, 0.7), np.float32)
    col = pic.col
    tone = np.where((lamb > 0.5)[..., None], pt.mixa(col, pt.rgb(SKYLIGHT), 0.1),
                    np.where((lamb > -0.05)[..., None], col, pt.mixa(col, pt.rgb(SHADE), 0.55)))
    tone = np.where(pic.flat[..., None], col, tone)
    veil = np.zeros(pic.shape, np.float32)  # haze laid over the middle distance as flat fields by depth band
    for beyond, amount in look.veil:
        veil = np.where(pic.away > beyond, amount, veil)
    tone = pt.mixa(tone, pt.rgb(HAZE), veil * ~pic.flat)
    wobble = 1 + 0.16 * (pt.noise(pic.shape, 150 * k, rng) - 0.5)  # the rings are cut by hand, not by compass
    r = pic.r * wobble
    if look.ring_bands:  # on wet ground the light lies in broken horizontal bands, not a compass curve
        band = pt.noise(pic.shape, (6 * k, 260 * k), rng) - 0.5
        r = np.where(pic.wet, r * (1 + look.ring_bands * band), r)
    lit = pic.lit
    if look.unshaded:  # there the light falls wherever the surface faces it, whatever stands in the way
        lit = lit | (look.unshaded(pic) & (pic.ndl > 0.06) & pic.solid & ~pic.flat)
    if look.shade_wobble:  # a cast shadow's edge is cut by hand too: it wanders, and stays on its own surface
        reach = look.shade_wobble * k * 2
        dy, dx = ((pt.noise(pic.shape, 90 * k, rng) - 0.5) * reach for _ in range(2))
        lit = (pt.warp(lit.astype(np.float32)[..., None], dy, dx)[..., 0] > 0.5) & pic.solid & (pic.ndl > 0.06) \
            & ~pic.flat
    f = np.zeros(pic.shape, np.float32)
    for edge, amount in zip(reversed(look.rings), reversed(look.amounts)):
        f = np.where(lit & (r < edge), amount, f)
    f = pt.blur(f, look.cut * k)
    return pt.mixa(tone, pt.rgb(look.key_colour), f)


def lights(pic, out):
    """Windows and lamps as flat shapes of their own colour; far ones sit back in the haze."""
    dim = np.where(pic.far, pic.look.far_dim, 0.0).astype(np.float32)
    colour = pt.mixa(pic.emit, pt.rgb(TIERS[1]), dim)
    return pt.mixa(out, colour, pic.glow)


def pigment(pic, out, rng, amount=0.1):
    """Uneven pigment in the colour fields: paint is never quite the same strength across a wash."""
    wash = pt.noise(pic.shape, (90 * pic.k, 220 * pic.k), rng) - 0.5
    return out * (1 + amount * wash)[..., None]


def smears(pic, out, rng):
    """Wet ground: each light pulled straight down into a soft smear of its colour, broken by dark bands where
    the puddles end. No mirror image of anything."""
    k = pic.k
    h, w = pic.shape
    hz = pic.horizon
    weight = 1.0 + sum(g.smear * m for g, m in zip(pic.look.glows, pic.masks))
    lightmap = pic.emit * (pic.glow * weight)[..., None] + np.clip(pic.halo + pic.disc_light(), 0, 1) * 0.35
    rows = np.arange(h)
    from_row = np.round(hz - (rows - hz) * 1.7).astype(int)  # squeezed, so tall lights reach the near ground
    ok = (from_row >= 0) & (rows > hz)
    r = np.where(ok[:, None, None], lightmap[np.clip(from_row, 0, h - 1)], 0.0).astype(np.float32)
    r = pt.blur(r, 60 * k, axes=(0,))
    gap = 0.3
    if pic.look.strokes:  # a brush pulls the light down in strokes: each its own width, start, end and strength
        s = pic.look.strokes
        stroke = pt.step(0.36, 0.6, pt.noise(pic.shape, (320 * k, 20 * k), rng)) \
            * (0.55 + 0.45 * pt.noise(pic.shape, (150 * k, 50 * k), rng))
        r = r * (1 - s + s * 1.3 * stroke)[..., None]
        gap = 0.3 * (1 - s)
    r = pt.blur(r, (5.0 if pic.look.strokes else 2.5) * k, axes=(1,))
    bands = gap + (1 - gap) * pt.step(0.38, 0.56, pt.noise(pic.shape, (7 * k, 300 * k), rng))
    local = pt.luma(pic.col)
    puddle = local < pt.blur(local, 40 * k) * 0.93  # the darker patches of the ground are standing water
    wet = bands * np.where(puddle, 1.0, 0.6)
    return pt.screen(out, r * (wet * pic.wet * 2.2)[..., None])


def lines(pic, out, rng, width=1.0):
    """Pen lines on silhouettes and creases, heaviest on the nearest things, gone on the far city."""
    k = pic.k
    reach = pic.look.tier_at[0]
    across, down = pt.edges(1.0 / np.maximum(pic.depth, 0.1), pic.n, pic.solid, parts=True)
    e = pt.hesitate(across, down, k, rng) if pic.look.hesitate else across | down
    if pic.flat.any():  # a flat shape keeps its outline and loses what is inside it
        inside = pic.flat.copy()
        for ax in (0, 1):
            for s in (-2, -1, 1, 2):
                inside &= np.roll(pic.flat, s, ax)
        e &= ~inside
    near = np.minimum(pic.dist, np.minimum(np.roll(pic.dist, 1, 0), np.roll(pic.dist, 1, 1)))
    weight = np.clip((reach + 20 - near) / (reach - 30), 0, 1) ** 0.7
    line = pt.ink(e, weight, k, rng, width)
    if pic.look.window_lines:  # window frames and painted joints: lighter lines where the local colour changes
        g = pt.luma(pic.col)
        ce = (np.abs(g - np.roll(g, 1, 0)) > 0.012) | (np.abs(g - np.roll(g, 1, 1)) > 0.012)
        ce &= pic.solid & ~pic.wet & ~pic.flat
        line = np.maximum(line, pt.ink(ce, np.clip((70 - near) / 50.0, 0, 1), k, rng, width * 0.7)
                          * pic.look.window_lines)
    for g, m in zip(pic.look.glows, pic.masks):
        if g.style != "flat":
            line *= 1 - np.clip(m * 2, 0, 1)
    if pic.look.no_ink:
        line = line * (1 - np.clip(pic.look.no_ink(pic), 0, 1))
    return pt.mixa(out, pt.rgb(LINE), line * 0.9)


def lamps(pic, out):
    """Lamps as drawn: a tube is a near-white core line inside a wider line of its colour; paper has a bright
    centre and keeps its colour at the edge. Then the halos: soft light, and the painted two-tone discs."""
    k = pic.k
    pale = pt.rgb(P["foreground"])
    for g, m in zip(pic.look.glows, pic.masks):
        if g.style == "tube":
            wide = pt.blur(m, 2.2 * k)
            colour = pt.blur(pic.emit * m[..., None], 2.2 * k) / np.maximum(wide, 1e-4)[..., None]
            out = pt.mixa(out, colour, pt.step(0.1, 0.3, wide))
            out = pt.mixa(out, pt.mixa(colour, pale, 0.75), pt.step(0.42, 0.7, pt.blur(m, 1.0 * k)))
        elif g.style == "paper":
            centre = pt.step(0.8, 0.98, pt.blur(m, g.core * k))
            out = pt.mixa(out, pt.mixa(pic.emit, pale, 0.6), centre * m)
    for spec, fields in zip(pic.look.discs, pic.discs):
        for f, amount in zip(fields, spec[2]):
            out = pt.mixa(out, pt.rgb(spec[3]), f * amount)
    out = pt.mixa(out, pt.rgb(pic.look.key_colour), pic.body())
    return pt.screen(out, pic.halo)


def rain(pic, out, rng):
    """Rain as pale streaks of two lengths, one direction, denser near the lights."""
    k = pic.k
    amount = pic.look.rain
    if not amount:
        return out
    halo = np.clip((pic.halo + pic.disc_light(body=0.3)).max(-1), 0, 1)  # the wide body of light adds little rain
    density = 0.04 + 0.96 * np.clip(halo * 2.5, 0, 1)
    n = int(9000 * k * k * amount)
    r = (pt.streaks(pic.shape, density, n, 30 * k, 0.16, rng)
         + pt.streaks(pic.shape, density, n // 2, 64 * k, 0.16, rng))
    r = pt.blur(np.clip(r, 0, 1), 0.5 * k) * (0.2 + 0.6 * halo)
    tubes = sum((m for g, m in zip(pic.look.glows, pic.masks) if g.style == "tube"), np.zeros(pic.shape, np.float32))
    r *= 1 - np.clip(pt.blur(tubes, 22 * k) * 12, 0, 1)  # the streaks stop at a tube and its tight halo
    if pic.look.rain_far:
        r *= np.where(pic.dist > pic.look.rain_far, 0.6, 1.0)
    if pic.look.rain_thin:
        r = r * (1 - np.clip(pic.look.rain_thin(pic), 0, 1))
    return pt.mixa(out, pt.rgb(pic.look.rain_colour), np.clip(r * 1.2, 0, 0.5))


def finish(pic, out, rng, amount=0.014):
    """The vignette at the top, then one even grain."""
    h = pic.shape[0]
    y = np.arange(h, dtype=np.float32)[:, None] / pic.k
    out = out * (0.3 + 0.7 * pt.step(30, 480, y))[..., None]
    return pt.grain(out, amount, rng)


def steam(pic, out, rng, at, size, lit, toward=-1, opacity=0.45, lift=0.45, notch=0.4, trail=0.9, lobes=3):
    """Steam as a veil, for a scene's `over`: a low ragged shape rising at `at` and trailing along the ground away
    from the light, thin enough that what is behind shows through. Its tone is the ground's own, lifted a little;
    only the rim toward the light is bright, in the colour `lit`. `size` is one lobe's half width and its height
    in metres. Things nearer than it stay clear of it. Keep it beside a lamp, never in front of one."""
    k = pic.k
    row, col = pic.at(at)
    reach = float(np.linalg.norm(np.array(at, np.float32) - pic.eye))
    per_m = pic.f / reach
    behind = pic.dist > reach - 0.5
    body, rim, _ = pt.puff(pic.shape, (row, col), size[0] * per_m, size[1] * per_m, rng, lobes=lobes, toward=toward,
                           notch=notch, trail=trail, points=10)
    ground = pt.blur(out, 30 * k)  # the tone of what it lies over
    tone = pt.mixa(ground, pt.rgb(STEAM), lift)
    shape = pt.blur((body > 0).astype(np.float32), 0.8 * k)  # the cut edge stays; only the rim's inner side is soft
    out = pt.mixa(out, tone, pt.blur(body, 0.8 * k) * opacity * behind)
    glow = np.clip(pt.blur(rim, size[0] * per_m * 0.12) * 1.6, 0, 1) * shape
    return pt.mixa(out, pt.rgb(lit), glow * opacity * behind)


def wander(pic, out, rng):
    """Near edges leave the ruler: the picture is pulled a pixel or two this way and that, slowly, and less with
    distance, so a long straight edge has a hand's slight wave in it."""
    k = pic.k
    near = pt.blur(np.clip((150 - pic.dist) / 90, 0, 1), 12 * k) * pic.look.wobble * k * 2
    dy = (pt.noise(pic.shape, 110 * k, rng) - 0.5) * near
    dx = (pt.noise(pic.shape, 110 * k, rng) - 0.5) * near
    return pt.warp(out, dy, dx)


def walls(pic):
    """Upright surfaces, with where each pixel is along its wall and which wall it is."""
    ax, ay = np.abs(pic.n[..., 0]), np.abs(pic.n[..., 1])
    side = ax > ay
    along = np.where(side, pic.pos[..., 1], pic.pos[..., 0])
    plane = np.floor(np.where(side, pic.pos[..., 0], pic.pos[..., 1]) + 0.5).astype(int) * 2 + side
    return pic.solid & (np.abs(pic.n[..., 2]) < 0.3), along, plane


def cells(pic, rng, bay, floor_h, ground, shift=1.0):
    """A wall divided by hand: floors, and bays that start somewhere different on every floor. Gives each
    pixel's place in its bay and floor (0 to 1), its floor number and eight chance numbers for its bay."""
    upright, along, plane = walls(pic)
    table = rng.random((61, 67, 8), dtype=np.float32)
    v = (pic.pos[..., 2] - ground) / floor_h
    j = np.floor(v).astype(int)
    u = along / bay + table[(j + plane * 5) % 61, 0, 6] * shift
    i = np.floor(u).astype(int)
    return upright & (j >= 0), u - i, v - j, i, j, table[(i * 7 + plane * 13) % 61, (j + plane * 3) % 67]


def windows(pic, rng, where, bay=3.3, floor_h=3.3, ground=3.6, part=0.55, warm=0.05, glass=None, edge=None,
            lit=None):
    """Windows on near walls as a painter puts them: not every bay, uneven in size and place, most of them a dark
    rectangle with one light edge, a few lit flat and warm, some of those with a blind half down."""
    ok, fu, fv, i, j, h = cells(pic, rng, bay, floor_h, ground)
    w, t = 0.26 + 0.34 * h[..., 1], 0.3 + 0.3 * h[..., 2]
    du, dv = fu - (0.5 + (h[..., 3] - 0.5) * 0.3), fv - (0.5 + (h[..., 4] - 0.5) * 0.2)
    inside = ok & where & (h[..., 0] < part) & (np.abs(du) < w / 2) & (np.abs(dv) < t / 2)
    on = inside & (h[..., 5] < warm)
    sill = np.where(h[..., 6] < 0.5, dv < -t / 2 + 0.13 / floor_h, du < -w / 2 + 0.13 / bay)
    pic.col = np.where(inside[..., None], pt.rgb(glass), pic.col)
    pic.col = np.where((inside & sill & ~on)[..., None], pt.rgb(edge), pic.col)
    blind = on & (h[..., 7] < 0.45) & (dv > -t * (h[..., 7] - 0.1))
    pic.emit = np.where(on[..., None], pt.rgb(lit), pic.emit)
    pic.emit = np.where(blind[..., None], pt.mixa(pt.rgb(lit), pt.rgb(glass), 0.45), pic.emit)
    pic.glow = np.where(on, 1.0, pic.glow).astype(np.float32)
    return inside


def marks(pic, rng, where, bay=7.0, floor_h=4.2, ground=8.0, part=0.3, warm=0.14, cool=None, lit=None):
    """Windows on far towers: small uneven dashes in loose clusters, most of them dim blue, a few warm."""
    ok, fu, fv, i, j, h = cells(pic, rng, bay, floor_h, ground)
    group = rng.random((23, 29), dtype=np.float32)[(i // 3) % 23, (j // 4) % 29]
    w, t = 0.2 + 0.5 * h[..., 1], 0.16 + 0.2 * h[..., 2]
    du, dv = fu - (0.5 + (h[..., 3] - 0.5) * 0.3), fv - (0.5 + (h[..., 4] - 0.5) * 0.4)
    inside = ok & where & (h[..., 0] < part * 2 * group) & (np.abs(du) < w / 2) & (np.abs(dv) < t / 2)
    on = h[..., 5] < warm
    pic.emit = np.where(inside[..., None], np.where(on[..., None], pt.rgb(lit), pt.rgb(cool)), pic.emit)
    pic.glow = np.where(inside, np.where(on, 1.0, 0.3 + 0.5 * h[..., 7]), pic.glow).astype(np.float32)
    return inside


def paint(d, look):
    rng = np.random.default_rng(look.seed)
    pic = Picture(d, look)
    if look.dress:
        look.dress(pic, np.random.default_rng(look.seed + 100))
    out = sky(pic, rng)
    out = np.where(pic.solid[..., None], surfaces(pic, rng), out)
    out = far_city(pic, out, np.random.default_rng(look.seed + 300))
    out = lights(pic, out)
    out = pigment(pic, out, rng)
    if look.under:
        out = look.under(pic, out, rng)
    out = smears(pic, out, rng)
    out = lines(pic, out, rng)
    out = lamps(pic, out)
    if look.wobble:
        out = wander(pic, out, np.random.default_rng(look.seed + 200))
    if look.over:
        out = look.over(pic, out, rng)
    out = rain(pic, out, rng)
    return finish(pic, out, rng), pic


def run(look, out_dir, percent=100, name=None):
    """Render the data, paint the picture, write it, and print its figures."""
    data = os.path.join(out_dir, "data")
    os.makedirs(data, exist_ok=True)
    t0 = time.time()
    d = passes(look, data, percent)
    t1 = time.time()
    out, pic = paint(d, look)
    path = os.path.join(out_dir, f"{name or look.name}.png")
    pt.save(path, out)
    grey = pt.luma(np.clip(out, 0, 1)) * 255
    print(f"{look.name}: seed {look.seed}, render {t1 - t0:.1f} s, paint {time.time() - t1:.1f} s, "
          f"mean {grey.mean():.1f}, top strip {grey[:int(150 * pic.k)].mean():.1f}", flush=True)
    return path
