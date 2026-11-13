# Full lesson video pipeline

A new **full lesson** gets a written lesson and a teaching video unless the user explicitly requests text only. This does not apply to a board explanation, temporary board, view, or chat answer. Reuse an existing video only if its lesson hash and reviewed map are valid. A changed lesson invalidates `project.json`, `anchors.json`, and the installed map. Keep the written lesson available when video credentials, a model, or rendering are blocked; report the video stage honestly.

The lesson writer is selected by `bin/lesson_routing.py` and the current user/workspace policy. That author owns the lesson. **Never replace the designated lesson author with the video author.** Once the written lesson is corrected and its routing receipt checked, video script/storyboard/scene work is assigned to actual `claude-opus-5-5` at an explicit supported effort (`high` recommended). Verify the host's runtime model metadata. A CLI receipt records supplied evidence; it cannot prove who actually ran. If the source lesson's math is wrong, stop synchronized video publication and send the discrepancy to the designated lesson author for correction first. Do not silently teach a different result in the video.

Work in an external project directory. Keep course content, audio, generated video, host logs, and secrets out of this repository. The bundled `video/` directory contains the complete runtime. Rendering needs Python 3.9+, Node 18+, `ffmpeg`/`ffprobe` with H.264 and AAC support, Playwright Chromium, and network access for the runtime's Google Fonts and KaTeX CDN assets. Narration is ElevenLabs whenever a key is present: `ELEVENLABS_API_KEY` in the environment, else the one-line file `~/.config/blackboard/elevenlabs.key` (`chmod 600`; `tts.py` refuses a file others can read). The key never goes in a project, this repo, a commit, a log or a chat. Without a key, narration falls back to local Kokoro-82M (`am_michael`): install it once with `sh bin/setup_tts.sh`, which puts a venv and weights in `~/.cache/blackboard/`. The default ElevenLabs voice is Brian, the closest to `am_michael`; leave `voice` out of `script.json` unless the user picked another (see [video/README.md](video/README.md#ttspy)). The video is blocked only when neither narrator is available; `tts.py` exits 2 with `TTS_BLOCKED` and the install line. No TTS call is needed for CLI tests.

## Exact sequence

From the Blackboard repo root, set paths to **your** lesson and external project:

```sh
BB_ROOT=$(pwd)
WS=/absolute/path/to/learn
LESSON="$WS/lessons/NNNN-slug.md"
PROJECT=/absolute/path/to/external-video-project
ID=$(basename "$LESSON" | cut -c1-4)
python3 "$BB_ROOT/bin/lesson_routing.py" resolve --workspace "$WS"
python3 "$BB_ROOT/bin/video_pipeline.py" init --lesson "$LESSON" --project "$PROJECT"
```

`init` defaults to the configured video effort `high`; supported values are exactly `low`, `medium`, and `high`. Select another value only when the host can dispatch it; an unsupported or mistyped value fails instead of falling back. It copies only the portable runtime files, plus README, package lock, and gitignore when present. It never copies `sample/`, `test/`, dependencies, or generated assets. It records the absolute lesson path and SHA-256 in `project.json` and refuses changed existing files. Repeating it after an interrupted copy is safe. It never creates `script.json`, `anchors.json`, or model receipts. `--runtime /path/to/portable-runtime` selects an explicitly reviewed alternative runtime source.

`init` also registers the project with the board (`bin/video_status.py register --project "$PROJECT"`, which writes `$WS/reference/video-project-NNNN.json`); run that by hand for a project made before this existed. From then on the lesson page shows a progress card where the video will go, until the import lands. Nobody updates it: the bridge recomputes it on each request from the project's files (`python3 "$BB_ROOT/bin/video_status.py" show --workspace "$WS" --lesson "$ID"` prints the same JSON). The stage is the first of these not yet done: script (`script.json` + `anchors.json`), narration (one audio file per spoken cue, counting Kokoro's `audio/.tmp-*.wav` files, which it renames only when the whole batch ends; `tts.done` finishes it), scenes (`scenes/<module>.js` per nonempty `SPLIT.json` module), render (`chunks/cNNNN.mp4` over the chunks in `chunks/plan.json`; `RENDERED` finishes it), review (`video-runs.json` with a passed reviewer), import. So keep those names: the card reads them.

