"""given.py wraps what an official problem states in ::: given, marks copied solution columns, and moves a video map."""
import hashlib, importlib.util, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("given", HERE.parent / "bin/given.py")
given = importlib.util.module_from_spec(spec)
spec.loader.exec_module(given)

LESSON = """# T

<!-- source: x, quoted verbatim -->
[Official · Spring 2019 Exam 3, Q4C](src:x.pdf#page=5)

**Part C** Fill in the table.

| S | C | NS |
|---|---|---|
| 0 | 1 | |
| 1 | 0 | |

::: checkin
- [Official · Spring 2019 Exam 3, Q4C](src:x.pdf#page=5) Fill it in. || Follow the arcs.

  | S | C | NS |
  |---|---|---|
  | 0 | 1 | 1 |
  | 1 | 0 | 0 |
:::

<!-- source: y, quoted verbatim -->
[Official · Fall 2018 Exam 3, Q1](src:y.pdf#page=3)

**Worked example.** Simulate the latch.

#### Solution

It holds.
"""


class Given(unittest.TestCase):
    def test_wraps_marks_and_splits(self):
        new, mapping, blocks, edits = given.wrap(LESSON)
        self.assertEqual(blocks, 2)
        self.assertIn("::: given\n**Part C** Fill in the table.", new)
        self.assertIn("  | >S | >C | NS |", new)
        self.assertIn("**Worked example.**\n\n::: given\nSimulate the latch.\n:::", new)
        old, nl = LESSON.split("\n"), new.split("\n")
        self.assertEqual(nl[mapping[old.index("It holds.") + 1] - 1], "It holds.")

    def test_video_map_follows_the_lines(self):
        with tempfile.TemporaryDirectory() as d:
            ws = Path(d) / "learn"
            (ws / "lessons").mkdir(parents=True)
            (ws / "reference").mkdir()
            lesson = ws / "lessons/0001-t.md"
            lesson.write_text(LESSON, encoding="utf-8")
            line = LESSON.split("\n").index("It holds.") + 1
            (ws / "reference/video-0001.json").write_text(json.dumps({"lessonSha256": hashlib.sha256(LESSON.encode()).hexdigest(), "segments": [{"line": line}]}))
            subprocess.run([sys.executable, str(HERE.parent / "bin/given.py"), str(lesson), "--write"], check=True, capture_output=True)
            new = lesson.read_text(encoding="utf-8")
            m = json.loads((ws / "reference/video-0001.json").read_text())
            self.assertEqual(m["lessonSha256"], hashlib.sha256(new.encode()).hexdigest())
            self.assertEqual(new.split("\n")[m["segments"][0]["line"] - 1], "It holds.")
            lint = subprocess.run([sys.executable, str(HERE.parent / "bin/lint.py"), str(lesson)], capture_output=True, text=True)
            self.assertNotIn("given block", lint.stderr)

if __name__ == "__main__":
    unittest.main()
