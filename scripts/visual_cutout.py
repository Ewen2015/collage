#!/usr/bin/env python3
"""Cut source photographs into transparent, content-shaped collage scraps.

This is deliberately small. The skill is a collage maker, not an image
segmentation library. The agent looks at a source photograph and describes the
part worth cutting with a normalized polygon (`shape`). A simple `silhouette`
mode can also remove a plain border/background. Both use Pillow + NumPy only.

Modes
-----
  shape       Cut an explicit, hand-observed contour. Coordinates are x,y pairs
              normalized to 0–1: "0,.1;1,0;.9,1;0,.9". This is the main mode.
  silhouette  Remove a plain background by colour distance from the image
              border. Best for isolated objects on white/neutral paper.

Examples
--------
  python3 scripts/visual_cutout.py --input photo.jpg --out semantic.png \
      --mode shape --shape "0,.1;1,0;.9,1;0,.9"
  python3 scripts/visual_cutout.py --input object.jpg --out object.png \
      --mode silhouette

`--contact-sheet` draws the cutout over a checkerboard for visual review.

Requires Python 3.9+, Pillow and NumPy.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


# ---------------------------------------------------------------------------
# Basic image helpers
# ---------------------------------------------------------------------------

def load_rgb(path):
    return np.asarray(Image.open(path).convert("RGB"))


def feather_mask(mask, radius=1.2):
    """Clean a binary alpha mask and give its edge a soft, cut-paper feel."""
    im = Image.fromarray(np.clip(mask, 0, 255).astype(np.uint8), "L")
    if radius > 0:
        im = im.filter(ImageFilter.GaussianBlur(radius))
    return np.asarray(im)


def largest_component(mask):
    """Keep only the largest 4-connected opaque region, using a small BFS."""
    from collections import deque
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    best = []
    ys, xs = np.where(mask > 8)
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        q = deque([(int(y0), int(x0))])
        seen[y0, x0] = True
        comp = []
        while q:
            y, x = q.popleft()
            comp.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and mask[ny, nx] > 8:
                    seen[ny, nx] = True
                    q.append((ny, nx))
        if len(comp) > len(best):
            best = comp
    out = np.zeros((h, w), dtype=np.uint8)
    for y, x in best:
        out[y, x] = 255
    return out


def crop_alpha(rgb, alpha, margin=10):
    """Crop RGBA to alpha bounds and return the image plus its source box."""
    ys, xs = np.where(alpha > 8)
    if not len(xs):
        raise ValueError("cutout is empty — adjust the shape or silhouette threshold")
    x0, x1 = max(0, int(xs.min()) - margin), min(rgb.shape[1], int(xs.max()) + margin + 1)
    y0, y1 = max(0, int(ys.min()) - margin), min(rgb.shape[0], int(ys.max()) + margin + 1)
    rgba = np.dstack([rgb[y0:y1, x0:x1], alpha[y0:y1, x0:x1]])
    return Image.fromarray(rgba, "RGBA"), [x0, y0, x1, y1]


def coverage(alpha):
    return float((alpha > 32).mean())


# ---------------------------------------------------------------------------
# Two lightweight cuts
# ---------------------------------------------------------------------------

def shape_mask(rgb, points, feather=1.2):
    """Use an explicit, hand-observed polygon as a content-following cut.

    The agent looks at the source photograph and names the contour of a real
    object or structural region. Coordinates are normalized to image width and
    height, so the same instruction survives resizing. This is the digital
    equivalent of a scalpel: cut around the thing, not around the rectangle.
    """
    if len(points) < 3:
        raise ValueError("--shape needs at least three normalized x,y pairs")
    h, w = rgb.shape[:2]
    poly = [(float(x) * (w - 1), float(y) * (h - 1)) for x, y in points]
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    return feather_mask(np.asarray(mask), feather)


def silhouette_mask(rgb, min_area=.05, threshold=38):
    """Remove a plain border/background by colour distance.

    This is intentionally a simple paper-background estimator. For busy
    photographs, prefer `shape` and name the visible contour yourself.
    """
    h, w = rgb.shape[:2]
    band = max(4, min(h, w) // 80)
    border = np.concatenate([
        rgb[:band].reshape(-1, 3), rgb[-band:].reshape(-1, 3),
        rgb[:, :band].reshape(-1, 3), rgb[:, -band:].reshape(-1, 3),
    ])
    bg = np.median(border, axis=0)
    dist = np.linalg.norm(rgb.astype(np.float32) - bg, axis=2)
    alpha = (dist > threshold).astype(np.uint8) * 255
    # A small cross-shaped close fills pinholes without extra libraries.
    filled = alpha.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        shifted = np.roll(alpha, (dy, dx), axis=(0, 1))
        filled = np.maximum(filled, shifted)
    alpha = largest_component(filled)
    if (alpha > 32).mean() < min_area:
        raise ValueError("silhouette too small; use --mode shape with a polygon")
    return feather_mask(alpha, 1.0)


# ---------------------------------------------------------------------------
# Output and review
# ---------------------------------------------------------------------------

@dataclass
class Report:
    input: str
    mode: str
    outputs: list
    source_size: list
    notes: dict


def checkerboard(size, square=18):
    w, h = size
    im = Image.new("RGB", (w, h), "#eeeae1")
    d = ImageDraw.Draw(im)
    for y in range(0, h, square):
        for x in range(0, w, square):
            if (x // square + y // square) % 2:
                d.rectangle([x, y, x + square, y + square], fill="#d8d4ca")
    return im


def make_contact_sheet(images, out, labels=None):
    thumb_w, thumb_h = 320, 260
    pad = 18
    cols = min(3, len(images))
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (thumb_w + pad) + pad,
                              rows * (thumb_h + pad + 24) + pad), "#f2efe8")
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(images):
        t = im.copy()
        t.thumbnail((thumb_w, thumb_h))
        x = pad + (i % cols) * (thumb_w + pad)
        y = pad + (i // cols) * (thumb_h + pad + 24)
        bg = checkerboard((thumb_w, thumb_h)).convert("RGBA")
        bg.alpha_composite(t, ((thumb_w - t.width) // 2, (thumb_h - t.height) // 2))
        sheet.paste(bg.convert("RGB"), (x, y))
        d.text((x, y + thumb_h + 4), (labels or [])[i] if labels else str(i + 1),
               fill="#222")
    sheet.save(out, quality=90)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", default="shape", choices=["shape", "silhouette"])
    ap.add_argument("--shape", help="shape-mode polygon: x,y;x,y;... normalized 0–1")
    ap.add_argument("--min-area", type=float, default=.02,
                    help="silhouette minimum retained area (fraction of image)")
    ap.add_argument("--threshold", type=float, default=38,
                    help="silhouette colour distance from border background")
    # Accepted for compatibility with older concepts/recipes; ignored here.
    ap.add_argument("--polarity", choices=["dark", "light", "auto"])
    ap.add_argument("--seed")
    ap.add_argument("--target-area", type=float)
    ap.add_argument("--sensitivity", type=float)
    ap.add_argument("--angle")
    ap.add_argument("--thickness", type=float)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--fallback")
    ap.add_argument("--contact-sheet", help="optional JPG contact sheet path")
    ap.add_argument("--report", help="optional JSON analysis report path")
    args = ap.parse_args()

    rgb = load_rgb(args.input)
    notes = {}

    if args.mode == "shape":
        if not args.shape:
            raise ValueError("--mode shape requires --shape x,y;x,y;...")
        pts = []
        for part in args.shape.split(";"):
            xy = part.split(",")
            if len(xy) != 2:
                raise ValueError("invalid --shape point: %r" % part)
            pts.append((float(xy[0]), float(xy[1])))
        alpha = shape_mask(rgb, pts)
        notes["polygon"] = pts
    else:
        alpha = silhouette_mask(rgb, args.min_area, args.threshold)
        notes["background_threshold"] = args.threshold

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    im, box = crop_alpha(rgb, alpha)
    im.save(args.out)
    report = Report(input=os.path.abspath(args.input), mode=args.mode,
                    outputs=[{"file": os.path.abspath(args.out), "source_box": box,
                              "size": list(im.size),
                              "coverage": round(coverage(alpha), 4)}],
                    source_size=[int(rgb.shape[1]), int(rgb.shape[0])], notes=notes)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, ensure_ascii=False, indent=2)
    if args.contact_sheet:
        make_contact_sheet([im], args.contact_sheet, [os.path.basename(args.out)])
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