Give the Opus video author [video-briefs/author.md](video-briefs/author.md), the lesson path, project path, current lesson routing receipt, and all source material. The author writes `script.json`, `anchors.json`, independent `mathcheck.py`, and `SPLIT.json`. Script scenes use `title`, `subtitle`, `voice`, `chapters`, `scenes`; each scene has `id`, `chapter`, `visual`, `cues`. Cues are `{ "id": "a", "say": "...", "show": "..." }` or `{ "id": "think1", "pause": 4 }`. The Opus author runs the math check and corrects its own video work; any lesson discrepancy goes back to the designated lesson author. Meaning and concrete picture precede the formula. Each worked example and question gets a visual whose quantities and geometry can be verified.

## Captions in the lesson's notation (Caio, 2026-11-02)

"The subtitles should follow the formatting of the lesson": a caption reads `$I_5 = 0$`, never "I five is zero". Every spoken cue has two texts. `say` is what the narrator speaks, math in words, for the TTS. `show` is the caption: the same words, with every symbol, subscript, complement, equation, number and value written as the lesson writes it, in `$KaTeX$` (`"say": "Row five: I five is zero."`, `"show": "Row 5: $I_5 = 0$."`). When the line quotes the lesson's math, copy the lesson's form. `show` keeps the sentences of `say` (same `.` `?` `!` `:` ends outside math) so each caption takes the time of its spoken sentence; a long sentence keeps its comma breaks or shows whole for that sentence, and a cue whose sentence count differs shows whole for the cue.

