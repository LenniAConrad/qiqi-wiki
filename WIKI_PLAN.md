<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Player wiki roadmap — owner request, 2026-10-09

The existing atlas is useful but is not a practical manual. Expand it into an original, searchable, statically hosted wiki that answers “how do I use this?” for ordinary players. Preserve existing biome/animal/island galleries and provenance. Do not rewrite old measurements as current evidence.

## First release

1. Audit the latest landed Voxelgame source and actual normal input. Establish a feature/status/control/recipe catalog tied to game commit and version, not inferred from agent backlog promises.
2. Clear navigation, search, Getting started, controls and survival/creative differences. Practical steps with prerequisites, relevant keys/buttons, expected outcome and a tested game screenshot where useful. Player language, not implementation jargon.
3. Crafting/materials/tool tiers and durability, inventory/stack movement/tooltips, resource gathering, cooking/furnaces, building/storage/glass, combat and Erik/Thor interaction/spawning.
4. Maps/exploration/caves, boats/sailing/wind controls and recovery, weather/water/fire/lava when implemented. Explain map visibility by mode and travel controls truthfully.
5. Built-in character and building tools: short actual workflows with valid file formats and safe recovery guidance.
7. Platform install/update, graphics settings/performance, multiplayer connection, common failures and native error-window/log instructions as available.

## Ongoing maintenance

Read agent-hub/backlogs/voxelgame.md, landed.log and current game source. For every newly landed player-facing feature, update the relevant guide and its version/commit receipt. Claims need source or actual gameplay evidence; planned pages are visibly labelled. Keep a wiki coverage ledger linking each feature to guide/evidence/next update. Coordinate feature agents to supply actual controls/recipes/screenshots. Wiki work should continue between game releases, not only at final cleanup.

No invented screenshots, proprietary copied artwork, hidden runtime service dependency or mandatory paid APIs. Static relative links must work on GitHub Pages and offline. Use small coherent commits, validate metadata/images/links/scripts, inspect browser layouts at mobile and desktop sizes, keyboard/tooltip/search accessibility and offline behavior. Reuse existing design rather than gratuitously replace the atlas. Publishing is authorized by the owner's request for a separate statically GitHub-hosted wiki; maintain exact original-asset/licence/provenance notices.

## Latest owner additions

Performance and memory analysis must include current measured FPS/frame-time/stutters/CPU/process RSS/peak RAM/system memory/VRAM, settings and loading/streaming/horizon/water comparisons with reproducible hardware/game-commit/seed/settings receipts and artifact-derived plots. Do not substitute old archived figures or guess metrics.

Installation guides must cover the requested update script and installer update-existing path, player-data preservation, failed-update recovery/rollback and version checks when implemented. Coordinate VOX-OWNER-UPDATE-INSTALLER; mark unimplemented functionality as planned.

## Progress — 11 October 2026

- **Coverage ledger (QW-COVERAGE):** `features.html` lists 187 base-game features of Voxelgame main `dd29d91` with one status each, verified controls, source evidence, the request IDs of planned work, 13 ranked guide gaps and 6 places where the game's documents disagree with its code. `data/features.json` is the source; `tools/build_features.py` renders and `tools/validate_features.py --game` checks it against an export from `tools/export_game_snapshot.sh`. It is a source audit, not a play test.
- **Deployment fix:** the Pages artifact now includes the linked performance reports; links are validated inside the staged site.
- **Browser QA:** `tools/browser_run.py` drives headless Firefox through Marionette for in-page checks, real keyboard input, `file://` loading and 1440/820/390 px captures without overflow.
- **Player guides (QW-PLAYER-GUIDES, first slice):** `guides.html` indexes four source-checked guides (Getting started, Controls reference, Your first survival day, Crafting and recipes). `data/guides.json` holds the structured text, `data/recipes.json` the 37 recipes, `tools/build_guides.py` renders them, `tools/link_guides.py` points the ledger at the owning guide and `tools/validate_guides.py [--game SNAPSHOT]` checks everything, including the recipe amounts against the game registry. Guides are source-checked and carry headless screenshots; none is a recorded play session yet.
- **Next:** guides ranked 5 onward in the ledger (maps, installation, building, sailing, hunting, settings, troubleshooting); then the measured performance and memory study.

## Base-game publication slice — 11 October 2026

The public ledger and generated controls now cover the base game only. Optional gallery files were removed from the current tree; original assets and provenance remain in Git history at `493c52c`. The source audit remains `dd29d91`; publication filtering is not a newer game audit. Guide-gap ranks retain their original IDs.

## Wiki interface slice — 11 October 2026

The home now provides eight player categories, the four written guides and an
Atlas section. The original biome gallery lives at `atlas.html`; animal habitat
links and old biome bookmarks point there. Shared category navigation is rendered
from `tools/wiki_layout.py`. The four guide articles use a title, breadcrumb and
contents list. An offline search script contains 320 guide, base-game feature,
recipe and biome records. New files are explicitly allowlisted.

Static validation is available in `tools/validate_wiki.py`; actual desktop/mobile,
keyboard and file-URL browser inspection remains the parent integration gate.
No new game facts, recipes or screenshots were added.
