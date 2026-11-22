# Lesson template

Every lesson is one markdown file, `lessons/NNNN-slug.md`, rendered on the board. This file holds the rules that every lesson shares. The shape of the lesson comes from one of three blueprints, which SKILL.md **Lesson blueprints** picks: [BLUEPRINT-STEM.md](./BLUEPRINT-STEM.md), [BLUEPRINT-HUMANITIES.md](./BLUEPRINT-HUMANITIES.md) or [BLUEPRINT-FUN.md](./BLUEPRINT-FUN.md).

**Minimize the energy it takes to read and practice. Every sentence either helps solve the problem or is cut. No intros, previews, recaps, answer checks or filler.**

## Board rules

1. One idea per block. A block is a paragraph, a display equation, a figure, or a toggle. Never two mechanisms in one block.
2. Picture beside the step it explains. Labels on the picture, not in prose.
3. Fixed top. Every lesson starts the same way: front matter → `# title` → Contents dropdown → Sources dropdown. Everything after that comes from the blueprint (**Lesson frame**).
4. Erase, don't add. Word caps below are real. Anything off-path is cut.
5. The practice is written as part of the lesson, as its blueprint says. The student never has to generate anything to start practicing.
6. Code lines stay at or under 60 characters, so a block fits the column at any zoom. An explanatory comment goes on its own line above the statement it explains, at the same indentation, never trailing a long line. Wrap anything longer. In an `::: interactive` trace, shorten comments rather than add lines, so the step line numbers stay right.
7. Code in a question: a stem, check-in question or answer that shows more than one statement of code puts that code in a fenced ```java block, formatted as real code with line breaks and indentation, then the question sentence on its own line after it. Never inline a class or several statements into a sentence. A single short expression stays inline in backticks.

   ````
   ::: mcq c2a a
   ```java
   public class Pet {
       private int age = 5;
   }
   ```
   What does `new Pet().getAge()` return?
   - `5`
   ...
   ````

## Didactic writing contract

Use these conventions for lessons and rewrites. They capture what worked in practice: small understandable steps, with the reason visible. Scale the depth to demonstrated knowledge and the task; coverage alone is not evidence that a prerequisite is understood. For questions asked in chat, follow SKILL.md's **Chat answers**.

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

`bin/prose_lint.py` (run by `render.sh`) flags long sentences, objects doing human actions, "the root you found" phrases, pronunciations and alternate spellings, noun stacks (when spaCy is installed) and terms used before they are explained. Fix every warning before the render counts as done. The tone editor handles what a script cannot judge.

### What a lesson leaves out

- No chapter-opening preview or summary paragraph ("this chapter covers…", "you know this from…", "the X is for…, the Y is for…"). A chapter opens directly with its first block, in the order its blueprint gives. A decision rule the student needs ("use parts when no $u$-substitution works") goes where the choice is made (the chapter's **What you need**).
- No obvious explanations. Never say how a symbol is pronounced ("$\overline{Q}$, read "Q bar""), list other spellings of the same thing ("also written QN or Q'"), or restate what the student can already see. Use the one notation the course's sources use, and use only that one. Explain what a symbol means, never how to say it.
- No trap or "common mistake" lines. The one exception: something the grader actually takes points off for, as stated by the instructor or the rubric, gets one **On the test** callout: a `::: callout` block with a `wrong:` line (the form that loses points), a `right:` line (the form the grader wants) and at most one short text line. The board renders it as an amber card with the wrong form struck through next to the right one; a plain `⚠️` line still renders as the same card with only its text.

  ```md
  ::: callout
  wrong: $1/\infty = 0$
  right: $\displaystyle\lim_{x\to\infty}\frac{1}{x} = 0$
  $\infty$ is not a number.
  :::
  ```

### Simplest to understand wins

This applies to every question, in every subject. Of all the ways to explain a step, choose the one that a student understands with the least decoding, even when it is longer: more steps, more rows, more arrows. Never make an explanation more abstract than the material forces.

- Before writing a step, ask: does the student have to translate this back into something simpler to follow it? If yes, write the simpler thing instead.
- Prefer what the lesson has been using over a new equivalent form, actual values over symbols that stand for them, and listing the cases over compressing them into a formula or a law. Do not reach for a clever shortcut, a merged expression or a general identity just because it is shorter.
- Use the abstract form only when the question asks for it (for example "give the simplified expression"), and then build it from the concrete version already shown.
- Example: on a state diagram with inputs Left and Up, writing the bit patterns on the arcs (`10`; `00, 01, 11`) is easier to follow than `Left·Up'` and its De Morgan complement, because the student would otherwise have to decode each expression back into those values. The same reasoning applies to any kind of question, not only state diagrams.

