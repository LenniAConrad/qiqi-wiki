<!-- SPDX-License-Identifier: GPL-3.0-only -->
# qiqi-wiki

Standalone static player wiki for Voxelgame, bootstrapped on 2026-10-09 from the owner's local `qiqi-dev` working files. The original checkout remains untouched. Ten topic indexes connect the written player guides, blocks and animal references, and the preserved atlas. The source-audited **Features** ledger (`features.html`) records base-game features, status and guide coverage. Search uses a local script built from topics, guides, features, recipes, blocks, animals and biomes. See [WIKI_PLAN.md](WIKI_PLAN.md) for the work queue.

Run `bash tools/verify_wiki.sh` before committing. GitHub Pages deploys the static site through `.github/workflows/pages.yml`; `tools/stage_site.py` selects the published files for both CI and the local gate, which checks every link inside that staged copy. No game server or bundler is needed. Preserve the existing original screenshots, data and provenance while refreshing them against actual game builds.

Publication uses an explicit list of pages, browser scripts, datasets, licences
and public reports. Add new public files to `PUBLIC_FILES` in
`tools/stage_site.py`; images must be recorded in the existing gallery/guide
catalogs or the scale manifest. Unknown files stay private, including raw logs,
source patches, engine files, saves and repository instructions. Private capture
evidence is preserved separately. Public footers use `ABOUT.md`, and
the performance follow-up links a public verification summary. The gate checks
HTML and Markdown links inside the staged artifact, with publication regressions
in `tools/test_stage_site.py`.

## Features and guide coverage ledger

Open **Features** in the navigation or `features.html`. Each player-facing
feature has one status for the audited game commit: Available,
Limited, Developer tool, In development or Planned. Features also list their
modes, verified controls, the source files and lines that support them, the
request that tracks planned work, and the wiki page that documents them. The
ranked writing order for practical guides and the places where the game's own
documents disagree with its code are on the same page. Search and the status
filters need JavaScript; the complete ledger is static HTML without it.

`data/features.json` is the single source. Edit it, then regenerate and check:

```sh
tools/export_game_snapshot.sh ../Voxelgame <commit> .cache/game-<commit>
python3 tools/build_features.py
python3 tools/validate_features.py --game .cache/game-<commit>
```

The export reads committed objects only, so the game checkout is never
modified. Without `--game`, the validator still checks the schema, status
rules, guide links, navigation and that `features.html` matches a fresh render.
With it, every cited `path:line` must exist in the exported commit. Planned
features must name the request that tracks them and cannot claim a guide.
Update `audited`, `game.commit` and the evidence together; never relabel old
evidence as a newer commit.

## Preserved atlas documentation

# qiqi-dev · Worldgen Atlas

A standalone HTML/CSS/JavaScript field guide to **all 92 Voxelgame biomes, 93 animals and six island shape families**. The **Animals** navigation link opens `animals.html`, with search, animal-group and biome filters, four model views per animal, dimensions and linked habitats. Each biome entry has a real in-game photograph, field notes describing its implemented terrain and vegetation, and its measured percentage of sampled world surface. Default order is most common first.

## Open it

Double-click `index.html`, or serve this folder:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Then visit **http://127.0.0.1:8765** for the player wiki, or **http://127.0.0.1:8765/atlas.html** for the biome gallery. No install, bundler, accounts, external fonts, or internet connection is required. The site also works directly with `file://` because its data is loaded as a local script.

In the Atlas, search by biome name, description, or features such as **volcano**, **cliff island**, **mountain**, and **steam vents**. Filter by landscape family or change the sort order. Select a photograph to see its seed, biome location, camera position, and sample count. `/` focuses search; the dialog supports arrow navigation and Escape to close. To visit a location, use a world with its listed seed and generator 09, switch to creative mode, open **Shift+M**, enter the dialog’s **Map destination · X Z** values, then press **Enter** or **Teleport**. This selects a safe surface landing. Screenshot viewpoints are separate and may be airborne or underwater.

## Animals

Open **Animals** in the navigation or `animals.html`. Search by animal name,
description or habitat; combine this with a group or biome filter. Select an
animal to switch between resting/moving poses and three-quarter/side views.
Arrow keys navigate animals, `/` focuses search and Escape closes the dialog.
Habitat links open the matching biome, whose details link back to its animals.

