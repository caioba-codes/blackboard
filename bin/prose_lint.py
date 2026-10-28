#!/usr/bin/env python3
"""prose_lint.py <lesson.md>  -- readability and order checks on a lesson's prose (TEMPLATES.md, Tone).

Checks the patterns a script can catch:
  - a sentence over 25 words (math counts as one word)
  - an object doing a human action ("the sign bites", "the method swallows")
  - "the root you found": a thing described by what someone does to it, with no "that"
  - three or more nouns in a row (only when spaCy and en_core_web_sm are installed)
  - order: a term or abbreviation used before the lesson explains it

Also imported by explain.py and quiz.py: check_text(text) returns warnings for a short generated text.
Prints warnings; exit 0 always. The tone editor handles what a script cannot judge."""
import re, sys

MAX_WORDS = 25
HUMAN_VERBS = r"bites?|swallows?|swallowed|eats|ate|eaten|dies|died|promises?|promised|kills?|killed|shadows|shadowed|hates?|likes|wants|knows|cares|complains?|insists?|refuses?|fires|fired"
HUMAN_RE = re.compile(rf"\b(?!(?:you|we|they|i|he|she|people|students?|the student|the reader)\b)(it|this|that|the [a-z$][^\s,.;:]*(?: [a-z][a-z-]*)?)\s+(?:{HUMAN_VERBS})\b", re.I)
PRONOUN_ORC = re.compile(r"\b(the|a|an|each|every|this) ([a-z]+) (you|we|they|he|she|I) ([a-z]+(?:ed|t|n|s)|did|got|made|saw|found|wrote|chose|picked|took|built|drew|kept|left)\b")
STOP_CAPS = {"I", "A", "OK", "TV", "PDF", "URL", "HTML", "CSS", "JS", "PM", "AM", "US", "USA", "UK", "II", "III", "IV"}


def prose_lines(s):
    """(line_no, text) for prose lines only. Math becomes the word X; code, front matter, tables,
    block markers, headings and the Prerequisites/Contents/Sources drop-downs are left out."""
    lines = s.split("\n")
    out, i, n = [], 0, len(lines)
    if lines and lines[0].strip() == "---":
        i = 1
        while i < n and lines[i].strip() != "---":
            i += 1
        i += 1
    skip_block = 0      # inside ::: prerequisites / contents / sources / fig / interactive / sheet
    in_code = in_math = False
    for k in range(i, n):
        ln = lines[k]
        st = ln.strip()
        if st.startswith("```"):
            in_code = not in_code; continue
        if in_code:
            continue
        if in_math:
            if "$$" in st:
                in_math = False
            continue
        if st.startswith("$$") and st.count("$$") == 1:
            in_math = True; continue
        if st.startswith(":::"):
            name = st[3:].strip().split(" ")[0] if st[3:].strip() else ""
            if name in ("prerequisites", "contents", "sources", "fig", "interactive", "sheet", "video", "figure", "photo"):
                skip_block += 1
            elif not name and skip_block:
                skip_block -= 1
            continue
        if re.match(r"^\*[^*].*\?\*$", st):
            continue    # the lesson's one-line opening question previews terms on purpose
        if skip_block or not st or st.startswith(("#", "|", "<!--", "{", "credit:", "query:", "caption:", "wrong:", "right:", "topics:")):
            continue
        t = re.sub(r"\$\$.*?\$\$", " X ", st)
        t = re.sub(r"\$[^$]+\$", "X", t)
        t = re.sub(r"`[^`]*`", "X", t)
        t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
        t = re.sub(r"^(?:[-*+]|\d+\.)\s+", "", t)
        t = re.sub(r"^why:\s*", "", t)
        out.append((k + 1, t))
    return out


def sentences(t):
    return [x for x in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9*_(\"“])", t) if x.strip()]


def words(t):
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'’-]*", t)


def _nlp():
    try:
        import spacy
        return spacy.load("en_core_web_sm", disable=["ner"])
    except Exception:
        return None


