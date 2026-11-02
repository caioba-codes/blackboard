"""Flags: the bridge keeps each workspace's flagged chapters and problems in learning-records/flags.json, answers only
the board's own pages, refuses unknown workspaces, lessons and malformed anchors, and marks a flag `missing` when
nothing in the lesson matches it any more."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bridge', ROOT / 'board/bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

LESSON = """---
title: Exam 2
---

## Chapter 1 · Bases and Conversions

**Worked example · Read hexadecimal.** Multiply each digit.

[Official · Fall 2018 Exam 2, Q3b](src:exams2/fa18-kj-e2.pdf#page=6)

::: checkin
- Fill in the grey boxes for $\\text{3A9}_{16}$. || Done.
:::

::: mcq r10oc1a c
Which pair fills the third row?
- a
- b
- c
- d
:::
"""


class FlagTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.wsp = os.path.join(self.tmp.name, 'ece', 'learn')
        os.makedirs(os.path.join(self.wsp, 'lessons'))
        Path(self.wsp, 'lessons', '0010-exam.md').write_text(LESSON)
        reg = {'ece': {'path': self.wsp}}
        self._orig = (bridge.state, bridge.workspaces)
        bridge.state = lambda: {'ws': self.wsp, 'workspaces': reg}
        bridge.workspaces = lambda: reg
        self.srv = bridge.ThreadingHTTPServer(('127.0.0.1', 0), bridge.H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f'http://127.0.0.1:{self.srv.server_address[1]}'

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        bridge.state, bridge.workspaces = self._orig
        self.tmp.cleanup()

    def call(self, path, body=None, origin=None):
        req = urllib.request.Request(self.base + path, data=json.dumps(body).encode() if body is not None else None,
                                     headers={'Content-Type': 'application/json', **({'Origin': origin} if origin else {})})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def add(self, **kw):
        return self.call('/flags', dict({'ws': 'ece', 'op': 'add', 'lesson': '0010', 'kind': 'question'}, **kw))

    def test_add_note_move_remove_persist(self):
        code, r = self.add(anchor='f-official-fall-2018-exam-2-q3b', label='Official · Fall 2018 Exam 2, Q3b',
                           chapter='Chapter 1 · Bases and Conversions', needle='Official · Fall 2018 Exam 2, Q3b')
        self.assertEqual(code, 200)
        fid = r['flag']['id']
        self.assertEqual(r['flag']['needle'], 'officialfall2018exam2q3b')
        self.assertTrue(r['flag']['added'].endswith('Z'))
        # a second add of the same item returns the same flag
        self.assertEqual(self.add(anchor='f-official-fall-2018-exam-2-q3b')[1]['flag']['id'], fid)
        on_disk = json.loads(Path(self.wsp, 'learning-records', 'flags.json').read_text())
        self.assertEqual([f['id'] for f in on_disk['flags']], [fid])
        self.assertEqual(self.call('/flags', {'ws': 'ece', 'op': 'note', 'id': fid, 'note': 'redo\nthis'})[1]['flag']['note'], 'redo this')
        self.assertEqual(self.call('/flags', {'ws': 'ece', 'op': 'move', 'id': fid, 'anchor': 'f-official-fall-2018-exam-2-q3b-2'})[0], 200)
        code, r = self.call('/api/flags?ws=ece&lesson=0010')
        self.assertEqual((code, r['flags'][0]['anchor'], r['flags'][0]['missing']), (200, 'f-official-fall-2018-exam-2-q3b-2', False))
        self.assertEqual(self.call('/api/flags?all=1')[1]['folders'][0]['slug'], 'ece')
        self.assertTrue(self.call('/flags', {'ws': 'ece', 'op': 'remove', 'id': fid})[1]['removed'])
        self.assertEqual(self.call('/api/flags?ws=ece')[1]['flags'], [])
        self.assertEqual(self.call('/flags', {'ws': 'ece', 'op': 'remove', 'id': fid})[0], 404)

    def test_missing(self):
        self.add(anchor='s-chapter-1-bases-and-conversions', kind='chapter', needle='Chapter 1 · Bases and Conversions')
        self.add(anchor='q-r10oc1a', needle='Which pair')
        self.add(anchor='f-fill-in-the-grey-boxes-for-3a916', needle='Fill in the grey boxes for 3A916.')  # rendered math, no LaTeX
        self.add(anchor='f-worked-example-read-hexadecimal', kind='example', needle='Worked example · Read hexadecimal')
        self.add(anchor='f-official-spring-1999-exam-2-q9', needle='Official · Spring 1999 Exam 2, Q9')
        self.add(anchor='q-zzz', needle='')
        got = {f['anchor']: f['missing'] for f in self.call('/api/flags?ws=ece&lesson=0010')[1]['flags']}
        self.assertEqual(got, {'s-chapter-1-bases-and-conversions': False, 'q-r10oc1a': False, 'f-fill-in-the-grey-boxes-for-3a916': False,
                               'f-worked-example-read-hexadecimal': False, 'f-official-spring-1999-exam-2-q9': True, 'q-zzz': True})

    def test_refusals(self):
        self.assertEqual(self.add(anchor='../../etc')[0], 400)
        self.assertEqual(self.add(anchor='x"><img>')[0], 400)
        self.assertEqual(self.add(anchor='s-x', lesson='0099')[0], 404)
        self.assertEqual(self.add(anchor='s-x', lesson='../0010')[0], 404)
        self.assertEqual(self.call('/flags', {'ws': 'nope', 'op': 'add', 'lesson': '0010', 'anchor': 's-x'})[0], 404)
        self.assertEqual(self.call('/flags', {'ws': 'ece', 'op': 'drop', 'id': 'x'})[0], 404)
        # another web page can neither read nor change them; the board's own origin can
        evil = 'https://evil.example'
        self.assertEqual(self.call('/api/flags?ws=ece', origin=evil)[0], 403)
        self.assertEqual(self.call('/flags', {'ws': 'ece', 'op': 'add', 'lesson': '0010', 'anchor': 's-x'}, origin=evil)[0], 403)
        self.assertEqual(self.add(anchor='s-x')[0], 200)
        self.assertEqual(self.call('/api/flags?ws=ece', origin=f'http://localhost:{bridge.PORT}')[0], 200)
        self.assertFalse(Path(self.tmp.name, 'etc').exists())
        # a damaged file reads as no flags instead of breaking the page
        Path(self.wsp, 'learning-records', 'flags.json').write_text('{oops')
        self.assertEqual(self.call('/api/flags?ws=ece')[1]['flags'], [])


if __name__ == '__main__':
    unittest.main()
