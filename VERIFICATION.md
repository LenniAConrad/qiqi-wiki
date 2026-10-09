<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Verification — 28 September 2026

These entries record separate snapshots and check runs. Earlier entries keep
their original dates, sources and limitations; the generation-9 entry below
describes the current biome and island refresh.

## Streaming optimization final audit — 28 September 2026

- The full shared-game rerun passes 1,189 workspace tests with zero failures
  (18 intentionally ignored), plus 81 devtools tests (one ignored) and all 15
  Python adapter tests. Formatting, Clippy with warnings denied, public Rustdoc
  and private core Rustdoc pass. Recorded source hashes stayed unchanged during
  every completed check; an interrupted preliminary attempt is kept separate.
- The remaining atlas assertion now passes in the full suite after its owner's
  correction for intentional bounded texture grain. The residency probe and all
  seven surface-band regressions also pass. Concurrent animal work was preserved.
- Eight native replays pass 780 commands / 118 assertions, covering 36 terrain
  setting combinations, water, craters, structures, render-origin crossings and
  the real-terrain study timer. All 126 frame captures were visually reviewed.
  A final shared-source rebuild passes another 64 movement/toggle commands and
  eleven reviewed toggle captures. Native logs are empty and saves are disabled.
- A fully settled village check waits for two stable, idle windows and reaches
  3,092 resident / 958 visible detailed chunks, 71 far tiles and the full 128 m
  detail radius. Its final capture was inspected. Cold starts and newly enabled
  horizons still stream asynchronously; distant terrain off exposes a finite
  resident terrain boundary.
- Updated `PERFORMANCE_OPTIMIZATION.md` and preserved the final counts, logs,
  source/binary fingerprints and review summaries under
  `data/performance/optimization/verification-20260928/`. Published evidence
  hashes match the game originals. This updates the verification record;
  existing performance measurements and page layout remain unchanged.

## Homepage and metadata refresh — 28 September 2026

- Updated the homepage to describe unequal island spacing, low atoll boulders,
  and the available island maps, 4K panoramas and four debug layers. The source
  snapshot date and completed photograph refresh date are now distinct.
- Removed the outdated island-ownership multiplier from survey provenance and
  rebuilt the JSON/JavaScript catalog mirrors. Source-aware validation passes
  all 92 photographs, measured counts and frozen-build hashes; no new terrain
  survey or photograph capture was required.
- Marked the performance priorities as the original 27 September list and
  linked its completed cache recommendation to the implemented follow-up.
  Existing measurements and remaining recommendations are preserved.
- All 109 reused browser checks pass: 31 biome checks over HTTP, 31 offline,
  and 47 performance checks. The performance page's 30 local links and anchors
  are valid. The update section fits at 1280, 375 and 320 pixels without
  horizontal overflow; desktop and mobile captures were visually inspected.
  Evidence is in `.cache/site-refresh-20260928/` and
  `.cache/performance-priorities-refresh/`. Python compilation, generated
  JavaScript syntax and `git diff --check` pass. This is a site content update;
  the game validation below retains its original scope and source snapshot.

## Streaming optimization follow-up — 28 September 2026

- Added a separately dated implementation/results section to `performance.html`
  and `PERFORMANCE_OPTIMIZATION.md`. The original 27 September load analysis
  retains its own snapshots, measurements and recommendations.
- Preserved isolated before/after source manifests, binary hashes, all four
  fully settled profile records, the summary and focused validation logs in
  `data/performance/optimization/`. Each A/B source pair differs only in the
  surface-bound cache. Main-thread CPU measured 18.3 → 8.7 ms/frame in pine
  and 33.1 → 8.2 in rainforest; GPU pass time remained essentially unchanged.
  These are observed CPU reductions, not promised FPS gains.
- All 46 focused headless browser checks pass, including the new result table,
  explicit measurement limits, report/data links, original report content,
  local downloads and responsive overflow checks at 1280, 768, 375 and 320 px.
  Desktop HTTP and mobile offline captures were inspected. Evidence is in
  `.cache/performance-opt/`.