The 372 square 512-pixel portraits are studio renders of the game's exact
production geometry and textures, using the existing Blender gallery pipeline.
They are static model previews. Each animal is framed independently, including
tiny insects; portrait size does not represent relative scale. Dimensions are
measured from the resting model. Habitat lists come from the ambient spawn
rules and remain subject to water, terrain and population checks.

`data/animals.json` and its offline script mirror contain all 93 species,
source/mesh/image hashes, dimensions, habitat links and view metadata. Woodland
bats, river otters and penguins join the catalog without changing earlier IDs.
Portraits show fixed poses; swimming and walking cycles are verified in the game
and are not interactive animations in this field guide.
`images/animals/` contains the WebP portraits. To regenerate:

```sh
# Choose an exact game commit and a NEW private HDD scratch directory.
# Run from this wiki; the original game and wiki checkouts are never capture outputs.
CAPTURE=/media/lennart/HDD-Storage-1/wiki-capture-YYYYMMDD
python3 tools/freeze_media_source.py /path/to/Voxelgame COMMIT "$CAPTURE"
mkdir -p "$CAPTURE/tmp"
env CARGO_TARGET_DIR="$CAPTURE/target" TMPDIR="$CAPTURE/tmp" CARGO_BUILD_JOBS=2 \
  timeout 2400 nice -n 10 cargo run --offline --locked \
  --manifest-path "$CAPTURE/source/Cargo.toml" -p voxelgame-render \
  --features creature-gallery --example export_creature_gallery -- "$CAPTURE/meshes"
# Smoke-test one species first by adding --species swan and using a separate output.
# Run full batches through the shared GPU lock on the fleet host.
env -u DISPLAY -u WAYLAND_DISPLAY PYTHONDONTWRITEBYTECODE=1 TMPDIR="$CAPTURE/tmp" \
  timeout 1700 nice -n 10 blender --background --factory-startup --threads 2 \
  --python-exit-code 1 --python tools/render_animal_capture.py -- \
  --game "$CAPTURE/source" --input "$CAPTURE/meshes" --output "$CAPTURE/renders" \
  --source-manifest "$CAPTURE/source-manifest.json" \
  --exporter "$CAPTURE/target/debug/examples/export_creature_gallery"
# Inspect all views and preserve the previous gallery privately before replacing it.
python3 tools/build_animals.py --game "$CAPTURE/source" --meshes "$CAPTURE/meshes" \
  --renders "$CAPTURE/renders" --source-manifest "$CAPTURE/source-manifest.json" \
  --render-receipt "$CAPTURE/renders/render-receipt.json" --date YYYY-MM-DD
python3 tools/validate_animals.py --game "$CAPTURE/source"
```

The full media exporter includes committed binary assets and `Cargo.lock`, which
the smaller documentation snapshot exporter omits. It refuses an existing output
directory or a destination inside the game checkout. A recursive manifest records
every input, the commit, tree and archive hash. The capture wrapper verifies those
inputs, uses the unchanged portrait renderer, and records actual Blender settings,
exporter/script hashes, mesh/material hashes and every output hash. Until all
portraits finish, only `capture-start.json` exists; it is not a completed render receipt.
Keep the process exit status and log alongside the receipt, including any failure
during application shutdown after images have been written.
The builder verifies both receipts before publishing a new dated catalog. Keep
full source archives, binaries, PNGs and receipts in private scratch, outside Pages.
Rebuild gallery previews, Mobs and wiki search after a successful refresh, then
perform the displayed-size, browser and normal deployment checks below.

The data builder derives the species count from the game catalog and checks every
entry and all biome rules; a source layout change requires updating its parser. Its category assignments are field
guide groupings. The animal browser checks are in `tools/animal_browser_checks.html`.
The parser includes the reviewed conditional Swan branch as well as the static
biome guilds. These are habitat candidates, not spawn probabilities. Unrecognized
logic before the guild match stops the builder for source review. This tooling
support does not add Swan to the dated gallery without actual replacement renders.

