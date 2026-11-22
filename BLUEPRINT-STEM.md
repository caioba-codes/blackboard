# Blueprint: STEM exam lesson

For course mode in math, physics, engineering or CS. The lesson is built from the exam, not from the concepts. One lesson covers one whole exam. Shared rules are in TEMPLATES.md; the STEM-only writing rules are at the end of this file.

## Find the problem types

Read every past exam, practice exam, quiz and official review for this test. Group their problems into **problem types**: problems that are solved the same way. There are no concept chapters and no prerequisites section. A concept appears only inside the problem type that needs it, the first time it is needed.

Conceptual questions (true or false, "explain why") are included only when the past exams ask them. Then they are a problem type like any other.

**Problem sources, best first.** Past exams of this test; the official review or practice set; past exams and practice sets of the earlier tests in this course; the student's own graded exams; homework; lecture examples and knowledge checks. Use the best that exist. Sources names the ones used and says when no past exam of this test exists.

**Cumulative finals.** The types are those of the earlier tests plus those of the material taught since the last test. Weights come from what the syllabus or instructor says ("more questions on the newest material"). With no numbers, estimate a split: head the table `**Exam Topics Breakdown (estimate)**` and put one line under it saying it is an estimate and what it rests on ("Estimate: no point split exists; weighted toward the material since Test 3, as the syllabus says."). That line is required; `bin/lint.py` warns when an estimated breakdown lacks it. A type already taught in an earlier lesson gets one worked example and one Your turn; a new-material type gets the full chapter.

**A type with no official problem.** Use lecture examples, homework or knowledge checks. If none exist, write problems in the format of the nearest official ones, label them "Written by Claude", keep the type to one worked example and one Your turn, and say in Sources that no official problem exists for it.

## Size

There is no target length. The size is the number of problem types, times the variations actually seen, times the steps per solution. A type worth under about 5% of the points that appeared once gets one example and no variations.

Before writing, tell the user one line with the types, the examples and the number of sessions, for example "6 types, 11 examples, about 5 mornings". The user can then cut a type. A session is the length the user stated, most recent first, then MISSION.md or NOTES.md; 45 minutes when none is stated.

## Top of the lesson

Contents, then Sources, then the **Exam Topics Breakdown**: the percent of the exam for each problem type, averaged over the past exams (format in **STEM writing rules** below).

## One chapter per problem type

Chapters go in order of exam weight, the biggest first. A chapter is one study session. It stands on its own: it never depends on reading another chapter the same day, so a concept that two types need is stated in both.

**Oversized type.** When one type is a single large problem (a "write a class hierarchy" question worth most of the points), split it into chapters by the parts of the problem, each with its own worked example and Your turn, then one chapter that solves a whole problem start to finish. Each chapter still fits one session.

Inside a chapter, in this order:

1. **The problem.** One official problem of this type, verbatim, with its label, in a `::: given` block.
2. **What it asks.** In plain words, written for a student who does not know the fundamentals yet.
3. **What you need.** Only the concepts and formulas this problem uses, each stated once.
4. **Worked example A.** That problem solved from start to end. Every step is shown and labelled by what it does ("find the constructor that runs", "test the endpoints"). Each step has one line of why, and the final answer is boxed. A code answer's final answer is the complete code block shown last under **Final answer**, with nothing boxed inside the code; a "what does this print" answer boxes the output.
5. **Your turn.** An official near-copy, shown exactly as on the exam. The solution sits behind the step-by-step reveal.
6. **Variations.** For each variation of this type that really appeared on a past exam:
   - what is different, and the one extra concept it needs;
   - worked example B on an official problem that looks different but is solved the same way;
   - one line saying what A and B have in common;
   - a Your turn on the variation.

## After the chapters

1. **Mixed drill.** Official problems from all types, shuffled, with no type named. The first step of every solution is "which type is this".
2. **Practice exam.** One full official-style exam. One line at its top gives the time per question: (total minutes − 10) ÷ number of questions. With no official exam, assemble it from official problems in the proportions of the breakdown and label it "Assembled from official problems"; never present it as a real past exam. Each question stands on its own, as a real exam prints it: when it builds on a class or result from an earlier chapter, put that class or result inside the question's `::: given` card under a short context line ("Uses this class:"), never a pointer to the chapter.
3. **Cheat sheet.** Formulas only (**STEM writing rules** below).

There are no chapter checkpoints and no separate end quiz. The Your turns, the mixed drill and the practice exam are the practice.

## Redo rounds

