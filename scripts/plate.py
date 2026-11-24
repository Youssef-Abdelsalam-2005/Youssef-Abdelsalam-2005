#!/usr/bin/env python3
"""Generates assets/plate.svg: a halftone Chladni plate.

A grid of dots where dot size is how much "sand" sits there. Each frequency
gathers the sand onto the plate's still lines (a Chladni figure). When the
frequency changes, the sand scatters and resettles, and the change sweeps
across the plate from left to right.

One ink colour that follows the viewer's light/dark theme; transparent background.
Run: python3 scripts/plate.py
"""
import math
import random
from pathlib import Path

W, H = 1200, 360
PITCH = 11
R_MIN, R_MAX = 0.55, 4.4
LINE_W = 7.5          # px half-width of a sand line
SWEEP = 2.2           # seconds for a change to cross the plate
INK_LIGHT, INK_DARK = "#1f2328", "#e6edf3"

# Square-plate Chladni figures cos(aπx)cos(bπy) ± cos(bπx)cos(aπy), in isotropic
# units (x/H, y/H) so they keep their shape on the wide plate.
MODES = [(2, 5, -1), (3, 4, 1), (1, 6, -1), (4, 5, 1), (3, 5, -1)]
SLOTS = ["hold", "hold", "hold", "scatter"]          # 1 s each, evenly spaced keyframes
DUR = len(MODES) * len(SLOTS)

rnd = random.Random(5)


def f(x, y, md):
    a, b, sg = md
    return (math.cos(a * math.pi * x) * math.cos(b * math.pi * y)
            + sg * math.cos(b * math.pi * x) * math.cos(a * math.pi * y))


def sand(px, py, md):
    """0..1: how close (px, py) is to a still line of mode md."""
    x, y, e = px / H, py / H, 1e-4
    v = f(x, y, md)
    gx = (f(x + e, y, md) - v) / e
    gy = (f(x, y + e, md) - v) / e
    dist = abs(v) / max(math.hypot(gx, gy), 1e-6) * H     # px to the nearest node line
    return math.exp(-(dist / LINE_W) ** 2)


cols = int(W / PITCH)
rows = int(H / PITCH)
x0 = (W - (cols - 1) * PITCH) / 2
y0 = (H - (rows - 1) * PITCH) / 2

dots = []
for c in range(cols):
    for r in range(rows):
        px, py = x0 + c * PITCH, y0 + r * PITCH
        vals = []
        for md in MODES:
            s = sand(px, py, md)
            rad = R_MIN + (R_MAX - R_MIN) * s * rnd.uniform(0.85, 1.0)
            for slot in SLOTS:
                vals.append(rad if slot == "hold" else R_MIN + (R_MAX - R_MIN) * rnd.random() ** 3)
        vals.append(vals[0])
        if max(vals) < R_MIN + 0.4:                       # never gathers sand: keep static
            dots.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{R_MIN}"/>')
            continue
        delay = c / cols * SWEEP + rnd.uniform(0, 0.25)   # left-to-right sweep
        v = ";".join(f"{x:.1f}" for x in vals)
        dots.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{vals[0]:.1f}">'
                    f'<animate attributeName="r" values="{v}" dur="{DUR}s" begin="-{DUR - delay:.2f}s" '
                    f'repeatCount="indefinite"/></circle>')

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Halftone Chladni plate: sand forming sound patterns">
<style>.ink{{fill:{INK_LIGHT}}}@media (prefers-color-scheme: dark){{.ink{{fill:{INK_DARK}}}}}</style>
<defs>
  <linearGradient id="fade"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".08" stop-color="#fff"/><stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
</defs>
<g class="ink" mask="url(#m)">{"".join(dots)}</g>
</svg>
"""
out = Path(__file__).resolve().parent.parent / "assets" / "plate.svg"
out.write_text(svg)
print(f"wrote {out.name}  {len(svg) / 1024:.0f} KB, {len(dots)} dots")