## Performance notes

Open **Performance** in the navigation or [performance.html](performance.html).
The 27 September 2026 load analysis records CPU/GPU costs across five habitats,
paired tree-geometry comparisons, and loading/flight traces. It includes the
component chart, repeated streaming-plan finding, optimization priorities,
measurement limitations, and the dated validation record. These are measurements
of separately preserved game builds, not the atlas photograph snapshot or an
FPS guarantee. The original recommendations retain their dated context.

The separate [28 September follow-up](PERFORMANCE_OPTIMIZATION.md) records the
implemented surface-bound cache: settled main-thread CPU fell from 18.3 to
8.7 ms/frame in pine and 33.1 to 8.2 in rainforest, with essentially unchanged
GPU time. Source-isolated before/after profiles and current validation limits
are under `data/performance/optimization/`; native evidence remains in the
sibling game's `.cache/performance-opt/` directory.

[PERFORMANCE_ANALYSIS.md](PERFORMANCE_ANALYSIS.md) preserves the full written
report. `data/performance/` contains raw profiles, summaries, a CSV, CPU attribution,
reproduction notes and binary/source hashes; `images/performance/` contains the
chart. The page is static and works offline without JavaScript or a server.
Full native captures, replay fixtures and executable snapshots remain under the
sibling game's `.cache/load-analysis/` evidence directory.

## What the percentages mean

- Generator: **Current / version 9**, using the local game snapshot recorded in `data/provenance.json`.
- Seeds: `812, 7, 91, 614, 913, 4242, 9001, 12039, 14, 2, 33`.
- Per seed: a square from **−55,296 to +55,296 metres**, inclusive, on X and Z, sampled every **144 metres** (769 × 769 columns).
- Total: **6,504,971 equally weighted columns**. Percentage = biome hits / total samples × 100.
- All terrain counts, including oceans. These are **sampled area shares**, not the number of biome patches, the chance of spawning there, or exact probabilities across an infinite world.
- Seeds are a fixed biome-audit reference set, not a random statistical sample. A regular grid may undercount narrow habitats. Rare biomes retain additional decimal places. Display rounding can make percentages add up slightly differently from 100%; the underlying data sums to 100%.

Viewpoint coordinates use the player’s feet position, matching the debug adapter’s `configure.position` input; the first-person eye is 1.62 metres higher. Screenshot viewpoints are selected separately to show natural habitats; they do not alter the frequency measurements. Screenshots can contain neighbouring biomes. Underwater views are used where appropriate. Biome captures use the production game renderer, clear daylight, creative flight, no content packs, and a hidden HUD. The renderer's normal distance fog and level of detail remain visible. They are photographs of the implementation, not painted concept images.

The current biome atlas documents **generation 9**. Biome photographs use the
production renderer at native 960 × 540 resolution, clear daylight, the Fast
shader and WebP quality 94. The survey and photographs use a frozen build whose
complete source and binary hashes are recorded; an old photograph is never
relabeled as a newer generation. The frozen build combines the previously complete
application snapshot with generation-9 terrain changes; unfinished concurrent
animal, shader and profiling edits are excluded. The shared game checkout is
untouched by this isolation. Every curated location is checked for biome
identity, surface height and water level before capture.

The generator keeps biome identities while softening their margins: coherent
material patches interleave at boundaries, local temperature controls snow
cover, and geological deposits taper into surrounding ground. High mountain
summits have broader uneven crowns while steep flanks remain. Rock clusters
have low irregular masses and broken ledges. Generation 8's larger individual
island shapes, climate relationships, forest groves and open clearings remain.
Generation 9 places these islands in unequal regions with staggered bands and
size-aware offsets, breaking up the old regular rows and repeated gaps.
Sparse, low limestone boulders add detail to dry atoll shores without filling
their channels. The Atlas's 28 September refresh highlights these changes
and links to the island maps, 4K panoramas and four terrain/climate layers.
Older saved worlds retain their generation, so use a generation-9 world to
visit this atlas's locations.

The animal gallery records its independently verified 28 September 2026
snapshot of the original cuboid models and pixel coats. Its 372 portraits use
production meshes and exported textures, with lighting proportional to model
bounds. They are static model previews, individually framed rather than shown
at a shared scale. Animal source provenance is separate from terrain photography.

