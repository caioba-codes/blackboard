"""lint.py finds a src: file whose name has spaces, written URL-encoded (%20) in the label link."""
import os, subprocess, sys, tempfile, unittest

LINT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "lint.py")


class SrcExists(unittest.TestCase):
    def lint(self, link):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "sources"))
            os.makedirs(os.path.join(d, "lessons"))
            open(os.path.join(d, "sources", "Final Exam 2024.pdf"), "w").close()
            lesson = os.path.join(d, "lessons", "l.md")
            with open(lesson, "w") as f:
                f.write(f"# T\n\n## Problem 1\n\n[Official · Final 2024, Q1]({link})\n")
            return subprocess.run([sys.executable, LINT, lesson], capture_output=True, text=True).stderr

    def test_encoded_space_is_found(self):
        self.assertNotIn("is not a file", self.lint("src:Final%20Exam%202024.pdf#page=2"))

    def test_missing_file_still_warns(self):
        self.assertIn("label source Missing%20File.pdf is not a file", self.lint("src:Missing%20File.pdf"))


if __name__ == "__main__":
    unittest.main()
