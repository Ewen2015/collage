---
name: collage-art
description: >-
  Turn a theme, a brief, or a passage of text into a finished collage artwork.
  Use when the user asks for collage art, a collage poster, a cut-paper
  composition, mixed-media / papier collé / photomontage / décollage styling,
  or wants visual imagery derived from a piece of writing. The skill extracts
  the ideas and imagery implicit in the text, finds its own source photographs,
  and composites them into a printed-paper assemblage.
license: MIT
compatibility: Requires Python 3.9+, Pillow, NumPy, and network access for image sourcing.
metadata:
  author: Ewen
  version: 0.1.0
  repo: ewen-collage
---

# Collage Art

You are given a topic or a body of text. Your job is to produce a **collage
artwork**, not a description of one. Work end to end: read → extract → find
imagery → compose → render → verify → explain.

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

## Step 3 — Compile the composition

```bash
python3 scripts/theme_to_recipe.py --concept <job>/concept.json \
    --assets <job>/assets --recipe <job>/recipe.json --seed 11 --format poster
```

This chooses the composition system, layer order, cut edges, rotations, type
treatment and tape from the strategy, and binds the sourced images to pieces.
It also writes `<job>/recipe-rationale.md`. `--format` accepts `poster`,
`editorial`, `square`, `banner`.

You may edit `<job>/recipe.json` by hand to fix a specific problem. See
`references/materials.md` for every `source`, `mask` and `blend` value, and
`references/composition.md` for the layout systems and anti-patterns.

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
smaller than the scraps, a photo that still reads as a window rather than a
printed scrap. If it fails, adjust the recipe or strategy and re-render.

Then deliver the PNG plus a short explanation of the pairing sentence, the
strategy and why those motifs were chosen. Include the credit lines from
`SOURCES.json`; reproduce the licence terms where required (CC BY-SA may
require the combined work to be shared alike). Point the user to
`recipe-rationale.md` for the full decision log.

## Quick reference

| Want | Command |
| --- | --- |
| See all built-in styles | `python3 scripts/collage.py --list` |
| Render a preset | `python3 scripts/collage.py --preset dada-montage --out out.png` |
| Save a preset as an editable recipe | `python3 scripts/collage.py --preset cubist-grid --out x.png --dump x.json` |
| Hand-write a recipe | `python3 scripts/collage.py --recipe x.json --out x.png` |
| Probe an image search | `python3 scripts/source_assets.py --query-only "moon crater"` |
| Test a concept offline | `python3 scripts/source_assets.py --concept c.json --out-dir a --offline` |

## Files in this skill

`scripts/collage.py` is the renderer (Pillow + NumPy, no network).
`scripts/source_assets.py` is the Commons search/downloader (stdlib only).
`scripts/theme_to_recipe.py` compiles a concept into a recipe (stdlib only).
`references/movements.md` is the art-historical decision map with sources.
`references/materials.md` documents paper stocks, sources, edges and blends.
`references/composition.md` documents layout systems and anti-patterns.
`references/prompts.md` gives prompt patterns for when a text-to-image model is
a better fit than the renderer.
`references/concept-schema.md` is the concept JSON contract.

A complete worked example (theme → concept → sourced assets → recipe →
rationale → final PNG) lives in the repo's `examples/demo/` directory.
