#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/validate.py
python3 tools/validate_animals.py
python3 tools/validate_islands.py
python3 tools/build_island_thumbnails.py --check
python3 tools/build_gallery_previews.py --check
python3 -m unittest discover -s tools -p 'test_*.py'
python3 tools/validate_features.py
python3 tools/validate_guides.py
python3 tools/validate_blocks.py
python3 tools/validate_mobs.py
python3 tools/validate_wiki.py
python3 tools/validate_site_links.py
for script in ./*.js data/*.js; do node --check "$script"; done
# Links must also resolve in the exact file set that GitHub Pages publishes.
staged=.cache/site-check
rm -rf "$staged"
python3 tools/stage_site.py "$staged"
python3 tools/validate_site_links.py --root "$staged"
python3 tools/validate_base_game.py "$staged"
rm -rf "$staged"
