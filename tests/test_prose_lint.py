"""prose_lint.py flags hard-to-read prose and terms used before they are explained."""
import os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LINT = os.path.join(HERE, "..", "bin", "prose_lint.py")
sys.path.insert(0, os.path.join(HERE, "..", "bin"))
from prose_lint import check_text  # noqa: E402

LESSON = """---
title: t
---
# T

*Why does absorption work?*

Simplify with absorption first. Then use the SOP form.

The method swallows the error. Plug in the root you found.

**Absorption** means $A + AB = A$.

SOP (sum of products) is an OR of ANDs. The carry bit is 1.

$$x = 1$$
"""


class ProseLint(unittest.TestCase):
    def run_lint(self, text):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(text)
        try:
            return subprocess.run([sys.executable, LINT, f.name], capture_output=True, text=True).stderr
        finally:
            os.unlink(f.name)

    def test_order_and_patterns(self):
        out = self.run_lint(LESSON)
        self.assertIn('line 8: "Absorption" is used here but explained on line 12', out)
        self.assertIn('line 8: "SOP" is used here but explained on line 14', out)
        self.assertIn('"The method swallows"', out)
        self.assertIn('"the root you found"', out)
        self.assertNotIn("carry bit", out)          # "bit" is a noun here, not a verb
        self.assertNotIn("line 6", out)             # the opening question may preview terms

    def test_clean_text(self):
        self.assertEqual(check_text("You found the root $x = 2$. Plug it in."), [])

    def test_long_sentence(self):
        long = " ".join(["word"] * 30) + "."
        self.assertTrue(any("30-word sentence" in w for w in check_text(long)))


if __name__ == "__main__":
    unittest.main()
