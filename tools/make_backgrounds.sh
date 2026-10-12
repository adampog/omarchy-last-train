#!/usr/bin/env bash
# Renders the eight Last Train backgrounds at full size and default samples, under their shipped names.
#   tools/make_backgrounds.sh [dest-dir]        # default: backgrounds/
# Each scene is painted by its own script (see PROVENANCE.md). Needs uv, an NVIDIA GPU with OptiX and an
# installed Omarchy (background 08 reads /usr/share/omarchy/logo.svg). GPU renders differ from the shipped
# files by a few pixels of sampling noise, so give it another dest-dir to compare rather than overwrite.
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo"
dest="${1:-backgrounds}"
work="$(mktemp -d "${TMPDIR:-/tmp}/last-train.XXXXXX")"
mkdir -p "$dest"
one() {  # one <painted name> <shipped name> <command...>
  local from="$1" to="$2"; shift 2
  "$@" --out "$work" >/dev/null
  cp "$work/$from.png" "$dest/$to.png"
  echo "wrote $dest/$to.png"
}
one a last-train-01-rain-gate uv run tools/anime_a.py
one b last-train-02-moored-lantern uv run tools/anime_b.py
one c last-train-03-riders-stop uv run tools/anime_c.py
one d last-train-04-signal-roof uv run tools/anime_d.py
one e last-train-05-last-train uv run tools/anime_e.py
one f last-train-06-tunnel-mouth uv run tools/anime_f.py
one g last-train-07-the-counter uv run tools/anime_g.py
one rough-06 last-train-08-omarchy-over-the-city uv run tools/anime_roughs.py --scene 06 --percent 100
rm -r "$work"
