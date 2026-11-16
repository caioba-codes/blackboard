#!/usr/bin/env python3
"""given.py <lesson.md> [--write]  -- mark what each official problem gives (TEMPLATES.md, Given vs calculated).

For a lesson written before the rule:
  - wraps the quoted text, tables and figures under each `[Official · …](src:…)` label in a `::: given` block
    (a leading "**Worked example.** …" line stays outside: it is ours);
  - in the check-in answer that follows, marks a solution table's columns copied from the problem with `>` (same
    header as a table in the given block, and every cell equal to the given cell);
  - keeps an installed video in sync: `$WS/reference/video-NNNN.json` gets its segment lines moved and the new
    lesson hash, but only when it matched the lesson before the edit.
Without --write it only reports what it would change."""
import hashlib, json, os, re, sys

LABEL = re.compile(r"\[Official ·[^\]]*\]\(src:[^)]+\)")
STOP = re.compile(r"^(#{1,6} |::: (checkin|mcq|fig|interactive|given)\b|\*\*(Solution|Worked example|Your turn)\b|\*Written by Claude\*)")
ROW = re.compile(r"^\s*\|(.*)\|\s*$")


def cells(line):
    return [c.strip() for c in ROW.match(line).group(1).split("|")]


def tables(lines):
    """[(header_index, [body indexes])] for each markdown table in lines."""
    out, i = [], 0
    while i < len(lines):
        if ROW.match(lines[i]) and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            j = i + 2
            while j < len(lines) and ROW.match(lines[j]):
                j += 1
            out.append((i, list(range(i + 2, j))))
            i = j
        else:
            i += 1
    return out


def wrap(text):
    L = text.split("\n")
    inserts = []          # (old index, line) inserted before that old line
    header_edits = {}     # old index -> new text
    fence = False
    stack = []            # open ::: containers by name; a label inside a check-in or mcq item is not a problem block
    i = 0
    while i < len(L):
        l = L[i]
        if re.match(r"^\s*(```|~~~)", l):
            fence = not fence
        if fence:
            i += 1
            continue
        if re.match(r"^::: ", l):
            stack.append(l.split()[1] if len(l.split()) > 1 else "")
        elif re.match(r"^:::\s*$", l) and stack:
            stack.pop()
        if set(stack) & {"checkin", "mcq", "given"} or not LABEL.search(l) or re.match(r"^\s*-", l):
            i += 1
            continue
        s = i + 1
        while s < len(L) and (not L[s].strip() or L[s].lstrip().startswith("<!--")):
            s += 1
        lead = []
        if s < len(L) and re.match(r"^\*\*Worked example", L[s]):
            w = re.match(r"^(\*\*Worked example[^*]*\*\*)\s*(.*)$", L[s])
            note = " ".join(L[max(0, i - 3):i])
            if w and w.group(2) and re.search(r"verbatim|quoted", note):
                # the official text shares the "Worked example." line: split it, the label stays ours
                header_edits[s] = w.group(1)
                lead = ["", "::: given", w.group(2)]
            s += 1
            if not lead:
                while s < len(L) and not L[s].strip():
                    s += 1
        if not lead and (s >= len(L) or STOP.match(L[s]) or LABEL.search(L[s])):
            i += 1
            continue
        e, d, f = s - 1 if lead else s, 0, False
        k = s
        while k < len(L):
            t = L[k]
            if re.match(r"^\s*(```|~~~)", t):
                f = not f
            if not f and d == 0 and (STOP.match(t) or LABEL.search(t)):
                break
            if not f and re.match(r"^::: ", t):
                d += 1
            elif not f and re.match(r"^:::\s*$", t):
                if d == 0:
                    break         # the end of the container this problem sits in
                d -= 1
            if t.strip():
                e = k
            k += 1
        inserts += ([(s, x) for x in lead] if lead else [(s, "::: given")]) + [(e + 1, ":::")]
        # the check-in answer of this problem: mark columns copied from a given table
        given = L[s:e + 1]
        gtabs = {tuple(cells(given[h])): [cells(given[b]) for b in body] for h, body in tables(given)}
        if gtabs and k < len(L) and re.match(r"^::: checkin\b", L[k]):
            c = k + 1
            while c < len(L) and not re.match(r"^:::\s*$", L[c]):
                c += 1
            for h, body in tables(L[k + 1:c]):
                h += k + 1
                head = cells(L[h])
                rows = gtabs.get(tuple(x.lstrip(">").strip() for x in head))
                if not rows or len(rows) != len(body):
                    continue
                ans = [cells(L[b + k + 1]) for b in body]
                mark = [n for n in range(len(head)) if all(r[n] for r in rows)
                        and all(a[n].strip("*") == r[n] for a, r in zip(ans, rows))]
                if mark and len(mark) < len(head):
                    lead = re.match(r"^(\s*)", L[h]).group(1)
                    header_edits[h] = lead + "| " + " | ".join((">" + x if n in mark and not x.startswith(">") else x)
                                                           for n, x in enumerate(head)) + " |"
        i = k
    out, mapping, j = [], {}, 0
    ins = sorted(inserts, key=lambda x: x[0])
    for n, l in enumerate(L):
        while j < len(ins) and ins[j][0] == n:
            out.append(ins[j][1]); j += 1
        mapping[n + 1] = len(out) + 1
        out.append(header_edits.get(n, l))
    while j < len(ins):
        out.append(ins[j][1]); j += 1
    return "\n".join(out), mapping, sum(1 for _, x in inserts if x == "::: given"), len(header_edits)


def remap_video(lesson, old, new, mapping):
    lid = os.path.basename(lesson)[:4]
    ref = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(lesson))), "reference", f"video-{lid}.json")
    if not os.path.isfile(ref):
        return "no video"
    m = json.load(open(ref, encoding="utf-8"))
    if m.get("lessonSha256", "").lower() != hashlib.sha256(old.encode()).hexdigest():
        return "video map was already stale; left alone"
    for sg in m.get("segments", []):
        sg["line"] = mapping.get(sg["line"], sg["line"])
    m["lessonSha256"] = hashlib.sha256(new.encode()).hexdigest()
    tmp = ref + ".tmp"
    json.dump(m, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, ref)
    return f"video map moved ({len(m.get('segments', []))} segments)"


def main(argv):
    path, write = argv[0], "--write" in argv
    old = open(path, encoding="utf-8").read()
    new, mapping, blocks, heads = wrap(old)
    msg = f"{blocks} given block(s), {heads} line(s) edited (given table columns, split worked-example lines)"
    if write and new != old:
        video = remap_video(path, old, new, mapping)
        open(path, "w", encoding="utf-8").write(new)
        msg += f"; written; {video}"
    print(msg)


if __name__ == "__main__":
    main(sys.argv[1:])
