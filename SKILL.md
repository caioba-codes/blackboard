---
name: blackboard
description: Opens and teaches on a persistent black board when the user invokes /blackboard or $blackboard, or asks to open the blackboard, open lessons, or show a lesson. Course mode uses the user's material or LMS; self-study uses primary sources.
---

# Blackboard

**Scope:** Open, write, and explain lessons on the board. **Precedence:** Direct user instructions come first. **Autonomy:** Pick the writer model, dispatch writing and tone editing, recompute answers. **Success/stop:** Publish only after the lesson checks pass; report concrete blockers.

## Temporary board

"temporary board", "blackboard temporário", "solve X on a plain board": a throwaway page with only what was asked, no banner photo, no lesson number or course line, no byline, no quiz, no check-ins, no learning record. Write it to `~/.cache/blackboard/scratch/learn/lessons/NNNN-slug.md` (next free number; outside every course folder) with front matter `plain: true` (plus `title:` only if a heading helps), render it with `BLACKBOARD_LAYOUT=app board/render.sh <file>` so nothing opens on its own, then open `http://localhost:7331/w/scratch/lessons/NNNN` in a new tab of this host's browser pane. The content still follows TEMPLATES.md **Derivations**.

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

# Lesson writer (required)

Before a new lesson or substantial rewrite, read [LESSON-WRITER.md](./LESSON-WRITER.md): pick the best model online, a separate writer agent writes, a fresh tone editor on the same model edits prose, and answers are recomputed independently before publishing.

# Full lesson video (default)

Every new full lesson includes both the written lesson and its video unless the user explicitly asks for text only. This does not apply to view/open, Explain, side questions, chat answers, or temporary boards. Read [VIDEO.md](./VIDEO.md) for the exact project commands, Opus 5.5 visual builder role (high effort recommended), optional user-authorized script author role, source-anchor schema, measured timing map, QA, and import gates. The video roles are separate from the lesson writer, whose byline stays. If source math differs from independent video math, the lesson writer corrects and rechecks the written lesson first; then rebuild the video against its new SHA. A missing video credential, model, or runtime blocks the video stage with an explicit report, while the written lesson remains available.

# Modes

`$ARGUMENTS` starts with one of:

- `learn <topic> [for <course>]` — write and render a lesson (default when the first word is not a mode).
- `remove <id>` — delete an explanation block.
- `add <path|url>` — add material to the workspace and re-tier.
- `sync` — re-pull the LMS course.
- `image NNNN` — re-roll the lesson photo.
- `grid` — open the lessons hub (`/lessons`): every lesson in every folder the board knows about, with search and folder chips.

# Workspace

`$WS` is the workspace root. Resolve it once per session:

1. `./learn/MISSION.md` exists → `$WS=./learn`
2. otherwise `$WS=./learn`, created on the first lesson. Never create `learn/learn`.

Files under `$WS` (formats linked):

- `MISSION.md` — why the user is learning this. [MISSION-FORMAT.md](./MISSION-FORMAT.md)
- `RESOURCES.md` — trusted sources with `kind` and `tier`. [RESOURCES-FORMAT.md](./RESOURCES-FORMAT.md)
- `sources/` — course files and extracted text. [LMS.md](./LMS.md)
- `lessons/NNNN-slug.md` — lessons, markdown + LaTeX. `lessons/assets/` holds photos, cropped figures, Manim clips and lesson videos.
- `reference/*.md` — cheat sheets and glossaries.
- `reference/chat/NNNN.json` — the board chat's history for lesson NNNN (see Chat). New chat renames it to `NNNN-<time>.json`.
- `learning-records/NNNN-slug.md` and `quiz-log.jsonl`. [LEARNING-RECORD-FORMAT.md](./LEARNING-RECORD-FORMAT.md)
- `NOTES.md` — the user's preferences about how they want to be taught.

Course mode vs self-study: a course is named in the command, or `MISSION.md` names one → course mode. Otherwise self-study. If both fit (no course named, a course workspace exists, and the topic is in its scope) ask once: "For <course> or on your own?"

# The board

The board is a web page served by `board/bridge.py` at `http://127.0.0.1:7331`. Explain, quiz generation and quiz grading all run headless inside the bridge, so they behave the same in every host and never type into the chat. `board/render.sh <lesson.md>` starts the bridge if needed, opens the board once per host, and renders the file. The page updates itself (SSE); never open a second tab or pane. Hosts are auto-detected ([HOSTS.md](./HOSTS.md)), except the Codex desktop app: there run `BLACKBOARD_LAYOUT=app board/render.sh …` and open `http://127.0.0.1:7331/` in the in-app browser with the browser tool, once per session, so the board sits beside the chat. A read-only sandbox cannot run the board: say so in one line and stop; never answer the lesson in chat instead.

