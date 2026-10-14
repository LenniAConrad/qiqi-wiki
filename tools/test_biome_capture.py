# SPDX-License-Identifier: GPL-3.0-only
"""Private orchestration fixtures, never native gameplay or visual-review receipts."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

import build_biome_capture
import capture_biomes
from biome_capture_evidence import read, sha, write
import refresh_survey
import update_provenance
from validate import validate_catalog

ROOT = Path(__file__).resolve().parents[1]


class BiomeCapture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='biome-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.game = self.base / 'source'
        self.manifest = self.base / 'source-manifest.json'
        files = {'Cargo.lock': '# fixture lock\n', 'Cargo.toml': '# fixture manifest\n',
                 refresh_survey.GENERATOR: 'pub enum GeneratorVersion {\n    Current = 10,\n}\n',
                 'tools/game_debug.py': '# test adapter injected; not an executable\n',
                 'crates/voxelgame-core/src/world/block.rs': '// fixture block\n',
                 'crates/voxelgame-core/src/world/generator/habitats.rs': '// fixture habitats\n',
                 'crates/voxelgame-render/src/lib.rs': '// fixture renderer\n'}
        for name, content in files.items():
            path = self.game / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        write(self.manifest, {'commit': 'a' * 40, 'tree': 'b' * 40,
              'method': 'TEST FIXTURE ONLY: no native source/build/capture claim.',
              'files': [{'path': name, 'bytes': (self.game / name).stat().st_size,
                         'sha256': sha(self.game / name)} for name in files]})
        self.survey = read(ROOT / 'data/survey.json')
        self.survey['generatorVersion'] = 10  # Old sample counts reused ONLY as orchestration fixtures.
        self.survey_dir = self.base / 'survey'
        self.build_dir = self.base / 'build'
        self.build_manifest = self.build_dir / 'build-manifest.json'
        self.output = self.base / 'captures'
        self.public = self.base / 'wiki'
        (self.public / 'data').mkdir(parents=True)
        (self.public / 'images').mkdir()
        for name in update_provenance.CATALOG_INPUTS:
            shutil.copy2(ROOT / name, self.public / name)
        self.fail_build = False
        self.after_build = lambda: None
        self.after_frame = lambda: None
        self.closed = []
        self.native_count = 0
        self.native_exit = 0
        self.native_state_change = lambda state: None
        with patch.object(refresh_survey.subprocess, 'run', side_effect=self.fake_command):
            refresh_survey.refresh(self.game, self.manifest, self.survey_dir)
            build_biome_capture.build(self.game, self.manifest, self.build_dir)
        self.initial_files = {str(p.relative_to(self.public)): p.read_bytes()
                              for p in self.public.rglob('*') if p.is_file()}

    def fake_command(self, command, **kwargs):
        binary = command[command.index('--bin') + 1]
        target = Path(kwargs['env']['CARGO_TARGET_DIR']) / 'release' / binary
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'Orchestration fixture, NOT a native executable.\n')
        if binary == 'voxelgame':
            if self.fail_build:
                raise subprocess.CalledProcessError(124, command)
            self.after_build()
        elif binary == 'qiqi-biome-survey':
            write(Path(command[-1]), self.survey)
        else:
            write(Path(command[-1]), {r['id']: {'height': r['height'], 'water': r['water'],
                                             'cameraGround': -1000000}
                                     for r in self.survey['biomes']})
        return subprocess.CompletedProcess(command, 0)

    def factory(self, binary, evidence, timeout):
        owner = self
        owner.native_count += 1

        class FixtureAdapter:
            def __init__(self):
                self.process = SimpleNamespace(returncode=None)
                self.commands = []
                self.state = {'generator_version': 10, 'seed': None, 'mods': [],
                              'save_writes': False, 'world': {'edited_voxels': 0},
                              'renderer': {'detail_clip_radius_metres': 64,
                                           'detail_clip_target_metres': 64}}
                metadata = {'binary_sha256': sha(binary), 'fixture': 'NO NATIVE PROCESS'}
                write(evidence / 'metadata.json', metadata)
                (evidence / 'processes.jsonl').write_text(json.dumps(metadata) + '\n')

            def call(self, command, arguments):
                self.commands.append({'command': command, **arguments})
                write(evidence / 'replay.json', {'version': 1, 'commands': self.commands})
                if command == 'reset':
                    owner.assertEqual(arguments['mods'], [])
                    owner.assertNotIn('save_path', arguments)
                    self.state['seed'] = arguments['seed']
                if command == 'capture_frame':
                    filename = arguments['name']
                    number = next(i for i, r in enumerate(owner.survey['biomes'])
                                  if r['id'] + '.png' == filename)
                    # Robustly distinct after lossy WebP; these are visibly synthetic test patterns.
                    image = Image.new('RGB', (960, 540), 'white')
                    draw = ImageDraw.Draw(image)
                    for bit in range(7):
                        if number & (1 << bit):
                            draw.rectangle((bit * 100, 0, bit * 100 + 50, 539), fill='black')
                    image.save(evidence / filename)
                    owner.native_state_change(self.state)
                    owner.after_frame()
                    return {'path': str(evidence / filename), 'state': self.state}
                return self.state

            def close(self):
                self.process.returncode = owner.native_exit
                owner.closed.append(True)

        return FixtureAdapter()

    def capture(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return capture_biomes.capture(self.game, self.manifest, self.survey_dir,
                    self.build_manifest, self.output, adapter_factory=self.factory, **kwargs)

    def prepare(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return update_provenance.prepare(self.game, self.manifest, self.survey_dir,
                self.build_manifest, self.output, self.base / 'bundle', root=self.public, **kwargs)

    def assert_public_unchanged(self):
        self.assertEqual({str(p.relative_to(self.public)): p.read_bytes()
                          for p in self.public.rglob('*') if p.is_file()}, self.initial_files)

    def test_pilot_resume_complete_prepare_publish_and_archive(self):
        self.capture(ids=['Meadow'])
        self.assertEqual(self.native_count, 1)
        self.assertFalse((self.output / 'capture-manifest.json').exists())
        with self.assertRaises(FileNotFoundError):
            self.prepare()
        self.capture(resume=True)
        self.assertEqual(self.native_count, 92)
        self.assertEqual(len(self.closed), 92)
        receipt_before = (self.output / 'capture-manifest.json').read_bytes()
        self.capture(resume=True)
        self.assertEqual(self.native_count, 92, 'Resume must not repeat completed native work')
        self.assertEqual((self.output / 'capture-manifest.json').read_bytes(), receipt_before)
        self.prepare()
        bundle = self.base / 'bundle'
        self.assert_public_unchanged()
        self.assertEqual(read(bundle / 'data/provenance.json')['generator_version'], 10)
        self.assertNotIn(str(self.base), (bundle / 'data/captures.json').read_text())
        # Fake previous public bytes allow exact archive checks without touching the real wiki.
        for name in update_provenance.public_files(read(bundle / 'data/captures.json')):
            (self.public / name).write_bytes(b'Previous fixture gallery: ' + name.encode())
        before = {str(p.relative_to(self.public)): p.read_bytes()
                  for p in self.public.rglob('*') if p.is_file()}
        archive = self.base / 'archive'
        with contextlib.redirect_stdout(io.StringIO()):
            update_provenance.publish(bundle, archive, self.public)
        for name in update_provenance.public_files(read(bundle / 'data/captures.json')):
            self.assertEqual((archive / name).read_bytes(), before[name])
            self.assertEqual((self.public / name).read_bytes(), (bundle / name).read_bytes())
        # A cross-generation receipt cannot be rescued by regenerating the display JSON.
        captures = read(bundle / 'data/captures.json')
        captures['Meadow']['generatorVersion'] = 9
        write(bundle / 'data/captures.json', captures)
        with self.assertRaises(AssertionError):
            validate_catalog(bundle)
        with self.assertRaisesRegex(ValueError, 'Changed publication bundle'):
            update_provenance.publish(bundle, self.base / 'other-archive', self.public)
        self.assertFalse((self.base / 'other-archive').exists())

    def test_archived_public_atlas_remains_valid(self):
        with contextlib.redirect_stdout(io.StringIO()):
            validate_catalog(ROOT)

    def test_build_failure_has_no_completion_and_requires_isolated_outputs(self):
        self.fail_build = True
        output = self.base / 'failed-build'
        with patch.object(build_biome_capture.subprocess, 'run', side_effect=self.fake_command):
            with self.assertRaises(subprocess.CalledProcessError):
                build_biome_capture.build(self.game, self.manifest, output)
        self.assertFalse((output / 'build-manifest.json').exists())
        self.assertTrue((output / 'build.log').exists())
        with self.assertRaisesRegex(ValueError, 'outside'):
            build_biome_capture.build(self.game, self.manifest, self.game / 'bad')

    def test_source_change_during_build_does_not_certify(self):
        self.after_build = lambda: (self.game / 'Cargo.lock').write_text('changed')
        output = self.base / 'changed-build'
        with patch.object(build_biome_capture.subprocess, 'run', side_effect=self.fake_command):
            with self.assertRaisesRegex(ValueError, 'Changed or missing'):
                build_biome_capture.build(self.game, self.manifest, output)
        self.assertFalse((output / 'build-manifest.json').exists())

    def test_old_or_changed_binary_is_rejected_before_a_native_process(self):
        (self.build_dir / 'target/release/voxelgame').write_bytes(b'another executable')
        with self.assertRaisesRegex(ValueError, 'build does not match'):
            self.capture(ids=['Meadow'])
        self.assertEqual(self.native_count, 0)
        self.assertFalse(self.output.exists())

    def test_changed_survey_or_checked_camera_fails_before_capture(self):
        for name in ('survey.json', 'viewpoints.json', 'survey-sites.csv', 'survey-sites-checked.json'):
            path = self.survey_dir / name
            original = path.read_bytes()
            path.write_bytes(original + b' ')
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Changed survey evidence'):
                self.capture(ids=['Meadow'])
            path.write_bytes(original)
        self.assertEqual(self.native_count, 0)

    def test_no_output_may_enter_source_or_wiki_or_existing_capture(self):
        for path in (self.game / 'new', ROOT / 'data/new'):
            self.output = path
            with self.assertRaisesRegex(ValueError, 'outside'):
                self.capture(ids=['Meadow'])
        self.output = self.base / 'captures'
        self.capture(ids=['Meadow'])
        with self.assertRaises(FileExistsError):
            self.capture(ids=['Meadow'])
        self.assert_public_unchanged()

    def test_failed_capture_closes_native_and_preserves_partial_evidence(self):
        def fail():
            raise RuntimeError('fixture native failure')
        self.after_frame = fail
        with self.assertRaisesRegex(RuntimeError, 'fixture native failure'):
            self.capture(ids=['Meadow'])
        self.assertEqual(len(self.closed), 1)
        self.assertFalse((self.output / 'capture-manifest.json').exists())
        self.assertFalse((self.output / 'captures.json').exists())
        self.assertTrue(list((self.output / 'evidence').glob('*/Meadow.png')))
        self.assert_public_unchanged()

    def test_non_base_game_state_cannot_receive_capture_receipt(self):
        self.native_state_change = lambda state: state.update(mods=['fixture-pack'])
        with self.assertRaisesRegex(ValueError, 'unedited base-game'):
            self.capture(ids=['Meadow'])
        self.assertEqual(len(self.closed), 1)
        self.assertFalse((self.output / 'captures.json').exists())

    def test_resume_rejects_replaced_images_or_changed_options(self):
        self.capture(ids=['Meadow'])
        with self.assertRaisesRegex(ValueError, 'Resume inputs changed'):
            self.capture(ids=['Meadow'], resume=True, batches=10)
        (self.output / 'images/Meadow.webp').write_bytes(b'changed image')
        with self.assertRaisesRegex(ValueError, 'Changed capture evidence'):
            self.capture(ids=['Meadow'], resume=True)
        self.assertEqual(self.native_count, 1)

    def test_changed_source_during_capture_has_no_completion_receipt(self):
        old_lock = (self.game / 'Cargo.lock').read_bytes()
        self.after_frame = lambda: (self.game / 'Cargo.lock').write_text('changed during capture')
        with self.assertRaisesRegex(ValueError, 'Changed or missing'):
            self.capture(ids=['Meadow'])
        self.assertFalse((self.output / 'capture-manifest.json').exists())
        self.assertTrue((self.output / 'capture-invalid.json').exists())
        (self.game / 'Cargo.lock').write_bytes(old_lock)
        with self.assertRaisesRegex(ValueError, 'Run invalidated'):
            self.capture(ids=['Meadow'], resume=True)
        self.assert_public_unchanged()

    def test_shutdown_failure_never_certifies_even_when_a_frame_exists(self):
        self.native_exit = 1
        with self.assertRaisesRegex(RuntimeError, 'did not exit successfully'):
            self.capture(ids=['Meadow'])
        self.assertEqual(len(self.closed), 1)
        self.assertFalse((self.output / 'captures.json').exists())
        self.assertTrue(list((self.output / 'evidence').glob('*/Meadow.png')))

    def test_total_capture_timeout_closes_the_owned_process(self):
        with patch.object(capture_biomes.time, 'monotonic', side_effect=[0, 2]):
            with self.assertRaisesRegex(TimeoutError, 'time budget exhausted'):
                self.capture(ids=['Meadow'], seconds=1)
        self.assertEqual(len(self.closed), 1)
        self.assertFalse((self.output / 'captures.json').exists())

    def test_replay_cannot_claim_settings_different_from_its_commands(self):
        self.capture(ids=['Meadow'])
        captures = read(self.output / 'captures.json')
        name = captures['Meadow']['evidence'] + '/replay.json'
        replay = read(self.output / name)
        replay['commands'][0]['mods'] = ['fixture-pack']
        write(self.output / name, replay)
        captures['Meadow']['evidenceHashes'][name] = sha(self.output / name)
        write(self.output / 'captures.json', captures)
        with self.assertRaisesRegex(ValueError, 'Native replay differs'):
            self.capture(resume=True)


if __name__ == '__main__':
    unittest.main()
