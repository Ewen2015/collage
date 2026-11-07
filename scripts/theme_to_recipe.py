#!/usr/bin/env python3
"""
theme_to_recipe.py — turn a concept + sourced images into a renderable recipe.

The creative step (reading the user's text, choosing a historical strategy,
writing the pairing sentence and the motif list) is done by the agent following
SKILL.md. This script is the deterministic half: it lays those decisions out as
a collage.py recipe, choosing a composition system, layer order, edges,
rotations, type and tape, and binding the downloaded assets to the pieces.

Usage
-----
    python3 theme_to_recipe.py --concept concept.json --assets assets/session-01 \
        --recipe out/recipe.json --cutouts out/cuts \
        [--seed 11] [--format poster|editorial|square|banner]

It also emits a rationale file (out/rationale.md): the design decisions in plain
language, so the output can be explained and revised.

Requires: Python stdlib, plus Pillow / NumPy for the cutout step.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

# Each movement carries its own defaults. These are the art-historical rules
# from references/movements.md expressed as layout parameters.
STRATEGIES = {
    "cubism":     {"paper": "cream", "blend": "multiply", "rotate": (-8, 8),
                   "edges": ["cut", "torn", "cut"], "font": "serif-bold", "marks": 0.9, "tape": 1},
    "dada":       {"paper": "newsprint", "blend": "normal", "rotate": (-19, 19),
                   "edges": ["torn", "strip", "cut"], "font": "sans-cond", "marks": 1.5, "tape": 1},
    "surrealism": {"paper": "cold", "blend": "normal", "rotate": (-6, 6),
                   "edges": ["arch", "circle", "torn"], "font": "serif-italic", "marks": 0.3, "tape": 1},
    "pop":        {"paper": "pink", "blend": "normal", "rotate": (-7, 7),
                   "edges": ["circle", "strip", "cut"], "font": "sans-cond", "marks": 0.8, "tape": 0},
    "decollage":  {"paper": "kraft", "blend": "multiply", "rotate": (-9, 9),
                   "edges": ["torn", "strip", "torn"], "font": "serif-bold", "marks": 0.7, "tape": 2},
    "editorial":  {"paper": "cream", "blend": "normal", "rotate": (-5, 5),
                   "edges": ["cut", "torn", "cut"], "font": "sans-cond", "marks": 0.4, "tape": 0},
}

FORMATS = {
    "poster":    (1200, 1500),
    "editorial": (1200, 1600),
    "square":    (1200, 1200),
    "banner":    (1600, 900),
}


def jitter(seed, lo, hi, n, salt=0):
    """Small deterministic pseudo-random numbers, no numpy dependency."""
    out = []
    x = seed * 1103515245 + salt * 12345 + 271828
    for _ in range(n):
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        out.append(lo + (hi - lo) * (x / 0x7FFFFFFF))
    return out


def pick(seq, i):
    return seq[i % len(seq)]


CUTOUT_METHODS = ("shape", "silhouette")


def cut_commands(a, cut_dir, index, concept=None):
    """Return lightweight content-cut commands for one source asset.

    Shape cuts are explicit polygons observed by the agent; silhouette cuts
    remove a plain border/background. Both run with Pillow + NumPy only.
    """
    raw = a.get("cut")
    if raw is None:
        raw = (concept or {}).get("cut_default",
                                  {"mode": "shape",
                                   "shape": "0.06,0.06;0.94,0.03;0.98,0.94;0.04,0.97"})
    items = raw if isinstance(raw, list) else [raw]
    commands, specs = [], []
    for j, item in enumerate(items):
        d = {"mode": item} if isinstance(item, str) else dict(item or {})
        mode = d.get("mode", "shape")
        if mode not in CUTOUT_METHODS:
            raise ValueError("unknown cut mode %r for %s; use shape or silhouette" %
                             (mode, a.get("id")))
        if mode == "shape" and not d.get("shape"):
            raise ValueError("shape cut for %s needs a normalized polygon" % a.get("id"))
        out = os.path.abspath(os.path.join(
            cut_dir, "%s-%02d.png" % (a.get("id", "asset-%d" % index), j + 1)))
        cmd = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "visual_cutout.py"),
               "--input", os.path.abspath(os.path.join(a["_dir"], a["file"])),
               "--out", out, "--mode", mode]
        for flag, key in (("--shape", "shape"),
                          ("--min-area", "min_area"),
                          ("--threshold", "threshold"),
                          ("--fallback", "fallback"),
                          ("--polarity", "polarity"),
                          ("--seed", "seed"),
                          ("--target-area", "target_area"),
                          ("--sensitivity", "sensitivity"),
                          ("--angle", "angle"),
                          ("--thickness", "thickness"),
                          ("--limit", "limit")):
            if key in d:
                cmd += [flag, str(d[key])]
        commands.append(cmd)
        specs.append({"source": out, "mask": "alpha", "cut": d,
                      "original": a["file"], "mode": mode})
    return commands, specs


def make_cut_sheet(cut_dir):
    """Write a small contact sheet so the agent can actually inspect the cuts."""
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return None
    files = sorted(os.path.join(cut_dir, f) for f in os.listdir(cut_dir)
                   if f.lower().endswith(".png"))
    if not files:
        return None
    tw, th, pad, label_h = 300, 230, 16, 24
    cols = min(3, len(files))
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + pad) + pad,
                              rows * (th + label_h + pad) + pad), "#eeeae1")
    d = ImageDraw.Draw(sheet)
    for i, path in enumerate(files):
        im = Image.open(path).convert("RGBA")
        im.thumbnail((tw, th))
        x = pad + (i % cols) * (tw + pad)
        y = pad + (i // cols) * (th + label_h + pad)
        bg = Image.new("RGBA", (tw, th), "#d8d4ca")
        bg.alpha_composite(im, ((tw - im.width) // 2, (th - im.height) // 2))
        sheet.paste(bg.convert("RGB"), (x, y))
        d.text((x, y + th + 4), os.path.basename(path), fill="#222")
    out = os.path.join(cut_dir, "contact-sheet.jpg")
    sheet.save(out, quality=90)
    return out


def build(concept, assets, fmt, seed, job_dir=None, cut_dir=None, run_cuts=True):
    W, H = FORMATS[fmt]
    key = concept.get("strategy", "editorial")
    if key not in STRATEGIES:
        raise ValueError("unknown strategy %r; choose from %s" % (key, ", ".join(STRATEGIES)))
    s = STRATEGIES[key]
    palette = concept.get("palette", [])
    inks = palette if len(palette) >= 2 else ["#1d1a17", "#c8412f", "#234a78", "#d8a02c"]

    # Layout slots by composition system. Anchor is always the hero motif.
    if key == "surrealism":
        # Headline band needs the lower ~15% clear, so keep all scraps above .74H.
        slots = [[int(W * .20), int(H * .09), int(W * .60), int(H * .48)],
                 [int(W * .08), int(H * .57), int(W * .84), int(H * .15)],
                 [int(W * .44), int(H * .60), int(W * .11), int(H * .14)]]
    elif key == "cubism":
        slots = [[int(W * .08), int(H * .07), int(W * .55), int(H * .36)],
                 [int(W * .47), int(H * .18), int(W * .44), int(H * .42)],
                 [int(W * .15), int(H * .37), int(W * .63), int(H * .38)],
                 [int(W * .62), int(H * .47), int(W * .26), int(H * .20)]]
    elif key == "pop":
        slots = [[int(W * .18), int(H * .13), int(W * .64), int(H * .62)],
                 [int(W * .06), int(H * .68), int(W * .40), int(H * .14)],
                 [int(W * .55), int(H * .60), int(W * .39), int(H * .18)]]
    elif fmt == "banner":
        slots = [[int(W * .04), int(H * .10), int(W * .52), int(H * .80)],
                 [int(W * .60), int(H * .12), int(W * .20), int(H * .36)],
                 [int(W * .82), int(H * .48), int(W * .16), int(H * .38)]]
    else:  # editorial / dada / decollage
        slots = [[int(W * .10), int(H * .08), int(W * .76), int(H * .47)],
                 [int(W * .06), int(H * .48), int(W * .44), int(H * .18)],
                 [int(W * .47), int(H * .52), int(W * .47), int(H * .28)],
                 [int(W * .08), int(H * .68), int(W * .84), int(H * .20)]]

    # Bind assets to pieces. Preserve hero-first order from the manifest.
    # Content-aware cuts are mandatory for sourced photographs: a rectangular
    # photo window is no longer the default. Each command is executed here so
    # the generated transparent PNG is ready before the recipe is rendered.
    if job_dir is None:
        job_dir = "."
    if cut_dir is None:
        cut_dir = os.path.join(job_dir, "cuts")
    if run_cuts:
        os.makedirs(cut_dir, exist_ok=True)
    by_role = {}
    for a in assets:
        by_role.setdefault(a.get("role", "satellite"), []).append(a)
    ordered = by_role.get("hero", []) + by_role.get("ground", []) + by_role.get("satellite", [])
    resolved, commands = [], []
    for i, a in enumerate(ordered):
        cmds, specs = cut_commands(a, cut_dir, i, concept)
        commands.extend(cmds)
        resolved.append(specs)
    if run_cuts:
        for cmd in commands:
            print("content cut: " + " ".join(cmd), file=sys.stderr)
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        make_cut_sheet(cut_dir)
    flat = [src for group in resolved for src in group]

    rots = jitter(seed, s["rotate"][0], s["rotate"][1], max(1, len(flat) + len(slots)))
    pieces = []
    for i, slot in enumerate(slots):
        a = flat[i] if i < len(flat) else None
        edge = a.get("mask", pick(s["edges"], i)) if a else pick(s["edges"], i)
        spec = {
            "source": (a["source"] if a else "grid"),
            "box": slot,
            "rotate": round(rots[i], 1),
            "mask": edge,
            "shadow": i < 2,
        }
        if not a:
            spec["palette"] = [inks[i % len(inks)], inks[(i + 1) % len(inks)]]
            if i % 2 == 0:
                spec["source"] = "newsprint"
        if a and i > 0 and s["blend"] == "multiply":
            spec["blend"] = "multiply"
            spec["opacity"] = 0.86
        pieces.append(spec)

    # One flat accent, one printed-paper field: the "limited ink" rule.
    # Flat accent disc: screen-print dots, clipped to a circle. A disc mask
    # must live on the piece, not in the halftone source, or the dots spill out.
    pieces.insert(1, {"source": "solid", "palette": [inks[1]],
                      "box": [int(W * .70), int(H * .28), int(W * .20), int(W * .20)],
                      "mask": "circle", "halftone": True, "cell": 10,
                      "opacity": .55, "rotate": 0})

    # Typography is a piece of cut paper, not a caption. Two bands, different
    # weights — the classic magazine-headline device.
    headline = concept.get("headline") or concept.get("theme", "COLLAGE")
    kicker = concept.get("kicker", "")
    hy = int(H * (0.865 if fmt != "banner" else 0.78))
    pieces.append({"text": str(headline).upper(), "font": s["font"],
                   "size": int(min(W * .13, 150)), "tracking": 9,
                   "color": inks[0], "box": [int(W * .07), hy, int(W * .86), int(H * .09)],
                   "rotate": round(jitter(seed, -3, 3, 1, 77)[0], 1)})
    if kicker:
        pieces.append({"text": str(kicker).upper(), "font": "mono", "size": 38, "tracking": 8,
                       "color": inks[min(1, len(inks) - 1)],
                       "box": [int(W * .08), hy - int(H * .055), int(W * .84), int(H * .04)],
                       "backing": True})

    tape = []
    if s["tape"]:
        tape.append([int(W * .80), int(H * .30), 190, 46, -11])
    if s["tape"] > 1:
        tape.append([int(W * .22), int(H * .72), 170, 42, 9])

    recipe = {
        "width": W, "height": H, "paper": s["paper"], "seed": seed,
        "pieces": pieces, "tape": tape,
        "marks": s["marks"] > 0, "mark_density": s["marks"],
        "_meta": {"strategy": key, "format": fmt, "statement": concept.get("statement", ""),
                  "headline": headline, "assets_used": len(ordered),
                  "content_cuts": [s["cut"] for s in flat]},
    }
    return recipe


def rationale(concept, recipe, manifest):
    m = recipe["_meta"]
    lines = [
        "# Design rationale", "",
        "**Theme:** %s" % concept.get("theme", ""),
        "**Pairing sentence:** %s" % m["statement"],
        "**Strategy:** %s — see `references/movements.md`." % m["strategy"],
        "**Format:** %s (%d × %d)" % (m["format"], recipe["width"], recipe["height"]),
        "**Paper stock:** `%s`. **Inks:** %s." % (
            recipe["paper"], ", ".join(concept.get("palette", [])[:4]) or "palette defaults"),
        "",
        "## From text to image", "",
    ]
    for mo in concept.get("motifs", []):
        lines.append("- **%s** (`%s`, role: %s) — %s" % (
            mo.get("id", "?"), mo.get("query", ""), mo.get("role", "satellite"), mo.get("why", "")))
    lines += [
        "",
        "## Composition decisions", "",
        "- %d pasted pieces; hero imagery first, then medium scraps, then type, then tape and pencil marks." % len(recipe["pieces"]),
        "- Found photographs are first cut according to their own visible content with hand-observed polygons or a simple plain-background silhouette. These transparent cut-outs are then recombined; no sourced image is pasted as a whole rectangular window.",
        "- A few geometric or torn paper scraps remain as counterpoint, so the content cuts read as cut paper rather than digital masking.",
        "- Rotations are small and non-repeating; only the two largest pieces carry drop shadow.",
        "- Exposed paper is intentional negative space; exact placement comes from `references/composition.md`.",
        "",
        "## Source imagery", "",
    ]
    for a in manifest.get("assets", []):
        lines.append("- `%s` — %s. %s, %s. %s" % (
            a["file"], a.get("title", ""), a.get("artist", "") or "unknown author",
            a.get("license", ""), a.get("page", "")))
    lines += ["", "Re-run with a different `--seed` for another arrangement of the same concept.", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Compile a concept + assets into a collage recipe.")
    ap.add_argument("--concept", required=True)
    ap.add_argument("--assets", required=True, help="directory containing SOURCES.json")
    ap.add_argument("--recipe", required=True, help="output recipe JSON path")
    ap.add_argument("--cutouts", help="directory for transparent content cuts (default: <recipe-dir>/cuts)")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--format", default="poster", choices=list(FORMATS))
    args = ap.parse_args()

    with open(args.concept, encoding="utf-8") as f:
        concept = json.load(f)
    mpath = os.path.join(args.assets, "SOURCES.json")
    with open(mpath, encoding="utf-8") as f:
        manifest = json.load(f)
    assets = manifest.get("assets", [])
    for a in assets:
        a["_dir"] = args.assets
    concept_cuts = concept.get("cuts", {})
    by_motif = {m.get("id"): m.get("cut") for m in concept.get("motifs", []) if m.get("cut")}
    for a in assets:
        if a.get("motif") in by_motif:
            a["cut"] = by_motif[a["motif"]]
        elif a.get("id") in concept_cuts:
            a["cut"] = concept_cuts[a["id"]]
        elif a.get("motif") in concept_cuts:
            a["cut"] = concept_cuts[a["motif"]]
        elif a.get("id") in by_motif:
            a["cut"] = by_motif[a["id"]]

    job_dir = os.path.dirname(os.path.abspath(args.recipe))
    cut_dir = args.cutouts or os.path.join(job_dir, "cuts")
    recipe = build(concept, assets, args.format, args.seed,
                   job_dir=job_dir, cut_dir=cut_dir)
    os.makedirs(os.path.dirname(os.path.abspath(args.recipe)), exist_ok=True)
    with open(args.recipe, "w", encoding="utf-8") as f:
        json.dump(recipe, f, ensure_ascii=False, indent=2)
    rpath = os.path.splitext(args.recipe)[0] + "-rationale.md"
    with open(rpath, "w", encoding="utf-8") as f:
        f.write(rationale(concept, recipe, manifest))
    print("wrote %s (%d pieces, %d sourced images, strategy=%s)" %
          (args.recipe, len(recipe["pieces"]), len(assets), recipe["_meta"]["strategy"]))
    print("wrote %s" % rpath)


if __name__ == "__main__":
    main()
