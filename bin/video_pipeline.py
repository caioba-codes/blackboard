#!/usr/bin/env python3
"""Prepare and validate a source-anchored Blackboard lesson video project."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import captions  # noqa: E402  (bin/captions.py: say/show alignment, spelled-math lint, the caption track)
import video_status  # noqa: E402  (bin/video_status.py: the board's live progress card)


ROLE = {"model": "claude-opus-5-5", "effort": "high"}
RUNTIME = ("engine.js", "style.css", "capture.mjs", "finish.sh", "tts.py", "index.html", "package.json", "render.sh")
OPTIONAL_RUNTIME = ("README.md", "package-lock.json", ".gitignore")
VIDEO_EFFORTS = frozenset(("low", "medium", "high"))
# The pace reference is ECE 2020 lesson 0010 (2026-11-02, Caio: "this is the right length / pace"): 20,100 lesson words
# became 41,883 spoken words, 204,456 narrated characters and 4 h 54 min of video with 83 pause-and-solve gates.
PACE_REF = {"lesson": "ece2020 0010", "spoken_per_lesson_word": 2.08, "minutes_per_1000_lesson_words": 14.6,
            "chars_per_spoken_word": 4.88}
PACE_FLOOR = 0.67   # check fails below two thirds of the reference density: the video is rushing the material
ACCENTS = {"red": "#9b3a4a", "blue": "#3f6f9b", "green": "#4a8b5f", "amber": "#a8762f", "violet": "#7a5a9b", "teal": "#3d8080"}
ACCENT_ORDER = ("red", "blue", "green", "amber", "violet", "teal")   # the board's cycle (board.html.tmpl applyAccent)
EPS = 0.02


class PipelineError(ValueError):
    pass


def read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PipelineError(f"{path}: {exc}") from exc


def write_new(path, data):
    raw = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode()
    if path.exists():
        if path.read_bytes() != raw:
            raise PipelineError(f"{path}: already exists with different content; inspect it before retrying")
        return
    path.write_bytes(raw)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project(project_dir):
    config = read(project_dir / "project.json")
    if not isinstance(config, dict) or set(config) != {"version", "lesson", "lessonSha256", "videoRole"} or config["version"] != 1:
        raise PipelineError("project.json: invalid project schema")
    role = config["videoRole"]
    if not isinstance(role, dict) or set(role) != {"model", "effort"} or role["model"] != ROLE["model"] or not isinstance(role["effort"], str) or role["effort"] not in VIDEO_EFFORTS:
        raise PipelineError("project.json: required Opus 5.5 model and supported video effort (low, medium, high)")
    if not isinstance(config["lesson"], str) or not isinstance(config["lessonSha256"], str):
        raise PipelineError("project.json: lesson path and SHA must be strings")
    lesson = Path(config["lesson"])
    if not lesson.is_absolute() or not lesson.is_file():
        raise PipelineError(f"lesson is missing: {lesson}")
    if sha(lesson) != config["lessonSha256"]:
        raise PipelineError("lesson changed since init; obtain designated lesson-author correction and create a fresh video project")
    if not lesson.name[:4].isascii() or not lesson.name[:4].isdigit() or lesson.name[4:5] != "-":
        raise PipelineError("lesson filename must begin NNNN-")
    return config, lesson, lesson.name[:4]


def init(args):
    lesson = args.lesson.expanduser().resolve(strict=True)
    if not lesson.is_file() or not lesson.name[:4].isascii() or not lesson.name[:4].isdigit() or lesson.name[4:5] != "-":
        raise PipelineError("--lesson must be an existing NNNN-*.md file")
    dest = args.project.expanduser().resolve()
    runtime = args.runtime.expanduser().resolve()
    if not runtime.is_dir():
        raise PipelineError(f"runtime absent: {runtime}; integration must copy video/ first or pass --runtime")
    missing = [name for name in RUNTIME if not (runtime / name).is_file()]
    if missing:
        raise PipelineError("runtime missing: " + ", ".join(missing))
    if dest == runtime or runtime.is_relative_to(dest) or dest.is_relative_to(runtime):
        raise PipelineError("project and runtime paths overlap")
    if args.video_effort not in VIDEO_EFFORTS:
        raise PipelineError("--video-effort must be low, medium, or high")
    dest.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink():
        raise PipelineError("project cannot be a symlink")
    config = {"version": 1, "lesson": str(lesson), "lessonSha256": sha(lesson),
              "videoRole": {"model": ROLE["model"], "effort": args.video_effort}}
    # Check conflicts before the first copy, so retrying an interrupted init is safe.
    entries = [runtime / name for name in (*RUNTIME, *OPTIONAL_RUNTIME) if (runtime / name).exists() or (runtime / name).is_symlink()]
    for src in entries:
        target = dest / src.name
        if src.is_symlink() or target.is_symlink():
            raise PipelineError(f"runtime symlink at {src} or {target}; inspect before retrying")
        if not src.is_file() or (target.exists() and (not target.is_file() or sha(src) != sha(target))):
            raise PipelineError(f"runtime conflict at {target}; preserve local work and inspect before retrying")
    if (dest / "project.json").exists() and read(dest / "project.json") != config:
        raise PipelineError("project.json already targets a different lesson or lesson revision")
    for src in entries:
        target = dest / src.name
        if not target.exists():
            shutil.copy2(src, target)
    write_new(dest / "project.json", config)
    write_look(lesson, dest)
    try:
        print(f"board progress card: {video_status.register(dest)}")
    except (ValueError, OSError) as exc:
        print(f"board progress card not registered: {exc}", file=sys.stderr)
    print(f"initialized {dest}; lesson SHA-256 {config['lessonSha256']}; video author {ROLE['model']} {args.video_effort}")
    print("next: author script.json and anchors.json from the lesson; no model receipt was generated")


def front_matter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return dict(re.findall(r"^([A-Za-z_]+):[ \t]*(.*?)[ \t]*$", m.group(1), re.M)) if m else {}


def lesson_words(text):
    """Words a reader sees: no front matter, no HTML comments."""
    body = re.sub(r"<!--.*?-->", "", re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S), flags=re.S)
    return len(re.findall(r"[A-Za-z0-9]+", body))


def lesson_look(lesson):
    """The board's look for this lesson: accent (front matter, else the board's cycle by lesson number) and surface."""
    fm = front_matter(lesson.read_text(encoding="utf-8"))
    def accent(value, fallback):
        k = str(value or "").strip().lower()
        return ACCENTS.get(k) or (k if re.fullmatch(r"#[0-9a-f]{3,8}", k) else fallback)
    n = int(lesson.name[:4]) if lesson.name[:4].isdigit() else 1
    acc = accent(fm.get("accent"), ACCENTS[ACCENT_ORDER[(n - 1) % len(ACCENT_ORDER)]])
    return {"accent": acc, "accent2": accent(fm.get("accent2"), acc),
            "board": "slate" if fm.get("board", "").strip().lower() == "slate" else "plain"}


def write_look(lesson, dest):
    """look.css: the lesson's board accent and surface, loaded after style.css, so the video looks like the board."""
    look = lesson_look(lesson)
    css = f":root{{--acc:{look['accent']};--acc2:{look['accent2']}}}\n"
    if look["board"] == "slate":
        slate = Path(__file__).resolve().parents[1] / "board" / "slate.jpg"
        shutil.copy2(slate, dest / "slate.jpg")
        css += ("#stage{background:linear-gradient(rgba(6,6,6,.42),rgba(6,6,6,.42)),url(slate.jpg) center/cover,#121212}\n"
                "#scenes{color:#ecebe3;text-shadow:0 0 1px rgba(236,235,227,.35)}\n")
    (dest / "look.css").write_text(css, encoding="utf-8")
    return look