- Game formatting, Clippy with denied warnings, public/private Rustdoc, cache
  regressions, the corrected residency probe and 81 devtools tests pass. Native
  forest and distant-terrain toggle/movement replays pass; input saves are
  unchanged. The full workspace initially had five failures; the fixed residency
  test and three concurrent animal fixes pass fresh focused rechecks. One atlas
  row-brightness assertion remained in that concurrent snapshot, recorded in the
  full report. That initial snapshot was not represented as clean; the complete
  final audit above supersedes its validation status.

## Load analysis page — 28 September 2026

- Added `performance.html`, linked from the biome, animal, island and village
  navigation, with the dated CPU/GPU findings, tree comparisons, chart, movement
  breakdown, optimization priorities and measurement limits.
- Preserved `PERFORMANCE_ANALYSIS.md` and portable raw/aggregate measurements
  under `data/performance/`, including source/binary hashes. This analysis has
  separate provenance from the atlas photographs and is not an FPS guarantee.
- All 40 headless browser checks passed: section/table contents, loaded chart,
  local links/downloads, navigation, and document overflow with collapsed/open
  details at 1280, 768, 375 and 320 pixels. JSON parsing, local anchors and copied
  evidence hashes also passed; `git diff --check` was clean.
- Inspected desktop HTTP and mobile offline (`file://`) captures. Corrected
  sentence spacing when the shared mobile style hides introductory line breaks.
  Browser evidence is in `.cache/performance-page/`. No visible window was opened.
- Original game test results, including the five workspace failures from that
  earlier snapshot, remain in `data/performance/VALIDATION.md`; no new game
  benchmark or game-code change is claimed for publishing these notes.


## Generation 9 terrain and island atlas — 27 September snapshot

- The final frozen source passed formatting, all 1,121 workspace tests
  (18 ignored), Clippy with warnings denied, documentation, 80 devtools tests
  and all 14 debug-adapter Python tests. Exact results and logs are in
  `../Voxelgame/.cache/ecotone-9/validation/`.
- The 11-seed survey again samples 6,504,971 columns and finds all 92 biomes.
  All curated sites passed biome, height, water and camera checks. The final
  survey is byte-identical to the preceding production-equivalent build;
  only an atoll regression assertion changed between those builds.
- Final photographs use the frozen executable with SHA-256
  `a88cd01417b01e5ce3821894564fcd0a071ebc4ce467b79b4def199ba0bea1cb`.
  Its source manifest SHA-256 is
  `3937294b9c1278b922cf37100fb0fcdf33d072c91e077400fc2949a1f9410dbd`.
  The complete source, binary, survey, camera checks and original captures are
  retained under `.cache/generation9-refresh/`. This complete application
  snapshot excludes unfinished concurrent animal, shader, village and
  profiling work in the shared game checkout; those changes keep separate
  provenance.
- The shared checkout was also checked while unrelated animal work was
  changing. Its four earlier animal/model and pixel-contrast failures now
  pass focused reruns after their owners' updates; relevant source hashes
  stayed unchanged during those reruns. This is separate from the complete
  clean frozen workspace run above, and does not claim a repeat of the full
  changing shared workspace. Commands and source hashes are in
  `../Voxelgame/.cache/generation9-shared-checks/animal-recheck/` and
  `animal-recheck-final/`.
- Island placement now uses unequal regions and independent offsets. A
  three-seed native replay also checks low atoll boulders from two angles:
  76 commands passed, with zero edits, disabled saves and an empty native log.
  This replay used the production-identical build before the test-only
  assertion correction, whose exact binary hash remains in its evidence.
- The final release sampling benchmark is 11–17% faster for map columns and
  12–13% faster for equally sized dry-land workloads across three seeds.
  These are CPU terrain-query measurements, not game-frame-rate claims.
