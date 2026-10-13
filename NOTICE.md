<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Provenance

This local atlas was created on 25 September 2026 from the sibling **Voxelgame** project (`../Voxelgame`). Website code, survey/capture tooling, and derived catalog data are distributed under GPL-3.0-only, consistent with the game's license. A full copy is in `LICENSE`.

- Descriptions and habitat layers: the 92 variants of `Biome` in `crates/voxelgame-core/src/world/generator.rs`, the exhaustive profiles in `generator/habitats.rs`, and `docs/HABITAT_VARIATION.md`. The current biome atlas uses generator 9.
- Names and measured counts: the public `Biome::ALL`, `Biome::name()`, `World::new(seed)`, and `TerrainSampler::surface_column` APIs.
- Biome photographs: the original game's production renderer, using the built-in assets with no packs enabled. No external image libraries, stock photography, proprietary game assets, or AI-generated substitutes are used.
- WebP conversion: biome frames use quality 94; animal portraits use quality 92. Conversion lossily encodes the complete original frames without cropping, compositing, or changing the depicted terrain. PNGs and replay metadata remain in the local ignored `.cache` directory.
- Island overviews: generated height, water, material and physical-climate samples from the original game. The 4K panoramas are offline Blender terrain renders with no vertical exaggeration; they omit vegetation, caves and small structures. North-up maps and diagnostic layers use NumPy and Pillow. Legend arrows and scale bars are drawn locally; island views use WebP quality 94. They are distinct from production-renderer biome photographs. Grid and image hashes are recorded in `data/islands.json`.
- Animals: descriptions and habitat candidates derive from `entities/mod.rs`. Model portraits use production geometry and texture exports, rendered by the game’s Blender gallery pipeline at 512 × 512. Four static views per species are converted to WebP without cropping. Studio lights scale with model bounds for consistent illumination. Animal source, mesh and image hashes are recorded in `data/animals.json`; the 28 September refresh contains 93 species and 372 portraits. Its PNGs, canonical OBJ exports, exact-input reuse proof and final source manifest remain under `.cache/animal-model-refresh-2026-09-28/`.
- Fonts: the visitor's installed system fonts; no font assets are redistributed.
- Biome source/binary snapshot hashes: `data/provenance.json`. The source was a modified local working tree, so the recorded Git commit alone does not reproduce it. The generation-9 biome capture build is isolated: the previously complete application snapshot plus the terrain, generation-version and debug-horizon changes. Unfinished concurrent entity, shader and profiling edits are excluded; the exact composition is recorded in the frozen source manifest, without reverting the shared game checkout.

The fixed-seed measurements describe this snapshot. They are not guaranteed frequencies for all seeds or future game versions.

## Responsive island previews — 13 October 2026

The island gallery uses 480- and 960-pixel WebP derivatives of its existing
maps and panoramas. Full-size images and their original provenance are unchanged
and load when a view is opened. `data/island-thumbnails.json` records each source
hash, derivative hash, dimensions, filter and encoder settings. BOX and Lanczos
were compared at 480 pixels; Lanczos was selected for the small terrain boundaries
in this collection, with WebP quality 88. This is not a resampling rule for other
images. The original GPL-3.0-only terms apply; no new artwork was introduced.

## Performance analysis

`performance.html`, `PERFORMANCE_ANALYSIS.md`, `data/performance/` and
`images/performance/component-costs.png` document original local Voxelgame
measurements from 27 September 2026. The chart was plotted from those values;
no third-party imagery, fonts or assets were added. Snapshot hashes and
measurement limitations accompany the report. Project GPL-3.0-only terms apply.

## World scale comparison — 8 October 2026

Scale measurements use NASA's Sun and planetary fact sheets (volumetric mean
radii), the Minecraft Java maximum border convention, and the sibling game's
explicit persistence/network limits. Sources and limitations are visible on
scale.html. Original comparison code and all eleven naturalistic procedural
illustrations are GPL-3.0-only under this project's existing terms. No third-party
texture maps or proprietary Minecraft artwork are included.

## Player guides — 11 October 2026

`guides.html`, `guide-*.html`, `data/guides.json`, `data/recipes.json` and
`images/guides/` are original text and data written for this project. Facts come
from reading the Voxelgame source at the commit shown on each guide; the 37
recipes are extracted from the game's recipe registry and rechecked by
`tools/validate_guides.py --game`. The four screenshots are headless captures
(1280 × 720, lossy WebP quality 80) of the original game's release build running
against a disposable world with no packs enabled, and contain no third-party
assets. Project GPL-3.0-only terms apply.


## Responsive gallery and guide previews — 13 October 2026

The biome, animal and guide collections have smaller WebP derivatives for
cards, small reference rows and mobile screens. `data/gallery-previews.json`
records source and output hashes, dimensions, filter and encoder settings.
Sources are the unchanged original game captures and model renders described
above; their capture dates and licences still apply. After displayed-size
comparisons, these collections use Lanczos with WebP quality 90 (landscapes
and portraits) or 86 (guide screenshots). This does not establish a filter
preset for future images. Original views remain available on demand.
