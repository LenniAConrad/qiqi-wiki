<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Original game validation — 2026-09-27 snapshot

The headless runs, focused core profiling tests (2), native devtools tests
(81 passed / 1 ignored), and Python adapter checks (15) passed. Final Clippy,
formatting, documentation, release build and the six-stage tree probe passed.

The full workspace test run reported five failures outside profiling:

- `entities::models::aquatic_tests::blobfish_mouth_is_exposed_on_the_face_below_the_nose`
- `entities::models::tests::focused_species_keep_their_defining_final_silhouettes`
- `entities::models::tests::animal_parts_stay_attached_through_walk_and_attention_poses`
- `world::generator::ecology::tests::landscape_composition_preserves_water_bare_ground_and_rock_caps`
- `atlas::tests::every_species_has_one_unique_opaque_original_pixel_tile`

An intermediate duplicate-Boar match warning was removed by concurrent creature
work before the final clean Clippy run. The full suite was not rerun after
concurrent changes. This is a dated validation record, not a statement about
later source revisions or the atlas's separately captured worldgen snapshot.
The game evidence folder `.cache/load-analysis/REPORT.md` retains exact logs,
source locations and debug-session directories. No normal saves changed.
