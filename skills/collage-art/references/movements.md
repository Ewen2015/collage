# Collage: a short art-historical map

This is the reference behind the presets in `scripts/collage.py`. It is a
working map for making decisions, not an academic survey. Every movement below
answers a different question, and each one leaves a different visual trace.

## The core definition

Collage is a two-dimensional work built from an assemblage of different
materials — paper, photographs, fabric, printed ephemera — that have been
selected, cut, arranged and affixed. The word comes from the French *coller*,
"to glue". The craft lies in the **choosing, arranging and affixing**, not in
drawing. Two consequences matter for a renderer:

1. The material is *already made*. A newspaper scrap carries its own history,
   its own typography, its own print registration. Respect that instead of
   recolouring it into a generic texture.
2. Collage is a medium/technique, not a formal movement. It was taken up by
   Cubism, Dada, Surrealism, Pop and Nouveau Réalisme, and each one used it for
   a different argument. Its development ran parallel to early-20th-century
   experiments in poetry and literature: fragmentation, reassembly, multiple
   simultaneous meanings, the texture of urban life.

## Timeline and the visual trace each period left

| Period | What it argued | What you should actually see in the image | Preset |
| --- | --- | --- | --- |
| **Cubism, 1912–13** — Braque's *Fruit Dish and Glass*, Picasso's *Still Life with Chair Caning* (1912) | An assault on painting's imaginary space and on "proper" art materials. Printed oilcloth imitating chair caning, real rope as a frame. | Newspaper, woodgrain/wallpaper, faceted planes, a legible letter or two, shallow overlapping depth, no perspective. Analyse the object into facets and reassemble it. | `cubist-grid` |
| **Papier collé** (pasted paper, 1912–13) | The pasted paper is both the depicted object and itself. | Flat cut rectangles, deliberate edges, one dominant colour accent, a small headline to anchor the picture plane. | `riso-editorial` |
| **Dada / photomontage, 1916–1920s** — John Heartfield, Hannah Höch, Raoul Hausmann, later Kurt Schwitters | Social and political commentary through violent juxtaposition. Schwitters brought street detritus (ticket stubs, stamps, newspapers) into high art; he was called "the king of collage". | Photographic fragments at conflicting scales, jarring rotations, oversized type as a shout, newsprint columns, visible seams. Never pretty it up. | `dada-montage`, `analog-scrapbook` |
| **Surrealism, 1920s–30s** | The irrational juxtaposition; Lautréamont's "chance meeting of a sewing machine and an umbrella on a dissecting table". More attention to the coordination of materials' own colour and texture than Dada. | One calm architectural frame (an arch, a horizon) holding one impossible object. Restraint. Dream logic comes from *what* is paired, not from how many things are on the page. | `surreal-arch` |
| **Décollage / Nouveau Réalisme, c. 1960** | "To unstick". Torn poster layers are removed rather than added; the street is the author. | Layered, partly stripped paper, kraft and stripes, half-legible words, adhesive tape, a sense that something was peeled away. | `decollage-poster` |
| **Pop, 1950s–60s** — Richard Hamilton and others | Mass-media imagery as subject matter. | Halftone dots, saturated spot colour, a single iconic circle, onomatopoeic type, repetition. | `pop-halftone` |
| **Contemporary / mixed media** — e.g. Kareem Rizk, Benjamin West's *Processed* series (a tribute to Heartfield) | Analogue process as nostalgia and as critique; scanned, re-photographed, re-registered. | Clean negative space, one or two meticulously textured scraps, tape, registration marks, evidence of the scan. | `analog-scrapbook`, `riso-editorial` |

## Related techniques worth distinguishing

- **Assemblage** — three-dimensional found objects. The boundary with collage is fluid (Artsy explicitly notes this); in a 2D renderer, simulate it with drop shadows and thickness rather than pretending the objects are flat.
- **Photomontage** — a collage made specifically from photographs, usually with a polemical edge. Compose from cut photographic fragments, not from a single filtered photo.
- **Décollage** — subtractive. Start with a full poster field and tear parts of it away.
- **Montage** — the general joining of pre-existing images; historically tied to film as well as print.

## What the plane-design literature adds

The Chinese design article *实战演示！如何把拼贴艺术运用到平面设计中？* (UISDC, 2016) treats collage as a practical method for commercial/graphic work: it identifies **断裂 (fracture), 重组 (reassembly), 融合 (fusion)** as the defining visual moves, and notes the use of **点线面、色块、重复、平衡、波普** (point/line/plane, colour blocks, repetition, balance, pop) in fashion-magazine and e-commerce work. Its useful working method is: gather references from a similar style, **extract the constituent elements**, then rebuild a new composition from those elements rather than copying a whole image. It also points out that the initial attraction is visual impact, but what holds the viewer is the idea — collage uses imagination to go beyond reality. Translated into a skill: decide the semantic pairing first, then choose edges and textures.

## Sources

- [A Guide to Collage — Rise Art](https://www.riseart.com/guide/2371/a-guide-to-collage) — definition, *coller* etymology, 1912 origin, papier collé / assemblage / décollage / photomontage, Heartfield, Schwitters, Benjamin West, Kareem Rizk. (Direct fetch returned HTTP 202 with an empty body; the summary is based on the indexed text.)
- [Collage — Artsy gene page](https://www.artsy.net/gene/collage) — 2D assemblage definition, Picasso's 1912 *Still Life with Chair Caning*, Schwitters and street ephemera, collage as a technique rather than a movement. (Direct fetch was blocked by Cloudflare, HTTP 403; the summary is based on the indexed text.)
- [实战演示！如何把拼贴艺术运用到平面设计中？— 优设网 UISDC](https://www.uisdc.com/tiles-in-graphic-design) — Cubist / Dada / Surrealist lineage, 断裂·重组·融合, point-line-plane and colour-block vocabulary, the extract-elements-then-rebuild method, e-commerce examples.
