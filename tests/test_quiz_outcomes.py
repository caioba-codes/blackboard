"""Self-marking and the item outcome map: a "Got it" / "Missed it" under a check-in answer appends one quiz-log line next to
the multiple-choice lines, and the bridge folds the log into one map per lesson (latest mark per item wins, a multiple-choice
Reset clears the item, a wrong latest pick reads as missed), which the page reads back from /api/answers."""
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile
import threading
import unittest
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bridge', ROOT / 'board/bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def line(**kw):
    return json.dumps(kw)


class OutcomeMapTests(unittest.TestCase):
    def test_latest_mark_per_item_wins(self):
        log = [
            line(lesson='0001', mode='self', item='c-1a', chapter='Chapter 1 · Sums', result='missed', score=0),
            line(lesson='0001', mode='mcq', item='q1', choice='b', sig='s1', score=0),
            line(lesson='0001', mode='self', item='c-1a', chapter='Chapter 1 · Sums', result='got', score=5),
            line(lesson='0001', mode='mcq', item='q1', choice='c', sig='s1', chapter='Chapter 2 · Tests', score=5),
            line(lesson='0001', mode='mcq', item='q2', choice='a', sig='s2', score=5),
            line(lesson='0001', mode='mcq', item='q2', choice='d', sig='s2', score=0),
            line(lesson='0001', mode='mcq', item='q3', choice='a', sig='s3', score=5),
            line(lesson='0001', mode='mcq', item='q3', event='reset', sig='s3'),
            line(lesson='0001', mode='self', item='c-2b', chapter='Chapter 2 · Tests', result='missed', score=0),
            line(lesson='0002', mode='self', item='c-1a', result='missed', score=0),
            line(lesson='0001', mode='cards', item='k1', score=1),
            line(lesson='0001', mode='self', item='c-3c', result='maybe', score=2),
            '{not json',
        ]
        self.assertEqual(bridge.outcomes(log, '0001'), {
            'c-1a': {'kind': 'self', 'result': 'got', 'chapter': 'Chapter 1 · Sums'},
            'q1': {'kind': 'mcq', 'result': 'got', 'chapter': 'Chapter 2 · Tests', 'choice': 'c', 'sig': 's1'},
            'q2': {'kind': 'mcq', 'result': 'missed', 'chapter': '', 'choice': 'd', 'sig': 's2'},
            'c-2b': {'kind': 'self', 'result': 'missed', 'chapter': 'Chapter 2 · Tests'},
        })

    def test_a_pick_after_a_reset_counts_again(self):
        log = [line(lesson='0001', mode='mcq', item='q1', choice='a', sig='s', score=5),
               line(lesson='0001', mode='mcq', item='q1', event='reset', sig='s'),
               line(lesson='0001', mode='mcq', item='q1', choice='b', sig='s', score=0)]
        self.assertEqual(bridge.outcomes(log, '0001')['q1']['result'], 'missed')

    def test_record_shapes(self):
        rec = bridge.quiz_record({'ts': 'T', 'lesson': '0001', 'kind': 'self', 'item': 'c-1a', 'chapter': 'Chapter 1 · Sums', 'result': 'got'})
        self.assertEqual(json.dumps(rec, ensure_ascii=False),
                         '{"ts": "T", "lesson": "0001", "topic": "c-1a", "mode": "self", "item": "c-1a", "chapter": "Chapter 1 · Sums", "result": "got", "score": 5}')
        self.assertEqual(bridge.quiz_record({'ts': 'T', 'lesson': '0001', 'kind': 'self', 'item': 'c-1a', 'result': 'missed'})['score'], 0)
        self.assertIsNone(bridge.quiz_record({'kind': 'self', 'item': 'c-1a', 'result': 'later'}))
        self.assertIsNone(bridge.quiz_record({'kind': 'self', 'item': '', 'result': 'got'}))
        self.assertIsNone(bridge.quiz_record({'kind': 'predict', 'item': 'c-1a', 'result': 'got'}))
        self.assertEqual(bridge.quiz_record({'ts': 'T', 'lesson': '0001', 'kind': 'mcq', 'item': 'q1', 'event': 'reset', 'sig': 's'}),
                         {'ts': 'T', 'lesson': '0001', 'topic': 'q1', 'mode': 'mcq', 'item': 'q1', 'event': 'reset', 'sig': 's'})


class SelfMarkRouteTests(unittest.TestCase):
    """POST /ask logs into the page's workspace; GET /api/answers reads the map back; scores() counts self marks."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.wsp = os.path.join(self.tmp.name, 'calc', 'learn')
        os.makedirs(os.path.join(self.wsp, 'lessons'))
        Path(self.wsp, 'lessons', '0001-sums.md').write_text('---\ntitle: Sums\n---\n\n::: checkin\n- 1+1? || 2\n:::\n')
        reg = {'calc': {'path': self.wsp}}
        self._orig = (bridge.state, bridge.workspaces, bridge.QUEUE)
        bridge.state = lambda: {'ws': self.wsp, 'workspaces': reg}
        bridge.workspaces = lambda: reg
        bridge.QUEUE = os.path.join(self.tmp.name, 'queue.jsonl')
        self.srv = bridge.ThreadingHTTPServer(('127.0.0.1', 0), bridge.H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f'http://127.0.0.1:{self.srv.server_address[1]}'

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        bridge.state, bridge.workspaces, bridge.QUEUE = self._orig
        self.tmp.cleanup()

    def call(self, path, body=None):
        req = urllib.request.Request(self.base + path, data=json.dumps(body).encode() if body is not None else None,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())

    def test_self_mark_round_trip(self):
        mark = {'kind': 'self', 'ws': 'calc', 'lesson': '0001', 'item': 'c-k3x9', 'chapter': 'Chapter 1 · Sums'}
        self.assertEqual(self.call('/ask', dict(mark, result='missed')), {'queued': True, 'wake': 'none'})
        self.call('/ask', dict(mark, result='got'))
        self.call('/ask', {'kind': 'mcq', 'ws': 'calc', 'lesson': '0001', 'item': 'q1', 'choice': 'b', 'correct': False, 'sig': 's1',
                           'chapter': 'Chapter 1 · Sums'})
        lines = Path(self.wsp, 'learning-records', 'quiz-log.jsonl').read_text().splitlines()
        first = json.loads(lines[0])
        self.assertRegex(first.pop('ts'), r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$')
        self.assertEqual(first, {'lesson': '0001', 'topic': 'c-k3x9', 'mode': 'self', 'item': 'c-k3x9',
                                 'chapter': 'Chapter 1 · Sums', 'result': 'missed', 'score': 0})
        self.assertEqual(len(lines), 3)
        self.assertEqual(self.call('/api/answers?id=0001&ws=calc'), {
            'c-k3x9': {'kind': 'self', 'result': 'got', 'chapter': 'Chapter 1 · Sums'},
            'q1': {'kind': 'mcq', 'result': 'missed', 'chapter': 'Chapter 1 · Sums', 'choice': 'b', 'sig': 's1'},
        })
        self.assertEqual(bridge.scores(self.wsp), {'0001': [0, 5, 0]})

    def test_a_bad_self_mark_writes_nothing(self):
        self.call('/ask', {'kind': 'self', 'ws': 'calc', 'lesson': '0001', 'item': 'c-k3x9', 'result': 'perfect'})
        self.assertFalse(Path(self.wsp, 'learning-records', 'quiz-log.jsonl').exists())
        self.assertEqual(self.call('/api/answers?id=0001&ws=calc'), {})


if __name__ == '__main__':
    unittest.main()
