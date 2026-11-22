"""lint.py rules from the CS 1331 final: Written by Claude cards, self-contained practice-exam questions,
official code exempt from the 60-character line rule, and the required estimate line."""
import os, subprocess, sys, tempfile, unittest

LINT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "lint.py")
LONG = "public class Pet { private int age; public Pet(int a) { age = a; } public int getAge() { return age; } }"


def lint(body):
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "sources")); os.makedirs(os.path.join(d, "lessons"))
        open(os.path.join(d, "sources", "f.pdf"), "w").close()
        lesson = os.path.join(d, "lessons", "l.md")
        with open(lesson, "w") as f:
            f.write("# T\n\n## Chapter 1 · X\n\n" + body)
        return subprocess.run([sys.executable, LINT, lesson], capture_output=True, text=True).stderr


CHECKIN = "\n::: checkin\n- Write it. || done\n:::\n"


class WrittenByClaude(unittest.TestCase):
    def test_statement_in_given_card_is_clean(self):
        self.assertEqual(lint("*Written by Claude*\n\n::: given\nWrite `sum(a, b)`.\n:::\n" + CHECKIN), "")

    def test_statement_outside_given_warns(self):
        self.assertIn("Written by Claude problem's statement outside a ::: given block",
                      lint("*Written by Claude*\n\nWrite `sum(a, b)`.\n" + CHECKIN))

    def test_bold_worked_example_line_may_precede_the_card(self):
        self.assertEqual(lint("*Written by Claude*\n\n**Worked example A.**\n\n::: given\nWrite `sum(a, b)`.\n:::\n" + CHECKIN), "")

    def test_mcq_under_label_is_clean(self):
        self.assertEqual(lint("*Written by Claude*\n\n::: mcq q1 a\nStem\n- a\n- b\n- c\n- d\n:::\n"), "")


class SelfContainedQuestion(unittest.TestCase):
    def test_context_line_and_class_inside_given(self):
        body = ("[Official · Final 2024, Q3](src:f.pdf#page=2)\n\n::: given\nUses this class:\n\n```java\n"
                + LONG + "\n```\n\nWrite a subclass `Dog` of `Pet`.\n:::\n" + CHECKIN)
        self.assertEqual(lint(body), "")


class CodeLineLength(unittest.TestCase):
    def test_official_code_in_given_is_exempt(self):
        body = "[Official · Final 2024, Q1](src:f.pdf#page=1)\n\n::: given\n```java\n" + LONG + "\n```\n:::\n" + CHECKIN
        self.assertNotIn("code line", lint(body))

    def test_official_mcq_stem_code_is_exempt(self):
        body = ("[Official · Final 2024, Q2](src:f.pdf#page=1)\n\n::: mcq q2 a\n```java\n" + LONG
                + "\n```\nWhich is true?\n- a\n- b\n- c\n- d\n:::\n")
        self.assertNotIn("code line", lint(body))

    def test_our_code_over_60_warns(self):
        self.assertIn("a code line of", lint("Our solution:\n\n```java\n" + LONG + "\n```\n"))

    def test_indented_answer_code_counts_from_the_fence(self):
        ok = "  " + "x" * 58
        self.assertNotIn("code line", lint("::: checkin\n- Q *Written by Claude* || ```java\n" + ok + "\n  ```\n:::\n"))


class EstimateLine(unittest.TestCase):
    TABLE = "**Exam Topics Breakdown (estimate)**\n\n| Problem type | % of exam | Shape it takes |\n|---|---:|---|\n| A | 60% | a |\n| B | 40% | b |\n\n"

    def test_estimate_line_present(self):
        self.assertNotIn("estimate line", lint(self.TABLE + "Estimate: no point split exists; weighted toward the new material.\n"))

    def test_estimate_line_missing_warns(self):
        self.assertIn("without its estimate line", lint(self.TABLE + "## Chapter 2 · Y\n"))


if __name__ == "__main__":
    unittest.main()
