<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Provenance

This local atlas was created on 25 September 2026 from the sibling **Voxelgame** project (`../Voxelgame`). Website code, survey/capture tooling, and derived catalog data are distributed under GPL-3.0-only, consistent with the game's license. A full copy is in `LICENSE`.

- Descriptions and habitat layers: the 92 variants of `Biome` in `crates/voxelgame-core/src/world/generator.rs`, the exhaustive profiles in `generator/habitats.rs`, and `docs/HABITAT_VARIATION.md`. The current biome atlas uses generator 9.
- Names and measured counts: the public `Biome::ALL`, `Biome::name()`, `World::new(seed)`, and `TerrainSampler::surface_column` APIs.
- Biome photographs: the original game's production renderer, using the built-in assets with no packs enabled. No external image libraries, stock photography, proprietary game assets, or AI-generated substitutes are used.
- Village photographs: eleven native 960 × 540 production offscreen captures with the original Jade Willow Village 1.4.0 pack (`chinese_village:pack`) enabled. Nine inspection views show the authored village and two generated-world views show its Autumn Forest placement and residents at X 36, Z 380, on generator 9 with seed `1786640127379949800` (stored as an exact decimal string). Captures use the Fast shader, clear daylight or evening and a hidden HUD. `data/villages.json` and its offline script mirror record image and frozen-executable hashes, cameras and replay paths. Original PNGs, replays and the exact executable are preserved in ignored `.cache/village-captures-TIMESTAMP/` directories; later concurrent source edits are not attributed to that executable or these images.
- WebP conversion: biome and village frames use quality 94, with method 6 for village frames; animal portraits use quality 92. Conversion lossily encodes the complete original frames without cropping, compositing, or changing the depicted terrain. PNGs and replay metadata remain in the local ignored `.cache` directory.
- Island overviews: generated height, water, material and physical-climate samples from the original game. The 4K panoramas are offline Blender terrain renders with no vertical exaggeration; they omit vegetation, caves and small structures. North-up maps and diagnostic layers use NumPy and Pillow. Legend arrows and scale bars are drawn locally; island views use WebP quality 94. They are distinct from production-renderer biome photographs. Grid and image hashes are recorded in `data/islands.json`.
- Animals: descriptions and habitat candidates derive from `entities/mod.rs`. Model portraits use production geometry and texture exports, rendered by the game’s Blender gallery pipeline at 512 × 512. Four static views per species are converted to WebP without cropping. Studio lights scale with model bounds for consistent illumination. Animal source, mesh and image hashes are recorded in `data/animals.json`; the 28 September refresh contains 93 species and 372 portraits. Its PNGs, canonical OBJ exports, exact-input reuse proof and final source manifest remain under `.cache/animal-model-refresh-2026-09-28/`.
- Fonts: the visitor's installed system fonts; no font assets are redistributed.
- Biome source/binary snapshot hashes: `data/provenance.json`. The source was a modified local working tree, so the recorded Git commit alone does not reproduce it. The generation-9 biome capture build is isolated: the previously complete application snapshot plus the terrain, generation-version and debug-horizon changes. Unfinished concurrent entity, shader, village and profiling edits are excluded; the exact composition is recorded in the frozen source manifest, without reverting the shared game checkout.

The fixed-seed measurements describe this snapshot. They are not guaranteed frequencies for all seeds or future game versions.

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
