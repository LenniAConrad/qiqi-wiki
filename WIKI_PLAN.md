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
and 390 × 844, recorded the following sums of exposed response-body sizes. Mobile values
omit HTML when Firefox reports a zero-sized navigation entry; see the measurement
correction below. The extra request is the small thumbnail lookup script.

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
scrolling. Bytes are browser-reported response-body sums. The mobile rows omit HTML
(see the measurement correction below); desktop rows include it. Request counts
include the small new gallery helper.

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

**Measurement correction:** the new changelog checks exposed zero-sized HTML
navigation entries in Firefox's mobile iframe. This also affects the earlier
gallery receipts: 9/18 live rows and 18/27 local rows in the last gallery run.
The mobile byte sums above are browser-reported partial sums, excluding HTML;
they are not complete page totals as the earlier wording suggested. Preserve
the raw receipts and image-size reductions, but do not infer full page savings
from these partial sums. The runner now marks incomplete totals as null, lists
the unmeasured URLs and keeps exposed bytes in separate fields. Complete mobile
transfer accounting remains part of the open image-performance acceptance.

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

The final browser review checks both histories at 1440/820/390/320 px, real
keyboard source disclosures, date links and page switching, mobile navigation,
search, and desktop/mobile file URLs with and without JavaScript. Before/after
home captures and native reading views were inspected. The two histories add
no image downloads or runtime dataset request. Their uncompressed HTML files
are 53,912 and 23,308 bytes; there was no previous published changelog to measure.
Home HTML/styles/search grow by 5,004 uncompressed bytes; image files are unchanged.

| New page | Desktop reported bytes / requests | Mobile requests | Local settled seconds: desktop / mobile / constrained mobile |
| --- | ---: | ---: | --- |
| Game history | 97,140 / 7 | 6 | 1.582 / 58.269 / 35.402 |
| Wiki history | 66,536 / 7 | 6 | 43.131 / 24.979 / 60.668 |

Both mobile byte sums expose 42,947 bytes of styles/scripts and omit the HTML
navigation body; complete mobile byte totals are unavailable from these readings.
The constrained profile shares 200,000 B/s with 150 ms response latency. Heavy
shared-disk contention affected these single observations, including browser
startup. These are not LCP, real-phone results or a speedup claim. Raw and
corrected receipts are retained; live Pages verification follows the normal land.

## Loading-accounting repair and CI — 13 October 2026

The browser runner now measures mobile pages in a same-origin iframe at exactly
390 × 844. Its existing-CSS setup request and any other parent requests have
their own `harness` receipt. This exposes the HTML response size; the previous
opaque parent hid it. HTTP caches remain disabled in a fresh profile, but the
setup warms the origin connection and is included in settled time. This method
must not be described as a fully cold connection or a real-phone benchmark.

`tools/check_loading_browser.py` checks real gzip HTML/CSS and an image against
the local server's response log, including repeated requests and separate wrapper
overhead. Desktop and mobile pass at the measured viewport sizes. The earlier
direct-navigation candidate was rejected because it measured a 590-pixel top-level
page. The static gate also rejects missing or duplicate document timing entries;
unknown response sizes still make totals null. Old raw readings are preserved.
Completed matched measurements and their accepted/excluded checkpoints are recorded below.

Pages validation and deployment pin Ubuntu 24.04 and exact upstream releases of
checkout 7.0.1, setup-python 7.0.0, setup-node 7.1.0, upload-pages-artifact 5.0.0
and deploy-pages 5.0.1. The JavaScript actions use Node 24; the validation tools
remain Python 3.12, Node 22 and Pillow 10.2.0. The normal hosted Pages run is the
delivery gate. These tooling changes do not refresh any game or media receipts.

## Media source prerequisite — 13 October 2026

