#!/usr/bin/env python3
"""define.py <lesson.md> '<request json>'

Definition of 1-5 selected words, READ IN CONTEXT: the paragraph the student selected from
and the lesson around it pick the sense, so "prime" in a K-map lesson is not "prime number".
Request: {"text": selected words, "line": 42, "block": "b12"}
Prints {"text": ..., "term": ..., "via": "lesson"|"local"|"cli"}.

Nothing is written to the lesson file: this feeds a transient popup, so it is built to come
back fast, in three tiers, cheapest first:
  lesson  the lesson already defines the term -> instant, no model
  local   Ollama with thinking off -> ~2-3 s warm
  cli     claude -p -> 12-20 s, only when Ollama is not running
"""
import json, os, re, shutil, subprocess, sys, urllib.request

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLLAMA = os.environ.get("BLACKBOARD_OLLAMA", "http://127.0.0.1:11434")
CLI_MODEL = os.environ.get("BLACKBOARD_DEFINE_MODEL", "claude-haiku-4-5-20251001")
MAX_LOCAL_DEF = 240   # a lesson sentence longer than this is prose, not a definition

path, req = sys.argv[1], json.loads(sys.argv[2])
text = (req.get("text") or "").strip()
if not text:
    print(json.dumps({"error": "no selection"})); sys.exit(1)
src = open(path).read()
line = int(req.get("line") or 1)


def block_at(s, ln):
    """The markdown block (paragraph / $$ block / container) containing 1-based `ln`."""
    lines = s.split("\n")
    i = max(0, min(len(lines) - 1, ln - 1))
    a = i
    while a > 0 and lines[a - 1].strip() != "":
        a -= 1
    b = i
    while b < len(lines) - 1 and lines[b + 1].strip() != "":
        b += 1
    return a, b, "\n".join(lines[a:b + 1])


def nearby(s, ln, radius=7):
    lines = s.split("\n")
    return "\n".join(lines[max(0, ln - radius):min(len(lines), ln + radius)])


def front(s, key):
    m = re.search(rf"^{key}:\s*(.+)$", s, re.M)
    return m.group(1).strip() if m else ""


def unmath_words(s):
    """A small model likes to wrap the whole answer in math: $Riemann\\ sum$\\ refers\\ to...

    Any $...$ whose body is words with no real operators is prose, so unwrap it, and a
    backslash before a space is a TeX space that leaked into a sentence."""
    def fix(m):
        body = m.group(1)
        if re.search(r"[=+^_/\\{}<>]|\\\\[a-zA-Z]+", body.replace("\\ ", " ")):
            return m.group(0)                 # real math, keep it
        return body.replace("\\ ", " ").strip()
    s = re.sub(r"\$([^$]{1,120})\$", fix, s)
    s = s.replace("\\ ", " ").replace("\u202f", " ").replace("\\,", " ").replace("\\;", " ")
    return re.sub(r"\s+", " ", s)


def clean(s):
    s = re.sub(r'^["“”\'\s]+|["“”\'\s]+$', "", (s or "").strip())
    s = re.sub(r"^\*\*[^*]+\*\*\s*[—:-]\s*", "", s)
    s = re.sub(rf"^{re.escape(text)}\s*[—:-]\s*", "", s, flags=re.I)
    s = re.sub(r"<think>.*?</think>", "", s, flags=re.S | re.I)
    s = unmath_words(s.replace("$$", "$").replace("\n", " "))
    # "<term> refers to a loop that…" -> "A loop that…"
    # "A don't-care is a cell…" -> "A cell…"; the popup already shows the term as its title.
    # Only strip when a copula follows, so "Antiderivative of f" is left alone.
    s = re.sub(rf"^(the|a|an)?\s*{re.escape(text)}\b(\s+of\s+[^,.]{{0,40}}?)?\s*"
               r"(is|are|refers to|means|is defined as)\s+", "", s, count=1, flags=re.I)
    s = re.sub(r"^\W+", "", s)
    s = s.strip()
    return (s[0].upper() + s[1:]) if s else s


