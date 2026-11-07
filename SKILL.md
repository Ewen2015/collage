---
name: collage
description: >-
  Turn a theme, a brief, or a passage of text into a finished collage artwork.
  Use when the user asks for collage art, a collage poster, a cut-paper
  composition, mixed-media / papier collé / photomontage / décollage styling,
  or wants visual imagery derived from a piece of writing. The skill extracts
  the ideas and imagery implicit in the text, finds its own source photographs,
  and composites them into a printed-paper assemblage.
license: MIT
compatibility: Requires Python 3.9+; run the bundled install.sh once to install Pillow and NumPy. Network access is needed only for autonomous image sourcing.
metadata:
  author: Ewen
  version: 0.2.1
  repo: collage
---

# Collage

You are given a topic or a body of text. Your job is to produce a **collage
artwork**, not a description of one. Work end to end: read → extract → find
imagery → compose → render → verify → explain.

## This skill is a folder, not a single file

An install is only complete if `SKILL.md`, `references/`, `scripts/`,
`requirements.txt`, `install.sh`, `install.ps1` and `scripts/check_setup.py`
are all present in the same directory. If any of them are missing, re-install
the whole package instead of copying `SKILL.md` on its own.

## Step 0 — Check the install (do this once)

```bash
python3 scripts/check_setup.py
```

It verifies the Python version, every bundled file, Pillow, NumPy, font
resolution, a renderer smoke test and a content-cut smoke test. If anything is
missing:

```bash
bash install.sh          # macOS / Linux: installs requirements.txt, then re-runs the check
# Windows: powershell -ExecutionPolicy Bypass -File install.ps1
```

The installers need a network connection only for the Python packages; every
other part of the skill works offline.

The guiding idea comes from the reference material in `references/`: collage is
an assemblage of materials that already have a history (Rise Art, Artsy), and
its visual logic is 断裂 / 重组 / 融合 — fracture, reassembly, fusion (UISDC).
So the deliverable must look like cut paper that was glued down and re-scanned,
and it must carry an idea formed by putting two unlike things together.

## Do not ask the user to make artistic decisions

Infer everything that can be inferred: strategy, palette, format, headline,
motifs. Only ask if the brief is a single ambiguous word with no context, or
if the user's own assets are clearly required. Default to a 1200×1500 poster,
one of the six strategies below, and autonomous image sourcing.

## Step 1 — Read and extract (this is the creative step; you do it)

Read the user's theme or passage and write a small concept JSON. Do **not**
just list nouns from the text. Do this:

1. Identify the **tension or movement** in the text (what changes, what is
   opposed, what returns, what is lost). A collage needs two unlike things.
2. Write one **pairing sentence**: "X meets Y, which suggests Z." This is the
   work's argument. If you cannot write it, you have not understood the text.
3. Extract 2–4 **visual motifs** that can *carry* that argument. For each,
   write a concrete image-search query (English works best on Commons) and a
   `why` explaining what it contributes. Prefer photographable objects and
   textures over abstract nouns. "memory" is not a motif; "a faded ticket
   stub", "a breaking wave", "a night skyline" are.
4. Choose a **strategy** from `references/movements.md` that matches the
   emotional register, and a **palette** of 2–4 inks.
5. Choose a **headline** (a short cut-from-a-magazine phrase, in the user's
   language or English) and optionally a **kicker** (a small mono line).

Write it to `<job>/concept.json`:

```json
{
  "theme": "潮汐与城市",
  "headline": "TIDE / CITY",
  "kicker": "A NOTE ON DISTANCE",
  "statement": "The returning tide meets the sleeping city, suggesting a memory that keeps coming back.",
  "strategy": "surrealism",
  "palette": ["#16283a", "#d94f36", "#4a86a8", "#f0c94b"],
  "motifs": [
    {"id": "tide", "query": "breaking ocean wave water", "role": "hero",
     "why": "the returning tide, the thing that keeps coming back"},
    {"id": "city", "query": "city skyline night silhouette", "role": "ground",
     "why": "the sleeping city, the fixed thing"},
    {"id": "moon", "query": "moon crater lunar surface", "role": "satellite",
     "why": "the distant witness, one impossible object inside the arch"}
  ]
}
```