The metadata builder now classifies Swan as a bird and reads its conditional
ambient-habitat branch. At checked game source `9e946731`, that branch names
Wetland Fen, Flooded Grassland, Inland Delta and River Delta. The older parser
read only the static guilds and would have left Swan's habitat list empty.
All 94 current species have candidate habitats across the same 92 biome IDs;
these source candidates do not guarantee a spawn or imply a measured frequency.
Five focused regressions cover the legacy guilds, conditional branch, category,
unknown species/biomes and rejection of unreviewed conditions.

The public gallery remains the preserved 93-species snapshot. Current portraits
and habitat scenes still require a full isolated game export, a renderer, actual
captures, source/asset receipts and visual review. The documentation snapshot
exporter omits binary assets and Cargo.lock and is insufficient for that build.

## Completed loading samples — 13 October 2026

Matched Firefox readings compare the preserved `185455d` site with the current
public files (unchanged since `bd2616b`). All reported samples include the HTML
body and have no unmeasured response bodies. Matched pairs use identical recorded
runner hashes, browser, viewport and DPR 1. Old incomplete readings remain preserved.

Mobile uses a 390 × 844 iframe; desktop content is 1440 × 814. Each page starts
in a fresh profile with HTTP caches disabled. The same-origin mobile setup fetch
is recorded separately and warms the origin connection; settled time includes
it. Body sums cover the completed document/resource entries at the checkpoint,
not the entire gallery archive or a packet capture. The home checkpoint is its
initial view; other image pages include the first media row after scrolling.

| Mobile page / checkpoint | Before → after encoded bodies | Reduction | Requests | Settled seconds |
| --- | ---: | ---: | ---: | ---: |
| Home | 301,211 → 228,916 B | 24.0% | 7 → 7 | 25.608 → 51.594 |
| Animal gallery | 381,051 → 310,816 B | 18.4% | 16 → 17 | 17.620 → 41.448 |
| Getting started | 106,739 → 84,180 B | 21.1% | 7 → 7 | 31.799 → 22.554 |
| Islands | 2,321,386 → 198,126 B | 91.5% | 17 → 18 | 62.093 → 20.822 |

The constrained local profile shares 200,000 B/s and adds 150 ms response
latency. These are individual observations on a busy shared host. Several
timings get worse despite fewer bytes; these data support response-body savings,
not a universal loading-time improvement, LCP result or real-phone benchmark.

| Constrained mobile / same checkpoint | Before → after encoded bodies | Requests | Settled seconds |
| --- | ---: | ---: | ---: |
| Home | 301,211 → 228,916 B | 7 → 7 | 28.276 → 12.676 |
| Animal gallery | 381,051 → 310,816 B | 16 → 17 | 16.576 → 21.559 |
| Getting started | 106,739 → 84,180 B | 7 → 7 | 89.485 → 5.593 |

The matched desktop home records 301,492 → 239,011 encoded body bytes
(8 → 8 requests); settled time is 42.363 → 28.979 s.

Live Pages readings below include the same page checkpoints and actual response
compression. Do not compare their compressed text sizes directly with the
identity-encoded local server. The two histories had no published counterpart
in the baseline; their rows are new-page costs, not before/after savings.

| Live page | Viewport | Encoded bodies | Requests | Settled seconds |
| --- | --- | ---: | ---: | ---: |
| Home | mobile | 75,453 B | 7 | 19.902 |
| Animal gallery | mobile | 98,795 B | 17 | 51.532 |
| Getting started | mobile | 35,526 B | 7 | 43.573 |
| Islands | mobile | 124,121 B | 18 | 79.896 |
| Game history | mobile | 23,224 B | 6 | 88.413 |
| Wiki history | mobile | 17,468 B | 6 | 72.648 |
| Home | desktop | 85,500 B | 8 | 73.155 |

The private receipts contain 38 raw checkpoint records, of which 36 are accepted complete rows: 12 before, 14 current, 10 live.
The initial constrained getting-started checkpoint in each local run still had
a selected lazy image pending. Those two raw records are retained and excluded
from accepted results; the completed first-media checkpoints are used above.
The generator, source images, capture dates and public image collection are
unchanged by this measurement work. Fresh current-build media and its derivative
review remain part of the open overhaul. Regeneration and measurement commands
are in README; raw requests, image selections, setup costs and runner hashes
remain in the retained measurement receipts.