def estimate(args):
    lesson = args.lesson.expanduser().resolve(strict=True)
    words = lesson_words(lesson.read_text(encoding="utf-8"))
    minutes = words * PACE_REF["minutes_per_1000_lesson_words"] / 1000
    spoken = words * PACE_REF["spoken_per_lesson_word"]
    print(json.dumps({"lessonWords": words, "minutes": round(minutes), "spokenWords": round(spoken),
                      "elevenLabsCharacters": round(spoken * PACE_REF["chars_per_spoken_word"]),
                      "reference": PACE_REF["lesson"]}, indent=2))


def pace_ok(lesson, project_dir):
    """Spoken words per lesson word against the 0010 reference; a short lesson (< 300 words) is not judged."""
    words = lesson_words(lesson.read_text(encoding="utf-8"))
    script = read(project_dir / "script.json")
    spoken = sum(len(str(c.get("say", "")).split()) for sc in script.get("scenes", []) for c in sc.get("cues", []))
    ratio, ref = (spoken / words if words else 0), PACE_REF["spoken_per_lesson_word"]
    if words >= 300 and ratio < ref * PACE_FLOOR:
        raise PipelineError(f"too fast: {spoken} spoken words for {words} lesson words ({ratio:.2f} per word); "
                            f"the 0010 reference is {ref} and the floor {ref * PACE_FLOOR:.2f}. Add steps, values and bridges")
    return f"ready ({ratio:.2f} spoken words per lesson word; reference {ref})"


