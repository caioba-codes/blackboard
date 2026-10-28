---
name: blackboard
description: Opens and teaches on a persistent black board when the user invokes /blackboard or $blackboard, or asks to open the blackboard, open lessons, or show a lesson. Course mode uses the user's material or LMS; self-study uses primary sources.
---

# Blackboard

**Scope:** Open, write, and explain lessons on the board. **Precedence:** Direct user instructions and explicit lesson role policy govern routing. **Autonomy:** Resolve roles, dispatch teaching and review, and verify receipts. **Success/stop:** Publish only after lesson and routing checks pass; report concrete blockers.

## Temporary board

"temporary board", "blackboard temporário", "solve X on a plain board": a throwaway page with only what was asked, no banner photo, no lesson number or course line, no byline, no quiz, no check-ins, no learning record. Write it to `~/.cache/blackboard/scratch/learn/lessons/NNNN-slug.md` (next free number; outside every course folder) with front matter `plain: true` (plus `title:` only if a heading helps), render it with `BLACKBOARD_LAYOUT=app board/render.sh <file>` so nothing opens on its own, then open `http://localhost:7331/w/scratch/lessons/NNNN` in a new tab of this host's browser pane. The content still follows the derivation rules (one step per line, reasons in the margin).

Before anything else, run `bin/update.sh` once per session. In a git clone it pulls new versions at most once a day; elsewhere it does nothing. If it prints a line, pass that line to the user.

## Open the blackboard (the default)

"open the blackboard", "open my lessons", or `/blackboard` with no arguments: open the all-lessons menu `http://localhost:7331/` beside the chat in this host's browser pane (Claude desktop: the in-app Browser pane; cmux: the existing browser pane; Codex app: the in-app browser), always with `http://` since a bare `localhost:7331` becomes https and fails. "show lesson 3 (in math)" opens `http://localhost:7331/m/3`: any unique prefix of the course slug, then the lesson number. If the page does not load, run `bin/install.sh` (it installs the always-on bridge) and retry. Reply in one line. Every reply that renders or changes a lesson ends with a clickable link to it, e.g. `[Open lesson 0003](http://localhost:7331/m/3)`.

People never need the address: `bin/install.sh` (run automatically by the first `render.sh` on macOS) keeps the bridge running at login through launchd (`com.blackboard.bridge`) and adds a **Blackboard** app to `~/Applications` and the Dock that opens the menu in the default browser.

The user wants to learn something, over many sessions, on the Blackboard. Lessons and explanations belong on the board; chat gets one line (see **Chat answers**).

## Changing this skill while the user studies

The user keeps studying on the live board (port 7331) while the skill is being changed. Never disturb it:
1. Edit in the source checkout and test on the **dev board**: `bin/dev.sh` starts a separate bridge from the checkout on port 7390 (own state dir, same lesson folders); `bin/dev.sh restart` after editing `bridge.py`; `bin/dev.sh stop` when done. Open it only in a **new background tab** that you close afterwards. Never navigate, reload, scroll or click in the user's tab, never render into their workspace to test, and never click quiz answers on the dev board (they log to the real learning records).
2. Sync to the installed copy only when the change is finished and checked. The open page then shows a small "Board updated · reload" chip instead of reloading; the user reloads when they want and keeps their place.
3. Restart the live bridge (`launchctl kickstart -k gui/$UID/com.blackboard.bridge`) only when `bridge.py` changed, and say so in one line.
4. Every finished change is committed and pushed right away, without asking, in the source repo the skill is developed in (`$BLACKBOARD_SRC`, default `~/stuff/projects/cskills`; skip this step if it does not exist): `git -C "${BLACKBOARD_SRC:-$HOME/stuff/projects/cskills}" add -A skills/blackboard && git commit -m "blackboard: <what changed>" && git push` (on a rejected push, `git pull --rebase` then push). One commit per change the user asked for, and the source checkout is the only place edited; `~/.claude/skills` and `~/.codex/skills` are rsync copies.