## Reproducible media inputs — 13 October 2026

`tools/freeze_media_source.py` exports a complete committed tree into new private
scratch, including binary assets and the lockfile. It records every file hash,
the commit, tree and archive, rejects incomplete exports, and never writes into
the game checkout. Six regressions check preservation of working changes,
binary/lockfile inclusion, changed inputs, path boundaries and render receipts.

`tools/render_animal_capture.py` wraps the existing portrait renderer with actual
Blender settings and input/output hashes. The animal builder can verify that
receipt against the full snapshot before assigning its commit to new images.
README records the separate freeze, export, headless render and publication steps.
Full source, raw renders and native logs stay outside the published wiki.

The isolated `9e946731` export built successfully and produced all 94 species.
Blender 4.5.3 LTS starts headlessly. A Swan smoke run wrote four 512-pixel views
and its actual 16-sample Eevee settings; its outer timeout was 124 during shutdown,
so that failure is retained rather than reported as a clean process exit.
The previous 93-species gallery and derivatives are privately archived at their
exact wiki commit, `6aca599`. This prerequisite does not update the public gallery
or its coverage: fresh portraits, habitat scenes and displayed-size review remain
part of QW-ASTRA-MEDIA until their own verification and delivery.

## Current animal portraits — 13 October 2026

The gallery and Mobs reference now cover all 94 species at game commit
`9e946731`, including Swan and its four source-backed freshwater habitat
candidates. All 376 portraits were rendered again from the production pose
meshes and exported materials. The unmodified game source, recursive file hashes,
exporter, actual Blender settings and every mesh/material/output hash are retained.
The complete headless run exited successfully. The older September collection
was privately archived before replacement; animal artwork and geometry were not edited.

The final images are 512 pixels square, WebP quality 92. All four views per
species were inspected in contact sheets, with native-size Swan, ant and whale
checks. New 72/144/192/320-pixel previews use Lanczos at quality 90 after comparing
nearest, BOX and Lanczos on thin legs, markings, feather steps and dark silhouettes
at displayed sizes. This decision applies to this collection. These remain studio
poses; actual habitat scenes and the other media refresh work are still open.

The builder now finds model and atlas source modules recursively. The old
hard-coded `bird_models.rs` path no longer exists in this game snapshot; its
failed first catalog build is retained, and a regression covers split modules.
Source hashes are checked before image replacement. The full receipt catalog
remains downloadable. The browser script contains all display fields and omits
the receipt hashes it never reads; the validator compares it to the full catalog's
exact display projection. The script shrinks from 243,472 to 123,990 uncompressed
bytes compared with the previous published gallery.

The original portrait collection changes from 3,358,360 bytes for 93 species to
3,356,804 bytes for 94. Animal previews change from 850,584 to 868,106 bytes. Full
portraits remain available on demand; raw PNGs and game source stay private.
The biome photographs, survey frequencies and island galleries keep their older
generation-9 receipts. Fresh animal portraits do not relabel that evidence.

Matched local browser checkpoints compare the previous published gallery at
`f469610` with this collection. Each page uses a fresh Firefox profile with HTTP
cache disabled, first at its top and then at the first media row. All visible
images were complete and all recorded response body sizes were available. These
figures include HTML and the requests completed at that checkpoint; Firefox's
lazy loading changes the request set. They are not a whole-page download or a
load-time claim. Text is uncompressed on this local server.

| Page | Viewport | Before bodies | Current bodies | Before/current requests |
| --- | --- | ---: | ---: | ---: |
| Animal gallery | desktop, 1440 × 814 | 344,617 B | 240,652 B | 21 / 24 |
| Animal gallery | mobile, 390 × 844 | 305,624 B | 191,697 B | 15 / 17 |
| Mobs reference | desktop, 1440 × 814 | 184,481 B | 188,634 B | 16 / 20 |
| Mobs reference | mobile, 390 × 844 | 181,418 B | 182,373 B | 12 / 12 |

