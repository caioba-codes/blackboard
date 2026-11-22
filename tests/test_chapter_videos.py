"""Per-chapter lesson videos: one project per ## chapter, tied to that chapter's text; the board joins the ready ones
into one playlist (parts with offsets, absolute lesson lines) and keeps the others as not ready yet."""

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PIPE = ROOT / "bin/video_pipeline.py"
IMPORT = ROOT / "bin/lesson_video.py"
sys.path.insert(0, str(ROOT / "bin"))
import lesson_chapters  # noqa: E402

LESSON = """---
title: Two Chapters
photo: assets/x.jpg
---

# Two Chapters

::: contents
1. [Chapter 1 · Limits](#s-a)
2. [Chapter 2 · Parts](#s-b)
:::

## Chapter 1 · Limits

Question one

## Chapter 2 · Parts

Question two
"""


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs ffmpeg")
class ChapterVideoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ws = self.root / "learn"
        (self.ws / "lessons").mkdir(parents=True)
        self.lesson = self.ws / "lessons/0042-two.md"
        self.lesson.write_text(LESSON, encoding="utf-8")
        self.importer = load(IMPORT, "lesson_video_chapters")
        self.bridge = self.importer.board_bridge()

    def run_ok(self, *args):
        r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return r

    def build(self, n, question_line):
        proj = self.root / f"ch{n}"
        self.run_ok(PIPE, "init", "--lesson", self.lesson, "--project", proj, "--chapter", n)
        config = json.loads((proj / "project.json").read_text())
        script = {"title": "T", "subtitle": "", "chapters": ["C"], "scenes": [{"id": "s00", "chapter": 0, "visual": "q", "cues": [
            {"id": "a", "say": "Your turn: pause and solve it.", "show": "Your turn."}, {"id": "think1", "pause": 1},
            {"id": "b", "say": "The answer.", "show": "The answer."}]}]}
        timeline = {"title": "T", "total": 6, "fps": 30, "scenes": [{"id": "s00", "start": 0, "dur": 6, "cues": {
            "a": {"s": .2, "e": 1}, "think1": {"s": 1, "e": 3, "pause": True}, "b": {"s": 3, "e": 5}},
            "subs": [{"s": .2, "e": 1, "text": "Your turn: pause and solve it."}, {"s": 3, "e": 5, "text": "The answer."}]}]}
        anchors = {"version": 1, "lessonSha256": config["lessonSha256"], "segments": [
            {"id": "q", "label": f"Question {n}", "scene": "s00", "from": "start", "to": "end", "line": question_line,
             "step": None, "practice": {"pause": "think1", "reveal": "b"}}]}
        for name, data in (("script.json", script), ("timeline.json", timeline), ("anchors.json", anchors), ("SPLIT.json", {"m": ["s00"]})):
            (proj / name).write_text(json.dumps(data), encoding="utf-8")
        self.run_ok(PIPE, "build-map", "--project", proj)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=32x32:r=5",
                        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=8000", "-t", "6",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(proj / "final.mp4")],
                       check=True, capture_output=True, text=True)
        return proj

    def install(self, n, proj):
        self.run_ok(IMPORT, "import", "--workspace", self.ws, "--lesson", "0042", "--chapter", n,
                    "--video", proj / "final.mp4", "--map", proj / f"video-0042-ch{n:02d}.json")

    def test_chapters_build_install_and_play_as_one_playlist(self):
        self.assertEqual(lesson_chapters.spans(LESSON), [(5, 16), (17, 19)])
        p1, p2 = self.build(1, 15), self.build(2, 19)
        m1 = json.loads((p1 / "video-0042-ch01.json").read_text())
        self.assertEqual((m1["chapter"], m1["video"], m1["segments"][0]["line"]), (1, "0042-ch01-lecture.mp4", 11))
        self.assertEqual(json.loads((p2 / "video-0042-ch02.json").read_text())["segments"][0]["line"], 3)
        stages = json.loads(subprocess.run([sys.executable, PIPE, "check", "--project", p2], capture_output=True, text=True).stdout)["stages"]
        for stage in ("source", "anchors", "practice", "coverage", "padding", "map", "captions"):
            self.assertTrue(stages[stage].startswith("ready"), (stage, stages[stage]))
        # nothing installed yet, both projects registered: the board lists both chapters as not ready
        self.assertEqual([c["state"] for c in self.bridge.lesson_video("0042", str(self.ws))["chapters"]], ["missing", "missing"])
        self.install(1, p1)
        v = self.bridge.lesson_video("0042", str(self.ws))
        self.assertTrue(v["available"])
        self.assertEqual([c["state"] for c in v["chapters"]], ["ready", "missing"])
        self.assertEqual(len(v["parts"]), 1)
        self.install(2, p2)
        v = self.bridge.lesson_video("0042", str(self.ws))
        self.assertEqual([(p["chapter"], p["offset"]) for p in v["parts"]], [(1, 0), (2, 6)])
        self.assertEqual([(s["start"], s["end"], s["line"]) for s in v["segments"]], [(0, 6, 15), (6, 12, 19)])
        self.assertEqual(v["segments"][1]["practice"], {"pauseAt": 7, "revealAt": 9})
        caps = self.bridge.chapter_captions("0042", str(self.ws))
        self.assertGreaterEqual(min(c["s"] for c in caps["cues"] if c["text"] == "The answer."), 3)
        self.assertTrue(any(c["s"] >= 9 for c in caps["cues"]))
        # a new line in chapter 1 invalidates chapter 1 only; chapter 2's lines move with it
        self.lesson.write_text(LESSON.replace("Question one\n", "Question one\nMore.\n"), encoding="utf-8")
        v = self.bridge.lesson_video("0042", str(self.ws))
        self.assertEqual([c["state"] for c in v["chapters"]], ["stale", "ready"])
        self.assertEqual([(p["chapter"], p["offset"]) for p in v["parts"]], [(2, 0)])
        self.assertEqual(v["segments"][0]["line"], 20)
        out = self.root / "joined.mp4"
        self.lesson.write_text(LESSON, encoding="utf-8")
        joined = json.loads(self.run_ok(IMPORT, "join", "--workspace", self.ws, "--lesson", "0042", "--out", out).stdout)
        self.assertEqual(joined["chapters"], [1, 2])
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                                   capture_output=True, text=True).stdout)
        self.assertAlmostEqual(dur, 12, delta=0.6)

    def test_a_whole_lesson_video_still_wins(self):
        p1 = self.build(1, 15)
        self.install(1, p1)
        whole = self.ws / "lessons/assets/0042-lecture.mp4"
        shutil.copy(p1 / "final.mp4", whole)
        m = json.loads((p1 / "video-0042-ch01.json").read_text())
        m.pop("chapter")
        m.update(video="0042-lecture.mp4", lessonSha256=__import__("hashlib").sha256(self.lesson.read_bytes()).hexdigest())
        m["segments"][0]["line"] = 15
        (self.ws / "reference/video-0042.json").write_text(json.dumps(m), encoding="utf-8")
        v = self.bridge.lesson_video("0042", str(self.ws))
        self.assertTrue(v["available"] and v["mappingValid"])
        self.assertNotIn("parts", v)


if __name__ == "__main__":
    unittest.main()
