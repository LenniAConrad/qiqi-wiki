<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Player wiki roadmap — owner request, 2026-10-09

The existing atlas is useful but is not a practical manual. Expand it into an original, searchable, statically hosted wiki that answers “how do I use this?” for ordinary players. Preserve existing biome/animal/island galleries and provenance. Do not rewrite old measurements as current evidence.

## First release

1. Audit the latest landed Voxelgame source and actual normal input. Establish a feature/status/control/recipe catalog tied to game commit and version, not inferred from agent backlog promises.
2. Clear navigation, search, Getting started, controls and survival/creative differences. Practical steps with prerequisites, relevant keys/buttons, expected outcome and a tested game screenshot where useful. Player language, not implementation jargon.
3. Crafting/materials/tool tiers and durability, inventory/stack movement/tooltips, resource gathering, cooking/furnaces, building/storage/glass, combat and Erik/Thor interaction/spawning.
4. Maps/exploration/caves, boats/sailing/wind controls and recovery, weather/water/fire/lava when implemented. Explain map visibility by mode and travel controls truthfully.
5. Built-in character and building tools: short actual workflows with valid file formats and safe recovery guidance.
7. Platform install/update, graphics settings/performance, multiplayer connection, common failures and native error-window/log instructions as available.

## Ongoing maintenance

Read agent-hub/backlogs/voxelgame.md, landed.log and current game source. For every newly landed player-facing feature, update the relevant guide and its version/commit receipt. Claims need source or actual gameplay evidence; planned pages are visibly labelled. Keep a wiki coverage ledger linking each feature to guide/evidence/next update. Coordinate feature agents to supply actual controls/recipes/screenshots. Wiki work should continue between game releases, not only at final cleanup.

No invented screenshots, proprietary copied artwork, hidden runtime service dependency or mandatory paid APIs. Static relative links must work on GitHub Pages and offline. Use small coherent commits, validate metadata/images/links/scripts, inspect browser layouts at mobile and desktop sizes, keyboard/tooltip/search accessibility and offline behavior. Reuse existing design rather than gratuitously replace the atlas. Publishing is authorized by the owner's request for a separate statically GitHub-hosted wiki; maintain exact original-asset/licence/provenance notices.

## Latest owner additions

Performance and memory analysis must include current measured FPS/frame-time/stutters/CPU/process RSS/peak RAM/system memory/VRAM, settings and loading/streaming/horizon/water comparisons with reproducible hardware/game-commit/seed/settings receipts and artifact-derived plots. Do not substitute old archived figures or guess metrics.

Installation guides must cover the requested update script and installer update-existing path, player-data preservation, failed-update recovery/rollback and version checks when implemented. Coordinate VOX-OWNER-UPDATE-INSTALLER; mark unimplemented functionality as planned.

## Progress — 11 October 2026

- **Coverage ledger (QW-COVERAGE):** `features.html` lists 187 base-game features of Voxelgame main `dd29d91` with one status each, verified controls, source evidence, the request IDs of planned work, 13 ranked guide gaps and 6 places where the game's documents disagree with its code. `data/features.json` is the source; `tools/build_features.py` renders and `tools/validate_features.py --game` checks it against an export from `tools/export_game_snapshot.sh`. It is a source audit, not a play test.
- **Deployment fix:** the Pages artifact now includes the linked performance reports; links are validated inside the staged site.
- **Browser QA:** `tools/browser_run.py` drives headless Firefox through Marionette for in-page checks, real keyboard input, `file://` loading and 1440/820/390 px captures without overflow.
- **Player guides (QW-PLAYER-GUIDES, first slice):** `guides.html` indexes four source-checked guides (Getting started, Controls reference, Your first survival day, Crafting and recipes). `data/guides.json` holds the structured text, `data/recipes.json` the 37 recipes, `tools/build_guides.py` renders them, `tools/link_guides.py` points the ledger at the owning guide and `tools/validate_guides.py [--game SNAPSHOT]` checks everything, including the recipe amounts against the game registry. Guides are source-checked and carry headless screenshots; none is a recorded play session yet.
- **Next:** guides ranked 5 onward in the ledger (maps, installation, building, sailing, hunting, settings, troubleshooting); then the measured performance and memory study.

## Base-game publication slice — 11 October 2026

The public ledger and generated controls now cover the base game only. Optional gallery files were removed from the current tree; original assets and provenance remain in Git history at `493c52c`. The source audit remains `dd29d91`; publication filtering is not a newer game audit. Guide-gap ranks retain their original IDs.

## Wiki interface slice — 11 October 2026

The home now provides eight player categories, the four written guides and an
Atlas section. The original biome gallery lives at `atlas.html`; animal habitat
links and old biome bookmarks point there. Shared category navigation is rendered
from `tools/wiki_layout.py`. The four guide articles use a title, breadcrumb and
contents list. An offline search script contains 320 guide, base-game feature,
recipe and biome records. New files are explicitly allowlisted.