# Lesson author routing (required)

Before a new lesson or substantial rewrite, read [LESSON-WRITER.md](./LESSON-WRITER.md). Run `python3 bin/lesson_routing.py resolve --workspace "$WS"` before model selection. A per-user policy at `${XDG_CONFIG_HOME:-$HOME/.config}/blackboard/lesson-routing.json` or optional `$WS/.blackboard/lesson-routing.json` explicitly selects author, reviewer, and support model **and effort**; a direct user request takes higher priority. When a policy is present, dispatch those exact roles, verify actual runtime identities, and check the routing receipt before final render/publication. A missing, unsupported, or mismatched required identity blocks publication; preserve existing lesson content and report the concrete blocker while independent support work continues. Without a policy, use the automatic selection in LESSON-WRITER.md. The chatting model coordinates; a separate writer authors the teaching. For every lesson, a fresh tone editor uses that same author's model and effort. A designated child skips selection/delegation; never recurse. This instruction directs agents; the CLI validates supplied evidence but cannot enforce the host's dispatch.

# Full lesson video (default)

Every new full lesson includes both the written lesson and its video unless the user explicitly asks for text only. This does not apply to view/open, Explain, side questions, chat answers, or temporary boards. Read [VIDEO.md](./VIDEO.md) for the exact project commands, Opus 5.5 video role (high effort recommended), source-anchor schema, measured timing map, QA, and import gates. The video role is separate from the designated written lesson author: preserve the current `lesson_routing.py` selection, author byline, reviewer and support roles. If source math differs from independent video math, the designated lesson author corrects and rechecks the written lesson first; then rebuild the video against its new SHA. A missing video credential, model, or runtime blocks the video stage with an explicit report, while the written lesson remains available. The CLI checks supplied receipts; the orchestrator verifies actual runtime identities from host evidence.

# Modes

`$ARGUMENTS` starts with one of:

- `learn <topic> [for <course>]` — write and render a lesson (default when the first word is not a mode).
- `explain <id> <line> "<text>"` — answer an Explain request from the board (see Explain).
- `remove <id>` — delete an explanation block.
- `quiz <topic> <cards|mcq>` — run a quiz by hand in chat (see [QUIZ.md](./QUIZ.md)). The board's own Quiz panel does not use this: it generates and grades headless through `bin/quiz.py`.
- `predict <block> <choice>` / `mcq <item> <choice>` — record a click from the board.
- `add <path|url>` — add material to the workspace and re-tier.
- `sync` — re-pull the LMS course and rebuild the topic map.
- `image NNNN` — re-roll the lesson photo.
- `grid` — open the lessons hub (`/lessons`): every lesson in every folder the board knows about, with search and folder chips.

Requests from the board arrive as one line of JSON in `board/queue.jsonl` (delivered by `bin/wait-ask.sh`, `cmux send`, or pasted by the user); treat that line exactly like the corresponding command.

# Workspace

`$WS` is the workspace root. Resolve it once per session:

1. `./learn/MISSION.md` exists → `$WS=./learn`
2. otherwise `$WS=./learn`, created on the first lesson. Never create `learn/learn`.

Files under `$WS` (formats linked):

- `MISSION.md` — why the user is learning this. [MISSION-FORMAT.md](./MISSION-FORMAT.md)
- `RESOURCES.md` — trusted sources with `kind` and `tier`. [RESOURCES-FORMAT.md](./RESOURCES-FORMAT.md)
- `sources/` — course files and extracted text. [LMS.md](./LMS.md)
- `lessons/NNNN-slug.md` — lessons, markdown + LaTeX. `lessons/assets/` holds photos and Manim stills.
- `reference/*.md` — cheat sheets, glossaries ([GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md)), `topic-map.md` in exam mode.
- `reference/chat/NNNN.json` — the board chat's history for lesson NNNN (see Chat). New chat renames it to `NNNN-<time>.json`.
- `learning-records/NNNN-slug.md` and `quiz-log.jsonl`. [LEARNING-RECORD-FORMAT.md](./LEARNING-RECORD-FORMAT.md)
- `NOTES.md` — the user's preferences about how they want to be taught.

