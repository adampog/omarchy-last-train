# Provenance

Every image in this theme is original art made by the code in `tools/`. Nothing is photographed, downloaded,
traced from another work or made by an image-generation model. No third-party textures, environment maps or
3D models are used. Each image can be rendered again from its script with the seed and sample count below.

## Assets

Every shipped file, with the command that makes it. Samples: each painted scene is rendered as five data passes
at the script default of 16 samples (the painting itself is numpy, not sampled). All eight backgrounds are
3440x1440 and original code-made art. `tools/make_backgrounds.sh` runs the eight commands in order and writes
the shipped names; `python3 tools/build_preview.py` makes the three preview and unlock images.

| Asset | Command | Scene commit | Seed | Samples | sha256 | Origin |
|---|---|---|---|---|---|---|
| `backgrounds/last-train-01-rain-gate.png` | `uv run tools/anime_a.py` | 41934d7 | 7 | 16 | 59b0cba4a6b41ee625507144a853030bf4b6d77a3fb4bd262869209481304b4b | original code-made art: a wet street under a sign stack of plain frames, bars and a ring, no lettering |
| `backgrounds/last-train-02-moored-lantern.png` | `uv run tools/anime_b.py` | 4dcfabc | 11 | 16 | a7513411c364f089375fba094baffb2bf1f03b9123d140816552c20c2ddc2ee0 | original code-made art: a paper lantern moored to a wet roof, low cloud among far towers |
| `backgrounds/last-train-03-riders-stop.png` | `uv run tools/anime_c.py` | b5eab30 | 12 | 16 | ec13eaa486c75ec4962597b3e65cf7ed33686f32169b80dd336d654bd82e431a | original code-made art: a trail bike of tubes and boxes on a wet elevated road, sign tower, thin cloud |
| `backgrounds/last-train-04-signal-roof.png` | `uv run tools/anime_d.py` | e332627 | 13 | 16 | c873b7972cca37a70bf2688ed44dc646d2821e9b0ffd71e8c4374770053c8328 | original code-made art: a roof with a red beacon mast, a tank, two dishes and layered far city |
| `backgrounds/last-train-05-last-train.png` | `uv run tools/anime_e.py` | 67003e3 | 14 | 16 | 61b742c91a5e6a6fbcb6c618115a338060a0b177ccc742178daab7178f87718b | original code-made art: a three-car train on a viaduct over a canal, broken reflection bands |
| `backgrounds/last-train-06-tunnel-mouth.png` | `uv run tools/anime_f.py` | 90de698 | 15 | 16 | 5904a5899275ba4d7ad9053edb6fbbb2436dccf145fc85f03a2ce7846c177d58 | original code-made art: a wet road bending into a lit tunnel under a stepped retaining wall |
| `backgrounds/last-train-07-the-counter.png` | `uv run tools/anime_g.py` | 16c7dcf | 16 | 16 | 0d141dfe2ba942472bf88d05a87491a8ced82a3c0be2930adf9c8cc249f62514 | original code-made art: a night food stall in a wet alley, flat warm wall tone, kettle steam |
| `backgrounds/last-train-08-omarchy-over-the-city.png` | `uv run tools/anime_roughs.py --scene 06 --percent 100` | d9fa22e, word placed 2026-10-13 | 1 | 16 | e8e1be7d92efaf093df8a15e9ed20d338bd75f73874610fea19cc49435e087c6 | original code-made art: the Omarchy wordmark extruded over a city, painted in the same style (the mark itself is Omarchy's) |
| `unlock.png` | `python3 tools/build_preview.py` | | | | 8fe93fd7cfb86b3e24ccb856bec9a8540892c42e270a76dc4ff9868ca2be9651 | the Omarchy wordmark in the accent colour, drawn from Omarchy's logo.svg |
| `preview-unlock.png` | `python3 tools/build_preview.py` | | | | dcc6800174453b044d846f9a5e61b9faf21a8ebe1651813c28597ff2a0f917dc | the unlock image over the background colour with a padlock and a field, drawn as vector shapes |
| `preview.png` | `python3 tools/build_preview.py` | | | | ccad1edf9561c6e719a9b93bb4ed22e281d96e3d85738d6670604c146400276f | the palette as an editor and a terminal, with background 05 in the art panel |
| `colors.toml`, `neovim.lua`, `btop.theme`, `chromium.theme`, `icons.theme` | written by hand | | | | | the theme palette and configuration |

All eight backgrounds are painted by `tools/anime.py` (painter commit 4dcfabc) with `tools/paint.py`, from the
geometry in the matching `tools/bg_*.py` (scene 08 from `tools/bg6_wordmark.py`, through `tools/anime_roughs.py`).
The approved files are frozen: a fresh render matches them to within a few pixels of GPU sampling noise, not
byte for byte (see the README). Scenes that were tried and dropped, rough sheets and review folders are
development material in `.cache/` and are not shipped.

## Technique

The backgrounds are painted, not rendered as pictures. Blender renders each scene five times as plain data
(local colour, emission, position, surface direction and a hard shadow mask from the one key light), and
`tools/anime.py` paints the picture from that data in numpy: a gradient sky, stepped far-city silhouettes, one
flat local colour and one flat shadow tone per surface, windows drawn unevenly on the walls, pen lines on edges
that wander a pixel or two and hesitate at corners, cast shadows with a hand-cut edge, drawn lamps and halos
with a wide soft body of light in the air round the key lamp, a far city that sinks into banded haze, smears on
wet ground, steam as a thin low veil with a ragged cut edge that the street shows through, rain streaks, uneven pigment in the colour fields, a darker top edge
and one even grain. All of it comes
from seeded noise and the colours in `colors.toml`.

## Regeneration check

On 2026-10-13, `tools/make_backgrounds.sh <scratch dir>` rendered all eight backgrounds again at the script
default samples (2 min 36 s on one RTX 3090 Ti), and `python3 tools/build_preview.py --out <scratch dir>` made
the three preview and unlock images again. Each file was compared with the shipped file by ImageMagick
`compare` (AE = pixels that differ; PSNR 120 is the value it prints for identical images) and by `cmp`:

| File | AE | PSNR | Bytes |
|---|---|---|---|
| `backgrounds/last-train-01-rain-gate.png` | 0 | 120 | identical |
| `backgrounds/last-train-02-moored-lantern.png` | 0 | 120 | identical |
| `backgrounds/last-train-03-riders-stop.png` | 0 | 120 | identical |
| `backgrounds/last-train-04-signal-roof.png` | 0 | 120 | identical |
| `backgrounds/last-train-05-last-train.png` | 0 | 120 | identical |
| `backgrounds/last-train-06-tunnel-mouth.png` | 0 | 120 | identical |
| `backgrounds/last-train-07-the-counter.png` | 0 | 120 | identical |
| `backgrounds/last-train-08-omarchy-over-the-city.png` | 0 | 120 | identical |
| `preview.png` | 0 | | identical |
| `unlock.png` | 0 | | identical |
| `preview-unlock.png` | 0 | | identical |

dev-qa made an independent run on 2026-10-13 from a fresh clone at 592f380 on the same machine
(`tools/make_backgrounds.sh` took 2 min 34.7 s). Ten of the eleven files were byte-identical. In
`backgrounds/last-train-03-riders-stop.png`, 2 pixels differed (at 579,1229 and 2122,1317), each by 1 of 255:
AE 2 channel values, PSNR 116.84, and the file was 7 bytes smaller. The other seven backgrounds and the three
preview and unlock images were identical (AE 0). The figures are in the mission's `slices/02-build/QA-EVIDENCE.md`.

Background 08 was placed again after both of those runs, on 2026-10-13: its wordmark was cut at the right edge
of a centred 16:9 crop (x 440 to 3000 of 3440), so the word was moved 130 px left and made 9 % smaller in
`tools/bg6_wordmark.py` (`WORD_PX` 1900 to 1770, `WORD_W_PX` 2200 to 2000). It now spans x 761 to 2793, whole
inside the crop, and every pixel outside the word's box equals the earlier file. The new file was rendered
twice with `uv run tools/anime_roughs.py --scene 06 --percent 100`; both runs were byte-identical (AE 0), and
the shipped 08 is those bytes. The two runs above compared the earlier 08 (sha256 9741d1d8...); the other ten
files are unchanged since.

So GPU renders can differ by a few pixels of sampling noise from run to run, even on one machine. The shipped
files are the frozen bytes; a fresh render is a check, not a replacement.

## Contrast

`omarchy dev theme preview . --no-osc` on 2026-10-12 (it prints and applies nothing): mode dark, foreground
`#f2ece4` on background `#0a0a0f` is 16.83:1 (target 4.5). Every text colour on the background, from
`tools/build_preview.py`, which refuses a palette below target: red and accent 5.57, green 10.51, yellow 11.06,
blue 6.01, magenta 7.51, cyan 10.30, muted 5.70, bright_red 7.07, bright_green 13.77, bright_yellow 13.77,
bright_blue 9.25, bright_magenta 10.02, bright_cyan 13.07, light_foreground 13.14, bright_foreground 16.83,
dark_foreground 9.47, orange 9.44, brown 5.86 (target 3.0 each; lowest 5.57).

## Colours

The palette is the theme palette in `colors.toml`. The scripts read their colours from that file and mix them in
code. They contain no colour values of their own.

## The Omarchy wordmark

`tools/bg6_wordmark.py` (background 08) and `tools/build_preview.py` (`unlock.png`, `preview-unlock.png`) read
`/usr/share/omarchy/logo.svg` from the installed Omarchy at render time. That file and `colors.toml` are the only
files they read. The wordmark is Omarchy's own mark, not ours. It is used unaltered,
as Omarchy's stock themes use it, and no copy of the SVG is kept in this repository.

## Tools

| Tool | Used for | Licence |
|---|---|---|
| Blender, as the `bpy` 5.2.2 Python module, with Cycles | modelling and rendering the scenes | GPL-3.0-or-later |
| Python 3.13 | running the scripts | PSF-2.0 |
| uv | installing the pinned packages | MIT or Apache-2.0 |
| ImageMagick | resizing, previews and checks | ImageMagick License |
| rsvg-convert (librsvg) | turning the preview SVGs into PNGs | LGPL-2.1-or-later |

The scripts are this repository's own code under its MIT licence, including the shared helpers in
`tools/scenes.py` and the city kit in `tools/city.py` (building faces, wet road, tubes, mist, haze, low cloud, steam), which
load no images. `pyproject.toml` and `uv.lock` pin the Python packages; `bpy` brings
numpy, requests, cattrs, cython and zstandard with it, each under its own open licence. Blender's licence covers
the program, not the images made with it.

## Fonts

The only lettering in any background is the Omarchy wordmark in background 08, drawn from
`/usr/share/omarchy/logo.svg`, which is Omarchy's own mark. No background uses a font. Any font added later must
be openly licensed and is listed here with its licence.

| Font | Used for | Path | Licence |
|---|---|---|---|
| JetBrainsMono Nerd Font | the code and palette text inside `preview.png`, drawn into the image; the font itself is not shipped | `/usr/share/fonts/TTF/JetBrainsMonoNerdFont-*.ttf` (package ttf-jetbrains-mono-nerd-basic 3.5.1) | SIL OFL 1.1 (JetBrains Mono); the Nerd Fonts patching is MIT |
| Liberation Sans Regular | tile labels and the title on the review sheets only, which are not shipped | `/usr/share/fonts/liberation/LiberationSans-Regular.ttf` | SIL OFL 1.1, `/usr/share/licenses/ttf-liberation/LICENSE` |
