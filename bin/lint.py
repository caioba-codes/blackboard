#!/usr/bin/env python3
"""lint.py <lesson.md>  -- warn about derivation steps written sideways.
A display equation with more than one `=` or any `\\Rightarrow` outside an aligned/cases block is a chain of steps on one line.
The board's rule is one operation per line, reason in the margin. Prints warnings; exit 0 always."""
import re, sys

def strip_why(t):
    """\\why{math}{rule} (or \\why[name]{math}{rule}) -> math: the hint is board-only, every tool reads the plain math."""
    out, i = "", 0
    while True:
        k = t.find("\\why", i)
        if k < 0:
            return out + t[i:]
        j = k + 4
        if j < len(t) and t[j].isalpha():
            out += t[i:j]; i = j; continue
        if j < len(t) and t[j] == "[":
            e = t.find("]", j)
            j = e + 1 if e > 0 else j
        args = []
        for _ in range(2):
            while j < len(t) and t[j] == " ":
                j += 1
            if j >= len(t) or t[j] != "{":
                break
            d, q = 0, j
            while q < len(t):
                if t[q] == "\\":
                    q += 2; continue
                d += {"{": 1, "}": -1}.get(t[q], 0)
                if d == 0:
                    break
                q += 1
            args.append(t[j + 1:q]); j = q + 1
        if len(args) < 2:
            out += t[i:k + 4]; i = k + 4; continue
        out += t[i:k] + strip_why(args[0]); i = j

s = strip_why(open(sys.argv[1]).read())   # rule hints are not steps: judge the plain math
warn = 0
for m in re.finditer(r"\$\$(.*?)\$\$", s, re.S):
    body = m.group(1)
    if re.search(r"\\begin\{(aligned|cases|array|matrix)", body):
        continue
    # several independent formulas on one line (a reference table) are separated by \qquad, \quad or commas; judge each chunk
    chunks = re.split(r"\\qquad|\\quad|,\s", body)
    eq = max(len(re.findall(r"(?<![<>!:])=(?!=)", c)) for c in chunks)
    arrows = body.count("\\Rightarrow") + body.count("\\implies")
    if eq >= 3 or arrows >= 2 or (arrows == 1 and eq >= 2):
        line = s[:m.start()].count("\n") + 1
        print(f"  lint: line {line}: sideways derivation ({eq} '=' on one line). Use \\begin{{aligned}} with one step per line.", file=sys.stderr); warn += 1
for m in re.finditer(r"(?<!\$)\$(?!\$)([^$\n]+)\$(?!\$)", s):
    eqi = len(re.findall(r"(?<![<>!:])=(?!=)", m.group(1)))
    if eqi >= 3 or ("\\Rightarrow" in m.group(1) and eqi >= 2):
        line = s[:m.start()].count("\n") + 1
        print(f"  lint: line {line}: a chain of steps inside inline math. Break it into a display block, one step per line.", file=sys.stderr); warn += 1
# worked steps strung through a prose sentence (answers, your-turn, why: lines): two or more "=" across a line's inline math
body = re.sub(r"\$\$.*?\$\$", lambda m: "\n" * m.group(0).count("\n"), s, flags=re.S)
body = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), body, flags=re.S)
for n, ln in enumerate(body.split("\n"), 1):
    if ln.lstrip().startswith(("<!--", "|", "{")):
        continue
    # an option and its mistake line, or a question and its answer, are separate texts: judge each part of a "||" line
    eqs = max(sum(len(re.findall(r"(?<![<>!:\\])=(?!=)", t)) for t in re.findall(r"(?<!\$)\$(?!\$)([^$\n]+)\$(?!\$)", part)) for part in ln.split("||"))
    if eqs >= 2:
        print(f"  lint: line {n}: equations chained through prose ({eqs} '=' in inline math). Write it as a worked solution: setup, aligned steps with reasons, boxed answer.", file=sys.stderr); warn += 1
# tables faked in math: an array/tabular with \hline or | column rules is a table and belongs in a markdown board table
for m in re.finditer(r"\\begin\{(array|tabular)\}\{([^}]*)\}(.*?)\\end\{\1\}", s, re.S):
    if "|" in m.group(2) or "\\hline" in m.group(3):
        line = s[:m.start()].count("\n") + 1
        print(f"  lint: line {line}: a table built with \\begin{{{m.group(1)}}} and rules. Write it as a markdown table (TEMPLATES.md, Tables).", file=sys.stderr); warn += 1
