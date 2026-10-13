# SPDX-License-Identifier: GPL-3.0-only
"""Capture exports must include committed binary assets without touching game WIP."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from freeze_media_source import freeze, git, verify_snapshot
from build_animals import ROOT, capture_receipts, sha


class MediaSnapshot(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / 'game'
        self.game.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.game)], check=True)
        git(self.game, 'config', 'user.email', 'fixture@example.invalid')
        git(self.game, 'config', 'user.name', 'Fixture')
        (self.game / 'Cargo.lock').write_text('committed lock\n')
        (self.game / 'coat.png').write_bytes(b'\x00\xffasset\x00')
        git(self.game, 'add', '.')
        git(self.game, 'commit', '-qm', 'fixture')

    def test_commit_export_preserves_wip_and_captures_binary_and_lock(self):
        (self.game / 'coat.png').write_bytes(b'owner WIP')
        (self.game / 'untracked.txt').write_text('keep me')
        before = git(self.game, 'status', '--porcelain')
        output = self.root / 'capture'
        manifest = freeze(self.game, 'HEAD', output)
        self.assertEqual((output / 'source/coat.png').read_bytes(), b'\x00\xffasset\x00')
        self.assertEqual({row['path'] for row in manifest['files']}, {'coat.png', 'Cargo.lock'})
        self.assertEqual(git(self.game, 'status', '--porcelain'), before)
        self.assertEqual((self.game / 'coat.png').read_bytes(), b'owner WIP')
        self.assertEqual(verify_snapshot(output / 'source', output / 'source-manifest.json'), manifest)
        (output / 'source/coat.png').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Changed or missing'):
            verify_snapshot(output / 'source', output / 'source-manifest.json')

    def test_existing_capture_and_game_checkout_are_never_overwritten(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            freeze(self.game, 'HEAD', self.game / 'capture')
        output = self.root / 'capture'
        output.mkdir()
        with self.assertRaises(FileExistsError):
            freeze(self.game, 'HEAD', output)

    def test_export_ignored_assets_cannot_be_called_a_complete_snapshot(self):
        (self.game / '.gitattributes').write_text('coat.png export-ignore\n')
        git(self.game, 'add', '.')
        git(self.game, 'commit', '-qm', 'ignore fixture asset')
        with self.assertRaisesRegex(ValueError, 'full tracked tree'):
            freeze(self.game, 'HEAD', self.root / 'incomplete')

    def test_manifest_paths_cannot_escape_capture(self):
        output = self.root / 'capture'
        freeze(self.game, 'HEAD', output)
        path = output / 'source-manifest.json'
        manifest = json.loads(path.read_text())
        manifest['files'][0]['path'] = '../outside'
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'Invalid or duplicate'):
            verify_snapshot(output / 'source', path)

    def render_fixture(self):
        game_tools = self.game / 'tools'
        game_tools.mkdir()
        (game_tools / 'render_creature_gallery.py').write_text('# renderer fixture\n')
        git(self.game, 'add', '.')
        git(self.game, 'commit', '-qm', 'renderer fixture')
        output = self.root / 'capture'
        snapshot = freeze(self.game, 'HEAD', output)
        meshes, renders = output / 'meshes', output / 'renders'
        meshes.mkdir()
        renders.mkdir()
        (meshes / 'coat.ppm').write_bytes(b'texture fixture')
        (renders / 'swan.png').write_bytes(b'render fixture')
        path = output / 'render-receipt.json'
        receipt = {'sourceCommit': snapshot['commit'],
                   'sourceManifestSha256': sha(output / 'source-manifest.json'),
                   'wikiRenderScriptSha256': sha(ROOT / 'tools/render_animals.py'),
                   'gameRenderScriptSha256': sha(output / 'source/tools/render_creature_gallery.py'),
                   'meshHashes': {'coat.ppm': sha(meshes / 'coat.ppm')},
                   'renderHashes': {'swan.png': sha(renders / 'swan.png')},
                   'blenderVersion': 'fixture', 'engine': 'fixture', 'resolution': [512, 512],
                   'renderSettings': {}, 'exporterSha256': 'a' * 64,
                   'captureDriverSha256': 'c' * 64}
        path.write_text(json.dumps(receipt))
        return output, meshes, renders, path, receipt

    def test_render_run_must_match_its_snapshot_and_unchanged_output(self):
        output, meshes, renders, path, receipt = self.render_fixture()
        args = (output / 'source', meshes, renders, output / 'source-manifest.json', path)
        capture, _ = capture_receipts(*args)
        self.assertEqual(capture['gameCommit'], receipt['sourceCommit'])
        (renders / 'swan.png').write_bytes(b'different image')
        with self.assertRaisesRegex(ValueError, 'Changed or missing render'):
            capture_receipts(*args)
        receipt['sourceCommit'] = 'b' * 40
        path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, 'does not match'):
            capture_receipts(*args)

    def test_render_run_must_record_material_inputs(self):
        output, meshes, renders, path, receipt = self.render_fixture()
        receipt['meshHashes'] = {}
        path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, 'missing material'):
            capture_receipts(output / 'source', meshes, renders,
                             output / 'source-manifest.json', path)


if __name__ == '__main__':
    unittest.main()
