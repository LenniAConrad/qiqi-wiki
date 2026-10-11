<!-- SPDX-License-Identifier: GPL-3.0-only -->

# Streaming performance optimization — 2026-09-28

The repeated terrain sampling identified in the [load analysis](PERFORMANCE_ANALYSIS.md)
now uses a bounded per-world cache. The complete surface, tree-canopy and sea
coverage interval remains unchanged. This targets CPU stalls during streaming;
world drawing, tree geometry, shadows and graphics settings are unchanged.

## Measured result

Each result below averages two 120-frame stationary windows in a fresh process
after background generation and meshing have settled. Resident/visible geometry
counts and camera positions match between each before/after pair.

| Scene | Main CPU before | Main CPU after | Reduction | Streaming + pruning before → after |
| --- | ---: | ---: | ---: | ---: |
| Pine hills | 18.3 ms/frame | 8.7 ms/frame | 52.7% | 10.89 → 0.014 ms/frame |
| Rainforest | 33.1 ms/frame | 8.2 ms/frame | 75.1% | 24.72 → 0.017 ms/frame |

The slowest individual stationary streaming plan fell from **263 to 0.40 ms**
of thread CPU in pine and **524 to 0.49 ms** in rainforest. Both scenes formerly
sampled 3,548 surface bands across those 240 frames, including pruning; the
optimized runs sampled **zero**. Request maintenance still ran 11 times.

Measured GPU pass time stayed essentially unchanged: pine 24.27 → 24.36 ms/frame,
rainforest 34.56 → 34.52 ms/frame. This improves CPU work and removes a repeated
stall source; it does not establish a matching percentage increase in FPS.
The GPU remains the major sustained cost in these forest views.

## Implementation and correctness

Detailed streaming and pruning share up to 1,024 cached horizontal chunk
columns. A miss performs the same nine height samples as before. FIFO eviction
removes one old column at a time, so long journeys cannot grow the cache without
bound or periodically discard every useful nearby entry. Hits neither allocate
an eviction record nor recompute procedural height.

Keys use absolute integer world coordinates. A world's seed and generator
version are immutable. Structure overlay installation, growth, replacement,
removal and terrain-profile changes advance the landscape revision and
invalidate cached bounds. Ordinary player and fluid edits do not change
`World::surface_height`, so they retain the cached reference interval; their
existing occupancy, mesh invalidation and persistence paths still run. The
cache is never serialized.

Request maintenance still runs at an unchanged camera position. In particular,
new structure roofs and crowns can add required chunks after the first plan.
The optimization does not narrow the vertical band or bypass detail readiness.
See the game's `docs/ARCHITECTURE.md` and the Rustdoc on `SurfaceBandCache`,
`World::surface_height`, streaming admission and retention for the contracts.

Six added regressions cover bounded long-travel eviction, revision changes,
multiple generator versions and distant coordinates, structure growth and
removal, terrain-profile replacement/clearing, and ordinary block edits. The
existing canopy/readiness-envelope regression also passes.

The faster main thread exposed a race in the resident-meshing probe: 600 tight
simulation updates finished with only 19 resident chunks in a focused reproduction
(28 in the full suite), before background generation had time to run. Its setup
now waits for residency with a 30-second deadline and yields to workers, outside
the measured meshing interval. Its existing minimum-residency assertion remains.
The corrected probe passes and still meshes all 50 reference chunks.

Rustdoc now describes coordinate units, cache lifetime and invalidation, and the
distinction between reference surfaces and effective edited occupancy. A stale
private tree-mesher link to a removed trait method was replaced with the current
per-voxel filtering contract.

## Measurement method

The preserved before/after executables were built from a frozen source snapshot.
Only `world/mod.rs` and the new `world/surface_band_cache.rs` differ between their
source manifests. Later documentation and test-setup changes do not alter the
measured production implementation. Other Codex edits and running processes
were preserved.

Both binaries use release optimization and opt-in devtools profiling on the
same Intel i9-13900H / Iris Xe machine: Vulkan offscreen rendering at 960 × 540,
Fast shader, view distance 32, distant terrain on, clear weather and fixed
camera/daylight. Generation-9 pine and rainforest saves match the earlier
analysis. All sessions disable save writes.

Fixed-step replays first compare the same startup, stationary and boosted-flight
inputs. Stationary bounds stop being sampled after warm-up; across the two
120-frame flight windows, sampling falls from 3,841 to 128 columns in each
forest, **96.7% fewer samples**, with matching player positions. New columns still
need sampling. Asynchronous job completion can differ at the same simulation
step, so these flight traces do not establish an equal-work meshing speedup.

Eight additional alternating wall-time benchmark runs used a 30-second warm-up
and 8-second measurement. Background jobs were still completing in those runs;
they are retained as streaming evidence and excluded from settled-frame results.
A further fresh-process comparison waits for two successive 120-frame windows
with no generation/meshing completions and stable residency counts, then records
two 120-frame windows. Every included measurement window is checked again for
zero asynchronous job completions.

Concurrent compilation, tests and other captures make this a shared-machine
measurement, not an idle-laptop FPS claim. Thread CPU excludes descheduling,
but frequency, memory contention and driver work can still vary. CPU and GPU
use separate clocks; their times must not be added.

## Evidence

