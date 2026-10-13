# SPDX-License-Identifier: GPL-3.0-only
"""Image refresh and publication failures must be caught before Pages deploys."""
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image
import build_gallery_previews as previews
from image_variants import digest
from validate_site_links import References


class GalleryPreviews(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'data').mkdir()
        self.names = {'biomes': 'images/meadow.webp', 'animals': 'images/animals/ant.webp',
                      'guides': 'images/guides/crafting.webp'}
        for kind, name in self.names.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new('RGB', previews.PROFILES[kind]['originalSize'], (35, 90, 50)).save(path)
        (self.root / 'data/biomes.json').write_text(json.dumps({'biomes': [{'image': self.names['biomes']}]}))
        (self.root / 'data/animals.json').write_text(json.dumps({'animals': [{'views': [
            {'image': self.names['animals'], 'pose': 'idle', 'angle': 'three-quarter'}]}]}))
        (self.root / 'data/guides.json').write_text(json.dumps({'guides': [{'blocks': [
            {'t': 'figure', 'src': self.names['guides']}]}]}))
        self.originals = {name: digest(self.root / name) for name in self.names.values()}
        self.manifest = previews.generate(self.root)

    def test_refresh_preserves_originals_and_requires_new_capture_receipts(self):
        previews.validate(self.root)
        self.assertEqual(self.originals, {name: digest(self.root / name) for name in self.names.values()})
        source = self.root / self.names['biomes']
        Image.new('RGB', (960, 540), (90, 30, 50)).save(source)
        with self.assertRaisesRegex(AssertionError, 'Stale source'):
            previews.validate(self.root)

    def test_missing_or_corrupt_derivative_cannot_ship(self):
        target = self.root / self.manifest['images'][0]['variants'][0]['path']
        target.write_bytes(b'broken')
        with self.assertRaisesRegex(AssertionError, 'Preview bytes differ'):
            previews.validate(self.root)
        target.unlink()
        with self.assertRaises(FileNotFoundError):
            previews.validate(self.root)

    def test_html_and_script_regeneration_follow_the_collection(self):
        attrs = previews.attributes(self.names['animals'], 'animals', '42vw', minimum=192)
        parser = References()
        parser.feed('<img ' + attrs + '>')
        self.assertEqual(len(parser.refs), 4)  # fallback + 192/320/native candidates
        self.assertTrue(all((self.root / path).is_file() for path in parser.refs))
        (self.root / previews.SCRIPT).write_text('stale')
        with self.assertRaisesRegex(AssertionError, 'Stale responsive-image script'):
            previews.validate(self.root)

    def test_static_links_include_every_responsive_candidate(self):
        parser = References()
        parser.feed('<img src="small.webp" srcset="small.webp 480w, missing.webp 960w">')
        self.assertIn('missing.webp', parser.refs)

    def test_higher_quality_cannot_make_a_preview_heavier_than_its_source(self):
        variant = self.manifest['images'][0]['variants'][0]
        target = self.root / variant['path']
        Image.effect_noise((variant['width'], variant['height']), 80).save(target, 'WEBP', quality=95)
        variant.update(bytes=target.stat().st_size, sha256=digest(target))
        (self.root / previews.MANIFEST).write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(AssertionError, 'not smaller than its original'):
            previews.validate(self.root)


if __name__ == '__main__':
    unittest.main()
