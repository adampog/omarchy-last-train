# Last Train

A cyberpunk megacity theme for [Omarchy](https://omarchy.org): red and orange neon on blue-black.

## What's inside

| File | What it does |
|---|---|
| `colors.toml` | The palette. Omarchy generates terminal, Waybar, Hyprland, VS Code and the rest from it |
| `neovim.lua`, `btop.theme`, `chromium.theme` | The same palette for Neovim, btop and Chromium |
| `icons.theme` | Yaru-red icons, to match the red accent |
| `backgrounds/` | Eight wallpapers at 3440×1440, all original art made by the scripts in `tools/` |
| `preview.png`, `unlock.png`, `preview-unlock.png` | The theme picker preview and the lock-screen images |

## Install

Omarchy takes a theme's name from its folder name, so the folder must be named `last-train`; it then shows
as "Last Train". Copy or clone this repository to that folder:

```bash
git clone <this repository> ~/.config/omarchy/themes/last-train
omarchy theme set "Last Train"
```

`omarchy theme install <git-url>` also works. It names the folder after the repository, with a leading
`omarchy-` and a trailing `-theme` removed, so the repository has to be named `last-train`,
`omarchy-last-train-theme` or the like.

## Palette

| | |
|---|---|
| Background | `#0a0a0f` |
| Foreground | `#f2ece4` |
| Accent, red | `#ff3b30` |
| Orange | `#fa9d5a` |
| Yellow | `#fcb362` |
| Blue | `#4d8fe6` |
| Selection | `#1c3f8f` |
| Cyan | `#6cc7e6` |
| Green | `#5fd38a` |
| Magenta | `#ff6ea0` |

## The art

Every image is original and made by code in this repository. No photographs, downloaded textures or models, and
no image-generation models are used. [PROVENANCE.md](PROVENANCE.md) lists each asset, the script that makes it,
and the tools and their licences.

## Rebuilding the art

The scripts need [uv](https://docs.astral.sh/uv/), an NVIDIA GPU with OptiX, and an installed Omarchy (background
08 and the unlock images read `/usr/share/omarchy/logo.svg`). `pyproject.toml` and `uv.lock` pin Blender's `bpy`
module at 5.2.2 on Python 3.13. The preview images also need `rsvg-convert`, ImageMagick and the JetBrainsMono
Nerd Font.

```bash
uv sync
tools/make_backgrounds.sh .cache/regen   # the eight backgrounds, under their shipped names
python3 tools/build_preview.py --out .cache/regen   # preview.png, unlock.png, preview-unlock.png
```

Leave out the folder to write into `backgrounds/` and the repository root. Each scene's own script
(`tools/anime_a.py` to `anime_g.py`, and `tools/anime_roughs.py --scene 06` for background 08) makes one
picture; PROVENANCE.md says which command makes which file. Seeds are fixed and sampling is at the script
defaults, so a re-render matches the shipped image apart from a few pixels of GPU sampling noise.

## Licence

MIT, see [LICENSE](LICENSE). The Omarchy wordmark is Omarchy's own mark and is not covered by this licence.