Course mode vs self-study: a course is named in the command, or `MISSION.md` names one → course mode. Otherwise self-study. If both fit (no course named, a course workspace exists, and the topic is in its scope) ask once: "For <course> or on your own?"

# The board

The board is a web page served by `board/bridge.py` at `http://127.0.0.1:7331`. Explain, quiz generation and quiz grading all run headless inside the bridge, so they behave the same in every host and never type into the chat. `board/render.sh <lesson.md>` starts the bridge if needed, opens the board once per host, and renders the file. The page updates itself (SSE); never open a second tab or pane. Hosts are auto-detected ([HOSTS.md](./HOSTS.md)), except the Codex desktop app: there run `BLACKBOARD_LAYOUT=app board/render.sh …` and open `http://127.0.0.1:7331/` in the in-app browser with the browser tool, once per session, so the board sits beside the chat. A read-only sandbox cannot run the board: say so in one line and stop; never answer the lesson in chat instead.

**One bridge, every workspace.** A single bridge on 7331 serves every course; each workspace gets its own slug and URL (`/w/<slug>/`), and `/lessons` is the hub across every folder. Never start a second bridge or use another port for lessons (the only exception is the dev board of `bin/dev.sh`). How the page behaves (top bar, XP bar, reading scale, chalk writing, sounds, quiz cards, Explain and Definition popups, chat panel, slate surface): [board/README.md](./board/README.md).

Headings are the navigation: name them by what the section does, and put each problem or major part at `##` so it gets a mark on the reading scale. `**Step N · …**` at the start of a paragraph is boxed as a sub-step. `board: slate` in front matter gives the lesson a real-blackboard surface (on trial).

**Codex desktop app.** Run the renderer with `BLACKBOARD_LAYOUT=app` (it also auto-detects `CODEX_INTERNAL_ORIGINATOR_OVERRIDE=Codex Desktop`). After the first successful render in a task:

1. Use the in-app Browser tool to create a tab, navigate that tab to `http://127.0.0.1:7331/`, verify the lesson title, and mark the tab as a deliverable so it survives the turn.
2. Call `codex_app__open_in_codex` with `target: {type: "browser", tabId: <the Browser tab's id>}` and `placement: "right"` so that exact navigated tab is presented beside chat. The app action may report `queued`; finish the turn so it can present the tab.

The tools may be deferred, so find them by exact name before concluding they are unavailable. Do not pass an app/provider tab id discovered elsewhere and do not call macOS `open`; both paths can leave a blank tab. Reuse the same Browser tab for later renders because SSE refreshes it.

**Streaming rule.** Write a lesson by appending to the `.md` block by block, never in one write at the end:

1. Write the front matter (`title`, `course`, `exam`, `model`, `image`) and run `board/render.sh <lesson.md> --live` (opens the board, marks the lesson as being written).
   **The parent does this first, before course research**, while running the quick writer-model check; leave the writer byline pending until selection, then let the designated writer author the body. The board is never blank: the page immediately writes "Explain: <title>" in chalk. Then, while you research (read the syllabus, the LMS, sources), keep the board alive with `bin/brainstorm.sh <lesson.md> "note" ...` after every step or two. Each call sends the whole list: the page handwrites new lines and wipes removed or moved lines with a felt eraser. Use the shape `"Explain: <topic>"`, `"Goal: <what the student must be able to do>"`, `"Sources:"` followed by `"- <source you are reading>"` lines (add them as you open them, drop the ones you reject, reorder by how much you will use them), `"Outline:"` followed by `"- 1. <section>"` lines once the plan is clear. Real notes only: what you are actually reading and deciding. When the first body block lands, the board wipes the brainstorm itself and starts writing the lesson.
