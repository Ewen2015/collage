#!/usr/bin/env python3
"""
collage.py — a deterministic paper-collage renderer.

Everything is built from procedural paper, ink and print textures so the output
looks like something cut, glued and re-scanned, rather than vector shapes on a
canvas. Same seed -> same picture. No network access, no external assets.

Usage
-----
    python3 collage.py --list
    python3 collage.py --preset cubist-grid --out cubist.png --seed 4
    python3 collage.py --recipe my-recipe.json --out custom.png --scale 1.5

A recipe is plain JSON:

    {
      "width": 1200, "height": 1600, "paper": "cream", "seed": 11,
      "pieces": [
        {"source": "newsprint", "box": [120, 300, 640, 420], "rotate": -4,
         "mask": "torn", "blend": "multiply", "shadow": true},
        {"source": "gradient", "palette": ["#1f4a8a", "#e8dfc8"],
         "box": [700, 200, 520, 700], "mask": "cut", "rotate": 8},
        {"text": "CUT / PASTE", "box": [200, 1200, 900, 160],
         "font": "sans-bold", "size": 120, "color": "ink", "tracking": 6}
      ],
      "tape": [[600, 260, 220, 54, -8]],
      "marks": true
    }

`box` is [x, y, w, h] in canvas pixels. Rotation keeps the box center fixed.
A transparent PNG produced by visual_cutout.py can be used with
`mask: "alpha"`; its own image-dependent silhouette is preserved.

Requires: Pillow, NumPy. Content-dependent cutting uses the same two libraries.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# Palettes. Two to four inks + one paper stock. The limited ink count is what
# makes a collage read as printed matter rather than a mood board.
# ---------------------------------------------------------------------------

PALETTES = {
    "cream": {"paper": "#f2e9d6", "ink": ["#1d1a17", "#c8412f", "#234a78", "#d8a02c", "#6b7a55"]},
    "newsprint": {"paper": "#e5e0d3", "ink": ["#26241f", "#b23a2c", "#3a5f8a", "#c9962e"]},
    "kraft": {"paper": "#cdb08a", "ink": ["#2b211a", "#8d3b2a", "#e8ddc2", "#3f5d55"]},
    "cold": {"paper": "#e8ecea", "ink": ["#16283a", "#d94f36", "#4a86a8", "#f0c94b"]},
    "pink": {"paper": "#f3dfd8", "ink": ["#241a20", "#e0446d", "#2e4f9e", "#f2b13c", "#3d7169"]},
    "black": {"paper": "#1c1b1a", "ink": ["#f0e6d2", "#e4543a", "#6f9fc4", "#e3b64a"]},
}

# Fonts are resolved at runtime; missing ones fall back gracefully.
FONT_CANDIDATES = {
    "sans": ["Poppins-Regular.ttf", "DejaVuSans.ttf", "Lato-Medium.ttf"],
    "sans-bold": ["Poppins-Bold.ttf", "DejaVuSans-Bold.ttf", "Lato-Bold.ttf"],
    "sans-cond": ["DejaVuSansCondensed-Bold.ttf", "Poppins-Bold.ttf", "DejaVuSans-Bold.ttf"],
    "serif": ["DejaVuSerif.ttf", "Lora-Variable.ttf"],
    "serif-bold": ["DejaVuSerif-Bold.ttf", "Lora-Variable.ttf"],
    "serif-italic": ["DejaVuSerif-Italic.ttf", "Lora-Italic-Variable.ttf"],
    "mono": ["NotoSansMono-Regular.ttf", "DejaVuSansMono.ttf"],
    "mono-bold": ["DejaVuSansMono-Bold.ttf", "NotoSansMono-Regular.ttf"],
}
FONT_DIRS = [
    "/usr/share/fonts/truetype/google-fonts",
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/lato",
    "/usr/share/fonts/truetype/liberation2",
    "/usr/share/fonts/opentype/noto",
    "/System/Library/Fonts",
    "/Library/Fonts",
]


def rgb(hexstr):
    s = hexstr.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def resolve_font(name, size):
    for fn in FONT_CANDIDATES.get(name, FONT_CANDIDATES["sans"]):
        for d in FONT_DIRS:
            p = os.path.join(d, fn)
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except OSError:
                    pass
    return ImageFont.load_default()


def alpha_source(spec, w, h, rng, pal):
    """Fit a transparent, content-cut PNG into its box without losing alpha.

    The cutout carries a shape chosen by the agent from the photograph's
    subject. Here we preserve that silhouette exactly and letterbox rather
    than centre-crop, so no part of the cut is thrown away. A missing cutout
    degrades to a printed-paper field instead of aborting the whole poster.
    """
    path = str(spec.get("source", ""))
    if not os.path.isfile(path):
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        paper = source_image({"source": "newsprint"}, w, h, rng, pal).convert("RGBA")
        im.alpha_composite(paper, (0, 0))
        return im
    im = Image.open(path).convert("RGBA")
    ratio = min(w / im.width, h / im.height)
    size = (max(1, int(im.width * ratio)), max(1, int(im.height * ratio)))
    im = im.resize(size, Image.Resampling.LANCZOS)
    alpha = im.getchannel("A")
    rgb_im = Image.new("RGB", im.size, mix(rgb(pal["paper"]), rgb("#d8c9a8"), .35))
    rgb_im.paste(im.convert("RGB"), (0, 0), alpha)
    rgb_im = halftone(rgb_im, cell=7, angle=15, ink=(28, 26, 24), opacity=.18)
    tint = Image.new("RGB", rgb_im.size, mix(rgb(pal["paper"]), rgb("#d8c9a8"), .35))
    rgb_im = Image.blend(rgb_im, tint, .06)
    rgb_im = grain_overlay(rgb_im, rng, strength=4)
    canvas = Image.new("RGBA", (w, h), rgb(pal["paper"]) + (0,))
    canvas.paste(rgb_im.convert("RGBA"), ((w - size[0]) // 2, (h - size[1]) // 2), alpha)
    return canvas


def noise2d(rng, w, h, scale=1.0):
    """Smooth-ish multi-octave value noise in [0,1]."""
    acc = np.zeros((h, w), dtype=np.float32)
    amp, total = 1.0, 0.0
    for octave in (4, 12, 36, 96):
        gh = max(2, int(h / octave * scale))
        gw = max(2, int(w / octave * scale))
        small = rng.random((gh, gw)).astype(np.float32)
        big = np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BILINEAR),
                         dtype=np.float32) / 255.0
        acc += big * amp
        total += amp
        amp *= 0.55
    return acc / total


def grain_overlay(base, rng, strength=9):
    a = np.asarray(base, dtype=np.float32).copy()
    g = rng.normal(0, strength, (a.shape[0], a.shape[1], 1)).astype(np.float32)
    a += g
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def paper_base(w, h, color, rng):
    c = np.array(rgb(color), dtype=np.float32)
    n = noise2d(rng, w, h) - 0.5
    fiber = rng.normal(0, 2.2, (h, w)).astype(np.float32)
    arr = np.empty((h, w, 3), dtype=np.float32)
    for i in range(3):
        arr[:, :, i] = c[i] + n * 15 + fiber
    # faint warm vignette, like a scan of a physical sheet
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = ((xx / w - 0.5) ** 2 + (yy / h - 0.5) ** 2)
    arr -= (d[..., None] * 26)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def halftone(img, cell=6, angle=15, ink=(30, 28, 25), opacity=0.45):
    """Screen-print dots over an image, in image space (rotated grid)."""
    w, h = img.size
    layer = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(layer)
    r = max(1.0, cell * 0.34)
    diag = int(math.hypot(w, h)) + cell * 4
    for gy in range(-diag, diag, cell):
        for gx in range(-diag, diag, cell):
            a = math.radians(angle)
            x = gx * math.cos(a) - gy * math.sin(a) + w / 2
            y = gx * math.sin(a) + gy * math.cos(a) + h / 2
            if -cell < x < w + cell and -cell < y < h + cell:
                d.ellipse([x - r, y - r, x + r, y + r], fill=ink)
    layer = layer.rotate(-angle, resample=Image.Resampling.BILINEAR, center=(w / 2, h / 2),
                         expand=False).filter(ImageFilter.GaussianBlur(0.35))
    return Image.blend(img, Image.fromarray(np.minimum(np.asarray(img), np.asarray(layer)), "RGB"), opacity)


def source_image(spec, w, h, rng, pal):
    kind = spec.get("source", "solid")
    inks = [rgb(c) for c in spec.get("palette", pal["ink"])]
    paper = rgb(spec.get("paper", pal["paper"]))
    c0 = inks[0]
    c1 = inks[min(1, len(inks) - 1)]
    c2 = inks[min(2, len(inks) - 1)]

    looks_like_path = ("/" in str(kind) or os.sep in str(kind)) or str(kind).lower().endswith(
        (".png", ".jpg", ".jpeg", ".webp"))
    if looks_like_path and not os.path.isfile(str(kind)):
        # A sourced asset went missing (offline run, moved folder). Degrade to a
        # procedural magazine crop instead of failing the whole composition.
        kind = "photo"
    if os.path.isfile(str(kind)) and str(kind).lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        im = Image.open(kind).convert("RGB")
        ratio = max(w / im.width, h / im.height)
        im = im.resize((max(1, int(im.width * ratio)), max(1, int(im.height * ratio))), Image.Resampling.LANCZOS)
        im = im.crop(((im.width - w) // 2, (im.height - h) // 2,
                      (im.width - w) // 2 + w, (im.height - h) // 2 + h))
        # Two-screen treatment: every found photograph is printed, halftoned and
        # slightly re-coloured. This is what turns a stock photo into a *scrap*
        # so it can sit beside real paper instead of looking like a window.
        im = halftone(im, cell=7, angle=15, ink=(28, 26, 24), opacity=.30)
        tint = Image.new("RGB", (w, h), mix(rgb(pal["paper"]), rgb("#d8c9a8"), .35))
        im = Image.blend(im, tint, .12)
        return grain_overlay(im, rng, strength=7)

    if kind == "solid":
        im = Image.new("RGB", (w, h), c0)
    elif kind == "gradient":
        yy = np.linspace(0, 1, h)[:, None, None]
        xx = np.linspace(0, 1, w)[None, :, None]
        t = np.clip(0.62 * yy + 0.38 * xx, 0, 1)
        a = np.array(c0, dtype=np.float32)
        b = np.array(c1, dtype=np.float32)
        im = Image.fromarray((a[None, None, :] * (1 - t) + b[None, None, :] * t).astype(np.uint8), "RGB")
    elif kind == "photo":
        # simulated magazine crop: soft colour field + halftone + bloom
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        cx, cy = w * rng.uniform(0.3, 0.7), h * rng.uniform(0.25, 0.7)
        t = np.clip(1 - np.sqrt(((xx - cx) / (w * .7)) ** 2 + ((yy - cy) / (h * .8)) ** 2), 0, 1)
        a = np.array(c0, dtype=np.float32)
        b = np.array(c1, dtype=np.float32)
        arr = a[None, None, :] * (1 - t[..., None]) + b[None, None, :] * t[..., None]
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
        im = halftone(im, cell=max(4, int(min(w, h) / 110)), angle=45, ink=c2, opacity=0.28)
    elif kind == "halftone":
        im = Image.new("RGB", (w, h), paper)
        im = halftone(im, cell=int(spec.get("cell", 9)), angle=spec.get("angle", 15), ink=c0, opacity=0.9)
    elif kind == "newsprint":
        im = Image.new("RGB", (w, h), mix(paper, (255, 255, 255), 0.35))
        d = ImageDraw.Draw(im)
        cols = max(2, int(w / 190))
        cw = w / cols
        for ci in range(cols):
            y = 8
            while y < h - 10:
                ln = rng.uniform(0.55, 0.97) * (cw - 18)
                d.rectangle([ci * cw + 9, y, ci * cw + 9 + ln, y + 2.0],
                            fill=mix(paper, rgb("#4a453c"), 0.48))
                y += rng.uniform(6.5, 9.5)
        if rng.random() < 0.8:
            d.rectangle([10, 10, min(w - 10, 10 + w * rng.uniform(.5, .95)), 10 + rng.uniform(20, 46)], fill=c0)
        im = im.filter(ImageFilter.GaussianBlur(0.3))
    elif kind == "stripes":
        im = Image.new("RGB", (w, h), paper)
        d = ImageDraw.Draw(im)
        bw = max(6, int(spec.get("band", w / 12)))
        for x in range(0, w, bw * 2):
            d.rectangle([x, 0, x + bw, h], fill=c0 if (x // bw) % 4 < 2 else c1)
    elif kind == "grid":
        # cubist facet field
        im = Image.new("RGB", (w, h), paper)
        d = ImageDraw.Draw(im)
        step = max(28, int(min(w, h) / 6))
        for gy in range(0, h + step, step):
            for gx in range(0, w + step, step):
                col = inks[rng.integers(0, len(inks))]
                if rng.random() < 0.62:
                    pts = [(gx, gy), (gx + step, gy + rng.uniform(-step / 3, step / 3)),
                           (gx + step, gy + step), (gx + rng.uniform(-step / 3, step / 3), gy + step)]
                    d.polygon(pts, fill=col)
    elif kind == "wood":
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        v = np.sin(xx / 13 + np.sin(yy / 47) * 2.6) * 0.5 + 0.5
        a = np.array(mix(paper, c0, 0.55), dtype=np.float32)
        b = np.array(c0, dtype=np.float32)
        im = Image.fromarray((a[None, None, :] * (1 - v[..., None]) + b[None, None, :] * v[..., None]).astype(np.uint8), "RGB")
    elif kind == "kraft":
        n = noise2d(rng, w, h, 2.0)[..., None]
        a = np.array(paper, dtype=np.float32)
        im = Image.fromarray(np.clip(a[None, None, :] * (0.82 + n * 0.36), 0, 255).astype(np.uint8), "RGB")
    elif kind == "stamp":
        im = Image.new("RGB", (w, h), mix(paper, (255, 255, 255), .55))
        d = ImageDraw.Draw(im)
        d.rectangle([12, 12, w - 12, h - 12], fill=c0)
        d.ellipse([w * .28, h * .25, w * .72, h * .75], fill=c1)
        for x in range(12, w - 12, 16):
            d.ellipse([x - 4, -4, x + 4, 8], fill=paper)
            d.ellipse([x - 4, h - 8, x + 4, h + 4], fill=paper)
        for y in range(12, h - 12, 16):
            d.ellipse([-4, y - 4, 8, y + 4], fill=paper)
            d.ellipse([w - 8, y - 4, w + 4, y + 4], fill=paper)
    elif kind == "type":
        im = Image.new("RGB", (w, h), c0)
        d = ImageDraw.Draw(im)
        f = resolve_font("serif-bold", int(min(w, h) * 0.92))
        ch = spec.get("char", rng.choice(list("ABCDEFGMRS")))
        bb = d.textbbox((0, 0), ch, font=f)
        d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], (h - (bb[3] - bb[1])) / 2 - bb[1]),
               ch, font=f, fill=c1)
    else:
        raise ValueError("unknown source: %s" % kind)

    if spec.get("halftone"):
        im = halftone(im, cell=int(spec.get("cell", 7)), ink=rgb("#241f1b"), opacity=.35)
    return grain_overlay(im, rng, strength=spec.get("grain", 6))


def make_mask(kind, w, h, rng):
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    if kind in (None, "cut", "rect"):
        j = 1 if kind == "cut" else 0
        d.rectangle([j, j, w - j - 1, h - j - 1], fill=255)
    elif kind in ("alpha", "content", "retain-alpha"):
        # alpha_source() already returns a transparent layer with the exact
        # silhouette; this branch is only a safe fallback for hand recipes.
        d.rectangle([0, 0, w - 1, h - 1], fill=255)
    elif kind in ("torn", "strip", "torn-v"):
        vertical = kind == "torn-v"
        length = h if vertical else w
        pts_top, pts_bot = [], []
        step = 5
        amp = 8 if kind == "strip" else 13
        for t in range(0, length + step, step):
            off = rng.uniform(-amp, amp) + 3 * math.sin(t / 19)
            if vertical:
                pts_top.append((w * .5 + off, t))
                pts_bot.append((w * .5 + off, t))
            else:
                pts_top.append((t, h * .5 - h * .42 + off))
                pts_bot.append((t, h * .5 + h * .42 + off))
        poly = pts_top + list(reversed(pts_bot))
        if vertical:
            poly = [(0 + rng.uniform(-amp, amp), t) for t in range(0, h + step, step)] + \
                   [(w + rng.uniform(-amp, amp), t) for t in reversed(range(0, h + step, step))]
        d.polygon(poly, fill=255)
        # feather the tear slightly, like paper fibre
        m = m.filter(ImageFilter.GaussianBlur(0.6))
    elif kind == "circle":
        d.ellipse([2, 2, w - 3, h - 3], fill=255)
    elif kind == "arch":
        # an arch with a true flat bottom: semicircular head + rectangular stem
        head_h = w / 2
        d.pieslice([0, 0, w - 1, 2 * head_h - 1], 180, 360, fill=255)
        d.rectangle([0, head_h, w - 1, h - 1], fill=255)
    elif kind == "triangle":
        d.polygon([(w / 2, 0), (w, h), (0, h)], fill=255)
    elif kind == "diamond":
        d.polygon([(w / 2, 0), (w, h / 2), (w / 2, h), (0, h / 2)], fill=255)
    elif kind == "perforated":
        d.rectangle([6, 6, w - 7, h - 7], fill=255)
        for x in range(6, w - 6, 15):
            d.ellipse([x - 4, -4, x + 4, 8], fill=0)
            d.ellipse([x - 4, h - 8, x + 4, h + 4], fill=0)
        for y in range(6, h - 6, 15):
            d.ellipse([-4, y - 4, 8, y + 4], fill=0)
            d.ellipse([w - 8, y - 4, w + 4, y + 4], fill=0)
    else:
        raise ValueError("unknown mask: %s" % kind)
    return m


def blend_region(canvas, layer, mode, opacity):
    """Composite an RGBA layer onto an RGB canvas using a print-like blend."""
    la = np.asarray(layer, dtype=np.float32)
    a = (la[:, :, 3:4] / 255.0) * opacity
    c = np.asarray(canvas, dtype=np.float32)
    src = la[:, :, :3]
    if mode == "multiply":
        out = c * (src / 255.0)
    elif mode == "screen":
        out = 255 - (255 - c) * (255 - src) / 255.0
    elif mode == "overlay":
        out = np.where(c < 128, 2 * c * src / 255.0, 255 - 2 * (255 - c) * (255 - src) / 255.0)
    else:
        out = src
    c = c * (1 - a) + out * a
    return Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB")


def paste_piece(canvas, piece_rgba, cx, cy, angle, shadow, rng, mode="normal", opacity=1.0):
    """Composite a piece onto the canvas, clipping safely at the sheet edges."""
    if angle:
        piece_rgba = piece_rgba.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    pw, ph = piece_rgba.size
    x0, y0 = int(cx - pw / 2), int(cy - ph / 2)
    if shadow:
        alpha = piece_rgba.getchannel("A")
        sh = Image.new("RGBA", piece_rgba.size, (0, 0, 0, 0))
        sh.putalpha(alpha.point(lambda v: int(v * 0.42)).filter(ImageFilter.GaussianBlur(11)))
        # shadow is an under-layer: draw it into a transparent full-size layer
        shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        shadow_layer.paste(sh, (x0 + 12, y0 + 16), sh)
        canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), shadow_layer).convert("RGB"), (0, 0))

    # Work on a full-canvas transparent layer so negative/overflowing coords
    # are handled by Pillow rather than by manual crop arithmetic.
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    if mode != "normal":
        # blend against a copy of the canvas translated into layer space
        bg = Image.new("RGB", canvas.size, (255, 255, 255))
        bg.paste(canvas, (0, 0))
        region = Image.new("RGB", (pw, ph), (255, 255, 255))
        sx0, sy0 = max(0, x0), max(0, y0)
        sx1, sy1 = min(canvas.width, x0 + pw), min(canvas.height, y0 + ph)
        if sx1 > sx0 and sy1 > sy0:
            region.paste(bg.crop((sx0, sy0, sx1, sy1)), (sx0 - x0, sy0 - y0))
        region = blend_region(region, piece_rgba, mode, opacity)
        layer.paste(region.convert("RGBA"), (x0, y0), piece_rgba.getchannel("A").point(lambda v: int(v * opacity)))
    else:
        if opacity < 1.0:
            piece_rgba = piece_rgba.copy()
            piece_rgba.putalpha(piece_rgba.getchannel("A").point(lambda v: int(v * opacity)))
        layer.paste(piece_rgba, (x0, y0), piece_rgba)
    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), layer).convert("RGB"), (0, 0))
    return canvas


def text_piece(spec, w, h, rng, pal):
    """Render a headline as a cut-out typographic scrap.

    Glyphs are first drawn into a generous scratch layer, then cropped to their
    real ink bounds and fitted inside the requested box. This avoids the classic
    bug where a font's descenders get clipped by the box height.
    """
    text = spec.get("text", "")
    raw_color = spec.get("color", pal["ink"][0])
    color = rgb(raw_color) if str(raw_color).startswith("#") else rgb(pal["ink"][0])
    size = int(spec.get("size", min(h * 0.8, 100)))
    font = resolve_font(spec.get("font", "sans-bold"), size)
    tracking = int(spec.get("tracking", 0))
    probe = ImageDraw.Draw(Image.new("L", (1, 1)))
    widths = [probe.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * max(0, len(text) - 1)

    scratch_w = max(4, int(total + 40))
    scratch_h = max(4, int(size * 1.8))
    raw = Image.new("RGBA", (scratch_w, scratch_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(raw)
    bbox = d.textbbox((0, 0), "Hg", font=font)
    y = int(size * 0.32 - bbox[1])
    x = 20.0
    for ch, cw in zip(text, widths):
        if ch != " ":
            d.text((int(x), y), ch, font=font, fill=color + (255,))
        x += cw + tracking
    ink_box = raw.getchannel("A").getbbox()
    if ink_box:
        raw = raw.crop(ink_box)

    fit = min(1.0, (w - 6) / max(1, raw.width), (h - 6) / max(1, raw.height))
    if fit < 1.0:
        raw = raw.resize((max(1, int(raw.width * fit)), max(1, int(raw.height * fit))),
                         Image.Resampling.LANCZOS)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer.alpha_composite(raw, ((w - raw.width) // 2, (h - raw.height) // 2))

    if spec.get("cutout"):
        bg = Image.new("RGBA", (w, h), color + (255,))
        holes = Image.new("L", (w, h), 255)
        holes.paste(255 - layer.getchannel("A"), (0, 0))
        bg.putalpha(holes)
        layer = bg
    return layer


def add_tape(canvas, specs, rng, pal):
    for t in specs:
        x, y, w, h, ang = (list(t) + [0])[:5]
        c = mix(rgb(pal["paper"]), rgb("#d8c58c"), .55)
        strip = Image.new("RGBA", (int(w), int(h)), c + (150,))
        d = ImageDraw.Draw(strip)
        for _ in range(int(w / 3)):
            xx = rng.uniform(0, w)
            d.line([(xx, 0), (xx + rng.uniform(-4, 4), h)], fill=(255, 255, 255, 26), width=1)
        # torn ends
        m = Image.new("L", (int(w), int(h)), 255)
        md = ImageDraw.Draw(m)
        for yy in range(0, int(h), 3):
            md.line([(0, yy), (int(rng.integers(0, 8)), yy)], fill=0)
            md.line([(w - int(rng.integers(0, 8)), yy), (w, yy)], fill=0)
        strip.putalpha(Image.new("L", strip.size, 150))
        strip = strip.rotate(ang, resample=Image.Resampling.BICUBIC, expand=True)
        canvas.paste(strip, (int(x - strip.width / 2), int(y - strip.height / 2)), strip)
    return canvas


def add_marks(canvas, rng, pal, density=1.0):
    w, h = canvas.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ink = rgb(pal["ink"][0]) + (150,)
    for _ in range(int(9 * density)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.uniform(18, 80)
        d.arc([x - r, y - r, x + r, y + r], rng.uniform(0, 200), rng.uniform(220, 380), fill=ink, width=2)
    for _ in range(int(7 * density)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        d.line([(x, y), (x + rng.uniform(30, 130), y + rng.uniform(-30, 30))], fill=ink, width=1)
    for _ in range(int(5 * density)):
        x, y = rng.uniform(20, w - 20), rng.uniform(20, h - 20)
        d.line([(x - 9, y), (x + 9, y)], fill=ink, width=1)
        d.line([(x, y - 9), (x, y + 9)], fill=ink, width=1)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=ink, width=1)
    for _ in range(int(24 * density)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.uniform(0.6, 3.2)
        d.ellipse([x - r, y - r, x + r, y + r], fill=ink)
    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), layer).convert("RGB"), (0, 0))
    return canvas


def render(recipe):
    w = int(recipe.get("width", 1200))
    h = int(recipe.get("height", 1600))
    seed = int(recipe.get("seed", 1))
    rng = np.random.default_rng(seed)
    pal = PALETTES.get(recipe.get("paper", "cream"), PALETTES["cream"])
    canvas = paper_base(w, h, pal["paper"], rng)

    for spec in recipe.get("pieces", []):
        x, y, pw, ph = spec["box"]
        angle = float(spec.get("rotate", 0))
        if spec.get("backing"):
            paste_piece(canvas, Image.new("RGBA", (int(pw) + 16, int(ph) + 16),
                                         rgb(pal["paper"]) + (238,)),
                        x + pw / 2, y + ph / 2, angle, False, rng)
        if "text" in spec:
            layer = text_piece(spec, int(pw), int(ph), rng, pal)
            if spec.get("mask"):
                layer.putalpha(ImageChops_multiply(layer.getchannel("A"), make_mask(spec["mask"], layer.width, layer.height, rng)))
        else:
            mask = spec.get("mask", "cut")
            if mask in ("alpha", "content", "retain-alpha"):
                # Keep the cut made from the photograph's visible structure.
                src = alpha_source(spec, int(pw), int(ph), rng, pal)
                a = src.getchannel("A")
            else:
                src = source_image(spec, int(pw), int(ph), rng, pal).convert("RGBA")
                a = make_mask(mask, int(pw), int(ph), rng)
                src.putalpha(a)
            layer = src
        paste_piece(canvas, layer, x + pw / 2, y + ph / 2, angle,
                    bool(spec.get("shadow", False)), rng,
                    spec.get("blend", "normal"), float(spec.get("opacity", 1.0)))

    if recipe.get("tape"):
        canvas = add_tape(canvas, recipe["tape"], rng, pal)
    if recipe.get("marks"):
        canvas = add_marks(canvas, rng, pal, float(recipe.get("mark_density", 1.0)))
    canvas = grain_overlay(canvas, rng, strength=float(recipe.get("finish_grain", 5)))
    # unified warm print wash ties unrelated scraps into one sheet
    wash = Image.new("RGB", (w, h), mix(rgb(pal["paper"]), rgb("#c9b48c"), .5))
    canvas = Image.blend(canvas, wash, 0.045)
    return canvas


def ImageChops_multiply(a, b):
    from PIL import ImageChops
    return ImageChops.multiply(a, b)


# ---------------------------------------------------------------------------
# Presets. Each one encodes a different art-historical strategy, not just a
# different colour scheme. See references/movements.md for the reasoning.
# ---------------------------------------------------------------------------

PRESETS = {
    "cubist-grid": {
        "width": 1200, "height": 1500, "paper": "cream", "seed": 3, "marks": True,
        "pieces": [
            {"source": "wood", "box": [90, 110, 650, 520], "rotate": -3, "mask": "torn", "shadow": True},
            {"source": "newsprint", "box": [560, 260, 520, 620], "rotate": 5, "blend": "multiply", "shadow": True},
            {"source": "grid", "box": [180, 560, 760, 560], "rotate": -6, "mask": "cut", "shadow": True},
            {"source": "solid", "palette": ["#c8412f"], "box": [740, 700, 330, 330], "rotate": 12, "mask": "circle"},
            {"source": "type", "char": "R", "box": [200, 930, 380, 380], "rotate": -8, "shadow": True},
            {"text": "PAPIER COLLE", "box": [120, 1290, 980, 120], "font": "sans-cond", "size": 108, "tracking": 12},
        ],
        "tape": [[880, 480, 190, 48, -14]],
    },
    "dada-montage": {
        "width": 1200, "height": 1500, "paper": "newsprint", "seed": 7, "marks": True, "mark_density": 1.6,
        "pieces": [
            {"source": "photo", "palette": ["#3a5f8a", "#e5e0d3", "#b23a2c"], "box": [150, 120, 900, 700], "rotate": -7, "mask": "torn", "shadow": True},
            {"source": "type", "char": "D", "box": [720, 300, 340, 340], "rotate": 18, "mask": "circle"},
            {"source": "newsprint", "box": [560, 820, 560, 420], "rotate": -11, "shadow": True},
            {"text": "DADA", "box": [180, 620, 840, 200], "font": "sans-cond", "size": 190, "tracking": 22, "color": "#b23a2c", "rotate": -4, "shadow": True},
            {"source": "solid", "palette": ["#b23a2c"], "box": [80, 740, 520, 180], "rotate": 4, "mask": "strip"},
            {"text": "MONTEUR  ·  1920", "box": [180, 1300, 840, 80], "font": "mono", "size": 46, "tracking": 8},
        ],
    },
    "surreal-arch": {
        "width": 1100, "height": 1500, "paper": "cold", "seed": 12,
        "pieces": [
            {"source": "gradient", "palette": ["#16283a", "#4a86a8"], "box": [250, 160, 600, 900], "mask": "arch", "shadow": True},
            {"source": "halftone", "palette": ["#d94f36"], "box": [330, 320, 440, 440], "mask": "circle", "rotate": 0},
            {"source": "photo", "palette": ["#f0c94b", "#e8ecea", "#16283a"], "box": [90, 880, 920, 380], "rotate": -3, "mask": "torn", "shadow": True},
            {"source": "solid", "palette": ["#16283a"], "box": [470, 980, 160, 310], "rotate": 22},
            {"text": "A DREAM OF PAPER", "box": [110, 1350, 900, 90], "font": "serif-italic", "size": 62, "tracking": 5},
        ],
        "tape": [[550, 240, 170, 42, 8]],
    },
    "pop-halftone": {
        "width": 1200, "height": 1200, "paper": "pink", "seed": 21, "marks": True,
        "pieces": [
            {"source": "halftone", "palette": ["#e0446d"], "cell": 12, "box": [0, 0, 1200, 1200], "opacity": .55},
            {"source": "photo", "palette": ["#2e4f9e", "#f2b13c", "#241a20"], "box": [220, 180, 760, 760], "mask": "circle", "rotate": 0, "shadow": True},
            {"source": "solid", "palette": ["#f2b13c"], "box": [80, 820, 480, 200], "rotate": -6, "mask": "strip"},
            {"text": "WOW!", "box": [500, 830, 620, 230], "font": "sans-cond", "size": 210, "color": "#e0446d", "rotate": 5},
            {"source": "solid", "palette": ["#f3dfd8"], "box": [90, 1070, 1020, 96]},
            {"text": "JUST ADD GLUE", "box": [110, 1080, 980, 70], "font": "mono-bold", "size": 44, "tracking": 10},
        ],
    },
    "decollage-poster": {
        "width": 1100, "height": 1500, "paper": "kraft", "seed": 33, "mark_density": .7, "marks": True,
        "pieces": [
            {"source": "stripes", "palette": ["#8d3b2a", "#e8ddc2"], "band": 46, "box": [0, 0, 1100, 1500], "opacity": .55},
            {"source": "newsprint", "box": [110, 180, 800, 520], "rotate": -5, "mask": "torn", "blend": "multiply", "shadow": True},
            {"source": "solid", "palette": ["#3f5d55"], "box": [300, 560, 700, 400], "rotate": 7, "mask": "torn", "shadow": True},
            {"source": "kraft", "box": [60, 900, 960, 360], "rotate": -3, "mask": "strip", "shadow": True},
            {"text": "AFFICHE", "box": [140, 1010, 830, 180], "font": "serif-bold", "size": 140, "color": "#2b211a", "rotate": -3},
        ],
        "tape": [[820, 700, 220, 50, -12], [250, 1180, 180, 44, 9]],
    },
    "riso-editorial": {
        "width": 1200, "height": 1600, "paper": "cream", "seed": 5,
        "pieces": [
            {"source": "solid", "palette": ["#234a78"], "box": [80, 90, 1040, 300], "rotate": 0},
            {"text": "CUT", "box": [120, 130, 960, 210], "font": "sans-cond", "size": 200, "color": "#f2e9d6", "tracking": 26},
            {"source": "grid", "box": [80, 430, 500, 560], "rotate": -4, "halftone": True, "shadow": True},
            {"source": "photo", "palette": ["#c8412f", "#f2e9d6", "#234a78"], "box": [620, 430, 500, 560], "rotate": 4, "shadow": True},
            {"source": "newsprint", "box": [80, 1030, 1040, 300], "blend": "multiply", "mask": "torn"},
            {"text": "&  PASTE", "box": [110, 1370, 980, 140], "font": "serif-italic", "size": 100, "tracking": 8},
        ],
    },
    "analog-scrapbook": {
        "width": 1200, "height": 1000, "paper": "black", "seed": 9, "marks": True,
        "pieces": [
            {"source": "stamp", "palette": ["#f0e6d2", "#e4543a", "#6f9fc4"], "box": [120, 110, 330, 330], "rotate": -9, "shadow": True},
            {"source": "photo", "palette": ["#6f9fc4", "#1c1b1a", "#e3b64a"], "box": [430, 150, 620, 560], "rotate": 6, "mask": "torn", "shadow": True},
            {"source": "type", "char": "E", "box": [150, 520, 280, 300], "rotate": 4, "shadow": True},
            {"text": "EPOCH", "box": [500, 730, 620, 130], "font": "sans-cond", "size": 110, "color": "#f0e6d2", "tracking": 16},
        ],
        "tape": [[330, 300, 200, 46, 12], [800, 640, 180, 44, -8]],
    },
    "bauhaus-balance": {
        "width": 1200, "height": 1500, "paper": "cream", "seed": 41,
        "pieces": [
            {"source": "solid", "palette": ["#234a78"], "box": [120, 130, 420, 660], "rotate": -2},
            {"source": "solid", "palette": ["#c8412f"], "box": [560, 200, 460, 460], "mask": "circle", "rotate": 0},
            {"source": "solid", "palette": ["#d8a02c"], "box": [640, 680, 380, 620], "mask": "triangle", "rotate": 6},
            {"source": "stripes", "palette": ["#1d1a17", "#f2e9d6"], "band": 22,
             "box": [110, 830, 500, 420], "rotate": -7, "shadow": True},
            {"text": "FORM", "box": [130, 1310, 940, 120], "font": "sans-cond", "size": 104, "tracking": 18},
        ],
        "tape": [[560, 660, 170, 42, -12]],
    },
    "punk-fanzine": {
        "width": 1100, "height": 1500, "paper": "newsprint", "seed": 47, "marks": True, "mark_density": 2.0,
        "pieces": [
            {"source": "newsprint", "box": [0, 0, 1100, 1500], "opacity": .55},
            {"source": "solid", "palette": ["#1d1a17"], "box": [80, 170, 940, 300], "rotate": -3, "mask": "torn"},
            {"text": "NOISE", "box": [110, 200, 880, 220], "font": "sans-cond", "size": 190,
             "color": "#f2e9d6", "tracking": 14, "rotate": -3},
            {"source": "photo", "palette": ["#c8412f", "#26241f", "#e5e0d3"],
             "box": [130, 540, 820, 620], "rotate": 5, "mask": "torn", "shadow": True},
            {"source": "solid", "palette": ["#c8412f"], "box": [60, 1120, 520, 150], "rotate": -8, "mask": "strip"},
            {"text": "CUT IT OUT", "box": [120, 1280, 880, 110], "font": "mono-bold", "size": 76, "tracking": 6},
        ],
        "tape": [[800, 560, 210, 46, 14]],
    },
    "photomontage-scale": {
        "width": 1200, "height": 1500, "paper": "cold", "seed": 53, "marks": True,
        "pieces": [
            {"source": "type", "char": "A", "box": [80, 100, 560, 620], "rotate": -6, "shadow": True},
            {"source": "halftone", "palette": ["#16283a"], "cell": 10,
             "box": [560, 180, 560, 560], "mask": "circle", "rotate": 0},
            {"source": "newsprint", "box": [180, 700, 420, 520], "rotate": 9, "blend": "multiply", "shadow": True},
            {"source": "photo", "palette": ["#d94f36", "#e8ecea", "#4a86a8"],
             "box": [560, 720, 540, 420], "rotate": -11, "mask": "torn", "shadow": True},
            {"text": "SCALE", "box": [140, 1250, 920, 150], "font": "sans-cond", "size": 140, "tracking": 20},
        ],
    },
    "ticket-stub": {
        "width": 1200, "height": 900, "paper": "kraft", "seed": 59, "marks": True,
        "pieces": [
            {"source": "stamp", "palette": ["#2b211a", "#8d3b2a", "#e8ddc2"],
             "box": [110, 110, 330, 330], "rotate": -8, "shadow": True},
            {"source": "stamp", "palette": ["#3f5d55", "#cdb08a", "#e8ddc2"],
             "box": [450, 150, 620, 380], "rotate": 4, "shadow": True},
            {"source": "newsprint", "box": [130, 480, 940, 240], "rotate": -3, "mask": "torn", "blend": "multiply"},
            {"text": "ADMIT ONE", "box": [470, 260, 580, 120], "font": "serif-bold", "size": 86, "color": "#e8ddc2", "tracking": 6},
        ],
        "tape": [[900, 420, 190, 44, 9]],
    },
    "cutout-letter": {
        "width": 1100, "height": 1400, "paper": "pink", "seed": 61,
        "pieces": [
            {"source": "wood", "palette": ["#2e4f9e", "#f3dfd8"], "box": [80, 90, 940, 940], "rotate": -2, "shadow": True},
            {"source": "solid", "palette": ["#e0446d"], "box": [250, 260, 600, 600], "mask": "circle", "rotate": 0},
            {"source": "type", "char": "C", "box": [330, 330, 440, 460], "rotate": 0},
            {"source": "solid", "palette": ["#f2b13c"], "box": [80, 1050, 520, 150], "rotate": -5, "mask": "strip"},
            {"text": "COLLAGE", "box": [110, 1190, 900, 130], "font": "serif-bold", "size": 96, "tracking": 10},
        ],
    },
    "two-ink-riso": {
        "width": 1200, "height": 1200, "paper": "cream", "seed": 67,
        "pieces": [
            {"source": "halftone", "palette": ["#234a78"], "cell": 14, "angle": 45,
             "box": [0, 0, 1200, 1200], "opacity": .5},
            {"source": "solid", "palette": ["#c8412f"], "box": [180, 180, 480, 480], "mask": "arch", "rotate": -4},
            {"source": "halftone", "palette": ["#234a78"], "cell": 9, "angle": 45,
             "box": [560, 430, 460, 460], "mask": "circle", "rotate": 0, "opacity": .88},
            {"source": "stripes", "palette": ["#1d1a17", "#f2e9d6"], "band": 18,
             "box": [180, 720, 840, 260], "rotate": 3, "mask": "torn"},
            {"text": "2 INKS", "box": [200, 1030, 800, 110], "font": "sans-cond", "size": 100, "tracking": 16},
        ],
    },
    "assemblage-depth": {
        "width": 1200, "height": 1400, "paper": "black", "seed": 71, "marks": True,
        "pieces": [
            {"source": "kraft", "box": [160, 130, 620, 520], "rotate": -7, "shadow": True},
            {"source": "wood", "palette": ["#6f9fc4", "#1c1b1a"], "box": [560, 420, 520, 520],
             "rotate": 12, "mask": "torn", "shadow": True},
            {"source": "stamp", "palette": ["#f0e6d2", "#e4543a", "#6f9fc4"],
             "box": [200, 760, 300, 300], "rotate": -14, "shadow": True},
            {"source": "solid", "palette": ["#e3b64a"], "box": [620, 880, 380, 380], "mask": "diamond", "rotate": 5,
             "shadow": True},
            {"text": "OBJECTS", "box": [130, 1240, 940, 110], "font": "sans-cond", "size": 100,
             "color": "#f0e6d2", "tracking": 16},
        ],
        "tape": [[480, 660, 200, 46, -9]],
    },
    "dada-heartfield": {
        "width": 1200, "height": 1400, "paper": "newsprint", "seed": 73, "marks": True, "mark_density": 1.3,
        "pieces": [
            {"source": "newsprint", "box": [0, 0, 1200, 1400], "opacity": .6},
            {"source": "type", "char": "H", "box": [90, 100, 500, 540], "rotate": -9, "mask": "circle", "shadow": True},
            {"source": "photo", "palette": ["#b23a2c", "#26241f", "#e5e0d3"],
             "box": [520, 260, 620, 640], "rotate": 8, "mask": "torn", "shadow": True},
            {"text": "MONTEUR", "box": [100, 880, 1000, 190], "font": "sans-cond", "size": 150,
             "color": "#b23a2c", "tracking": 12, "rotate": -3, "shadow": True},
            {"source": "solid", "palette": ["#26241f"], "box": [80, 1090, 1040, 90], "rotate": 2, "mask": "strip"},
        ],
    },
    "surreal-window": {
        "width": 1100, "height": 1400, "paper": "cold", "seed": 79,
        "pieces": [
            {"source": "solid", "palette": ["#4a86a8"], "box": [140, 120, 820, 900], "rotate": 0, "shadow": True},
            {"source": "gradient", "palette": ["#16283a", "#f0c94b"],
             "box": [260, 240, 580, 660], "mask": "arch", "rotate": 0},
            {"source": "halftone", "palette": ["#d94f36"], "cell": 12,
             "box": [400, 380, 300, 300], "mask": "circle", "rotate": 0},
            {"source": "solid", "palette": ["#e8ecea"], "box": [80, 1020, 940, 180], "rotate": -2, "mask": "torn"},
            {"text": "ELSEWHERE", "box": [130, 1060, 860, 110], "font": "serif-italic", "size": 82, "tracking": 8},
        ],
    },
}


def main():
    ap = argparse.ArgumentParser(description="Render a deterministic paper collage.")
    ap.add_argument("--list", action="store_true", help="list available presets")
    ap.add_argument("--preset", help="preset name")
    ap.add_argument("--recipe", help="path to a JSON recipe")
    ap.add_argument("--out", default="collage.png")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--dump", help="write the resolved recipe to this JSON file")
    args = ap.parse_args()

    if args.list:
        for k, v in PRESETS.items():
            print("%-20s %4dx%-4d  seed=%s  pieces=%d" %
                  (k, v["width"], v["height"], v.get("seed", 1), len(v.get("pieces", []))))
        return
    recipe_dir = None
    if args.recipe:
        recipe_path = os.path.abspath(args.recipe)
        recipe_dir = os.path.dirname(recipe_path)
        with open(recipe_path, encoding="utf-8") as f:
            recipe = json.load(f)
        # Relative image paths in a hand-written recipe belong beside the
        # recipe, not to whatever directory the user happened to launch from.
        for piece in recipe.get("pieces", []):
            source = piece.get("source")
            if isinstance(source, str) and ("/" in source or os.sep in source or
                                            source.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))):
                if not os.path.isabs(source) and not os.path.isfile(source):
                    candidate = os.path.join(recipe_dir, source)
                    if os.path.isfile(candidate):
                        piece["source"] = candidate
    elif args.preset:
        if args.preset not in PRESETS:
            sys.exit("unknown preset %r (try --list)" % args.preset)
        recipe = json.loads(json.dumps(PRESETS[args.preset]))
    else:
        ap.print_help()
        return
    if args.seed is not None:
        recipe["seed"] = args.seed
    if args.dump:
        with open(args.dump, "w", encoding="utf-8") as f:
            json.dump(recipe, f, ensure_ascii=False, indent=2)
    img = render(recipe)
    if args.scale != 1.0:
        img = img.resize((int(img.width * args.scale), int(img.height * args.scale)), Image.Resampling.LANCZOS)
    img.save(args.out)
    print("wrote %s (%dx%d, seed=%s)" % (args.out, img.width, img.height, recipe.get("seed", 1)))


if __name__ == "__main__":
    main()
