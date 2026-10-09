<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Island terrain and climate exports

From `qiqi-dev`, with the sibling `Voxelgame` source frozen:

```sh
python3 tools/export_island_grids.py --cargo /usr/bin/cargo --date 2026-09-27
```

For an isolated game snapshot, pass `--game .cache/generation9-refresh/source`.
The script copies the sampler into its output directory and rewrites its core
dependency to that exact path; it never silently builds against the live game
checkout. `--target-dir` can share dependency artifacts with the biome survey.

`tools/island_sites.json` selects six actual seed/ownership-cell fixtures. The
exporter reruns the game's ignored, devtools-only `export_island_atlas_candidates`
test to obtain their private island plans. It then builds `island_grid`, which
samples `World::terrain_sampler().surface_column`, and runs the ignored
`export_island_atlas_climate` test for the private physical fields. No generator
formulas are copied into the atlas, and the game exports no additional runtime
API. Changed or missing curated plans fail explicitly and require visual review.

Outputs are under `.cache/island-atlas/`:

- `geometry.json`: catalog geometry, measured sample area, grid paths and hashes.
  Planned ellipse axes are distinct from sampled dry bounds and sampled area.
- `grids/SLUG.bin` and `.json`: sampled terrain and its metadata/palette.
- `grids/SLUG-climate.bin` and `.json`: six actual physical generator fields.
- `grid-provenance.json`: core source hashes, sampler hash and inputs.

The renderer/builder adds the final map and panorama views to `data/islands.json`
and its offline JavaScript mirror. Terrain overviews omit objects smaller than
the sampling interval, including most foliage and small structures.

## Surface grid

The default is a 1025×1025 endpoint grid, square in world metres. Row zero is
`minZ` (north), columns increase toward `maxX`. The selected bounds remain the
same for terrain and climate. World positions are rounded to the nearest
half-metre voxel before sampling. Height is the top face of the occupied voxel,
`(height + 1) / VOXELS_PER_METRE`, in metres. There is no vertical exaggeration.

Each little-endian record occupies 12 bytes (`<ffBBBB`):

| Offset | Type | Value |
| --- | --- | --- |
| 0 | f32 | Ground top-face height in metres |
| 4 | f32 | Water top-face height in metres, NaN when dry |
| 8 | u8 | Ground block/material ID |
| 9 | u8 | Authoritative biome ID |
| 10 | u8 | Water block/material ID, air/0 when dry |
| 11 | u8 | Reserved, zero |

The JSON sidecar includes `resolution`, `bounds` (`[minX,minZ,maxX,maxZ]`),
`spacingMetres`, `recordBytes`, `dataFile`, `heightRangeMetres`, and `palette`.
The palette maps numeric block IDs to the unmodified `Block::color()` RGBA
floats in 0..1. `dryBoundsMetres` is null for an entirely wet frame.
`sampledDryAreaKm2` uses trapezoidal endpoint weights and includes all dry terrain
inside the frame, including satellite islets. It is a resolution-dependent area
estimate, not the exact area of one connected island.

## Climate grid

Each record is six little-endian f32 values (24 bytes), at the same endpoint
positions. The sidecar `fields` array supplies byte offsets, labels, descriptions,
display ranges and observed ranges.

| Offset | Field | Interpretation |
| --- | --- | --- |
| 0 | `temperature` | 0..1 cold-to-warm climate carrier, including altitude cooling |
| 4 | `moisture` | 0..1 dry-to-wet climate carrier with maritime, upwind and drainage effects |
| 8 | `continentality` | 0..1 ocean-to-interior island support carrier |
| 12 | `ruggedness` | 0..1 tectonic/volcanic relief character, not measured local slope |
| 16 | `riverDistance` | 0..0.5 drainage distance carrier; zero is near a channel, not metres |
| 20 | `geothermal` | 0..1 physical volcanic heat, not air temperature |

Temperature is not Celsius, and moisture is not relative humidity. These are the
actual unperturbed physical `terrain_profile` values; biome classification adds
small ecology offsets to temperature and moisture. The physical coastline also
depends on elevation and hydrology, not just the continentality field.

Exports use at most four sampling threads and process islands sequentially.
The script rejects source changes during export and mixed generator versions.
Use `--resolution 129` and a separate `--output` directory for inexpensive visual
scouting. The core's manual climate test can also accept an explicit CSV through
`VOXELGAME_ATLAS_CLIMATE_INPUT` and an output directory through
`VOXELGAME_ATLAS_CLIMATE_OUTPUT`.
