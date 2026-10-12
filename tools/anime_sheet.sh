#!/usr/bin/env bash
# The animated-look tests of scene A for review: each treatment at full size, at 1720 wide and as the centred
# 16:9 crop, a labelled sheet beside the round 1 render, and 1:1 crops of the sign, the wet road and a far tower.
#   tools/anime_sheet.sh <out-dir>      (after: uv run tools/anime_a.py --treatment t1, then t2, then t3)
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
tile "$repo/backgrounds/a-rain-gate.png" "A, round 1: the path-traced render, for comparison" 1
tile "$repo/.cache/anime/a-t1.png" "T1  cel in the renderer: Toon, Freestyle, value steps" 2
tile "$repo/.cache/anime/a-t2.png" "T2  data renders, then painted in numpy" 3
tile "$repo/.cache/anime/a-t3.png" "T3  T2 toward gouache: stepped halos, brush filter" 4
magick montage "$tmp"/[1-4].png -tile 2x2 -geometry +6+6 -background "$paper" "$out/anime-sheet.png"
for t in t1 t2 t3; do
  src="$repo/.cache/anime/a-$t.png"
  magick "$src" -alpha off "$out/A-$t-3440x1440.png"
  magick "$src" -resize 1720x -quality 93 "$out/A-$t-1720.jpg"
  magick "$src" -crop 2560x1440+440+0 +repage -resize 1280x -quality 93 "$out/A-$t-crop-440-3000-at-1280.jpg"
  magick "$src" -crop 900x700+900+250 +repage "$out/A-$t-1to1-sign.png"
  magick "$src" -crop 900x600+1500+840 +repage "$out/A-$t-1to1-wet-road.png"
  magick "$src" -crop 800x560+1560+130 +repage "$out/A-$t-1to1-far-tower.png"
done
rm -r "$tmp"
echo "wrote $out"
