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
# official problems (TEMPLATES.md, Official problems): every problem has a label, every src: file exists, and only a
# verbatim official multiple-choice item may have other than four (or two) options
import os
raw = open(sys.argv[1]).read()
lesson_dir = os.path.dirname(os.path.abspath(sys.argv[1]))
LABEL = re.compile(r"\[Official ·[^\]]*\]\(src:[^)]+\)|\*Written by Claude\*")
def src_exists(ref):
    ref = ref.split("#")[0]
    for base in (os.path.join(lesson_dir, "..", "sources"), os.path.join(lesson_dir, ".."), lesson_dir, os.path.join(lesson_dir, "..", "..")):
        if os.path.isfile(os.path.normpath(os.path.join(base, ref))):
            return True
    return False
for m in re.finditer(r"\]\(src:([^)\s]+)\)", raw):
    if not src_exists(m.group(1)):
        line = raw[:m.start()].count("\n") + 1
        print(f"  lint: line {line}: label source {m.group(1)} is not a file under sources/ or the course folder.", file=sys.stderr); warn += 1
L = raw.split("\n")
def label_above(i, span=14):
    """A label in the lines just above line i (0-based), not crossing a heading or another problem block's end."""
    for k in range(i - 1, max(-1, i - span), -1):
        t = L[k].strip()
        if LABEL.search(t):
            return True
        if t.startswith("#") or re.match(r"^::: (mcq|checkin)\b", t):
            return False
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
if warn: print(f"  lint: {warn} warning(s). TEMPLATES.md: one operation per line; tables as markdown tables.", file=sys.stderr)