`strategy` is one of `cubism`, `dada`, `surrealism`, `pop`, `decollage`,
`editorial`. `role` is `hero` (one), `ground`, or `satellite`. Full schema:
`references/concept-schema.md`.

When the user supplies their own images, skip Step 2 and write a
`SOURCES.json` manifest pointing at those files, with `license: "user-provided"`.

## Step 2 — Find source imagery autonomously

```bash
python3 scripts/source_assets.py --concept <job>/concept.json \
    --out-dir <job>/assets --per-motif 1
```

This searches Wikimedia Commons, keeps only CC BY / BY-SA / CC0 / public-domain
results, skips files with personality-rights warnings, downloads thumbnails,
and writes `<job>/assets/SOURCES.json` with author, licence and source page for
every image. **Do not skip this manifest** — the finished work must be
attributable. Use `--query-only "..."` to probe a search term when a motif
comes back with poor results, then edit the concept and re-run.

Rules for good queries: concrete nouns, no aesthetic adjectives ("beautiful",
"vintage"), 2–4 words, avoid queries that return people. If a downloaded image
turns out to be a portrait or a diagram, replace it — check the rendered result
in Step 5 rather than trusting the filename.

If the environment has no network, say so and continue with the procedural
paper sources (`photo`, `newsprint`, `grid`, `wood`, `halftone`), which need no
downloads. The renderer degrades gracefully when an asset path is missing.

## Step 3 — Cut the images according to their visible content

**This is not optional.** A finished collage must not be a stack of whole
rectangular photographs with decorative torn edges. Look at each source image
and cut the thing that carries meaning: a silhouette, a hand, a keyboard, a
mouth, a bridge plank, a dark diagonal, a field of blue, a line of seats, a
chalkboard, a passage through grass. Recombine those image-shaped fragments so
the seam becomes an argument. Lydia Rink's beginner guide reinforces the
physical version of this: a scalpel/craft knife is for precision cutting around
elements; arrange loosely before gluing; leave negative space; vary scale; use
layers to make depth.

`scripts/visual_cutout.py` is a deliberately small digital scalpel. It uses
only Pillow and NumPy. The main mode is `shape`: look at the source photograph
and describe the visible object or structural region with a normalized polygon.
A second `silhouette` mode removes a plain border/background by colour
distance. There is no heavyweight image-segmentation dependency. The compiler
also writes `cuts/contact-sheet.jpg`; inspect it before composing and adjust
the polygon if the cut misses the subject.

The compiler runs the cuts and binds the resulting transparent PNGs to the
recipe with `mask: "alpha"`:

```bash
python3 scripts/theme_to_recipe.py --concept <job>/concept.json \
    --assets <job>/assets --recipe <job>/recipe.json \
    --cutouts <job>/cuts --seed 11 --format poster
```

Describe cuts in the concept on each motif (`cut`) or in a `cuts` map keyed by
motif id. A motif may provide one instruction or a list of instructions, which
produces several fragments from one photograph:

```json
"cut": [
  {"mode": "shape", "shape": "0.00,0.00;1.00,0.00;1.00,0.46;0.00,1.00"},
  {"mode": "shape", "shape": "0.00,0.79;0.34,0.60;1.00,0.73;1.00,1.00;0.00,1.00"}
]
```

Use `shape` for the semantic contour you can see in the photograph;
coordinates are normalized `x,y;x,y;...`. Use `silhouette` only when the
object sits on a plain paper-like background. Keep one or two geometric/torn
paper scraps as counterpoint, but the found photographs must be cut by content
first. See `references/composition.md` for the cutting method and
`references/materials.md` for `alpha` sources and masks.

