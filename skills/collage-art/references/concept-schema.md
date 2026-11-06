# Concept JSON schema

The concept file is the hand-off between the interpretive step (done by the
agent reading the user's text) and the deterministic pipeline. It is plain
JSON, UTF-8, no comments.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `theme` | string | yes | Short label for the brief. Used in the rationale and as a fallback headline. |
| `statement` | string | yes | One sentence: "X meets Y, which suggests Z." The argument of the piece. |
| `headline` | string | no | Short phrase cut from a magazine. Uppercased at render time. Keep under ~18 characters for a poster. |
| `kicker` | string | no | Small monospace line above the headline. |
| `strategy` | enum | yes | `cubism`, `dada`, `surrealism`, `pop`, `decollage`, `editorial`. Chooses paper, edges, rotation range, font, tape and marks. |
| `palette` | string[] | no | 2–4 hex inks, dominant first. Defaults to the paper's ink set. |
| `motifs` | object[] | yes | 2–4 entries, described below. |

Each motif:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | yes | Short ASCII slug; becomes the downloaded filename. |
| `query` | string | yes | 2–4 concrete English words for Commons. No aesthetic adjectives, no abstract nouns, avoid queries that return portraits. |
| `role` | enum | yes | Exactly one `hero` (largest piece), plus `ground` and/or `satellite`. |
| `why` | string | yes | What this image contributes to the pairing sentence. Appears in the rationale. |

## Choosing a strategy from the text

- Opposition, protest, irony, noise, media saturation → `dada`
- Dream, distance, memory, one strange object in a calm frame → `surrealism`
- Analysing a subject from several sides, cubist faceting, printed matter → `cubism`
- Consumer culture, bright single icon, onomatopoeia → `pop`
- Peeling, decay, layers of street posters, half-lost words → `decollage`
- Article, cover, e-commerce banner, typographic hierarchy → `editorial`

## Worked example

See `examples/demo/concept.json` in the repo. It turns 潮汐与城市 ("tide and city")
into the pairing sentence "The returning tide meets the sleeping city,
suggesting a memory that keeps coming back", then into three photographable
motifs (breaking wave, night skyline, lunar crater) under a Surrealist arch.

## Validation

`source_assets.py --offline` validates that every motif has `id` and `query`
without making network calls. `theme_to_recipe.py` validates the strategy name
and will refuse an unknown one.