## Islands and debug layers

Open **Islands** or `islands.html`. Rounded, Long, Crescent, Twin-lobed, Rugged
and Atoll describe existing island shape families; they are not additional
biomes. Search by shape or seed, sort by name or planned size, then open a card.
Each example has a 2048 × 2048 north-up map, a 3840 × 2160 panorama and temperature,
moisture, elevation and ruggedness maps. Full-size images are downloadable.

Panoramas render actual terrain heights, materials and water in Blender at
true vertical scale. These offline whole-island overviews cover up to 16 km,
beyond the game's live horizon. They omit trees, caves, small structures and
half-metre detail; the biome photographs remain actual game captures. Source
grids have 1025 × 1025 samples including both endpoints. Enlarging a map does
not increase its sampling precision; every view reports its original spacing.

Temperature and moisture are normalized generator fields, not degrees Celsius
or relative humidity. Ruggedness describes generated terrain character, not
measured slope. Elevation is ground top-face height in metres, including the
sea floor. Each debug tab has a legend and the exact field meaning. Coastal
outlines and water surfaces can differ from a climate contour because physical
relief and hydrology also determine the coastline.

Coordinates identify each island's centre, which may lie in water. Planned
axes are not measured coastline diameters. Sampled dry area includes all dry
terrain within the displayed bounds, weighted at grid endpoints.

Gallery cards load responsive 480/960-pixel previews; opening a view requests
its existing full-size image. Regenerate after refreshing island sources with
`python3 tools/build_island_thumbnails.py`, then `python3 tools/build_wiki.py`.
`python3 tools/build_island_thumbnails.py --check` verifies source and derivative
hashes, dimensions and the browser lookup. The gate and publication allowlist
include the derivatives. Filter/encoder choices are recorded in
`data/island-thumbnails.json`; originals keep their existing capture receipts.

To export and rebuild island views (NumPy, Pillow and Blender required):

```sh
python3 tools/export_island_grids.py --game .cache/generation9-refresh/source --target-dir .cache/generation9-refresh/sampling-target --date 2026-09-27
python3 tools/map_islands.py --input .cache/island-atlas/grids --output .cache/island-atlas/renders
blender --background --python-exit-code 1 --python tools/render_islands.py -- --input .cache/island-atlas/grids --output .cache/island-atlas/renders
python3 tools/build_islands.py --geometry .cache/island-atlas/geometry.json --grids .cache/island-atlas/grids --renders .cache/island-atlas/renders --source-manifest .cache/generation9-refresh/source-manifest.json
python3 tools/validate_islands.py --game .cache/generation9-refresh/source
```

`tools/survey/src/bin/island_grid.rs` exports production surface samples. The
game's devtools-only ignored `export_island_atlas_climate` test exports private
physical fields without adding a runtime API. Metadata and image hashes are in
`data/islands.json`; raw grids, PNGs and the exact build are kept in `.cache/`.

## Files

- `index.html`, `wiki.css`, `wiki-search.js`, `data/search.js`: player wiki home and offline search.
- `atlas.html`, `style.css`, `app.js`: preserved biome gallery.
- `islands.html`, `islands.css`, `islands.js`: island maps, panoramas and debug layers.
- `images/islands/`, `data/islands.json`, `data/islands.js`: 36 island views and their measured catalog.
- `images/*.webp`: 92 genuine 960 × 540 biome screenshots, encoded as WebP.
- `data/biomes.json`: complete ranked, downloadable catalog.
- `data/biomes.js`: identical data packaged for offline loading.
- `data/survey.json`: unrounded survey counts and original candidate sites.
- `data/descriptions.json`: concise field notes for the implemented terrain and vegetation.
- `data/habitats.json`: all 92 shrub, stone/reef and ground-companion profiles from the current game habitat documentation.
- `data/captures.json`: camera and provenance records for every screenshot. An optional `data/viewpoints.json` may hold refined photography locations for a specific generator snapshot.
- `features.html`, `features.css`, `features.js`, `data/features.json`: the generated feature and guide-coverage ledger and its source data.
- `tools/`: reproducible survey, screenshot, data-building, and verification scripts; `tools/stage_site.py` selects the published file set.
- `.cache/` (ignored): raw PNGs, game replay evidence, binaries, and browser QA output.