2. `image:` is required and names the lesson's **literal subject** as a photographer would caption it: "Java source code on a computer screen" for a Java classes lesson, "calculus integrals handwritten in a notebook" for an integration lesson, "river delta from above" for sediment transport. Never a metaphor for a term in the lesson (contract → law books, interface → people meeting, sorting → library shelves, array → lockers, absolute value → folded paper). Never the lesson title, and never a chalkboard, blackboard, slate, chalk, classroom or whiteboard unless the lesson is about that object: the page is already a blackboard, so a board photo says nothing about the lesson. `render.sh` refuses a board-photo subject and falls back to the title's topic, with a warning. `image.sh` only accepts a photo whose title, description or tags name the query's subject words (whole words; generic words like page, sheet, formula, paper, macro do not count) and prints `image.sh: chose "<title>"` to stderr. After picking, open the downloaded asset (Read the image file) and confirm it shows the subject; if it does not, change `image:` and re-roll. Every lesson has a banner, no exceptions. `render.sh` fetches the photo itself when `photo:` is missing (background, via `bin/image.sh`) and writes `photo:`/`credit:` into the front matter; the board shows it as the banner above the title. Banners must be unique across every workspace in All lessons. Never copy another lesson’s `photo:` or use a shared default. `image.sh` rejects already-used bytes, source URLs, and photo credits under a global lock; `render.sh` rejects manually copied duplicate banners. If the subject search fails, it tries the topic derived from the title and then reports failure; it never falls back to a chalkboard or reuses a banner. Run `python3 bin/banner_guard.py` before delivery; resolve missing or duplicate banners. A lock older than 10 minutes is cleared. Run `bin/image.sh` by hand only to re-roll. Before finishing a lesson, check that its front matter has `photo:`.
3. Append each block (title, question, check-in, each section) with its own write, separated by blank lines, and never rewrite earlier blocks while writing (a rewrite rebuilds the page).
4. When the lesson is complete, run `board/render.sh <lesson.md>` (clears the live flag).

**One-line delivery messages.** After rendering: `On the board: 0004 Sum of Products from a Truth Table`. After a board explanation: `explained on board`. After a board quiz item: the score, one line.

# Chat answers

Chat gets one line. Math, steps and explanations go on the board: with a lesson open, as a side-question section in that lesson (**Board answers to side questions** below); with none open, on a temporary board. The one line says what landed and links to it. In terminal chat that line is plain text with readable Unicode math (NOT A, A · B), never raw LaTeX. Reply in the user's language.

# Lesson opening and chapters (required)

Every non-plain lesson starts below its title with a collapsed `::: prerequisites` block labeled **Prerequisites**. Inside: a simple list of the concepts the reader must already know, one short phrase per bullet. No introductory paragraph, time-budget prose, or repeated description of the lesson. If none, one bullet: “None.” This is an inventory, not hidden instruction: explain any prerequisite the learner has not demonstrated in the chapter where it is needed.

Next comes **Contents**: a collapsed `::: contents` block, styled like Prerequisites, holding a short linked list of chapters, each with a brief phrase saying what it covers. Organize the body like a book: `## Chapter 1 · <topic>`, `## Chapter 2 · <topic>`, with `###` subsections. Even a short lesson can have one chapter. Sources go right under Contents as a collapsed `::: sources` drop-down; keep the Quiz as end matter; do not turn every small step into a chapter. Replace long opening roadmaps and pass tables with this compact index. See TEMPLATES.md for the exact frame.

Quizzes: [QUIZ.md](./QUIZ.md) sets the counts (1–2 checkpoints per chapter, 2–3 mixed at the end) and **Source fidelity**, which applies to authored quizzes and generated More practice.

# Author byline (required)

