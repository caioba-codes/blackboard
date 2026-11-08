"""Lesson video captions in the lesson's notation: say/show alignment, the spelled-math lint, the caption track that
build-map writes and lesson_video.py installs, the display-only fingerprint, the practice-reading warning, and frames
that carry neither captions (unless asked) nor a progress bar."""

import importlib.util
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import captions  # noqa: E402
import test_video_pipeline as vp  # noqa: E402
import test_video_tts as vt  # noqa: E402


def load_tts():
    spec = importlib.util.spec_from_file_location("tts_for_captions", ROOT / "video" / "tts.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def subs_for(say, t0=0.0):
    """Timed say chunks exactly as tts.py makes them: one per piece, 1 s each."""
    return [{"text": say[a:b + 1].strip(), "s": t0 + i, "e": t0 + i + 0.9} for i, (a, b) in enumerate(load_tts().pieces(say))]


class AlignTest(unittest.TestCase):
    def test_sentences_are_tts_pieces_grouped(self):
        tts, rnd = load_tts(), random.Random(7)
        words = ["Row", "five", "is", "zero", "and", "I", "five", "x", "one", "two"]
        for _ in range(400):
            text = " ".join(rnd.choice(words) + rnd.choice(["", "", ",", ".", ":", "?", "!"]) for _ in range(rnd.randint(1, 40)))
            self.assertEqual([p for s in captions.sentences(text) for p in s], tts.pieces(text), text)

    def test_show_takes_the_times_of_its_say_sentence(self):
        say = "Row five: I five is zero. Row six: I six is one."
        show = "Row 5: $I_5 = 0$. Row 6: $I_6 = 1$."
        out = captions.align(say, show, subs_for(say))
        self.assertEqual([c["text"] for c in out], ["Row 5:", "$I_5 = 0$.", "Row 6:", "$I_6 = 1$."])
        self.assertEqual([c["s"] for c in out], [0, 1, 2, 3])

    def test_math_and_decimals_never_end_a_show_sentence(self):
        say = "A half is zero point five. Done."
        show = "A half is $0.5$. Done."
        self.assertEqual([c["text"] for c in captions.align(say, show, subs_for(say))], ["A half is $0.5$.", "Done."])
        say = "Sigma m of one, two, three, six. Next."
        show = "$F: \\Sigma m(1,2,3,6)$. Next."
        self.assertEqual(len(captions.align(say, show, subs_for(say))), 2)

    def test_long_sentence_keeps_its_comma_split_or_shows_whole(self):
        say = ("So the data inputs, I zero through I seven, are zero, one, one, one, zero, zero, one, zero, "
               "which is the whole design.")
        subs = subs_for(say)
        self.assertGreater(len(subs), 1)
        whole = captions.align(say, "So the data inputs are 01110010.", subs)
        self.assertEqual(len(whole), 1)
        self.assertEqual((whole[0]["s"], whole[0]["e"]), (subs[0]["s"], subs[-1]["e"]))
        same = ("So the data inputs, $I_0$ through $I_7$, are 0, 1, 1, 1, 0, 0, 1, 0, which is the whole design.")
        # commas inside the digit list do not split (they are not followed by a word in the say text the same way):
        # whatever the split, the chunks cover the same time span and keep the show text in order
        out = captions.align(say, same, subs)
        self.assertEqual(" ".join(c["text"] for c in out), same)
        self.assertEqual((out[0]["s"], out[-1]["e"]), (subs[0]["s"], subs[-1]["e"]))

    def test_sentence_count_mismatch_falls_back_to_whole_cue(self):
        say = "One. Two. Three."
        out = captions.align(say, "One and two. Three.", subs_for(say))
        self.assertEqual(out, [{"s": 0, "e": 2.9, "text": "One and two. Three."}])


class LintTest(unittest.TestCase):
    def test_spelled_math_is_flagged(self):
        for text in ("I five is zero.", "S one and S zero", "two to the n minus one", "x squared", "C sub 2",
                     "C in and C out", "A bar plus B prime", "F equals sigma m of one", "zero point five",
                     "x plus y", "one over two"):
            self.assertTrue(captions.spelled_math(text), text)

    def test_notation_and_english_pass(self):
        for text in ("$I_5 = 0$.", "Rows 1, 2, 3 and 6 get a 1.", "That's seven bits.", "A four bit adder.",
                     "a two-input gate", "B in series", "A bar over a letter means NOT.", "the mux's select bar",
                     "One $\\mathrm{Sub}$ wire", "Write the eight rows, 0 through 7."):
            self.assertEqual(captions.spelled_math(text), [], text)

    def test_lint_script_reports_missing_and_spelled(self):
        script = {"scenes": [{"id": "s", "cues": [{"id": "a", "say": "I five"}, {"id": "b", "say": "x", "show": "I five"},
                                                 {"id": "p", "pause": 3}]}]}
        missing, found = captions.lint_script(script)
        self.assertEqual(missing, ["s.a"])
        self.assertEqual(found[0][:2], ("s.b", "letter and number word"))


class TrackTest(unittest.TestCase):
    def test_track_is_absolute_and_uses_show_or_falls_back_to_say(self):
        say = "Row five: I five is zero."
        script = {"scenes": [{"id": "s0", "cues": [{"id": "a", "say": say, "show": "Row 5: $I_5 = 0$."}, {"id": "w", "pause": 2},
                                                   {"id": "b", "say": "Done."}]}]}
        subs = subs_for(say, 0.5) + [{"text": "Done.", "s": 5.0, "e": 5.5}]
        timeline = {"total": 20.0, "scenes": [{"id": "s0", "start": 10.0, "dur": 10.0, "subs": subs,
                                               "cues": {"a": {"s": .5, "e": 2.4}, "w": {"s": 2.8, "e": 4.8, "pause": True}, "b": {"s": 5.0, "e": 5.5}}}]}
        t = captions.track(script, timeline, "0042")
        self.assertEqual([(c["s"], c["text"]) for c in t["cues"]], [(10.5, "Row 5:"), (11.5, "$I_5 = 0$."), (15.0, "Done.")])
        captions.valid_track(t, "0042", 20.2)
        with self.assertRaises(ValueError):
            captions.valid_track(t, "0043")
        with self.assertRaises(ValueError):
            captions.valid_track(dict(t, extra=1), "0042")
        captions.valid_track(dict(t, progressBarBurnedIn=True), "0042")
        over = {"s0.a": "Row 5: $I_{5}=0$."}
        self.assertEqual(captions.track(script, timeline, "0042", over)["cues"][1]["text"], "$I_{5}=0$.")


class SpokenFingerprintTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs ffmpeg/ffprobe")
    def test_a_caption_edit_keeps_the_narration_valid_but_a_say_edit_does_not(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)
            script = json.loads(json.dumps(vt.SCRIPT))
            script["scenes"][0]["cues"][0]["show"] = "Pick $u$ with LIATE. Then $du = 2\\,dx$, and $v = \\tfrac14\\tan 4x$."
            (project / "script.json").write_text(json.dumps(script))
            env = {k: v for k, v in os.environ.items() if k not in ("ELEVENLABS_API_KEY", "BLACKBOARD_TTS_ENGINE")}
            env.update(BLACKBOARD_TTS_HOME=str(project / "none"), BLACKBOARD_ELEVENLABS_KEY_FILE=str(project / "no-key"))
            with patch.dict(os.environ, env, clear=True):
                tts = vt.load(project)
                os.makedirs(tts.AUD, exist_ok=True)
                with patch.object(tts, "kokoro_available", return_value=True), patch.object(tts, "kokoro_synth", side_effect=vt.fake_synth):
                    self.assertEqual(tts.main([]), 0)
                self.assertEqual(tts.main(["--verify"]), 0)
                script["scenes"][0]["cues"][0]["show"] = "Pick $u$ by LIATE. Then $du=2\\,dx$, and $v=\\frac14\\tan 4x$."
                (project / "script.json").write_text(json.dumps(script))
                self.assertEqual(tts.main(["--verify"]), 0, "a caption edit needs no narration or render")
                script["scenes"][0]["cues"][1:2] = []
                script["scenes"][0]["cues"][0]["say"] += " Again."
                (project / "script.json").write_text(json.dumps(script))
                self.assertEqual(tts.main(["--verify"]), 1, "a narration edit does")
                bad = json.loads(json.dumps(vt.SCRIPT))
                bad["scenes"][0]["cues"][1]["show"] = "a pause has no caption"
                (project / "script.json").write_text(json.dumps(bad))
                with self.assertRaises(tts.Stop):
                    tts.load_script(str(project / "script.json"))


class PipelineCaptionsTest(unittest.TestCase):
    setUp, cli, init = vp.VideoPipelineTest.setUp, vp.VideoPipelineTest.cli, vp.VideoPipelineTest.init

    def plan(self):
        """The pipeline test's project, with one measured subtitle chunk per spoken cue."""
        anchors = vp.VideoPipelineTest.plan(self)
        script = json.loads((self.project / "script.json").read_text())
        timeline = json.loads((self.project / "timeline.json").read_text())
        for sc, tsc in zip(script["scenes"], timeline["scenes"]):
            tsc["subs"] = [{"text": c["say"], "s": tsc["cues"][c["id"]]["s"], "e": tsc["cues"][c["id"]]["e"]} for c in sc["cues"] if "say" in c]
        (self.project / "timeline.json").write_text(json.dumps(timeline))
        return anchors

    def report(self):
        return json.loads(self.cli("check", "--project", self.project, ok=False).stdout)

    def test_build_map_writes_the_track_and_check_wants_notation(self):
        self.plan()
        self.cli("build-map", "--project", self.project)
        track = json.loads((self.project / "captions.json").read_text())
        self.assertEqual((track["lessonId"], track["video"], track["duration"]), ("0042", "0042-lecture.mp4", 15))
        self.assertTrue(self.report()["stages"]["captions"].startswith("ready"))
        script = json.loads((self.project / "script.json").read_text())
        script["scenes"][1]["cues"][0]["show"] = "S one equals one"
        (self.project / "script.json").write_text(json.dumps(script))
        self.assertIn("spell math in words", self.report()["stages"]["captions"])
        del script["scenes"][1]["cues"][0]["show"]
        (self.project / "script.json").write_text(json.dumps(script))
        self.assertIn("s01.a", self.report()["stages"]["captions"])
        script["scenes"][1]["cues"][0]["show"] = "Summary of $S_1$"
        (self.project / "script.json").write_text(json.dumps(script))
        self.assertIn("stale", self.report()["stages"]["captions"])
        self.cli("build-map", "--project", self.project)
        self.assertTrue(self.report()["stages"]["captions"].startswith("ready"))

    def test_a_your_turn_that_reads_the_question_is_warned(self):
        self.plan()
        self.cli("build-map", "--project", self.project)
        self.assertEqual(self.report()["warnings"], [])
        script = json.loads((self.project / "script.json").read_text())
        script["scenes"][0]["cues"][0]["say"] = "Your turn. Here we have a mux whose select lines are A and B, find F for every row."
        (self.project / "script.json").write_text(json.dumps(script))
        warnings = self.report()["warnings"]
        self.assertEqual(len(warnings), 1)
        self.assertIn("practice q1", warnings[0])

    def test_captions_command_installs_only_the_track(self):
        self.plan()
        self.cli("build-map", "--project", self.project)
        ws = self.workspace
        (ws / "lessons/assets").mkdir()
        (ws / "lessons/assets/0042-lecture.mp4").write_bytes(b"video")
        (ws / "reference").mkdir(exist_ok=True)   # init already made it for the progress pointer
        shutil.copy2(self.project / "video-0042.json", ws / "reference/video-0042.json")
        cli = ROOT / "bin/lesson_video.py"
        run = lambda *a: subprocess.run([sys.executable, str(cli), *map(str, a)], capture_output=True, text=True)
        track = self.project / "captions.json"
        r = run("captions", "--workspace", ws, "--lesson", "0042", "--captions", track)
        self.assertEqual(r.returncode, 0, r.stderr)
        installed = ws / "lessons/assets/0042-lecture.captions.json"
        self.assertEqual(installed.read_bytes(), track.read_bytes())
        status = json.loads(run("status", "--workspace", ws, "--lesson", "0042").stdout)
        self.assertTrue(status["captionsExist"])
        changed = json.loads(track.read_text())
        changed["cues"][0]["text"] = "Question $1$"
        other = self.project / "fixed.json"
        other.write_text(json.dumps(changed))
        self.assertNotEqual(run("captions", "--workspace", ws, "--lesson", "0042", "--captions", other).returncode, 0)
        r = run("captions", "--workspace", ws, "--lesson", "0042", "--captions", other, "--replace")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(list((ws / "lessons/assets").glob("0042-lecture.captions.json.bak-*"))), 1)
        wrong = dict(changed, duration=99)
        other.write_text(json.dumps(wrong))
        self.assertIn("differs from the video map", run("captions", "--workspace", ws, "--lesson", "0042", "--captions", other, "--replace").stderr)


class FrameTest(unittest.TestCase):
    def test_frames_have_no_progress_bar_and_captions_only_on_request(self):
        video = ROOT / "video"
        for name in ("index.html", "style.css", "engine.js"):
            text = (video / name).read_text()
            self.assertIsNone(re.search(r"id=\"prog|#prog|getElementById\('prog", text), f"{name} draws a progress bar")
        engine = (video / "engine.js").read_text()
        self.assertIn("if (window.BURN_CAPTIONS)", engine)
        self.assertIn("window.BURN_CAPTIONS = q.has('burn')", (video / "index.html").read_text())
        capture = (video / "capture.mjs").read_text()
        self.assertIn("process.env.VIDEO_BURN_CAPTIONS === '1'", capture)
        self.assertIn("if (BURN) plan.captions = 'burned'", capture)


if __name__ == "__main__":
    unittest.main()
