# Prompt patterns for generative image tools

This skill renders deterministically with Pillow. When the user wants a
photographic or illustrated collage instead — or wants to feed a text-to-image
model — use these patterns. The trick is to describe **materials, edges and
layer order**, not "collage style".

## The reusable skeleton

> Analog [MOVEMENT] collage on [PAPER STOCK], [CANVAS RATIO]. [SEMANTIC
> PAIRING: X meets Y]. One large [ANCHOR PIECE] with [EDGE TYPE] edges,
> [2–4 SATELLITE SCRAPS] at slightly conflicting scales, [TYPE TREATMENT],
> [INK COUNT] spot inks, visible paper fibre, halftone print registration,
> torn paper edges, soft drop shadow on two layers only, masking tape, faint
> pencil registration marks, scanned on a flatbed, no clean vector shapes, no
> gradients-as-background, no 3D render, no glossy finish.

## Filled examples

**Cubist / papier collé**
> Analog 1912 papier collé on aged cream book paper, 4:5. A café table analysed
> into overlapping facets: woodgrain wallpaper, a fragment of French newspaper,
> and one large cut serif "R" as if clipped from a headline. Straight scissor
> cuts, shallow overlap, three spot inks (charcoal, vermilion, prussian blue),
> a single vermilion circle as the accent, one torn strip crossing the grid,
> flatbed scan, visible paper fibre, no perspective, no shading.

**Dada / photomontage**
> Berlin Dada photomontage on cheap grey newsprint, 4:5. A giant red sans-serif
> "DADA" cut letterforms colliding with a tilted halftone portrait fragment and
> two columns of illegible newspaper type at conflicting scales. Violent 15°
> rotations, hard seams, one piece of black tape, ink specks, two inks only
> (vermilion and charcoal), flatbed scan, no blending, no soft focus.

**Surreal**
> Surrealist collage on cold grey paper, 3:4. A flat-bottomed blue arch cut from
> printed paper holds a halftone moon; a single dark rectangular bar leans
> across a torn ochre horizon below it. One impossible pairing, calm negative
> space, two torn edges against one clean cut, no other objects, muted blue /
> ochre / charcoal, faint pencil arcs, flatbed scan.

**Décollage**
> 1960s décollage street poster on kraft paper, 3:4. Layers of striped
> wallpaper, torn newsprint and a half-peeled green printed sheet, with a
> serif "AFFICHE" only partly surviving. Kraft fibre, torn feathered edges,
> two strips of aged masking tape, no clean rectangles, flatbed scan.

**Pop / riso**
> Two-colour riso collage on pink paper, 1:1. A halftone-dot circle portrait in
> blue and yellow, one vermilion "WOW!" cut from a magazine headline, a yellow
> torn strip, visible misregistration, 12 lpi dot screen, paper grain, no
> smooth gradients.

## Negative prompts that actually help

`clean vector shapes, glossy, 3D render, single filtered photograph, bevel,
neon glow, symmetrical centered stack, drop shadow on every layer, smooth
airbrush gradient, lorem ipsum, six equally saturated colours, stock-photo
watermark`

## Translating a user brief into a recipe

Ask for (or infer) these five things, then fill `scripts/collage.py`:
subject/pairing → `pieces` sources and text; mood → `paper` palette; era →
choose from `movements.md`; format → `width`/`height`; variability → `seed`.
If the user supplies real images, use their paths as `source` values rather
than the procedural stand-ins. Always render at least two seeds and pick the
better one — the torn edges and facet fields are stochastic.
