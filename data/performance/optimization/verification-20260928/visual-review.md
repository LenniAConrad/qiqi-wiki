<!-- SPDX-License-Identifier: GPL-3.0-only -->

# Native visual review — 28 September 2026

Reviewed all 126 frame captures from the eight accepted replays in fourteen
contact sheets. Also inspected the middle/far crater and disabled-horizon land
captures at native resolution. The raccoon tail atlas was inspected before the
test correction and remains byte-identical afterward; the bounded grain and
alternating bands are intentional.

- The land/water matrix covers 36 combinations of horizon enabled/disabled,
  Classic/Fast/Cinematic shading, and Off/Edges/X-ray voxel views. Ground and
  water coverage remain continuous within loaded terrain; disabling the horizon
  leaves the expected finite detailed-chunk boundary. Debug colors distinguish
  detailed chunks from the six distant stages.
- The TNT excavation stays excavated at close and middle distance, with no
  green fill replacing its exposed interior. Further views retain the terrain
  and tree coverage through the detail handoff.
- Water flight, diving, and surfacing preserve the expected water/kelp surfaces.
  The immediate cold-start frame precedes chunk generation and is explicitly
  loading evidence, not a fully loaded landscape.
- The village remains intact through horizon toggles, 60–640 m inspection
  distances, reversed viewing direction and ordinary flight. The fixed-step
  checkpoint named `village-on-settled.png` still has outstanding far-tile work;
  a separate check waits for two quiet stable windows before accepting a fully
  loaded capture. That follow-up passed with 3,092 resident / 958 visible
  detailed chunks, 71 resident far tiles and the full 128 m detail radius.
  The native-resolution `village-on-fully-settled.png` was reviewed and retains
  consistent terrain and structure coverage, with an empty native log and no
  edits or save writes.
- All four signed render-origin crossing sequences retain spatially aligned
  water geometry. Disabled-horizon sequences show the resident geometry limit;
  fog/rain varies with each fixture's requested weather.
- The study timer retains readable controls over real terrain, fixed/orbit
  camera behavior, rain options, and return to the illustrated background.

All eight native logs are empty and all returned save flags are false. The
TNT replay intentionally edits its disposable world; no normal save is written.
This review records these scenes and discrete frames, not an exhaustive claim
about every possible world, hardware configuration, or intervening frame.

The final build includes the concurrent Bat, River Otter and Penguin spawn-egg
mappings added after the eight-replay build. Movement and toggle-readiness
smoke replays pass again on that executable (64 commands). All eleven extra
toggle captures were reviewed; their native logs are empty and save writes
remain disabled. Terrain/rendering source is unchanged between these builds.
The immediate toggle frames retain available detail while far tiles rebuild;
they do not promise an instantly restored, fully populated horizon.
