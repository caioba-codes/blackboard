"""Being written: while a lesson is live the bridge reports the planned chapters (from Contents), how many are
finished (the next ## heading landed) and, after two timed chapters, a rough time left."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('BLACKBOARD_HOME', tempfile.mkdtemp())
spec = importlib.util.spec_from_file_location('bridge', ROOT / 'board/bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

CONTENTS = ("---\ntitle: T\n---\n# T\n\n::: contents\n1. [Chapter 1 · Limits](#s-a) — 30% of the exam.\n"
            "2. [Chapter 2 · Parts](#s-b) — 20%.\n3. Chapter 3 · Series\n4. [Chapter 4 · Drill](#s-d)\n:::\n\n")


class WriteProgressTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = os.path.join(self.dir.name, '0001-t.md')
        bridge.WRITE_SEEN.clear()

    def write(self, text):
        Path(self.path).write_text(text, encoding='utf-8')

    def test_plan_rows_count_and_time_left(self):
        self.write(CONTENTS)
        w = bridge.write_progress(self.path, True, now=0)
        self.assertEqual([c['state'] for c in w['chapters']], ['planned'] * 4)
        self.assertEqual((w['finished'], w['total'], w['eta_s']), (0, 4, None))
        body = CONTENTS
        for i, (title, t) in enumerate((('Chapter 1 · Limits', 100), ('Chapter 2 · Parts', 400),
                                        ('Chapter 3 · Series', 700))):
            body += f"## {title}\n\nStep.\n\n"
            self.write(body)
            w = bridge.write_progress(self.path, True, now=t)
        self.assertEqual([c['state'] for c in w['chapters']], ['done', 'done', 'writing', 'planned'])
        self.assertEqual(w['chapters'][3]['title'], 'Chapter 4 · Drill')
        self.assertEqual((w['finished'], w['total']), (2, 4))
        # two finished chapters of 300 s each, the third just started: two chapters left, about 600 s
        self.assertEqual(w['eta_s'], 600)
        self.assertEqual(bridge.write_progress(self.path, True, now=1000)['eta_s'], 300)

    def test_headings_seen_together_give_no_time(self):
        self.write(CONTENTS + "## Chapter 1 · Limits\n\n## Chapter 2 · Parts\n\n## Chapter 3 · Series\n")
        w = bridge.write_progress(self.path, True, now=50)
        self.assertEqual((w['finished'], w['eta_s']), (2, None))

    def test_not_live_is_none(self):
        self.write(CONTENTS)
        self.assertIsNone(bridge.write_progress(self.path, False))


if __name__ == '__main__':
    unittest.main()