The gallery checkpoint improves by 30.2% on desktop and 37.3% on mobile; the
reference increases by 2.3% and 0.5%. The main reduction is the smaller display
script. Mobile uses a same-origin CSS wrapper, whose setup request is separate
from the page totals and warms the connection. DPR is 1; these are browser
viewports, not physical-phone measurements. Raw requests and captures stay in
the worker's retained `media-refresh/browser-before` and `browser-after` receipts.

Desktop/mobile visual review, real keyboard search/view/navigation controls,
local-file gallery behavior and the 94-row reference without JavaScript pass.
The static gate passes 78 tests, 44 pages and 4,004 local references, including
the staged base-game-only check. Source-backed animal and Mobs validators also
pass against the frozen capture tree. Two private browser-harness errors were
retained and corrected before the remaining checks passed; they required no
website change. Final live delivery is recorded in the worker's Pages receipt.

## Revised public scope — 13 October 2026

The owner's later concise-catalog direction takes priority at the next safe
unit after the current portrait delivery. Public pages should introduce the
survival game briefly and show its biomes, animals and items with clear names,
short natural descriptions and useful imagery. The landing page and navigation
need to emphasize those routes. The public changelog should group actual shipped
player-visible changes by calendar day, with brief “Fixed” or “Changed” entries.
Commit hashes, development narratives and gate/performance receipts belong in
the retained internal evidence. The landing/catalog revision is described below. The daily changelog revision is described below; fresh biome captures remain
open in the same finite assignment.


## Concise landing and catalog — 13 October 2026

The home now briefly explains survival and creative play and presents biomes,
animals and items before the longer guide directory. The Items index has six
short descriptions backed by the existing guides and recipe data. The shared
menu has eight destinations, with a single current-route marker on every page.
All ten topic indexes and original public URLs remain available; the ledger
and archived performance reports retain their evidence and direct links.

Offline search focuses on catalog entries, recipes, guides and dated updates.
The development ledger no longer fills the results. The home reuses the dated
September meadow/pine captures and the reviewed October Fox/Swan portraits,
with responsive image candidates and lazy loading below the main landscape.
This is a presentation update, not a fresh biome capture or a new game audit.
The owner-requested daily changelog and current biome/habitat captures remain
open. Browser, loading and final deployment receipts are recorded separately.

The gate passes 80 tests and 3,735 local references across 44 pages. Browser
review covers desktop/tablet/mobile layouts, real keyboard search and menus,
320/390-pixel scrolling, all shared navigation, local files and no-JavaScript
reading. Scrolled mobile captures confirm the lazy catalog images load before
inspection; full-page captures alone do not prove that.

Matched local initial-view response bodies change from 239,216 to 188,192 bytes
on desktop (8 to 11 requests) and 229,121 to 178,097 on mobile (7 to 10). Each
profile is fresh with caches disabled; the mobile CSS wrapper warms the origin
and its setup is counted separately. HTML bodies are included and all sizes
are known. These are page checkpoints, not complete gallery downloads. Observed
settling times rose from 55.629 to 73.899 seconds and 26.085 to 63.334 seconds
respectively on the busy host. This supports smaller payloads, not a time gain.
Source images are unchanged; the catalog search script is now 85,412 bytes.
Raw measurements and final visual receipts are retained in the worker's
`player-home/` scratch, with before/after/final images under
`renders/qiqi-wiki/astra-player-home/`.


## Brief daily changelog — 13 October 2026

The game and wiki histories now show short plain-language bullets under their
calendar dates. All 21 existing date URLs and both history pages are preserved.
Eighty-four public summaries cover 86 recorded entries; two internal-only rows
keep their evidence without an announcement. All 82 original narratives and
references, plus the five compatibility records, remain intact in the maintenance
dataset. Four already-landed wiki changes extend its reviewed cutoff to fbd5f19:
initial histories, corrected X guidance, the 94-species portraits and the new home.
The game cutoff remains 5856103c; this is not a new audit of later game changes.