- All six 1025² terrain/climate exports match the frozen generator sources,
  have valid finite field values and keep an ocean margin around their frames.
  All six 4K panoramas, six top-down maps and 24 debug layers have been
  rendered and visually reviewed. Source-aware island validation passes all
  36 images. All 91 island browser checks pass over HTTP and directly from
  `file://`, including keyboard navigation, image loading and responsive
  layouts. Desktop, mobile, map, panorama and climate dialogs were visually
  inspected; evidence is in `.cache/island-ui-final/`. Island Python tools
  compile, JavaScript syntax checks pass, and the Rust sampling tools pass
  formatting and Clippy with warnings denied.
- Replaced and visually reviewed all 92 biome photographs at native
  960 × 540 resolution, Fast shading and WebP quality 94. Six camera retakes
  expose the cloud-forest tree belt, adjoining delta water, coastal rock and
  water context, and the caldera basin/rim. Original biome anchors and camera
  locations remain distinct, with neighbouring-biome context recorded.
  Sparse atoll stones are clearly visible beside palms and shore plants.
- Rebuilt both catalog formats and provenance, then passed source-aware biome
  validation and all 92 site/camera checks. The accepted photo set contains
  954 successful recorded commands, 59,280 warm-up frames and 954 checked
  states, with zero edits, disabled saves and empty native logs. Exact replay,
  PNG, WebP and binary hashes are in
  `.cache/generation9-refresh/capture-evidence-audit.json`; the final review
  sheets are in `contact-sheets/final92/` beside that audit. Superseded and
  interrupted attempts remain separate from the accepted set.
- Native adapter Git metadata identifies the hosting qiqi checkout because
  the frozen source is nested inside it. It is retained unchanged as raw
  evidence; the authoritative game source identity is the explicit frozen
  manifest, complete file hashes and executable hash above.
- Final headless browser verification passes all 31 biome checks and all
  91 island checks over both HTTP and offline file loading. Another 57 checks
  pass in each mode for navigation and header widths across Biomes, Islands,
  Animals, Village and Performance at 320–1280 pixels: 358 passing checks in
  total. Desktop, mobile and two biome dialogs were visually reviewed; both
  application scripts pass syntax checks. All 17 snapshotted UI/catalog/
  provenance files stayed unchanged during this QA. Evidence and hashes are
  in `.cache/biome-ui-final-20260928/`.


## Jade Willow Village gallery

- Added eleven fresh native 960 × 540 screenshots: nine inspection views and
  two generated-world views, including a resident. Reviewed houses, furnished
  interiors, lanes, the pond bridge, the village outline and evening lighting.
  Inspection and generated scenes retain explicit labels throughout the UI.
- Captured Jade Willow Village 1.4.0 with generator 9, seed
  `1786640127379949800`, using the reviewed frozen devtools executable. Its
  SHA-256 is `6fca0d203a6436828e98c78af80f11a27d3f40f9e8708a8da6bc7de28e77441d`.
  These photographs have their own provenance; later concurrent source edits
  are not attributed to the executable. Original PNGs, replays and the binary
  remain in `.cache/village-captures-20260927T150158Z/`.
- All 87 native commands succeeded. All 83 returned states with a save flag
  confirm disabled saves, both native logs are empty, and every capture has
  zero voxel edits. Detailed geometry finished loading before photography.
  No visible game window was opened. WebP conversion preserves complete frames.
- The village validator passes all eleven WebPs, original PNG hashes, exact
  binary hash, dimensions, camera metadata and the offline JavaScript mirror.
  All 255 village browser checks pass, including filters, every photograph,
  dialog navigation, deep links and layout widths from 320 to 1280 pixels.
  Header overflow checks cover all four site pages.
- Trusted keyboard input verifies Enter, arrow navigation, native modal focus
  and inert background controls, and Escape with focus restored to its opener.
  Direct `file://` loading also passes for the data script and all eleven images.
- Visually reviewed the final 1280-pixel desktop page and gallery, 375-pixel
  mobile page, and 320-pixel dialog. Browser evidence is in
  `.cache/village-review/` and `.cache/village-browser-qa/`. Python compilation,
  JavaScript syntax and scoped whitespace checks pass.
- A separate existing biome-browser run stops at
  `tools/browser_checks.html:29`: `data/biomes.json` currently declares
  generation 4 while the page and check say generation 9. The concurrent
  biome refresh files were preserved; this gallery addition does not claim
  that unrelated check passes.

