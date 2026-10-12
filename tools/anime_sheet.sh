#!/usr/bin/env bash
# The animated rough sheet for review: scenes A to G and background 06 through the painter, as labelled tiles
# 860 wide on one sheet, plus each picture at 1720 wide.
#   tools/anime_sheet.sh <out-dir>
# after:  uv run tools/anime_a.py --percent 50   and   uv run tools/anime_roughs.py --scene all
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
out="${1:?out dir}"
src="${2:-$repo/.cache/anime}"
tmp="$(mktemp -d)"
font=/usr/share/fonts/liberation/LiberationSans-Regular.ttf
ink="$(grep '^foreground' "$repo/colors.toml" | cut -d'"' -f2)"
paper="$(grep '^background' "$repo/colors.toml" | cut -d'"' -f2)"

tile() {  # tile <image> <label> <order> <name>
  magick "$src/$1" -alpha off -resize 1720x "$out/$4-1720.png"
  magick "$src/$1" -alpha off -resize 860x360! -font "$font" -pointsize 20 -fill "$ink" -undercolor "$paper" \
    -gravity SouthWest -annotate +10+8 " $2 " "$tmp/$3.png"
}
tile a.png "A  Rain gate" 1 A
tile rough-b.png "B  Moored lantern" 2 B
tile rough-c.png "C  Rider's stop" 3 C
tile rough-d.png "D  Signal roof" 4 D
tile rough-e.png "E  Last train" 5 E
tile rough-f.png "F  Tunnel mouth" 6 F
tile rough-g.png "G  The counter" 7 G
tile rough-06.png "06  Omarchy over the city, restyled" 8 06-restyled
magick montage "$tmp"/[1-8].png -tile 2x4 -geometry +6+6 -background "$paper" "$out/anime-rough-sheet.png"
rm -r "$tmp"
echo "wrote $out"
