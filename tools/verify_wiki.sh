#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/validate.py
python3 tools/validate_animals.py
python3 tools/validate_islands.py
python3 tools/validate_villages.py
python3 tools/validate_site_links.py
for script in ./*.js data/*.js; do node --check "$script"; done