def look(args):
    cfg, lesson, _ = project(args.project)
    print(json.dumps(write_look(lesson, args.project.expanduser().resolve())))


def number(value, where):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise PipelineError(f"{where}: expected finite number")
    return float(value)


def timing(project_dir):
    script = read(project_dir / "script.json")
    timeline = read(project_dir / "timeline.json")
    if not isinstance(script, dict) or not isinstance(timeline, dict):
        raise PipelineError("script and timeline must be objects")
    ss, ts = script.get("scenes"), timeline.get("scenes")
    if not isinstance(ss, list) or not ss or not isinstance(ts, list) or len(ts) != len(ss):
        raise PipelineError("script/timeline scene lists are missing or differ")
    total = number(timeline.get("total"), "timeline.total")
    prior = 0.0
    for n, (s, t) in enumerate(zip(ss, ts)):
        if not isinstance(s, dict) or not isinstance(t, dict) or s.get("id") != t.get("id") or not isinstance(s.get("id"), str):
            raise PipelineError(f"scene {n}: script/timeline ID mismatch")
        start, dur = number(t.get("start"), "scene start"), number(t.get("dur"), "scene duration")
        if abs(start - prior) > EPS or dur <= 0:
            raise PipelineError(f"scene {s['id']}: timeline has gap, overlap, or nonpositive duration")
        prior = start + dur
        scues, tcues = s.get("cues"), t.get("cues")
        if (not isinstance(scues, list) or not scues or not all(isinstance(c, dict) and isinstance(c.get("id"), str) for c in scues)
                or not isinstance(tcues, dict) or [c["id"] for c in scues] != list(tcues)):
            raise PipelineError(f"scene {s['id']}: script and measured cue IDs/order differ")
        cue_end = 0.0
        for cue in scues:
            cid = cue["id"]
            c = tcues[cid]
            if not isinstance(c, dict):
                raise PipelineError(f"scene {s['id']} cue {cid}: invalid timing")
            a, b = number(c.get("s"), "cue start"), number(c.get("e"), "cue end")
            if a < cue_end - EPS or b <= a or b > dur + EPS:
                raise PipelineError(f"scene {s['id']} cue {cid}: invalid measured interval")
            if ("pause" in cue) != (c.get("pause") is True):
                raise PipelineError(f"scene {s['id']} cue {cid}: pause flag differs")
            cue_end = b
    if abs(prior - total) > EPS:
        raise PipelineError("timeline total differs from final scene end")
    return script, timeline


def split_ok(project_dir, timeline):
    split = read(project_dir / "SPLIT.json")
    if not isinstance(split, dict) or not split or any(not isinstance(k, str) or not isinstance(v, list) for k, v in split.items()):
        raise PipelineError("SPLIT.json must map scene module names to scene ID arrays")
    if any(not re.fullmatch(r"[A-Za-z0-9_-]+", k) for k in split):
        raise PipelineError("SPLIT.json keys must be scene basenames without .js ([A-Za-z0-9_-]+)")
    flat = [sid for group in split.values() for sid in group]
    expected = [s["id"] for s in timeline["scenes"]]
    if flat != expected:
        raise PipelineError("SPLIT.json must cover every scene exactly once in timeline order")
    return split


