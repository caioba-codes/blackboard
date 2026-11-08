#!/usr/bin/env python3
"""Live progress of a lesson video that is still being made, read from the video project's own files.

  register --project P                 point the project's lesson at P: writes $WS/reference/video-project-NNNN.json
  show --workspace WS --lesson NNNN    print the computed status JSON (what the board's progress card shows)

`video_pipeline.py init` registers on its own. Nothing in the pipeline writes progress: every request recomputes it
from the artifacts the runtime already leaves, so it cannot go stale or be forgotten.

Stages, in order, each done when its artifact exists:
  script     script.json and anchors.json
  narration  one audio file per spoken cue; Kokoro writes audio/.tmp-<scene>_<cue>.wav as it goes and renames the whole
             batch only at the end, so those count too. tts.done + timeline.json mean finished.
  scenes     scenes/<module>.js for every nonempty SPLIT.json module
  render     chunks/cNNNN.mp4 over the chunks in chunks/plan.json; RENDERED means finished
  review     video-runs.json with a passed reviewer
  import     the board has the installed video; the card is then gone
The time left is measured from the mtimes of the current stage's last files, never guessed.
"""

import argparse
import json
import math
import os
from pathlib import Path
import re
import sys
import time

POINTER = "video-project-{}.json"
# Share of the whole job per stage, in percent; narration and render are the long, machine-bound ones.
WEIGHTS = {"script": 10, "narration": 30, "scenes": 15, "render": 35, "review": 5, "import": 5}
LABELS = {"script": "Script", "narration": "Narration", "scenes": "Scenes", "render": "Render", "review": "Review", "import": "Import"}
RATE_WINDOW = 200     # the last N finished items set the pace
STALL_MIN = 600       # seconds without a new item before the stage reads as stalled (at least 10x the pace)
CHUNK = re.compile(r"c\d{4}\.mp4")


def read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, UnicodeError, ValueError):
        return None


def pointer_path(workspace, lid):
    return Path(workspace) / "reference" / POINTER.format(lid)


def register(project_dir):
    project_dir = Path(project_dir).expanduser().resolve()
    config = read_json(project_dir / "project.json")
    if not isinstance(config, dict) or not isinstance(config.get("lesson"), str):
        raise ValueError(f"{project_dir}/project.json has no lesson path")
    lesson = Path(config["lesson"])
    lid = lesson.name[:4]
    if not re.fullmatch(r"\d{4}", lid) or lesson.parent.name != "lessons":
        raise ValueError(f"{lesson} is not a lessons/NNNN-*.md file")
    target = pointer_path(lesson.parent.parent, lid)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps({"version": 1, "project": str(project_dir), "registered": int(time.time())}) + "\n", encoding="utf-8")
    os.replace(tmp, target)
    return target


def pace(mtimes, remaining, now):
    """(seconds left, stalled) from the spacing of the newest finished items; None when there is too little to measure."""
    ts = sorted(mtimes)[-RATE_WINDOW:]
    if remaining <= 0 or len(ts) < 3 or ts[-1] <= ts[0]:
        return None, False
    per = (ts[-1] - ts[0]) / (len(ts) - 1)
    idle = max(0.0, now - ts[-1])
    if idle > max(STALL_MIN, 10 * per):
        return None, True
    return max(0.0, remaining * per - idle), False


def spoken_cues(script):
    if not isinstance(script, dict) or not isinstance(script.get("scenes"), list):
        return None
    return [f"{sc.get('id')}_{c.get('id')}" for sc in script["scenes"] if isinstance(sc, dict)
            for c in sc.get("cues") or [] if isinstance(c, dict) and "say" in c]


def files(directory):
    """name -> mtime for one directory, {} when it does not exist."""
    try:
        with os.scandir(directory) as it:
            return {e.name: e.stat().st_mtime for e in it if e.is_file()}
    except OSError:
        return {}


def stage_script(p):
    have = [n for n in ("script.json", "anchors.json") if (p / n).is_file()]
    return {"done": len(have), "total": 2, "unit": "files", "finished": len(have) == 2}


def stage_narration(p, script):
    cues = spoken_cues(script)
    finished = (p / "tts.done").is_file() and (p / "timeline.json").is_file()
    if cues is None:
        return {"done": 0, "total": None, "unit": "lines", "finished": finished}
    audio = files(p / "audio")
    # Kokoro (.wav, or its .tmp- file while the batch runs) or ElevenLabs (.mp3): count whichever engine has more
    wav = [audio.get(f"{c}.wav") or audio.get(f".tmp-{c}.wav") for c in cues]
    mp3 = [audio.get(f"{c}.mp3") for c in cues]
    got = max((wav, mp3), key=lambda xs: sum(1 for x in xs if x))
    times = [t for t in got if t]
    return {"done": len(cues) if finished else len(times), "total": len(cues), "unit": "lines", "finished": finished,
            "mtimes": times}


