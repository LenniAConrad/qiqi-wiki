#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Unit tests for the guide builder, the ledger linker and the guide validator."""

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_guides  # noqa: E402
import link_guides  # noqa: E402
import validate_guides  # noqa: E402


def ledger():
    return {
        "game": {"commit": "a" * 40, "commitDate": "2026-10-10T22:47:55+08:00", "branch": "main"},
        "statuses": [{"key": "available", "label": "Available", "description": "d"},
                     {"key": "planned", "label": "Planned", "description": "d"}],
        "areas": [{"key": "basics", "label": "Basics", "description": "Area"}],
        "features": [
            {"id": "pack-panel", "area": "basics", "name": "Pack", "status": "available", "modes": ["survival"],
             "summary": "s", "controls": [["E", "Open the pack"]], "evidence": ["a.rs:1"],
             "guide": {"state": "none", "next": "Crafting"}},
            {"id": "fire", "area": "basics", "name": "Fire", "status": "planned", "summary": "s",
             "evidence": ["search: none"], "controls": [["G", "Light it"]]},
        ],
        "guideGaps": [], "readiness": {},
    }


def recipes():
    return {
        "schema": 1, "piecesPerBlock": 8,
        "sections": [{"key": "timber", "label": "Timber"}, {"key": "fire", "label": "Fire & food"}],
        "recipes": [
            {"name": "Split boards", "section": "timber", "output": "Boards", "quantity": 4,
             "inputs": [["Log", 1]], "evidence": "crates/a.rs:1-2"},
            {"name": "Burn <charcoal>", "section": "fire", "output": "Charcoal", "quantity": 2,
             "inputs": [["Boards", 4]], "evidence": "crates/a.rs:3-4", "notes": "See {{pack-panel}}."},
        ],
    }


def guides():
    return {
        "schema": 1, "title": "G", "description": "D", "headline": "H", "lead": "L", "comingLead": "C",
        "updated": "2026-10-11",
        "guides": [{
            "id": "start", "page": "guide-start.html", "number": 1, "kicker": "K", "title": "Start",
            "headline": "Start", "summary": "S", "lead": "L", "readTime": "1 min", "audience": "All",
            "updated": "2026-10-11", "state": "complete", "covers": ["pack-panel"], "owns": ["pack-panel"],
            "verification": {"method": "Read.", "limits": "Not play-tested."},
            "sections": [{"id": "one", "title": "One", "blocks": [
                {"t": "p", "text": "Press [[E]] for the {{pack-panel}} and **bold** <b>."}]}],
        }],
    }


class InlineMarkup(unittest.TestCase):
    def test_markup_escapes_html_and_expands_links(self):
        ctx = build_guides.Context(guides(), ledger(), recipes())
        html = ctx.inline("Press [[E]] for {{pack-panel}} and **bold** <b>.")
        self.assertIn("<kbd>E</kbd>", html)
        self.assertIn('<a href="features.html#f-pack-panel">Pack</a>', html)
        self.assertIn("<strong>bold</strong>", html)
        self.assertIn("&lt;b&gt;", html)

    def test_unknown_feature_link_fails_the_build(self):
        ctx = build_guides.Context(guides(), ledger(), recipes())
        with self.assertRaises(KeyError):
            ctx.inline("{{no-such-feature}}")

    def test_guide_link_uses_the_guide_title(self):
        ctx = build_guides.Context(guides(), ledger(), recipes())
        self.assertIn('<a href="guide-start.html">Start</a>', ctx.inline("{{guide:start}}"))


class Rendering(unittest.TestCase):
    def test_pages_are_deterministic_and_complete(self):
        first = build_guides.render_all(guides(), ledger(), recipes())
        self.assertEqual(first, build_guides.render_all(guides(), ledger(), recipes()))
        self.assertEqual(set(first), {"guides.html", "guide-start.html"})
        self.assertIn('<a href="guides.html" aria-current="true">All guides</a>', first["guide-start.html"])

    def test_recipe_tables_filter_by_name_and_escape(self):
        ctx = build_guides.Context(guides(), ledger(), recipes())
        everything = build_guides.recipe_tables(ctx, {"t": "recipes"})
        self.assertIn("Burn &lt;charcoal&gt;", everything)
        only = build_guides.recipe_tables(ctx, {"t": "recipes", "names": ["Split boards"]})
        self.assertIn("Split boards", only)
        self.assertNotIn("Burn", only)

    def test_controls_reference_labels_non_available_features(self):
        ctx = build_guides.Context(guides(), ledger(), recipes())
        html = build_guides.controls_reference(ctx, {"t": "controls-all"})
        self.assertIn("<kbd>E</kbd>", html)
        self.assertIn('class="status status-planned"', html)
        self.assertIn("2 controls listed", html)


