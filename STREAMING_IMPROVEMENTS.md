<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Why streaming became faster — 30 September 2026

The improvement comes from doing less unnecessary work and retaining less
nearby geometry. It is not a new GPU, a blanket reduction in world resolution,
or a measured promise of a particular FPS multiplier.

## What changed

- **Reuse meshes during LOD transitions.** An unchanged outgoing mesh now keeps
  its GPU buffers for the fade. Previously a level change could rebuild and
  upload both the outgoing and incoming representations.
- **Coalesce edits and cancel obsolete work.** A chunk already being meshed gets
  one pending latest request. Teleports and changed LOD plans cancel queued work
  that can no longer be displayed. Stale completions cannot replace newer data.
- **Retire old GPU residency after teleporting.** Rendering reconciles its cache
  against world residency, including when distant terrain is disabled.
- **Use distance in three dimensions.** The visible detailed radius is capped
  at 64 metres. High flight uses distant ground instead of retaining a detailed
  column all the way down. Coverage checks keep the old representation until
  its replacement is ready; nearby collision data remains available.
- **Stop simulating distant unloaded wildlife.** Creatures outside the retention
  volume are culled; retained distant creatures wait for their terrain instead
  of repeatedly probing unloaded procedural ground.
- **Keep fine LOD decisions separate from GPU batches.** Selection now follows
  16-metre chunk footprints. Equal neighboring regions merge inside the existing
  128-metre batches, avoiding thousands of extra buffers and draw objects.
- **Cache repeated terrain bounds.** The earlier surface-band cache removes
  repeated height/canopy sampling during stationary streaming and pruning.

## Recorded evidence

| Same replay observation | Before | After |
| --- | ---: | ---: |
| Resident detailed chunks after 640 m flight | 1,777 | 543 |
| Recorded detail mesh builds during that flight | 4,023 | 2,393 |
| Recorded detail/LOD builds in final 1,080 idle frames | — | 0 / 0 |
| Nearby collision-cache chunks at Y = 600 m | — | 27 |

The original audit recorded 50 LOD jobs producing 77 mesh builds: the extra
outgoing builds were real redundant work. The final replay recorded 16 jobs
and five builds, but cancellation and jobs crossing measurement boundaries
mean those totals **must not be treated as a timing speedup ratio**.

A teleport regression confirms that the first rendered synchronization removes
all 1,046 stale GPU chunks in its fixture. A settled 64-chunk aerial comparison
keeps exactly 252 resident / 60 visible distant batches while refining selection
from 128-metre squares to 16-metre steps.

These are release/devtools, 960 × 540 offscreen replays with asynchronous workers.
They are not equal-duration windowed FPS benchmarks. Earlier independently
measured stationary CPU reductions (pine 18.3 → 8.7 ms; rainforest 33.1 → 8.2 ms)
are documented in [the surface-cache report](PERFORMANCE_OPTIMIZATION.md).
CPU worker time and GPU time use different clocks and must not be added.

## Why detailed chunks still exist

LOD 1 and detailed terrain both sample half-metre voxels. Detailed chunks also
carry arbitrary local edits, full occupancy, lighting and gameplay interaction.
The distant representation is a bounded terrain/decoration approximation,
including sampled cave floors, roofs and cliff openings. Sharing canonical tree
and cactus geometry reduces visual disagreement without making distant meshes
responsible for local physics. They overlap only where readiness and transitions
require replacement coverage.

The debug controls expose this work: F3 shows exclusive CPU effort, a pie chart,
red budget overruns and frame-specific lag attribution. Spike records are written
as bounded asynchronous JSONL logs. GPU samples are labeled separately; windowed
GPU timings are not implied when unavailable.

## Visual follow-up

Flat terrace normals now remain independent of greedy rectangle boundaries.
Ice retains full block height and no longer carries liquid-only inset/depth flags
that conflict with non-liquid handoff flags. Nearby cactus LODs share connected
stem geometry, including raised arms. Structure culling respects excavated air.
Leaf curtains gain cached supporting twigs, leaves retain their quarter shapes,
and rain uses narrower tapered drops with a camera-distance fade. Atmospheric
fog is denser, with the Balanced coefficient increased by about 22%.

The blue frame was identified near `(-8, 18, -78)` metres in the legacy debug
world and reproduced from a read-only copy of the save. Its lumen-crystal outer
frame, obsidian inner frame, open center and projecting luminous/amethyst feet
match the saved edits. The feet are authored blocks, not stale duplicate meshes.
A regression checks that the opening and material-specific exposed faces survive
all six LOD stages.

## Remaining wildlife spike

The same 1,200-tick boosted-flight replay exposed a 37.23 ms spawn CPU peak.
Spreading admission over two candidates alone did not remove it: the first
residency check could find air near the player while the proposed animal's
actual ground and neighboring collision chunks were still unloaded.
Admission now waits for that whole local volume before querying occupancy.
The seeded candidate grid rotates, so deferred candidates do not starve later
cells or permanently prevent wildlife after descending.