def boundary(scene, cue, is_end):
    if not isinstance(cue, str):
        raise PipelineError(f"scene {scene['id']}: boundary cue must be a string")
    if cue == "start" and not is_end:
        return scene["start"]
    if cue == "end" and is_end:
        return scene["start"] + scene["dur"]
    c = scene["cues"].get(cue)
    if c is None:
        raise PipelineError(f"scene {scene['id']}: unknown boundary cue {cue}")
    return scene["start"] + c["s"]


def anchors_ok(project_dir, config, lesson, script, timeline):
    anchors = read(project_dir / "anchors.json")
    if not isinstance(anchors, dict) or set(anchors) != {"version", "lessonSha256", "segments"} or anchors["version"] != 1 or anchors["lessonSha256"] != config["lessonSha256"]:
        raise PipelineError("anchors.json: schema/source SHA mismatch; replan from the current lesson")
    segments = anchors["segments"]
    if not isinstance(segments, list) or not segments:
        raise PipelineError("anchors.json: segments must be a nonempty array")
    lines = lesson.read_text(encoding="utf-8").splitlines()
    scenes = {s["id"]: s for s in timeline["scenes"]}
    scripts = {s["id"]: s for s in script["scenes"]}
    result, seen = [], set()
    prev = 0.0
    for i, anchor in enumerate(segments):
        if not isinstance(anchor, dict) or set(anchor) != {"id", "label", "scene", "from", "to", "line", "step", "practice"}:
            raise PipelineError(f"anchor {i}: require id,label,scene,from,to,line,step,practice")
        sid, aid, label = anchor["scene"], anchor["id"], anchor["label"]
        if not isinstance(sid, str) or sid not in scenes or not isinstance(aid, str) or not aid.strip() or aid in seen or not isinstance(label, str) or not label.strip():
            raise PipelineError(f"anchor {i}: invalid scene, ID, or label")
        seen.add(aid)
        line, step = anchor["line"], anchor["step"]
        if isinstance(line, bool) or not isinstance(line, int) or line < 1 or line > len(lines) or not lines[line - 1].strip():
            raise PipelineError(f"anchor {aid}: line must refer to nonblank lesson source")
        if step is not None and (isinstance(step, bool) or not isinstance(step, int) or step < 1):
            raise PipelineError(f"anchor {aid}: step must be positive integer or null")
        if step is not None:
            if r"\begin{aligned}" not in lines[line - 1]:
                raise PipelineError(f"anchor {aid}: step requires line {line} to contain an aligned derivation; use null when row mapping is uncertain")
        scene = scenes[sid]
        start, end = boundary(scene, anchor["from"], False), boundary(scene, anchor["to"], True)
        if abs(start - prev) > EPS or end <= start:
            raise PipelineError(f"anchor {aid}: segments must exactly cover the measured video in order (expected start {prev:.3f}, got {start:.3f})")
        prev = end
        practice = None
        if anchor["practice"] is not None:
            p = anchor["practice"]
            if not isinstance(p, dict) or set(p) != {"pause", "reveal"}:
                raise PipelineError(f"anchor {aid}: practice requires pause and reveal cue IDs")
            if not isinstance(p["pause"], str) or not isinstance(p["reveal"], str):
                raise PipelineError(f"anchor {aid}: practice cue IDs must be strings")
            pc, rc = scene["cues"].get(p["pause"]), scene["cues"].get(p["reveal"])
            cue_ids = [c["id"] for c in scripts[sid]["cues"]]
            if not pc or pc.get("pause") is not True or not rc or rc.get("pause") is True or cue_ids.index(p["reveal"]) != cue_ids.index(p["pause"]) + 1:
                raise PipelineError(f"anchor {aid}: reveal must be the first spoken cue after its measured pause")
            pause, reveal = scene["start"] + pc["s"], scene["start"] + rc["s"]
            if not start < pause < scene["start"] + pc["e"] <= reveal < end:
                raise PipelineError(f"anchor {aid}: question, complete think pause, and answer must fit one segment")
            pauses = [cid for cid, cue in scene["cues"].items()
                      if cue.get("pause") is True and start - EPS <= scene["start"] + cue["s"] < end - EPS]
            if pauses != [p["pause"]]:
                raise PipelineError(f"anchor {aid}: each question needs a distinct segment and practice gate")
            practice = {"pauseAt": round(pause, 3), "revealAt": round(reveal, 3)}
        else:
            for cid, c in scene["cues"].items():
                if c.get("pause") is True and start - EPS <= scene["start"] + c["s"] < end - EPS:
                    raise PipelineError(f"anchor {aid}: measured think cue {cid} needs its own question/answer practice gate")
        # each segment starts exactly where the previous one ended: rounding the two boundaries separately
        # can leave a start 1 ms before the previous end (they differ within EPS), which the board rejects as overlap
        start_r = result[-1]["end"] if result else round(start, 3)
        result.append({"id": aid, "label": label, "start": start_r, "end": max(round(end, 3), start_r + 0.001), "line": line, "step": step, "practice": practice})
    if abs(prev - timeline["total"]) > EPS:
        raise PipelineError(f"anchors end at {prev:.3f}; timeline ends at {timeline['total']:.3f}")
    return result