class Linking(unittest.TestCase):
    def test_link_sets_state_page_and_label_and_is_idempotent(self):
        data, board = guides(), ledger()
        self.assertEqual(link_guides.link(data, board), 1)
        self.assertEqual(board["features"][0]["guide"],
                         {"state": "complete", "page": "guide-start.html", "label": "Start"})
        self.assertEqual(link_guides.link(data, board), 0)

    def test_partial_keeps_the_next_guide_title(self):
        data, board = guides(), ledger()
        data["guides"][0]["partial"] = ["pack-panel"]
        link_guides.link(data, board)
        self.assertEqual(board["features"][0]["guide"]["next"], "Crafting")
        self.assertEqual(board["features"][0]["guide"]["state"], "partial")


class Validation(unittest.TestCase):
    def linked(self):
        data, board = guides(), ledger()
        link_guides.link(data, board)
        return data, board

    def test_valid_guide_passes(self):
        data, board = self.linked()
        validate_guides.validate_guides(data, board, recipes())

    def test_planned_feature_outside_a_planned_note_is_rejected(self):
        data, board = self.linked()
        data["guides"][0]["covers"].append("fire")
        data["guides"][0]["sections"][0]["blocks"].append({"t": "p", "text": "Light the {{fire}}."})
        with self.assertRaisesRegex(ValueError, "planned feature fire"):
            validate_guides.validate_guides(data, board, recipes())

    def test_planned_feature_inside_a_planned_note_is_allowed(self):
        data, board = self.linked()
        data["guides"][0]["sections"][0]["blocks"].append(
            {"t": "note", "kind": "planned", "text": "{{fire}} is planned."})
        validate_guides.validate_guides(data, board, recipes())

    def test_planned_feature_cannot_be_owned(self):
        data, board = self.linked()
        data["guides"][0]["covers"].append("fire")
        data["guides"][0]["owns"].append("fire")
        with self.assertRaisesRegex(ValueError, "cannot be owned"):
            validate_guides.validate_guides(data, board, recipes())

    def test_unlinked_ledger_entry_is_rejected(self):
        data, board = guides(), ledger()
        with self.assertRaisesRegex(ValueError, "not linked"):
            validate_guides.validate_guides(data, board, recipes())

    def test_two_guides_cannot_own_one_feature(self):
        data, board = self.linked()
        second = copy.deepcopy(data["guides"][0])
        second.update(id="second", page="guide-second.html", number=2)
        data["guides"].append(second)
        with self.assertRaisesRegex(ValueError, "also owned"):
            validate_guides.validate_guides(data, board, recipes())

    def test_verification_must_state_play_testing(self):
        data, board = self.linked()
        data["guides"][0]["verification"]["limits"] = "Checked."
        with self.assertRaisesRegex(ValueError, "play-tested"):
            validate_guides.validate_guides(data, board, recipes())

    def test_recipe_amounts_must_be_positive_integers(self):
        broken = recipes()
        broken["recipes"][0]["quantity"] = 0
        with self.assertRaisesRegex(ValueError, "quantity"):
            validate_guides.validate_recipes(broken)


class Registry(unittest.TestCase):
    SOURCE = '''
pub static RECIPES: [Recipe; 3] = [
    Recipe {
        name: "Split boards",
        description: "Splits a log",
        category: RecipeCategory::Timber,
        ingredients: &[(WOOD, 1)],
        outputs: &[(PLANKS, 4)],
    },
    Recipe {
        name: "Blow flasks",
        category: RecipeCategory::Fire,
        ingredients: &[(GLASS, BLOCK), (Item::CHARCOAL, 1)],
        outputs: &[(Item::EMPTY_FLASK, 2)],
    },
    Recipe {
        name: "Dress chalk",
        category: RecipeCategory::Materials,
        ingredients: &[(Item(Block::CHALK.0 as u16), BLOCK / 2), (SAND, 3 * BLOCK)],
        outputs: &[(Item(Block::CHALK_BRICKS.0 as u16), BLOCK)],
    },
];
'''

    def test_amounts_resolve_block_expressions_and_nested_parentheses(self):
        entries = validate_guides.parse_registry(self.SOURCE)
        self.assertEqual([entry[0] for entry in entries], ["Split boards", "Blow flasks", "Dress chalk"])
        self.assertEqual(entries[1][2:], ([8, 1], [2]))
        self.assertEqual(entries[2][2:], ([4, 24], [8]))


if __name__ == "__main__":
    unittest.main()
