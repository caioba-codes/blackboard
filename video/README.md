# Lesson video runtime

Turns a narration script and a set of hand-built animated scenes into a 1920×1080, 30 fps MP4 with burned-in subtitles, plus an SRT. Each frame is a pure function of time, so a render is deterministic and can resume.

Copy the runtime files into a new project directory. A project is self-contained, and every command below runs inside it.

| Runtime file | Role |
|---|---|
| `tts.py` | Narrates every spoken cue (local Kokoro by default, ElevenLabs with a key) and measures it. Writes `timeline.json`, `timeline.js`, `narration.wav` and their fingerprint `tts.done`. |
| `engine.js`, `style.css` | Scene engine and board look (fonts, KaTeX, colors, components). |
| `index.html` | Loads `timeline.js`, `engine.js`, then the scene files named in `SPLIT.json`, and checks every registration. |
| `capture.mjs` | Strict check, QA stills, preview server, and the resumable full frame render. |
| `finish.sh` | Joins the chunks, normalizes the narration and muxes `final.mp4`, then writes `final.srt`. |
| `render.sh` | Runs the full render and `finish.sh` under a lock, makes contact sheets, then writes `RENDERED`. |
| `package.json` | Pins Playwright. |

`sample/` contains a tiny generic project (4 scenes, about 20 s) and `test/smoke.py` exercises the whole chain on it. Neither is needed at runtime, and `.gitignore` lists the generated files.

## Requirements

- macOS or Linux: `render.sh` locks with `flock(2)` through Python's `fcntl`.
- Python 3.9+ (stdlib only), Node 18+, `ffmpeg`/`ffprobe` built with libx264, libmp3lame and aac.
- Playwright Chromium: run `npm install` and `npx playwright install chromium` once per project.
- Network access during capture, because `index.html` loads Playfair Display, Crimson Pro and Patrick Hand from Google Fonts and KaTeX 0.16.11 from cdnjs.
- A narrator, needed only when a cue still has to be narrated: local Kokoro (`sh <skill>/bin/setup_tts.sh` once per machine) or `ELEVENLABS_API_KEY` in the environment.

## Project files you write

`script.json` uses this format:

```json
{
  "title": "Lesson title",
  "subtitle": "Course line · Lesson 0001",
  "voice": "XrExE9yKIg1WjnnlVkGX",
  "chapters": ["Introduction", "Chapter 1 · …", "Quiz & recap"],
  "scenes": [
    {"id": "s00", "chapter": 0, "visual": "storyboard for the scene builder",
     "cues": [{"id": "a", "say": "Narration in words, no symbols."}, {"id": "think", "pause": 5}]}
  ]
}
```

- `chapter` is an index into `chapters`. Chapter 0 hides the top-left chapter label.
- Scene and cue IDs use `[A-Za-z0-9_-]`. Each cue has either `say` or `pause` (in seconds), never both.
- `visual` is read only by the people or agents building scenes.

`SPLIT.json` maps scene files to consecutive scene IDs, for example:

```json
{"intro": ["s00", "s01"], "ch1": ["s02", "s03"], "quiz": ["s04"]}
```

- Each key is a file name `scenes/<key>.js` matching `[A-Za-z0-9_-]+`. The names are free, and nothing is fixed to chapter IDs.
- Reading the values in key order must give every scene from `timeline.json` exactly once, in timeline order. An empty list means the file is not used.
- Each file must register exactly the scenes it lists.

Each file in `scenes/<key>.js` wraps its code in an IIFE and registers its scenes:

```js
(() => {
  scene('s02', (root, S) => {          // build DOM once
    const f = S.fig({ x: 100, y: 120, w: 820, h: 800, xr: [0, 5], yr: [0, 4] });
    return t => { f.clear(); f.arrow(0, 0, 3, 1, '#6fa8dc', 6, S.p(t, S.at('a'))); };   // t = scene-local seconds
  });
})();
```

The helpers are documented at the top of `engine.js`: `S.at/end`, `S.el/txt/tex`, `S.show/wipe/pulse/p`, `S.fig`, `S.deriv`, `S.mcq`, `S.countdown`, `S.header`, `S.chapterCard(n, title, tagline[, kicker])`, and `S.sc.subs` for sentence timing. Scene code must not use CSS transitions, timers or `Math.random` (use `S.hash` instead).