**One bridge, every workspace.** A single bridge on 7331 serves every course; each workspace gets its own slug and URL (`/w/<slug>/`), and `/lessons` is the hub across every folder. Never start a second bridge or use another port for lessons (the only exception is the dev board of `bin/dev.sh`). How the page behaves (top bar, XP bar, reading scale, the being-written state, sounds, quiz cards, Explain and Definition popups, chat panel, slate surface): [board/README.md](./board/README.md).

Headings are the navigation: name them by what the section does, and put each problem or major part at `##` so it gets a mark on the reading scale. `**Step N · …**` at the start of a paragraph is boxed as a sub-step. `board: slate` in front matter gives the lesson a real-blackboard surface (on trial).

**Codex desktop app.** Run the renderer with `BLACKBOARD_LAYOUT=app` (it also auto-detects `CODEX_INTERNAL_ORIGINATOR_OVERRIDE=Codex Desktop`). After the first successful render in a task:

1. Use the in-app Browser tool to create a tab, navigate that tab to `http://127.0.0.1:7331/`, verify the lesson title, and mark the tab as a deliverable so it survives the turn.
2. Call `codex_app__open_in_codex` with `target: {type: "browser", tabId: <the Browser tab's id>}` and `placement: "right"` so that exact navigated tab is presented beside chat. The app action may report `queued`; finish the turn so it can present the tab.

The tools may be deferred, so find them by exact name before concluding they are unavailable. Do not pass an app/provider tab id discovered elsewhere and do not call macOS `open`; both paths can leave a blank tab. Reuse the same Browser tab for later renders because SSE refreshes it.

**Streaming rule.** Show the lesson while it is written:

1. Write the front matter (`title`, `course`, `exam`, `model`, `image`) and run `board/render.sh <lesson.md> --live`. **The parent does this first, before course research.** The banner rules are in TEMPLATES.md **Photos**; before finishing, check that the front matter has `photo:`.
2. Write the `::: contents` block with every planned chapter first. The board shows each planned chapter as a "being written" row and counts progress from it.
3. Append the rest block by block, each with its own write, and never rewrite earlier blocks while writing (a rewrite rebuilds the page).
4. When the lesson is complete, run `board/render.sh <lesson.md>` (clears the live flag).

**One-line delivery messages.** After rendering: `On the board: 0004 Sum of Products from a Truth Table`. After a board explanation: `explained on board`. After a board quiz item: the score, one line.

# Chat answers

Chat gets one line. Math, steps and explanations go on the board: with a lesson open, as a side-question section in that lesson (**Board answers to side questions** below); with none open, on a temporary board. The one line says what landed and links to it. In terminal chat that line is plain text with readable Unicode math (NOT A, A · B), never raw LaTeX. Reply in the user's language.

# Lesson blueprints (required)

A lesson has exactly one of three shapes. Pick it before writing:

- Course mode, STEM subject (math, physics, engineering, CS) → [BLUEPRINT-STEM.md](./BLUEPRINT-STEM.md): exam-first, one chapter per problem type.
- Course mode, any other subject → [BLUEPRINT-HUMANITIES.md](./BLUEPRINT-HUMANITIES.md): exam-first, one chapter per question type, flashcards for recall.
- Self-study, no course → [BLUEPRINT-FUN.md](./BLUEPRINT-FUN.md): chapters are the questions a curious person asks.

Every lesson starts with its title, a collapsed **Contents** (`::: contents`, chapter links with a brief phrase each) and a collapsed **Sources** (`::: sources`). The rest follows the blueprint. TEMPLATES.md holds the rules all three share, including the **Lesson frame**.

# Author byline

`model:` in front matter is the actual writer's full name, with variant and effort when known (`GPT-6 Astra Medium`; the board adds "Prof.").

# Sources

Course mode: only this course's material, from `$WS/sources/` via RESOURCES.md, tiered. Never YouTube, never external explainers unless the user adds them. Label claims whose authority matters (`officially stated`, `professor emphasized`, `inferred`) in the `::: sources` drop-down; lessons never carry them inline.

Self-study: find primary sources first (papers, official docs, textbooks) and record them in RESOURCES.md. Then pick one video from `## Channels` that covers the topic: `bin/yt-transcript.sh "ytsearch5:<topic> <channel>"`, save the transcript under `sources/youtube/`, cite it, and put it under `## Extra` at the end (BLUEPRINT-FUN.md **End**) as a `::: video` embedding that exact video with `?start=` at the most relevant minute. Never embed a video that was not used.

Never trust parametric memory for facts that a source in the workspace can settle.

# Onboarding (course mode, no material yet)

When course mode is detected and `$WS/sources/` and RESOURCES.md are empty, render this on the board and stop until the user answers:

> **Set up <course>**
> Drop what you have. Paths, links, or PDFs, in any order. The more from the top of this list, the better the lessons:
> 1. Practice exams or past exams. Best. I reverse-engineer the real problems and teach the topics through them.
> 2. Official topic list or the professor's exam announcement.
> 3. Professor's review notes.
> 4. Homework and recitation sheets.
> 5. Lecture slides or notes.
>
> Syllabus and textbook are optional. Is the course on Canvas, Moodle, Blackboard, or Brightspace? Paste the course link and I'll pull everything.

