#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Point ledger features at the guides that own them.

data/guides.json lists, per guide, the features it owns and which of them it
covers only partly. This rewrites the guide state, page and label of exactly
those features in data/features.json and leaves every other field alone. Run it
after changing ownership, then python3 tools/build_features.py and
python3 tools/build_guides.py; tools/validate_guides.py checks the result.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def link(guides, ledger):
    """Update ledger in place and return how many features changed."""
    features = {feature["id"]: feature for feature in ledger["features"]}
    changed = 0
    for guide in guides["guides"]:
        for feature_id in guide.get("owns", []):
            feature = features[feature_id]
            old = feature.get("guide", {})
            state = "partial" if feature_id in guide.get("partial", []) else "complete"
            new = {"state": state, "page": guide["page"], "label": guide["title"]}
            if state == "partial" and old.get("next"):
                new["next"] = old["next"]
            if old != new:
                feature["guide"] = new
                changed += 1
    return changed


def main():
    guides = json.loads((ROOT / "data" / "guides.json").read_text(encoding="utf-8"))
    path = ROOT / "data" / "features.json"
    ledger = json.loads(path.read_text(encoding="utf-8"))
    changed = link(guides, ledger)
    path.write_text(json.dumps(ledger, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Linked {changed} features to their guides")


if __name__ == "__main__":
    main()
