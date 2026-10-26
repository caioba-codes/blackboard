"""Narrator selection and the Kokoro path of video/tts.py, with the model mocked (no weights, no API)."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import wave


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = {"title": "T", "voice": "eleven-voice", "chapters": ["Intro"], "scenes": [
    {"id": "s00", "chapter": 0, "visual": "", "cues": [
        {"id": "a", "say": "Pick u with LIATE. Then d u is two d x, and v is one fourth tan four x."},
        {"id": "think", "pause": 1},
        {"id": "b", "say": "Done."}]}]}


def load(project):
    shutil.copy2(ROOT / "video" / "tts.py", project / "tts.py")
    spec = importlib.util.spec_from_file_location(f"tts_{id(project)}", project / "tts.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fake_synth(jobs):
    """Stand-in for the Kokoro venv: 0.5 s of silence per piece plus the requested gaps, measured spans out."""
    out = []
    for job in jobs:
        t, spans = 0.0, []
        for gap in job["gaps"]:
            spans.append([round(t, 4), round(t + 0.5, 4)])
            t += 0.5 + gap
        with wave.open(job["tmp"], "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(b"\0\0" * int(t * 24000))
        out.append({"tmp": job["tmp"], "spans": spans})
    return out


class TtsEngineTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.project = Path(tmp.name)
        (self.project / "script.json").write_text(json.dumps(SCRIPT))
        env = {k: v for k, v in os.environ.items()
               if k not in ("ELEVENLABS_API_KEY", "BLACKBOARD_TTS_ENGINE", "BLACKBOARD_TTS_VOICE")}
        env["BLACKBOARD_TTS_HOME"] = str(self.project / "no-tts-home")
        patcher = patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.tts = load(self.project)
        os.makedirs(self.tts.AUD, exist_ok=True)

    def choose(self, available, **env):
        with patch.dict(os.environ, env), patch.object(self.tts, "kokoro_available", return_value=available):
            return self.tts.choose_engine(SCRIPT)[0]

    def test_kokoro_is_default_without_key(self):
        self.assertEqual(self.choose(True), "kokoro")

    def test_elevenlabs_with_key(self):
        self.assertEqual(self.choose(True, ELEVENLABS_API_KEY="k"), "elevenlabs")
        self.assertEqual(self.choose(False, ELEVENLABS_API_KEY="k"), "elevenlabs")

    def test_explicit_engine_wins(self):
        self.assertEqual(self.choose(True, ELEVENLABS_API_KEY="k", BLACKBOARD_TTS_ENGINE="kokoro"), "kokoro")
        self.assertEqual(self.choose(True, BLACKBOARD_TTS_ENGINE="elevenlabs"), "elevenlabs")

    def test_blocked_when_neither_with_install_hint(self):
        with self.assertRaises(self.tts.Stop) as cm:
            self.choose(False)
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("TTS_BLOCKED", str(cm.exception))
        self.assertIn("setup_tts.sh", str(cm.exception))

    def test_main_blocked_exit_2_and_check_still_reports(self):
        with self.assertRaises(self.tts.Stop) as cm:
            self.tts.main([])
        self.assertEqual(cm.exception.code, 2)
        self.assertEqual(self.tts.main(["--check"]), 1)

    def test_cached_elevenlabs_project_is_reused_without_key(self):
        for path, voice, text in self.tts.jobs_for(SCRIPT, "elevenlabs"):
            Path(path).write_bytes(b"mp3")
            Path(path + ".json").write_text(json.dumps({"hash": self.tts.cache_key(voice, text), "alignment": {"x": 1}}))
        self.assertEqual(self.choose(True), "elevenlabs")

    def test_voice_override(self):
        with patch.dict(os.environ, {"BLACKBOARD_TTS_VOICE": "bf_emma"}):
            self.assertEqual(self.tts.jobs_for(SCRIPT, "kokoro")[0][1], "bf_emma")
        self.assertEqual(self.tts.jobs_for(SCRIPT, "kokoro")[0][1], "af_heart")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs ffmpeg/ffprobe")
    def test_kokoro_run_measures_timeline_and_caches(self):
        with patch.object(self.tts, "kokoro_available", return_value=True), \
                patch.object(self.tts, "kokoro_synth", side_effect=fake_synth) as synth:
            self.assertEqual(self.tts.main([]), 0)
            tl = json.loads((self.project / "timeline.json").read_text())
            cues = tl["scenes"][0]["cues"]
            # cue a: pieces "Pick u with LIATE." (0.5) + 0.3 gap + second sentence (0.5) = 1.3 s, measured by ffprobe
            self.assertAlmostEqual(cues["a"]["e"] - cues["a"]["s"], 1.3, places=2)
            subs = tl["scenes"][0]["subs"]
            self.assertEqual(subs[0]["text"], "Pick u with LIATE.")
            self.assertAlmostEqual(subs[1]["s"] - subs[0]["s"], 0.8, places=2)
            self.assertEqual(self.tts.main(["--verify"]), 0)
            self.assertEqual(synth.call_count, 1)
            self.assertEqual(self.tts.main([]), 0)          # everything cached: no second synthesis
            self.assertEqual(synth.call_count, 1)
        self.assertTrue((self.project / "audio" / "s00_a.wav").exists())


if __name__ == "__main__":
    unittest.main()