## Refresh from the sibling game checkout

The survey wrapper copies its Rust source into an evidence Cargo project and points its core dependency at the frozen `--game` checkout. It uses Rust 1.75 or newer and has no dependencies beyond the game core. The capture tools use Python 3.9+, Pillow, and the sibling game's existing debug adapter.

```sh
# Build an isolated source snapshot: cargo build --release --features devtools
# Freeze its executable and matching recursive source hashes in source-manifest.json.
python3 tools/refresh_survey.py --game .cache/generation9-refresh/source --source-manifest .cache/generation9-refresh/source-manifest.json
python3 tools/capture_biomes.py --game .cache/generation9-refresh/source --binary .cache/generation9-refresh/voxelgame --source-manifest .cache/generation9-refresh/source-manifest.json --overwrite
python3 tools/update_provenance.py --source-manifest .cache/generation9-refresh/source-manifest.json
python3 tools/build_data.py
python3 tools/validate.py --game .cache/generation9-refresh/source
```

Refresh the source/binary hashes in `data/provenance.json` when changing the game snapshot. Captures record individual binary and generator hashes; list the capture binaries in provenance when a refresh spans compatible builds. If a source-only optimization preserves terrain rules, retain its exact original generator/module hashes in `capture_generator_snapshots` and document the compatibility evidence; never relabel an old photograph with a newer source hash. The validator rejects captures from a different generator or obsolete survey locations, cameras and look angles. If its biome catalog changes, also refresh descriptions and category membership. Saved viewpoint overrides are specific to this snapshot; review or remove them before regenerating a different world generator. A viewpoint may set `warmupFrames` in multiples of 120; snowy peaks, the tepui, caldera and granite domes use 1,440 frames so their terrain finishes streaming. `--batches` explicitly overrides this for a capture run. Screenshot capture is resumable: without `--overwrite`, entries are skipped only when their image, source snapshot, viewpoint and warm-up still match. Normal game saves are never loaded or written. Raw captures and a replay per biome are kept under `.cache/captures/`.

To recheck curated locations, `check_sites INPUT.csv OUTPUT.json` accepts rows of
`id,seed,x,z,camera_x,camera_z` and checks biome identity plus terrain/water heights.
After a generator update, adjust camera clearance and inspect the new photographs.

For photography scouting, `tools/survey/src/bin/photo_grid.rs` exports local height, water and biome maps without changing the frequency survey.

For browser checks, serve the folder and open `tools/browser_checks.html`. It checks search, synonyms, sorting, filters, dialog navigation, screenshot loading, and layout overflow at desktop/tablet/mobile widths. The data validator checks all 92 images and the count/percentage/provenance relationships.

## License and provenance

GPL-3.0-only; see `LICENSE` and `NOTICE.md`. The site has no third-party runtime assets. Biome descriptions and game screenshots derive from the original Voxelgame project. Nothing is uploaded or published by these tools.

## World scale — 8 October 2026

Open **Scale** in the navigation or [scale.html](scale.html). The textured,
side-by-side comparison includes Voxelgame, Minecraft Java, the Sun and all eight
planets. Choose visible objects or a preset, switch between actual diameters/map
widths and total surface/map areas, and drag, wheel/pinch, or use the keyboard.
Focus controls make tiny bodies inspectable without silently exaggerating size.
Expand uses full screen where supported. Arrow keys pan the focused diagram;
plus/minus zoom; Escape fits all. The URL retains object selection and mode.

The Voxelgame figure is the theoretical save/network envelope from revision
78b45ed, inspected 2026-10-08, not a verified playable range or fully stored map.
Minecraft uses the maximum Java border of ±29,999,984 one-metre blocks. NASA
mean radii determine approximate spherical areas; giant planets use atmospheric
reference surfaces and rings are excluded.