Then: paths → copy into `$WS/sources/<kind>/`, extract text, tier per RESOURCES-FORMAT.md, show the tiering once. Link → [LMS.md](./LMS.md). Never show this ask again for that workspace; `add` and `sync` extend it later.

If `MISSION.md` is missing, write it from the course or topic and one question at most ("what is this for: a test, a project, curiosity?").

# Lessons

**Source check (hard rule, course mode).** Before writing any lesson, before model selection or a single body block, check that every source the lesson depends on exists in `$WS/sources/` (or the course's LMS mirror): (1) the official review sheet(s) for the exam or topic, (2) past exams **with their answer keys**, (3) lecture notes or slides for every topic covered, (4) the homework or WebWork sets for those topics, (5) the syllabus or official topic list that says what the exam covers. For each one that is missing, try to fetch it from the LMS ([LMS.md](./LMS.md)). If any is still missing, tell the user in one short message which sources are missing and what they can drop in. A missing past exam or official review for this exact test does not block: use the next official problem sources in the blueprint's order (**Problem sources**) and say in Sources which were used. **Stop** without writing, outlining or streaming only when the course has no official problems of any kind. Self-study lessons and temporary boards are exempt.

Read [TEMPLATES.md](./TEMPLATES.md), including its **Didactic writing contract**, **Titles** and **Photos**, before writing or rewriting a lesson. Apply that contract to explanations as well, scaled to the requested depth. Then read the blueprint the lesson uses (**Lesson blueprints** above).

Before writing: read `learning-records/` (latest first) and `NOTES.md`. Pick the zone of proximal development from the records and the mission; the user may also name the exact thing.

Before the final render, run TEMPLATES.md **Before the final render**.

Figures: when to draw one and how are in [FIGURES.md](./FIGURES.md) (**When to illustrate**, templates, `bin/fig-check.sh`).

**Visuals are optional.** Add a figure, interactive or animation only when it makes the solution easier to follow; never a decorative one. Put it beside the step it explains.

- Physical or spatial objects whose shape is the explanation: build the figure with the `anatomy` skill as a dark-theme SVG and place it with `::: figure assets/NNNN-<name>.svg`.
- Interactive blocks (`::: interactive trace`, `::: interactive function`): [INTERACTIVES.md](./INTERACTIVES.md).
- Continuous motion: a Manim scene in `board/anim/scenes.py`, rendered with `bin/anim.sh <Scene> <name> $WS`, embedded as `::: video assets/<name>.mp4`.

# Board answers to side questions

A question asked in chat while a lesson is open goes on the board: append one `## ` section to the current lesson and re-render. Chat gets one line. The section is a note, not a lesson:

- **Lead with the line they were missing**, as display math, before any words. For "how do I compute $2^{9/2}$ by hand" that line is $2^{9/2} = 2^{4}\cdot 2^{1/2} = 16\sqrt{2}$.
- Then the rule in one sentence and the steps as a numbered list, one operation per step. Apply it to the user's own numbers, nothing else.
- Under 12 lines of source. No sanity checks, no decimal approximations, no second example, no "the same trick when…", no rubric talk.
- New content stays in place without a flashing frame or forced scroll.

# Chat panel

Each lesson page has a chat panel run by the bridge (one Claude Code session per lesson, history in `$WS/reference/chat/`, instructions in `board/chat-system.md`). Details: [board/README.md](./board/README.md).

# Explain

Selecting words on the board raises **Explain**, **Definition** (1–5 words) and **Ask**. Definition is a popup answered by `bin/define.py` and never touches the lesson; write definition tables or `**Term** — …` notes so it answers instantly in the lesson's own words (details: [board/README.md](./board/README.md)).

Explain is answered by `bridge.py` running `bin/explain.py` with the lesson, source block, and selection. The worker writes an `::: exp` block. Nothing reaches the chat.

The interactive agent handles Explain when explicitly asked in chat:

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

Read [QUIZ.md](./QUIZ.md). The practice is part of the lesson and its blueprint says what it is: Your turns, a mixed drill and a practice exam (STEM); Your turns, flashcards, a mixed set and a practice exam (humanities); an optional 2 to 3 question quiz (self-study). It is written with the lesson, never left as an empty panel.

The board runs the loop on its own. Speak fills the answer box from `bin/listen.sh` through the bridge, Validate grades headless in `bin/quiz.py` with a fast model, and the verdict is written back as a `::: score` block. Nothing reaches the chat. Every item is logged; a misconception seen twice goes into the learning record.

# Learning records

Write one when the user demonstrated understanding, disclosed prior knowledge, corrected a misconception, or shifted the mission. Coverage is not learning. Quiz results are the usual evidence.

# Reference documents

Lessons are rarely reread; `reference/` is. Keep a glossary once terms accumulate, and cheat sheets for syntax, formulas, and procedures. Lessons link to them.
