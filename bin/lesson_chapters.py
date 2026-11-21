#!/usr/bin/env python3
"""The chapters of a lesson, as the per-chapter videos see them.

A chapter is a `##` heading and everything up to the next one. Chapter 1 also holds the opening (the title,
Contents, Sources and the weights table before the first `##`); the front matter belongs to no chapter, so a new
banner never invalidates a video. A chapter video is tied to the SHA-256 of its chapter's text only: editing one
chapter invalidates that chapter's video and no other.

Chapter video files use the key NNNN-chNN (NNNN-ch02-lecture.mp4, video-NNNN-ch02.json); a segment's `line` in a
chapter map counts from the chapter's first line (1), so lines added above it do not move it.
"""

import hashlib
import re


def body_start(lines):
    """0-based index of the first line after the front matter."""
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return i + 1
    return 0


def spans(text):
    """[(first, last)] 1-based inclusive line spans, one per chapter, in order. A lesson with no `##` is one chapter."""
    lines = text.splitlines()
    start = body_start(lines)
    heads, fence = [], False
    for i in range(start, len(lines)):
        if lines[i].lstrip().startswith("```"):
            fence = not fence
        elif not fence and lines[i].startswith("## "):
            heads.append(i)
    firsts = [start] + heads[1:] if heads else [start]
    out = []
    for k, a in enumerate(firsts):
        b = firsts[k + 1] - 1 if k + 1 < len(firsts) else len(lines) - 1
        out.append((a + 1, max(a, b) + 1))
    return out


def titles(text):
    """The `##` heading of each chapter (chapter 1's own heading, or "Introduction" when there is none)."""
    lines = text.splitlines()
    out = []
    for a, b in spans(text):
        head = next((l[3:].strip() for l in lines[a - 1:b] if l.startswith("## ")), "Introduction")
        out.append(head)
    return out


def chapter_text(text, n):
    a, b = spans(text)[n - 1]
    return "\n".join(text.splitlines()[a - 1:b])


def chapter_sha(text, n):
    return hashlib.sha256(chapter_text(text, n).encode("utf-8")).hexdigest()


def key(lid, n=None):
    """NNNN for a whole-lesson video, NNNN-chNN for a chapter video."""
    return lid if n is None else f"{lid}-ch{int(n):02d}"


KEY = re.compile(r"\d{4}(?:-ch\d{2})?")
