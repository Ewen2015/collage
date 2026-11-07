# Materials and edges

A collage is convincing when every scrap looks like it came from somewhere
else. These are the stocks the renderer can synthesise, and what each one is
for.

## Paper stocks (the `paper` palette key)

| Stock | Colour | Use for |
| --- | --- | --- |
| `cream` | `#f2e9d6` | Default. Aged book paper, gallery stock, editorial work. |
| `newsprint` | `#e5e0d3` | Dada, protest, anything that should feel cheap and immediate. |
| `kraft` | `#cdb08a` | Décollage, packaging, street-poster warmth. |
| `cold` | `#e8ecea` | Surrealism, architectural calm, clinical negative space. |
| `pink` | `#f3dfd8` | Pop, fashion, romance, screen-print misregistration. |
| `black` | `#1c1b1a` | Scrapbook / contact-sheet. Inks invert to light colours. |

All stocks get multi-octave fibre noise, a faint warm vignette and a final
grain pass. That shared paper texture is what makes unrelated scraps look like
they were photographed on the same sheet — do not skip it.

## Sources (`source` on a piece)

- `solid` — a single ink. The most underused element; use it for the one flat
  accent that stops the eye.
- `gradient` — a two-colour field. Use as a sky or a ground, never as the whole
  image.
- `photo` — a simulated magazine crop: soft colour field plus a halftone
  screen. Stands in for a photographic fragment when no asset is supplied.
- `halftone` — a rotated screen-print dot grid. Set `cell` (dot spacing) and
  `angle` (usually 15°, 45° or 75°).
- `newsprint` — ruled column lines and a headline bar, deliberately not
  legible. Legible fake text is worse than illegible texture.
- `stripes` — wallpaper / oilcloth / chair-caning stand-in. The Cubist reference
  to printed oilcloth is here.
- `grid` — faceted colour planes, the Cubist analytic move.
- `wood` — wavy woodgrain, for wallpaper or faux-wood printed paper.
- `kraft` — fibrous brown paper.
- `stamp` — perforated postage stamp, for ticket stubs and Schwitters-like
  ephemera.
- `type` — a single giant cut letter (`char`), the classic *papier collé*
  device.
- Any local `.png` / `.jpg` / `.webp` path — centre-cropped to the box. Use
  real assets when the user supplies them; the procedural ones are fallbacks.
- A transparent content-cut `.png` made by `scripts/visual_cutout.py` — use it
  with `mask: "alpha"` (also accepted: `content`, `retain-alpha`). The cut is a
  hand-observed polygon or a simple plain-background silhouette, made with
  Pillow + NumPy. The renderer letterboxes the cutout inside its box so no part
  of its silhouette is cropped away, then applies the same halftone, warm tint
  and paper grain to its ink. This is the required source form for found
  photographs after Step 3.

## Cut edges (`mask` on a piece)

| Mask | Reads as |
| --- | --- |
| `cut` / `rect` | Scissors, straight and certain. Cubism, editorial. |
| `torn` | Hand-torn horizontally, slightly feathered fibre. Most human edge. |
| `torn-v` | Hand-torn vertically. |
| `strip` | A narrow torn band, like a ripped poster remnant. |
| `circle` | Punched / compass-cut. Pop, Dada, Surrealism. |
| `arch` | Flat-bottomed arch, an architectural aperture. |
| `triangle`, `diamond` | Geometric facet. |
| `perforated` | Stamp or ticket edge. |
| `alpha` / `content` / `retain-alpha` | Preserve the transparent silhouette made from a source image's own content. Required for photographs cut by `visual_cutout.py`. |

Rule of thumb: mix **one** geometric cut or torn paper scrap with two or three
content-derived silhouettes. All straight reads as graphic design; all torn
reads as a scrapbook; all rectangle-shaped photographs reads as simple stacking.
The content cut is the primary edge; geometric and torn edges are counterpoint.

## Blend, shadow, tape, marks

- `blend`: `normal` (opaque pasted paper), `multiply` (ink showing through,
  like newsprint or a rubbing), `screen`, `overlay`. Multiply is the only one
  you need most of the time.
- `shadow: true` gives the piece physical thickness. Use it on 1–3 hero pieces,
  never on all of them — otherwise everything floats.
- `tape` — semi-transparent washi/masking tape with torn ends. Its job is to
  admit the glue. Two strips maximum per composition.
- `marks: true` — pencil arcs, registration crosses, ink specks. Keep density
  low (0.7–1.6). These are the evidence of a working table.

## Colour discipline

Two to four inks plus one paper. Choose one dominant (~60%), one secondary
(~25%), one accent (~10%), and let the paper supply the rest (~5%). A collage
with six equally loud colours stops reading as printed matter. If you need
variety, get it from material (newsprint vs woodgrain vs halftone), not hue.
