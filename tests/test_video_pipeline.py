"""CLI boundary tests for portable project preparation and measured lesson maps."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin/video_pipeline.py"
RUNTIME = ("engine.js", "style.css", "capture.mjs", "finish.sh", "tts.py", "index.html", "package.json", "render.sh")


class VideoPipelineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()
        for name in RUNTIME:
            (self.runtime / name).write_text(f"generic {name}\n", encoding="utf-8")
        (self.runtime / "scenes").mkdir()
        (self.runtime / "scenes/sample.js").write_text("// portable example\n", encoding="utf-8")
        (self.runtime / "README.md").write_text("runtime instructions\n", encoding="utf-8")
        (self.runtime / "package-lock.json").write_text("{}\n", encoding="utf-8")
        (self.runtime / ".gitignore").write_text("final.mp4\n", encoding="utf-8")
        self.workspace = self.root / "learn"
        (self.workspace / "lessons").mkdir(parents=True)
        self.lesson = self.workspace / "lessons/0042-motion.md"
        self.lesson.write_text("# Motion\nQuestion one\nQuestion two\nSummary\n", encoding="utf-8")
        self.project = self.root / "project"

    def cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(CLI), *map(str, args)], capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stderr + result.stdout)
        return result

    def init(self):
        return self.cli("init", "--lesson", self.lesson, "--project", self.project, "--runtime", self.runtime)

    def plan(self):
        self.init()
        script = {"title": "Motion", "subtitle": "Example", "voice": "sample", "chapters": ["Intro"], "scenes": [
            {"id": "s00", "chapter": 0, "visual": "two questions", "cues": [
                {"id": "a", "say": "Question one"}, {"id": "think1", "pause": 1},
                {"id": "b", "say": "Answer one"}, {"id": "c", "say": "Question two"},
                {"id": "think2", "pause": 1}, {"id": "d", "say": "Answer two"}]},
            {"id": "s01", "chapter": 0, "visual": "recap", "cues": [{"id": "a", "say": "Summary"}]}]}
        timeline = {"title": "Motion", "total": 15, "fps": 30, "scenes": [
            {"id": "s00", "start": 0, "dur": 10, "cues": {
                "a": {"s": .5, "e": 1}, "think1": {"s": 1, "e": 2, "pause": True},
                "b": {"s": 2, "e": 3}, "c": {"s": 3, "e": 4},
                "think2": {"s": 4, "e": 5, "pause": True}, "d": {"s": 5, "e": 6}}},
            {"id": "s01", "start": 10, "dur": 5, "cues": {"a": {"s": .5, "e": 1}}}]}
        anchors = {"version": 1, "lessonSha256": hashlib.sha256(self.lesson.read_bytes()).hexdigest(), "segments": [
            {"id": "q1", "label": "Question one", "scene": "s00", "from": "start", "to": "c", "line": 2, "step": None, "practice": {"pause": "think1", "reveal": "b"}},
            {"id": "q2", "label": "Question two", "scene": "s00", "from": "c", "to": "end", "line": 3, "step": None, "practice": {"pause": "think2", "reveal": "d"}},
            {"id": "recap", "label": "Summary", "scene": "s01", "from": "start", "to": "end", "line": 4, "step": None, "practice": None}]}
        for name, data in (("script.json", script), ("timeline.json", timeline), ("anchors.json", anchors), ("SPLIT.json", {"intro": ["s00", "s01"]})):
            (self.project / name).write_text(json.dumps(data), encoding="utf-8")
        return anchors

    def test_init_resumes_and_refuses_to_clobber_runtime_work(self):
        (self.runtime / "node_modules/.bin").mkdir(parents=True)
        (self.runtime / "node_modules/.bin/playwright").symlink_to(self.runtime / "capture.mjs")
        (self.runtime / "sample").mkdir()
        (self.runtime / "sample/script.json").write_text("{}\n")
        (self.runtime / "test").mkdir()
        (self.runtime / "test/smoke.py").write_text("pass\n")
        for name in ("final.mp4", "timeline.json", "RENDERED"):
            (self.runtime / name).write_text("generated\n")
        first = self.init()
        self.assertIn("no model receipt was generated", first.stdout)
        self.assertFalse((self.project / "video-runs.json").exists())
        self.assertEqual({p.name for p in self.project.iterdir()}, set(RUNTIME) | {"README.md", "package-lock.json", ".gitignore", "project.json"})
        self.assertFalse((self.project / "scenes").exists())
        self.init()
        (self.project / "engine.js").write_text("local changes", encoding="utf-8")
        failure = self.cli("init", "--lesson", self.lesson, "--project", self.project, "--runtime", self.runtime, ok=False)
        self.assertIn("runtime conflict", failure.stderr)
        self.assertEqual((self.project / "engine.js").read_text(), "local changes")

    def test_effort_rejects_typo_and_accepts_supported_value(self):
        failure = self.cli("init", "--lesson", self.lesson, "--project", self.project,
                           "--runtime", self.runtime, "--video-effort", "hgih", ok=False)
        self.assertIn("--video-effort must be low, medium, or high", failure.stderr)
        self.assertFalse(self.project.exists())
        self.cli("init", "--lesson", self.lesson, "--project", self.project,
                 "--runtime", self.runtime, "--video-effort", "medium")
        config = json.loads((self.project / "project.json").read_text())
        self.assertEqual(config["videoRole"]["effort"], "medium")

    def test_split_requires_runtime_basename(self):
        self.plan()
        split = self.project / "SPLIT.json"
        split.write_text(json.dumps({"intro.js": ["s00", "s01"]}))
        rejected = self.cli("build-map", "--project", self.project, ok=False)
        self.assertIn("without .js", rejected.stderr)
        split.write_text(json.dumps({"intro": ["s00", "s01"]}))
        self.cli("build-map", "--project", self.project)
        (self.project / "scenes").mkdir()
        (self.project / "scenes/intro.js").write_text("// fixture scene\n")
        report = json.loads(self.cli("check", "--project", self.project, ok=False).stdout)
        self.assertEqual(report["stages"]["split"], "ready")
        self.assertEqual(report["stages"]["scenes"], "ready")

    def test_nondict_cue_is_reported_in_timing_stage(self):
        self.plan()
        path = self.project / "script.json"
        script = json.loads(path.read_text())
        script["scenes"][0]["cues"][0] = "bad cue"
        path.write_text(json.dumps(script))
        failed = self.cli("check", "--project", self.project, ok=False)
        report = json.loads(failed.stdout)
        self.assertIn("script and measured cue IDs/order differ", report["stages"]["timing"])
        self.assertNotIn("Traceback", failed.stderr)
        script["scenes"][0]["cues"][0] = {"id": "a", "say": "Question one"}
        path.write_text(json.dumps(script))
        report = json.loads(self.cli("check", "--project", self.project, ok=False).stdout)
        self.assertEqual(report["stages"]["timing"], "ready")

    def test_media_requires_completed_fresh_render(self):
        self.plan()
        self.cli("build-map", "--project", self.project)
        (self.project / "scenes").mkdir()
        scene = self.project / "scenes/intro.js"
        scene.write_text("// fixture scene\n")
        (self.project / "timeline.js").write_text("window.TIMELINE={};\n")
        (self.project / "narration.wav").write_bytes(b"fixture narration")
        (self.project / "audio").mkdir()
        (self.project / "audio/s00_a.mp3").write_bytes(b"fixture cue")
        (self.project / "final.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nFixture\n")
        # These are deliberately local schema fixtures, never production runtime receipts.
        role = {"model": "claude-opus-5-5", "effort": "high"}
        def receipt(requested, outcome):
            return {"requested": requested, "resolved": requested, "outcome": outcome,
                    "runtimeEvidence": "fixture://test-video-pipeline"}
        runs = {"version": 1, "author": receipt(role, "complete"),
                "builders": {"intro": receipt(role, "complete")},
                "reviewer": receipt({"model": "fixture-reviewer", "effort": "high"}, "passed")}
        (self.project / "video-runs.json").write_text(json.dumps(runs))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=32x32:r=1",
                        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=8000", "-t", "15",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(self.project / "final.mp4")],
                       check=True, capture_output=True, text=True)
        missing = json.loads(self.cli("check", "--project", self.project, ok=False).stdout)
        self.assertIn("RENDERED success marker", missing["stages"]["media"])
        marker = self.project / "RENDERED"
        marker.write_text("DONE\n")
        self.assertTrue(json.loads(self.cli("check", "--project", self.project).stdout)["ready"])
        newer = (self.project / "final.mp4").stat().st_mtime_ns + 1_000_000_000
        for path in (scene, self.project / "audio/s00_a.mp3", self.project / "script.json", self.project / "engine.js"):
            os.utime(path, ns=(newer, newer))
            stale = json.loads(self.cli("check", "--project", self.project, ok=False).stdout)
            self.assertIn("final.mp4 is stale", stale["stages"]["media"])
            os.utime(path, ns=(1, 1))
        mp4_time = newer + 1_000_000_000
        os.utime(self.project / "final.mp4", ns=(mp4_time, mp4_time))
        os.utime(self.project / "final.srt", ns=(mp4_time, mp4_time))
        marker_time = mp4_time + 1_000_000_000
        os.utime(marker, ns=(marker_time, marker_time))
        self.assertTrue(json.loads(self.cli("check", "--project", self.project).stdout)["ready"])

    def test_measured_map_has_distinct_gates_and_board_schema(self):
        self.plan()
        result = self.cli("build-map", "--project", self.project)
        self.assertIn("3 source-linked segments", result.stdout)
        mapping = json.loads((self.project / "video-0042.json").read_text())
        self.assertFalse(mapping["captionsBurnedIn"])
        self.assertEqual([(s["start"], s["end"]) for s in mapping["segments"]], [(0, 3), (3, 10), (10, 15)])
        self.assertEqual([s["practice"] for s in mapping["segments"][:2]],
                         [{"pauseAt": 1, "revealAt": 2}, {"pauseAt": 4, "revealAt": 5}])
        # The existing board validator consumes this exact manifest schema.
        media = self.workspace / "lessons/assets/0042-lecture.mp4"
        media.parent.mkdir()
        media.touch()
        ref = self.workspace / "reference"
        ref.mkdir()
        (ref / "video-0042.json").write_text(json.dumps(mapping), encoding="utf-8")
        spec = importlib.util.spec_from_file_location("lesson_video_import", ROOT / "bin/lesson_video.py")
        importer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(importer)
        verdict = importer.board_bridge().lesson_video("0042", str(self.workspace))
        self.assertTrue(verdict.get("available"), verdict)
        self.assertTrue(verdict.get("mappingValid"), verdict)
        self.cli("build-map", "--project", self.project, "--captions-burned-in", "--replace")
        verified = json.loads((self.project / "video-0042.json").read_text())
        self.assertTrue(verified["captionsBurnedIn"])

    def test_rounding_never_makes_segments_overlap(self):
        # measured scene boundaries that differ inside EPS used to round to a start 1 ms before the previous end
        self.plan()
        t = json.loads((self.project / "timeline.json").read_text())
        t["scenes"][0]["dur"] = 10.0006
        t["scenes"][1]["start"], t["scenes"][1]["dur"] = 9.9996, 5.0004
        (self.project / "timeline.json").write_text(json.dumps(t), encoding="utf-8")
        self.cli("build-map", "--project", self.project)
        segs = json.loads((self.project / "video-0042.json").read_text())["segments"]
        for a, b in zip(segs, segs[1:]):
            self.assertEqual(a["end"], b["start"])
            self.assertLess(b["start"], b["end"])

    def test_unpaired_or_grouped_questions_fail_before_map(self):
        anchors = self.plan()
        anchors["segments"][0]["to"] = "end"
        anchors["segments"].pop(1)
        (self.project / "anchors.json").write_text(json.dumps(anchors), encoding="utf-8")
        failure = self.cli("build-map", "--project", self.project, ok=False)
        self.assertIn("each question needs a distinct segment", failure.stderr)
        self.assertFalse((self.project / "video-0042.json").exists())

    def test_source_revision_blocks_reuse_and_check_names_missing_stages(self):
        self.plan()
        self.cli("build-map", "--project", self.project)
        incomplete = self.cli("check", "--project", self.project, ok=False)
        report = json.loads(incomplete.stdout)
        self.assertEqual(report["stages"]["map"], "ready")
        self.assertIn("video-runs.json", report["stages"]["receipts"])
        self.assertIn("final.mp4", report["stages"]["media"])
        self.lesson.write_text(self.lesson.read_text() + "New author correction\n", encoding="utf-8")
        changed = self.cli("build-map", "--project", self.project, ok=False)
        self.assertIn("lesson changed since init", changed.stderr)

    def test_invalid_derivation_step_is_rejected(self):
        anchors = self.plan()
        anchors["segments"][2]["step"] = 3
        (self.project / "anchors.json").write_text(json.dumps(anchors), encoding="utf-8")
        failure = self.cli("build-map", "--project", self.project, ok=False)
        self.assertIn("step requires line", failure.stderr)


if __name__ == "__main__":
    unittest.main()
