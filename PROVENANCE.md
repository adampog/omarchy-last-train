# Provenance

Every image in this theme is original art made by the code in `tools/`. Nothing is photographed, downloaded,
traced from another work or made by an image-generation model. No third-party textures, environment maps or
3D models are used. Each image can be rendered again from its script with the seed and sample count below.

## Assets

| Asset | Made by | Seed | Samples | Origin |
|---|---|---|---|---|
| `colors.toml`, `neovim.lua`, `btop.theme`, `chromium.theme`, `icons.theme` | written by hand | | | the theme palette and configuration |
| `backgrounds/06-neo-tokyo-omarchy-skyline.png` | `tools/bg6_wordmark.py` | 1 | 64 | original code-made art: the Omarchy wordmark extruded, over a city of procedural boxes |
| `backgrounds/a-rain-gate.png` | `tools/bg_a_rain_gate.py` | 7 | 160 | original code-made art: a wet street of procedural boxes under a sign stack of plain frames, bars and a ring, with no lettering |
| scenes B and C at full size, in progress (no image committed yet) | `tools/bg_b_moored_lantern.py`, `tools/bg_c_riders_stop.py` | 11, 12 | 160 | original code-made art: the lantern sphere in low cloud on its roof, and the parked trail bike of tubes and boxes on an elevated road |
| roughs of scenes B to G (860x360, not shipped, written to `.cache/roughs/`) | `tools/roughs.py` | 11 to 16 | 64 | original code-made art: a lantern sphere on a roof, a parked trail bike of boxes and tubes, a mast and tank, a box-car train on a viaduct, a tunnel mouth, an alley counter |
| the rough sheet (not shipped) | `tools/rough_sheet.sh` | | | the images above as labelled tiles |
| animated-look tests of scene A, three treatments (not shipped; the scripts as tested are at commit 0585ba5) | `tools/anime_a.py` with `tools/paint.py` | 7 | 16 (data renders), 128 (the dropped cel render) | original code-made art: the same street, sign and camera as `a-rain-gate`; the second treatment was chosen and is the technique below |
| animated roughs of scenes A to G and of background 06 (not shipped, written to `.cache/anime/`) | `tools/anime.py` (the painter) with `tools/paint.py`; `tools/anime_a.py` for A, `tools/anime_roughs.py` for B to G and 06 | A 7, B to G 11 to 16, 06 1 | 16 (data renders) | original code-made art: the committed scenes and cameras, rendered as flat data and painted in numpy from seeded noise; no brush, texture or image is loaded |
| scene C, Rider's stop, painted full size (candidate, not yet shipped, written to `.cache/anime/c.png`) | `tools/anime_c.py` with `tools/bg_c_riders_stop.py` and the painter `tools/anime.py` | 12 | 16 (data renders) | original code-made art: a trail bike on a wet elevated road with a sign tower, drawn windows and thin cloud painted in numpy; no image, brush or font is loaded |
| the animated rough sheet (not shipped) | `tools/anime_sheet.sh` | | | the images above as labelled tiles |

## Technique

The backgrounds are painted, not rendered as pictures. Blender renders each scene five times as plain data
(local colour, emission, position, surface direction and a hard shadow mask from the one key light), and
`tools/anime.py` paints the picture from that data in numpy: a gradient sky, stepped far-city silhouettes, one
flat local colour and one flat shadow tone per surface, windows drawn unevenly on the walls, pen lines on edges
that wander a pixel or two and hesitate at corners, cast shadows with a hand-cut edge, drawn lamps and halos
with a wide soft body of light in the air round the key lamp, a far city that sinks into banded haze, smears on
wet ground, steam as a low wide cut shape, rain streaks, uneven pigment in the colour fields, a darker top edge
and one even grain. All of it comes
from seeded noise and the colours in `colors.toml`.

Each new image gets a row here in the commit that adds it. Final file names are given when the set is chosen.

## Colours

The palette is the theme palette in `colors.toml`. The scripts read their colours from that file and mix them in
code. They contain no colour values of their own.

## The Omarchy wordmark

`tools/bg6_wordmark.py` reads `/usr/share/omarchy/logo.svg` from the installed Omarchy at render time. That file
and `colors.toml` are the only files it reads. The wordmark is Omarchy's own mark, not ours. It is used unaltered,
as Omarchy's stock themes use it, and no copy of the SVG is kept in this repository.

## Tools

| Tool | Used for | Licence |
|---|---|---|
| Blender, as the `bpy` 5.2.2 Python module, with Cycles | modelling and rendering the scenes | GPL-3.0-or-later |
| Python 3.13 | running the scripts | PSF-2.0 |
| uv | installing the pinned packages | MIT or Apache-2.0 |
| ImageMagick | resizing, previews and checks | ImageMagick License |

The scripts are this repository's own code under its MIT licence, including the shared helpers in
`tools/scenes.py` and the city kit in `tools/city.py` (building faces, wet road, tubes, mist, haze, low cloud, steam), which
load no images. `pyproject.toml` and `uv.lock` pin the Python packages; `bpy` brings
numpy, requests, cattrs, cython and zstandard with it, each under its own open licence. Blender's licence covers
the program, not the images made with it.

## Fonts

The only lettering in any background is the Omarchy wordmark in background 06, drawn from
`/usr/share/omarchy/logo.svg`, which is Omarchy's own mark. No background uses a font. Any font added later must
be openly licensed and is listed here with its licence.

| Font | Used for | Path | Licence |
|---|---|---|---|
| Liberation Sans Regular | tile labels on the rough sheet only, which is not shipped | `/usr/share/fonts/liberation/LiberationSans-Regular.ttf` | SIL OFL 1.1, `/usr/share/licenses/ttf-liberation/LICENSE` |
