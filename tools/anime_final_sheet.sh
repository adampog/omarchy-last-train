#!/usr/bin/env bash
# The final sheet of the Last Train theme for review: the eight painted backgrounds at full size as labelled tiles 860 wide on one sheet.
#   tools/anime_final_sheet.sh <src-dir> <sheet.png>
# <src-dir> holds a.png to g.png and 06.png at 3440x1440, each painted by its own script:
#   uv run tools/anime_<a to g>.py   and   uv run tools/anime_roughs.py --scene 06 --percent 100
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
src="${1:?src dir}"
sheet="${2:?sheet file}"
tmp="$(mktemp -d)"
font=/usr/share/fonts/liberation/LiberationSans-Regular.ttf
ink="$(grep '^foreground' "$repo/colors.toml" | cut -d'"' -f2)"
paper="$(grep '^background' "$repo/colors.toml" | cut -d'"' -f2)"

tile() {  # tile <image> <label> <order>
  magick "$src/$1" -alpha off -resize 860x360! -font "$font" -pointsize 20 -fill "$ink" -undercolor "$paper" \
    -gravity SouthWest -annotate +10+8 " $2 " "$tmp/$3.png"
}
tile a.png "A  Rain gate" 1
tile b.png "B  Moored lantern" 2
tile c.png "C  Rider's stop" 3
tile d.png "D  Signal roof" 4
tile e.png "E  Last train" 5
tile f.png "F  Tunnel mouth" 6
tile g.png "G  The counter" 7
tile 06.png "06  Omarchy over the city" 8
magick montage "$tmp"/[1-8].png -tile 2x4 -geometry +6+6 -background "$paper" -font "$font" -pointsize 30 \
  -fill "$ink" -title "Last Train" "$sheet"
rm -r "$tmp"
echo "wrote $sheet"