Local evidence is in `.cache/performance-opt/`: preserved executables,
`source-before.json` / `source-after.json`, replay inputs and logs,
`run_benchmarks.py`, `run_settled.py`, `summarize.py`, raw profiles and
`summary.json`. The source manifests identify exactly which files changed in
the A/B executable pair. Disposable debug bundles preserve input saves, native
logs, profiles, transcripts and images. No normal game window was opened.

## Validation and concurrent work

### Final audit — 28 September

The complete follow-up run passes **1,189 workspace tests**, with zero failures
and 18 intentionally ignored tests. `cargo fmt --check`, `cargo lint`,
`cargo doc --workspace --no-deps` and the private core Rustdoc build all pass
without warnings. The additional devtools run passes 81 tests (one ignored),
and all 15 Python debug-adapter tests pass. The recorded Rust, shader, manifest
and debug-tool source hashes stayed unchanged throughout every completed check.

The earlier atlas failure was reproduced and its native texture inspected.
Concurrent animal work corrected the assertion to allow the texture's intended
bounded grain while checking strong light/dark band contrast. The texture itself
was preserved. That assertion and the repaired residency probe now pass in the
complete workspace run. An interrupted preliminary run is retained separately;
it is not counted as a completed validation.

Eight fresh headless replays pass 780 commands and 118 assertions, covering the
36 land/water, horizon, shader and voxel-view combinations, flight/diving,
close-to-far TNT excavation, village structure views, all four signed horizontal
render-origin crossings, and the real-terrain study timer. All 126 frame captures
were visually reviewed, with native-resolution checks of the crater and horizon
boundary. Native logs are empty, distant tiles are absent in disabled-horizon
captures, and all returned save flags are false.

A separate village toggle follow-up waits for two stable 120-frame windows with
no generation or meshing completions. Its reviewed final capture retains 3,092
resident / 958 visible detailed chunks, 71 resident far tiles and the full 128 m
detail radius, with zero edits and disabled saves. Fixed-step checkpoints alone
are not described as fully loaded: cold starts and newly enabled horizons still
stream asynchronously, and disabling distant terrain exposes the finite resident
terrain boundary.

After concurrent Bat, River Otter and Penguin spawn-egg mappings arrived, the
latest shared source was rebuilt again. Its source hashes match the full-check
snapshot; fresh movement and rapid-toggle smoke replays pass another 64 commands,
and all 11 additional toggle captures were reviewed. The earlier eight-replay
build differs only in those three egg mappings and their tests; terrain and
rendering source are unchanged. The final executable's SHA-256 is
`210716cdc8014312b268666e0e7c699837812afaae14a7a2f03c6692066ee8e5`.

Logs, source manifests, native state summaries, visual-review sheets and the
preserved executables are in `.cache/perfection-audit/`. The published [final verification record](data/performance/optimization/public-verification.md)
summarizes check counts and native evidence. The original manifests and logs remain in the repository archive. Other Codex work and
processes were preserved. These checks found no regressions in the tested scenes;
they do not establish that every possible world and graphics configuration is
free of defects.

### Initial optimization check snapshot

- `cargo fmt --check` and `cargo lint` pass. Clippy covers all targets and all
  features with warnings denied; no lint suppressions or dependencies were added.
- `cargo doc --workspace --no-deps` and the additional private core Rustdoc build
  pass without warnings after correcting the stale tree-mesher link.
- All seven surface-band tests pass, including six new regressions. The repaired
  resident-meshing probe passes separately. `cargo test --features devtools`
  passes 81 tests, with one intentionally ignored test.
- The complete `cargo test --workspace --no-fail-fast` run recorded 1,181 passes,
  five failures and 18 ignored tests. One failure was the residency-test race
  fixed here. Four were in concurrent animal-model/atlas work. Fresh focused
  rechecks pass both model assertions and the Peafowl contrast assertion; the
  remaining `anatomical_part_tiles_have_their_expected_dominant_color_relationships`
  assertion in `crates/voxelgame-render/src/atlas.rs:2890` reported a row-brightness
  mismatch (2689 versus 2671). That work was left intact. This initial snapshot
  was **not reported as clean**; the complete final audit above supersedes that
  validation status.
- Both forest before/after input replays pass. The optimized
  `lod_toggle_readiness.json` (58 commands) and
  `distant_terrain_off_streaming.json` (35 commands) pass, covering repeated
  distant-terrain toggles, ordinary flight, boosted reversal and settling.
  The shared checkout was also rebuilt in release/devtools mode and the toggle
  replay passed in a fresh native process. An extended shared-build replay
  waited through two idle windows after the final toggle: the completed scene
  reached the full 128 m detail radius with 77 resident far tiles. Reviewed
  captures retain ground and canopy coverage; distant tiles still arrive
  asynchronously after re-enabling.
- Fully settled forest captures were inspected before and after. Pine retained
  2,344 resident chunks / 802 visible chunks / 76 resident far tiles; rainforest
  retained 2,051 / 695 / 71. All input-save hashes from the eight wall-time runs
  match before and after, and debug sessions report zero edits and disabled saves.

The checks describe the recorded snapshots. Other Codex sessions continued
editing and running throughout; their files and processes were not reverted or
stopped. These samples validate this optimization rather than proving that all
possible scenes and rendering combinations are free of defects.
