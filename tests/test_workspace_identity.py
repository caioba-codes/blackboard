import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('bridge', Path(__file__).resolve().parents[1] / 'board/bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class WorkspaceIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.course = self.make_course('school')

    def tearDown(self):
        self.temp.cleanup()

    def make_course(self, parent):
        course = self.root / parent / 'ece2020' / 'learn'
        (course / 'lessons').mkdir(parents=True)
        (course / 'lessons/0009-checkoff.md').write_text(
            '---\ntitle: Checkoff\ncourse: ECE 2020\ndate: 2026-10-12\n---\n\nUnique circuit explanation.\n')
        return str(course)

    def test_hashed_registration_last_workspace_and_discovery_are_one(self):
        state = {'ws': self.course, 'current': '0009', 'workspaces': {
            'ece2020': {'path': str(self.root / 'gone')},
            'ece2020-58ec': {'path': self.course, 'current': '0009'}}}
        with patch.object(bridge, 'state', return_value=state), patch.object(bridge, 'discovered', return_value=[self.course]):
            self.assertEqual(list(bridge.workspaces()), ['ece2020-58ec'])
            self.assertEqual(len(bridge.hub()), 1)
            self.assertEqual(len(bridge.search('Unique circuit')), 1)
            self.assertEqual(bridge.ws('ece2020-58ec'), self.course)

    def test_symlink_alias_keeps_existing_urls(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.course, target_is_directory=True)
        state = {'ws': str(alias), 'workspaces': {
            'ece2020': {'path': self.course}, 'old-link': {'path': str(alias)}}}
        with patch.object(bridge, 'state', return_value=state), patch.object(bridge, 'discovered', return_value=[str(alias)]):
            self.assertEqual(len(bridge.hub()), 1)
            self.assertEqual(bridge.ws('old-link'), str(alias))

    def test_identical_titles_and_numbers_in_distinct_folders_survive(self):
        other = self.make_course('other')
        state = {'ws': other, 'workspaces': {'ece2020': {'path': self.course}}}
        with patch.object(bridge, 'state', return_value=state), patch.object(bridge, 'discovered', return_value=[self.course, other]):
            self.assertEqual(len(bridge.hub()), 2)
            self.assertEqual(len(bridge.search('Unique circuit')), 2)
            self.assertEqual({w['path'] for w in bridge.workspaces().values()}, {self.course, other})


if __name__ == '__main__':
    unittest.main()