Static validation is available in `tools/validate_wiki.py`; actual desktop/mobile,
keyboard and file-URL browser inspection remains the parent integration gate.
No new game facts, recipes or screenshots were added.

## Blocks reference — 12 October 2026

`blocks.html` lists the 177 core registry entries at Voxelgame `65364e6`, with
base colour swatches, stable anchors and recipes linked at their existing
`03c6519` audit. `tools/build_blocks.py --game SNAPSHOT` extracts the registry;
`tools/validate_blocks.py --game SNAPSHOT` compares every entry to its source.
The material-catalogue ledger entry now links this partial reference. Gathering
methods, drops and tool requirements remain outside this source-only slice.
Desktop/mobile, keyboard and file-URL browser review belongs to parent integration.

## Mobs reference — 12 October 2026

`mobs.html` groups the preserved 93-species animal atlas by family, with
habitat names linked to the biome atlas and small previews of existing models.
Its catalog, models and habitat provenance retain the 28 September 2026 date.
`tools/build_mobs.py` renders it without changing the original datasets or assets.
`tools/validate_mobs.py --game SNAPSHOT` checks that every listed species belongs
to the supplied core registry; it does not relabel the older atlas as a new audit.
Spawning and peaceful-animal ledger entries now link this partial reference.
Current-snapshot Swan has no preserved atlas entry and remains outside this slice.
Browser review remains a parent integration gate.

## Topic structure — 13 October 2026

Ten topic indexes now organize all 22 existing guides, the blocks and animal
references, and the preserved galleries. Building, exploration, equipment and
vehicle topics lead to their written articles; the home no longer labels
published work as unwritten. Article breadcrumbs identify the owning topic.
Related articles, quick section links and 643 offline search records connect
the existing material without changing game facts or audit dates.

`data/topics.json` owns this structure. `tools/build_wiki.py` renders the home,
topic pages, shared gallery navigation and search. The shared reading layout
uses the game's turf, soil and sand palette, with a dated atlas photograph on
the home. A native disclosure provides mobile navigation; without JavaScript,
navigation remains open and every topic and article can still be read.

The finite overhaul's fresh captures, full game/wiki changelog and measured
image-loading work are separate remaining slices. Do not label the full
overhaul complete based on this navigation delivery.

## Image loading, island preview slice — 13 October 2026

The island gallery now selects 480/960-pixel previews instead of downloading
2048-pixel maps and 3840-pixel panoramas for its cards. Opening a view still
loads the recorded original. Twenty-four derivatives add 486,830 image bytes
to the deployable collection; they do not replace source images or receipts.

Matched cold-profile Firefox measurements against `185455d`, at 1440 × 900
and 390 × 844, recorded the following local encoded response bodies. The
extra request is the small thumbnail lookup script.

| Initial page | Before | After | Requests before → after |
| --- | ---: | ---: | ---: |
| Desktop | 1,846,187 B | 176,504 B | 16 → 17 |
| Mobile | 715,620 B | 122,110 B | 11 → 12 |
| First gallery row, desktop (cumulative) | 2,814,555 B | 218,352 B | 20 → 21 |
| First gallery row, mobile (cumulative) | 1,179,530 B | 140,668 B | 13 → 14 |

In the bounded local network model (200,000 bytes/s shared across responses,
150 ms added response latency), the mobile initial view settled in 5.259 s
before and 2.505 s after; the first gallery row settled in 13.230 s and 4.546 s
cumulatively. Each value is one observation on the shared host, including the
runner's settling interval. These are not real-phone or LCP measurements and
are not a general speed guarantee. Live Pages checks remain part of landing.

The gate checks source and derivative hashes, dimensions, aspect ratios and
the browser lookup. Browser review compares actual desktop/mobile previews
and verifies full-size images load only after opening a view. The home,
animal/biome galleries, guide images and eventual changelog still need the
rest of the full image-performance acceptance; QW-ASTRA-IMAGE-PERF stays open.


## Image loading, galleries and guides — 13 October 2026

The home and biome gallery now use 480/640-pixel previews; animal cards use
192/320 pixels, and the Mobs reference uses 72/144-pixel candidates for its
72-pixel cells. Four guide screenshots have 640/960-pixel previews and keyboard
accessible links to their originals. High-density displays can choose larger
candidates, including the source image. The main landscape remains eager and
high priority; below-fold pictures retain lazy loading and async decoding.

The 564 derivatives add 7,398,146 bytes. The complete published image collection
therefore grows from 25,350,862 to 32,749,008 bytes: full views still need the
preserved originals. The benefit is smaller page requests, not a smaller
full-gallery archive. Original image bytes, game dates and capture receipts
are unchanged. The ledger's image-coverage note records this distinction.

