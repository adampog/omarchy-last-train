#!/usr/bin/env python3
"""Builds Last Train's unlock.png, preview-unlock.png and preview.png from colors.toml and one background.

    python3 tools/build_preview.py [--out DIR] [--hero FILE] [--align left|centre|right]

Vendored from the shared Omarchy theme toolkit's build.py (written for this project, MIT like the rest of the
repository) and cut down to the three images. unlock.png is Omarchy's own OMARCHY wordmark, read from the
installed Omarchy's logo.svg, in the accent colour. preview.png shows the hero background in its art panel
beside a code sample and the palette. Needs python3 (stdlib), rsvg-convert, ImageMagick, the JetBrainsMono
Nerd Font and an installed Omarchy. Refuses a palette that fails the contrast targets.
"""

import argparse
import base64
import os
import re
import subprocess
import sys
import tempfile
import tomllib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONO = "JetBrainsMono Nerd Font"
LOGO = "/usr/share/omarchy/logo.svg"
HERO = "backgrounds/last-train-05-last-train.png"


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def hexc(c):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in c)


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return hexc(tuple(x + (y - x) * t for x, y in zip(a, b)))


def luminance(h):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(h)
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n{body}\n</svg>\n')


def wordmark(cx, cy, width, fill):
    """Omarchy's own pixel OMARCHY wordmark (logo.svg), recoloured and centred on (cx, cy)."""
    with open(LOGO) as fh:
        logo = fh.read()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', logo).group(1).split()]
    paths = "".join(re.findall(r"<path\b[^>]*/>", logo))
    paths = re.sub(r'\sfill="[^"]*"', "", paths)
    k = width / vb[2]
    x, y = cx - width / 2 - vb[0] * k, cy - vb[3] * k / 2 - vb[1] * k
    return (f'<linearGradient id="wordmetal" gradientUnits="userSpaceOnUse" x1="0" y1="{vb[1]}" x2="0" y2="{vb[1]+vb[3]}">'
            f'<stop offset="0" stop-color="{fill[0]}"/><stop offset="0.55" stop-color="{fill[1]}"/><stop offset="1" stop-color="{fill[2]}"/></linearGradient>'
            f'<g transform="translate({x:.3f},{y:.3f}) scale({k:.6f})" fill="url(#wordmetal)">{paths}</g>')


# The editor panel's code in preview.png: lines of (palette key, text), the selected line's index, the file name.
SAMPLE = ([
    [("muted", "# The last train of the night, as the board sees it.")],
    [("magenta", "from "), ("foreground", "datetime "), ("magenta", "import "), ("foreground", "time")],
    [],
    [("foreground", "LAST "), ("magenta", "= "), ("foreground", "time("), ("orange", "0"), ("foreground", ", "), ("orange", "12"), ("foreground", ")")],
    [],
    [("magenta", "class "), ("yellow", "Platform"), ("foreground", ":")],
    [("foreground", "    line "), ("magenta", "= "), ("green", '"outer loop"')],
    [("foreground", "    cars "), ("magenta", "= "), ("orange", "3")],
    [("foreground", "    lamp "), ("magenta", "= "), ("green", '"red"')],
    [],
    [("magenta", "    def "), ("blue", "departs"), ("foreground", "(self, now: "), ("cyan", "time"), ("foreground", ") -> "),
     ("cyan", "bool"), ("foreground", ":")],
    [("muted", "        # nothing runs after the last one")],
    [("magenta", "        return "), ("foreground", "now "), ("magenta", "<= "), ("foreground", "LAST")],
    [],
    [("magenta", "    def "), ("blue", "wait"), ("foreground", "(self):")],
    [("magenta", "        raise "), ("red", "TimeoutError"), ("foreground", "("), ("green", '"the rain has the platform now"'),
     ("foreground", ")")],
], 12, "last_train.py")


def data_uri(png):
    with open(png, "rb") as fh:
        return "data:image/png;base64," + base64.b64encode(fh.read()).decode()