# size is a board level, never hand-set: \Large, \Huge and friends in math -> wrap the display in ::: big or ::: key
for m in re.finditer(r"\\(Large|LARGE|large|Huge|huge)(?![A-Za-z])", s):
    line = s[:m.start()].count("\n") + 1
    print(f"  lint: line {line}: hand-sized math (\\{m.group(1)}). Wrap the display in ::: big (level 1) or ::: key (level 2) instead.", file=sys.stderr); warn += 1
# official problems (TEMPLATES.md, Problems and solutions): every problem has a label, every src: file exists, and only a
# verbatim official multiple-choice item may have other than four (or two) options
import os
from urllib.parse import unquote
raw = open(sys.argv[1]).read()
lesson_dir = os.path.dirname(os.path.abspath(sys.argv[1]))
LABEL = re.compile(r"\[Official ·[^\]]*\]\(src:[^)]+\)|\*Written by Claude\*")
def src_exists(ref):
    ref = unquote(ref.split("#")[0])
    for base in (os.path.join(lesson_dir, "..", "sources"), os.path.join(lesson_dir, ".."), lesson_dir, os.path.join(lesson_dir, "..", "..")):
        if os.path.isfile(os.path.normpath(os.path.join(base, ref))):
            return True
    return False
for m in re.finditer(r"\]\(src:([^)\s]+)\)", raw):
    if not src_exists(m.group(1)):
        line = raw[:m.start()].count("\n") + 1
        print(f"  lint: line {line}: label source {m.group(1)} is not a file under sources/ or the course folder.", file=sys.stderr); warn += 1
L = raw.split("\n")
# lines inside a ::: given block (the quoted problem); they do not count toward a label's distance
IN_GIVEN, _stack = set(), []
for n, l in enumerate(L):
    if re.match(r"^::: ", l):
        _stack.append(l.split()[1] if len(l.split()) > 1 else "")
    elif re.match(r"^:::\s*$", l) and _stack:
        _stack.pop()
    if "given" in _stack:
        IN_GIVEN.add(n)
for n, l in enumerate(L):   # the closing ::: of a given block
    if re.match(r"^:::\s*$", l) and n - 1 in IN_GIVEN:
        IN_GIVEN.add(n)
def label_above(i, span=14):
    """A label in the lines just above line i (0-based), not crossing a heading or another problem block's end.
    The lines of a ::: given block in between do not count toward the span."""
    k, left = i - 1, span
    while k >= 0 and left > 0:
        t = L[k].strip()
        if k not in IN_GIVEN:
            left -= 1
            if LABEL.search(t):
                return True
            if t.startswith("#") or re.match(r"^::: (mcq|checkin)\b", t):
                return False
        k -= 1
    return False
i = 0
while i < len(L):
    m = re.match(r"^::: (mcq|checkin)\b", L[i])
    if not m:
        i += 1; continue
    j = i + 1
    while j < len(L) and not re.match(r"^:::\s*$", L[j]):
        j += 1
    body = L[i + 1:j]
    above = label_above(i)
    if m.group(1) == "mcq":
        opts = [l for l in body if re.match(r"^\s*-", l)]
        labeled = above or any(LABEL.search(l) for l in body if not re.match(r"^\s*-", l))
        official = labeled and re.search(r"\[Official ·", "\n".join(L[max(0, i - 14):i] + body))
        if not labeled:
            print(f"  lint: line {i + 1}: a multiple-choice item without a label above it ([Official · …](src:…) or *Written by Claude*).", file=sys.stderr); warn += 1
        elif len(opts) not in (2, 4) and not official:
            print(f"  lint: line {i + 1}: {len(opts)} options; only a verbatim official item keeps a count other than four.", file=sys.stderr); warn += 1
    else:
        items = [n for n, l in enumerate(body) if re.match(r"^\s?-(\s|$)", l)]
        for n in items:
            if not (LABEL.search(body[n]) or (len(items) == 1 and above)):
                print(f"  lint: line {i + 2 + n}: a check-in item without a label (put the label on the item, or above a one-item check-in).", file=sys.stderr); warn += 1
    i = j + 1
# a Your turn is the exam question, nothing more: between an Official label and its problem block, only the quoted
# text and the source's own cropped figure (::: figure); a redrawn ::: fig there is help the exam never gave
for i, l in enumerate(L):
    if not re.search(r"\[Official ·[^\]]*\]\(src:", l) or l.lstrip().startswith("-"):
        continue
    for k in range(i + 1, min(len(L), i + 40)):
        t = L[k].strip()
        if re.match(r"^::: (mcq|checkin)\b", t) or t.startswith("#") or LABEL.search(t):
            break
        if re.match(r"^::: fig\b", t):
            print(f"  lint: line {k + 1}: a drawn ::: fig between an official problem's label and the problem. Show only the source's own figure (::: figure, cropped); move drawings into the solution.", file=sys.stderr); warn += 1
            break