Every new lesson must set `model:` to the actual writer's full display name: family/version, variant, and reasoning effort when available. Example: `model: GPT-6 Astra Medium`, rendered as “by Prof. GPT-6 Astra Medium.” (the board adds “Prof.”; never write it in `model:`). Do not shorten this to “GPT-6,” omit a known variant or effort, or copy the example as a default for another writer.

Use the designated writer agent's explicit runtime model metadata and effort, not the parent chat session's identity. If there is no delegation for a small edit, use the active session's explicit metadata. Do not infer the writer from the CLI brand, a configured default, or a previous lesson. If a component is unavailable, retain the known name and explicitly mark the missing component as unspecified; never invent it. Omit effort only when the model has no such setting. A full rewrite updates the byline to its actual writer; a small explanation, quiz addition, or copy edit does not claim authorship of the whole lesson. Do not change an existing lesson just to retrofit a byline unless the user asks.

Verify the complete byline under the title after rendering. This is lesson metadata, not a claim about which model runs the board's separate quiz or Explain workers.

# Sources

Course mode: only this course's material, from `$WS/sources/` via RESOURCES.md, tiered. Never YouTube, never external explainers unless the user adds them. Label claims whose authority matters (`officially stated`, `professor emphasized`, `inferred`) in the `::: sources` drop-down; STEM lessons never carry them inline.

Self-study: find primary sources first (papers, official docs, textbooks) and record them in RESOURCES.md. Then pick one video from `## Channels` that covers the topic: `bin/yt-transcript.sh "ytsearch5:<topic> <channel>"`, save the transcript under `sources/youtube/`, cite it, and end the lesson with `::: video` embedding that exact video with `?start=` at the most relevant minute. Never embed a video that was not used.

Never trust parametric memory for facts that a source in the workspace can settle.

# Onboarding (course mode, no material yet)

When course mode is detected and `$WS/sources/` and RESOURCES.md are empty, render this on the board and stop until the user answers:

> **Set up <course>**
> Drop what you have. Paths, links, or PDFs, in any order. The more from the top of this list, the better the lessons:
> 1. Practice exams or past exams. Best. I reverse-engineer the real problems and teach the topics through them.
> 2. Official topic list or the professor's exam announcement.
> 3. Professor's review notes.
> 4. Homework and recitation sheets. I never solve your assigned problems, I teach you to.
> 5. Lecture slides or notes.
>
> Syllabus and textbook are optional. Is the course on Canvas, Moodle, Blackboard, or Brightspace? Paste the course link and I'll pull everything.

Then: paths → copy into `$WS/sources/<kind>/`, extract text, tier per RESOURCES-FORMAT.md, show the tiering once. Link → [LMS.md](./LMS.md). If any tier ≤ 4 item exists → [EXAM-MODE.md](./EXAM-MODE.md) builds the topic map. Never show this ask again for that workspace; `add` and `sync` extend it later.

If `MISSION.md` is missing, write it from the course or topic and one question at most ("what is this for: a test, a project, curiosity?").

# Lessons

Read [TEMPLATES.md](./TEMPLATES.md), including its **Didactic writing contract**, **Titles** and **Photos**, before writing or rewriting a lesson. Apply that contract to explanations as well, scaled to the requested depth. STEM lessons follow the one template: TEMPLATES.md **STEM lessons** and the model lesson [examples/stem/learn/lessons/0001-how-to-ace-your-second-integral-calculus-test.md](./examples/stem/learn/lessons/0001-how-to-ace-your-second-integral-calculus-test.md); a non-STEM template comes later. The lesson frame and its slot order are in TEMPLATES.md (**Board rules** and **Lesson frame**).

Before writing: read `learning-records/` (latest first) and `NOTES.md`. Include “Before we start” ONLY when the lesson actually builds on an earlier lesson (for example HW2 after HW1), not merely because its number is higher. Set `prev:` to that prerequisite lesson and take 1–2 relevant retrieval questions from its record, tagged `from lesson NNNN: <title>`. Omit the entire section for standalone lessons. Pick the zone of proximal development from the records and the mission; the user may also name the exact thing.