def stage_scenes(p):
    split = read_json(p / "SPLIT.json")
    if not isinstance(split, dict):
        return {"done": 0, "total": None, "unit": "modules", "finished": False}
    mods = [k for k, v in split.items() if isinstance(k, str) and isinstance(v, list) and v]
    have = files(p / "scenes")
    times = [have[f"{m}.js"] for m in mods if f"{m}.js" in have]
    return {"done": len(times), "total": len(mods), "unit": "modules", "finished": bool(mods) and len(times) == len(mods),
            "mtimes": times}


def stage_render(p):
    finished = (p / "RENDERED").is_file()
    plan = read_json(p / "chunks" / "plan.json")
    total = None
    if isinstance(plan, dict) and isinstance(plan.get("total"), int) and isinstance(plan.get("chunkFrames"), int) and plan["chunkFrames"] > 0:
        total = math.ceil(plan["total"] / plan["chunkFrames"])
    else:
        tl = read_json(p / "timeline.json")   # before the first chunk: capture.mjs's default 60-second chunks
        if isinstance(tl, dict) and isinstance(tl.get("total"), (int, float)) and tl["total"] > 0:
            total = math.ceil(tl["total"] / 60)
    chunks = files(p / "chunks")
    times = [t for n, t in chunks.items() if CHUNK.fullmatch(n)]
    done = (total or len(times)) if finished else len(times)
    out = {"done": done, "total": total, "unit": "chunks", "finished": finished, "mtimes": times}
    if not finished and total and len(times) >= total:
        out["note"] = "joining and muxing"
    return out


def stage_review(p):
    runs = read_json(p / "video-runs.json")
    passed = isinstance(runs, dict) and isinstance(runs.get("reviewer"), dict) and runs["reviewer"].get("outcome") == "passed"
    return {"done": int(passed), "total": 1, "unit": None, "finished": passed}


def installed_files(workspace, lid):
    ws = Path(workspace)
    return (ws / "lessons" / "assets" / f"{lid}-lecture.mp4").is_file() and (ws / "reference" / f"video-{lid}.json").is_file()


def status(workspace, lid, installed=None, now=None):
    """The progress card's data. `installed` is the board's own verdict on the installed video (bridge.lesson_video);
    without it, the imported files' presence decides."""
    now = time.time() if now is None else now
    if not re.fullmatch(r"\d{4}", str(lid)):
        return {"active": False, "error": "lesson must be NNNN"}
    if installed is None:
        installed = installed_files(workspace, lid)
    if installed:
        return {"active": False, "installed": True, "lesson": lid}
    ptr = read_json(pointer_path(workspace, lid))
    if not isinstance(ptr, dict) or not isinstance(ptr.get("project"), str):
        return {"active": False, "installed": False, "lesson": lid}
    p = Path(ptr["project"])
    if not p.is_absolute() or not (p / "project.json").is_file():
        return {"active": False, "installed": False, "lesson": lid, "error": "the registered video project is gone"}
    script = read_json(p / "script.json")
    found = {"script": stage_script(p), "narration": stage_narration(p, script), "scenes": stage_scenes(p),
             "render": stage_render(p), "review": stage_review(p),
             "import": {"done": 0, "total": 1, "unit": None, "finished": False}}
    current = next(k for k in WEIGHTS if not found[k]["finished"])
    stages, overall = [], 0.0
    for k, s in found.items():
        frac = 1.0 if s["finished"] else (min(1.0, s["done"] / s["total"]) if s["total"] else 0.0)
        overall += WEIGHTS[k] * frac
        stages.append({"key": k, "label": LABELS[k], "state": "done" if s["finished"] else ("current" if k == current else "todo"),
                       "done": s["done"], "total": s["total"], "unit": s["unit"], "percent": round(100 * frac, 1),
                       **({"note": s["note"]} if s.get("note") else {})})
    cur = found[current]
    eta, stalled = pace(cur.get("mtimes") or [], (cur["total"] or 0) - cur["done"], now)
    last = max(cur.get("mtimes") or [0]) or None
    return {"active": True, "installed": False, "lesson": lid, "project": str(p), "stage": current,
            "stageIndex": list(WEIGHTS).index(current) + 1, "stageCount": len(WEIGHTS),
            "percent": round(overall, 1), "eta": None if eta is None else round(eta), "stalled": stalled,
            "lastProgress": None if last is None else round(last), "now": round(now), "weights": WEIGHTS, "stages": stages}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("register", help="point the board at a video project (video_pipeline.py init does this)")
    p.add_argument("--project", type=Path, required=True)
    p = sub.add_parser("show", help="print the live status JSON for one lesson")
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--lesson", required=True)
    a = ap.parse_args(argv)
    if a.command == "register":
        try:
            print(f"registered {register(a.project)}")
        except ValueError as exc:
            print(f"video status: {exc}", file=sys.stderr)
            return 1
    else:
        print(json.dumps(status(a.workspace.expanduser().resolve(), a.lesson), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