## Current animal refresh: 28 September 2026

- Updated the local gallery to 93 animals and 372 unique 512 × 512 portraits,
  including Bat, River Otter and Penguin. All four views of every species were
  personally inspected in 16 contact sheets. Final Tiger tail bands and the
  calmer small-part coat mapping were reviewed separately.
- The source-aware validator passes all 93 entries, dimensions, image hashes,
  four-view coverage and links to the 92 biome rules. The habitat parser now
  accepts rustfmt's brace-wrapped Penguin rule. Catalog counts follow the game
  rather than a fixed 90-species assumption.
- Headless Chromium passes 62 browser assertions with zero console or runtime
  errors. These include all three new cards, their four detail views and
  habitat links, every portrait load, filtering, keyboard navigation and
  layouts at 320, 375, 768 and 1280 pixels. Desktop and mobile screenshots were
  inspected; a missing mobile intro space was corrected and checks repeated.
- Production exports are frozen in the game's
  `.cache/all-mob-review-final/frozen/animal-motion-meshes/`. All four final
  Tiger meshes match the production exporter byte for byte. Sixty-four
  portraits were reused only after exact image, mesh, used-material, texture
  and renderer-script hash comparisons; the remaining 308 were freshly
  rendered. No generated reference-board bitmap is used as a game or site asset.
- Game-wide checks and native replay evidence are maintained separately under
  `../Voxelgame/.cache/all-mob-review-final/`. This site refresh does not claim
  that every concurrently edited terrain or renderer path was retested here.
  Unrelated biome, island, village and performance changes were preserved.
  Nothing was committed, pushed or deployed, and no visible game window opened.

Evidence: `.cache/animal-model-refresh-2026-09-28/final-manifest.json`,
`validate.log`, `browser-results.json`, `portrait-review.json`, all 16 contact
sheets, six page captures and canonical export/source hashes.

## Previous animal refresh: 27 September 2026 — original cuboid models and pixel coats

- Regenerated all 360 portraits for 90 animals from the final production meshes
  and material exports. All four 512 × 512 views of every animal were visually
  reviewed in 15 contact sheets; no clipping, missing materials or framing
  defects were found. Portraits remain static studio previews.
- The game changes simplify bodies and limbs, improve eye/ear/muzzle placement,
  and align restrained walking and hopping cycles with planted feet. Seven
  original four-tone coat tiles and two anatomical tiles were revised; the
  other 128 runtime coat/part tiles remain unchanged. The source game separately
  exports 49 eight-phase gait reviews, with representative cycles visually
  accepted and 55 focused model/animation tests passing.
- Rebuilt both catalog formats, dimensions, image/mesh hashes and habitat links.
  The builder now accepts a snapshot date and records atlas/shader provenance.
  The validator requires those material sources and a valid ISO snapshot date.
- Source-aware animal validation passes for all 90 animals and 360 unique images.
  All 37 animal and 31 biome browser checks pass in headless Chromium, including
  offline image loading, filters, navigation and layouts from 320 to 1280 pixels.
  Python compilation and JavaScript syntax checks pass.
- The accepted animal snapshot passed 1,048 workspace tests plus formatting,
  Clippy and documentation checks. Fresh follow-up native replays passed all
  168 commands with empty logs. The later concurrently edited game checkout is
  not globally green: its partial workspace run has seven unrelated terrain
  failures and active generator formatting differences. Current Clippy, docs,
  devtools, Python and exporter checks pass. Exact logs and source fingerprints
  are in `../Voxelgame/.cache/animal-review-latest/`; this refresh does not claim
  to validate those concurrent terrain changes.
- The generation-4 biome photographs and survey keep their own source snapshot.
  No biome data or photograph was changed. A scoped backup and hashes of every
  protected site file are retained before replacement. Nothing was committed,
  pushed or uploaded, and no visible game window or player save was used.

Evidence: `.cache/animal-model-refresh-2026-09-27/`, including raw exports/renders,
15 visual review sheets, staged browser reports and rollback backup. Production
animal evidence: `../Voxelgame/.cache/animal-review-verified/`.