Concept sequencing: before streaming each block, check its prerequisites against the preceding blocks. Introduce the meaning of each new term, symbol, or abbreviation in plain words before using it in a rule or applying it to another concept. After writing, read the whole lesson in order and run the completion check in TEMPLATES.md before the final render. A rule name alone does not explain a step.

Figures: when to draw one and how are in [FIGURES.md](./FIGURES.md) (**When to illustrate**, templates, `bin/fig-check.sh`).

**3D and physical objects: use `anatomy`.** When the idea is a physical or spatial thing whose shape is the explanation (an engine, a gear train, a valve, a lock, a dial gauge, a relay, a pump, a bridge truss, a molecule, an organ) and a flat `::: fig` would lose the depth, invoke the `anatomy` skill (`/anatomy`) to build the figure instead of drawing it with `::: fig raw`. Ask it for a lone dark-theme SVG (`figureSvg({ standalone: "dark" })`), have the parts the lesson names be parts in the drawing, save it as `$WS/lessons/assets/NNNN-<name>.svg`, check the PNG anatomy's own checks produce, and place it beside the step it explains with `::: figure assets/NNNN-<name>.svg`, a short caption naming it, and one sentence of prose saying what to look at. The board shows it as a still: anatomy's motion and drag live in its HTML page, which the board does not embed. Abstract relationships (flows, balance sheets, graphs, K-maps) stay `::: fig`. If `anatomy` is not installed, say so in one line and fall back to `::: fig raw` or a `::: photo`.

**Visual and interactive teaching contract.** Every new or substantially rewritten lesson includes at least one instructional visual tied to a specific explanation. The banner photo does not count. Every math lesson includes a manipulable mathematical example or a meaningful inline animation; that inline visual requirement is separate from the full lesson video default above. An interaction can satisfy the inline visual requirement when it teaches the idea better than an animation, while a new full lesson still gets its teaching video unless the user requests text only. For CS execution/state topics, prefer a step-through code trace with active line, variables, output, Previous/Next, Play/Pause, and Reset. For other subjects choose the medium that exposes the mechanism: circuit-state changes, a timeline, a causal diagram, or an image with a specific observation task. Never add decorative motion just to meet the rule.

Read [INTERACTIVES.md](./INTERACTIVES.md) when authoring an interactive block. Built-in `::: interactive trace` supports verified authored execution states; `::: interactive function` supports a polynomial graph with one coefficient slider. Do not present a precomputed trace as a live compiler. For unsupported concepts use the existing SVG figure templates or implement a suitable scoped interaction; do not invent renderer syntax. Put the visual beside the paragraph it explains, give the learner one thing to change or predict, and explain what the observed change means. Keep a short static takeaway so review does not require replaying a video.

Use Manim when continuous motion or a geometric transformation is clearer as an animation: add a Scene to `board/anim/scenes.py`, render with `bin/anim.sh <Scene> <name> $WS`, and embed `::: video assets/<name>.mp4` with a short caption and a one-line observation prompt in the prose before it. Videos need replay/controls and must not autoplay in a distracting loop. A static figure is sufficient when motion adds no information, but does not by itself satisfy the math interaction/animation requirement.

Before finishing a lesson, verify the instructional visual renders; exercise interactive controls at initial, intermediate, and final states (or watch the animation); check values against the worked example; verify reset and keyboard operation. If a required visual cannot be produced, report the gap instead of claiming the lesson meets this contract.

Money and math: `$100` in prose is money and renders as typed. Inline math is `$…$` on one line with no space just inside either `$`; it may start with a digit (`$4$`, `$0.5 \cdot 2$`, `$2^{9/2}$`). Two money amounts on one line (`$5 and $10`) are fine because the would-be body ends in a space. `\$` forces a literal dollar sign.

