#!/usr/bin/env python3
"""explain.py <lesson.md> '<request json>'

Headless writer for the board's expandable Explain callouts. Called by bridge.py in a background thread.
Request: {"text": selected words, "depth": "line"|"deep", "block": "b12", "line": 42,
          "parent": "e3" (nested) | null, "grow": "e5" (rewrite in place) | null, "pending": "p123" (page placeholder id)}
Writes the ::: exp block into the lesson file and prints {"id": "e8"}.
The lesson file change is picked up by the bridge's SSE loop; no explicit render call needed.
"""
import json, os, re, shutil, subprocess, sys, time

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path, req = sys.argv[1], json.loads(sys.argv[2])
text = (req.get("text") or "").strip()
depth = req.get("depth", "line")
parent, grow = req.get("parent"), req.get("grow")
src = open(path).read()
# No line from the page (it happens): find the selected words in the body instead of falling back to line 1,
# which would drop the callout into the front matter above the title.
if not req.get("line") and text:
    _fm = re.match(r"^---\n.*?\n---\n", src, re.S)
    _k = src.find(text, _fm.end() if _fm else 0)
    if _k < 0:
        _k = src.find(" ".join(text.split()[:4]), _fm.end() if _fm else 0)
    if _k >= 0:
        req["line"] = src[:_k].count("\n") + 1

def next_id(s):
    ids = [int(x) for x in re.findall(r"^::: exp e(\d+)", s, re.M)]
    return f"e{max(ids) + 1 if ids else 1}"

def course_mode(s):
    return bool(re.search(r"^course:\s*\S", s, re.M))

def context_lines(s, line, radius=40):
    lines = s.split("\n")
    lo, hi = max(0, line - radius), min(len(lines), line + radius)
    return "\n".join(lines[lo:hi])

def atomic_spans(lines):
    """0-based (start, end) line spans that must never be split: fenced code, ::: interactive JSON, tables.
    They can hold blank lines, so a paragraph search alone would insert a note in the middle of them."""
    spans, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if re.match(r"^\s*(```|~~~)", ln):
            fence = ln.strip()[:3]; j = i + 1
            while j < len(lines) and not lines[j].strip().startswith(fence):
                j += 1
            spans.append((i, min(j, len(lines) - 1))); i = j + 1; continue
        if re.match(r"^::: interactive\b", ln):
            j = i + 1
            while j < len(lines) and not re.match(r"^:::\s*$", lines[j]):
                j += 1
            spans.append((i, min(j, len(lines) - 1))); i = j + 1; continue
        if ln.lstrip().startswith("|"):
            j = i
            while j + 1 < len(lines) and lines[j + 1].lstrip().startswith("|"):
                j += 1
            spans.append((i, j)); i = j + 1; continue
        i += 1
    return spans


def block_at(s, line):
    """The markdown block (paragraph / $$ block / container) containing 1-based `line`, widened to the whole
    fenced code block, interactive block or table it touches, so a note is always inserted after those."""
    lines = s.split("\n")
    i = max(0, min(len(lines) - 1, line - 1))
    a = i
    while a > 0 and lines[a - 1].strip() != "":
        a -= 1
    b = i
    while b < len(lines) - 1 and lines[b + 1].strip() != "":
        b += 1
    spans = atomic_spans(lines)
    changed = True
    while changed:
        changed = False
        for x, y in spans:
            if x <= b and y >= a and (x < a or y > b):
                a, b, changed = min(a, x), max(b, y), True
    return a, b, "\n".join(lines[a:b + 1])

