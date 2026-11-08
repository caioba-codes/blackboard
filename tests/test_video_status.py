"""The board's video progress card: stage, counts, overall percent and measured time left, from a project's files."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin/video_status.py"
PIPELINE = ROOT / "bin/video_pipeline.py"
sys.path.insert(0, str(ROOT / "bin"))
import video_status  # noqa: E402


class VideoStatusTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.ws = self.root / "learn"
        (self.ws / "lessons").mkdir(parents=True)
        self.lesson = self.ws / "lessons/0042-motion.md"
        self.lesson.write_text("# Motion\n", encoding="utf-8")
        self.project = self.root / "video"
        (self.project / "audio").mkdir(parents=True)
        (self.project / "project.json").write_text(json.dumps({"lesson": str(self.lesson)}), encoding="utf-8")
        cues = [{"id": "a", "say": "One"}, {"id": "t", "pause": 3}, {"id": "b", "say": "Two"}]
        script = {"scenes": [{"id": "s1", "cues": cues}, {"id": "s2", "cues": [{"id": "a", "say": "Three"}, {"id": "b", "say": "Four"}]}]}
        for name, data in (("script.json", script), ("anchors.json", {}), ("SPLIT.json", {"intro": ["s1"], "rest": ["s2"]})):
            (self.project / name).write_text(json.dumps(data), encoding="utf-8")

    def touch(self, rel, t):
        p = self.project / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
        os.utime(p, (t, t))

    def cli(self, *args):
        r = subprocess.run([sys.executable, str(CLI), *map(str, args)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_narration_counts_kokoro_tmp_files_and_measures_time_left(self):
        self.assertIn("video-project-0042.json", self.cli("register", "--project", self.project))
        self.touch("audio/s1_a.wav", 1000)          # renamed by an earlier batch
        self.touch("audio/.tmp-s1_b.wav", 1002)     # still a temp file in the running batch
        self.touch("audio/.tmp-s2_a.wav", 1004)
        self.touch("audio/.tmp-0f3k.wav", 1004)     # an atomic_write temp, not a cue
        s = video_status.status(self.ws, "0042", now=1005)
        self.assertEqual((s["active"], s["stage"], s["stageIndex"]), (True, "narration", 2))
        narration = s["stages"][1]
        self.assertEqual((narration["done"], narration["total"], narration["unit"], narration["percent"]), (3, 4, "lines", 75.0))
        self.assertEqual([x["state"] for x in s["stages"]], ["done", "current", "todo", "todo", "todo", "todo"])
        self.assertEqual(s["percent"], 10 + 30 * 0.75)
        self.assertEqual(s["eta"], 1)               # 1 cue left at 2 s per cue, 1 s already spent on it
        self.assertFalse(s["stalled"])
        self.assertTrue(video_status.status(self.ws, "0042", now=1004 + 3600)["stalled"])
        self.assertEqual(json.loads(self.cli("show", "--workspace", self.ws, "--lesson", "0042"))["stage"], "narration")

    def test_render_counts_chunks_then_installed_hides_the_card(self):
        video_status.register(self.project)
        for n in ("tts.done", "timeline.json", "scenes/intro.js", "scenes/rest.js"):
            self.touch(n, 900)
        (self.project / "chunks").mkdir()
        (self.project / "chunks/plan.json").write_text(json.dumps({"total": 1000, "chunkFrames": 100}), encoding="utf-8")
        for i in range(4):
            self.touch(f"chunks/c{i:04d}.mp4", 2000 + 10 * i)
        self.touch("chunks/c0004.part.mp4", 2035)
        s = video_status.status(self.ws, "0042", now=2030)
        self.assertEqual(s["stage"], "render")
        self.assertEqual((s["stages"][3]["done"], s["stages"][3]["total"], s["stages"][3]["unit"]), (4, 10, "chunks"))
        self.assertEqual(s["percent"], 10 + 30 + 15 + 35 * 0.4)
        self.assertEqual(s["eta"], 60)              # 6 chunks left at 10 s per chunk; the .part file is not done
        assets = self.ws / "lessons/assets"
        assets.mkdir()
        (assets / "0042-lecture.mp4").touch()
        (self.ws / "reference/video-0042.json").write_text("{}", encoding="utf-8")
        self.assertEqual(video_status.status(self.ws, "0042"), {"active": False, "installed": True, "lesson": "0042"})

    def test_init_registers_and_no_pointer_means_no_card(self):
        self.assertEqual(video_status.status(self.ws, "0042")["active"], False)
        runtime = self.root / "runtime"
        runtime.mkdir()
        for name in ("engine.js", "style.css", "capture.mjs", "finish.sh", "tts.py", "index.html", "package.json", "render.sh"):
            (runtime / name).write_text("x\n", encoding="utf-8")
        fresh = self.root / "fresh"
        r = subprocess.run([sys.executable, str(PIPELINE), "init", "--lesson", self.lesson, "--project", fresh, "--runtime", runtime],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        ptr = json.loads((self.ws / "reference/video-project-0042.json").read_text(encoding="utf-8"))
        self.assertEqual(ptr["project"], str(fresh.resolve()))
        s = video_status.status(self.ws, "0042")
        self.assertEqual((s["active"], s["stage"], s["percent"]), (True, "script", 0.0))


if __name__ == "__main__":
    unittest.main()