All eleven textures are original naturalistic procedural illustrations, with no
third-party source imagery or texture attribution requirements. All eleven images use 2048-pixel
materials with solar granulation, grouped sunspots, foreshortened craters,
cloud shadows, polar ice, atmospheric haze, mountain ridges and river-like channels. Geography
is invented, including Earth’s continents. Voxelgame has cool islands and
turquoise shallows; Minecraft has warmer, chunkier continental terrain. These
are illustrative maps, not observations, world captures or proprietary game art. The page works offline via file://
without runtime dependencies, external image requests or a bundler.

Rebuild illustrations with NumPy and Pillow:
`python3 tools/build_scale_textures.py`. No source images or downloads are needed;
`images/scale/manifest.json` records the output hashes.
Open `tools/scale_browser_checks.html` through the local server to verify
geometry, mode/selection controls, focus, textures and responsive layout.

## Maintain the changelog

`changelog.html` and `changelog-wiki.html` separate game changes from website
changes. `data/changelog.json` is the curated source. Dates use the committer's
recorded timezone; they are not release dates. The game source cutoff and the
wiki source cutoff are independent. Neither is the page's deployment revision.

For an update, read the commits after the recorded `sources[].last.commit` in
each repository. Check relevant patches and current source, especially save,
network and blueprint formats. Group actual player-facing base-game changes by
date, with full commit hashes and their committer dates in `refs`. Omit plans,
internal-only changes and optional content. Retain old groups and stable IDs.
If a feature was corrected later, describe both changes on their actual dates.
Do not turn source review into a claim of a fresh gameplay test.

Advance the reviewed cutoff and `commitCount` only through the history actually
reviewed. `git rev-list --count COMMIT` counts that pinned history. Check tags
and hosted releases separately; an inaccessible endpoint is not evidence of
no releases. Public wiki commit links are available; game identifiers remain
plain text while that repository is unavailable to public requests. Recheck
that condition before changing `publicCommitLinks`.

```sh
python3 tools/build_changelog.py
python3 tools/build_features.py
python3 tools/build_guides.py
python3 tools/build_blocks.py
python3 tools/build_mobs.py
python3 tools/build_wiki.py
python3 tools/validate_changelog.py --game /path/to/Voxelgame --wiki .
bash tools/verify_wiki.sh
```

The optional repository checks read Git objects only. They reject an incorrect
history count, missing root, unreachable source hash or mismatched commit date.
The ordinary gate also rejects stale HTML, missing receipts, backdated groups,
invalid ranges and missing earliest/latest coverage. Update the coverage note
in `data/features.json` without moving the full feature audit's older source pin.
Review desktop/mobile, keyboard source disclosures, date anchors, page switching,
search and `file://` with `tools/changelog_browser_checks.html` and the browser
runner. Both histories are complete static HTML; no image or dataset request is
needed to read them. Measure each page with `tools/measure_loading.py`, then
verify the normal Pages run and live bytes/MIME before reporting delivery.

## Rebuild the wiki interface

`data/topics.json` assigns each written guide to exactly one topic, supplies
quick section links and connects related topics. To add an article, register it
there as well as in `data/guides.json`; the gate rejects orphaned or multiply
assigned guides and broken anchors. Topic indexes use `topic-<id>.html`.

After changing guide, recipe or ledger data, run `python3 tools/build_features.py`,
`python3 tools/build_guides.py`, `python3 tools/build_blocks.py`,
`python3 tools/build_mobs.py` and `python3 tools/build_wiki.py`. The gate rejects
stale pages/search data and differing shared category navigation. Add public
files explicitly to `tools/stage_site.py`. Browser checks for the home and shared
navigation are in `tools/wiki_browser_checks.html`; the browser runner supports
`--offline index.html --keyboard index.html --mobile-menu index.html`.
`wiki-ui.js` enhances the native mobile menu; the full menu remains usable
without JavaScript. The home search link also works from a local file URL.
The home meadow photo retains its 28 September 2026 generation-9 receipt.

