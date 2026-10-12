#!/usr/bin/env bash
# The rough sheet: scene A, the roughs B to G and background 06 as labelled 860x360 tiles, two across.
#   tools/rough_sheet.sh <out-dir>      (after: uv run tools/bg_a_rain_gate.py && uv run tools/roughs.py)
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
out="${1:?out dir}"
tmp="$(mktemp -d)"
font=/usr/share/fonts/liberation/LiberationSans-Regular.ttf
ink="$(grep '^foreground' "$repo/colors.toml" | cut -d'"' -f2)"
paper="$(grep '^background' "$repo/colors.toml" | cut -d'"' -f2)"

tile() {  # tile <image> <label> <name>
  magick "$1" -resize 860x360! -font "$font" -pointsize 20 -fill "$ink" -undercolor "$paper" \
    -gravity SouthWest -annotate +10+8 " $2 " "$tmp/$3.png"
}
tile "$repo/backgrounds/a-rain-gate.png" "A  Rain gate (full build, shown at quarter size)" 1
tile "$repo/.cache/roughs/rough-b.png" "B  Moored lantern (rough)" 2
tile "$repo/.cache/roughs/rough-c.png" "C  Rider's stop (rough)" 3
tile "$repo/.cache/roughs/rough-d.png" "D  Signal roof (rough, reserve)" 4
tile "$repo/.cache/roughs/rough-e.png" "E  Last train (rough)" 5
tile "$repo/.cache/roughs/rough-f.png" "F  Tunnel mouth (rough, reserve)" 6
tile "$repo/.cache/roughs/rough-g.png" "G  The counter (rough, reserve)" 7
tile "$repo/backgrounds/06-last-train-omarchy-skyline.png" "06  carried over, re-tinted to the theme palette" 8
magick montage "$tmp"/[1-8].png -tile 2x4 -geometry +6+6 -background "$paper" "$out/rough-sheet.png"
rm -r "$tmp"
echo "wrote $out/rough-sheet.png"
