<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Player wiki roadmap — owner request, 2026-10-09

The existing atlas is useful but is not a practical manual. Expand it into an original, searchable, statically hosted wiki that answers “how do I use this?” for ordinary players. Preserve existing biome/animal/island/village galleries and provenance. Do not rewrite old measurements as current evidence.

## First release

1. Audit the latest landed Voxelgame source and actual normal input. Establish a feature/status/control/recipe catalog tied to game commit and version, not inferred from agent backlog promises.
2. Clear navigation, search, Getting started, controls and survival/creative differences. Practical steps with prerequisites, relevant keys/buttons, expected outcome and a tested game screenshot where useful. Player language, not implementation jargon.
3. Crafting/materials/tool tiers and durability, inventory/stack movement/tooltips, resource gathering, cooking/furnaces, building/storage/glass, combat and Erik/Thor interaction/spawning.
4. Maps/exploration/caves, boats/sailing/wind controls and recovery, weather/water/fire/lava when implemented. Explain map visibility by mode and travel controls truthfully.
5. Resource packs, animal/structure/texture editors, skin import/save/painting, blueprint placement and workshops: short actual workflows with valid file formats and safe recovery guidance.
6. Optional mods and dimensions: enable/disable, entry/return, dangers, creative spawning and save behavior. Herobrine/hell/sky mods are PLANNED until landed and playable; do not invent their recipes or entry mechanics.
7. Platform install/update, graphics settings/performance, multiplayer connection, common failures and native error-window/log instructions as available.

## Ongoing maintenance

Read agent-hub/backlogs/voxelgame.md, landed.log and current game source. For every newly landed player-facing feature, update the relevant guide and its version/commit receipt. Claims need source or actual gameplay evidence; planned pages are visibly labelled. Keep a wiki coverage ledger linking each feature to guide/evidence/next update. Coordinate feature agents to supply actual controls/recipes/screenshots. Wiki work should continue between game releases, not only at final cleanup.

No invented screenshots, proprietary copied artwork, hidden runtime service dependency or mandatory paid APIs. Static relative links must work on GitHub Pages and offline. Use small coherent commits, validate metadata/images/links/scripts, inspect browser layouts at mobile and desktop sizes, keyboard/tooltip/search accessibility and offline behavior. Reuse existing design rather than gratuitously replace the atlas. Publishing is authorized by the owner's request for a separate statically GitHub-hosted wiki; maintain exact original-asset/licence/provenance notices.

## Latest owner additions

Performance and memory analysis must include current measured FPS/frame-time/stutters/CPU/process RSS/peak RAM/system memory/VRAM, settings and loading/streaming/horizon/water comparisons with reproducible hardware/game-commit/seed/settings receipts and artifact-derived plots. Do not substitute old archived figures or guess metrics.

Installation guides must cover the requested update script and installer update-existing path, player-data preservation, failed-update recovery/rollback and version checks when implemented. Coordinate VOX-OWNER-UPDATE-INSTALLER; mark unimplemented functionality as planned.

## Progress — 11 October 2026

- **Coverage ledger (QW-COVERAGE):** `features.html` lists 213 player-facing features of Voxelgame main `dd29d91` with one status each, verified controls, 743 cited source locations, the request IDs of planned work, 15 ranked guide gaps and 10 places where the game's documents disagree with its code. `data/features.json` is the source; `tools/build_features.py` renders and `tools/validate_features.py --game` checks it against an export from `tools/export_game_snapshot.sh`. It is a source audit, not a play test.
- **Deployment fix:** the Pages artifact now includes the linked performance reports; links are validated inside the staged site.
- **Browser QA:** `tools/browser_run.py` drives headless Firefox through Marionette for in-page checks, real keyboard input, `file://` loading and 1440/820/390 px captures without overflow.
- **Next:** write the ranked guides, starting with Getting started, Controls reference, Your first survival day and Crafting and recipes, each verified in a disposable headless session; then the measured performance and memory study.