## Previous refresh: generation 4

- Re-ran the 11-seed, 6,504,971-column survey. Coverage counts changed in 82
  biome entries; totals remain exact and all 92 biomes have nonzero samples.
- Checked all 92 curated photograph locations against generation 4 for biome
  identity, terrain height and water level. Updated camera clearance and
  reframed the forest and snowy-peak photographs.
- Added all 92 habitat profiles to the biome dialogs and search. “Metystone”
  now finds Amethyst gorge. Version labels and travel instructions use
  generation 4. The Updates section distinguishes implemented work from the
  remaining mountain, silhouette, placement and thermal-pool priorities.
- Capture settings: native 960 × 540, standard shader, default draw distance
  64, clear daylight, hidden HUD, zero world edits and disabled save writes.
  Every capture retains its exact source and binary hashes. The pinned build
  prevents concurrent game edits from changing the photograph set midway.
- The subsequent live generator diff changes only sparse grid sampling to
  call the same point-query rules instead of filling unused intermediate
  samples. Its source hash is recorded separately from the capture snapshot;
  no old photograph has been relabeled with the newer hash.
- All 92 final images were visually reviewed at native resolution or in contact
  sheets. The final source-aware biome and animal validators pass. All 31 biome
  and 37 animal browser checks pass, including offline loading, image loading,
  search, navigation and widths from 320 to 1280 pixels.
- The 92 final capture bundles contain 944 successful commands, 944 states
  confirming generator 4, zero edits and disabled saves, and 92 empty native
  logs. A resumption check skips every completed image. Screenshot replacement
  is now atomic so future refreshes do not expose partially encoded images.
- Atlas Rust formatting and Clippy with warnings denied, Python compilation,
  JavaScript syntax and diff whitespace checks pass. Animal source validation
  and all 37 animal browser checks pass; the 90 animals and 360 portraits remain
  unchanged. Desktop and mobile biome details were visually inspected.

Evidence: `.cache/worldgen4-refresh/`; exact per-image replay paths are in
`data/captures.json`. The game’s earlier habitat-refinement checks (984 workspace
passes and the associated devtools/Python checks) are recorded in its
`docs/HABITAT_VARIATION.md`; they are separate from these atlas checks.

## Previous fix: forest-floor dot pattern

- The near/far ground blend omitted procedural moss because its material does
  not use the terrain atlas. Generated top surfaces now carry terrain identity;
  both representations converge in lighting and share mapped canopy shadows.
- The game passed **969 workspace tests**, zero failures, seven ignored;
  formatting, Clippy, documentation and final WGSL validation passed. Devtools
  tests and all 12 Python adapter tests also passed. A real moss-versus-placed-
  moss mesh regression covers the missing metadata.
- Matched old-growth before/after replays reproduce and remove the visible
  8 × 8 dot pattern. The sampled patch's periodic residual drops by about 96%,
  while the final image preserves shade. Close and elevated views, grass and
  moss, and Classic/Fast/Cinematic paths were inspected headlessly.
- Recaptured all **18 woodland entries plus mossy highlands** with the final
  build, preserving their chosen viewpoints and quality-94 native frames.
  Remaining images keep their preceding glare-fixed binary records; the
  original frequency survey and animal portraits are unchanged.
- Both source-aware catalog validators pass: 92 biome photographs and 90
  animals with 360 model views. All 27 biome browser checks pass, including
  every image load and layouts at 320–1280 pixels. The 19 new capture bundles
  contain 190 successful native commands, 171 states with save writes disabled,
  and 19 empty game logs. All final forest photographs were visually reviewed.
- Current source provenance includes the terrain mesher as well as shaders.
  The current binary is
  `e72d3b84683b91ca4f4dd2b9bd41861c9566a356e3a49dfb3419cd0eb4167b80`.

Game evidence: `../Voxelgame/.cache/grass-shading/`.
Atlas evidence: `.cache/forest-ground-refresh/`.

## Previous refresh: lighting and photography