The complete history JSON is excluded from Pages. Public entries and search
use only reviewed summaries/titles; no fallback exposes an internal narrative.
The validator requires short explicit summaries or an internal-only reason,
while preserving all source-date/reachability checks. Short updating reminders
use a native collapsed disclosure. The two browser harnesses that still expected
the former home/menu names have been updated to the delivered catalog navigation.
README records the repeatable update and publication checks. Fresh biome/habitat
captures and the full overhaul handoff remain open.

The normal static check passes 82 tests, 44 pages and 3,731 relative references;
the staged site has 1,210 files and excludes the internal chronology. Read-only
source checks verify 704 game commits with 230 references and 107 wiki commits
with 70 references. Actual desktop/mobile review, keyboard date links/history
switching/update disclosure, search, local files and no-JavaScript reading pass.
Both the daily-history and existing guide browser harnesses pass.

Generated game-history HTML falls from 53,577 to 12,861 bytes; wiki history from
22,973 to 5,067 bytes. These are exact uncompressed file sizes, not transfer or
timing measurements. No images or runtime dataset requests were added. Raw
before/after captures, file hashes, source archive and review receipts are in
`daily-changelog/` scratch and `renders/qiqi-wiki/astra-daily-changelog/`.


## Private biome survey preparation — 13 October 2026

The old survey runner stopped with `KeyError: sourceFilesSha256` on the complete
media-source manifest. It now verifies that manifest format as well as the
archived format, and stages the survey, reviewed camera candidates and their
completion receipt in a new private directory. Public atlas data is never a
survey output. Failed commands or changed inputs leave private evidence without
a completed survey receipt. Source/module, sample-contract, site and camera
checks remain required; the fixed reference sampling design is unchanged.

Coverage ledger: the 94-species animal portraits retain their delivered receipt;
biome photographs and sample frequencies remain the September generation-9
snapshot. No game feature, guide, image date or public coverage status is advanced
by this tooling prerequisite. Current-generation sampling, native capture-tool
integration, fresh biome/habitat photographs and visual review remain open.
Fixture regressions exercise orchestration only. NN/Janus retain compute priority;
no native survey, game build or new photograph is claimed for this unit.

Fourteen orchestration regressions pass; the complete static gate passes 96
tests, 44 pages, 3,731 relative references and the 1,210-file staged publication
boundary. All published files are unchanged. Read-only preflight of the retained
animal source verified its 1,836 recorded inputs, then rejected one unrecorded
Python import cache. That cache and the source were preserved. The next survey
must use a clean current-source export; this is not a failed gameplay survey
or a reason to relabel the old images.

## Private biome capture and publication preparation — 14 October 2026

The current-generation survey now has a private capture/replacement path. A
bounded offline devtools build records its exact inputs and executable. Pilot
captures can resume into a full set; source, checked-site, replay, native-exit
and image mismatches cannot produce a valid completion receipt. Publication
preparation assembles and validates a private catalog. A separate replacement
step archives every overwritten file before changing the own-worktree atlas.
The public validator accepts the new evidence format without relabeling the
existing generation-9 catalog. README records the commands and recovery path.

Coverage ledger: this is a tooling prerequisite only. Existing 94-species
portraits retain their delivered receipt, and biome photographs, sample counts,
gameplay facts and public dates remain unchanged. Fresh native biome/habitat
photographs, content/display review, derivative loading measurements, normal
gate, publication and full overhaul handoff remain open. Fixture tests use
synthetic private images and reused survey shapes; they are not game evidence.
Equal NN/Voxelgame/Janus scheduling supersedes the older priority note above.
The coordinator admitted low-I/O authoring only; no native build, survey, game
capture, browser session or land was launched in this unit.