def practice_items(lines):
    """Spans (first, last) of 1-based lesson lines, one per practice item: each top-level bullet of a
    `::: checkin` block and each whole `::: mcq` block. Fenced code is skipped."""
    items, block, fence = [], None, False
    for n, raw in enumerate(lines, 1):
        line = raw.rstrip()
        if line.lstrip().startswith("```"):
            fence = not fence
        if fence:
            continue
        if block is None:
            if line.startswith("::: checkin"):
                block = "checkin"
            elif line.startswith("::: mcq"):
                block = "mcq"
                items.append([n, n])
            continue
        if line == ":::":
            if block == "mcq":
                items[-1][1] = n
            block = None
        elif block == "checkin" and line.startswith("- "):
            items.append([n, n])
        elif block == "checkin" and items and (not line or raw.startswith("  ")):
            items[-1][1] = n
    return [tuple(i) for i in items]


def practice_ok(lesson, segments):
    """Every lesson practice item needs a video segment with a pause and reveal anchored inside it."""
    lines = lesson.read_text(encoding="utf-8").splitlines()
    gated = [s["line"] for s in segments if s.get("practice")]
    items = practice_items(lines)
    missing = [a for a, b in items if not any(a <= g <= b for g in gated)]
    if missing:
        shown = "; ".join(f"line {a}: {lines[a - 1].strip()[:60]}" for a in missing[:8])
        more = f" (+{len(missing) - 8} more)" if len(missing) > 8 else ""
        raise PipelineError(f"{len(missing)} of {len(items)} lesson practice items have no pause-and-solve video segment: {shown}{more}")
    return len(items)


def map_data(project_dir, captions_burned_in=False):
    config, lesson, lid = project(project_dir)
    script, timeline = timing(project_dir)
    split_ok(project_dir, timeline)
    segments = anchors_ok(project_dir, config, lesson, script, timeline)
    return {"version": 1, "lessonId": lid, "lessonSha256": config["lessonSha256"], "video": f"{lid}-lecture.mp4", "duration": timeline["total"], "captionsBurnedIn": captions_burned_in, "segments": segments}


def caption_track(project_dir, lesson_id):
    """The caption track the board overlays: each cue's `show` (lesson notation) timed by its spoken chunks."""
    return captions.track(read(project_dir / "script.json"), read(project_dir / "timeline.json"), lesson_id)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_map(args):
    data = map_data(args.project, args.captions_burned_in)
    target = args.project / f"video-{data['lessonId']}.json"
    if target.exists() and read(target) != data and not args.replace:
        raise PipelineError(f"{target}: stale or different map; review changes, then rerun with --replace")
    write_json(target, data)
    track = caption_track(args.project, data["lessonId"])
    write_json(args.project / "captions.json", track)   # display only: always rebuilt from the script's show texts
    print(f"built {target}: {len(data['segments'])} source-linked segments, {data['duration']:.3f}s; "
          f"captions.json: {len(track['cues'])} captions")


