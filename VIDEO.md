# Full lesson video pipeline

A new **full lesson** gets a written lesson and a teaching video unless the user explicitly requests text only. This does not apply to a board explanation, temporary board, view, or chat answer. Reuse an existing video only if its lesson hash and reviewed map are valid. A changed lesson invalidates `project.json`, `anchors.json`, and the installed map. Keep the written lesson available when video credentials, a model, or rendering are blocked; report the video stage honestly.

The lesson writer is selected by `bin/lesson_routing.py` and the current user/workspace policy. That author owns the lesson. **Never replace the designated lesson author with the video author.** Once the written lesson is corrected and its routing receipt checked, video script/storyboard/scene work is assigned to actual `claude-opus-5-5` at an explicit supported effort (`high` recommended). Verify the host's runtime model metadata. A CLI receipt records supplied evidence; it cannot prove who actually ran. If the source lesson's math is wrong, stop synchronized video publication and send the discrepancy to the designated lesson author for correction first. Do not silently teach a different result in the video.

Work in an external project directory. Keep course content, audio, generated video, host logs, and secrets out of this repository. The bundled `video/` directory contains the complete runtime. Rendering needs Python 3.9+, Node 18+, `ffmpeg`/`ffprobe` with H.264 and AAC support, Playwright Chromium, and network access for the runtime's Google Fonts and KaTeX CDN assets. Narration is local Kokoro-82M by default (no key): install it once with `sh bin/setup_tts.sh`, which puts a venv and weights in `~/.cache/blackboard/`, never in a project or this repo. ElevenLabs is used instead when `ELEVENLABS_API_KEY` is set in the environment (never stored in a project file). The video is blocked only when neither is available; `tts.py` exits 2 with `TTS_BLOCKED` and the install line. No TTS call is needed for CLI tests.

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

Give the Opus video author [video-briefs/author.md](video-briefs/author.md), the lesson path, project path, current lesson routing receipt, and all source material. The author writes `script.json`, `anchors.json`, independent `mathcheck.py`, and `SPLIT.json`. Script scenes use `title`, `subtitle`, `voice`, `chapters`, `scenes`; each scene has `id`, `chapter`, `visual`, `cues`. Cues are `{ "id": "a", "say": "..." }` or `{ "id": "think1", "pause": 4 }`. The Opus author runs the math check and corrects its own video work; any lesson discrepancy goes back to the designated lesson author. Meaning and concrete picture precede the formula. Each worked example and question gets a visual whose quantities and geometry can be verified.

## Pacing and practice (Caio, 2026-10-26)

A video that jumps from concept to concept fails, whatever its length. There is **no length cap or target**: the video runs as many minutes as it takes to be easy to follow.

- **Every concept**: say what it is and why it is needed, then build it one visible step at a time. Example for a full adder: what a half adder does and its truth table, why one is not enough, wire the first half adder, trace its outputs, wire the second, trace it, why the OR, the final values.
- **Define before use**: never put a symbol, gate, wire name or term on screen or in narration before saying what it means, in that scene or an earlier one.
- **Worked examples narrate every intermediate value**: each carry, partial sum, flipped bit, select value or wire value is said aloud and shown as it appears. No step is skipped as obvious.
- **Bridges**: one sentence links each concept to the next (why the next idea is needed now).
- **Practice from official sources**: every lesson practice item (each check-in bullet, checkpoint MCQ, practice-exam part and quiz MCQ) must be a real problem from the course's official material (past exams, practice sets, homework, official review or slides), verified against its official solution and an independent calculation; a changed-number analog or invented item is replaced by an official problem on the same skill before the video is made. The video covers **all** of them: show the full prompt, a `think` pause long enough to try it (8–20 s; longer for multi-part work), then the complete step-by-step solution with every intermediate value, and every MCQ distractor named with its mistake. `video_pipeline.py check` fails its `practice` stage when a lesson practice item has no anchored pause-and-solve segment.

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

`tts.py` supplies measured `timeline.json` and `timeline.js`. It uses the runtime's configured voice (Kokoro `am_michael` unless `BLACKBOARD_TTS_VOICE` says otherwise; see [video/README.md](video/README.md#ttspy)). Do not guess times from the script or a target length. The first `check` should report incomplete scene, receipt, and media stages; that is useful planning output, not a passing gate. `build-map` refuses stale maps; after reviewing changed anchors, use `--replace` to regenerate one. A source revision requires a **new project** and reviewed map, not a flag to bypass the SHA check.

The parent orchestrator dispatches the author and each nonempty `SPLIT.json` module builder as actual `claude-opus-5-5` at the exact effort in `project.json`, using [video-briefs/scenebuilder.md](video-briefs/scenebuilder.md) for builders. The parent keeps each child host run reference for receipt verification. A builder writes only its scene module. Each key is a basename matching `[A-Za-z0-9_-]+` and never includes `.js`; the runtime loads `scenes/<key>.js`. Run the runtime's syntax/capture/QA commands and inspect stills at cue starts, pauses, reveals, and scene end. Verify diagrams against `mathcheck.py` and the lesson: lengths/angles/arrows/axes must be physically true. A solution must remain hidden until its question's `think` cue ends. Check every multiple-choice option and trap explanation, subtitles, clipping, and blank frames. Re-capture after fixes. The reviewer independently checks source coverage, math, animation geometry, answer timing, and the final rendered frames.

For a batch, build independent scenes in parallel but render one lesson at a time; use the shared render lock when separate workers may start renders. After all builders finish, run `node capture.mjs check` in the project. It strictly loads every module, verifies registration and order, and must exit successfully before rendering. Then run `./render.sh "$PROJECT"` from inside the project; it writes `RENDERED` only after the frame render, mux, and contact sheets succeed. The initial map says `captionsBurnedIn: false`. After watching the rendered captions, run `python3 "$BB_ROOT/bin/video_pipeline.py" build-map --project "$PROJECT" --captions-burned-in --replace` to mark them as verified; if captions were not burned in, leave the field false. Write `video-runs.json` **from actual dispatch and host runtime metadata**, not a scaffold. It has this shape:

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

`check` verifies schema, source SHA, ordered measured coverage, a pause-and-solve segment for every lesson practice item, scene modules, supplied runtime receipts, the `RENDERED` success marker, final MP4 audio/video duration, and media freshness against script, timeline, scene, narration, and render inputs. It does not judge pedagogy or prove runtime identity. Rerun `./render.sh` after editing an input, even when the MP4 duration stays the same. The existing importer verifies the installed board schema and media duration. Use `--replace` on import only after reviewing a conflict. The lesson remains accessible without video if this chain cannot finish.

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
