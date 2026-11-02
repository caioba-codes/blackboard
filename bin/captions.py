#!/usr/bin/env python3
"""Lesson video captions in the lesson's notation.

Each spoken cue in script.json has two texts: `say` (what the narrator speaks: "I five is zero") and `show` (what
the caption shows, in the lesson's notation with $KaTeX$ math: "$I_5 = 0$"). The timeline's subtitle chunks are timed
from the `say` audio; this module maps each cue's `show` onto those chunks sentence by sentence and writes the caption
track the board player overlays on the video (captions.json in the project, installed as
lessons/assets/NNNN-lecture.captions.json beside the MP4).

  python3 captions.py lint --project P     show texts that spell math out in words (exit 1 when any)
  python3 captions.py lint --track FILE    the same for an installed caption track
"""

import argparse
import json
from pathlib import Path
import re
import sys

NUMS = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
        "seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred").split()
NUM = r"(?:" + "|".join(NUMS) + r")"
SENTENCE = re.compile(r"[^.?!:]+[.?!:]?")
MATH = re.compile(r"\$\$.+?\$\$|\$[^$]+\$", re.S)
LONG = 95   # tts.py splits a sentence longer than this at its commas


# ---------- the spelled-math lint ----------
# Each rule: (name, pattern). Run on show text with its $math$ removed, so notation inside math never trips it.
RULES = (
    # "That's six" and "A four bit adder" are English: no letter after an apostrophe, no article before a counted noun
    ("letter and number word", re.compile(r"(?<!['\u2019])\b(?!a\b)(?!A\s+" + NUM + r"[\s-]+(?:bit|input|output|segment|word|digit|way|level|row|line)s?\b)"
                                          r"[A-Za-z]\s+(?:sub\s+)?" + NUM + r"\b(?!-)")),
    ("'sub' subscript", re.compile(r"\b\w+\s+sub\s+\w+")),
    ("letter with in/out subscript", re.compile(r"\b[A-Z]\s+(?:in|out)\b(?![-'])(?!\s+(?:series|parallel|the|a|an|order)\b)")),
    ("power in words", re.compile(r"\b(?:" + NUM + r"|[a-z])\s+to\s+the\s+(?:power\s+of\s+)?(?:" + NUM + r"|[a-z]|n|minus)\b", re.I)),
    ("squared/cubed", re.compile(r"\b(?:[A-Za-z]|" + NUM + r")\s+(?:squared|cubed)\b", re.I)),
    ("bar/prime/not on a variable", re.compile(r"(?<!['\u2019])\b(?![aA]\s+bar\b)[A-Za-z]\s+(?:bar|prime)\b|\bnot\s+[A-Z]\b(?!-)")),
    ("sigma m", re.compile(r"\bsigma\s+m\b", re.I)),
    ("operator between symbols", re.compile(r"\b(?:[A-Za-z]|\d+|" + NUM + r")\s+(?:equals|plus|minus|times|xor|x-?or)\s+(?:[A-Za-z]|\d+|" + NUM + r")\b(?!-)")),
    ("fraction in words", re.compile(r"\b" + NUM + r"\s+over\s+" + NUM + r"\b", re.I)),
    ("decimal in words", re.compile(r"\b" + NUM + r"\s+point\s+" + NUM + r"\b", re.I)),
)


def strip_math(text):
    return MATH.sub(" ", text)


def spelled_math(text):
    """[(rule, match)] for each place `text` spells math out in words instead of notation."""
    plain, found, seen = strip_math(text), [], set()
    for name, rx in RULES:
        for m in rx.finditer(plain):
            if m.span() in seen:
                continue
            seen.add(m.span())
            found.append((name, m.group(0)))
    # one hit per place: the overlapping generic rule repeats a specific one
    out, spans = [], []
    for name, hit in found:
        if any(hit in s or s in hit for s in spans):
            continue
        spans.append(hit)
        out.append((name, hit))
    return out


# ---------- sentence chunks shared with tts.py ----------
def _mask(text):
    """Same-length copy of a show text in which math and decimal points cannot end a sentence or split at a comma."""
    out = list(text)
    for m in MATH.finditer(text):
        for i in range(m.start(), m.end()):
            out[i] = "x"
    for m in re.finditer(r"(?<=\d)[.:,](?=\d)", text):
        out[m.start()] = "x"
    return "".join(out)


def _split(text, masked, a, b, cut):
    """Inclusive (start, end) spans of text[a:b] split after each ', ' when `cut`, leading space dropped."""
    bounds, prev = [], a
    if cut:
        for i in range(a + 1, b):
            if masked[i - 1] == "," and masked[i].isspace():
                bounds.append((prev, i))
                prev = i + 1
    bounds.append((prev, b))
    out = []
    for x, y in bounds:
        while x < y and text[x].isspace():
            x += 1
        if x <= y - 1:
            out.append((x, y - 1))
    return out


def sentences(text, masked=None, cut_long=True):
    """Sentences of `text`, each a list of inclusive (start, end) chunk spans. With the defaults this is exactly
    tts.py's pieces() grouped by sentence: a sentence longer than 95 characters is split after its commas."""
    masked = masked if masked is not None else text
    out = []
    for m in SENTENCE.finditer(masked):
        if not m.group(0).strip():
            continue
        parts = _split(text, masked, m.start(), m.end(), cut_long and len(m.group(0)) > LONG)
        if parts:
            out.append(parts)
    return out


