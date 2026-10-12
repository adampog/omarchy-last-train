# Provenance

Every image in this theme is original art made by the code in `tools/`. Nothing is photographed, downloaded,
traced from another work or made by an image-generation model. No third-party textures, environment maps or
3D models are used. Each image can be rendered again from its script with the seed and sample count below.

## Assets

| Asset | Made by | Seed | Samples | Origin |
|---|---|---|---|---|
| `colors.toml`, `neovim.lua`, `btop.theme`, `chromium.theme`, `icons.theme` | written by hand | | | the theme palette and configuration |
| `backgrounds/06-neo-tokyo-omarchy-skyline.png` | `tools/bg6_wordmark.py` | 1 | 64 | original code-made art: the Omarchy wordmark extruded, over a city of procedural boxes |

Each new image gets a row here in the commit that adds it.

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
| ImageMagick | resizing, previews and checks | ImageMagick License |

The scripts are this repository's own code under its MIT licence. They also use a small shared helper module of
the author's own (`_toolkit/scenes.py`, beside this repository), which loads no images. Blender's licence covers the program, not the
images made with it.

## Fonts

None yet. Any font added later must be openly licensed and is listed here with its licence.
