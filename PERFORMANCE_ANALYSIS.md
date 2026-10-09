<!-- SPDX-License-Identifier: GPL-3.0-only -->

# Component load analysis — 2026-09-27

The follow-up [streaming optimization report](PERFORMANCE_OPTIMIZATION.md)
records the bounded surface-cache implementation and its separate 28 September
before/after measurements. The original analysis below retains its dated results.

The largest sustained cost in these scenes is GPU world rendering and shadows.
Trees have a measurable rendering cost, but removing their geometry leaves most
of that cost in place. The clearest CPU problem is repeated terrain-height
sampling for streaming plans, including when the camera is stationary. During
flight, background chunk generation and meshing become the largest CPU consumers.

These are measurements of the development snapshots described below, not an
FPS promise or a performance optimization. The added profiling hooks compile
out of normal builds. No player saves were changed and no visible windows opened.

## Settled rendering

Intel Core i9-13900H / Intel Iris Xe, Vulkan offscreen rendering, 960×540,
Fast shader, 32-chunk view distance, distant terrain enabled, clear weather,
fixed daytime and camera. Each run warmed for 20 seconds and measured for 8.
The following values are the median of two per-run averages in milliseconds
per frame. All included runs completed no background mesh jobs during their
measurement window.

| Scene | Main-thread CPU | World GPU | Shadows GPU | Post + UI GPU | Total measured GPU |
| --- | ---: | ---: | ---: | ---: | ---: |
| Meadow | 8.9 | 11.1 | 4.4 | 0.40 | 15.9 |
| Mixed grove | 8.3 | 14.1 | 5.7 | 0.40 | 20.2 |
| Pine hills | 10.2 | 18.5 | 5.2 | 0.41 | 24.2 |
| Rainforest | 16.2 | 24.4 | 9.1 | 0.39 | 33.9 |
| Bamboo thicket | 9.6 | 25.3 | 7.3 | 0.41 | 32.9 |

World and shadows together account for 97–99% of measured GPU pass time.
The world pass includes terrain, vegetation, entities, water and atmosphere;
this experiment does not separately time those draws or distinguish vertex,
fragment, bandwidth and overdraw limits. Bamboo is expensive in this camera,
but its entire 32.9 ms cannot be attributed to bamboo plants alone.

CPU and GPU clocks have separate denominators: **do not add these columns**
or invert their sum to predict windowed FPS. The offscreen renderer waits for
GPU completion, and pass timestamps exclude uploads and time waiting in queues.

| Scene | Streaming checks CPU | Render preparation CPU | Remaining main-thread CPU |
| --- | ---: | ---: | ---: |
| Meadow | 4.6 ms | 2.8 ms | 1.5 ms |
| Mixed grove | 4.2 ms | 2.7 ms | 1.4 ms |
| Pine hills | 4.7 ms | 3.6 ms | 1.9 ms |
| Rainforest | 10.0 ms | 3.8 ms | 2.4 ms |
| Bamboo thicket | 6.3 ms | 1.9 ms | 1.4 ms |

The CPU columns use exclusive scopes. Render preparation here is the remaining
`render.total` work after named child scopes, chiefly visibility/draw preparation
and command encoding. The remaining column includes entity rendering preparation,
UI, scene lighting, simulation, driver wait bookkeeping and profiler readback.
In the first meadow/pine/rainforest runs, creature simulation cost 0.06–0.16 ms
per frame, player update about 0.015 ms, UI preparation 0.17–0.22 ms, and cached
minimap preparation about 0.002 ms. These small stationary values do not cover
combat, many spawned creatures, full-map searches, storms or enabled mods.

## Tree geometry comparison

Separate fresh processes retained the same world, camera and settings while
suppressing near and distant natural-tree geometry. Each condition has two runs.