RULES = """You write one explanation for a student reading a lesson on a black board. It appears in an expandable callout under the selected paragraph.
Rules: one idea per sentence, at most 25 words; split long sentences instead of dropping words. Keep "that" and "of", keep the subject next to its verb, at most two nouns in a row, no nouns used as verbs, no objects doing human actions ("the term dies"), no invented phrases. Use only terms the lesson has already introduced, or explain a new term before you use it.
If the selected words name a rule, law, theorem, identity, method or technical term, the FIRST thing you write is what it is, in general form, before saying how it is used here. A name is not an explanation. Example: for "De Morgan" start with the law itself, $\\overline{{A+B}} = \\overline{{A}}\\,\\overline{{B}}$ and $\\overline{{AB}} = \\overline{{A}}+\\overline{{B}}$, then show it on this line.
Math typesetting: symbols inline with $...$. Any equation, and especially a chain of equal signs, goes on its own line as a display block:

$$ ... $$

Never write a chain like "= ... = ..." inside a sentence. One equation per display line; use \\begin{{aligned}} for a multi-step chain.
{length}
{tag}
Output only the note. Do not repeat or quote the selected words at the start. No label, no quotation marks around the answer, no markdown heading."""

length = "Length: explain the selected passage clearly in a short paragraph. Add steps or a display equation when needed to resolve the question. Avoid unrelated background." if depth == "line" else "Length: one paragraph, 4 to 8 sentences, plus one or two display equations."
tag = 'End with " → Exam: <problem it serves>" if the lesson text names an exam problem for this block, otherwise end with " → background".' if course_mode(src) and re.search(r"→ (Exam|background)\b", src) else "Do not add any trailing tag."  # STEM lessons carry no inline tags
a, b, block = block_at(src, int(req.get("line") or 1))
prompt = RULES.format(length=length, tag=tag) + f"""

Lesson excerpt (the block the student is reading is marked between <<< and >>>):
{context_lines(src, a, 30)}

<<<
{block}
>>>

The student selected: "{text}"
Explain what "{text}" means in this exact place."""

def run_writer(prompt):
    if shutil.which("claude"):
        cmd = ["claude", "-p", prompt, "--output-format", "text", "--no-session-persistence"]
        if os.environ.get("BLACKBOARD_WRITER_MODEL"):
            cmd += ["--model", os.environ["BLACKBOARD_WRITER_MODEL"]]
    elif shutil.which("codex"):
        cmd = ["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", prompt]
    else:
        raise RuntimeError("no headless writer: install Claude Code (claude) or Codex (codex)")
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDECODE")}
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=SKILL, env=env)
    out = (r.stdout or "").strip()
    if r.returncode != 0 or not out:
        raise RuntimeError((r.stderr or out or "writer failed")[:300])
    # codex exec prints its own preamble; keep the last paragraph
    if cmd[0] == "codex":
        out = out.strip().split("\n\n")[-1].strip()
    return out

def note_label(t):
    """First six words, extended so a $formula$ is never cut in half (the board's noteLabel does the same)."""
    dg = re.match(r"\s*\[diagram: ([^;\]]+)", t)
    if dg: t = "Diagram: " + dg.group(1)
    t = re.sub(r"\s*\(in \$[\s\S]*$", "", t)
    out = []
    for w in t.split():
        out.append(w)
        j = " ".join(out)
        if (len(out) >= 6 and j.count("$") % 2 == 0) or len(out) >= 40: break
    j = " ".join(out)
    return j.replace("$", "") if j.count("$") % 2 else j
label = note_label(text)
def existing_note(s, line, label):
    """Id of a top-level ::: exp with this label sitting right after the block at `line`, or None."""
    a, b, _ = block_at(s, line)
    lines = s.split("\n"); j = b + 1
    while j < len(lines):
        if lines[j].strip() == "": j += 1; continue
        m = re.match(r"^::: exp (e\d+)", lines[j])
        if not m: return None
        nxt = lines[j + 1] if j + 1 < len(lines) else ""
        lm = re.match(r"^\*\*([^*]+)\*\*", nxt)
        if lm and lm.group(1).strip().lower() == label.lower(): return m.group(1)
        d = 0
        while j < len(lines):
            if lines[j].startswith("::: "): d += 1
            elif re.match(r"^:::\s*$", lines[j]): d -= 1
            j += 1
            if d == 0: break
    return None

if not grow and not parent:
    dup = existing_note(src, int(req.get("line") or 1), label)
    if dup:
        s2 = re.sub(rf"^(::: exp {dup}[^\n]*?)\s*folded\s*$", r"\1", src, flags=re.M)
        if s2 != src: open(path, "w").write(s2)
        print(json.dumps({"id": dup, "pending": req.get("pending"), "reused": True})); sys.exit(0)