# given vs calculated (TEMPLATES.md): an official problem's quoted text sits in a ::: given block under its label
for i, l in enumerate(L):
    if not re.search(r"\[Official ·[^\]]*\]\(src:", l) or l.lstrip().startswith("-"):
        continue
    for k in range(i + 1, min(len(L), i + 6)):
        t = L[k].strip()
        if not t or t.startswith("<!--") or re.fullmatch(r"\*\*Worked example[^*]*\*\*.*", t):
            continue
        if not re.match(r"^(::: (given|mcq|checkin)\b|#{1,6} |\*\*Solution)", t):
            print(f"  lint: line {k + 1}: an official problem's text outside a ::: given block. Wrap what the problem states (text, tables, figures) in ::: given so it reads apart from the work.", file=sys.stderr); warn += 1
        break
# a Written by Claude problem reads like an official one: its statement sits in the same ::: given card under the label
for i, l in enumerate(L):
    if l.strip() != "*Written by Claude*":
        continue
    for k in range(i + 1, min(len(L), i + 6)):
        t = L[k].strip()
        if not t or t.startswith("<!--"):
            continue
        if re.fullmatch(r"\*\*Worked example[^*]*\*\*.*", t):
            continue
        if not re.match(r"^(::: (given|mcq|checkin)\b|#{1,6} |\*\*Solution)", t):
            print(f"  lint: line {k + 1}: a Written by Claude problem's statement outside a ::: given block. Put it in ::: given under the label, as for an official problem.", file=sys.stderr); warn += 1
        break
# code lines stay at or under 60 characters (TEMPLATES.md, Board rules); official code quoted in a ::: given block is
# verbatim and never rewrapped, so it is exempt; so is the stem of an official multiple-choice item, quoted as printed
MAX_CODE = 60
OFFICIAL_CODE = set(IN_GIVEN)
for i, l in enumerate(L):
    if re.match(r"^::: mcq\b", l) and re.search(r"\[Official ·", "\n".join(L[max(0, i - 14):i])) and label_above(i):
        j = i + 1
        while j < len(L) and not re.match(r"^:::\s*$", L[j]):
            OFFICIAL_CODE.add(j); j += 1
fence = None
for n, l in enumerate(L):
    m = re.match(r"^(\s*)(```+)", l)
    if m:
        fence = None if fence is not None else len(m.group(1))
        continue
    if fence is None or n in OFFICIAL_CODE:
        continue
    code = l[fence:] if l[:fence].strip() == "" else l.lstrip()
    if len(code.rstrip()) > MAX_CODE:
        print(f"  lint: line {n + 1}: a code line of {len(code.rstrip())} characters (over {MAX_CODE}). Wrap it, or move a trailing comment onto its own line above.", file=sys.stderr); warn += 1
# an estimated breakdown (BLUEPRINT-STEM.md, Cumulative finals) is marked "**Exam Topics Breakdown (estimate)**" and must
# keep the line under its table that says it is an estimate and what it rests on
for i, l in enumerate(L):
    if not re.match(r"^\*\*Exam Topics Breakdown \(estimate\)\*\*", l.strip()):
        continue
    k = i + 1
    while k < len(L) and not L[k].strip():
        k += 1
    while k < len(L) and L[k].lstrip().startswith("|"):
        k += 1
    while k < len(L) and not L[k].strip():
        k += 1
    if k >= len(L) or "estimate" not in L[k].lower():
        print(f"  lint: line {i + 1}: an estimated Exam Topics Breakdown without its estimate line under the table. Keep the line that says the split is an estimate and what it rests on.", file=sys.stderr); warn += 1
# step sources (TEMPLATES.md, Step sources): a step's {@id} names a [phrase]{#id} tagged in its own problem, and {@L3-5}
# or {@name:L3-5} names lines of a code block in it. A problem is everything from its first label to the next problem:
# one quoted over two pages has two labels and two given cards, and a step may cite either. Its cards are its ::: given
# blocks and ::: mcq stems. In a lesson that uses step sources, a solved problem whose steps never cite it gets a soft note.
GTAG = re.compile(r"\[[^\[\]\n]+?\]\{#([A-Za-z][\w-]*)\}")
REF_ID = r"[A-Za-z][\w-]*(?::L\d+(?:-\d+)?)?"
GREF = re.compile(rf"\{{@({REF_ID}(?:\s+@?{REF_ID})*)\}}")
GLINE = re.compile(r"^(?:([A-Za-z][\w-]*):)?L(\d+)(?:-(\d+))?$")
IN_FENCE, FENCES, _open = set(), [], None
for n, l in enumerate(L):
    if re.match(r"^\s*```", l):
        IN_FENCE.add(n)
        if _open is None:
            nm = re.search(r"\{#([A-Za-z][\w-]*)\}", l)
            _open = (n, nm.group(1) if nm else None)
        else:
            FENCES.append({"start": _open[0], "end": n, "name": _open[1], "lines": n - _open[0] - 1}); _open = None
        continue
    if _open is not None:
        IN_FENCE.add(n)
