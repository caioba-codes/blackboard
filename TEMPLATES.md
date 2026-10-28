# Lesson template

Every lesson is one markdown file, `lessons/NNNN-slug.md`, rendered on the board. There is one template, for STEM lessons (math, physics, engineering, CS): the rules below, **STEM lessons**, and the full model lesson [examples/stem/learn/lessons/0001-how-to-ace-your-second-integral-calculus-test.md](./examples/stem/learn/lessons/0001-how-to-ace-your-second-integral-calculus-test.md). Copy its structure, block types and format for any STEM lesson. A template for conceptual or memorization courses comes later; until then, use the same frame and rules and skip the STEM-only parts.

## Board rules

1. One idea per block. A block is a paragraph, a display equation, a figure, or a toggle. Never two mechanisms in one block.
2. Question before answer. The reader sees the question, then predicts, then the answer appears.
3. Picture beside the step it explains. Labels on the picture, not in prose.
4. Fixed slots. Same geometry every lesson: front matter → `# title` → Prerequisites dropdown → short Contents → Sources dropdown → one-line question (not in STEM lessons) → conditional check-in → numbered chapters with checkpoints → `## Quiz` → `## Extra` (self-study, only if a video was used).
5. Erase, don't add. Word caps below are real. Anything off-path is cut.
6. Every lesson ships with its quiz: 1–2 checkpoint `::: mcq` items after each chapter and 2–3 mixed ones in `## Quiz` (QUIZ.md), written before calling the lesson done. The student never has to generate anything to start revising. Each item restates the expression, inputs or figure facts it depends on, so it is answerable without scrolling back into the lesson. The "More practice" panel below them generates flashcards or more multiple choice, on one sub-topic or on all of them.
7. Name the actual writer fully. Follow SKILL.md’s **Author byline** contract: `model:` includes family/version, variant, and reasoning effort when available, e.g. `GPT-6 Astra Medium`. The title byline must preserve the full value.
8. Code lines stay at or under 60 characters, so a block fits the column at any zoom. An explanatory comment goes on its own line above the statement it explains, at the same indentation, never trailing a long line. Wrap anything longer. In an `::: interactive` trace, shorten comments rather than add lines, so the step line numbers stay right.
9. Code in a question: a stem, check-in question or answer that shows more than one statement of code puts that code in a fenced ```java block, formatted as real code with line breaks and indentation, then the question sentence on its own line after it. Never inline a class or several statements into a sentence. A single short expression stays inline in backticks.

## Didactic writing contract

Use these conventions for lessons and rewrites. They capture what worked in practice: small understandable steps, with the reason visible. Scale the depth to demonstrated knowledge and the task; coverage alone is not evidence that a prerequisite is understood. For questions asked in chat, follow SKILL.md's **Chat answers**.

### Shape of each explanation

Every explanation follows the same order, from a whole chapter down to a single step:

1. **What you need first.** The prerequisites, each explained in plain words before it is used.
2. **The tool.** Any formula or rule the example will apply, stated briefly (e.g. $\int u\,dv = uv - \int v\,du$).
3. **How to choose or set it up.** The decision the student makes before using the tool (e.g. LIATE for $u$). For a rule with cases, go case by case.
4. **ONE labeled worked example**, steps as labels on the math, final answer boxed.
5. **Your turn.** A near-copy with the answer hidden: this is the quick check, a question for the student, never a verification paragraph.
6. **Summary or generalization**, only if it adds something the example did not show.

An example never uses a formula, notation or step that has not been shown above it. "Example before the rule" applies only to a pattern the student is meant to notice (a family of answers, a sign rule): then the examples come first and the pattern is named after them.

Lessons never show answer-verification work: no "Check:" paragraphs, no differentiating back, no plugging back in. The writer verifies every answer silently and never prints it.

Do not end with a "common mistake" or "why people get this wrong" paragraph.

### Tone: easy to read top to bottom

These rules come from research on why AI text is hard for people to read (Clark, Martin and Mahowald 2026, arXiv 2610.29162). Models squeeze sentences to save words: they drop small words, stack nouns and pack ideas together. People read best when information is spread out evenly. So short means one idea per sentence, never fewer words per idea. When a sentence runs long, split it into two sentences. Never squeeze it.

**Sentences**

- Keep a step or instruction to 20 words or fewer, and a description to 25. Put one idea in each sentence. Meet the cap by splitting, never by cutting "that", "of" or "the".
- Keep the subject next to its verb. Never put a clause, a list or an aside between them. Write "Simplify first. Then $x = 4$.", not "The value of $x$, once you simplify both sides, is 4."
- Put the known thing first and the new thing last. Put a short part before a long part.
- Don't describe a thing by what someone does to it ("the term you factor out", "the value the loop prints"). Split it: "Factor out $x$. The term left inside is $x + 1$." If you keep the phrase, keep "that": "the value that the loop prints".
- Keep the small words that show how a sentence fits together: "the", "a", "this", "that", "of", "so that", "in order to". Write "the roof of the old house", "all of the rows", "check that the sum is 1".

**Words**

- Use common, predictable words: "use", not "utilize"; "before", not "prior to"; "about", not "approximately".
- Use word pairs a textbook already uses. Never coin a phrase ("reader-patience budget", "gear trap", "papercut bug").
- At most two nouns in a row. "The loop counter update line" becomes "the line that updates the counter".
- Use a noun as a noun. Don't turn it into a verb: "put it on your calendar", not "calendar it".
- Only people do human actions. A method, term or rule never "swallows", "bites", "promises", "wants", "fires", "dies" or "eats" anything. Say what actually happens: "the method catches the error and returns `false`".

**Hard-to-read patterns.** Each one saves a word or two and costs the reader time. The tone editor checks every sentence for them.

| Pattern | Hard | Easy |
|---|---|---|
| Subject far from its verb | The value of $x$, once you simplify both sides, is 4. | Simplify both sides. Then $x = 4$. |
| Thing described by what someone does to it | Plug in the root you found. | You found the root $x = 2$. Plug it in. |
| Dropped "that" or "of" | You know the sum is 1. | You know that the sum is 1. |
| Three or more nouns in a row | the carry bit output wire | the wire that outputs the carry bit |
| Noun used as a verb | Table the cases. | Put the cases in a table. |
| Object doing a human action | The minus sign bites here. | The minus sign flips both terms. |
| Invented word pair | It is a sign-flip trap. | The sign flips. |

`bin/prose_lint.py` (run by `render.sh`) flags long sentences, objects doing human actions, "the root you found" phrases, noun stacks (when spaCy is installed) and terms used before they are explained. Fix every warning before the render counts as done. The tone editor handles what a script cannot judge.

### What a lesson leaves out

- No chapter-opening preview or summary paragraph ("this chapter covers…", "you know this from…", "the X is for…, the Y is for…"). A chapter opens directly with its prerequisites, if any, or its first step. A decision rule the student needs ("use parts when no $u$-substitution works") goes where the choice is made, usually the Which Technique table.
- No trap or "common mistake" lines. The one exception: something the grader actually takes points off for, as stated by the instructor or the rubric, gets one **On the test** callout: a `::: callout` block with a `wrong:` line (the form that loses points), a `right:` line (the form the grader wants) and at most one short text line. The board renders it as an amber card with the wrong form struck through next to the right one; a plain `⚠️` line still renders as the same card with only its text.

  ```md
  ::: callout
  wrong: $1/\infty = 0$
  right: $\displaystyle\lim_{x\to\infty}\frac{1}{x} = 0$
  $\infty$ is not a number.
  :::
  ```

### Sequence meaning before use

- **Top to bottom, hard rule.** The student reads once, from the top. Never use a term, symbol or abbreviation before the paragraph that explains it. When one shows up early, move its explanation up to before that first use. Never leave a forward pointer ("see below", "more on this later"). Write each term in **bold** at the place that explains it, so `bin/prose_lint.py` can see where it is explained and flag any earlier use.
- Start with the task the learner will be able to perform. Name the actual homework or exam skill; keep enrichment off the main path.
- Establish only the prerequisites that task needs. Define a new concept in familiar words, introduce its notation, explain what that notation means, then use it. Do not define one unknown term through another unknown term.
- Introduce symbols beside their first use, including overloaded operators, bars, parentheses, subscripts, abbreviations, and implicit multiplication when relevant. Read an unfamiliar expression aloud in prose before manipulating it.
- Explain an operation before using it inside a larger operation. Make grouping and order explicit. For nested expressions, name the pieces and treat each group as one piece until it is that group's turn.
- Keep names stable throughout an example. Distinguish input values, intermediate results, outputs, and placeholders in a general rule. When matching a rule, point out exactly which piece of the example fills each placeholder.
- Use a meaning-level concrete case to make an abstract rule understandable. Do not begin with a wall of named theorems.

### Build a small example into a method

- Give the setup: what is given, what is wanted, and the rule needed for the next step. Introduce later rules just before they are needed, rather than front-loading a catalogue.
- Begin with the smallest example that exposes the mechanism. Work one truth-table row before showing all rows; trace one intermediate wire before a complete circuit; evaluate one case before generalizing.
- Explain why a rule works with a short causal argument or a complete small case split. “Absorption” or “identity” can label a reason after its meaning is established; neither word substitutes for an explanation.
- Name the action, show the change, and give the reason. Use one operation per equation line. Separate factoring, complement replacement, and identity cleanup instead of collapsing all three into a single equality chain.
- For a difficult step, put a short paragraph immediately before its equation: identify the piece being changed and what stays in place. Keep the equation's right-margin reason short.
- Show intermediate results explicitly. Use helper columns, named wires, or short stage headings so the learner does not have to carry several unfinished operations in memory.
- Finish one simple worked example before adding a complication. Change one feature in the next example, explain the new decision it requires, and reuse the established method.
- Use modified practice analogs for assigned work, preserving the tested skill without revealing or setting up the assigned answer. Do not promise what the homework's final answer will look like.
- When several task types coexist, provide a compact task → first move → check table. Keep it actionable; omit a recap paragraph that only repeats the lesson.

### Language and visual conventions

- Follow **Tone: easy to read top to bottom** above, including the **Hard-to-read patterns** table.
- Explain the meaning in plain words before giving its technical name when that helps. Keep the course's technical vocabulary available so the student can recognize it on the assignment.
- One idea per paragraph. Use headings that name the action or decision. Do not compress several new concepts into a dense paragraph merely to meet a word cap.
- Keep the reasoning needed for the task visible. The Prerequisites toggle lists expected prior knowledge only. Toggles may hide predictions, retrieval answers, and optional detail; explanations needed to follow the next line stay visible.
- Use tables for repeated comparisons after explaining one representative case. Give columns operational labels such as “NOT Q” or “previous column OR R”; avoid unexplained shorthand.
- Use a small diagram when it clarifies actual connections or dependencies. Label intermediate results at the point they are produced. Read the diagram in prose once so the learner knows how to trace it.
- A block flow is a wiring plan; identify it as such if the assignment requires standard circuit symbols. Distinguish the representation being taught from the required submission format.
- Respect the user's language preference; do not infer a language switch from a technical term. Preserve the course workspace's language convention unless asked to change it.
- Fit the session's time budget by cutting tangents and duplicate examples. Preserve the prerequisite explanations and intermediate steps that make the remaining examples understandable.

Diagrams: when one helps and how to draw it are in FIGURES.md (**When to illustrate**).

### Practice and completion check

- Ask a small prediction after teaching the prerequisite and before revealing the outcome. The reveal explains the causal step.
- Cover the taught skills with 1–2 checkpoint MCQs after each chapter and 2–3 fresh mixed MCQs at the end, grounded in relevant supplied questions, following QUIZ.md Source fidelity. Match source difficulty, reasoning and alternatives; change parameters or adapt free-response questions to MCQ. Do not replace exam-level questions with easy recall or quiz an untaught prerequisite.
- Write explanations that connect the answer to the rule and identify the actual mistaken operation. Verify every option; mathematically equivalent alternatives cannot be marked wrong merely because one uses more steps.
- Before the final render, read top to bottom as a learner. Does every term and symbol appear after its plain explanation? Is every rule explained before it is applied? Is every transition supported by a visible intermediate step? Is every check correct? Does each explanation follow the Shape order? Does every sentence follow the Tone rules? Is `bin/prose_lint.py` clean?
- Verify section order, the full author byline, rendered math, figure labels, and quiz keys. Fix rendering or ambiguous questions before declaring the lesson ready. Do not infer mastery or completion from having rewritten or displayed material.

## STEM lessons (math, physics, engineering, CS)

The model is an exam-prep lesson for a calculus test: Prerequisites, Contents, an **Exam Topics Breakdown**, then one chapter per technique, each in the **Shape** order, a checkpoint per chapter, a practice exam, a cheat sheet, the quiz.

- **Show, don't list.** Every method section opens with one or two plain sentences saying what you are doing and when (minimal, never zero), then is built the same way, because the student learns most by following one worked example:
  1. the tool, at level 2 (`::: key`, e.g. $\int u\,dv = uv - \int v\,du$), with one line saying what its parts are;
  2. how to choose or set it up, as a big visual where one exists (e.g. LIATE as five letters with the words underneath, at level 1);
  3. ONE annotated worked example, with the steps written as labels on the math (`\underbrace`, `\overset`, a boxed $u$/$du$/$dv$/$v$ grid), never as a prose list of steps, and the final answer boxed;
  4. one near-copy "Your turn" in a `::: checkin` with the answer behind the toggle.
  This is the **Shape of each explanation** order.
- **Every result produced by a rule carries its rule.** Wrap the result in `\why{<math>}{<rule>}` (optionally `\why[short name]{<math>}{<rule>}`): the board shows the math with a faint dotted underline, and a tap opens the rule in a small popup. Use it in setup boxes, derivation steps, worked examples and your-turn answers. The hint is the GENERAL rule, never the specific computation: `du = \why{5\,dx}{\tfrac{d}{dx}(kx) = k}`, `v = \why{\tfrac13\tan(3x)}{\int\sec^{2}(ax)\,dx = \tfrac{1}{a}\tan(ax) + C}`. Check every rule is right. Copy, Explain, search and the Kindle book see only the plain math.
- **Size encodes importance: three levels, never hand-sized.** Level 1 (`::: big` around a display or a table) is the one or two fundamental rules or mnemonics a chapter rests on, as a big visual (LIATE, the trig-sub forms, the decomposition shapes, the p-rule); at most two per chapter. Level 2 (`::: key`) is a tool or key formula, about 1.4× ($\int u\,dv = uv - \int v\,du$, L'Hôpital's rule). Everything else is level 3, the normal size. Never write `\Large`, `\Huge` or `\small` to size math (`bin/lint.py` flags them); put labels under a formula with `\underset{label}{…}`, which sets them in the smaller script size on its own.

  ```md
  ::: big
  $$\underset{x \,=\, a\sin\theta}{a^{2}-x^{2}}\qquad\underset{x \,=\, a\tan\theta}{a^{2}+x^{2}}$$
  :::
  ```
- **Every solution uses the worked-example format**: Your turn, checkpoint and check-in answers, drills, practice-exam solutions and `why:` lines that show work. At most one short sentence, the labeled setup (for parts the boxed $u$/$du$/$dv$/$v$ grid), an aligned derivation with one step per line and the reason after `&&`, and the boxed answer. Never chain equations through a prose sentence ("$u = x$, $v = …$. Then … = … = …"); a one-line answer is fine only for a single result with no steps. `bin/lint.py` flags any line with two or more `=` in inline math.
  At most two short sentences of prose around all of it.
- **Solutions open one step at a time.** The board steps every worked solution the student solves themselves (a `::: checkin` answer, an `::: mcq` `why:` with display math): the lead sentence and the first piece (the boxed setup, else row 1 with its reason), then **Next step** adds one aligned row with its reason and the last press shows the boxed answer; **Show all** opens everything. A wrong pick shows the verdict and the lead sentence as its hint first. Taught worked examples are never stepped. No markup is needed: write the solution in the format above and the steps come from its rows, so keep one operation per row and the boxed answer on the last row.
- **No opening hook.** No "Question first" line under the Contents.
- **No exam logistics.** No date, time, room, closed-book or grading-policy paragraph. The topic scope is the breakdown table. A rule the grader takes points off for becomes one `::: callout` instead (see **What a lesson leaves out**).
- **No inline provenance.** No `→ Exam:`, `→ background` or "officially stated" tags in the body. Where things came from goes in the `::: sources` drop-down under Contents.
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
- **Exam Topics Breakdown**, right after Contents in every exam-prep STEM lesson: a bold `**Exam Topics Breakdown**` line, then a three-column table, then one short line naming the past exams it averages.

```md
**Exam Topics Breakdown**

