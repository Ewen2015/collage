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
        --recipe out/recipe.json [--seed 11] [--format poster|editorial|square|banner]

It also emits a rationale file (out/rationale.md): the design decisions in plain
language, so the output can be explained and revised.

Requires: Python stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
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


def build(concept, assets, fmt, seed):
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
    by_role = {}
    for a in assets:
        by_role.setdefault(a.get("role", "satellite"), []).append(a)
    ordered = by_role.get("hero", []) + by_role.get("ground", []) + by_role.get("satellite", [])

    rots = jitter(seed, s["rotate"][0], s["rotate"][1], max(1, len(ordered) + len(slots)))
    pieces = []
    for i, slot in enumerate(slots):
        a = ordered[i] if i < len(ordered) else None
        edge = pick(s["edges"], i)
        spec = {
            "source": (os.path.join(assets[0]["_dir"], a["file"]) if a else "grid"),
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
                  "headline": headline, "assets_used": len(ordered)},
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
        "- Mixed edges (straight cuts against torn strips) to keep it reading as assemblage rather than a filtered photo.",
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

    recipe = build(concept, assets, args.format, args.seed)
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