### Top to bottom

The student reads once, from the top. Never use a term, symbol or abbreviation before the paragraph that explains it. When one shows up early, move its explanation up to before that first use. Never leave a forward pointer ("see below", "more on this later"). Write each term in **bold** at the place that explains it, so `bin/prose_lint.py` can see where it is explained and flag any earlier use.

### Before the final render

- Read the lesson once from the top as a learner.
- Check section order, chapter links, rendered math, figure labels and every answer key.
- `bin/lint.py` and `bin/prose_lint.py` are clean (`render.sh` runs both).

## Problems and solutions

These rules apply to every blueprint that uses official problems (STEM and humanities).

- **A Your turn goes in a `::: checkin`** with the solution or model answer behind the toggle.
- **Every solution is a derivation** (see **Derivations**) when it has steps: worked examples, Your turn solutions, drills, practice-exam solutions and `why:` lines that show work. At most two short sentences of prose around it, the labeled setup, and the boxed answer. A one-line answer is fine only for a single result with no steps.
- **Solutions open one step at a time.** The board steps every solution that the student works out alone (a `::: checkin` answer, an `::: mcq` `why:` with display math): the lead sentence and the first piece (the boxed setup, else row 1 with its reason), then **Next step** adds one aligned row with its reason and the last press shows the boxed answer; **Show all** opens everything. A wrong pick shows the verdict and the lead sentence as its hint first. Taught worked examples are never stepped. No markup is needed: write the solution in the format above and the steps come from its rows, so keep one operation per row and the boxed answer on the last row.
- **No exam logistics.** No date, time, room, closed-book or grading-policy paragraph. The topic scope is the breakdown table. A rule the grader takes points off for becomes one `::: callout` instead (see **What a lesson leaves out**).
- **No inline provenance.** No "officially stated" tags in the body. Where things came from goes in the `::: sources` drop-down under Contents. The one exception is the problem label below.
- **Official problems are quoted in full.** Problems come from official sources first (QUIZ.md **Source fidelity**). Every problem (worked example, Your turn, drill, practice-exam part, quiz item) that comes from an official source is quoted verbatim: its text word for word, with its original numbers, pin names and wording, plus every figure, diagram, table or given circuit it shows, cropped from the source PDF page as the real image (`bin/crop_figure.py --pdf … --page N --preview` to pick the box, then `--box l,t,r,b --out $WS/lessons/assets/NNNN-<src>-<q>.png`, look at the PNG, then `::: figure assets/… wide` with a one-line caption naming the source). Never redraw an official figure or retell it in prose. A table on the page may become a markdown table only when it is pure data with every cell copied.
- **A Your turn is the exam question, nothing more.** Show the problem exactly as the source has it: the official text verbatim and only its own figure (the cropped image when it has one, nothing when it is text only). No sentence before it explaining or restating the question, no redrawn diagram, no added helper table or hint, no highlight; the reader faces it as on the exam, with no help. The solution, behind the reveal, may start by saying what the question asks, then solves it step by step. The same holds for drills, practice-exam parts and quiz items.
- **Every problem has a label (hard rule).** A small line of its own directly above the problem: `[Official · Fall 2018 Exam 2, Q3b](src:exams2/fa18-kj-e2.pdf#page=6)` for an official problem (term, exam or set, question number; no points, no logistics; the link opens the source in the board's viewer at that page, so the path is the file under `sources/` and the page is the PDF page) or `*Written by Claude*` for one we wrote. In a `::: checkin`, put the label, the quoted problem and its figure as blocks before the check-in and keep the item's question short ("Fill in the grey boxes."). `bin/lint.py` warns about a problem block without a label and a `src:` file that does not exist.
- **Given vs calculated.** The student must always see what the problem gave and what we worked out. Put everything quoted from a problem (its text, data tables, given values and figures) inside a `::: given` block, right under the label. The board shows it as a quiet quote card headed **From the problem**, apart from the teaching and the work. Inside a solution, anything copied back from the problem goes in its own `::: given` block too, never mixed into the calculation. When one table holds both, write `>` before each copied column's header (`| >S1 | >S0 | >C1 | >C0 | NS1 | NS0 | P |`); the board mutes those columns, labels them *given*, and leaves the calculated columns bright. The question line of a `::: checkin` item stays outside the block. `bin/lint.py` warns about official problem text that is not in a `::: given` block. For a lesson written before this rule, `python3 bin/given.py <lesson> --write` adds the blocks and the `>` marks, and keeps an installed video's text sync.

  ```md
  [Official · Spring 2019 Exam 3, Q4C](src:exams3/sp19-lw-e3.pdf#page=5)

  ::: given
  **Part C** Fill in the state table for this state machine.

  ::: figure assets/0011-sp19-lw-e3-p4-diagram.png wide
  The state diagram.
  :::
  :::
  ```

## Lesson frame

Every lesson has the same top: front matter, the `# title`, a collapsed **Contents**, a collapsed **Sources**. The rest comes from the blueprint (SKILL.md **Lesson blueprints** picks it). This example is the top of a STEM lesson.

```md
---
title: How to Ace Your Second Integral Calculus Test
course: MATH 1552          # omit in self-study
exam: Test 2               # omit if unknown / self-study
model: GPT-6 Astra Medium  # example only; use the actual session's full writer identity
image: calculus integrals handwritten in a notebook   # the lesson's literal subject, never a metaphor or a chalkboard
photo: assets/0004.jpg     # filled by bin/image.sh
credit: Photo by … (Openverse, CC0)   # shown only in the Image credits line
caption: a short description of the banner   # optional; otherwise the title part of credit:
---

# How to Ace Your Second Integral Calculus Test

::: contents
1. [Chapter 1 · Improper integrals](#s-chapter-1-improper-integrals) — 28% of the exam.
2. [Chapter 2 · Integration by parts](#s-chapter-2-integration-by-parts) — 22% of the exam.
:::

::: sources
<!-- files: `sources/exams2/fa18-kj-e2.pdf` `sources/review/test2-review.pdf` -->
- Fall 2018 Exam 2 · problems and weights
- Test 2 review sheet · the topic list
:::

**Exam Topics Breakdown**

…the table from BLUEPRINT-STEM.md…

## Chapter 1 · Improper integrals

…the chapter, in the blueprint's order…
```

Every `##` after the top is `## Chapter N · <name>`, the mixed drill, practice exam, cheat sheet and flashcards included, so the board's reading scale and level map list it. Chapter links must match the rendered heading anchors. `prev:` in front matter names an earlier lesson only when this one continues it.

Block syntax the renderer understands:

- `::: interactive trace` or `::: interactive function` / JSON spec / `:::` → manipulable lesson example; see INTERACTIVES.md.
- `::: prerequisites` / short `- concept` lines / `:::` → a collapsed **Prerequisites** list. Older lessons only: the renderer still shows it, but new lessons do not write one.
- `::: sources` / one line per source (its name, then a 3–6 word note on what it was used for) / `:::` → the collapsed **Sources** drop-down, the row after Contents. No file paths, problem lists or tier tags in the rendered lines: put the paths the chat panel reads in an HTML comment inside the block. The board adds the Image credits line as its last item, so all attribution sits in one place (a lesson without it keeps Image credits at the end). An older lesson's trailing `## Sources` still renders as a normal section.
- `::: contents` / numbered chapter links with a one-line description each / `:::` → the collapsed **Contents** drop-down right under the title. A plain `**Contents**` line over a list (older lessons) renders the same way.
- `::: checkin … :::` with `- question || answer` items → Notion-style toggles. An item may continue on lines indented two spaces and hold a fenced code block; the first `||` outside code splits question from answer.
- `units: …` on the line after a display equation → "symbols & units" toggle.
- `::: predict` / option lines / `reveal: …` / `:::` → prediction buttons; the reveal opens after a click. Older lessons only: new lessons do not write one.
- `\why{math}{rule}` inside any `$…$` → the math with a dotted underline; a tap shows the rule (BLUEPRINT-STEM.md **STEM writing rules**).
- `::: sheet` / `::: group <label>` cards / `:::` → a cheat-sheet chapter: cards of formulas with small-caps labels, two columns when there is room (BLUEPRINT-STEM.md **STEM writing rules**).
- `::: big` / a display or table / `:::` → size level 1 (the chapter's fundamental rule); `::: key` → level 2 (a tool formula). See BLUEPRINT-STEM.md **STEM writing rules**.
- `::: callout` / `wrong: …` / `right: …` / optional short text / `:::` → the amber **On the test** card for a grader deduction (see **What a lesson leaves out**). A line starting `⚠️` renders as the same card with just its text.
- `::: exp e12 [folded] … :::` → an expandable callout. Written only after an Explain request, not prefilled in a fresh lesson.
- `::: fig <template>` / JSON spec / `:::` → inline chalk SVG (taccounts, bars, flow, timeline, table, kmap, vectors, wave, raw). Specs in [FIGURES.md](./FIGURES.md). `caption` in the spec becomes the figcaption.
- `::: photo [side|wide]` / `query: <what to fetch>` / `caption: <short description>` / `:::` → a real photograph of the thing being discussed, fetched by `bin/photos.py` from licensed sources and saved under `assets/`; `src: https://…` skips the fetch when a specific image (a maker's press photo) is the only good one. `side` floats it right at 44% width with the text flowing on the left; `wide` spans the column. Rules in **Photos** below.
- `::: figure assets/x.svg|png` / caption / `:::` → an existing image; `.svg` is inlined so the page fonts apply; add `wide` for a full-width `.png`.
- `$100` in prose is money and stays as typed. Inline math is `$…$` on one line with no space just inside either `$`. It may start with a digit (`$4$`, `$0.5 \cdot 2$`, `$2^{9/2}$`), because money never has a closing `$` on the same line. Two amounts on one line (`$5 and $10`) stay money. `\$` is a literal dollar sign.
- `::: video assets/x.mp4|URL` / caption / `:::` → a Manim animation rendered with `bin/anim.sh`, or a YouTube embed URL as an iframe.
- `::: quiz` / `topics: a, b, c` / items / `:::` → the quiz. Items render first, the "More practice" panel under them. Humanities lessons hold their flashcards in one; self-study lessons end with one.
- `::: mcq q1 b` / stem / option lines `- option || the mistake that gives it` (the key has no `||` part; how many: QUIZ.md **Multiple choice**) / `why: …` / `:::` → one multiple-choice item in a numbered list; the letter is the key in the order written, options shuffle on render, a wrong pick shows that option's mistake line. The stem may hold a fenced code block (rendered as a code box, question sentence after it); an option that is a whole statement of code in backticks shows as a small preformatted box.
- `::: card c1` / question / `answer: …` / `must: …` lines / `:::` → one flashcard. Every card in a quiz joins one deck, shown one card at a time where the first card sat: the front holds the question and an answer box (typed, or filled by Speak); Validate grades it and the card turns to show `answer:` and the verdict. `must:` lines are the grader's rubric and stay off the front. A humanities lesson ships with its flashcards (BLUEPRINT-HUMANITIES.md **Recall**); only a lesson with a `::: quiz` block (humanities, self-study) has the More practice panel (`bin/quiz.py`).
- `::: score c1 4` / the answer, the rationale, `Missing: …` / `:::` → the verdict on the back of that card. Written by `bin/quiz.py`, never by hand.
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

The board scrolls a wide table horizontally rather than squeezing it, so a long third column is fine.

A markdown table is the default. `::: fig table` (see [FIGURES.md](./FIGURES.md)) is only for the case a markdown table cannot do: highlighting a specific cell or row to point at it from the prose.

## Derivations

The steps inside every worked example and solution. A derivation is a column: never `a = b = c = d` on one line, never `A \Rightarrow B \Rightarrow C` inside a sentence, and never equations chained through prose ("$u = x$, $v = …$. Then … = …"), for a worked example or a "small" step alike. Solving for the crossings of two curves is a derivation; so is evaluating a bracket at its limits. `bin/lint.py` (run by `render.sh`) warns about every sideways chain.

1. **Setup block first.** State what is given and wanted. Explain the next rule before applying it; introduce additional rules at the stage that needs them.
2. **One operation per line.** One substitution, one expansion, one cancellation, one limit. Never two.
3. **One `=` per line, in a column.** `\begin{aligned} LHS &= … \\ &= … \end{aligned}`. LHS written once.
4. **Reason in the right margin.** `&& \text{(reason)}` on every line. No unexplained jumps. The board renders everything after `&&` as a chalk margin note (dashed rule, accent colour, smaller, a "why" label on the first), so it reads as an aside, never as a step: put only the reason or the formula being used there, never part of the derivation.
5. **Tool before use.** Every formula a line uses was shown above it. Keep required reasoning visible.
6. **Expand explicitly.** $(a+b)^2 \to a^2+2ab+b^2$ written out.
7. **Separate cleanup steps.** Simplify when the method needs it, one operation per line; box the final result. A simplification lesson should expose each simplification as its own justified step.
8. **Box the final answer** of every worked derivation (`\boxed{…}` on the last line). No verification paragraph after it.
9. **Layout.** Display math left-aligned, one `aligned` block per stage, a `###` heading per stage ("Setup", "Step 1 — width", …). Derivation steps never side by side; a figure may sit beside its caption.

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
- Aim for two to seven words; a longer title is fine when it names the subject clearly. Lead with "How to", "How X Works", "Why X", or the thing itself.
- Name the subject in plain words, never the course code: "How to Ace Your Second Integral Calculus Test", not "How to Ace MATH 1552 Test 2". The course stays in `course:`, which the board shows above the title.
- The `title:` in front matter and the `# ` line are the same string. The hub and the tab show it, so it must read well at a glance next to other courses' lessons.

## Photos

Captions are a short description of the image only (no longer than "Cornell University notebook and exam pages for Math 221, Spring 1973"). Author, license and source go in the lesson's **Image credits** line, which the board builds at the end of the lesson from every `credit:` (the banner's front matter and each `::: photo`).

**The banner is the subject.** When the lesson is about a specific object (a machine, a chip, a building, an animal), the banner photo is that object, not a generic image of its category: a DGX Spark lesson opens with the DGX Spark, never with "a computer chip". If the free sources cannot produce the object itself, use the maker's press photo as the banner (`photo: assets/NNNN.jpg` copied from a press image, `credit: <maker> press image`) and leave `image:` for abstract lessons only. Check the banner after the first render; a wrong banner is worse than none.

**Every lesson has a banner**, and it is unique across every workspace. `render.sh` fetches it when `photo:` is missing (`bin/image.sh`, in the background) and writes `photo:` and `credit:` into the front matter; never copy another lesson's `photo:` or use a shared default. `image.sh` rejects already-used bytes, source URLs and credits; `render.sh` rejects copied duplicates. Run `python3 bin/banner_guard.py` before delivery and resolve what it reports. Run `bin/image.sh` by hand only to re-roll.

**`image:` is the literal subject, never a metaphor.** Name what a photo of the lesson's topic would actually show, with concrete nouns: "Java source code on a computer screen", "calculus integrals handwritten in a notebook", "graph of a function". Never a picture of a word in the lesson: contract → law books, interface → people meeting, sorting → library shelves, array → lockers, absolute value → folded paper are all wrong. Never the lesson title, and never a chalkboard, blackboard, slate, chalk, classroom or whiteboard unless the lesson is about that object: the page is already a blackboard. `render.sh` refuses a board-photo subject and falls back to the title's topic. `bin/image.sh` accepts only candidates whose title, description or tags contain the query's subject words as whole words (page, sheet, formula, paper, macro, notebook and similar generic words do not count), and names its pick on stderr (`image.sh: chose "<title>"`). The match is on metadata, not pixels: after picking, open the downloaded file and confirm it shows the subject; if not, change `image:` and re-roll.

Photos inside the body (`::: photo`) belong to self-study lessons about a physical thing: BLUEPRINT-FUN.md **Photos**.
