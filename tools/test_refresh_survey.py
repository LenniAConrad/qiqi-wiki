# SPDX-License-Identifier: GPL-3.0-only
"""Survey orchestration fixtures: these tests do not compile or sample the game."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import refresh_survey as survey_tool
from freeze_media_source import sha


class SurveyStaging(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / 'source'
        self.wiki = self.root / 'wiki'
        self.output = self.root / 'private-survey'
        self.manifest = self.root / 'source-manifest.json'
        files = {'Cargo.lock': '# fixture lock\n',
                 survey_tool.GENERATOR: 'pub enum GeneratorVersion {\n    Current = 10,\n}\n',
                 'crates/voxelgame-core/src/world/block.rs': '// fixture block\n',
                 'crates/voxelgame-core/src/world/generator/habitats.rs': '// fixture habitats\n'}
        for name, text in files.items():
            path = self.game / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        self.snapshot = {
            'commit': 'a' * 40,
            'files': [{'path': name, 'bytes': (self.game / name).stat().st_size,
                       'sha256': sha(self.game / name)} for name in files]}
        self.manifest.write_text(json.dumps(self.snapshot))
        # Reuse the old survey's shape, never mistake its numbers for a fresh run.
        self.survey = json.loads((survey_tool.ROOT / 'data/survey.json').read_text())
        self.survey['generatorVersion'] = 10
        (self.wiki / 'data').mkdir(parents=True)
        (self.wiki / 'data/survey.json').write_text('published survey must survive\n')
        (self.wiki / 'data/viewpoints.json').write_text(json.dumps({
            'Meadow': {'x': -999, 'surveySha256': 'stale', 'warmupFrames': 1200}}))
        for name in ['tools/survey/src/main.rs', 'tools/survey/src/bin/check_sites.rs']:
            path = self.wiki / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('// private orchestration fixture only\n')
        self.public_before = {p.name: p.read_bytes() for p in (self.wiki / 'data').iterdir()}
        self.addCleanup(self.assert_public_unchanged)
        self.addCleanup(patch.stopall)
        patch.object(survey_tool, 'ROOT', self.wiki).start()
        self.runner = patch.object(survey_tool.subprocess, 'run', side_effect=self.fake_native).start()
        self.after_survey = lambda: None
        self.after_sites = lambda: None

    def assert_public_unchanged(self):
        self.assertEqual({p.name: p.read_bytes() for p in (self.wiki / 'data').iterdir()},
                         self.public_before)

    def fake_native(self, command, **kwargs):
        """Write deterministic fixture outputs instead of running Cargo/game code."""
        binary = command[command.index('--bin') + 1]
        target = Path(kwargs['env']['CARGO_TARGET_DIR']) / 'release' / binary
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'Orchestration fixture, not an executable or game receipt.\n')
        if binary == 'qiqi-biome-survey':
            Path(command[-1]).write_text(json.dumps(self.survey))
            self.after_survey()
        else:
            checked = {row['id']: {'height': row['height'], 'water': row['water'],
                                   'cameraGround': row['height']} for row in self.survey['biomes']}
            Path(command[-1]).write_text(json.dumps(checked))
            self.after_sites()
        return subprocess.CompletedProcess(command, 0)

    def refresh(self, **kwargs):
        return survey_tool.refresh(self.game, self.manifest, self.output, **kwargs)

    def assert_incomplete(self):
        self.assertFalse((self.output / 'survey-manifest.json').exists())

    def test_complete_snapshot_stages_without_publishing_and_clears_stale_cameras(self):
        record = self.refresh()
        self.assertEqual(record['generatorVersion'], 10)
        self.assertEqual(record['sourceCommit'], self.snapshot['commit'])
        self.assertEqual(record['surveySha256'], sha(self.output / 'survey.json'))
        self.assertEqual(record['viewpointsSha256'], sha(self.output / 'viewpoints.json'))
        self.assertEqual(record['checkedSitesSha256'], sha(self.output / 'survey-sites-checked.json'))
        self.assertEqual(record['sourceManifestSha256'], sha(self.manifest))
        self.assertEqual(json.loads((self.output / 'viewpoints.json').read_text())['Meadow'],
                         {'warmupFrames': 1200})
        self.assertEqual(json.loads((self.output / 'survey-manifest.json').read_text()), record)
        for call in self.runner.call_args_list:
            command = call.args[0]
            self.assertEqual(command[:2], ['timeout', '--kill-after=30s'])
            self.assertIn('--offline', command)
            self.assertEqual(call.kwargs['env']['CARGO_BUILD_JOBS'], '2')
            self.assertEqual(call.kwargs['env']['TMPDIR'], str(self.output / 'tmp'))
            self.assertEqual(call.kwargs['cwd'], self.output)

    def test_archived_manifest_remains_readable(self):
        hashes = {row['path']: row['sha256'] for row in self.snapshot['files']}
        self.manifest.write_text(json.dumps({
            'sourceCommit': 'b' * 40, 'generatorVersion': 10,
            'sourceFilesSha256': hashes, 'generatorSha256': hashes[survey_tool.GENERATOR],
            'generatorSourcesSha256': {name: value for name, value in hashes.items()
                                       if name.endswith('habitats.rs')}}))
        self.assertEqual(self.refresh()['sourceCommit'], 'b' * 40)

    def test_outputs_reject_source_trees_existing_receipts_and_symlink_aliases(self):
        for output in [self.game / 'nested', self.wiki / 'data/new']:
            with self.subTest(output=output), self.assertRaisesRegex(ValueError, 'outside'):
                survey_tool.refresh(self.game, self.manifest, output)
        alias = self.root / 'alias'
        alias.symlink_to(self.wiki, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'outside'):
            survey_tool.refresh(self.game, self.manifest, alias / 'new')
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.refresh(target=self.game / 'target')
        self.output.mkdir()
        sentinel = self.output / 'survey-manifest.json'
        sentinel.write_text('keep previous evidence')
        with self.assertRaises(FileExistsError):
            self.refresh()
        self.assertEqual(sentinel.read_text(), 'keep previous evidence')
        self.runner.assert_not_called()

    def test_changed_or_unrecorded_sources_stop_before_any_native_command(self):
        path = self.game / 'Cargo.lock'
        original = path.read_bytes()
        path.write_bytes(b'changed lock')
        with self.assertRaisesRegex(ValueError, 'Changed or missing'):
            self.refresh()
        path.write_bytes(original)
        (self.game / 'unrecorded.rs').write_text('// extra input')
        with self.assertRaisesRegex(ValueError, 'unrecorded'):
            self.refresh()
        self.runner.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_source_or_manifest_changes_during_native_execution_do_not_certify(self):
        def change_source():
            (self.game / 'Cargo.lock').write_text('changed during run')
        self.after_survey = change_source
        with self.assertRaisesRegex(ValueError, 'Changed or missing'):
            self.refresh()
        self.assertEqual(self.runner.call_count, 1)
        self.assert_incomplete()

    def test_rewritten_manifest_cannot_relabel_a_running_survey(self):
        def change_manifest():
            self.snapshot['commit'] = 'b' * 40
            self.manifest.write_text(json.dumps(self.snapshot))
        self.after_survey = change_manifest
        with self.assertRaisesRegex(ValueError, 'manifest changed'):
            self.refresh()
        self.assert_incomplete()

    def test_changed_copied_tool_does_not_certify(self):
        self.after_survey = lambda: (self.output / 'survey-project/main.rs').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'tool changed'):
            self.refresh()
        self.assert_incomplete()

    def test_failed_native_command_preserves_private_log_without_completion(self):
        def fail(command, **kwargs):
            kwargs['stderr'].write('fixture native failure\n')
            raise subprocess.CalledProcessError(124, command)
        self.runner.side_effect = fail
        with self.assertRaises(subprocess.CalledProcessError):
            self.refresh()
        self.assertEqual((self.output / 'survey.log').read_text(), 'fixture native failure\n')
        self.assert_incomplete()

    def test_mismatched_generation_and_sampling_contract_fail_before_site_check(self):
        for key, value in [('generatorVersion', 9), ('seeds', [1]), ('radiusMetres', 1),
                           ('strideMetres', 1), ('totalSamples', 1)]:
            with self.subTest(key=key):
                sample = copy.deepcopy(self.survey)
                sample[key] = value
                with self.assertRaisesRegex(ValueError, 'sampling contract'):
                    survey_tool.validate_survey(sample, 10)
        self.survey['biomes'][-1]['id'] = self.survey['biomes'][0]['id']
        with self.assertRaisesRegex(ValueError, 'sampling contract'):
            self.refresh()
        self.assertEqual(self.runner.call_count, 1)
        self.assert_incomplete()

    def test_changed_survey_during_site_check_does_not_certify(self):
        self.after_sites = lambda: (self.output / 'survey-pending.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'changed during site verification'):
            self.refresh()
        self.assert_incomplete()

    def test_replaced_survey_executable_cannot_receive_another_binarys_receipt(self):
        path = self.output / 'target/release/qiqi-biome-survey'
        self.after_sites = lambda: path.write_bytes(b'replacement fixture')
        with self.assertRaisesRegex(ValueError, 'executable or resolved dependencies changed'):
            self.refresh()
        self.assert_incomplete()

    def test_changed_generator_declaration_needs_review_before_compilation(self):
        path = self.game / survey_tool.GENERATOR
        path.write_text('pub enum GeneratorVersion {\n    Current,\n}\n')
        for row in self.snapshot['files']:
            if row['path'] == survey_tool.GENERATOR:
                row.update(bytes=path.stat().st_size, sha256=sha(path))
        self.manifest.write_text(json.dumps(self.snapshot))
        with self.assertRaisesRegex(ValueError, 'GeneratorVersion::Current'):
            self.refresh()
        self.runner.assert_not_called()

    def test_buried_camera_does_not_certify(self):
        def bury():
            path = self.output / 'survey-sites-checked.json'
            data = json.loads(path.read_text())
            data['Meadow']['cameraGround'] = 1e9
            path.write_text(json.dumps(data))
        self.after_sites = bury
        with self.assertRaisesRegex(ValueError, 'buried camera'):
            self.refresh()
        self.assert_incomplete()

    def test_missing_checked_site_does_not_certify(self):
        def omit():
            path = self.output / 'survey-sites-checked.json'
            data = json.loads(path.read_text())
            data.pop('Meadow')
            path.write_text(json.dumps(data))
        self.after_sites = omit
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            self.refresh()
        self.assert_incomplete()


if __name__ == '__main__':
    unittest.main()
