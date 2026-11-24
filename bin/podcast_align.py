#!/usr/bin/env python3
"""Make a lesson podcast's transcript JSON: when each sentence of the script starts in the audio.

    podcast_align.py script.txt audio.mp3 out.json

script.txt is the narration as read, paragraphs separated by a blank line. The audio's pauses come from ffmpeg
silencedetect (noise=-35dB, d=0.25); a DP picks one pause per sentence boundary, in order, close to where the
boundary falls by character count and preferring long pauses. Output: [{"p": paragraph, "t": start seconds, "s": sentence}].
Needs ffmpeg and ffprobe on PATH.
"""
import json
import re
import subprocess
import sys


def sentences(text):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out = []
    for pi, p in enumerate(paras):
        for s in re.split(r"(?<=[.?!])\s+", " ".join(p.split())):
            if s.strip():
                out.append((pi, s.strip()))
    return out


def duration(audio):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def silences(audio):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", audio, "-af", "silencedetect=noise=-35dB:d=0.25",
                        "-f", "null", "-"], capture_output=True, text=True)
    out, start = [], None
    for line in r.stderr.splitlines():
        m = re.search(r"silence_(start|end): (-?[\d.]+)", line)
        if not m:
            continue
        if m.group(1) == "start":
            start = float(m.group(2))
        elif start is not None:
            out.append((max(0.0, start), float(m.group(2))))
            start = None
    return out


def align(sents, sil, T):
    n = len(sents)
    if n == 0:
        return []
    pauses = [(a, b) for a, b in sil if a > 0.5 and b < T - 0.5]
    cands = [(a + b) / 2 for a, b in pauses]
    width = [b - a for a, b in pauses]
    m = len(cands)
    lens = [len(s) + 12 for _, s in sents]
    tot = sum(lens)
    cum = [0]
    for x in lens:
        cum.append(cum[-1] + x)
    pred = [cum[i + 1] / tot * T for i in range(n - 1)]
    if n == 1:
        bounds = [0.0, T]
    elif m < n - 1:   # too few pauses: fall back to the character-count estimate
        bounds = [0.0] + pred + [T]
    else:
        INF = float("inf")
        prev, back = [INF] * m, []
        for i in range(n - 1):
            cur, bk = [INF] * m, [-1] * m
            best, bi = INF, -1
            for j in range(m):
                if i > 0:
                    if j > 0 and prev[j - 1] < best:
                        best, bi = prev[j - 1], j - 1
                    base = best
                else:
                    base = 0.0
                if base == INF:
                    continue
                d = cands[j] - pred[i]
                cur[j] = base + (d / 25) ** 2 - 2 * min(width[j], 1.2)
                bk[j] = bi
            back.append(bk)
            prev = cur
        j = min(range(m), key=lambda k: prev[k])
        path = []
        for i in range(n - 2, -1, -1):
            path.append(j)
            j = back[i][j]
        path.reverse()
        bounds = [0.0] + [cands[j] for j in path] + [T]
    return [{"p": pi, "t": round(bounds[k], 2), "s": s} for k, (pi, s) in enumerate(sents)]


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: podcast_align.py script.txt audio.mp3 out.json")
    script, audio, out = sys.argv[1:]
    sents = sentences(open(script, encoding="utf-8").read())
    T = duration(audio)
    rows = align(sents, silences(audio), T)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    print(f"{len(rows)} sentences over {T:.1f}s -> {out}")


if __name__ == "__main__":
    main()