Focused validation passes 35 tests across capture orchestration, survey staging
and source snapshots, including the unchanged archived atlas. All 1,210 public
paths are unchanged by this source checkpoint. The full static gate and normal
land remain pending a capacity allocation; no deployment receipt is claimed.

## Approved header branding, source checkpoint — 14 October 2026

The shared header now includes the owner's approved rainbow cube beside Qiqi
and the descriptor “Player wiki”. The canonical SVG is copied byte-for-byte
from game commit `a07f2748da593ca1207417a39ccd73a14f44d9eb`, with its licence
notice intact and commit/tree/blob/SHA-256 receipts in `data/brand-source.json`.
It uses a relative local image path and explicit dimensions. The small-screen
layout places the descriptor under the name and lets the header wrap; the
existing cream, green and rust palette, navigation and search are retained.

Coverage ledger: this is the source-only part of
`QW-HOME-BRAND-REFINEMENT-20261014`, not a completed or published visual change.
Actual before/after desktop/mobile, keyboard and offline browser review, the
full wiki gate, remote-main delivery and live Pages checks remain pending the
coordinator's verification allocation. The sharper real hero, building/crafting
imagery and fresh biome photographs remain open under the same brand/media
claims. Existing gameplay photos, counts and capture dates are unchanged.

Source validation passes 13 existing navigation/publication tests, all 44 shared
headers and 3,776 local references. A source comparison confirms that every
page is unchanged outside its header, with identical navigation and search.
The allowlist contains 1,211 files; the SVG is its only addition and the source
receipt stays private. Static sRGB ratios against the cream background are
11.009:1 for the name, 5.254:1 for the descriptor and 5.888:1 for the existing
focus accent. These are nominal color checks, not rendered visual acceptance.

## Header integration and focused checkpoint repair — 14 October 2026

The retained header and biome-capture tooling landed at `238a26ba`; local and
actual remote main match. Local before/after desktop, 320/390-pixel, keyboard,
search, menu and offline review passed 111 assertions across 26 inspected
captures. The publication check matched 1,211 staged files and 3,776 references.

The intended-head Pages run `38583101769` ran the full static checkpoint and
failed one of 110 tests. The changelog escaping test rejected every image tag,
including the approved shared-header logo. It now compares parsed element
structure before and after an injected summary and requires the complete
escaped text. All seven focused changelog tests and generated-output checks
pass; an in-memory renderer with escaping disabled fails the repaired test as
expected. No published page, asset or renderer changes in this repair.

Coverage ledger: header source is integrated; public delivery remains pending.
The failed workflow skipped deployment, and live homepage bytes still match
`df9ec7f`. `FULL_VALIDATION_PENDING` remains until the repaired source passes
the intended-head hosted checkpoint and actual live checks. All four retained
claims stay open. Fresh biome/habitat photos, a sharper real hero and
crafting/building imagery remain unfulfilled; gameplay evidence is unchanged.

## Finite visual refinement — 14 October 2026

The owner's final bounded pass gives the home and shared headings a stronger
game identity: substantial sans-serif titles, compact monospace navigation,
square framing and the existing meadow-turf accent. Six linked colour samples
come directly from the audited block catalog. They are colour swatches, not
rendered blocks. The approved original cube and cream reading surface remain.

The home now shows the existing Meadow photograph with readable foreground
trees and the existing Build-tab screenshot beside the first-day links. Their
28 September and 11 October dates stay visible. No image bytes, capture dates,
gameplay facts, search records or public catalog counts are refreshed. There
is no new media-generation claim. Native current-game photographs remain open.

Coverage ledger: this is one presentation slice of the retained BRAND/MEDIA
claims. Focused navigation/publication checks and source-relative links pass;
actual browser inspection and intended-head publication acceptance are required
before calling this slice delivered. The four open media/performance claims
remain for a named handoff when the finite allocation ends. Dark mode belongs
to the returning wiki worker. The full overhaul remains FULL_VALIDATION_PENDING.
