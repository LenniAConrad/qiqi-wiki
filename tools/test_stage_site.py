# SPDX-License-Identifier: GPL-3.0-only
"""Publication regressions: unknown files stay private regardless of extension."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

import stage_site
import validate_base_game


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.output = Path(self.temp.name) / 'site'
        for name in stage_site.PUBLIC_FILES:
            self.write(name)
        for name in stage_site.IMAGE_CATALOGS:
            self.write(name, '{}')
        self.write('images/scale/manifest.json', '{}')
        self.write('images/performance/component-costs.png')

    def write(self, name, content='fixture'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def test_explicit_public_files_and_images_only(self):
        private = [
            'AGENTS.md', 'WIKI_PLAN.md', 'README.md', 'VERIFICATION.md',
            'new-agent-notes.md', 'game.js', 'crates/core/src/main.rs',
            'target/release/voxelgame', 'saves/world.json', 'tools/helper.html',
            'data/new-internal-record.json', 'data/changelog.json', 'data/performance/raw-build.log',
            'data/performance/optimization/source-before.json',
            'data/performance/optimization/verification-20260928/verification-status.json',
            'data/performance/optimization/verification-20260928/native-production-delta.patch',
            'images/source.rs', 'images/debug.log', 'images/native.patch',
            'images/save.json', 'third_party/unreviewed.js',
            'images/unreviewed.webp', 'images/saves/thumbnail.png',
        ]
        for name in private:
            self.write(name)
        self.write('images/biome.webp')
        self.write('images/guides/capture.png')
        self.write('data/biomes.json', json.dumps({'image': 'images/biome.webp'}))
        self.write('data/guides.json', json.dumps({'image': 'images/guides/capture.png'}))
        count = stage_site.stage(self.output, self.root)
        published = {str(p.relative_to(self.output)) for p in self.output.rglob('*') if p.is_file()}
        self.assertEqual(published, set(stage_site.PUBLIC_FILES) | {
            'images/biome.webp', 'images/guides/capture.png', 'images/performance/component-costs.png'})
        self.assertEqual(count, len(published))
        for name in private:
            self.assertTrue((self.root / name).exists(), name)
            self.assertNotIn(name, published)

    def test_symlinked_assets_are_not_copied(self):
        secret = self.write('private/secret.webp')
        (self.root / 'images/leak.webp').symlink_to(secret)
        (self.root / 'images/linked').symlink_to(secret.parent, target_is_directory=True)
        stage_site.stage(self.output, self.root)
        self.assertFalse((self.output / 'images/leak.webp').exists())
        self.assertFalse((self.output / 'images/linked').exists())

    def test_catalogued_symlink_and_escaping_image_rejected(self):
        secret = self.write('private/secret.webp')
        (self.root / 'images/leak.webp').symlink_to(secret)
        self.write('data/biomes.json', '{"image": "images/leak.webp"}')
        with self.assertRaises(ValueError):
            stage_site.stage(self.output, self.root)
        self.write('data/biomes.json', '{"image": "images/../private/secret.webp"}')
        with self.assertRaises(ValueError):
            stage_site.stage(self.output, self.root)
        self.assertFalse(self.output.exists())

    def test_staged_markdown_links_cannot_point_into_private_archive(self):
        self.write('PERFORMANCE_OPTIMIZATION.md',
                   '[raw log](data/performance/private.log)\n'
                   '[summary](data/performance/optimization/public-verification.md)')
        self.write('data/performance/private.log')
        self.write('data/performance/optimization/public-verification.md',
                   '[report](../../../PERFORMANCE_OPTIMIZATION.md)')
        stage_site.stage(self.output, self.root)
        result = subprocess.run(
            [sys.executable, str(stage_site.ROOT / 'tools/validate_site_links.py'), '--root', str(self.output)],
            capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('PERFORMANCE_OPTIMIZATION.md: broken/non-portable reference data/performance/private.log', result.stderr)
        self.assertNotIn('broken/non-portable reference ../../../PERFORMANCE_OPTIMIZATION.md', result.stderr)

    def test_required_symlink_rejected_before_any_copy(self):
        source = self.root / 'index.html'
        source.unlink()
        source.symlink_to(self.write('private/source.html'))
        with self.assertRaises(ValueError):
            stage_site.stage(self.output, self.root)
        self.assertFalse(self.output.exists())

    def test_optional_content_regression_in_staged_artifact(self):
        stage_site.stage(self.output, self.root)
        validate_base_game.validate(self.output)
        path = self.output / 'data/features.json'
        for payload in ('{"status":"optional-pack"}', *validate_base_game.PACK_IDS):
            with self.subTest(payload=payload):
                path.write_text(payload)
                with self.assertRaisesRegex(ValueError, 'pack ID'):
                    validate_base_game.validate(self.output)
        path.write_text('{}')
        page = self.output / 'index.html'
        for payload in ('<nav><a href="mods.html">Mods</a></nav>',
                        '<nav><a href="#future">Mods</a></nav>',
                        '<nav><a href="villages.html">Village</a></nav>'):
            page.write_text(payload)
            with self.assertRaisesRegex(ValueError, 'navigation'):
                validate_base_game.validate(self.output)
        page.write_text('<nav><a href="guide-crafting.html">Crafting</a></nav><p>Open the Pack tab.</p>')
        validate_base_game.validate(self.output)

    def test_nonempty_output_and_source_directory_rejected(self):
        self.output.mkdir()
        receipt = self.output / 'owner.txt'
        receipt.write_text('keep')
        with self.assertRaises(SystemExit):
            stage_site.stage(self.output, self.root)
        self.assertEqual(receipt.read_text(), 'keep')
        with self.assertRaises(ValueError):
            stage_site.stage(self.root / 'images/staged', self.root)

    def test_real_archive_excluded_and_preserved(self):
        patch = stage_site.ROOT / 'data/performance/optimization/verification-20260928/native-production-delta.patch'
        before = patch.read_bytes()
        stage_site.stage(self.output)
        self.assertEqual(patch.read_bytes(), before)
        self.assertTrue(list((stage_site.ROOT / 'data').rglob('*.log')))
        self.assertFalse(list(self.output.rglob('*.log')))
        self.assertFalse(list(self.output.rglob('*.patch')))
        self.assertFalse((self.output / 'data/performance/optimization/verification-20260928').exists())
        for name in ('AGENTS.md', 'README.md', 'WIKI_PLAN.md', 'VERIFICATION.md',
                     'tools', 'crates', 'target', 'saves', '.git', '.github', '.cache'):
            self.assertFalse((self.output / name).exists(), name)


if __name__ == '__main__':
    unittest.main()