| Flight CPU measurement | Before | After |
| --- | ---: | ---: |
| Spawn mean per frame | 0.167 ms | 0.038 ms |
| Spawn maximum | 37.229 ms | 0.257 ms |
| Total simulation mean per frame | 1.387 ms | 1.242 ms |
| Total simulation maximum | 40.155 ms | 6.879 ms |

This does not remove all flight costs. Creature motion peaked at 5.334 ms in the
final replay. The old cold-spawn report at `(100000,200,0)` no longer reproduces:
the read-only 120-tick legacy fixture recorded 4.49 ms total creature CPU and a
0.043 ms maximum, with zero animals while its ground was unavailable.

## Optional 512-chunk horizon

The setting now reaches **512 chunks / 8 km**, with the default still **64**.
At 512, complete 4×4 groups of Remote tiles outside the two-kilometre ring use
one 512-metre GPU batch. Nearby LOD selection still follows 16-metre chunks.
The active old representation stays until its entire replacement group is
ready; parent and child batches never draw together. Changes to any child edit
invalidate the group, and obsolete buffers retire after the switch.

Remote trees retain the same canopy occupancy and tint but replace their full
branch graph with one rooted trunk. Over the fixed forest probe, sixteen base
batches fell from **518,356 to 72,100 vertices** (86.1% fewer); merging those
regions reduces that to 70,464. This is a mesh-size result, not an FPS multiplier.
Ocean, desert and forest probes confirmed that grouping covers the same area.

The native Intel Iris Xe matrix used seed 42, current generation, camera
`(0,400,0)`, clear weather, Fast shaders and 960×540 offscreen rendering:

| Settled same-camera measurement | 256 chunks | 512 chunks |
| --- | ---: | ---: |
| Resident distant batches | 3,404 | 2,408 |
| Visible distant batches | 1,056 | 777 |
| Allocated distant vertex buffers | 1,792.2 MiB | 1,891.8 MiB |
| Mean world GPU pass | 37.30 ms | 38.65 ms |
| Mean render CPU scope | 1.71 ms | 1.87 ms |

The extra horizon settled in 11.8 seconds after switching from 256 in this run.
During eight seconds of boosted flight, sampled buffer allocation peaked at
1,995.3 MiB and the scheduling/upload scope reached 15.1 ms CPU; the existing
budget cannot interrupt an individual upload. After the long teleport, the
ocean view settled in 7.8 seconds at 305.2 MiB; shrinking to 32 chunks released
that to 12.0 MiB / 77 batches. Worker queues drained in every settled capture.
The teleport's first frame is still loading, as expected for uncached terrain.

This remains an expensive optional view, especially over forests. Buffer bytes
exclude indices, textures and driver overhead, and are **not total GPU memory**.
The measurements are single shared-machine offscreen observations, not stable
windowed FPS or performance guarantees. Save version 18 persists the new setting
while preserving the meaning of older horizon bytes.

## Reproduction and scope

Native replay inputs live in `tools/debug_scenarios/`: `performance_residency`,
`lod_high_altitude`, `lod_caves`, `lod_granularity`, `leaf_support_rain`, and
`lod_surface_regressions` (JSON). Wait for distant residency before comparing
screenshots; fixed tick counts do not guarantee completed worker jobs.

Local evidence: `.cache/debug/performance-fix-report.md`,
`.cache/debug/lod-granularity-report.md`, `ice-before.log`, `terrace-before.log`,
`structure-before.log`, and the `surface-final-*` verification logs. The older
handoff documents describe dated snapshots; this report supersedes their earlier
statement that selection remains one LOD per 128-metre tile.

## Final verification — 30 September

The current checkout passes 1,357 workspace tests, with zero failures and
19 intentionally ignored checks. Formatting, strict all-target/all-feature Clippy and workspace Rustdoc
pass. The optional devtools suite passes 93 tests (one ignored); all 33 Python
tool tests pass. GPU checks used Intel Iris Xe to avoid competing for the running
player session's NVIDIA memory. No player saves were written.

Fresh native before/after surface captures are in local debug sessions
`session-5pv7p4zc` and `session-pyyj3s91`; all six images were inspected after
waiting for distant residency. Leaf/rain captures are `session-9utb7gfx` and
`session-kez1d5br`. The fixed ice, terrace, and excavation regressions each failed
before their correction. Cactus geometry is checked against its canonical raised
arm fixture through Near, Fine and Middle LODs.

Final follow-up evidence: flight `session-3c6c2ib9` → `session-3vgd7ndx`;
remote forest `session-ulz_iz1_` → `session-ifda6lna`; full horizon matrix
`session-2zf6jpzz`; blue frame `session-2ltdt4c_` → `session-55z093ov`; Sundown strike
`session-wv6ccbcm`. The strike replay also validates the concurrent flash/cloud
presentation changes. `tools/benchmark_horizon.py` waits for actual worker
completion and writes capture counts, buffer bytes and profiles into its local
`horizon-summary.json`. No normal save is modified.