| Scene | Normal GPU | Trees hidden GPU | Net reduction |
| --- | ---: | ---: | ---: |
| Mixed grove | 20.2 ms | 18.1 ms | 2.1 ms / 10.3% |
| Pine hills | 24.2 ms | 19.2 ms | 4.9 ms / 20.4% |
| Rainforest | 33.9 ms | 29.0 ms | 4.9 ms / 14.5% |

These are **net scene differences**, not an additive measurement of every tree
operation. Removing geometry changes occlusion, exposes ground and changes
shadow-map work. Procedural occupancy, collision, tree data and shadow-ray
occupancy remain. The diagnostic near-mesh mask also covers modeled cactus stems;
the compared scenes are forest locations. Screenshots verified the intended
forest views and removal of tree meshes.

In additional detailed loading/flight traces, explicitly named tree work
(root/graph construction, cached voxel lookups, daylight-column lookup, tree
voxelization, generated wood/leaf geometry and distant-tree meshes) used 0.4–1.1% of
total process CPU. **That is not the total CPU cost of trees:** chunk scans,
block retrieval, shared lighting and surrounding terrain queries remain in
common meshing categories.
Once settled, those explicit tree construction scopes were essentially inactive.
The useful distinction is construction while streaming versus repeated GPU
drawing of the resulting geometry every frame.

The tree crown mesher currently uses two geometric resolutions across the six
terrain rings: Near/Fine/Middle/Far share the full occupancy grid;
Horizon/Remote halve its resolution. Six terrain stages therefore do not imply
six different crown mesh densities. The manual tree probe now covers every ring
and pins its historical forest to generation 4 so changing world generation
cannot silently turn the reference forest into a different habitat.

That release probe passed for 267 trees. Crown geometry contained 111,888
vertices on each of the first four rings and 24,412 on each of the last two
(78% fewer). Crown construction took roughly 10.5–11.0 ms versus 3.2–3.3 ms
for the whole reference stand. Those are generation-4 crown-construction
measurements, excluding trunks and GPU rendering, not per-frame costs of the
generation-9 scenes above. The record itself occupies 152 bytes per tree;
mesh storage is additional.

## Early streaming and movement

Fresh disposable sessions used the same pine and rainforest saves and normal
boosted flight input. Each profiled window contained 120 fixed steps at 1/60 s.
Early streaming measured two windows after initial renderer setup; stationary
and flight windows followed an unprofiled warm-up. These measure the game paths
used during loading, not total application startup time.

The table gives **exclusive percentages of all process CPU time**, including
worker threads, for the final instrumented snapshot. Detail meshing below
includes its separately measured sky-lighting work; named tree scopes are
excluded from the other rows to avoid double counting.

| CPU work | Pine loading | Rainforest loading | Pine flight | Rainforest flight |
| --- | ---: | ---: | ---: | ---: |
| Detailed meshing, including sky lighting | 40.3% | 41.3% | 59.6% | 56.9% |
| Chunk generation | 23.0% | 20.5% | 18.5% | 15.2% |
| Distant plants and rocks | 15.4% | 15.4% | 6.9% | 10.5% |
| Other distant terrain meshing | 8.6% | 5.7% | 4.6% | 5.4% |
| Streaming surface bounds | 3.3% | 4.8% | 2.9% | 4.1% |
| Explicit tree operations | 0.7% | 0.4% | 0.7% | 1.1% |
| Unattributed / jobs crossing window boundaries | 7.0% | 10.7% | 4.1% | 4.4% |

The remaining roughly 1–2% is render preparation, simulation, uploads and other
instrumented work. Sky-lighting cache misses alone accounted for 7–11% of process
CPU during these loading/flight samples, within the detail-meshing row above.
Concurrent worker CPU seconds can exceed elapsed wall seconds. Different async
completion order means these fixed-step windows do not complete identical jobs;
their percentages describe observed load, not exact per-chunk comparisons.

## Repeated streaming plans are a stutter candidate

