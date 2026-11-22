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


class FromLesson0009(unittest.TestCase):
    """Cases from the first real lesson that used step sources (CS 1331 final)."""

    def test_problem_over_two_pages_cites_either_card(self):
        body = ("[Official · Exam 2, Q13 p.22](src:x.pdf#page=22)\n\n::: given\nA [`Shelter` holds pets]{#shelter}.\n:::\n\n"
                "[Official · Exam 2, Q14 p.24](src:x.pdf#page=24)\n\n::: given\n[Write `adopt`]{#adopt}.\n:::\n\n"
                "Start from the class on page 22. {@shelter}\n\n$$x = 1$$\n\nThen the method page 24 asks for. {@adopt}\n")
        out = run(LINT, body)
        self.assertNotIn("cites {@shelter}", out)
        self.assertNotIn("(soft)", out)

    def test_worked_example_under_a_subheading_is_scanned(self):
        body = (PROBLEM + "### What it asks\n\nBuild the machine.\n\n### Worked example A\n\n" + SOLVED)
        self.assertNotIn("(soft)", run(LINT, body))

    def test_code_lines_in_range(self):
        body = ("*Written by Claude*\n\n::: given\n```java\nint a = 1;\nint b = a + 1;\nSystem.out.println(b);\n```\n:::\n\n"
                "Line 2 adds one to `a`. {@L2}\n\n$$b = 2$$\n")
        self.assertEqual(run(LINT, body), "")
        self.assertIn("{@L4-5} is outside the code block, which has 3 lines", run(LINT, body.replace("{@L2}", "{@L4-5}")))

    def test_two_blocks_need_a_name(self):
        two = ("*Written by Claude*\n\n::: given\n```java {#node}\nclass Node {}\n```\n\n```java\nint x;\nint y;\n```\n:::\n\n")
        self.assertIn("is ambiguous", run(LINT, two + "Line 1. {@L1}\n"))
        self.assertEqual(run(LINT, two + "The class. {@node:L1}\n\n$$x = 1$$\n"), "")
        self.assertIn("has no code block named {#leaf}", run(LINT, two + "x {@leaf:L1}\n"))

    def test_mcq_stem_tags_cited_from_its_why(self):
        body = ("*Written by Claude*\n\n::: mcq q1 a\nWhat does [`a.length` return]{#len}?\n- 3\n- 2\n- 4\n- 0\n"
                "why: The stem asks for the length. {@len}\n:::\n")
        self.assertEqual(run(LINT, body), "")
        self.assertIn("cites {@size}", run(LINT, body.replace("{@len}", "{@size}")))

    def test_line_like_tag_name_warns(self):
        self.assertIn("looks like a line reference", run(LINT, "*Written by Claude*\n\n::: given\n[x]{#L3}\n:::\n"))


class Prose(unittest.TestCase):
    def test_refs_and_tags_are_not_words(self):
        out = run(PROSE, PROBLEM + SOLVED)
        self.assertNotIn("@start", out)
        self.assertNotIn("{#", out)


if __name__ == "__main__":
    unittest.main()
