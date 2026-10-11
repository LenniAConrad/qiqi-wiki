# SPDX-License-Identifier: GPL-3.0-only
"""Registry parser and evidence boundary regressions for the block reference."""
import copy
import json
import unittest

import build_blocks
import build_wiki
import validate_blocks
from validate_wiki import Page


class RegistryParsing(unittest.TestCase):
    def test_multiline_docs_gaps_colours_and_evidence(self):
        rows = build_blocks.parse_table('''// Header
blocks! {
    /// Pale stone.
    /// Found on shores.
    STONE = 3, "Slate", [0.4, 0.43, 0.47];
    // Preserve gaps in saved identifiers.
    /// Empty space.
    AIR = 0, "Air", [0.0, 0.0, 0.0];
}''')
        self.assertEqual([r['id'] for r in rows], [3, 0])
        self.assertEqual(rows[0]['sourceDescription'], 'Pale stone. Found on shores.')
        self.assertEqual(rows[0]['color'], [0.4, 0.43, 0.47])
        self.assertEqual(rows[0]['evidence'], build_blocks.TABLE + ':5')

    def test_unknown_syntax_missing_docs_duplicate_ids_and_bad_colour_fail(self):
        for body in ('STONE: 3;', 'STONE = 3, "Slate", [0.4, 0.4, 0.4];',
                     '/// Rock\nSTONE = 3, "Slate", [1.4, 0.4, 0.4];',
                     '/// Rock\nSTONE = 3, "Slate", [0.4, 0.4, 0.4];\n'
                     '/// Air\nAIR = 3, "Air", [0.0, 0.0, 0.0];'):
            with self.subTest(body=body), self.assertRaises(ValueError):
                build_blocks.parse_table('blocks! {\n' + body + '\n}')


class PublishedBlocks(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((build_blocks.ROOT / 'data/blocks.json').read_text())
        self.recipes = json.loads((build_blocks.ROOT / 'data/recipes.json').read_text())

    def test_every_reviewed_block_has_an_anchor_and_search_record(self):
        validate_blocks.validate(self.data, self.recipes)
        page = Page(build_blocks.render(self.data))
        records = [r for r in build_wiki.search_records() if r['kind'] == 'Block']
        self.assertEqual(len(records), self.data['catalogCount'])
        self.assertEqual({r['href'] for r in records},
                         {'blocks.html#' + b['anchor'] for b in self.data['blocks']})
        self.assertTrue(page.breadcrumb and page.contents)

    def test_optional_id_or_unsupported_recipe_is_rejected(self):
        for field, value in [('symbol', 'voxelgame_wwii:pack'), ('recipes', ['Invented drop'])]:
            data = copy.deepcopy(self.data)
            data['blocks'][0][field] = value
            with self.subTest(field=field), self.assertRaises(AssertionError):
                validate_blocks.validate(data, self.recipes)

    def test_unknown_acquisition_has_no_visible_field(self):
        html = build_blocks.render(self.data)
        self.assertIn('<td data-label="How to get it"></td>', html)
        self.assertEqual(html.count('Creative only</td>'), 2)


if __name__ == '__main__':
    unittest.main()