`Game::update_world_streaming` rebuilds requests every 0.35 simulated seconds.
`World::queue_chunks_around` visits 293 horizontal chunk columns in these traces.
For each, `surface_chunk_band` samples nine procedural heights to retain the
ground and full tree-canopy interval. Pruning repeats that calculation.
The plan still does these height checks when the camera has not moved and all
requested chunks are resident.

The final stationary pine trace spent 1.06 CPU seconds in five plans across
120 frames; the rainforest trace spent 1.75 CPU seconds in five plans.
The slowest individual plans took 266 ms and 412 ms of thread CPU respectively.
Surface bounds consumed about 54% and 68% of all process CPU in those settled
fixed-step traces. Earlier detailed traces reproduced the same hotspot in meadow,
pine and rainforest; it is not specific to one forest.

Those spikes were measured while other workspace compilation/testing sometimes
competed for the machine. Their absolute durations are not a clean idle-laptop
baseline. CPU clocks exclude time descheduled, but frequency, thermal state and
cache/memory contention still affect CPU execution time. The repeated work is
confirmed by both call counts and source inspection.

The first optimization to investigate is reusing bounded per-column surface
intervals and skipping unchanged streaming plans. Any implementation must retain
the current canopy/sea coverage invariant and invalidate correctly for edits,
world/generator changes and terrain profiles. Do not narrow the retained band
to save time: that risks restoring missing treetops and LOD handoff holes.

Next priorities are GPU world/shadow cost, then detailed meshing and lighting
while moving. Trees offer roughly 2–5 ms of measured net GPU opportunity in
these scenes, but the remaining terrain/vegetation work is larger. A separate
bamboo/ground-cover ablation and shader/overdraw investigation would identify
which part of the world pass deserves optimization; these measurements alone
do not justify adding another LOD stage or reducing every tree indiscriminately.

## Method, overhead and retained evidence

Profiling uses thread CPU clocks with nested exclusive accounting, process CPU
clocks, and optional hardware GPU pass timestamps. Linux `perf` sampling was
unavailable (`perf_event_paranoid=4`), so no sampling flame graph is claimed.
No system permissions were changed. See [profiling guidance](data/performance/PROFILING.md) for
`step` with `profile:true`, `VOXELGAME_PROFILE_JSON`, and tree geometry masking.

Eighteen stationary runs were executed. Sixteen profiled, settled runs form
the tables; one additional profiled pine run was still completing 532 detail
mesh jobs and was excluded. One unprofiled run was attempted for overhead
comparison, but competing work made that wall-time comparison inconclusive.
The GPU pass results were substantially more stable than whole-frame wall times.
Two runs per condition are a diagnostic sample, not a confidence interval.

An empty nested scope microbenchmark measured about 2.4 microseconds of CPU
overhead per enabled call, and 6 nanoseconds wall time per disabled call in a
devtools binary. At the observed call counts, that suggests roughly 0.3–1.1%
observer overhead in the final traces, not a rigorous correction. Very small
tree operation times are especially sensitive to it. GPU readback itself used
about 0.03–0.06 ms CPU per frame. Normal builds have no profiling call sites.

The stationary matrix used one preserved executable. The later CPU traces used
separate preserved executables with progressively finer scopes, amid concurrent
workspace changes; do not treat those as an optimization before/after pair.
Generation 9 fixtures use seeds 42, 9001, 7 and 4242. The mixed-grove fixture is
at a dense-forest/bamboo boundary and is not a pure oak benchmark. Input-save
hashes matched before/after every stationary run. All replays use disposable
sessions with saving disabled.

Local evidence is in `.cache/load-analysis/`: `summary.json`,
`steady-results.csv`, raw per-run JSON/logs/metadata/screenshots, input saves,
preserved executables, `*-load-windows.json`, `*-final-windows.json`, replay
scenarios, `profile-overhead.log`, and `component-costs.png`. `REPORT.md` there
records validation and exact debug evidence directories. `summarize.py`
recreates the settled summary and chart from the retained raw aggregation.