| Section | % of exam | Shape it takes |
|---|---:|---|
| 8.8 improper integrals | 28% | evaluate $\int_a^{\infty}$ with parts or a $u$ inside |
| 4.5 L'Hôpital | 2% | one limit; check the form first |

Average over past second exams: Summer 2023, Fall 2017, Fall 2018, Spring 2019.
```

  Percentages, never points. For each past exam, divide each in-scope topic's points by that exam's in-scope total (bonus left out), then average across the exams and round so the column adds up to 100. If only one exam has a point split, use it alone and say so. Rows go from most to least common. The shape column names the problem types in a few words, with neutral wording.

## Lesson frame

```md
---
title: Sum of Products from a Truth Table
course: ECE 2020          # omit in self-study
exam: Test 1, Q3–Q5       # omit if unknown / self-study
model: GPT-6 Astra Medium # example only; use the actual session's full writer identity
image: Java source code on a computer screen   # the lesson's literal subject, never a metaphor or a chalkboard
photo: assets/0004.jpg     # filled by bin/image.sh
credit: Photo by … (Openverse, CC0)   # shown only in the Image credits line
caption: a short description of the banner   # optional; otherwise the title part of credit:
prev: 0003                 # previous lesson number, omit on the first
---

# Sum of Products from a Truth Table