- All 92 biome photographs now come from the latest material-glare-fixed
  release devtools binary, SHA-256
  `aa7bd228f56312c7af1bd67884033175a4cede7b65213f7260fae8b0eb9e5b4d`.
  The atlas records exact generator and renderer source hashes. No game source
  changed during this atlas refresh; the game checks below describe the verified
  source build used for these captures.
- Compared standard and cinematic shaders from the same orchard camera;
  retained the standard shader for clearer foliage and terrain. Encoded each
  entire native 960 × 540 frame at WebP quality 94, without resizing or retouching.
- Reviewed all 92 photographs and refined 20 viewpoints. The gorge, tepui and
  granite dome are framed from outside their features; the cold river now shows
  its watercourse. Closer dryland/grassland views expose ground cover. Coastal
  views include shoreline context. Rejected the closer bamboo trial in favour
  of the original overview. Natural fog and neighbouring biomes remain visible.
- Checked all 92 final location labels, heights and water levels against the
  current generator. Retained the separate 6,504,971-point frequency survey.
  Capture resumption skips all 92 final records, including their new encoding
  quality, camera, water-level and source metadata.
- The 92 selected evidence bundles contain **944 successful native commands**,
  944 states confirming save writes are disabled, and 92 empty native logs.
- Rendered all **360 animal views** again from unchanged, current production
  meshes and textures. Lights scale in distance, size and power to each model’s
  bounds; this removes the whale/giraffe spotlight problem and keeps tiny
  animals readable. Compared six size extremes before rendering the full set,
  then visually reviewed every final view in contact sheets.
- Both data validators pass, including exact comparisons with the sibling game
  checkout. All **27 biome and 37 animal browser checks** pass in headless
  Chromium: image loads, navigation, filters and widths from 320 to 1280 pixels.
  Desktop biome details and the animal gallery, plus mobile animal details,
  were also visually inspected.
- Python compilation, JavaScript syntax, atlas Rust formatting, Clippy with
  warnings denied and diff whitespace checks pass. Rendering and browser work
  stayed headless. No player saves were accessed. Changes remain local; this
  atlas checkout has no configured remote.

Evidence: `.cache/photo-refresh/`, including final contact sheets, before/after
comparisons, 360 raw animal PNGs, browser reports and the reference-site audit.
Per-biome raw PNGs and replays are referenced by `data/captures.json`.

## Animal gallery — 90 species

- Added `animals.html` and navigation from the biome atlas. All 90 built-in
  animals have search, five category filters, a biome filter, descriptions,
  model dimensions and links to their candidate habitats. Biome details link
  back to filtered wildlife; habitat links open the matching biome directly.
- Exported the current production meshes/materials with the existing game
  exporter. They match the previously reviewed model-fix exports byte for
  byte. Rendered all 360 views anew in headless Blender at 512 × 512: resting
  and moving poses from three-quarter and side angles. These are explicitly
  labeled studio model previews, not live gameplay/animation recordings.
- Reframed the three smallest animals without the QA camera's fixed upward
  offset so their portraits remain legible. No production geometry was changed.
- Visually reviewed all 90 primary portraits in contact sheets, all four views
  for six animals spanning size extremes, and desktop/mobile gallery layouts.
- The animal validator passes for 90 species, 360 unique images, dimensions,
  habitat links and exact source/image hashes. Its builder covers the spawning rules for all 92 biomes; local terrain/water/population constraints are explained.
- All **37 animal browser checks** and **27 existing biome browser checks**
  pass in headless Chromium with local files. Checks cover all 360 image loads,
  combined filters, view selection, keyboard navigation, both directions of
  habitat linking, empty-state recovery and layouts from 320 to 1280 pixels.
- Existing biome-data validation, JavaScript syntax, Python compilation and
  whitespace checks pass. No game source changed in this addition. No visible
  game window was opened and no player saves were accessed.

Evidence, raw renders and export inputs: `.cache/animal-refresh/`.
Reproduction commands are in `README.md`; asset notices are in `NOTICE.md`.

## Previous update: map coordinate travel and bow recovery