Every Your turn, drill problem and practice-exam part ends its answer with **Got it** and **Missed it**, and the board logs the tap; a wrong multiple-choice pick counts as missed too. While a lesson has misses, a row under its title reads "N missed problems · Redo them". A study session starts there: Redo them shows only the missed problems, each under its own label and problem text, then the session continues with the next new chapter. A Got it drops a problem from the next round; **Next round** shows what is still missed. The rounds stop at "No misses left." Every problem needs its label above it (TEMPLATES.md **Problems and solutions**) so the round can show it whole.

## STEM writing rules

- **Worked examples are annotated.** Each step's label says what the step does, and its why sits in the right margin of the derivation (`&& \text{…}`). Labels on the math (`\underbrace`, `\overset`, a boxed $u$/$du$/$dv$/$v$ grid) are fine; a prose list of steps is not. The final answer is boxed.
- **Every result produced by a rule carries its rule.** Wrap the result in `\why{<math>}{<rule>}` (optionally `\why[short name]{<math>}{<rule>}`): the board shows the math with a faint dotted underline, and a tap opens the rule in a small popup. Use it in setup boxes, derivation steps, worked examples and your-turn answers. The hint is the GENERAL rule, never the specific computation: `du = \why{5\,dx}{\tfrac{d}{dx}(kx) = k}`, `v = \why{\tfrac13\tan(3x)}{\int\sec^{2}(ax)\,dx = \tfrac{1}{a}\tan(ax) + C}`. Check every rule is right. Copy, Explain, search and the Kindle book see only the plain math.
- **Size encodes importance: three levels, never hand-sized.** Level 1 (`::: big` around a display or a table) is the one or two fundamental rules or mnemonics a chapter rests on, as a big visual (LIATE, the trig-sub forms, the decomposition shapes, the p-rule); at most two per chapter. Level 2 (`::: key`) is a tool or key formula, about 1.4× ($\int u\,dv = uv - \int v\,du$, L'Hôpital's rule). Everything else is level 3, the normal size. Never write `\Large`, `\Huge` or `\small` to size math (`bin/lint.py` flags them); put labels under a formula with `\underset{label}{…}`, which sets them in the smaller script size on its own.

  ```md
  ::: big
  $$\underset{x \,=\, a\sin\theta}{a^{2}-x^{2}}\qquad\underset{x \,=\, a\tan\theta}{a^{2}+x^{2}}$$
  :::
  ```
- **Draw what the key draws.** When the problem has a diagram and its human solution is a drawing (mux or decoder wiring, a circuit, a K-map, a timing diagram, a truth table filled in visually), the solution draws too, step by step: step 1 draws the part with `::: fig` (`raw` SVG, or `kmap`/`wave`), each later step's figure builds on the last one's drawing and marks what it added in the accent, then the calculation, then a step that points at the drawing ("$I_0$ passes to $Y$ because $S_1S_0=00$"). Show each drawing in the solution where its step is, so the board's **Next step** reveal shows it in order. Problems whose solution is only algebra or arithmetic keep the plain format. The video follows the same order.
- **Cheat sheet chapters are formulas to memorize, never prose.** Wrap the chapter in `::: sheet`, one `::: group <Method>` card per method in chapter order (the board lays the cards out as a two-column sheet when there is room). Inside a card: its formulas as display math, one per line, aligned on `=` where useful, each with a muted 1–4 word tag after `&&` ("Pythagorean", "p-rule"); level 2 (`::: key`) for the key formulas; a small board table where the content is tabular (the trig-power cases); at most one small `::: callout` per card and two or three in the whole sheet, only for a real grading trap. No sentences, no bold-label paragraphs.

  ```md
  ::: sheet
  ::: group Trig integrals
  $$\begin{aligned}
  \sin^{2}x + \cos^{2}x &= 1 &&\text{Pythagorean} \\
  \sin^{2}x &= \tfrac{1}{2}(1 - \cos 2x) &&\text{power reducing}
  \end{aligned}$$
  :::
  :::
  ```
- **Exam Topics Breakdown**, right after Sources: a bold `**Exam Topics Breakdown**` line, then a three-column table with one row per problem type, then one short line naming the past exams it averages.

  ```md
  **Exam Topics Breakdown**

  | Problem type | % of exam | Shape it takes |
  |---|---:|---|
  | Improper integrals | 28% | evaluate $\int_a^{\infty}$ with parts or a $u$ inside |
  | L'Hôpital limits | 2% | one limit; check the form first |

  Average over past second exams: Summer 2023, Fall 2017, Fall 2018, Spring 2019.
  ```

  Percentages, never points. For each past exam, divide each problem type's points by that exam's in-scope total (bonus left out), then average across the exams and round so the column adds up to 100. If only one exam has a point split, use it alone and say so. Rows go from the biggest weight to the smallest, in chapter order. The shape column says in a few words what the problems look like, with neutral wording.