## Exact calls

Run these from the project directory:

```sh
npm install && npx playwright install chromium        # once
python3 tts.py --check                                # cached vs missing cues, no API call (exit 1 if any missing)
python3 tts.py                                        # narrate missing cues → timeline.json, timeline.js, narration.wav, tts.done
python3 tts.py --verify                               # those three files come from one complete run (exit 1 otherwise)
node capture.mjs check                                # strict: SPLIT.json order + every scene registered (exit 1 otherwise)
node capture.mjs scene s05 2                          # QA stills of one scene → qa/s05_<t>.png (warns about unbuilt scenes)
node capture.mjs qa 12.5 61                           # stills at absolute times → qa/t_<t>.png
node capture.mjs serve 8137                           # preview http://127.0.0.1:8137/index.html?t=12  (?play, ?play=30)
./render.sh . 4                                       # full render with 4 workers + finish + qa/sheet_*.jpg + RENDERED
```

You can also run the full render by hand:

```sh
node capture.mjs all 4 && ./finish.sh
```

### tts.py

- Engine (`--engine` or `BLACKBOARD_TTS_ENGINE`, default `auto`): ElevenLabs when `ELEVENLABS_API_KEY` is set or every cue is already cached from it, else Kokoro-82M (Apache-2.0, runs locally, no key). With neither, it exits 2 with `TTS_BLOCKED` and the install line.
- Kokoro runs in `$BLACKBOARD_TTS_HOME/tts-venv` (default `~/.cache/blackboard`) with weights in `kokoro/`, both made by the skill's `bin/setup_tts.sh`. Voice `BLACKBOARD_TTS_VOICE`, else `script.json` `kokoroVoice`, else `af_heart`; speed `BLACKBOARD_TTS_SPEED` (1.0). Each subtitle chunk is synthesized separately and its span measured, so cue durations and subtitle times come from the audio. Cues are `audio/<scene>_<cue>.wav` plus `.wav.json`, keyed on model, voice, speed and text.
- ElevenLabs: the voice comes from `script.json` `voice` (default `XrExE9yKIg1WjnnlVkGX`). The model defaults to `eleven_v4`, with voice settings stability 0.55, similarity_boost 0.8, style 0.15, speed 0.97 and output format `mp3_44100_192`.
- `ELEVENLABS_MODEL` overrides the model. `ELEVENLABS_API_BASE` overrides the endpoint (the smoke test uses a local mock). `--workers N` sets the number of parallel requests (default 3).
- Every ElevenLabs cue is stored as `audio/<scene>_<cue>.mp3` plus `.mp3.json`, which holds the alignment and the cache key. The key is a SHA-256 of the model, voice, voice settings, output format and text. Changing any of them re-narrates only the affected cues.
- Audio cached by the earlier pipeline (key `sha1(model+voice+text)` under the same default settings) is accepted and its metadata upgraded in place, so already-narrated lessons are not paid for twice.
- Writes are atomic. Before a cue's audio is replaced, its old metadata is deleted, and the new metadata is written last, so an interrupted run leaves that cue missing (never cached under the wrong text) and resumes when you run it again.
- `narration.wav` is built to a temporary file first. Only then are `timeline.json`, `timeline.js` and `narration.wav` replaced, and `tts.done` is written last with the SHA-256 of the script and all three outputs. `--verify` checks that fingerprint against the current script, and `capture.mjs all` and `finish.sh` run it before doing anything, so a failed or interrupted run can never be rendered as a mix of new and old files. Rerunning `tts.py` (no API call when every cue is cached) writes a valid `tts.done`, including for projects narrated before it existed.
- Exit codes:
  - `0`: done.
  - `1`: `--check` found missing cues, or `--verify` found files that do not match `tts.done` (`TTS_INCOMPLETE: …`).
  - `2`: bad `script.json`, or no narrator for the cues that need one (`TTS_BLOCKED`, or ElevenLabs forced without a key).
  - `3`: quota or auth refused (`TTS_QUOTA_OR_AUTH: HTTP 401 quota_exceeded …`). The run stops at once, keeps what was cached and says how many cues are left.
  - `4`: other API failure after 6 attempts (429, 5xx and network errors are retried with backoff), or a Kokoro run failed.
