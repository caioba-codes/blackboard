"""prose_lint.py says out loud when the noun-stack check is skipped because spaCy is missing."""
import os, subprocess, sys, tempfile, unittest

PROSE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "prose_lint.py")


class SpacyMissing(unittest.TestCase):
    def test_skip_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            # a spacy module that fails to import stands in for "not installed", whatever this machine has
            with open(os.path.join(d, "spacy.py"), "w") as f:
                f.write("raise ImportError('no spacy')\n")
            lesson = os.path.join(d, "l.md")
            with open(lesson, "w") as f:
                f.write("# T\n\nA short clean sentence.\n")
            env = dict(os.environ, PYTHONPATH=d)
            err = subprocess.run([sys.executable, PROSE, lesson], capture_output=True, text=True, env=env).stderr
        self.assertIn("noun-stack check skipped: spaCy not installed", err)


if __name__ == "__main__":
    unittest.main()
