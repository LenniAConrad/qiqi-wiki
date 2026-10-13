# SPDX-License-Identifier: GPL-3.0-only
"""Refresh regressions: a new capture or missing thumbnail cannot ship stale data."""
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image
import build_island_thumbnails as thumbnails


class ThumbnailRefresh(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'data').mkdir()
        (self.root / 'images/islands').mkdir(parents=True)
        self.source = self.root / 'images/islands/example--map.webp'
        Image.new('RGB', (1200, 1200), (50, 90, 30)).save(self.source)
        (self.root / 'data/islands.json').write_text(json.dumps({
            'islands': [{'views': [{'type': 'map', 'image': 'images/islands/example--map.webp'}]}]}))
        self.manifest = thumbnails.generate(self.root)

    def test_changed_capture_requires_refresh(self):
        thumbnails.validate(self.root)
        Image.new('RGB', (1200, 1200), (30, 50, 90)).save(self.source)
        with self.assertRaisesRegex(AssertionError, 'Stale source'):
            thumbnails.validate(self.root)

    def test_missing_responsive_file_fails_validation(self):
        item = self.manifest['images'][0]['variants'][1]
        (self.root / item['path']).unlink()
        with self.assertRaises(FileNotFoundError):
            thumbnails.validate(self.root)


if __name__ == '__main__':
    unittest.main()