def captions_ok(project_dir, lesson_id):
    """Every spoken cue has a show text in notation (no math spelled in words), and captions.json is current."""
    missing, findings = captions.lint_script(read(project_dir / "script.json"))
    if missing:
        more = f" (+{len(missing) - 6} more)" if len(missing) > 6 else ""
        raise PipelineError(f"{len(missing)} spoken cue(s) have no show caption: {', '.join(missing[:6])}{more}")
    if findings:
        shown = "; ".join(f"{w}: {h!r} ({r})" for w, r, h in findings[:6])
        more = f" (+{len(findings) - 6} more)" if len(findings) > 6 else ""
        raise PipelineError(f"{len(findings)} show caption(s) spell math in words instead of the lesson's notation: {shown}{more}")
    path = project_dir / "captions.json"
    if not path.is_file() or read(path) != caption_track(project_dir, lesson_id):
        raise PipelineError("captions.json is missing or stale; rerun build-map")
    return f"ready ({len(read(path)['cues'])} captions in lesson notation)"


def practice_warnings(project_dir, timeline, anchors):
    """A Your turn segment shows the problem and waits: it should not read or explain the question before its pause
    (at most one short line such as "Your turn: pause and solve it.")."""
    script = {s["id"]: s for s in read(project_dir / "script.json")["scenes"]}
    scenes = {s["id"]: s for s in timeline["scenes"]}
    out = []
    for a in anchors.get("segments", []):
        p = a.get("practice")
        if not p:
            continue
        sc, cues = scenes[a["scene"]], script[a["scene"]]["cues"]
        start = boundary(sc, a["from"], False) - sc["start"]
        pause = sc["cues"][p["pause"]]["s"]
        said = [c for c in cues if "say" in c and start - EPS <= sc["cues"][c["id"]]["s"] < pause - EPS]
        words = sum(len(c["say"].split()) for c in said)
        if len(said) > 1 or words > 12:
            out.append(f"practice {a['id']}: {len(said)} spoken cue(s), {words} words before its pause; a Your turn shows "
                       "the problem and waits (at most one short line)")
    return out


def receipts_ok(project_dir, split, video_role):
    data = read(project_dir / "video-runs.json")
    if not isinstance(data, dict) or set(data) != {"version", "author", "builders", "reviewer"} or data["version"] != 1:
        raise PipelineError("video-runs.json: require version, author, builders, reviewer")
    def run(record, name, outcome, opus):
        if not isinstance(record, dict) or set(record) != {"requested", "resolved", "outcome", "runtimeEvidence"}:
            raise PipelineError(f"video-runs.json {name}: incomplete runtime receipt")
        identity = record["resolved"]
        if (not isinstance(identity, dict) or set(identity) != {"model", "effort"} or
                any(not isinstance(identity[k], str) or not identity[k].strip() for k in ("model", "effort"))):
            raise PipelineError(f"video-runs.json {name}: malformed runtime model/effort")
        if opus and (record["requested"] != video_role or record["resolved"] != video_role):
            raise PipelineError(f"video-runs.json {name}: required Opus 5.5 video runtime identity mismatch")
        if record["requested"] != record["resolved"] or record["outcome"] != outcome:
            raise PipelineError(f"video-runs.json {name}: request/runtime mismatch or incomplete run")
        evidence = record["runtimeEvidence"]
        if not isinstance(evidence, str) or not evidence.strip():
            raise PipelineError(f"video-runs.json {name}: missing actual host runtime evidence reference")
    run(data["author"], "author", "complete", True)
    builders = data["builders"]
    used = [name for name, scenes in split.items() if scenes]
    if not isinstance(builders, dict) or set(builders) != set(used):
        raise PipelineError("video-runs.json builders: one receipt required per used SPLIT module")
    for name, record in builders.items():
        run(record, name, "complete", True)
    run(data["reviewer"], "reviewer", "passed", False)