# ---------- tier 1: the lesson already says it ----------

def variants(t):
    t = t.strip().rstrip(".,;:")
    out = {t, t.lower()}
    if t.lower().endswith("s"):
        out.add(t[:-1])
        out.add(t[:-1].lower())
    else:
        out.add(t + "s")
    return {v for v in out if v}


def from_lesson(s, t):
    """A definition the lesson itself gives: a table row, a bold-dash note, or Term: sentence."""
    pats = []
    for v in variants(t):
        e = re.escape(v)
        pats += [
            rf"^\|\s*{e}\s*\|\s*(?P<d>[^|\n]+?)\s*\|",            # | Term | definition |
            rf"^\*\*{e}\*\*\s*[:—-]\s*(?P<d>[^\n]+)",         # **Term** — definition
            rf"^\*\*{e}\*\*:\s*\n(?P<d>[^\n*_][^\n]*)",            # **Term**:\ndefinition
            rf"^{e}\s*[:—]\s*(?P<d>[^\n]{{12,}})",            # Term: definition
        ]
    for p in pats:
        m = re.search(p, s, re.M | re.I)
        if m:
            d = clean(m.group("d"))
            d = re.sub(r"\s*\|?\s*$", "", d)
            if 12 <= len(d) <= MAX_LOCAL_DEF:
                return d
    return None


hit = from_lesson(src, text)
if hit:
    print(json.dumps({"text": hit, "term": text, "via": "lesson"})); sys.exit(0)

# ---------- the prompt both model tiers share ----------
a, b, block = block_at(src, line)
title, course = front(src, "title"), front(src, "course")
RULES = (
    "You define one term for a student reading a lesson on a black board.\n"
    "Give the meaning the term carries IN THIS LESSON, in this paragraph, not a generic dictionary sense: "
    "if the word has several meanings, pick the one the surrounding text uses, and keep the lesson's own notation.\n"
    "Length: one sentence, at most 25 words. Style: start straight with the definition, do not repeat the term, "
    "no \"refers to\", no preamble, no examples unless the definition is useless without one.\n"
    "Math: use $...$ ONLY around mathematical symbols, never around ordinary words, and never a display block. "
    "Never put a backslash before a space.\n"
    "Do not begin with the term itself and do not write \"refers to\", \"is a term for\" or \"means\": "
    "begin with the noun that the term is.\n"
    "If the paragraph does not discuss the term, still define it as it is used in this subject and lesson. "
    "Never answer that the lesson does not define or use it, never describe the lesson, never ask a question.\n"
    "Output only the definition."
)
def mentions(s, t, limit=3):
    """Other lines of the lesson that use the term: the rest of its context."""
    out, pats = [], [re.escape(v) for v in variants(t)]
    rx = re.compile("|".join(pats), re.I)
    for ln in s.split("\n"):
        q = ln.strip()
        if q and rx.search(q) and not q.startswith("::: ") and q not in out:
            out.append(q[:220])
        if len(out) >= limit:
            break
    return "\n".join(out)


elsewhere = mentions(src, text)
block = block[:900]
USER = ((f"Lesson: {title}\n" if title else "")
        + (f"Course: {course}\n" if course else "")
        + "\nLesson text around the selection:\n" + nearby(src, a)
        + "\n\nThe paragraph the student is reading:\n" + block
        + (f"\n\nOther lines of this lesson that use it:\n{elsewhere}" if elsewhere else "")
        + f"\n\nDefine, as used right here: \"{text}\"")
prompt = (RULES + "\n\n"
          + (f"Lesson: {title}\n" if title else "")
          + (f"Course: {course}\n" if course else "")
          + "\nLesson text around the selection:\n" + nearby(src, a)
          + "\n\nThe paragraph the student is reading:\n" + block
          + (f"\n\nOther lines of this lesson that use it:\n{elsewhere}" if elsewhere else "")
          + f"\n\nDefine, as used right here: \"{text}\"")


