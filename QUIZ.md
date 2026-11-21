# Quiz

The practice in a lesson is what its blueprint says. STEM ([BLUEPRINT-STEM.md](./BLUEPRINT-STEM.md)): Your turns in every chapter, a mixed drill and a practice exam. Humanities ([BLUEPRINT-HUMANITIES.md](./BLUEPRINT-HUMANITIES.md)): Your turns, flashcards, a mixed set and a practice exam. Self-study ([BLUEPRINT-FUN.md](./BLUEPRINT-FUN.md)): an optional `::: quiz` of 2 to 3 questions at the end. There are no chapter checkpoints, and only the self-study blueprint has an end quiz. All items count toward the same lesson XP and are logged as usual.

Mixed drills and mixed sets do not name the type or the chapter to use. Keep the real source difficulty everywhere.

Generation and grading both run headless in `bin/quiz.py` (its prompts hold the flashcard writing and 1–5 grading rules), called by `bridge.py` in a background thread the same way `bin/explain.py` is. Neither wakes the interactive agent, so a quiz works identically in cmux, the Claude app and the Codex app, and nothing lands in the chat.

## Source fidelity (required; overrides generic item-writing preferences)

Before writing any lesson practice, More practice set or flashcard, inspect the user's relevant sources: practice exams, past exams, quizzes, problem sets, homework, and their answer keys. Match what the lesson actually teaches.

- **Official first.** Worked examples, Your turns, drills, practice exams and quizzes use official problems from the course's official sources (past exams, practice sets, homework, the official review, lecture slides), quoted as TEMPLATES.md **Problems and solutions** says. Write our own only when no official problem trains that skill, or the official one skips the fundamentals the lesson needs; label it `*Written by Claude*`. Never change an official problem's numbers.
- A free-response official problem stays free response (a Your turn), or becomes multiple choice only by adding options around its exact text.
- **Answer keys are checked.** Recompute every answer and every option independently of the official key; when the key is wrong, the lesson gives the right answer with a one-line note on the key's mistake.
- Record the actual source filename and question/page plus what changed in a Markdown comment immediately before each authored item. Never invent a source citation or claim to have read an unavailable question.
- Independently invent questions only when there are no relevant supplied question sources, such as a non-school lesson without user-provided material. First inspect the available sources; missing extraction/access is not evidence that no relevant source exists. If expected sources cannot be read, report that gap rather than silently inventing exam-style questions.
- Test only taught material, but retain the source difficulty.

## Multiple choice

- Stem is a complete question answerable before reading the options (cover-the-options test).
- Self-contained: every stem restates the facts it needs (the expression, the inputs, the table row, the circuit) so the student answers without scrolling back. Never "in problem 1", "from the example above" or a bare wire name like n2; write "For $W=\overline{R}S+T$ with $RST=111$…" instead.
- Code in a stem: TEMPLATES.md **Board rules** 7.
- Four options for our own items, exactly one correct (true/false keeps two; a verbatim official item keeps its own count). Each added distractor is a real, plausible mistake on that problem: a dropped sign, a wrong constant ($\tfrac{1}{a}$ for $a$), the wrong substitution or form, a forgotten chain-rule factor, a wrong bound. No joke options. Differentiate or simplify every distractor to make sure none is also correct. Spread the key over all four written positions across a lesson's items (the key letter is the key in written order; the board shuffles on render). Evaluate or derive every option before shipping. An equivalent expression is correct even when obtained in fewer or more steps; do not mark it wrong for skipping the preferred teaching sequence. If the stem asks for a specific intermediate step, state that constraint explicitly and ensure only one option meets it.
- Every distractor is a real misconception or a common procedural error, taken from the student's own quiz log when available.
- Options equal in length, grammar, specificity, and structure. No "all/none of the above", no negatives ("except"), no absolutes ("always/never").
- No word from the stem appearing only in the key. The key is not the longest or the middle option.
- At least half the items are application ("what would happen if…"), not recall.
- Randomise option order on render.
- Answers stay changeable on the board: the student can pick another option at any time and the newest pick is what counts (logged, restored on reload, XP). A wrong pick shows "Not quite" without revealing the key; the `why:` line appears once the right option is picked, in an olive callout like an Explain note. A `why:` with more than one step writes them down, not sideways: one short sentence, then `$$\begin{aligned} … \\ … \end{aligned}$$` on the same line, one operation per row.
- Wrong pick → one line naming the mistake behind that option, written after the option as `- option || the mistake`. The board shows it with the verdict, then the step reveal of the `why:`. No narration.
- A `why:` with worked steps is stepped on the board: after the right pick it opens at its first piece and **Next step** reveals one row at a time; after a wrong pick the verdict and the why's first sentence (the hint) show first, then the same steps. So the first sentence of a worked `why:` is a hint that does not give the key away.

## Logging

Every graded item appends one line to `learning-records/quiz-log.jsonl`:

```json
{"ts":"2026-09-02T19:40:11Z","lesson":"0004","topic":"simplifying SOP","mode":"cards","score":4,"misconception":null}
```

`misconception` is a short sentence describing the wrong belief when the score is ≤ 2, otherwise `null`. The grid's quiz dots read this file, and so will the redo rounds (ROADMAP.md). When a misconception appears twice, add a line to the current learning record under **Misconceptions** so later quizzes re-probe it in a new context.

## Board syntax for quiz items

Written inside the lesson's `::: quiz` block, after the `topics:` line. Plain headings, no decoration.

A flashcard carries its own answer and its own rubric. `answer:` is what the back shows. `must:` lines are what a correct answer has to contain; they stay off the front and are read by the grader.

```md
::: card c1
Why does $\int \csc^2(ax)\,dx$ carry a minus sign?
answer: It is $-\frac{1}{a}\cot(ax) + C$, and cotangent is a co-function; Rule 3 makes every co-function answer negative.
must: the answer is cotangent, a co-function
must: Rule 3 makes every co-function answer negative
:::
```

```md
### Question 1

::: mcq q1 c
Inputs $A = 1$, $B = 0$. Which expression evaluates to 1?
- $A \cdot B$ || AND needs both inputs at 1, and $B$ is 0.
- $\overline{A} + B$ || $\overline{A}$ is 0 and $B$ is 0, so the OR is 0.
- $A + B$
- $A \cdot \overline{A}$ || A variable AND its complement is always 0.
why: OR needs only one input at 1, and $A$ is 1.
:::

### Question 2

::: card r2
Two product terms share every variable except one. Why can you drop that variable?
must: the odd variable appears once true and once complemented
must: $X\overline{Y} + XY = X$, so it factors out
:::

::: score r2 4
*"because the one that changes is or'd with its complement so it's one"*

Missing: the rule has a name, $X\overline{Y} + XY = X$. Say it back in one sentence.
:::
```

`- option || mistake` gives that distractor its one-line feedback. `why:` is the solution: on a right pick it opens stepped; on a wrong pick only its first sentence shows, as a hint. Explain the operation or causal rule that produces the answer, not only its theorem name. Any explanation of a distractor must describe an error that could actually produce that distractor. Options are shuffled on render; the key letter (`a`/`b`/`c`) refers to the order written.