def media_ok(project_dir, duration):
    mp4, srt = project_dir / "final.mp4", project_dir / "final.srt"
    if not mp4.is_file() or not srt.is_file() or not srt.read_text(encoding="utf-8").strip():
        raise PipelineError("final.mp4 and nonempty final.srt are required")
    rendered = project_dir / "RENDERED"
    if not rendered.is_file() or rendered.read_text(encoding="utf-8").strip() != "DONE":
        raise PipelineError("RENDERED success marker is required; run render.sh to completion")
    # script.json counts by its spoken content: a caption (`show`) edit after the render changes captions.json only.
    # tts.done fingerprints the spoken script; a project without one falls back to the file's time.
    done = project_dir / "tts.done"
    spoken = None
    if done.is_file():
        try:
            spoken = read(done).get("script.json:spoken")
        except (PipelineError, AttributeError):
            spoken = None
    if spoken:
        import importlib.util
        spec = importlib.util.spec_from_file_location("blackboard_tts", Path(__file__).resolve().parents[1] / "video" / "tts.py")
        tts = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tts)   # stdlib only; spoken_sha256 is the fingerprint tts.py writes
        if tts.spoken_sha256(str(project_dir / "script.json")) != spoken:
            raise PipelineError("script.json's narration changed after tts.py ran; rerun tts.py, then render")
    required = ("timeline.json", "timeline.js", "SPLIT.json", "narration.wav",
                "engine.js", "style.css", "index.html", "capture.mjs", "finish.sh", "render.sh",
                "tts.py", "package.json")
    inputs = [project_dir / name for name in required]
    if not spoken:
        inputs.append(project_dir / "script.json")
    lockfile = project_dir / "package-lock.json"
    if lockfile.is_file():
        inputs.append(lockfile)
    inputs.extend(path for directory in ("scenes", "audio", "assets")
                  for path in (project_dir / directory).rglob("*") if path.is_file())
    missing = [str(path.relative_to(project_dir)) for path in inputs if not path.is_file()]
    if missing:
        raise PipelineError("render input missing: " + ", ".join(missing))
    latest = max(inputs, key=lambda path: path.stat().st_mtime_ns)
    if mp4.stat().st_mtime_ns < latest.stat().st_mtime_ns:
        raise PipelineError(f"final.mp4 is stale after {latest.relative_to(project_dir)}; rerender")
    if srt.stat().st_mtime_ns < (project_dir / "timeline.json").stat().st_mtime_ns:
        raise PipelineError("final.srt is stale after timeline.json; rerender")
    if rendered.stat().st_mtime_ns < max(mp4.stat().st_mtime_ns, srt.stat().st_mtime_ns):
        raise PipelineError("RENDERED marker predates final media; rerender")
    if not shutil.which("ffprobe"):
        raise PipelineError("ffprobe is required to verify final.mp4")
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                 "format=duration:stream=codec_type", "-of", "json", str(mp4)],
                                capture_output=True, text=True, timeout=30, check=True)
        probe = json.loads(result.stdout)
        actual = number(float(probe["format"]["duration"]), "MP4 duration")
        streams = {stream["codec_type"] for stream in probe["streams"]}
        if not {"video", "audio"} <= streams or abs(actual - duration) > 0.5:
            raise PipelineError(f"MP4 needs audio/video and duration within 0.5s of timeline ({actual:.3f}s versus {duration:.3f}s)")
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise PipelineError(f"ffprobe could not verify final.mp4: {exc}") from exc