The following are matched cold-profile Firefox observations against `07c1204`.
Desktop content viewport was 1440 × 814; mobile was a fully visible 390 × 844
iframe, at device pixel ratio 1. The home row is its initial view. Other rows
include the initial page and the first gallery/reference/guide image after
scrolling. Bytes count completed encoded response bodies, including HTML,
styles and scripts. Request counts include the small new gallery helper.

| Page and viewport | Before → after bytes | Requests | Settled seconds |
| --- | ---: | ---: | ---: |
| index.html · desktop | 301,492 → 234,007 | 8 → 8 | 1.165 → 1.095 |
| animals.html · desktop | 445,296 → 357,532 | 23 → 24 | 3.107 → 20.053 |
| atlas.html · desktop | 1,729,729 → 604,031 | 21 → 21 | 2.672 → 9.726 |
| mobs.html · desktop | 273,158 → 186,248 | 20 → 20 | 13.152 → 2.220 |
| guide-getting-started.html · desktop | 107,020 → 97,252 | 8 → 8 | 8.941 → 5.989 |
| index.html · mobile | 293,940 → 216,394 | 7 → 7 | 1.185 → 1.181 |
| animals.html · mobile | 336,066 → 293,215 | 12 → 13 | 11.268 → 3.172 |
| atlas.html · mobile | 497,626 → 208,596 | 10 → 11 | 10.514 → 4.156 |
| mobs.html · mobile | 67,400 → 43,790 | 9 → 9 | 4.390 → 3.240 |
| guide-getting-started.html · mobile | 85,052 → 58,534 | 7 → 7 | 3.832 → 5.580 |

The bounded mobile network model shares 200,000 B/s across responses and adds
150 ms response latency. Each timing below is one observation on the shared
host, including the settling interval; disk contention was observed during
this work. These are not LCP, real-phone, or general loading-speed guarantees.

| Page / same checkpoint | Before → after seconds, constrained mobile |
| --- | ---: |
| index.html | 2.887 → 2.524 |
| animals.html | 5.399 → 6.260 |
| atlas.html | 7.968 → 160.995 |
| mobs.html | 5.189 → 8.548 |
| guide-getting-started.html | 5.714 → 43.705 |

The guide timing worsened in the constrained run despite fewer bytes. Report
that observation alongside the reductions; do not infer universal time gains.
Early incomplete runs are superseded: the measurement helper now excludes
images outside either viewport axis and its mobile iframe fits entirely inside
the parent viewport. Otherwise browser chrome can clip the iframe's bottom,
so native lazy loading correctly defers images the child thinks are visible.
A local temporary wrapper also permits real mobile `file://` checks.

The preview gate checks source/derivative hashes, dimensions, complete width
sets, original-byte savings and the generated helper. `srcset` candidates are
included in staged relative-link validation. Content-specific filter and encoder
receipts live in `data/gallery-previews.json`; regeneration is in README.
Initial quality-92 guide previews could be heavier than their sources; inspected
quality-86 versions resolved that, and a regression rejects larger derivatives.
Fresh game captures, habitat scenes, the changelog and its loading measurements,
CI maintenance and the final handoff remain separate overhaul work.

## Game and wiki history — 13 October 2026

The main navigation and home link two dated changelogs. The game chronology
reviews the available 704-commit interval from `6c39b717` (16 August) through
`5856103c` (13 October); wiki history reviews 93 commits from `ae659a32`
(9 October) through `17fbfdb3` (13 October). Eighty-two curated change groups
cover the recorded period, with source identifiers, additions/changes/fixes
and separate compatibility notes. This is a source review, not a new play test.

Compatibility distinguishes world-save format 29, network protocol 16 and
blueprint format 1. Earlier save and network changes keep their own dates;
legacy elevated workshops remain separate from new flat workshops. Neither
checkout has tags. The public game release endpoint returned 404; wiki releases
were empty. Entries therefore use commit dates without invented release names.
Coarse early snapshots, omitted internal/optional content and the cutoff are
explicit. The older feature and gallery receipts are unchanged.

`data/changelog.json`, `tools/build_changelog.py` and
`tools/validate_changelog.py` supply deterministic HTML and checked provenance.
README describes incremental maintenance. The pages work without JavaScript or
images; source disclosures, date links and switching use native HTML. Browser,
payload and actual Pages receipts are required before closing this slice.

The same source review found the X shortcut still documented as choosing the
first affordable recipe. Its ledger row, generated controls/crafting text and
first-survival-day note now follow `a6d56495`, checked at `5856103c`: X repeats
the selected Craft-tab recipe and reports missing materials. Only that row's
receipts and the affected guide verification notes were refreshed. The save
rollback note already said format 29 after the milestone update; it required
no correction. No new gameplay test is claimed.