For image-loading measurements, use `python3 tools/measure_loading.py --root .
--page islands.html --out .cache/island-loading.json` (on one command line).
It starts a fresh Firefox profile for each page and viewport, records the
initial page and first visible gallery row, then repeats mobile with a local
200,000 B/s / 150 ms network model. Compare the same page in a preserved source
tree with `--root /path/to/snapshot`. Add `--base https://lenniaconrad.github.io/qiqi-wiki`
for live Pages measurements without synthetic throttling. Raw request records
stay in the chosen private output file; timing observations include a settling
interval and are not LCP or real-phone measurements.

The mobile runner loads the site's existing `wiki.css` as a text document, then
replaces that document with a same-origin 390 × 844 iframe. This exposes the
child's HTML response size. The setup fetch and other parent requests are recorded
separately in `harness`; they are not page resources. The origin connection is
warm even though the profile is fresh and HTTP caching is disabled. Settled time
includes this setup. The previous opaque `data:` parent caused Firefox to report
zero for the HTML response. Check `unmeasuredBodies` before
using a byte total; if any response size is unavailable, the runner writes null for
`encodedBytes` and `transferBytes`; `reportedEncodedBytes` and
`reportedTransferBytes` are only the sizes it exposed, not complete page costs.
Older receipts predate this guard. Their mobile byte sums omit HTML where the
navigation entry reports zero, so do not reuse them as complete transfer totals.

Run `python3 tools/check_loading_browser.py --out /path/to/private/receipt.json`
to check both viewport paths against known gzip HTML/CSS and an image. It compares
the browser's measured sizes with the responses actually served, including the
compressed document and any repeated requests. It rejects omissions or counts
that disagree with the server's response log. This browser
check is separate from the static gate. Both measurement commands accept
`--startup-timeout 240` for slow shared disks; set `TMPDIR` to owned scratch.
`measure_loading.py --mode mobile` restricts a repeat to one profile.
The same timeout bounds mobile document readiness. A still-loading or initial
blank document fails the run instead of becoming a zero-resource sample.
Use `--require-complete` for comparison runs: an unavailable body size is recorded
as unknown and then stops the run, before spending time on further profiles.

Totals describe the document and resource entries at the recorded checkpoint,
not the cost of scrolling through every image. `encodedBytes` counts response
bodies after compression; `transferBytes` is the browser's header-inclusive
estimate, not a packet capture. Browser-internal traffic is outside the page's
Resource Timing timeline. Retain raw rows and compare matching runner versions,
actual viewports, pixel ratios, checkpoints and network profiles.


## Responsive gallery and guide images

Run `python3 tools/build_gallery_previews.py` after refreshing the biome, animal
or guide catalogs, then rebuild the guide, Mobs, Features and wiki pages using
the commands above. `data/gallery-previews.json` pins each original and derivative
hash, dimensions, content-specific filter, quality and encoder version. The gate
rejects stale captures, missing widths, changed derivatives, previews that are
larger than their original, and missing `srcset`
files in the staged site. `image-previews.js` is generated from the same profiles;
its small path rules avoid another copy of the full catalogs in the browser.

Biome/home cards use 480/640-pixel candidates plus the 960-pixel originals.
Animal cards use 192/320-pixel portraits; 72/144-pixel candidates serve the small
Mobs reference. High-density displays may choose larger candidates, up to the
original. Only the first resting portrait has derivatives; other poses load
when selected in the viewer. Guide screenshots use 640/960-pixel candidates
plus their 1280-pixel original, which can also be opened from the image link.
Static images keep responsive selection with JavaScript disabled. Full originals
remain published because gallery controls and screenshot links need them.

These are derivatives of the existing dated captures, not a fresh game/media
audit. Reinspect the filters and displayed detail when replacing those captures.
BOX, Lanczos and nearest were compared on terrain and small animal details;
BOX and Lanczos were also compared on the menu screenshot. Lanczos was chosen
for these collections, with WebP quality 90 for portraits/landscapes and 86 for
screenshots. No game texture or geometry is changed.

`tools/measure_loading.py` now also scrolls to the first animal-reference or
guide image. It counts images as visible only when they intersect both viewport
axes; an image outside a horizontally scrolling table must not stall a run.
The mobile iframe fits entirely inside the parent viewport so browser chrome
cannot leave its bottom images invisible to native lazy loading.
Compare identical runner versions and profiles. Time readings on a busy shared
host need the same caution as the network model described above.