def preview_desktop(p, c, background_png, sample, align="xMid"):
    w, h = 1800, 1012
    g = 10
    bar = 26
    mono = f'font-family="{MONO}"'
    # background 1 sits exactly where the old art did (same rectangle), so nothing outside it changes
    body = [f'<rect width="{w}" height="{h}" fill="{c["bg_edge"]}"/>',
            f'<image x="705" y="-12" width="1100" height="619" preserveAspectRatio="{align}YMid slice" xlink:href="{data_uri(background_png)}"/>',
            f'<rect width="{w}" height="{bar}" fill="{p["background"]}"/>']
    for i, n in enumerate("12345"):
        col = p["accent"] if i == 0 else p["dark_foreground"]
        body.append(f'<text x="{14 + i*20}" y="18" {mono} font-size="13" fill="{col}">{n}</text>')
    body.append(f'<text x="{w/2}" y="18" {mono} font-size="13" text-anchor="middle" fill="{p["foreground"]}">Monday 09:41</text>')

    def window(x, y, ww, hh, active):
        return (f'<rect x="{x}" y="{y}" width="{ww}" height="{hh}" rx="0" fill="{p["background"]}" fill-opacity="0.96" '
                f'stroke="{p["accent"] if active else p["selection"]}" stroke-width="2"/>')

    lx, ly, lw, lh = g, bar + g, 700, h - bar - 2 * g
    body.append(window(lx, ly, lw, lh, True))
    code, sel_line, filename = sample
    code = [[(p[key], text) for key, text in line] for line in code]
    fs, lh_ = 16, 25
    sel = "".join(t for _, t in code[sel_line]).rstrip()
    body.append(f'<rect x="{lx+18}" y="{ly + 40 + lh_*sel_line - 18}" width="{len(sel)*9.6+8:.0f}" height="24" fill="{p["selection"]}"/>')
    y = ly + 40
    for line in code:
        x = lx + 22
        if line:
            spans = "".join(f'<tspan fill="{col}">{t.replace("&", "&amp;").replace("<", "&lt;")}</tspan>' for col, t in line)
            body.append(f'<text x="{x}" y="{y}" {mono} font-size="{fs}" xml:space="preserve">{spans}</text>')
        y += lh_
    # status line
    sy = ly + lh - 34
    body.append(f'<rect x="{lx+2}" y="{sy}" width="{lw-4}" height="24" fill="{p["lighter_background"]}"/>')
    body.append(f'<rect x="{lx+2}" y="{sy}" width="84" height="24" fill="{p["accent"]}"/>')
    body.append(f'<text x="{lx+14}" y="{sy+17}" {mono} font-size="14" font-weight="bold" fill="{p["background"]}">NORMAL</text>')
    body.append(f'<text x="{lx+100}" y="{sy+17}" {mono} font-size="14" fill="{p["light_foreground"]}">{filename}</text>')

    # right bottom: terminal with the palette; the top-right tile is left free to show the wallpaper
    rx, rw = lx + lw + g, w - lw - 3 * g
    rh = 420
    ry = h - g - rh
    body.append(window(rx, ry, rw, rh, False))
    body.append(f'<text x="{rx+20}" y="{ry+36}" {mono} font-size="16" xml:space="preserve" fill="{p["green"]}">rider@omarchy<tspan fill="{p["foreground"]}"> ~ </tspan><tspan fill="{p["accent"]}">❯</tspan><tspan fill="{p["foreground"]}"> colours</tspan></text>')
    names = ["red", "orange", "yellow", "green", "cyan", "blue", "magenta", "brown"]
    for i, n in enumerate(names):
        yy = ry + 70 + i * 40
        body.append(f'<rect x="{rx+20}" y="{yy}" width="64" height="28" fill="{p[n]}"/>')
        bn = "bright_" + n
        if bn in p:
            body.append(f'<rect x="{rx+90}" y="{yy}" width="64" height="28" fill="{p[bn]}"/>')
        body.append(f'<text x="{rx+172}" y="{yy+20}" {mono} font-size="15" fill="{p[n]}">{n:<8}</text>')
        body.append(f'<text x="{rx+290}" y="{yy+20}" {mono} font-size="15" fill="{p["dark_foreground"]}">{p[n]}</text>')
        if bn in p:
            body.append(f'<text x="{rx+400}" y="{yy+20}" {mono} font-size="15" fill="{p[bn]}">{p[bn]}</text>')

    return svg(w, h, "\n".join(b for b in body if b))