- When anything fails, the previously published `timeline.json`, `timeline.js` and `narration.wav` are left as they were.

### capture.mjs

- Serves the project on a private `127.0.0.1` port, because browsers will not fetch `SPLIT.json` from `file://`.
- `check` and `all` load strictly: a SPLIT order mismatch, a missing or duplicate scene, a file that fails to load, or a scene registered by the wrong file prints `LOAD_FAILED` with the reason and exits 1 before any frame is rendered.
- `scene` and `qa` are lenient about scene files that are not built yet. They print `WARNINGS`, so scene builders can work in parallel.
- `all` first runs `python3 tts.py --verify` and stops with `RENDER_FAILED: TTS_INCOMPLETE …` if the timeline and narration are not one complete `tts.py` output.
- `all [workers]` uses the argument, else `VIDEO_WORKERS`, else min(4, CPUs), and never more than the CPU count. It renders fixed chunks of `VIDEO_CHUNK_SECONDS` (default 60 s), each H.264 (libx264 medium, CRF 17) from JPEG q93 frames.
  - Each chunk is renamed into place only when it is complete, and `chunks/plan.json` fingerprints every frame input: `timeline.json`, `timeline.js`, `engine.js`, `style.css`, `index.html`, `capture.mjs`, `SPLIT.json`, the scene files it lists and every file under `assets/`. Keep local images and other files scenes load in `assets/`.
  - A rerun skips finished chunks. Changing any input discards the old chunks.
  - A page exception or an ffmpeg failure, including ffmpeg exiting before or while a frame is written, prints `RENDER_FAILED`, exits 1 and keeps the finished chunks.

### finish.sh

- First runs `python3 tts.py --verify` and stops if it fails.
- Normalizes the narration with two-pass loudnorm (I = −16 LUFS, TP = −1.5 dBTP, LRA = 11) at 48 kHz.
- Muxes `final.mp4` (H.264 copied from the chunks, AAC 192k, `+faststart`) and writes `final.srt` from the subtitle chunks in the timeline. Both files are written to a temporary name and then moved into place.
- Prints the stream summary, integrated loudness and true peak.

### render.sh `[project-dir] [workers]`

- Allows one render per project with an exclusive kernel lock (`flock`) on the file `<project>/.render.lock`, whose content is the holder's PID (informational only). A held lock gives exit 75 at once.
- The kernel releases the lock when the last process of the render exits (`render.sh`, `node`, ffmpeg, Chromium), so a crashed or killed render leaves nothing stale and there is no takeover step. The file stays in place on purpose: do not delete it.
- For optional machine-wide serialization, set `VIDEO_RENDER_LOCK=/path/to/lockfile` (a file, created if missing, in an existing directory). `VIDEO_RENDER_LOCK_WAIT` is the number of seconds to wait for it (default 0), and the wait is bounded.
- A `.render.lock` directory left by an older `render.sh` stops the render with a message. Remove it once no render is running.
- Logs go to `render.log` and `finish.log`. A failure prints `RENDER_FAILED` or `FINISH_FAILED` and exits 1, and rerunning resumes. On success it writes `RENDERED`.

## Smoke test

This test makes no paid API call:

```sh
python3 video/test/smoke.py            # full: TTS mock, SPLIT checks, stills, chunked render + resume, finish, render.sh locks, injected failures
python3 video/test/smoke.py --quick    # skip the render/finish/render.sh part
VIDEO_NODE_MODULES=/path/with/playwright/node_modules python3 video/test/smoke.py   # skip npm install
```

Failures are injected at the real boundaries: `tts.py` killed between a cue's audio and its metadata; narration assembly failing (ffmpeg replaced on PATH); a timeline and WAV that do not belong together; an encoder exiting before or partway through a frame; a render killed outright, then 8 concurrent renders, with the steps jittered; edits to an asset and to `capture.mjs` after a render.

## Notes

- The output pixel format is H.264 High 4:2:0 full range (`yuvj420p`), from JPEG frames piped into x264. It is the same as the lesson videos already produced with this engine.
- The engine preloads every KaTeX font face before any scene is built, so layouts measured at build time are stable.
- `S.chapterCard` takes an optional `kicker` to replace the "Chapter n" tag.