Captions are not drawn into the frames. `build-map` writes `captions.json` (each cue's `show` timed by its spoken chunks), `lesson_video.py import` installs it beside the MP4 as `lessons/assets/NNNN-lecture.captions.json`, and the board's player overlays it, with a CC switch. Fixing a caption is a script edit and `build-map`, then `lesson_video.py captions --workspace "$WS" --lesson "$ID" --captions "$PROJECT/captions.json" --replace`: no narration, no render (`tts.done` fingerprints the script without its captions). `check` fails its `captions` stage when a spoken cue has no `show`, when a `show` spells math in words ("I five", "S one", "two to the n", "x squared", "C sub 2", "C in", "A bar"), or when `captions.json` is stale; `python3 "$BB_ROOT/bin/captions.py" lint --project "$PROJECT"` lists every finding. `VIDEO_BURN_CAPTIONS=1 ./render.sh` burns the captions in for a standalone export; only then run `build-map --captions-burned-in`. The frames never carry a progress bar: the player's seek bar has the chapters.

## Pacing and practice (Caio, 2026-10-26 and 2026-11-02)

Length comes from two things: how much material there is, and how hard each part is (Caio, 2026-11-13: "complex stuff needs more careful explanation"). The pace reference is ECE 2020 lesson 0010 ("How to Ace Your Digital Logic Test"), which Caio called the right pace for its material: **20,100 lesson words became 41,883 spoken words (2.08 per lesson word), 4 h 54 min of video (14.6 minutes per 1,000 lesson words) and 83 pause-and-solve gates**. That density is `standard`. Before writing the script, rate every `##` chapter of the lesson:

| Rating | Time per lesson word | What it looks like |
|---|---|---|
| `light` | half of 0010's | Definitions, recall, reading a value off a table, plugging numbers into one formula, a step the student has already seen done. Say it once, show one example, move on. |
| `standard` | 0010's | A procedure of a few steps the student must carry out alone: simplify, convert, fill a table, trace a circuit. Every step shown, one worked example, practice. |
| `hard` | one and a half times 0010's | New notation, a long derivation, several ideas in one problem, or the step where students usually get lost. Slow down: say why each step is legal, show the intermediate values, add a second example, pause more often. |

Save the ratings as `$PROJECT/complexity.json`, with a one-line reason for each that is not `standard`:

```json
{"default": "standard", "chapters": {"1": "light", "4": "hard"}, "why": {"1": "definitions only", "4": "two-step NPV with growing annuity"}}
```

Chapters count from 1 in the order of the lesson's `##` headings. Then run `python3 "$BB_ROOT/bin/video_pipeline.py" estimate --lesson "$LESSON" --complexity "$PROJECT/complexity.json"`. It prints the minutes, spoken words and ElevenLabs characters for each chapter and in total. Rate by how hard the material is to *understand*, not by how long it is: a long chapter of easy material stays `light`, and a short chapter with one hard idea is `hard`. A one-module exam on mostly familiar material comes out well under the old whole-test figure, and that is correct.

The estimate is a target, not a cap. `check` fails its `pace` stage when the script has fewer than two thirds of the target's spoken words (steps, values or bridges were skipped) or more than one and a half times it (easy material is being padded). Lessons under 300 words are not judged. Without `complexity.json`, every chapter counts as `standard`.

- **Every concept**: say what it is and why it is needed, then build it one visible step at a time. Example for a full adder: what a half adder does and its truth table, why one is not enough, wire the first half adder, trace its outputs, wire the second, trace it, why the OR, the final values.
- **Define before use**: never put a symbol, gate, wire name or term on screen or in narration before saying what it means, in that scene or an earlier one.
- **Worked examples narrate every intermediate value**: each carry, partial sum, flipped bit, select value or wire value is said aloud and shown as it appears. No step is skipped as obvious.
- **Bridges**: one sentence links each concept to the next (why the next idea is needed now).
- **Your turn is the exam, unaided** (Caio, 2026-11-02): a practice scene shows the problem exactly as the lesson quotes it, the official text verbatim and only its original cropped figure (no redrawn diagram, no added helper table or column, no hint, no highlight), with **no narration reading or explaining it**: at most one short line such as "Your turn: pause and solve it." Then the think pause, then the solution, which may first say what the question asks, then draws and solves it step by step. `check` warns (`warnings`) when a practice segment speaks more than one short line before its pause. Lesson 0010's current video predates this rule and needs a re-render to follow it.
- **Practice from official sources**: every lesson practice item (each check-in bullet, checkpoint MCQ, practice-exam part and quiz MCQ) must be a real problem from the course's official material (past exams, practice sets, homework, official review or slides), verified against its official solution and an independent calculation; a changed-number analog or invented item is replaced by an official problem on the same skill before the video is made. The video covers **all** of them: show the full prompt, a `think` pause long enough to try it (8–20 s; longer for multi-part work), then the complete step-by-step solution with every intermediate value, and every MCQ distractor named with its mistake. `video_pipeline.py check` fails its `practice` stage when a lesson practice item has no anchored pause-and-solve segment.
- **Looks like the board**: `init` writes `look.css` from the lesson (the board's black background, or the slate photo for `board: slate`, and the lesson's accent, cycled by lesson number exactly as the board does); scenes use the CSS variables (`--acc`, `--chalk`, `--dim`, `--green`, `--red`) instead of fixed colors. `video_pipeline.py look --project` rewrites it after a front-matter change.

Then in the external project:

```sh
cd "$PROJECT"
npm install
npx playwright install chromium
python3 mathcheck.py
python3 tts.py
python3 -m json.tool timeline.json >/dev/null
python3 "$BB_ROOT/bin/video_pipeline.py" build-map --project "$PROJECT"
python3 "$BB_ROOT/bin/video_pipeline.py" check --project "$PROJECT"
```

`tts.py` supplies measured `timeline.json` and `timeline.js`. It uses ElevenLabs Brian when a key is present, else Kokoro `am_michael` (`BLACKBOARD_ELEVENLABS_VOICE` and `BLACKBOARD_TTS_VOICE` override them; see [video/README.md](video/README.md#ttspy)). Do not guess times from the script or a target length. The first `check` should report incomplete scene, receipt, and media stages; that is useful planning output, not a passing gate. `build-map` refuses stale maps; after reviewing changed anchors, use `--replace` to regenerate one. A source revision requires a **new project** and reviewed map, not a flag to bypass the SHA check.

The parent orchestrator dispatches the author and each nonempty `SPLIT.json` module builder as actual `claude-opus-5-5` at the exact effort in `project.json`, using [video-briefs/scenebuilder.md](video-briefs/scenebuilder.md) for builders. The parent keeps each child host run reference for receipt verification. A builder writes only its scene module. Each key is a basename matching `[A-Za-z0-9_-]+` and never includes `.js`; the runtime loads `scenes/<key>.js`. Run the runtime's syntax/capture/QA commands and inspect stills at cue starts, pauses, reveals, and scene end. Verify diagrams against `mathcheck.py` and the lesson: lengths/angles/arrows/axes must be physically true. A solution must remain hidden until its question's `think` cue ends. Check every multiple-choice option and trap explanation, the caption track (`captions.py lint`, then read it in the board player), clipping, and blank frames. Re-capture after fixes. The reviewer independently checks source coverage, math, animation geometry, answer timing, and the final rendered frames.

For a batch, build independent scenes in parallel but render one lesson at a time; use the shared render lock when separate workers may start renders. After all builders finish, run `node capture.mjs check` in the project. It strictly loads every module, verifies registration and order, and must exit successfully before rendering. Then run `./render.sh "$PROJECT"` from inside the project; it writes `RENDERED` only after the frame render, mux, and contact sheets succeed. The map says `captionsBurnedIn: false`, which is right for a normal render: the frames have no captions and the player overlays `captions.json`. Only a render made with `VIDEO_BURN_CAPTIONS=1`, after watching its captions, gets `build-map --captions-burned-in --replace`; the player then starts with CC off and, turned on, covers the burned box. Write `video-runs.json` **from actual dispatch and host runtime metadata**, not a scaffold. It has this shape:

```json
{
  "version": 1,
  "author": {"requested": {"model": "claude-opus-5-5", "effort": "high"}, "resolved": {"model": "claude-opus-5-5", "effort": "high"}, "outcome": "complete", "runtimeEvidence": "host log or receipt reference"},
  "builders": {"intro": {"requested": {"model": "claude-opus-5-5", "effort": "high"}, "resolved": {"model": "claude-opus-5-5", "effort": "high"}, "outcome": "complete", "runtimeEvidence": "host log or receipt reference"}},
  "reviewer": {"requested": {"model": "actual reviewer model", "effort": "actual effort"}, "resolved": {"model": "actual reviewer model", "effort": "actual effort"}, "outcome": "passed", "runtimeEvidence": "host log or receipt reference"}
}
```

Every nonempty SPLIT module needs its own builder receipt. The orchestrator compares `runtimeEvidence` to the real host record; strings and self-reports alone are insufficient. Run:

```sh
python3 "$BB_ROOT/bin/video_pipeline.py" check --project "$PROJECT"
python3 "$BB_ROOT/bin/lesson_video.py" validate --workspace "$WS" --lesson "$ID" --video "$PROJECT/final.mp4" --map "$PROJECT/video-$ID.json"
python3 "$BB_ROOT/bin/lesson_video.py" import --workspace "$WS" --lesson "$ID" --video "$PROJECT/final.mp4" --map "$PROJECT/video-$ID.json" --dry-run
python3 "$BB_ROOT/bin/lesson_video.py" import --workspace "$WS" --lesson "$ID" --video "$PROJECT/final.mp4" --map "$PROJECT/video-$ID.json"
python3 "$BB_ROOT/bin/lesson_video.py" status --workspace "$WS" --lesson "$ID"
```

`check` verifies schema, source SHA, ordered measured coverage, a pause-and-solve segment for every lesson practice item, the pace window from size and complexity, captions in notation, scene modules, supplied runtime receipts, the `RENDERED` success marker, final MP4 audio/video duration, and media freshness against script, timeline, scene, narration, and render inputs. It does not judge pedagogy or prove runtime identity. Rerun `./render.sh` after editing an input, even when the MP4 duration stays the same. The existing importer verifies the installed board schema and media duration. Use `--replace` on import only after reviewing a conflict. The lesson remains accessible without video if this chain cannot finish.

## Anchor format

`anchors.json` is authored alongside the script, with a source SHA copied from `project.json`. An anchor names the exact lesson line and scene cue span. `from` and `to` are cue IDs at their measured **start**, except `start`/`end` for scene boundaries. Every scene needs complete finite coverage, including intro, padding, and recap; segments must be in order with no gaps or overlaps. Use one segment per practice question, even when several questions share a scene.

```json
{
  "version": 1,
  "lessonSha256": "64-character SHA from project.json",
  "segments": [
    {"id":"warmup-velocity", "label":"Warm-up: velocity", "scene":"s01", "from":"start", "to":"c", "line":48, "step":null, "practice":{"pause":"think1", "reveal":"b"}},
    {"id":"warmup-derivative", "label":"Warm-up: derivative", "scene":"s01", "from":"c", "to":"end", "line":48, "step":null, "practice":{"pause":"think2", "reveal":"d"}}
  ]
}
```

The example illustrates only one scene; a real file must anchor every scene from video start to end. `line` is a nonblank 1-based line in the original Markdown. The `step` field is required but may be `null`: use `null` for check-ins or whenever the displayed row cannot be verified. A numeric `step` refers to a 1-based **visible row group in the first `aligned` derivation of the target board block**, as observed on the rendered board. The board merges note-only rows with the preceding row and its check-in reveal also counts prose and other math items, so a raw count of Markdown row separators is not that number. The CLI checks only that a numeric step is positive and the anchor line contains `\begin{aligned}`; the author and reviewer must verify the actual displayed row and line. For `align*`, `alignedat`, or mixed check-in answers, use `null` unless the board mapping was inspected. A practice segment begins before its pause and ends after its first spoken answer cue. `build-map` calculates `pauseAt` and `revealAt` from measured timing and rejects an unpaired or grouped `think` cue. The author and reviewer must confirm that the line actually supports the segment and that the on-screen reveal occurs no earlier than the measured `revealAt`.