def preview_unlock(p, unlock_png):
    w, h = 1920, 1080
    mono = f'font-family="{MONO}"'
    bx, by, bw, bh = w / 2 - 105, 676, 280, 44
    lx, ly = w / 2 - 160, 680
    body = [f'<rect width="{w}" height="{h}" fill="{p["background"]}"/>',
            f'<image x="{w/2-400}" y="{h/2-150}" width="800" height="188" xlink:href="{data_uri(unlock_png)}"/>',
            # padlock
            f'<path d="M{lx+8},{ly+14} v-8 a14,14 0 0 1 28,0 v8" fill="none" stroke="{p["foreground"]}" stroke-width="5"/>',
            f'<rect x="{lx}" y="{ly+14}" width="44" height="30" rx="5" fill="{p["foreground"]}"/>',
            f'<circle cx="{lx+22}" cy="{ly+27}" r="4" fill="{p["background"]}"/>',
            f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="none" stroke="{p["foreground"]}" stroke-width="2"/>',
            f'<text x="{bx+16}" y="{by+30}" {mono} font-size="22" fill="{p["foreground"]}">••••</text>']
    return svg(w, h, "\n".join(body))



def run(*cmd):
    subprocess.run(cmd, check=True)


def render(svg_text, out_png, workdir, w=None, h=None):
    src = os.path.join(workdir, os.path.basename(out_png) + ".svg")
    with open(src, "w") as fh:
        fh.write(svg_text)
    args = ["rsvg-convert", "-f", "png", "-o", out_png]
    if w:
        args += ["-w", str(w), "-h", str(h)]
    run(*args, src)
    strip(out_png)


def strip(png):
    """Drop metadata chunks (dates, etc.) so rebuilding is byte-identical."""
    run("magick", png, "-strip", "-define", "png:exclude-chunks=date,time", png)


def contrast_report(p):
    bg = p["background"]
    lines = [f"foreground {p['foreground']} on background {bg}: {contrast(p['foreground'], bg):.2f}:1 (need 4.5)"]
    ansi = ["red", "green", "yellow", "blue", "magenta", "cyan", "muted",
            "bright_red", "bright_green", "bright_yellow", "bright_blue", "bright_magenta", "bright_cyan",
            "light_foreground", "bright_foreground", "dark_foreground", "orange", "accent"]
    worst = min(contrast(p[k], bg) for k in ansi)
    for k in ansi:
        lines.append(f"{k:17} {p[k]}: {contrast(p[k], bg):.2f}:1 (need 3.0)")
    ok = contrast(p["foreground"], bg) >= 4.5 and worst >= 3.0
    return ok, "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=REPO, help="write here instead of the repository root")
    ap.add_argument("--hero", default=os.path.join(REPO, HERO), help="the background shown in preview.png's art panel")
    ap.add_argument("--align", choices=("left", "centre", "right"), default="centre",
                    help="which side of the hero the preview's 16:9 art panel keeps")
    args = ap.parse_args()
    with open(os.path.join(REPO, "colors.toml"), "rb") as fh:
        p = tomllib.load(fh)
    ok, report = contrast_report(p)
    print(report)
    if not ok:
        sys.exit("contrast below targets; fix colors.toml")
    c = {"bg_edge": p["darker_background"]}
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    with tempfile.TemporaryDirectory() as work:
        small = os.path.join(work, "hero-small.png")
        run("magick", args.hero, "-resize", "1100x", small)
        strip(small)
        unlock = os.path.join(out, "unlock.png")
        render(svg(800, 188, wordmark(400, 94, 800, (p["accent"],) * 3)), unlock, work)
        render(preview_unlock(p, unlock), os.path.join(out, "preview-unlock.png"), work)
        render(preview_desktop(p, c, small, SAMPLE, {"left": "xMin", "centre": "xMid", "right": "xMax"}[args.align]),
               os.path.join(out, "preview.png"), work)
    print(f"built {out}")


if __name__ == "__main__":
    main()