- Updated `.cache/voxelgame` to the latest verified release devtools build,
  SHA-256 `bce69e8314dc85caa44f79f851059c14920d62a32e460f9649fd0898f6144450`.
  This includes creative map coordinate travel and continuous drawing-hand
  entry/release recovery. The sibling game passed 968 workspace tests with
  zero failures and seven ignored, formatting, Clippy and documentation checks.
- Compared the current generator, its modules and the block registry with the
  full atlas refresh: all five source hashes are unchanged. Retained the
  measured frequency survey and compatible photographs with their actual
  original capture-binary records.
- Recaptured redwood forest, orchard and coral shallows using the new build,
  then visually inspected all three. Their native logs are empty; captures ran
  in disposable offscreen sessions with normal save writes disabled.
- Updated provenance and rebuilt both catalog formats. Every biome dialog now
  provides a plain `X Z` map destination and explains creative `Shift+M` travel,
  the matching world seed, and how screenshot viewpoints differ from landings.
- All 92 entries, images, sample totals and provenance relationships pass
  `tools/validate.py`. All 27 browser checks pass in headless Chromium, covering
  search, filtering, sorting, navigation, image loading and responsive layouts.
  JavaScript syntax and diff-whitespace checks pass.

Evidence: `.cache/current-refresh/`, including the browser report and the
visually reviewed three-image contact sheet. No remote is configured for this
local atlas checkout; these changes are local.

## Previous refresh: mixed tree sizes and biome identity

- Refreshed all 92 images from the latest release devtools binary, including the
  habitat, audio, model and tree-size changes. Binary SHA-256:
  `313407ee5ee58e8bdf295e30d487915b1fb52e22e60ab36cdee6252f36f11357`.
- Reviewed all 92 final images in four contact sheets and the revised forest
  and snowy-peak views at full size. Raised cameras for old-growth, temperate
  rainforest and redwood stands to show the taller, mixed-height canopy.
- Updated 45 field descriptions to identify visible tree, ground-cover and
  habitat details. All 92 biomes retain their own catalog entries and explicit
  ground-cover or embedded surface-detail rules. This is a visual review of
  the recorded reference sites, not an exhaustive survey of every seeded stand.
- Checked all 92 reference biome labels, heights and water levels against the
  current generator. The tree/detail changes do not alter climate ownership;
  the original 6,504,971-point frequency survey is retained with its provenance.
- Final capture evidence contains 927 successful native commands, 927 states
  confirming save writes are disabled, and 92 empty native logs. All gameplay
  rendering ran offscreen on the Intel Iris Xe adapter.
- Added persistent per-viewpoint warm-up settings; snowy peaks use 1,440 frames.
  Capture resumption now checks camera, look, location and warm-up as well as
  source and image hashes. It automatically recaptured the four stale views;
  a subsequent full resume correctly skipped all 92 current images.
- Data validation passed. Negative checks confirmed stale cameras, look angles
  and insufficient summit warm-up are rejected. Python compilation and
  JavaScript syntax checks passed.
- All 27 browser checks passed in headless Chromium using local files, including
  the new field-note searches, 92 image loads, sorting, dialog navigation and
  no horizontal overflow at 1280, 768, 375 and 320 pixels.
- The sibling game passed formatting, all 962 workspace tests (seven existing
  manual probes ignored), Clippy with warnings denied, and documentation build.
  Tree regressions include 2,560 generated graphs and tall-crown query/felling
  agreement. Evidence: `../Voxelgame/.cache/tree-sizes/README.md`.

Current refresh evidence and contact sheets are under `.cache/tree-refresh/`.

## Earlier habitat-detail refresh

- Completed the interrupted capture refresh, then refreshed all 92 images again
  for the habitat-detail implementation and four new original blocks.
- Every current image records the exact release binary, main generator source,
  generator-module and block-registry hashes. The validator rejects mixed or
  stale snapshots. All screenshots are unique 960 × 540 WebP files.
- Reviewed all 92 final images in contact sheets and selected habitats at full
  size. The four new blocks were also inspected in cinematic and fast shaders.