## Step 4 — Render

```bash
python3 scripts/collage.py --recipe <job>/recipe.json --out <job>/final.png
```

The renderer applies paper fibre, halftone screening, torn edges, print
registration, drop shadows, tape, pencil marks, grain and a unifying warm wash.
It is deterministic: same recipe plus same seed gives the same image. Render
two or three seeds and pick the best one — torn edges and facet fields vary.

## Step 5 — Verify, then explain

Always **look at the image** you produced (open it or generate a contact sheet)
before delivering. Check the anti-patterns in `references/composition.md`:
too many colours, shadow on every layer, everything at 0°, all-torn edges, type
smaller than the scraps, and especially a photograph still reading as a whole
rectangular window instead of a shape cut from its own content. If the semantic
cut is not legible at thumbnail size, return to Step 3. If it fails, adjust the
recipe or strategy and re-render.

Then deliver the PNG plus a short explanation of the pairing sentence, the
strategy and why those motifs were chosen. Include the credit lines from
`SOURCES.json`; reproduce the licence terms where required (CC BY-SA may
require the combined work to be shared alike). Point the user to
`recipe-rationale.md` for the full decision log.

## Quick reference

| Want | Command |
| --- | --- |
| Verify the install | `python3 scripts/check_setup.py` |
| Install Python dependencies | `bash install.sh` |
| See all built-in styles | `python3 scripts/collage.py --list` |
| Render a preset | `python3 scripts/collage.py --preset dada-montage --out out.png` |
| Save a preset as an editable recipe | `python3 scripts/collage.py --preset cubist-grid --out x.png --dump x.json` |
| Hand-write a recipe | `python3 scripts/collage.py --recipe x.json --out x.png` |
| Cut a hand-observed contour | `python3 scripts/visual_cutout.py --input photo.jpg --out cut.png --mode shape --shape "0,.1;1,0;.9,1;0,.9" --contact-sheet sheet.jpg` |
| Remove a plain background | `python3 scripts/visual_cutout.py --input object.jpg --out cut.png --mode silhouette` |
| Probe an image search | `python3 scripts/source_assets.py --query-only "moon crater"` |
| Test a concept offline | `python3 scripts/source_assets.py --concept c.json --out-dir a --offline` |

## Files in this skill

`requirements.txt` declares Pillow and NumPy. `install.sh` (macOS/Linux) and
`install.ps1` (Windows) install them and run `scripts/check_setup.py`.
`scripts/check_setup.py` verifies every bundled file, the Python version, font
resolution, a renderer smoke test and a cutout smoke test. `scripts/collage.py`
is the renderer (Pillow + NumPy, no network). `scripts/visual_cutout.py` cuts
hand-observed polygons and simple plain-background silhouettes (Pillow + NumPy,
no network). `scripts/source_assets.py` is the Commons search/downloader
(stdlib only). `scripts/theme_to_recipe.py` compiles a concept into a recipe
and runs the lightweight content-cut commands.
`references/movements.md` is the art-historical decision map with sources.
`references/materials.md` documents paper stocks, sources, edges and blends.
`references/composition.md` documents layout systems and anti-patterns.
`references/prompts.md` gives prompt patterns for when a text-to-image model is
a better fit than the renderer.
`references/concept-schema.md` is the concept JSON contract.
`assets/` is the optional place for user-provided source images.

A historical worked example (theme → concept → sourced assets → recipe →
rationale → final PNG) lives in the repo's `examples/demo/` directory; it shows
the earlier rectangular-scrap pipeline and is kept as a renderer example, not
as the current content-cut workflow. The repository itself is the installable
package: `SKILL.md`, `references/`, `scripts/`, the installers and `assets/`
sit at the root. `dist/collage.skill` is a ZIP of exactly those files, with the
same paths at the archive root.