try:
    body = run_writer(prompt)
except Exception as e:
    print(json.dumps({"error": str(e)})); sys.exit(1)

# readability gate (TEMPLATES.md, Tone): one rewrite when the note breaks a checkable rule, else keep it as written
try:
    from prose_lint import check_text
    issues = check_text(body)
    if issues:
        fixed = run_writer("Rewrite this note so it fixes every problem listed. Keep its meaning, its math and LaTeX, "
                           "and its length. Split long sentences instead of dropping words. Output only the note.\n\nProblems:\n"
                           + "\n".join("- " + i for i in issues) + "\n\nNote:\n" + body)
        if fixed.strip():
            body = fixed
except Exception:
    pass

body = re.sub(r'^["“”\'\s]+|["“”\'\s]+$', '', body.strip())
body = re.sub(r'^\*\*[^*]+\*\*\s*[—:-]\s*', '', body)
# never let the writer's output open/close containers
body = body.replace("\n:::", "\n\\:::")

# The writer can take minutes; the file may have changed meanwhile (another callout, a fold, an edit). Re-read it under
# a lock and find the selected block again by its text, so nothing written in between is lost and ids never collide.
import fcntl, hashlib, tempfile
_lock = open(os.path.join(tempfile.gettempdir(), "bb-explain-" + hashlib.md5(os.path.abspath(path).encode()).hexdigest() + ".lock"), "w")
fcntl.flock(_lock, fcntl.LOCK_EX)
s = open(path).read()
line_now = int(req.get("line") or 1)
if block.strip() and s != src:
    k = s.find(block)
    if k >= 0:
        line_now = s[:k].count("\n") + 1 + max(0, line_now - (a + 1))
lines = s.split("\n")
if grow:
    m = re.search(rf"^::: exp {re.escape(grow)}(?P<flags>[^\n]*)\n\*\*(?P<label>[^*]+)\*\* — (?P<body>.*?)(?=\n(?:::: exp |:::\s*$))", s, re.S | re.M)
    if m:
        flags = m.group("flags")
        if "deep" not in flags:
            flags = (flags + " deep").rstrip()
        new = f"::: exp {grow}{flags}\n**{m.group('label')}** — {body}"
        s = s[:m.start()] + new + s[m.end():]
        eid = grow
    else:
        grow = None
if not grow:
    eid = next_id(s)
    block_md = f"::: exp {eid}{' deep' if depth == 'deep' else ''}\n**{label}** — {body}\n:::"
    if parent:
        # insert before the closing ::: of the parent block (after its children)
        m = re.search(rf"^::: exp {re.escape(parent)}[^\n]*\n", s, re.M)
        if m:
            i = m.end(); depth_c = 1
            while i < len(s) and depth_c > 0:
                nl = s.find("\n", i); ln = s[i:nl if nl >= 0 else len(s)]
                if ln.startswith("::: "): depth_c += 1
                elif re.match(r"^:::\s*$", ln): depth_c -= 1
                if depth_c == 0: break
                i = nl + 1 if nl >= 0 else len(s)
            s = s[:i] + block_md + "\n" + s[i:]
        else:
            parent = None
    if not parent:
        # Leave the selected paragraph untouched; insert the callout after it
        lines = s.split("\n")
        a2, b2, blk = block_at(s, line_now)
        # skip existing exp blocks that directly follow, so siblings keep order
        j = b2 + 1
        while j < len(lines):
            if lines[j].strip() == "": j += 1; continue
            if lines[j].startswith("::: exp"):
                d = 0
                while j < len(lines):
                    if lines[j].startswith("::: "): d += 1
                    elif re.match(r"^:::\s*$", lines[j]): d -= 1
                    j += 1
                    if d == 0: break
                continue
            break
        lines[j:j] = ["", block_md]
        s = "\n".join(lines)

open(path, "w").write(s)
print(json.dumps({"id": eid, "pending": req.get("pending")}))
