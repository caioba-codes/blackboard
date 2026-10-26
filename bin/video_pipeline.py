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


ROLE = {"model": "claude-opus-5-5", "effort": "high"}
RUNTIME = ("engine.js", "style.css", "capture.mjs", "finish.sh", "tts.py", "index.html", "package.json", "render.sh")
OPTIONAL_RUNTIME = ("README.md", "package-lock.json", ".gitignore")
VIDEO_EFFORTS = frozenset(("low", "medium", "high"))
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
    print(f"initialized {dest}; lesson SHA-256 {config['lessonSha256']}; video author {ROLE['model']} {args.video_effort}")
    print("next: author script.json and anchors.json from the lesson; no model receipt was generated")


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


def map_data(project_dir, captions_burned_in=False):
    config, lesson, lid = project(project_dir)
    script, timeline = timing(project_dir)
    split_ok(project_dir, timeline)
    segments = anchors_ok(project_dir, config, lesson, script, timeline)
    return {"version": 1, "lessonId": lid, "lessonSha256": config["lessonSha256"], "video": f"{lid}-lecture.mp4", "duration": timeline["total"], "captionsBurnedIn": captions_burned_in, "segments": segments}


def build_map(args):
    data = map_data(args.project, args.captions_burned_in)
    target = args.project / f"video-{data['lessonId']}.json"
    if target.exists() and read(target) != data and not args.replace:
        raise PipelineError(f"{target}: stale or different map; review changes, then rerun with --replace")
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"built {target}: {len(data['segments'])} source-linked segments, {data['duration']:.3f}s")


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
    required = ("script.json", "timeline.json", "timeline.js", "SPLIT.json", "narration.wav",
                "engine.js", "style.css", "index.html", "capture.mjs", "finish.sh", "render.sh",
                "tts.py", "package.json")
    inputs = [project_dir / name for name in required]
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
              ("source", "timing", "split", "anchors", "map", "scenes", "receipts", "media")}
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
        target = args.project / f"video-{lid}.json"
        try:
            installed = read(target)
            if not isinstance(installed, dict) or not isinstance(installed.get("captionsBurnedIn"), bool) or installed != dict(data, captionsBurnedIn=installed["captionsBurnedIn"]):
                raise PipelineError("map is stale; rerun build-map after reviewing anchors")
            stages["map"] = "ready"
        except PipelineError as exc:
            stages["map"] = str(exc)
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
    print(json.dumps({"ready": ready, "stages": stages}, indent=2))
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
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            init(args)
        elif args.command == "build-map":
            build_map(args)
        else:
            return check(args)
    except (PipelineError, OSError, UnicodeError) as exc:
        print(f"video pipeline: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
