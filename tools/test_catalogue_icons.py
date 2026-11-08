# SPDX-License-Identifier: GPL-3.0-only
import json
from pathlib import Path
import tempfile
import unittest

import build_catalogue_icons as icons
from catalogue_icons import MANIFEST, icon_html


def step(pointer, status, buttons=None):
    request = {'command': 'step', 'frames': 1, 'pointer': pointer}
    if buttons:
        request['buttons'] = buttons
    return {'request': request, 'response': {'ok': True, 'result': {'status': status}}}


class CatalogueIconTests(unittest.TestCase):
    def test_slots_name_only_clicks_with_a_new_catalogue_status(self):
        rows = [step(icons.PARK, 'Textures loaded'),
                {'request': {'command': 'capture_frame', 'name': 'page1.png'}, 'response': {'ok': True, 'result': {}}}]
        for slot, status in enumerate(['Dirt selected from creative catalog', 'Arrow taken from creative catalog',
                                       'Arrow taken from creative catalog', 'Furniture plan selected | RMB place',
                                       'Stone sword equipped from creative catalog']):
            point = icons.slot_centre(slot)
            rows += [step(point, rows[-1]['response']['result'].get('status'), ['primary']), step(point, status)]
        rows += [step(icons.NEXT_PAGE, 'Creative items page 2 / 4', ['primary'])]
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / 'transcript.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
            found = list(icons.slots(Path(folder)))
        self.assertEqual([label for _, _, label in found], ['Dirt', 'Arrow', None, None, 'Stone sword'])
        self.assertEqual([slot for _, slot, _ in found], [0, 1, 2, 3, 4])

    def test_replays_stay_under_the_session_command_limit(self):
        for pages in ((1, 2), (3, 4)):
            self.assertLess(len(icons.replay(pages)['commands']), 512)

    def test_icon_markup_uses_sprite_grid_and_hides_from_readers(self):
        name, index = next(iter(MANIFEST['icons'].items()))
        html = icon_html(name, 'small')
        self.assertIn(f'--x:{index % 16};--y:{index // 16}', html)
        self.assertIn('class="item-icon small"', html)
        self.assertIn('aria-hidden="true"', html)
        self.assertEqual(icon_html('Not a catalogue entry'), '')


if __name__ == '__main__':
    unittest.main()
