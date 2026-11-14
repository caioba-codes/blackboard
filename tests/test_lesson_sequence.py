"""A study route narrows navigation without removing older lessons from the board."""

import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.request


spec = importlib.util.spec_from_file_location('bridge', Path(__file__).resolve().parents[1] / 'board/bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class LessonSequenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name) / 'cs1331' / 'learn'
        lessons = self.workspace / 'lessons'
        lessons.mkdir(parents=True)
        for lid, title in [('0001', 'Earlier exam'), ('0006', 'Variables'),
                           ('0007', 'Methods'), ('0008', 'Programs')]:
            (lessons / f'{lid}-lesson.md').write_text(f'---\ntitle: {title}\n---\n\n# {title}\n')
        self.original_state, self.original_workspaces = bridge.state, bridge.workspaces
        registration = {'cs1331': {'path': str(self.workspace), 'current': '0007'}}
        bridge.state = lambda: {'ws': str(self.workspace), 'current': '0007', 'workspaces': registration}
        bridge.workspaces = lambda: registration
        self.server = bridge.ThreadingHTTPServer(('127.0.0.1', 0), bridge.H)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f'http://127.0.0.1:{self.server.server_address[1]}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        bridge.state, bridge.workspaces = self.original_state, self.original_workspaces

    def state(self):
        with urllib.request.urlopen(self.base + '/api/state?ws=cs1331&all=1') as response:
            self.assertEqual(response.status, 200)
            return json.load(response)

    def test_explicit_route_keeps_older_lessons_and_tolerates_stale_ids(self):
        (self.workspace / 'sequence.json').write_text(json.dumps({
            'version': 1, 'title': 'Exam 3',
            'lessons': ['0006', '0007', '0007', '0099', '0008']}))
        body = self.state()
        self.assertEqual([lesson['id'] for lesson in body['sequence']['lessons']], ['0006', '0007', '0008'])
        self.assertEqual(body['sequence']['title'], 'Exam 3')
        self.assertEqual(body['sequence']['total'], 3)
        self.assertEqual(body['sequence']['lessons'][1]['title'], 'Methods')
        self.assertEqual([lesson['id'] for lesson in body['lessons']], ['0001', '0006', '0007', '0008'])
        self.assertEqual(body['workspaces'][0]['sequence'], body['sequence'])
        self.assertEqual(body['workspaces'][0]['count'], 4)

    def test_default_and_unusable_route_still_offer_every_lesson(self):
        self.assertEqual([lesson['id'] for lesson in self.state()['sequence']['lessons']],
                         ['0001', '0006', '0007', '0008'])
        (self.workspace / 'sequence.json').write_text('{"version":1,"lessons":["0099","0099"]}')
        self.assertEqual([lesson['id'] for lesson in self.state()['sequence']['lessons']],
                         ['0001', '0006', '0007', '0008'])
        (self.workspace / 'sequence.json').write_text('{broken')
        self.assertEqual([lesson['id'] for lesson in self.state()['sequence']['lessons']],
                         ['0001', '0006', '0007', '0008'])

    def test_empty_and_single_lesson_routes(self):
        for path in (self.workspace / 'lessons').glob('*.md'):
            path.unlink()
        self.assertEqual(self.state()['sequence']['total'], 0)
        (self.workspace / 'lessons/0006-lesson.md').write_text('---\ntitle: Variables\n---\n\n# Variables\n')
        self.assertEqual([lesson['id'] for lesson in self.state()['sequence']['lessons']], ['0006'])


if __name__ == '__main__':
    unittest.main()