def check(args):
    stages = {name: "blocked by an earlier stage" for name in
              ("source", "timing", "split", "anchors", "practice", "pace", "map", "captions", "scenes", "receipts", "media")}
    warnings = []
    cfg = lesson = timeline = split = data = None
    try:
        cfg, lesson, lid = project(args.project)
        stages["source"] = "ready"
    except (PipelineError, OSError) as exc:
        stages["source"] = str(exc)
    if cfg:
        try:
            _, timeline = timing(args.project)
            stages["timing"] = "ready"
        except PipelineError as exc:
            stages["timing"] = str(exc)
    if timeline:
        try:
            split = split_ok(args.project, timeline)
            stages["split"] = "ready"
        except PipelineError as exc:
            stages["split"] = str(exc)
    if split:
        try:
            data = map_data(args.project)
            stages["anchors"] = "ready"
        except PipelineError as exc:
            stages["anchors"] = str(exc)
    if data:
        try:
            count = practice_ok(lesson, data["segments"])
            stages["practice"] = f"ready ({count} lesson practice items each have a pause-and-solve segment)"
        except PipelineError as exc:
            stages["practice"] = str(exc)
        try:
            stages["pace"] = pace_ok(lesson, args.project)
        except (PipelineError, OSError, AttributeError) as exc:
            stages["pace"] = str(exc)
    if data:
        target = args.project / f"video-{lid}.json"
        try:
            installed = read(target)
            if not isinstance(installed, dict) or not isinstance(installed.get("captionsBurnedIn"), bool) or installed != dict(data, captionsBurnedIn=installed["captionsBurnedIn"]):
                raise PipelineError("map is stale; rerun build-map after reviewing anchors")
            stages["map"] = "ready"
        except PipelineError as exc:
            stages["map"] = str(exc)
        try:
            stages["captions"] = captions_ok(args.project, lid)
        except (PipelineError, OSError, KeyError, TypeError) as exc:
            stages["captions"] = str(exc)
        try:
            warnings = practice_warnings(args.project, timeline, read(args.project / "anchors.json"))
        except (PipelineError, KeyError, TypeError):
            pass
    if split:
        try:
            for name, scenes in split.items():
                filename = name + ".js"
                if scenes and not (args.project / "scenes" / filename).is_file():
                    raise PipelineError(f"missing scene module: scenes/{filename}")
            stages["scenes"] = "ready"
        except PipelineError as exc:
            stages["scenes"] = str(exc)
        try:
            receipts_ok(args.project, split, cfg["videoRole"])
            stages["receipts"] = "ready; orchestrator must verify evidence against host metadata"
        except PipelineError as exc:
            stages["receipts"] = str(exc)
    if data:
        try:
            media_ok(args.project, data["duration"])
            stages["media"] = "ready"
        except (PipelineError, UnicodeError) as exc:
            stages["media"] = str(exc)
    ready = all(value.startswith("ready") for value in stages.values())
    print(json.dumps({"ready": ready, "stages": stages, "warnings": warnings}, indent=2))
    return 0 if ready else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init", help="copy portable runtime into an external project, without overwriting work")
    p.add_argument("--lesson", type=Path, required=True)
    p.add_argument("--project", type=Path, required=True)
    p.add_argument("--runtime", type=Path, default=Path(__file__).resolve().parents[1] / "video")
    p.add_argument("--video-effort", default="high", help="explicit Opus effort; high recommended")
    p = sub.add_parser("build-map", help="derive a board manifest from source anchors and measured timing")
    p.add_argument("--project", type=Path, required=True)
    p.add_argument("--replace", action="store_true", help="replace a reviewed stale map")
    p.add_argument("--captions-burned-in", action="store_true", help="set only after visually confirming rendered captions")
    p = sub.add_parser("check", help="report each stage of project readiness")
    p.add_argument("--project", type=Path, required=True)
    p = sub.add_parser("estimate", help="expected video length and narration characters at the 0010 pace")
    p.add_argument("--lesson", type=Path, required=True)
    p = sub.add_parser("look", help="rewrite look.css from the lesson's board accent and surface")
    p.add_argument("--project", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            init(args)
        elif args.command == "build-map":
            build_map(args)
        elif args.command == "estimate":
            estimate(args)
        elif args.command == "look":
            look(args)
        else:
            return check(args)
    except (PipelineError, OSError, UnicodeError) as exc:
        print(f"video pipeline: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