def align(say, show, subs):
    """Caption chunks [{"s", "e", "text"}] for one cue: `subs` are that cue's timed say chunks (tts.py order).
    Show sentences take the times of the matching say sentences; a long say sentence split at commas keeps the split
    when the show sentence has as many comma parts, else shows whole for the sentence's time. When the sentence counts
    differ (or the subs do not match the say text) the whole show text spans the whole cue."""
    if not subs:
        return []
    whole = [{"s": subs[0]["s"], "e": subs[-1]["e"], "text": " ".join(show.split())}]
    said = sentences(say)
    if sum(len(p) for p in said) != len(subs):
        return whole
    masked = _mask(show)
    shown = sentences(show, masked, cut_long=False)
    if len(shown) != len(said):
        return whole
    out, k = [], 0
    for say_parts, (show_span,) in zip(said, shown):
        times = subs[k:k + len(say_parts)]
        k += len(say_parts)
        a, b = show_span
        if len(say_parts) > 1:
            parts = _split(show, masked, a, b + 1, True)
            if len(parts) == len(say_parts):
                out += [{"s": t["s"], "e": t["e"], "text": show[x:y + 1].strip()} for t, (x, y) in zip(times, parts)]
                continue
        out.append({"s": times[0]["s"], "e": times[-1]["e"], "text": show[a:b + 1].strip()})
    return out


# ---------- the caption track ----------
def cue_subs(scene, cue_id):
    """The timeline subtitle chunks (scene-local) that fall inside one measured cue."""
    c = scene["cues"][cue_id]
    return [x for x in scene.get("subs") or [] if c["s"] - 0.02 <= x["s"] <= c["e"] + 0.02]


def track(script, timeline, lesson_id, shows=None):
    """The caption track: absolute-time chunks in lesson notation. `shows` ({"scene.cue": text}) overrides script
    show texts (used for a video narrated before cues had one); a cue with neither falls back to its say chunks."""
    shows = shows or {}
    scripts = {s["id"]: s for s in script["scenes"]}
    cues = []
    for sc in timeline["scenes"]:
        for cue in scripts[sc["id"]]["cues"]:
            if "say" not in cue:
                continue
            subs = cue_subs(sc, cue["id"])
            show = shows.get(f"{sc['id']}.{cue['id']}", cue.get("show"))
            chunks = align(cue["say"], show, subs) if show else [dict(s=x["s"], e=x["e"], text=x["text"]) for x in subs]
            for x in chunks:
                cues.append({"s": round(sc["start"] + x["s"], 3), "e": round(sc["start"] + x["e"], 3), "text": x["text"]})
    cues.sort(key=lambda x: x["s"])
    return {"version": 1, "lessonId": lesson_id, "video": f"{lesson_id}-lecture.mp4",
            "duration": timeline["total"], "cues": cues}


def valid_track(data, lesson_id, duration=None):
    """Raise ValueError unless `data` is a caption track for this lesson (and, when given, this video duration).
    Optional progressBarBurnedIn: true marks a video rendered with the old in-frame progress strip, which the player
    then hides."""
    if (not isinstance(data, dict) or set(data) - {"progressBarBurnedIn"} != {"version", "lessonId", "video", "duration", "cues"}
            or data["version"] != 1):
        raise ValueError("caption track needs version 1, lessonId, video, duration, cues")
    if not isinstance(data.get("progressBarBurnedIn", False), bool):
        raise ValueError("progressBarBurnedIn must be true or false")
    if data["lessonId"] != lesson_id or data["video"] != f"{lesson_id}-lecture.mp4":
        raise ValueError(f"caption track is not for lesson {lesson_id}")
    d = data["duration"]
    if isinstance(d, bool) or not isinstance(d, (int, float)) or d <= 0:
        raise ValueError("caption track duration must be positive")
    if duration is not None and abs(d - duration) > 0.5:
        raise ValueError(f"caption track duration {d}s differs from the video map's {duration}s")
    prev = 0.0
    if not isinstance(data["cues"], list) or not data["cues"]:
        raise ValueError("caption track has no cues")
    for i, c in enumerate(data["cues"]):
        if not isinstance(c, dict) or set(c) != {"s", "e", "text"} or not isinstance(c["text"], str) or not c["text"].strip():
            raise ValueError(f"caption cue {i}: needs s, e, text")
        if any(isinstance(c[k], bool) or not isinstance(c[k], (int, float)) for k in ("s", "e")):
            raise ValueError(f"caption cue {i}: times must be numbers")
        if c["s"] < prev - 0.001 or c["e"] <= c["s"] or c["e"] > d + 0.5:
            raise ValueError(f"caption cue {i}: times out of order or outside the video")
        prev = c["s"]
    return data


def lint_script(script):
    """(missing, findings): spoken cues without a show text, and [(where, rule, words)] spelled-math hits."""
    missing, findings = [], []
    for sc in script.get("scenes", []):
        for cue in sc.get("cues", []):
            if "say" not in cue:
                continue
            where = f"{sc.get('id')}.{cue.get('id')}"
            show = cue.get("show")
            if not isinstance(show, str) or not show.strip():
                missing.append(where)
                continue
            findings += [(where, rule, hit) for rule, hit in spelled_math(show)]
    return missing, findings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("lint", help="find show texts that spell math in words")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--project", type=Path)
    g.add_argument("--track", type=Path)
    a = ap.parse_args(argv)
    if a.project:
        missing, findings = lint_script(json.loads((a.project / "script.json").read_text(encoding="utf-8")))
    else:
        data = json.loads(a.track.read_text(encoding="utf-8"))
        missing, findings = [], [(f"{c['s']:.1f}s", r, h) for c in data["cues"] for r, h in spelled_math(c["text"])]
    for w in missing:
        print(f"{w}: no show text")
    for w, rule, hit in findings:
        print(f"{w}: {rule}: {hit!r}")
    print(f"{len(missing)} cue(s) without show text, {len(findings)} spelled-math finding(s)")
    return 1 if missing or findings else 0


if __name__ == "__main__":
    sys.exit(main())
