# Import an existing lesson video

Use this when the MP4 already exists and its lesson to video map has been reviewed. The importer does not create a map or judge whether its explanations match the lesson. Review every segment against the video and lesson first, especially practice pauses and reveal times.

```sh
python3 bin/lesson_video.py validate --workspace /path/to/course/learn --lesson 0013 --video /path/to/final.mp4 --map /path/to/reviewed-video-0013.json
python3 bin/lesson_video.py import --workspace /path/to/course/learn --lesson 0013 --video /path/to/final.mp4 --map /path/to/reviewed-video-0013.json --dry-run
python3 bin/lesson_video.py import --workspace /path/to/course/learn --lesson 0013 --video /path/to/final.mp4 --map /path/to/reviewed-video-0013.json
python3 bin/lesson_video.py status --workspace /path/to/course/learn --lesson 0013
```

`import` requires `ffprobe` on `PATH` to check the MP4's video stream and duration. `validate` checks duration when `ffprobe` is available; it reports when that check is skipped. The map's duration must be within 0.5 seconds of the MP4. An identical repeat import is a no-op. If an installed file differs, import stops; pass `--replace` only after reviewing the conflict. Replacement retains timestamp-independent unique `.bak-...` files beside the replaced files and reports their paths. The importer never edits lessons or learning records.

The map is JSON with exactly these top-level keys:

```json
{
  "version": 1,
  "lessonId": "0013",
  "lessonSha256": "<SHA-256 of the entire current lesson Markdown file, as bytes>",
  "video": "0013-lecture.mp4",
  "duration": 10.0,
  "captionsBurnedIn": true,
  "segments": [
    {"id": "opening", "label": "Opening idea", "start": 0, "end": 5, "line": 1, "step": null, "practice": null},
    {"id": "try-it", "label": "Try it", "start": 5, "end": 10, "line": 12, "step": null,
     "practice": {"pauseAt": 6, "revealAt": 8}}
  ]
}
```

`line` is a 1-based line in the original lesson source, not a rendered block ID. Times are seconds; intervals are ascending, do not overlap, and use an exclusive `end`. Covering the whole MP4 is preferred. Use `step` only where a verified derivation step is supported; otherwise use `null`. A practice gate's `pauseAt` and `revealAt` must both fall inside its segment, with the pause before the reveal. The map hash must match the current lesson exactly. The board's installed manifest validator enforces this structure during validation and import.

The player's seek bar has one zone per lesson chapter, taken from the lesson's `## ` headings: a segment belongs to the last heading at or above its `line`, or to the chapter its label names ("Chapter 3 card", "Practice exam intro", "Quiz 1: …"), so a map whose lines drifted after an edit still lands in the right zone. Segments before the first `## ` heading form an Introduction zone, a chapter the video does not cover gets no zone, and practice pauses are not drawn on the bar.

## Captions

The frames carry no captions. The caption track, `captions.json` from `video_pipeline.py build-map` (every cue's `show` text in the lesson's notation, timed by the narration), is installed beside the MP4 as `lessons/assets/NNNN-lecture.captions.json`. `import` carries `captions.json` from the map's folder (or `--captions FILE`) and checks its lesson, video and duration. To add or fix only the captions of an installed video, with no render and no new map:

```sh
python3 bin/lesson_video.py captions --workspace /path/to/course/learn --lesson 0013 --captions /path/to/captions.json [--replace] [--dry-run]
```

```json
{"version": 1, "lessonId": "0013", "video": "0013-lecture.mp4", "duration": 10.0,
 "cues": [{"s": 1.2, "e": 2.9, "text": "Row 5: $I_5 = 0$."}]}
```

`s` and `e` are absolute seconds. The player shows a caption from 0.05 s before `s` to 0.35 s after `e`, renders `$…$` with KaTeX in the lesson's font, and has a CC switch remembered in the browser. `captionsBurnedIn: true` in the map (a video rendered with captions in its frames) starts CC off; turned on, the overlay covers the burned box. An optional `"progressBarBurnedIn": true` in the track hides the progress strip that older renders drew at the foot of the frame.
