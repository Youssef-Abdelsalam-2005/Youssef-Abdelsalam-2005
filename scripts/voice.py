#!/usr/bin/env python3
"""Generates assets/voice.svg: an abstract voice-AI visual.

A morphing orb that "speaks", ripples spreading out from it, and audio bars
either side pulsing like speech with natural pauses. Transparent background,
so it sits on GitHub's light and dark themes alike.

Run: python3 scripts/voice.py
"""
import math
import random
from pathlib import Path

random.seed(7)

W, H = 1200, 360
CX, CY = W / 2, H / 2
ORB_R = 78
DUR = 8.0             # seconds per loop
FRAMES = 40           # loudness keyframes per loop
BAR_W, PITCH = 5, 11
BAR_START = 150       # distance of first bar from centre
BARS = int((W / 2 - BAR_START - 20) / PITCH)
PURPLE, BLUE, TEAL, PINK = "#7f5af0", "#3da9fc", "#2cb67d", "#ff7ab6"


# ---- a speech-like loudness curve: syllable bursts with a couple of pauses --
def loudness():
    vals = []
    for f in range(FRAMES):
        t = f / FRAMES
        pause = 0.08 if (0.42 < t < 0.55 or t > 0.9) else 1.0
        syll = 0.55 + 0.45 * abs(math.sin(t * math.pi * 11 + math.sin(t * 7)))
        vals.append(max(0.08, pause * syll * random.uniform(0.75, 1.0)))
    vals[-1] = vals[0] = 0.1           # start/end quiet so the loop is seamless
    return vals


LOUD = loudness()
KT = ";".join(f"{f / FRAMES:.4f}" for f in range(FRAMES)) + ";1"
SPLINES = ";".join([".4 0 .6 1"] * FRAMES)


def anim(attr, vals, extra=""):
    v = ";".join(f"{x:.1f}" for x in vals + [vals[0]])
    return (f'<animate attributeName="{attr}" values="{v}" keyTimes="{KT}" dur="{DUR}s" '
            f'calcMode="spline" keySplines="{SPLINES}" repeatCount="indefinite"{extra}/>')


# ---- audio bars ---------------------------------------------------------------
def bars():
    out = []
    for i in range(BARS):
        d = i / BARS                                    # 0 near orb → 1 at edge
        env = (1 - d) ** 1.6 * 0.92 + 0.08
        lag = int(i * 0.35)                             # sound travels outward
        jitter = [random.uniform(0.55, 1.0) for _ in range(FRAMES)]
        hs = [max(4, LOUD[(f - lag) % FRAMES] * jitter[f] * env * H * 0.62) for f in range(FRAMES)]
        ys = [CY - h / 2 for h in hs]
        op = 0.25 + 0.75 * (1 - d)
        for side in (-1, 1):
            x = CX + side * (BAR_START + i * PITCH) - BAR_W / 2
            out.append(
                f'<rect x="{x:.1f}" y="{ys[0]:.1f}" width="{BAR_W}" height="{hs[0]:.1f}" rx="{BAR_W / 2}" '
                f'fill="url(#bar{"L" if side < 0 else "R"})" opacity="{op:.2f}">'
                f'{anim("height", hs)}{anim("y", ys)}</rect>')
    return "\n".join(out)


# ---- orb: overlapping blobs that morph and rotate ----------------------------
def blob(r, wobble, seed, points=8):
    rnd = random.Random(seed)
    pts = []
    for k in range(points):
        a = 2 * math.pi * k / points
        rr = r * (1 + rnd.uniform(-wobble, wobble))
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    # closed Catmull-Rom → cubic Béziers (same command count for every shape)
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    n = len(pts)
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d + "Z"


def orb():
    layers = []
    for li, (grad, spin, dur) in enumerate([("o1", 1, 9), ("o2", -1, 13), ("o3", 1, 17)]):
        shapes = [blob(ORB_R * (1 - li * 0.06), 0.1, li * 10 + s) for s in range(4)]
        shapes.append(shapes[0])
        layers.append(
            f'<g><animateTransform attributeName="transform" type="rotate" values="0;{spin * 360}" '
            f'dur="{dur}s" repeatCount="indefinite"/>'
            f'<path d="{shapes[0]}" fill="url(#{grad})" opacity=".85">'
            f'<animate attributeName="d" values="{";".join(shapes)}" dur="{dur * 0.6:.1f}s" '
            f'calcMode="spline" keySplines="{";".join([".45 0 .55 1"] * 4)}" repeatCount="indefinite"/></path></g>')
    # the whole orb swells with the loudness curve
    scale = ";".join(f"{0.92 + 0.14 * v:.3f}" for v in LOUD + [LOUD[0]])
    return f"""
  <g transform="translate({CX} {CY})">
    <circle r="{ORB_R * 1.9}" fill="url(#halo)">
      <animate attributeName="r" values="{";".join(f"{ORB_R * (1.6 + 0.6 * v):.1f}" for v in LOUD + [LOUD[0]])}" keyTimes="{KT}" dur="{DUR}s" calcMode="spline" keySplines="{SPLINES}" repeatCount="indefinite"/>
    </circle>
    {ripples()}
    <g filter="url(#soft)">
      <g>
        <animateTransform attributeName="transform" type="scale" values="{scale}" keyTimes="{KT}" dur="{DUR}s" calcMode="spline" keySplines="{SPLINES}" repeatCount="indefinite"/>
        {''.join(layers)}
        <circle r="{ORB_R * 0.55}" fill="url(#core)"/>
      </g>
    </g>
  </g>"""


def ripples():
    out = []
    for k in range(3):
        out.append(
            f'<circle r="{ORB_R}" fill="none" stroke="url(#ring)" stroke-width="1.5" opacity="0">'
            f'<animate attributeName="r" values="{ORB_R};{ORB_R * 2.4}" dur="3.6s" begin="{k * 1.2}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values=".7;0" dur="3.6s" begin="{k * 1.2}s" repeatCount="indefinite"/>'
            f'</circle>')
    return "".join(out)


svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Abstract voice AI visual">
  <defs>
    <linearGradient id="barL" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{CX}" y2="0">
      <stop offset="0" stop-color="{TEAL}"/><stop offset="1" stop-color="{BLUE}"/>
    </linearGradient>
    <linearGradient id="barR" gradientUnits="userSpaceOnUse" x1="{CX}" y1="0" x2="{W}" y2="0">
      <stop offset="0" stop-color="{PURPLE}"/><stop offset="1" stop-color="{PINK}"/>
    </linearGradient>
    <radialGradient id="o1" cx="30%" cy="30%" r="80%"><stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{PURPLE}"/></radialGradient>
    <radialGradient id="o2" cx="70%" cy="40%" r="80%"><stop offset="0" stop-color="{PINK}" stop-opacity=".9"/><stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/></radialGradient>
    <radialGradient id="o3" cx="40%" cy="75%" r="80%"><stop offset="0" stop-color="{TEAL}" stop-opacity=".9"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
    <radialGradient id="core"><stop offset="0" stop-color="#ffffff" stop-opacity=".75"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>
    <radialGradient id="halo"><stop offset=".35" stop-color="{PURPLE}" stop-opacity=".35"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
    <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{PINK}"/></linearGradient>
    <filter id="soft" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <g>{bars()}</g>
  {orb()}
</svg>
"""

out = Path(__file__).resolve().parent.parent / "assets" / "voice.svg"
out.write_text(svg)
print(f"wrote {out} ({len(svg) / 1024:.0f} KB)")