SCRATCH = re.compile(r"^(we are given|we need to|the lesson text|let me|first,|looking at|okay|the user)", re.I)


def usable(s):
    """Enough letters outside math to be a sentence, and not just the term back."""
    if not s or len(s) < 12:
        return False
    prose = re.sub(r"\$[^$]*\$", "", s)
    if len(re.findall(r"[A-Za-z]", prose)) < 10:
        return False
    if SCRATCH.match(s.strip()):
        return False
    return s.strip().lower() != text.strip().lower()


def local_model():
    """Ollama, thinking off (a thinking model spends the whole budget reasoning and returns '')."""
    try:
        tags = json.load(urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=1.5)).get("models") or []
    except Exception:
        return None
    if not tags:
        return None
    want = os.environ.get("BLACKBOARD_DEFINE_LOCAL")
    # A 25-word definition out of supplied context is compression, not reasoning: a 3B answers in
    # under a second where a 27B takes eight. Prefer a plain instruct model — a hybrid reasoning
    # model (qwen3) prints its scratchpad here, since Ollama 0.33 honours neither think:false nor
    # /no_think for it. Otherwise fall back to the smallest installed.
    PREFER = ("llama3.2:3b", "llama3.2", "gemma3:4b", "gemma3", "phi4-mini", "qwen2.5:3b", "mistral")
    names = [m["name"] for m in tags]
    model = want
    if not model:
        for want_name in PREFER:
            hit = next((n for n in names if n.startswith(want_name)), None)
            if hit:
                model = hit
                break
    model = model or min(tags, key=lambda m: m.get("size") or 0)["name"]
    def chat(user, temp=0.2):
        body = json.dumps({"model": model, "think": False, "stream": False, "keep_alive": "30m",
                           "messages": [{"role": "system", "content": RULES},
                                        {"role": "user", "content": user}],
                           "options": {"num_predict": 90, "temperature": temp}}).encode()
        r = urllib.request.Request(f"{OLLAMA}/api/chat", data=body, headers={"Content-Type": "application/json"})
        d = json.load(urllib.request.urlopen(r, timeout=45))
        return clean((d.get("message") or {}).get("content", ""))

    try:
        out = chat(USER)
    except Exception:
        return None
    if usable(out):
        return out
    # small models echo the term or answer in math; one stricter retry is still under a second
    strict = (USER + "\n\nAnswer with one plain sentence of at most 20 words, nothing else. "
              "Do not write the term. Do not explain your reasoning. "
              "Do not use $ unless it wraps a single mathematical symbol.")
    try:
        out2 = chat(strict, temp=0)
        return out2 if usable(out2) else (out or None)
    except Exception:
        return out or None


def cli_model():
    if shutil.which("claude"):
        cmd = ["claude", "-p", prompt, "--output-format", "text", "--no-session-persistence", "--model", CLI_MODEL]
    elif shutil.which("codex"):
        cmd = ["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", prompt]
    else:
        raise RuntimeError("no definer: run Ollama, or install Claude Code / Codex")
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDECODE")}
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=90, cwd=SKILL, env=env)
    out = (r.stdout or "").strip()
    if r.returncode != 0 or not out:
        raise RuntimeError((r.stderr or out or "definer failed")[:200])
    if cmd[0] == "codex":
        out = out.strip().split("\n\n")[-1].strip()
    return clean(out)


REFUSAL = re.compile(r"^(the lesson|this lesson|the (paragraph|text|excerpt))\b.*\b(does not|doesn't|never)\b|^I (cannot|can't|don't)", re.I)

body = local_model()
via = "local"
if body and REFUSAL.match(body):
    body = None          # fall through to the stronger model rather than show a non-answer
if not body:
    try:
        body, via = cli_model(), "cli"
    except Exception as e:
        print(json.dumps({"error": str(e)})); sys.exit(1)
print(json.dumps({"text": body, "term": text, "via": via}))