- Recaptured the mountain with 1,440 warm-up frames after the first capture
  showed incomplete asynchronous terrain streaming; the full peak was verified.
- Added close viewpoints for heath, lavender, pampas and dunes, and underwater
  views for coral, kelp, seagrass and the ocean floor. DeepKelpForest uses a
  nearby deeper reference site of the same biome. Viewpoints and measured
  reference heights are recorded in `data/viewpoints.json`.
- Rebuilt both catalog formats. Validation checks all 6,504,971 samples, exact
  percentages, ranks, image hashes, cameras and source/binary provenance.
  The existing frequency survey is retained because habitat details do not
  change climate ownership. A current-generator audit confirms all 92 final
  reference biome labels, heights and water levels.
- All captures use disposable headless sessions with save writes disabled.
  Native logs contain no GPU validation errors or warnings.
- Python compilation and JavaScript syntax checks pass. Atlas Rust formatting
  and Clippy passed in the earlier handoff; the survey code is unchanged by
  this habitat-detail pass.
- Browser interaction checks were not rerun for this refresh. The prior browser
  verification below applies to the unchanged gallery UI.

## Previous browser and layout verification — 25 September 2026

- All 92 catalog biomes were found in 6,504,971 samples across 11 fixed seeds.
- All 92 screenshots are unique, valid 960 × 540 WebP files. Image hashes, seeds, positions, camera angles, ranks, counts, and percentages passed `tools/validate.py`.
- Capture transcripts confirm that the actual player position matches the recorded viewpoint. Images were inspected in contact sheets, with selected landscapes checked at full size. Five viewpoints were refined for clearer terrain or habitat framing.
- The native capture logs contained no rendering validation warnings.
- All 24 checks in `tools/browser_checks.html` passed in Chromium: complete catalog, nonzero rare-biome percentages, sorting, search synonyms, combined filters, empty-state recovery, modal navigation, image loading, and overflow checks at 1280, 768, 375, and 320 pixels.
- Desktop and mobile layouts were visually reviewed. All 92 entries also rendered when opening `index.html` directly via `file://`.
- JavaScript syntax checks, Python compilation, Rust formatting, and Clippy with warnings denied passed for the atlas tooling.

Local replay evidence, raw PNGs, contact sheets, browser reports, and screenshots remain under the ignored `.cache/` directory. No normal player saves were loaded or written.

## World scale — 8 October 2026

- Added the native Scale page and links in all five existing atlas pages.
  Verified each existing HTML change is exactly the inserted navigation link;
  all prior local content and edits are preserved.
- The new browser harness passes 32 checks: eleven objects, side-by-side
  non-overlap, exact diameter and squared area ratios, square versus equal-area
  disk geometry, zoom reversibility, Earth focus, visibility and presets,
  table-to-comparison selection, URL state and responsive navigation/layout.
- Chromium checks additionally cover wheel zoom, keyboard pan/reset, drag,
  direct file:// viewing with locally loaded textures, and the five existing
  page navigation bars at 1440, 768 and 320 pixels. No JavaScript errors.
- Inspected desktop, all-object width/area, game-area and mobile screenshots.
  Evidence is in ignored .cache/scale-qa/.
- JavaScript syntax and Python compilation checks pass. No Rust/game files
  changed; no game process, normal save or existing worker was touched.
- Replaced the initial third-party textures with eleven original procedural
  procedural illustrations and removed their source maps and attribution files.
  The refined 2K art includes sparse sunspot groups, foreshortened craters,
  cloud shadows, polar ice, restrained ocean glints, mountain ridges and
  river-like channels. Atmosphere stays inside each body’s measured silhouette.
  All geography is invented; Voxelgame uses cool islands and Minecraft uses
  warmer, chunkier continents. The displayed label is simply Minecraft.
  The offline generator takes no source images; output hashes are recorded in
  images/scale/manifest.json.
- Voxelgame remains explicitly labeled as a theoretical coordinate envelope,
  not a verified playable boundary. Area disks do not represent actual
  planetary diameters; rings and orbital spacing are excluded.