::: prerequisites
- AND, OR, NOT
- Truth-table rows
- Basic Boolean algebra
:::

::: contents
1. [Chapter 1 · Build an SOP](#s-chapter-1-build-an-sop) — turn rows into terms.
2. [Chapter 2 · Simplify it](#s-chapter-2-simplify-it) — combine terms.
:::

::: sources
<!-- files: `sources/slides/week2.pdf` `sources/exams/practice-test-1.txt` -->
- Week 2 slides · the SOP method
- Practice Test 1 · the quiz items
:::

*Question first: a table of 1s and 0s is in front of you. How do you turn it into a circuit?*

### Before we start  ·  from lesson 0003: Boolean Algebra and the Basic Gates
::: checkin
- What does a bar over a variable mean?  ||  NOT. $\overline{A}$ is 1 exactly when $A$ is 0.
- Why is $A+\overline{A}=1$?  ||  One of the two is always 1.
:::

## Chapter 1 · Build an SOP

…body: method sections in the STEM order (see the model lesson)…

## Chapter 2 · Simplify it

…next topic…

### Checkpoint

…1–2 standalone source-matched `::: mcq` blocks; also add a checkpoint after Chapter 1…

## Quiz

…2–3 fresh questions mixing the chapters; one final quiz container only…

::: quiz
topics: minterms, simplifying SOP, K-map merging

::: mcq q1 b
Two product terms differ in exactly one variable. What happens to that variable when you merge them?
- It becomes its complement || Merging removes the variable; complementing it changes the function.
- It is dropped, because $X\overline{Y} + XY = X$
- It moves to the other term || Both terms become one term; there is no other term left.
- It is kept in both terms || Then nothing was merged: the two terms are still separate.
why: The variable appears once true and once complemented, and $\overline{Y}+Y = 1$.
:::

::: mcq q2 a
A truth table has a 1 in row 0110. Which minterm is that?
- $\overline{A}BC\overline{D}$
- $A\overline{B}\,\overline{C}D$ || Every bar is flipped: a 0 is the complemented variable.
- $\overline{A}\,\overline{B}CD$ || The row was read as 0011, shifted one place.
- $\overline{A}BCD$ || The last 0 was read as a 1.
why: A 0 is the complemented variable, a 1 the plain one, read left to right.
:::
:::


## Extra          # self-study only, only when the video was a source
::: video https://www.youtube.com/embed/ID?start=95
Ben Eater, "Making logic gates from transistors"
:::

```

The “Before we start” block above is conditional: include it only for a genuine continuation of lesson 0003; otherwise omit both the heading and check-in, and omit `prev:`. Chapter links must match the rendered heading anchors.

Before finishing a new lesson, apply the visual/interactive contract in SKILL.md. Math needs an interaction or meaningful animation; a banner photo does not count. See [INTERACTIVES.md](./INTERACTIVES.md) for working schemas.

Block syntax the renderer understands:

- `::: interactive trace` or `::: interactive function` / JSON spec / `:::` → manipulable lesson example; see INTERACTIVES.md.
- `::: prerequisites` / short `- concept` lines / `:::` → collapsed **Prerequisites** list at the top of every non-plain lesson.
- `::: sources` / one line per source (its name, then a 3–6 word note on what it was used for) / `:::` → the collapsed **Sources** drop-down, the third row after Prerequisites and Contents. No file paths, problem lists or tier tags in the rendered lines: put the paths the chat panel reads in an HTML comment inside the block. The board adds the Image credits line as its last item, so all attribution sits in one place (a lesson without it keeps Image credits at the end). An older lesson's trailing `## Sources` still renders as a normal section.
- `::: contents` / numbered chapter links with a one-line description each / `:::` → collapsed **Contents** drop-down right after Prerequisites, styled the same. A plain `**Contents**` line over a list (older lessons) renders the same way.
- `::: checkin … :::` with `- question || answer` items → Notion-style toggles. An item may continue on lines indented two spaces and hold a fenced code block; the first `||` outside code splits question from answer.
- `units: …` on the line after a display equation → "symbols & units" toggle.
- `::: numeric … :::` → collapsed numeric detail under an abstract step.
- `::: predict` / option lines / `reveal: …` / `:::` → prediction buttons; the reveal opens after a click.
- `\why{math}{rule}` inside any `$…$` → the math with a dotted underline; a tap shows the rule (STEM lessons, see above).
- `::: sheet` / `::: group <label>` cards / `:::` → a cheat-sheet chapter: cards of formulas with small-caps labels, two columns when there is room (see **STEM lessons**).
- `::: big` / a display or table / `:::` → size level 1 (the chapter's fundamental rule); `::: key` → level 2 (a tool formula). See **STEM lessons**.
- `::: callout` / `wrong: …` / `right: …` / optional short text / `:::` → the amber **On the test** card for a grader deduction (see **What a lesson leaves out**). A line starting `⚠️` renders as the same card with just its text.
- `::: exp e12 [folded] … :::` → an expandable callout. Written only after an Explain request, not prefilled in a fresh lesson.
- `::: fig <template>` / JSON spec / `:::` → inline chalk SVG (taccounts, bars, flow, timeline, table, kmap, vectors, wave, raw). Specs in [FIGURES.md](./FIGURES.md). `caption` in the spec becomes the figcaption.
- `::: photo [side|wide]` / `query: <what to fetch>` / `caption: <short description>` / `:::` → a real photograph of the thing being discussed, fetched by `bin/photos.py` from licensed sources and saved under `assets/`; `src: https://…` skips the fetch when a specific image (a maker's press photo) is the only good one. `side` floats it right at 44% width with the text flowing on the left; `wide` spans the column. Rules in **Photos** below.
- `::: figure assets/x.svg|png` / caption / `:::` → an existing image; `.svg` is inlined so the page fonts apply; add `wide` for a full-width `.png`.
- `::: video assets/x.mp4` / caption / `:::` → a Manim animation rendered with `bin/anim.sh`; a YouTube embed URL gives an iframe.
- `$100` in prose is money and stays as typed. Inline math never starts with a digit or a space: `$F = 1$`, `${}0.5$`. `\$` is a literal dollar sign.
- `::: video URL` / caption / `:::` → embedded video.
- `::: quiz` / `topics: a, b, c` / items / `:::` → the quiz. Items render first, the "More practice" panel under them.
- `::: mcq q1 b` / stem / four `- option || the mistake that gives it` lines (the key has no `||` part) / `why: …` / `:::` → one multiple-choice item in a numbered list; the letter is the key in the order written, options shuffle on render, a wrong pick shows that option's mistake line. The stem may hold a fenced code block (rendered as a code box, question sentence after it); an option that is a whole statement of code in backticks shows as a small preformatted box.
- `::: card c1` / question / `answer: …` / `must: …` lines / `:::` → one flashcard. Every card in a quiz joins one deck, shown one card at a time where the first card sat: the front holds the question and an answer box (typed, or filled by Speak); Validate grades it and the card turns to show `answer:` and the verdict. `must:` lines are the grader's rubric and stay off the front. Cards are generated by `bin/quiz.py`; a lesson does not ship with them.
- `::: score c1 4` / the answer, the rationale, `Missing: …` / `:::` → the verdict on the back of that card. Written by `bin/quiz.py`, never by hand.
- `→ Exam: …` or `→ background` at the end of a block → course tag (course mode only, never in STEM lessons).
- A markdown table → a booktabs table (rules at the top, under the header, and at the bottom; no vertical rules, no fills). Math works in any cell. See **Tables** below.

## Tables

Use a table whenever the same two or three questions get asked of every item in a set: a family of formulas, gate truth tables, a ladder of problems, two things told apart attribute by attribute. Anything the reader will scan across and down rather than read in order.

Do not use one for a sequence (that is a Derivation), for a single fact, or for two rows. Tabular content is always a board table: never `\begin{array}`, `tabular` or `\begin{matrix}` with `\hline` or `|` rules to fake one. A real markdown table gets the rules, the spacing and the header treatment, with prose cells in the body font and math in inline `$…$`; `bin/lint.py` flags an array or tabular with rules. Real math arrays (a matrix, cases, an aligned setup grid) stay math. Headers wrap onto two lines when a column is narrow, so keep them to a few words.

```md
| $\displaystyle\int \cdots dx$ | comes from | answer |
|---|---|---|
| $\sin(ax)$ | $\frac{d}{dx}\cos x = -\sin x$ | $-\frac{1}{a}\cos(ax) + C$ |
| $\cos(ax)$ | $\frac{d}{dx}\sin x = \cos x$ | $\frac{1}{a}\sin(ax) + C$ |
```

Rules:

1. **Three or four columns, never more.** Column 1 is the thing being looked up; the rest answer one question each. A fifth column means two tables.
2. **Header names the question**, in two or three words: "comes from", "answer", "when to use it". The board renders headers as small dim capitals, so they read as labels, not data.
3. **Parallel cells.** Every cell in a column has the same shape — all integrands, all derivatives, all answers. A cell that breaks the pattern is prose and belongs under the table.
4. **Sorted so the pattern is visible.** Put the rows that share a sign or a co-function next to each other. The order is the teaching.
5. **One line per cell.** If a cell needs a sentence, the table is the wrong block.
6. **Numbers right-aligned** with `|---:|`; text and math left. Digits are already tabular.
7. **One line under the table** naming the pattern the rows just made ("three are co-functions and all three are negative"). The table shows, that line tells.

The board scrolls a wide table horizontally rather than squeezing it, so a long third column is fine.

A markdown table is the default. `::: fig table` (see [FIGURES.md](./FIGURES.md)) is only for the case a markdown table cannot do: highlighting a specific cell or row to point at it from the prose.

## Derivations

The steps inside every worked example and solution:

1. **Setup block first.** State what is given and wanted. Explain the next rule before applying it; introduce additional rules at the stage that needs them.
2. **One operation per line.** One substitution, one expansion, one cancellation, one limit. Never two.
3. **One `=` per line, in a column.** `\begin{aligned} LHS &= … \\ &= … \end{aligned}`. LHS written once.
4. **Reason in the right margin.** `&& \text{(reason)}` on every line. No unexplained jumps. The board renders everything after `&&` as a chalk margin note (dashed rule, accent colour, smaller, a "why" label on the first), so it reads as an aside, never as a step: put only the reason or the formula being used there, never part of the derivation.
5. **Tool before use.** Every formula a line uses was shown above it (see **Shape of each explanation**). Keep required reasoning visible.
6. **Expand explicitly.** $(a+b)^2 \to a^2+2ab+b^2$ written out.
7. **Separate cleanup steps.** Simplify when the method needs it, one operation per line; box the final result. A simplification lesson should expose each simplification as its own justified step.
8. **Box the final answer** of every worked derivation (`\boxed{…}` on the last line). No verification paragraph after it.
9. **Layout.** Display math left-aligned, one `aligned` block per stage, a `###` heading per stage ("Setup", "Step 1 — width", …). Derivation steps never side by side; a figure may sit beside its caption.

Add a `::: predict` before the result when the outcome is guessable ("what happens to F when A = 1?").

## Steps go down, never sideways (hard)

A derivation is a column, one operation per line, the reason in the right margin, the result boxed. Never `a = b = c = d` on one line and never `A \Rightarrow B \Rightarrow C` inside a sentence, for a worked example or a "small" step alike. Solving for the crossings of two curves is a derivation. Evaluating a bracket at its limits is a derivation. `render.sh` runs `bin/lint.py` and prints a warning for every sideways chain; fix them before the render counts as done.

```
$$\begin{aligned}
x^{2} &= 2x + 3 \\
x^{2} - 2x - 3 &= 0 &&\text{move everything left} \\
(x-3)(x+1) &= 0 &&\text{factor} \\
x &= -1,\; 3 &&\text{the limits}
\end{aligned}$$
```

## Titles

A title is a YouTube title, not a file name. Short, concrete, says what you will be able to do or understand after reading: "How to Solve All 5.5 Problems", "Test 1 Formula Sheet", "How Absorption Works", "How the NVIDIA DGX Spark Actually Works", "Split the Fraction First". Rules:

- No em dashes, no colons, no "Problem 1 — every step" suffixes, no "Step by Step" padding.
- Aim for two to seven words; a longer title is fine when it names the subject clearly, as in the calculus model lesson. Lead with "How to", "How X Works", "Why X", or the thing itself.
- Name the subject in plain words, never the course code: "How to Ace Your Second Integral Calculus Test", not "How to Ace MATH 1552 Test 2". The course stays in `course:`, which the board shows above the title.
- The `title:` in front matter and the `# ` line are the same string. The hub and the tab show it, so it must read well at a glance next to other courses' lessons.

## Photos

Captions are a short description of the image only (no longer than "Cornell University notebook and exam pages for Math 221, Spring 1973"): what to notice goes in the prose beside it, and author, license and source go in the lesson's **Image credits** line, which the board builds at the end of the lesson from every `credit:` (the banner's front matter and each `::: photo`).

**The banner is the subject.** When the lesson is about a specific object (a machine, a chip, a building, an animal), the banner photo is that object, not a generic image of its category: a DGX Spark lesson opens with the DGX Spark, never with "a computer chip". If the free sources cannot produce the object itself, use the maker's press photo as the banner (`photo: assets/NNNN.jpg` copied from a press image, `credit: <maker> press image`) and leave `image:` for abstract lessons only. Check the banner after the first render; a wrong banner is worse than none.

**`image:` is the literal subject, never a metaphor.** Name what a photo of the lesson's topic would actually show, with concrete nouns: "Java source code on a computer screen", "calculus integrals handwritten in a notebook", "graph of a function". Never a picture of a word in the lesson: contract → law books, interface → people meeting, sorting → library shelves, array → lockers, absolute value → folded paper are all wrong. `bin/image.sh` accepts only candidates whose title, description or tags contain the query's subject words as whole words (page, sheet, formula, paper, macro, notebook and similar generic words do not count), and names its pick on stderr (`image.sh: chose "<title>"`). The match is on metadata, not pixels: after picking, open the downloaded file and confirm it shows the subject; if not, change `image:` and re-roll.

Real photographs go between topics **only when the lesson is talking about a physical thing** and a photo of that thing exists: a machine, a chip, a board, an organ, a building, an instrument. Then:

- At least one photo of the thing itself, `wide`, near the top.
- A photo of a part **at the section that discusses that part** (the die, the connector, the cooling), `side` so the text keeps flowing, and only if a good photo of that exact part exists. A photo of something adjacent is worse than no photo.
- `query:` names the object precisely as a photographer would caption it ("NVIDIA DGX Spark desktop computer front", "GB10 Grace Blackwell chip package"); the caption names what it shows in a few words, and the sentence before or after the photo says what to notice.
- Never for abstract topics (a limit, an integral, a proof, a tax rule): those get `::: fig` drawings, not stock photos.
- Two or three photos per lesson is normal; more than five means the lesson is a gallery.
