"""lint.py checks step sources: every {@id} names a phrase tagged [..]{#id} in its own problem; a lesson that tags its
problems gets a soft note for a solved problem with no step citing it."""
import os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LINT = os.path.join(HERE, "..", "bin", "lint.py")
PROSE = os.path.join(HERE, "..", "bin", "prose_lint.py")


def run(tool, body):
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "lessons"))
        lesson = os.path.join(d, "lessons", "l.md")
        with open(lesson, "w") as f:
            f.write("# T\n\n## Chapter 1 · X\n\n" + body)
        return subprocess.run([sys.executable, tool, lesson], capture_output=True, text=True).stderr


PROBLEM = "*Written by Claude*\n\n::: given\nThe machine [starts in state E]{#start} and [outputs 1 on 101]{#out}.\n:::\n\n"
SOLVED = ("Start at E, from the first line. {@start}\n\n"
          "$$\\begin{aligned}\nE &\\to B && \\text{the output needs 101} {@out} \\\\\nB &\\to C && \\text{next input}\n\\end{aligned}$$\n")


class Refs(unittest.TestCase):
    def test_cited_tags_are_clean(self):
        self.assertEqual(run(LINT, PROBLEM + SOLVED), "")

    def test_unknown_tag_warns(self):
        self.assertIn("cites {@end} but its problem has no phrase tagged {#end}", run(LINT, PROBLEM + "Stop. {@end}\n"))

    def test_tag_of_another_problem_does_not_count(self):
        other = "*Written by Claude*\n\n::: given\nAdd two numbers.\n:::\n\nAdd them. {@start}\n"
        self.assertIn("cites {@start}", run(LINT, PROBLEM + SOLVED + "\n" + other))

    def test_code_is_not_read_for_refs(self):
        self.assertEqual(run(LINT, PROBLEM + SOLVED + "\n```java\nString s = \"{@nope}\";\n```\n"), "")


class SoftNote(unittest.TestCase):
    def test_solved_problem_without_refs_gets_a_soft_note(self):
        bare = "*Written by Claude*\n\n::: given\nFind x.\n:::\n\n$$x = 2$$\n"
        out = run(LINT, PROBLEM + SOLVED + "\n" + bare)
        self.assertIn("(soft) this solved problem has no step citing its problem", out)
        self.assertNotIn("warning(s)", out, "a soft note is not counted as a warning")

    def test_lesson_without_tags_gets_no_note(self):
        self.assertEqual(run(LINT, "*Written by Claude*\n\n::: given\nFind x.\n:::\n\n$$x = 2$$\n"), "")


class Prose(unittest.TestCase):
    def test_refs_and_tags_are_not_words(self):
        out = run(PROSE, PROBLEM + SOLVED)
        self.assertNotIn("@start", out)
        self.assertNotIn("{#", out)


if __name__ == "__main__":
    unittest.main()
