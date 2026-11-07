# collage

An **agent skill** by Ewen — a plain `SKILL.md` folder, usable by any agent that
can read skill instructions and run Python — that turns a theme, a brief, or a
passage of text into a finished collage artwork.

Give it a topic or a paragraph. It reads the text, finds the tension in it,
translates that into concrete visual motifs, searches for its own licensed
source photographs, cuts the meaningful visible shapes out of them with simple
hand-observed contours, and recombines those shaped fragments into a
printed-paper assemblage — halftone, torn paper counter-cuts, tape, pencil
marks and all.

```text
"潮水一次次回来，城市却装作睡着"  →  TIDE / CITY  →  [900×1125 PNG]
```

[See the worked example](examples/demo/tide-city.png) · [Its decision log](examples/demo/recipe-rationale.md) · [Its image credits](examples/demo/assets/SOURCES.json) · **[Project page and full gallery →](https://ewen2015.github.io/collage/)**

## One name, one folder

The repository *is* the skill. `SKILL.md` sits at the root next to
`references/`, `scripts/`, `requirements.txt`, the installers and `assets/`;
there is no nested `skills/` directory to find. The name `collage` is a
functional identifier, the way `pdf` or `xlsx` are: it says what the skill does
in slash commands, plugin namespaces and searches, without tying a reusable
tool to an author's name. Authorship lives in `metadata.author`, the README and
the LICENSE.

## Install

Install the whole repository — `SKILL.md`, five references, five scripts,
`requirements.txt` and the installers all travel together. A single `SKILL.md`
file is not a complete install.

The standard open agent-skills CLI (Node.js 22.20+) does this for you, targeting
whatever skills-compatible agent you use:

```bash
npx skills add Ewen2015/collage -g -y
# omit -g to install into the current project only
```

Alternatively use the direct folder link or the checked-in
[`dist/collage.skill`](dist/collage.skill) ZIP package. Clone and copy,
or unzip into your agent's skills directory:

```bash
git clone https://github.com/Ewen2015/collage.git
cp -r collage /path/to/your/agent/skills/collage

# or, with the portable package:
curl -L -o collage.skill \
  https://github.com/Ewen2015/collage/raw/main/dist/collage.skill
unzip -o collage.skill -d /path/to/your/agent/skills/collage
```

Then, from the installed folder, install its Python dependencies and verify
everything is present. This is the only step that needs a network connection;
the 16 built-in presets work offline and Wikimedia Commons sourcing needs
network only at run time.

```bash
cd /path/to/your/agent/skills/collage
bash install.sh                 # Windows: powershell -ExecutionPolicy Bypass -File install.ps1
python3 scripts/check_setup.py  # optional: re-check at any time
```

Requires Python 3.9+, Pillow and NumPy. Then just ask:
*"Make a collage poster about the tide and a sleeping city"* or paste a
paragraph and ask for a collage.

## What it does

1. **Extract** — reads the text, names the tension, writes a one-sentence
   pairing ("X meets Y, which suggests Z") and 2–4 photographable motifs.
2. **Source** — searches Wikimedia Commons for each motif, keeps only
   CC BY / BY-SA / CC0 / public-domain results, downloads them and writes an
   attribution manifest.
3. **Cut** — looks at each source photograph and cuts the meaningful part with a
   hand-observed polygon, or removes a plain background from an isolated object.
   Transparent fragments are made with Pillow + NumPy; no OpenCV or learned
   segmentation is required.
4. **Compose** — picks an art-historical strategy (Cubism, Dada, Surrealism,
   Pop, Décollage, editorial), a composition system, counter-cut paper scraps,
   rotations and type, and compiles a recipe JSON.
5. **Render** — a deterministic Pillow renderer produces the PNG: paper fibre,
   halftone screening, content-cut silhouettes, print registration, shadows,
   tape, grain.
6. **Verify** — checks the image against a list of anti-patterns, then explains
   the choices and credits the sources.

The guidance comes from four sources: [Rise Art's *A Guide to Collage*](https://www.riseart.com/guide/2371/a-guide-to-collage)
(definition, *coller*, papier collé / assemblage / décollage / photomontage,
Heartfield, Schwitters), [Artsy's Collage gene page](https://www.artsy.net/gene/collage)
(2D assemblage, Picasso's 1912 *Still Life with Chair Caning*, Schwitters'
street ephemera, collage as a technique rather than a movement), and
[优设网 UISDC's 实战演示！如何把拼贴艺术运用到平面设计中？](https://www.uisdc.com/tiles-in-graphic-design)
(断裂·重组·融合, point-line-plane and colour-block vocabulary, and the
extract-elements-then-rebuild method), and Lydia Rink's
[*Collage Art Beginner's Guide*](https://lydiarink.de/wp-content/uploads/2023/11/Lydia-Rink-Art-_Collage-Art-Beginners-Guide_.pdf)
(precision cutting, loose arrangement, negative space, scale shifts and
layered depth). Full notes are in
[`references/movements.md`](references/movements.md)
and [`references/composition.md`](references/composition.md).

## Repository layout

```text
collage/
├── SKILL.md                         end-to-end workflow (the skill itself)
├── README.md                        this file
├── LICENSE                          MIT, © Ewen
├── references/                      movements, materials, composition, prompts, schema
├── scripts/
│   ├── collage.py                   renderer (Pillow + NumPy)
│   ├── visual_cutout.py             content-aware transparent cut-outs
│   ├── source_assets.py             Commons search + attribution manifest
│   ├── theme_to_recipe.py           concept → cuts → recipe compiler
│   └── check_setup.py               install verification
├── requirements.txt                 Pillow + NumPy
├── install.sh / install.ps1         one-time dependency installers
├── assets/                          optional local source images
├── dist/
│   └── collage.skill                portable ZIP of the whole skill
├── docs/                            GitHub Pages site (index.html + 19 works)
└── examples/
    ├── gallery/                     16 built-in style presets
    └── demo/                        full theme → artwork worked example
```

## Gallery

Sixteen built-in presets, each encoding a different art-historical strategy
rather than just a colour scheme. [Browse all of them on the project page](https://ewen2015.github.io/collage/#gallery), or see the first seven here.

| | | |
| --- | --- | --- |
| ![cubist-grid](examples/gallery/cubist-grid.png) | ![dada-montage](examples/gallery/dada-montage.png) | ![surreal-arch](examples/gallery/surreal-arch.png) |
| `cubist-grid` | `dada-montage` | `surreal-arch` |
| ![pop-halftone](examples/gallery/pop-halftone.png) | ![decollage-poster](examples/gallery/decollage-poster.png) | ![riso-editorial](examples/gallery/riso-editorial.png) |
| `pop-halftone` | `decollage-poster` | `riso-editorial` |
| ![analog-scrapbook](examples/gallery/analog-scrapbook.png) | | |
| `analog-scrapbook` | | |

```bash
python3 scripts/collage.py --list
python3 scripts/collage.py --preset cubist-grid --out cubist.png --seed 4
```

## Run the pipeline manually

```bash
JOB=examples/my-job && mkdir -p $JOB

# 1. Write $JOB/concept.json following references/concept-schema.md
#    (normally the agent does this for you from your text)

python3 scripts/source_assets.py --concept $JOB/concept.json \
    --out-dir $JOB/assets --per-motif 1
python3 scripts/theme_to_recipe.py --concept $JOB/concept.json \
    --assets $JOB/assets --recipe $JOB/recipe.json --cutouts $JOB/cuts \
    --seed 11 --format poster
python3 scripts/collage.py --recipe $JOB/recipe.json --out $JOB/final.png
```

Every step produces a readable artefact — `concept.json`, `SOURCES.json`,
`cuts/*.png`, `cuts/contact-sheet.jpg`, `recipe.json`, `recipe-rationale.md` —
so you can inspect and revise any decision instead of treating the output as a
black box.

## Licensing and attribution

Source photographs come from Wikimedia Commons and retain their own licences.
`SOURCES.json` in each job records the author, licence, licence URL and source
page. CC BY / BY-SA works require attribution; BY-SA may additionally require
the combined work to be shared alike. Check the manifest before publishing a
finished piece. Everything else in this repo (code and generated paper textures)
is MIT-licensed.

## Roadmap

- More cut-paper edge types that still follow visible image content
- Additional image sources with licence filtering
- Multi-page / series output from a long text