def noun_stacks(text, nlp):
    if nlp is None:
        return []
    out = []
    doc = nlp(text)
    run = []
    for tok in list(doc) + [None]:
        # a stack is nouns that modify the next noun: every noun but the last is a "compound" of what follows
        if tok is not None and tok.pos_ == "NOUN" and tok.text != "X" and tok.text.isalpha() and (tok.dep_ == "compound" or (run and tok.dep_ != "ROOT")):
            run.append(tok.text)
            if tok.dep_ == "compound":
                continue
        else:
            tok = None
        if len(run) >= 3:
            out.append(" ".join(run))
        run = []
    return out


def sentence_warnings(t, nlp=None):
    w = []
    for sent in sentences(t):
        n = len(words(sent))
        if n > MAX_WORDS:
            w.append(f"{n}-word sentence. Split it into two sentences (\"{sent[:50]}…\").")
    for m in HUMAN_RE.finditer(t):
        w.append(f"\"{m.group(0)}\": an object doing a human action. Say what actually happens.")
    for m in PRONOUN_ORC.finditer(t):
        w.append(f"\"{m.group(0)}\": add \"that\" or split it (\"You found the root. Plug it in.\").")
    for st in noun_stacks(t, nlp):
        w.append(f"\"{st}\": three or more nouns in a row. Rewrite with \"of\" or \"that\".")
    return w


def check_text(text):
    """Warnings for a short generated text (an Explain note, a quiz string)."""
    return sentence_warnings(" ".join(t for _, t in prose_lines(text)), _nlp())


# ---- order: used before explained ----------------------------------------------------------

def _variants(term):
    t = term.lower()
    v = {t}
    if t.endswith("s") and len(t) > 4:
        v.add(t[:-1])
    else:
        v.add(t + "s")
    return v


def order_warnings(pl):
    """A **bold** term marks where the lesson explains it. An ALL-CAPS abbreviation is explained where
    it is bold, spelled out in parentheses, or followed by "means", "stands for" or "is short for".
    Warn when either appears in prose earlier than that point."""
    w = []
    intro = {}   # term(lower) -> (line, shown)
    for ln, t in pl:
        for m in re.finditer(r"\*\*([^*]{2,40}?)\*\*", t):
            raw = m.group(1).strip()
            if raw.endswith((".", ":")):
                continue    # a bold label: "**Your turn.**", "**B.**", "**Setup:**"
            term = raw
            if len(term) < 2 or term.endswith(("?", "!")) or len(term.split()) > 4 or re.search(r"[0-9=$]", term):
                continue
            if m.start() <= 1 and re.match(r"\s*[.:—-]", t[m.end():m.end() + 2] + " "):
                continue    # a bold label such as "**Your turn.**" or "**Setup:**"
            if term.lower() in ("your turn", "setup", "answer", "next step", "note", "tip", "step"):
                continue
            intro.setdefault(term.lower(), (ln, term))
        for m in re.finditer(r"\b([A-Z]{2,6})\b(?:\s*\(([a-z][^)]+)\)|\s+(?:means|stands for|is short for)\b)", t):
            ab = m.group(1)
            if ab not in STOP_CAPS:
                intro.setdefault(ab.lower(), (ln, ab))
    plain = [(ln, re.sub(r"\*\*[^*]+\*\*", " ", t)) for ln, t in pl]
    for key, (iln, shown) in intro.items():
        is_abbr = shown.isupper()
        pats = [re.compile(rf"\b{re.escape(v)}\b", 0 if is_abbr else re.I) for v in ((shown,) if is_abbr else _variants(key))]
        for ln, t in plain:
            if ln >= iln:
                break
            if any(p.search(t) for p in pats):
                w.append((ln, f"\"{shown}\" is used here but explained on line {iln}. Move the explanation above its first use."))
                break
    return w


def main(path):
    s = open(path).read()
    pl = prose_lines(s)
    nlp = _nlp()
    warn = []
    for ln, t in pl:
        for msg in sentence_warnings(t, nlp):
            warn.append((ln, msg))
    warn += order_warnings(pl)
    for ln, msg in sorted(warn):
        print(f"  prose: line {ln}: {msg}", file=sys.stderr)
    if warn:
        extra = "" if nlp else " (noun-stack check off: pip install spacy && python3 -m spacy download en_core_web_sm)"
        print(f"  prose: {len(warn)} warning(s). TEMPLATES.md, Tone and Sequence meaning before use.{extra}", file=sys.stderr)
    return len(warn)


if __name__ == "__main__":
    main(sys.argv[1])