Prose and tone: TEMPLATES.md (**Tone**, **Shape of each explanation**). Course mode only (front matter has `course:`), outside STEM lessons: a block that serves a specific exam problem ends with `→ Exam: <problem>`, context ends with `→ background`. STEM lessons and self-study lessons carry neither tag (TEMPLATES.md **STEM lessons**).

Homework rule (hard): an assigned problem is never solved, partially solved, or set up, not even "just the first step". Teach with modified-number analogs and end with a nudge naming the problem ("you now have what Problem 2 needs; think about which rows are 1").
Exception: when the user explicitly asks for the steps of their own problem ("fill the board with all steps for problem 1"), do exactly that. The rule sets the default, not a refusal.

# Board answers to side questions

A question asked in chat while a lesson is open goes on the board: append one `## ` section to the current lesson and re-render. Chat gets one line. The section is a note, not a lesson:

- **Lead with the line they were missing**, as display math, before any words. For "how do I compute $2^{9/2}$ by hand" that line is $2^{9/2} = 2^{4}\cdot 2^{1/2} = 16\sqrt{2}$.
- Then the rule in one sentence and the steps as a numbered list, one operation per step. Apply it to the user's own numbers, nothing else.
- Under 12 lines of source. No sanity checks, no decimal approximations, no second example, no "the same trick when…", no rubric talk. One `→ Exam:` tag at most, and none in a STEM lesson.
- New content stays in place without a flashing frame or forced scroll.

# Chat panel

Each lesson page has a chat panel run by the bridge (one Claude Code session per lesson, history in `$WS/reference/chat/`, instructions in `board/chat-system.md`). Details: [board/README.md](./board/README.md).

# Explain

Selecting words on the board raises **Explain**, **Definition** (1–5 words) and **Ask**. Definition is a popup answered by `bin/define.py` and never touches the lesson; write definition tables or `**Term** — …` notes so it answers instantly in the lesson's own words (details: [board/README.md](./board/README.md)).

Explain is answered by `bridge.py` running `bin/explain.py` with the lesson, source block, and selection. The worker writes an `::: exp` block. Nothing reaches the chat.

The interactive agent handles Explain when explicitly asked in chat or when the headless writer is unavailable:

1. Leave the selected paragraph untouched: no markers, underlines or inline links.
2. Insert after the source block, or inside the parent's `::: exp` for a nested request:
   ```
   ::: exp e<n> [folded]
   **<short descriptive title>** — <explanation>
   :::
   ```
   Use the next unused id. A short selection label is an acceptable title; prefer wording that identifies the question. Write enough to resolve the doubt, usually a short paragraph, with steps or equations when useful.
3. `remove <id>`: `python3 bin/exp-remove.py <lesson.md> <id>` removes that block and its children.
4. Re-render. Chat: `explained on board`.

Explanations follow TEMPLATES.md's tone rules and, for a step, the derivation rules.

# Quiz

Read [QUIZ.md](./QUIZ.md). **Every lesson ships with its quiz** (checkpoints plus the final `::: quiz`, counts in QUIZ.md), written as part of the lesson, never left as an empty panel. Flashcards are generated from the More practice panel.

The board runs the loop on its own. Speak fills the answer box from `bin/listen.sh` through the bridge, Validate grades headless in `bin/quiz.py` with a fast model, and the verdict is written back as a `::: score` block. Nothing reaches the chat. Every item is logged; a misconception seen twice goes into the learning record.

# Learning records

Write one when the user demonstrated understanding, disclosed prior knowledge, corrected a misconception, or shifted the mission. Coverage is not learning. Quiz results are the usual evidence.

# Reference documents

Lessons are rarely reread; `reference/` is. Keep a glossary once terms accumulate, and cheat sheets for syntax, formulas, and procedures. Lessons link to them.

# Wisdom

When a question needs experience rather than knowledge, answer, then point to a community from RESOURCES.md. Respect a recorded opt-out.
