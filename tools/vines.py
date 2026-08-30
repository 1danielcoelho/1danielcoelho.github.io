"""Regenerates static/vine-1.svg .. vine-8.svg.

One file per vine. Each tiles vertically down the left gutter; the CSS gives each
one a different height so they finish at staggered points down the page
(see assets/css/extended/vines.css).

Seamlessness is structural, not eyeballed: every stem is a sine wave whose period
divides the tile height an integer number of times, so both its x position and its
slope match at y=0 and y=H. Leaves straddling the boundary are emitted twice, once
shifted a whole tile, so their halves meet across the join.

Colours are baked into the SVGs rather than applied via CSS masks, which is what
allows each leaf its own tone. Pick values that read on both the light and dark
backgrounds; the CSS only lifts brightness slightly for dark.

Run:  python tools/vines.py
"""

import colorsys
import math
import pathlib
import random

W, H = 150.0, 1200.0     # tile size, SVG units. Keep W == --vine-width in the CSS.
STEP = 15.0              # stem sampling interval
LEAF_SPACING = 38.0      # along-stem distance between leaves (smaller = denser)
SEED = 20260830          # fixed, so regenerating gives identical files

STEM = "#7e6244"         # rgb(126, 98, 68)

# Leaves are jittered in HSL around a moss green. Widen these for more variation.
LEAF_HUE = (72, 108)     # degrees; <90 olive/yellow, >90 cooler green
LEAF_SAT = (0.20, 0.36)
LEAF_LIG = (0.34, 0.52)
BROWN_LEAF_CHANCE = 0.10  # occasional dying leaf, hue pulled toward the stem

# cx, amplitude, k (MUST be an integer), phase, stroke width
# Positions are deliberately uneven — evenly spaced stems read as a printed
# border rather than as growth. Keep cx +/- amplitude inside [0, W] or the
# container's overflow:hidden will clip a stem against the screen edge.
VINES = [
    ( 14.0,  7.0, 2, 0.30, 1.4),
    ( 26.0, 11.0, 1, 1.90, 2.0),
    ( 33.0,  6.0, 3, 3.40, 1.2),
    ( 52.0, 15.0, 1, 5.00, 2.3),
    ( 68.0,  9.0, 2, 0.90, 1.6),
    ( 79.0, 13.0, 3, 2.60, 1.5),
    (104.0, 17.0, 1, 4.40, 2.1),
    (131.0, 10.0, 2, 1.40, 1.7),
]


def x_at(cx, A, k, ph, y):
    return cx + A * math.sin(2 * math.pi * k * y / H + ph)


def dx_at(A, k, ph, y):
    """Slope dx/dy — used to angle each leaf off its stem's tangent."""
    return A * (2 * math.pi * k / H) * math.cos(2 * math.pi * k * y / H + ph)


def r(v, nd=1):
    return f"{v:.{nd}f}".rstrip("0").rstrip(".") or "0"


def leaf_colour(rng):
    if rng.random() < BROWN_LEAF_CHANCE:
        h = rng.uniform(28, 46) / 360.0
        s, l = rng.uniform(0.26, 0.40), rng.uniform(0.30, 0.42)
    else:
        h = rng.uniform(*LEAF_HUE) / 360.0
        s, l = rng.uniform(*LEAF_SAT), rng.uniform(*LEAF_LIG)
    rr, gg, bb = colorsys.hls_to_rgb(h, l, s)
    return "#%02x%02x%02x" % (round(rr * 255), round(gg * 255), round(bb * 255))


def build_vine(vi, cx, A, k, ph, sw, rng):
    pts, y = [], 0.0
    while y <= H + 1e-6:
        pts.append((x_at(cx, A, k, ph, y), y))
        y += STEP
    d = "M" + " L".join(f"{r(px)},{r(py)}" for px, py in pts)
    stem = (f'<path d="{d}" fill="none" stroke="{STEM}" stroke-width="{sw}" '
            f'stroke-linecap="round"/>')

    leaves = []
    y = (vi * 11.7) % LEAF_SPACING
    side = 1 if vi % 2 == 0 else -1
    while y < H:
        px = x_at(cx, A, k, ph, y)
        stem_ang = math.degrees(math.atan2(1.0, dx_at(A, k, ph, y)))
        ang = stem_ang + side * (46.0 + rng.uniform(-16.0, 16.0))
        L = rng.uniform(7.5, 13.5)
        col = leaf_colour(rng)
        body = (f'<use href="#l" fill="{col}" transform="translate({r(px)},{r(y)}) '
                f'rotate({r(ang, 0)}) scale({r(L)})"/>')
        leaves.append(body)
        # Straddles the seam -> draw the other half on the far edge too.
        if y < L:
            leaves.append(body.replace(f",{r(y)})", f",{r(y + H)})", 1))
        elif y > H - L:
            leaves.append(body.replace(f",{r(y)})", f",{r(y - H)})", 1))
        side = -side
        y += LEAF_SPACING * rng.uniform(0.72, 1.28)

    return stem, leaves


def main():
    rng = random.Random(SEED)
    out = pathlib.Path(__file__).resolve().parent.parent / "static"
    for old in out.glob("vine-*.svg"):
        old.unlink()

    hdr = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{r(W)}" height="{r(H)}" '
           f'viewBox="0 0 {r(W)} {r(H)}" preserveAspectRatio="none">'
           f'<defs><ellipse id="l" cx=".62" cy="0" rx=".62" ry=".3"/></defs>')

    total = 0
    print("seam continuity (x at y=0 vs y=H):")
    for vi, (cx, A, k, ph, sw) in enumerate(VINES):
        stem, leaves = build_vine(vi, cx, A, k, ph, sw, rng)
        (out / f"vine-{vi + 1}.svg").write_text(
            hdr + stem + "".join(leaves) + "</svg>", encoding="utf-8")
        a, b = x_at(cx, A, k, ph, 0.0), x_at(cx, A, k, ph, H)
        assert abs(a - b) < 1e-9, f"vine {vi + 1} does not close across the tile boundary"
        total += len(leaves)
        print(f"  vine-{vi + 1}  cx={cx:6.1f}  delta={abs(a - b):.1e}  leaves={len(leaves)}")
    print(f"\n{len(VINES)} files, {total} leaves total")


if __name__ == "__main__":
    main()
