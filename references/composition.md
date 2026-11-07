# Composition systems

Collage has no perspective and no single light source, so it needs an explicit
organising device. Pick one before placing any scrap.

## The five working systems

**1. Anchor + satellites.** One large piece (50–70% of the canvas) holds the
frame; 2–4 smaller scraps orbit and interrupt it. Best for first attempts and
for editorial work. Example: `surreal-arch`, `analog-scrapbook`.

**2. Faceted field.** Divide the picture plane into overlapping planes that
analyse a single object from multiple simultaneous viewpoints. No background,
no horizon, no vanishing point. Shallow depth made only by overlap and shadow.
Example: `cubist-grid`. Do not add a literal illustration of the object; the
facets *are* the object.

**3. Violent juxtaposition.** Two or three images at incompatible scales and
angles, forced into the same frame. Scale conflict is the whole point: a giant
letter beside a tiny newspaper column, a face next to a machine part. Add
oversized type as a third voice. Example: `dada-montage`.

**4. Poster grid.** A strong typographic band, a regular two-column body, and
one torn strip crossing the grid. The grid makes the tear legible. Good for
covers and e-commerce banners. Example: `riso-editorial`.

**5. Layered subtraction.** Start from a full-bleed patterned field, then cover
and tear away — kraft over stripes over newsprint. Half-legible words should
survive. Example: `decollage-poster`.

## Cut by content, then compose

A sourced photograph is raw material, not a finished scrap. Before arranging,
look inside it and cut out the region that can carry the argument: a subject
silhouette, a hand, a mouth, a keyboard, a bridge plank, a line of chairs, a
dark diagonal, a chalkboard, a passing path, or an organic blue/white/botanical
field. The cut edge should follow a contour, tonal boundary, semantic line or
object outline in the source. Join those shaped fragments so one image's edge
continues, interrupts or answers another image's edge; that is what makes the
seam meaningful rather than merely decorative.

Use `scripts/visual_cutout.py` as a small, dependency-light scalpel. The main
`shape` mode cuts a hand-observed semantic polygon; `silhouette` removes a plain
background around an isolated object. Inspect `cuts/contact-sheet.jpg` first. If
a cut is too literal or window-like, take a smaller region and let another
source continue its line. There is no OpenCV or learned segmentation here: the
agent's visual reading of the photograph is the point.

Lydia Rink's *Collage Art Beginner's Guide* adds the working discipline behind
this: use a scalpel or craft knife for precision cutting, arrange pieces loosely
before committing, use colour and texture as a first experiment, place key
elements with a focal point and negative space in mind, shift scale deliberately,
and build depth through layers. In a digital composition this means: cut first,
place without glue, keep 15–30% exposed ground, enlarge one small fragment,
reduce one large one, and let a translucent or printed field sit between the
foreground and background.

## Restraint: fewer, larger pieces

The strongest collages are usually the quietest. A user-supplied set of three
reference works makes the rule concrete:

- A narrow vertical diptych of a mouth above hands at a piano. Two rectangular
  scraps, one clean horizontal seam, monochrome, and roughly 80% empty grey
  ground. The dark curve of the neck continues into the dark diagonal of the
  keyboard, so the seam *is* the idea. No type, tape, marks or texture effects.
- A black-and-white landscape with four or five large, flowing cut-paper shapes
  (blue foliage, white snow, gold blossom, dark leaves) following the hills and
  waterline and spilling past the frame. Three colours total. Complexity lives
  in the contour of a few big pieces, not in the number of pieces.
- A guitarist cut along the subject's silhouette over a calm, low-contrast grid
  of sheet-music scraps. One dominant dark figure, one quiet warm ground, near
  monochrome.

The shared grammar: **one dominant element, two or three tones, a handful of
large pieces, generous negative space, edges that follow visible content,
almost no rotation, and no decorative clutter.** A seam that aligns a dark
shape with another dark shape (or a contour with a contour) reads as an
argument; ten overlapping scraps with tape, pencil marks, halftone discs,
shadows and a headline strip read as a pile of stickers.

Practical rule: start with 2–4 pieces. Remove one before adding one. If the
thumbnail reads as "many equally weighted fragments", it is too busy — merge
fragments into one larger cut, mute a colour, or delete the type band. Keep
type tiny and out of the way unless the movement genuinely calls for it.
Reserve tape, marks, halftone discs and shadows for at most one accent, and
usually for none.

## A repeatable procedure

1. **Name the semantic pairing.** Write one sentence: "X meets Y, which
   suggests Z." Collage is an argument made of two found things. If you cannot
   write this sentence, the result will be decoration. The UISDC article makes
   the same point from the design side: the visual impact hooks the viewer, but
   the transmitted idea is what holds them.
2. **Choose a system** from the five above, and a movement from
   `movements.md`. These two choices determine the palette, edges and type.
3. **Cut elements out of their own images.** Look at each source and follow its
   subject contour, tonal boundary, structural line or semantic shape. Do not
   paste a whole rectangular photograph and call it a scrap. From a reference,
   list its constituent parts: stock, edge, ink, type weight, one texture, one
   motif. Rebuild from that list. This prevents both plagiarism and the
   "generic AI collage" look.
4. **Lay the ground.** Paper stock first, then the largest content-cut piece,
   then medium fragments whose edges answer the hero cut, then type, then tape
   and pencil marks last. Layer order is the composition; reordering the same
   six pieces produces a different picture.
5. **Rotate with intent.** 2–8° for "hand placed"; 15–25° for "protest".
   Never 0° on every piece. Never more than two pieces at the same angle.
6. **Leave negative space.** The paper showing through between shaped cut-outs
   is a material, not empty canvas. Aim for 15–30% exposed ground; it is what
   makes an irregular silhouette legible.
7. **Check at thumbnail size.** Reduce to ~300px wide. If it reads as a single
   poster with one clear accent and the content-derived cuts are visible, it
   works. If it reads as a pile of stickers or rectangular photo windows,
   remove a piece, mute a colour, or return to the cutout step.

## Anti-patterns

- Six colours of equal weight.
- Drop shadow on every layer (everything floats, nothing is glued).
- A centred symmetrical stack with all pieces at 0°.
- Legible lorem ipsum where newsprint texture would do.
- A single photographic image with a "collage" filter over it — that is a
  filter, not an assemblage.
- Whole rectangular photo scraps whose edges ignore the subject inside them;
  this is simple stacking, not content-aware collage.
- A cutout that reads as a digital mask rather than cut paper: no halftone,
  paper grain, shadow, overlap or counter-cut nearby.
- Torn edges on every piece; torn edges only matter next to a clean cut.
- Many equally weighted scraps plus tape, marks, discs, shadows and a headline
  band all at once. This is busyness, not collage; see "Restraint" above.
- Type that is smaller than the scraps. In collage, type is usually a *piece*,
  cut from the same magazine as the images, and should carry comparable weight.

## Adapting to a format

For a poster use a 3:4 or 4:5 canvas with the headline in the lower third. For
an editorial spread use 4:5 with a strong top band and a two-column body. For a
banner, keep one hero scrap on the left and all type on the right. For social
square, use a single centred circle or arch and cut the supporting scraps off
the edges — bleeding off-canvas is what makes it feel cut from a larger sheet.