STEM = set()   # ::: mcq stem lines (before its options and why:), fences included
for i, l in enumerate(L):
    if not re.match(r"^::: mcq\b", l):
        continue
    j, fence = i + 1, False
    while j < len(L) and not (re.match(r"^:::\s*$", L[j]) and not fence):
        if re.match(r"^\s*```", L[j]):
            fence = not fence
        if not fence and (re.match(r"^\s*-", L[j]) or L[j].startswith("why:")):
            break
        STEM.add(j); j += 1
CARD = IN_GIVEN | STEM
LABEL_LINES = [n for n, l in enumerate(L) if LABEL.search(l) and not l.lstrip().startswith("-")]
def chained(j, k):
    """Labels j < k belong to one problem when only its quoted cards (and blank lines) sit between them."""
    return all(m in CARD or not L[m].strip() or L[m].lstrip().startswith("<!--") for m in range(j + 1, k))
STARTS = []
for idx, k in enumerate(LABEL_LINES):
    if idx and chained(LABEL_LINES[idx - 1], k):
        continue
    STARTS.append(k)
def problem_of(n):
    starts = [k for k in STARTS if k <= n]
    return starts[-1] if starts else 0
def problem_end(start):
    nxt = [k for k in STARTS if k > start] + [len(L)]
    heads = [m for m in range(start + 1, nxt[0]) if re.match(r"^## ", L[m])]
    return heads[0] if heads else nxt[0]
for n, l in enumerate(L):
    if n in IN_FENCE:
        continue
    for t in GTAG.findall(l):
        if GLINE.match(t):
            print(f"  lint: line {n + 1}: tag {{#{t}}} looks like a line reference. Name tags with a word; {{@L3}} cites code lines.", file=sys.stderr); warn += 1
    for m in GREF.finditer(l):
        start = problem_of(n)
        tags = {t for k in range(start, n + 1) if k not in IN_FENCE for t in GTAG.findall(L[k])}
        blocks = [f for f in FENCES if start <= f["start"] < n and f["start"] in CARD]
        for rid in (x.lstrip("@") for x in m.group(1).split()):
            lm = GLINE.match(rid)
            if not lm:
                if rid not in tags:
                    print(f"  lint: line {n + 1}: the step cites {{@{rid}}} but its problem has no phrase tagged {{#{rid}}}. Tag the phrase in the ::: given card: [its words]{{#{rid}}}.", file=sys.stderr); warn += 1
                continue
            name, a, b = lm.group(1), int(lm.group(2)), int(lm.group(3) or lm.group(2))
            pick = [f for f in blocks if f["name"] == name] if name else blocks
            if not pick:
                what = f"code block named {{#{name}}}" if name else "code block"
                print(f"  lint: line {n + 1}: the step cites {{@{rid}}} but its problem has no {what} in a given card or mcq stem.", file=sys.stderr); warn += 1
            elif len(pick) > 1 and not name:
                print(f"  lint: line {n + 1}: {{@{rid}}} is ambiguous: its problem shows {len(pick)} code blocks. Name one (```java {{#node}}) and cite {{@node:{rid}}}.", file=sys.stderr); warn += 1
            elif not (1 <= a <= b <= pick[-1]["lines"]):
                print(f"  lint: line {n + 1}: {{@{rid}}} is outside the code block, which has {pick[-1]['lines']} lines.", file=sys.stderr); warn += 1
if any((GTAG.search(l) or GREF.search(l)) for n, l in enumerate(L) if n not in IN_FENCE):
    for a in STARTS:
        end = problem_end(a)
        worked = any("$$" in L[k] or (re.match(r"^\s*```", L[k]) and k not in CARD) for k in range(a, end))
        if worked and not any(GREF.search(L[k]) for k in range(a, end)):
            print(f"  lint: line {a + 1}: (soft) this solved problem has no step citing its problem ({{@id}}). Say where each fact comes from and tag it (TEMPLATES.md, Step sources).", file=sys.stderr)
if warn: print(f"  lint: {warn} warning(s). TEMPLATES.md: one operation per line; tables as markdown tables.", file=sys.stderr)
