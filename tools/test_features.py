#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Unit tests for the feature-ledger builder and validator rules."""

import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_features  # noqa: E402
import validate_features  # noqa: E402


def ledger():
    statuses = [{"key": key, "label": key.title(), "description": f"{key} description"}
                for key in validate_features.STATUSES]
    return {
        "schema": 1, "title": "T", "description": "D", "headline": "A<br><em>B</em>", "lead": "L",
        "legendLead": "Legend", "gapsLead": "Gaps", "docNotesLead": "Notes", "audited": "2026-10-11",
        "game": {"commit": "a" * 40, "commitDate": "2026-10-10T22:47:55+08:00", "branch": "main",
                 "packageVersion": "0.1.0", "newWorldGeneration": 10},
        "method": [{"title": "M", "text": "Method"}],
        "statuses": statuses,
        "guideStates": [{"key": key, "label": key} for key in validate_features.GUIDE_STATES],
        "readiness": {key: key for key in validate_features.READINESS},
        "areas": [{"key": "basics", "label": "Basics", "description": "Area"}],
        "features": [
            {"id": "pack-panel", "area": "basics", "name": "Pack", "status": "available", "modes": ["survival"],
             "summary": "Open your pack.", "controls": [["E", "Open the pack"]],
             "evidence": ["src/input.rs:12 — E toggles the pack"], "guide": {"state": "none", "next": "Start"}},
            {"id": "lab", "area": "basics", "name": "Lab", "status": "partial",
             "summary": "Limited.", "evidence": ["src/lab.rs:1"]},
            {"id": "fire", "area": "basics", "name": "Fire", "status": "planned", "summary": "Not yet.",
             "evidence": ["search: no fire blocks"], "backlog": ["VOX-OWNER-FIRE"]},
            {"id": "atlas", "area": "basics", "name": "Animals", "status": "available", "summary": "Atlas.",
             "evidence": ["src/animals.rs:3-4"], "guide": {"state": "atlas", "page": "animals.html", "label": "Atlas"}},
        ],
        "guideGaps": [{"rank": 1, "title": "Start", "covers": ["pack-panel"], "readiness": "ready", "why": "Why."}],
        "docNotes": [{"topic": "Packs", "detail": "Count differs.", "evidence": ["README.md:2"]}],
    }


class LedgerRules(unittest.TestCase):
    def assertRejected(self, mutate, fragment):
        data = ledger()
        mutate(data)
        with self.assertRaisesRegex(ValueError, fragment):
            validate_features.validate_ledger(data)

    def test_valid_ledger_renders_every_feature(self):
        data = ledger()
        self.assertEqual(len(validate_features.validate_ledger(data)), 4)
        page = build_features.render_page(data)
        for feature in data["features"]:
            self.assertIn(f'id="f-{feature["id"]}"', page)
        self.assertIn('<a href="features.html">Coverage and sources</a>', page)
        self.assertEqual(page, build_features.render_page(copy.deepcopy(data)), "rendering is deterministic")

    def test_rendered_text_is_escaped(self):
        data = ledger()
        data["features"][0]["summary"] = 'Use <b> & "quotes"'
        page = build_features.render_page(data)
        self.assertIn("Use &lt;b&gt; &amp;", page)
        self.assertNotIn("Use <b>", page)

    def test_build_filters_optional_source_rows(self):
        data = ledger()
        data['features'].append({'id': 'optional-lab', 'area': 'basics', 'name': 'Lab',
                                 'status': 'optional-pack', 'pack': 'Lab',
                                 'summary': 'circuits:pack', 'controls': [['L', 'Open lab']],
                                 'evidence': ['mods/lab.rs:1']})
        page = build_features.render_page(data)
        self.assertNotIn('optional-pack', page)
        self.assertNotIn('circuits:pack', page)
        self.assertNotIn('f-optional-lab', page)

    def test_status_and_pack_rules(self):
        self.assertRejected(lambda d: d["features"][0].update(status="done"), "unknown status")
        self.assertRejected(lambda d: d["features"][1].update(status="optional-pack"), "unknown status")
        self.assertRejected(lambda d: d["features"][0].update(pack="Lab"), "cannot name a content pack")

    def test_planned_features_stay_honest(self):
        self.assertRejected(lambda d: d["features"][2].pop("backlog"), "cite the request")
        self.assertRejected(lambda d: d["features"][2].update(guide={"state": "atlas", "page": "animals.html",
                                                                     "label": "A"}), "cannot have a guide")

    def test_identity_evidence_and_links(self):
        self.assertRejected(lambda d: d["features"][1].update(id="pack-panel"), "duplicate id")
        self.assertRejected(lambda d: d["features"][0].update(evidence=[]), "evidence required")
        self.assertRejected(lambda d: d["features"][0].update(evidence=["/etc/passwd:1"]), "evidence must be")
        self.assertRejected(lambda d: d["features"][0].update(evidence=["src/../../secret.rs:1"]), "relative")
        self.assertRejected(lambda d: d["features"][0].update(evidence=["src/a.rs:9-3"]), "reversed")
        self.assertRejected(lambda d: d["features"][3]["guide"].update(page="missing.html"), "missing")
        self.assertRejected(lambda d: d["features"][0]["guide"].update(state="complete"), "without a page")
        self.assertRejected(lambda d: d.update(headline="<script>x</script>"), "headline")

    def test_gaps_and_areas(self):
        self.assertRejected(lambda d: d["guideGaps"][0].update(rank=0), "ranks")
        self.assertRejected(lambda d: d["guideGaps"][0].update(covers=["nope"]), "unknown feature")
        self.assertRejected(lambda d: d["areas"].append({"key": "empty", "label": "E", "description": "D"}),
                            "no features")
        self.assertRejected(lambda d: d["game"].update(commitDate="2026-10-12T01:00:00+08:00"), "postdate")

    def test_game_snapshot_evidence(self):
        data = ledger()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, lines in (("src/input.rs", 20), ("src/lab.rs", 1), ("src/animals.rs", 4),
                                ("README.md", 2)):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text("x\n" * (lines - 1) + "x")
            (root / "SNAPSHOT_COMMIT").write_text("a" * 40 + "\n")
            self.assertEqual(validate_features.check_game(data, root), 4)
            data["features"][0]["evidence"] = ["src/input.rs:21"]
            with self.assertRaisesRegex(ValueError, "outside"):
                validate_features.check_game(data, root)
            (root / "SNAPSHOT_COMMIT").write_text("b" * 40)
            with self.assertRaisesRegex(ValueError, "snapshot commit"):
                validate_features.check_game(ledger(), root)


if __name__ == "__main__":
    unittest.main()
