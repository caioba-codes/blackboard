#!/usr/bin/env python3
"""Blackboard bridge: serves the board, streams lesson changes, queues page actions.

Routes
  GET  /                 hub: the all-lessons menu (same as /lessons)
  GET  /lessons          hub: every lesson in every workspace (rendered before, or found under the scan roots)
  GET  /lessons/NNNN     board page for one lesson (last rendered workspace)
  GET  /<prefix>[/N]     short link: unique slug prefix -> /w/<slug>/lessons[/000N] (e.g. /m/3)
  GET  /w/<slug>/        board page pinned to one workspace: follows that workspace's current lesson
  GET  /w/<slug>/lessons/NNNN, /w/<slug>/assets/<file>, and every /api route accepts ?ws=<slug>
  GET  /api/state        {ws, slug, current, page_version, lessons:[...], brainstorm:{lesson,lines,rev}, workspaces:[{slug,name,path,current,count,last,lessons}]}
  GET  /api/lesson?id=NNNN&from=N&hash=H   {text, offset, reset}  (text = new bytes cut at last blank line)
  GET  /events?id=NNNN   SSE: `change` when the lesson file or state changes
  GET  /assets/<file>    $WS/lessons/assets/<file>
  GET  /api/sources?id=NNNN   {files: [...]} every file the lesson cites, with its viewer URL
  GET  /api/source-check?p=REF&p=REF   which references (e.g. paths the chat cites) name a viewable file
  GET  /source/<path>    a cited file (pdf, image, text), only from inside the course folder
  GET  /anim/<path>      board/anim/<path>
  GET  /end-card.jpg     the optional end-of-lesson photo (end_card_path()), 404 when none is configured
  POST /ask              {kind,...} -> appended to queue.jsonl, wake per host
  POST /open             {urls:[board lesson URLs]} -> opened in the default browser (for in-app panes that cannot open tabs)
  POST /define           {text,line,block} -> {text} dictionary definition of 1-5 selected words, in lesson context
  GET  /api/chat?lesson=NNNN        the lesson's chat thread {session_id, messages, running, pending}
  POST /chat             {lesson, text, selection?} -> SSE over the response: step {tool,label}, delta {text}, done {}, error {message}
  POST /chat/stop        {lesson} stops that lesson's running reply
  POST /chat/new         {lesson} archives the thread and starts an empty one
  GET  /health           ok
State lives in $BLACKBOARD_HOME/state.json (default ~/.cache/blackboard), written by render.sh: {ws, current, agent, layout, cli_surface, opened}
"""
import unicodedata
import calendar, fnmatch, glob, hashlib, json, os, re, shutil, signal, subprocess, sys, tempfile, threading, time, urllib.parse, uuid
import math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BOARD = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BOARD)
HOME_DIR = os.environ.get("BLACKBOARD_HOME") or os.path.join(os.path.expanduser("~"), ".cache", "blackboard")
os.makedirs(HOME_DIR, exist_ok=True)
STATE = os.path.join(HOME_DIR, "state.json")
QUEUE = os.path.join(HOME_DIR, "queue.jsonl")
TMPL = os.path.join(BOARD, "board.html.tmpl")
PORT = int(os.environ.get("BLACKBOARD_PORT", "7331"))


def state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except Exception:
        return {}


def scan_roots():
    """Folders to search for lessons/: BLACKBOARD_SCAN (colon-separated), else "scan" in $BLACKBOARD_HOME/config.json,
    else the grandparent of the last rendered workspace (…/school/math1552/learn -> …/school)."""
    env = os.environ.get("BLACKBOARD_SCAN")
    if env:
        return [os.path.expanduser(p) for p in env.split(":") if p]
    try:
        with open(os.path.join(HOME_DIR, "config.json")) as f:
            cfg = json.load(f)
        roots = cfg.get("scan") or []
        if roots:
            return [os.path.expanduser(p) for p in roots]
    except Exception:
        pass
    w = state().get("ws")
    return [os.path.dirname(os.path.dirname(os.path.abspath(w)))] if w else []


def end_card_path():
    """The optional photo on every lesson's end card. Local only, never shipped with the skill: BLACKBOARD_END_CARD, else
    "end_card" in $BLACKBOARD_HOME/config.json, else ~/.config/blackboard/end-card.jpg. A path inside the skill folder is
    refused, so the public mirror can never carry it. "" when there is none."""
    p = os.environ.get("BLACKBOARD_END_CARD")
    if not p:
        try:
            with open(os.path.join(HOME_DIR, "config.json")) as f:
                p = json.load(f).get("end_card")
        except Exception:
            p = None
    p = os.path.realpath(os.path.expanduser(p or "~/.config/blackboard/end-card.jpg"))
    if p.startswith(os.path.realpath(ROOT) + os.sep):
        return ""
    return p if os.path.isfile(p) else ""


_scan = {"t": 0, "v": [], "roots": None}


def slug_of(path):
    """Course slug for a workspace path: the directory above `learn` (math1552/learn -> math1552), else the basename."""
    path = os.path.abspath(path)
    base = os.path.basename(path)
    if base == "learn":
        base = os.path.basename(os.path.dirname(path))
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "ws"


def discovered():
    """Every */learn/lessons (depth <= 4) under the scan roots, cached for 30 s."""
    roots = scan_roots()
    if time.time() - _scan["t"] < 30 and roots == _scan["roots"]:
        return _scan["v"]
    out = []
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dp, dns, fns in os.walk(root):
            depth = dp[len(root):].count(os.sep)
            dns[:] = [d for d in dns if not d.startswith(".") and d not in ("node_modules", "venv", ".venv", "dist", "build", "assets")]
            if depth >= 4:
                dns[:] = []
            if os.path.basename(dp) == "lessons" and any(re.match(r"^\d{4}-.+\.md$", f) for f in fns):
                out.append(os.path.dirname(dp))
    _scan.update(t=time.time(), v=out, roots=roots)
    return out


def workspaces():
    """slug -> {path, current, streaming, rev, ...}: registered (rendered) workspaces plus discovered ones."""
    st = state()
    out, paths = {}, set()

    def add(slug, entry):
        path = os.path.realpath(entry["path"])
        if path in paths:
            return
        if slug in out:
            base = slug + "-" + hashlib.md5(path.encode()).hexdigest()[:4]
            slug = base
            suffix = 2
            while slug in out:
                slug = f"{base}-{suffix}"
                suffix += 1
        out[slug] = dict(entry)
        paths.add(path)

    for slug, w in (st.get("workspaces") or {}).items():
        if w.get("path") and os.path.isdir(os.path.join(w["path"], "lessons")):
            add(slug, w)
    if st.get("ws") and os.path.isdir(st["ws"]):
        add(slug_of(st["ws"]), {"path": st["ws"], "current": st.get("current", "")})
    for path in discovered():
        add(slug_of(path), {"path": path, "current": ""})
    return out


def ws(slug=None):
    """Workspace path: the slug's, else the last rendered one."""
    if slug:
        # Registered aliases remain valid for existing bookmarked lesson URLs.
        w = (state().get("workspaces") or {}).get(slug) or workspaces().get(slug)
        if w:
            return w["path"]
    return state().get("ws") or os.getcwd()


def current(slug=None):
    st = state()
    if slug:
        w = (st.get("workspaces") or {}).get(slug)
        if w and w.get("current"):
            return w["current"]
        if slug != slug_of(st.get("ws", "")):
            files = lesson_files(ws(slug))
            return files[-1][0] if files else ""
    return st.get("current", "")


def lessons_dir(wsp=None):
    return os.path.join(wsp or ws(), "lessons")


def front_matter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
    return fm


def lesson_files(wsp=None):
    d = lessons_dir(wsp)
    if not os.path.isdir(d):
        return []
    out = []
    for name in sorted(os.listdir(d)):
        m = re.match(r"^(\d{4})-(.+)\.md$", name)
        if m:
            out.append((m.group(1), m.group(2), os.path.join(d, name)))
    return out


def lesson_path(lid, wsp=None):
    for i, slug, p in lesson_files(wsp):
        if i == lid:
            return p
    return None


def lesson_video(lid, wsp, slug=""):
    """Return only verified, workspace-local media metadata to the lesson page."""
    if not re.fullmatch(r"\d{4}", lid):
        return {"available": False, "error": "Invalid lesson id."}
    lesson = lesson_path(lid, wsp)
    if not lesson:
        return {"available": False, "error": "Lesson not found."}
    workspace = os.path.realpath(wsp)
    if not os.path.realpath(lesson).startswith(workspace + os.sep):
        return {"available": False, "error": "Lesson video manifest is invalid."}
    reference = os.path.realpath(os.path.join(wsp, "reference"))
    manifest_path = os.path.realpath(os.path.join(reference, f"video-{lid}.json"))
    if not reference.startswith(workspace + os.sep) or not manifest_path.startswith(reference + os.sep) or not os.path.isfile(manifest_path):
        return {"available": False}
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        if not isinstance(manifest, dict) or manifest.get("version") != 1 or isinstance(manifest.get("version"), bool):
            raise ValueError
        if set(manifest) != {"version", "lessonId", "lessonSha256", "video", "duration", "captionsBurnedIn", "segments"}:
            raise ValueError
        source_hash = manifest["lessonSha256"]
        if manifest.get("lessonId") != lid or not isinstance(source_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", source_hash):
            raise ValueError
        video = manifest.get("video")
        if not isinstance(video, str) or video != f"{lid}-lecture.mp4":
            raise ValueError
        assets = os.path.realpath(os.path.join(wsp, "lessons", "assets"))
        media = os.path.realpath(os.path.join(assets, video))
        if not assets.startswith(workspace + os.sep) or not media.startswith(assets + os.sep) or not os.path.isfile(media):
            raise ValueError
        duration = manifest.get("duration")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
            raise ValueError
        if not isinstance(manifest.get("captionsBurnedIn"), bool):
            raise ValueError
        segments = manifest.get("segments")
        if not isinstance(segments, list) or not segments:
            raise ValueError
        with open(lesson, "rb") as f:
            source = f.read()
        mapping_valid = hashlib.sha256(source).hexdigest().lower() == source_hash.lower()
        line_count = len(source.decode("utf-8").splitlines())
        seen, previous_end = set(), 0
        for segment in segments:
            if not isinstance(segment, dict):
                raise ValueError
            if not {"id", "label", "start", "end", "line"} <= set(segment) or set(segment) - {"id", "label", "start", "end", "line", "step", "practice"}:
                raise ValueError
            sid, label = segment.get("id"), segment.get("label")
            if not isinstance(sid, str) or not sid.strip() or sid in seen or not isinstance(label, str) or not label.strip():
                raise ValueError
            seen.add(sid)
            start, end = segment.get("start"), segment.get("end")
            if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in (start, end)):
                raise ValueError
            if start < previous_end or end <= start or end > duration + 0.01:
                raise ValueError
            previous_end = end
            line, step = segment.get("line"), segment.get("step")
            if isinstance(line, bool) or not isinstance(line, int) or line < 1 or (mapping_valid and line > line_count):
                raise ValueError
            if step is not None and (isinstance(step, bool) or not isinstance(step, int) or step < 1):
                raise ValueError
            practice = segment.get("practice")
            if practice is not None:
                if not isinstance(practice, dict) or set(practice) != {"pauseAt", "revealAt"}:
                    raise ValueError
                pause, reveal = practice["pauseAt"], practice["revealAt"]
                if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in (pause, reveal)):
                    raise ValueError
                if not start <= pause < reveal <= end:
                    raise ValueError
        url = f"/w/{urllib.parse.quote(slug, safe='')}/assets/{video}" if slug else f"/assets/{video}"
        return dict(manifest, available=True, mappingValid=mapping_valid, videoUrl=url)
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return {"available": False, "error": "Lesson video manifest is invalid."}


def scores(wsp=None):
    p = os.path.join(wsp or ws(), "learning-records", "quiz-log.jsonl")
    out = {}
    try:
        with open(p) as f:
            for line in f:
                try:
                    r = json.loads(line)
                    if r.get("event") == "reset" or r.get("score") is None:
                        continue
                    out.setdefault(str(r.get("lesson")), []).append(int(r["score"]))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def log_mcq(req):
    """A multiple-choice click is verified evidence: one quiz-log line (score 5 right, 0 wrong), read back by the page (XP, restored answers) and by learning records."""
    try:
        d = os.path.join(ws(req.get("ws")), "learning-records")
        os.makedirs(d, exist_ok=True)
        rec = {"ts": req.get("ts"), "lesson": str(req.get("lesson", "")), "topic": req.get("item", ""), "mode": "mcq",
               "item": req.get("item", ""), "choice": req.get("choice", ""), "sig": req.get("sig", ""),
               "score": 5 if req.get("correct") else 0}
        if req.get("event") == "reset":
            # Reset on the board: no score, the item reads as unanswered; earlier picks stay as evidence
            rec = {"ts": req.get("ts"), "lesson": str(req.get("lesson", "")), "topic": req.get("item", ""), "mode": "mcq",
                   "item": req.get("item", ""), "event": "reset", "sig": req.get("sig", "")}
        with open(os.path.join(d, "quiz-log.jsonl"), "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        sys.stderr.write(f"mcq log error: {e}\n")


def answers(lid, wsp=None):
    """Latest multiple-choice answer per item for one lesson: {item: {choice, sig, correct}}."""
    out = {}
    try:
        with open(os.path.join(wsp or ws(), "learning-records", "quiz-log.jsonl")) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("mode") == "mcq" and str(r.get("lesson")) == str(lid) and r.get("item"):
                    if r.get("event") == "reset":
                        out.pop(r["item"], None)
                        continue
                    out[r["item"]] = {"choice": r.get("choice", ""), "sig": r.get("sig", ""), "correct": r.get("score", 0) >= 3}
    except FileNotFoundError:
        pass
    return out


def lessons_meta(wsp=None):
    sc = scores(wsp)
    out = []
    for i, slug, p in lesson_files(wsp):
        try:
            with open(p) as f:
                text = f.read(4000)
        except Exception:
            text = ""
        fm = front_matter(text)
        title = fm.get("title")
        if not title:
            m = re.search(r"^# (.+)$", text, re.M)
            title = m.group(1) if m else slug.replace("-", " ")
        out.append({
            "id": i, "slug": slug, "title": title, "course": fm.get("course", ""),
            "exam": fm.get("exam", ""), "photo": fm.get("photo", ""), "credit": fm.get("credit", ""),
            "date": time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(p))),
            "mtime": int(os.path.getmtime(p)),
            "scores": sc.get(i, []),
        })
    return out


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


def _plain(line):
    """Readable text of one markdown line: LaTeX commands, markup and block fences removed."""
    t = re.sub(r"\\(overline|bar|mathrm|text|textbf|mathbf|boxed)\{([^{}]*)\}", r"\2", strip_why(line))
    t = re.sub(r"\\[a-zA-Z]+", " ", t)
    t = re.sub(r"\\[,;:! ]|\\\\", " ", t)
    t = re.sub(r"[$*_`>#|{}]|^:::.*$|^\s*- ", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _anchor(heading):
    t = unicodedata.normalize("NFKD", _plain(heading).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60]
    return "s-" + (t or "section")


def search(q, limit=30):
    """Full-text search over every lesson in every workspace. All words must appear in the lesson;
    each hit carries the best matching line, its section and a link that scrolls there."""
    words = [w for w in re.split(r"\s+", q.lower().strip()) if w]
    if not words:
        return []
    hits = []
    for slug, w in workspaces().items():
        for lid, _, path in lesson_files(w["path"]):
            try:
                text = open(path, encoding="utf-8").read()
            except OSError:
                continue
            fm = front_matter(text)
            body = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)
            title = fm.get("title", "") or lid
            lines, heading, rows = body.splitlines(), "", []
            for ln in lines:
                if re.match(r"^#{2,3} ", ln):
                    heading = re.sub(r"^#+ ", "", ln).strip()
                pl = _plain(ln)
                if pl:
                    rows.append((pl, heading))
            hay = (title + " " + fm.get("course", "") + " " + " ".join(r[0] for r in rows)).lower()
            if not all(x in hay for x in words):
                continue
            best, score = None, 0
            for pl, hd in rows:
                low = pl.lower()
                n = sum(1 for x in words if x in low)
                n += 2 if q.lower().strip() in low else 0
                n += 1 if hd and any(x in hd.lower() for x in words) else 0
                if n > score:
                    best, score = (pl, hd), n
            in_title = all(x in title.lower() for x in words)
            snippet, sect = ("", "")
            if best:
                pl, sect = best
                i = min((pl.lower().find(x) for x in words if x in pl.lower()), default=0)
                a = max(0, i - 60)
                snippet = ("…" if a else "") + pl[a:a + 170] + ("…" if a + 170 < len(pl) else "")
            href = f"/w/{slug}/lessons/{lid}" + (f"#{_anchor(sect)}" if sect and not in_title else "")
            hits.append({"href": href, "title": title, "course": fm.get("course", ""), "ws": slug, "id": lid,
                         "section": _plain(sect), "snippet": snippet, "rank": (2 if in_title else 0) + score,
                         "mtime": os.path.getmtime(path)})
    hits.sort(key=lambda h: (-h["rank"], -h["mtime"]))
    return hits[:limit]


def hub():
    """Every workspace with its lessons, for the /lessons hub."""
    out = []
    for slug, w in workspaces().items():
        lessons = lessons_meta(w["path"])
        if not lessons:
            continue
        name = next((l["course"] for l in reversed(lessons) if l.get("course")), "") or slug
        out.append({"slug": slug, "name": name, "path": w["path"], "current": current(slug), "count": len(lessons),
                    "last": max(l["date"] for l in lessons), "lessons": lessons})
    out.sort(key=lambda w: max(l["mtime"] for l in w["lessons"]), reverse=True)
    return out


def cut_at_blank(text):
    """Return the prefix of text that ends at the last blank line (complete blocks only)."""
    idx = text.rfind("\n\n")
    if idx < 0:
        return ""
    # do not cut inside an unterminated ::: container
    head = text[: idx + 2]
    opens = len(re.findall(r"^::: ", head, re.M))
    closes = len(re.findall(r"^:::\s*$", head, re.M))
    if opens > closes:
        # back up to before the last unterminated container
        last_open = [m.start() for m in re.finditer(r"^::: ", head, re.M)][-1]
        prev_blank = head.rfind("\n\n", 0, last_open)
        head = head[: prev_blank + 2] if prev_blank >= 0 else ""
    return head


def read_lesson(lid, frm, h, wsp=None):
    p = lesson_path(lid, wsp)
    if not p:
        return {"reset": True, "text": "", "offset": 0, "missing": True}
    with open(p, "rb") as f:
        data = f.read()
    if frm > 0 and frm <= len(data) and hashlib.md5(data[:frm]).hexdigest() == h:
        new = data[frm:].decode("utf-8", "replace")
        complete = cut_at_blank(new) if state().get("streaming") else new
        end = frm + len(complete.encode("utf-8"))
        return {"reset": False, "text": complete, "offset": end, "hash": hashlib.md5(data[:end]).hexdigest()}
    text = data.decode("utf-8", "replace")
    return {"reset": True, "text": text, "offset": len(data), "hash": hashlib.md5(data).hexdigest()}


def host_command(req):
    """Build the agent command for a queue item."""
    agent = state().get("agent", "claude")
    prefix = "$blackboard" if agent == "codex" else "/blackboard"
    k = req.get("kind")
    q = lambda s: '"' + str(s).replace('"', "'") + '"'
    if k == "explain":
        parts = [prefix, "explain", f"L{req.get('line', 0)}", q(req.get("text", ""))]
        if req.get("depth") == "deep":
            parts.append("deep")
        if req.get("parent"):
            parts.append(f"parent={req['parent']}")
        if req.get("grow"):
            parts.append(f"grow={req['grow']}")
        parts.append(f"lesson={req.get('lesson','')}")
        return " ".join(parts)
    if k == "remove":
        return f"{prefix} remove {req.get('id')} lesson={req.get('lesson','')}"
    if k == "quiz":
        return f"{prefix} quiz {q(req.get('topic',''))} {req.get('mode','recall')} lesson={req.get('lesson','')}"
    if k == "predict":
        return f"{prefix} predict {req.get('block')} {req.get('choice')} lesson={req.get('lesson','')}"
    if k == "mcq":
        return f"{prefix} mcq {req.get('item')} {'reset' if req.get('event') == 'reset' else req.get('choice')} lesson={req.get('lesson','')}"
    if k == "grid":
        return f"{prefix} grid"
    return f"{prefix} {json.dumps(req)}"


PENDING = {}
PENDING_LOCK = threading.Lock()
LISTEN_LOCK = threading.Lock()


def headless(script, req, keep=("id",), timeout=180):
    """Run bin/<script> in a thread; record the result under the page's pending id.

    `keep` names the writer's output fields copied into the pending record, so the
    page can paint the result (a score, the new item ids) without refetching."""
    pid = req.get("pending") or f"p{int(time.time()*1000)}"
    wsp = ws(req.get("ws"))
    lesson = req.get("lesson") or current(req.get("ws"))
    path = lesson_path(lesson, wsp)
    with PENDING_LOCK:
        PENDING[pid] = {"status": "writing", "started": time.time()}
    def run():
        try:
            if not path:
                raise RuntimeError("lesson not found")
            r = subprocess.run([sys.executable, os.path.join(BOARD, "..", "bin", script), path, json.dumps(req)],
                               capture_output=True, text=True, timeout=timeout)
            out = json.loads((r.stdout or "{}").strip().splitlines()[-1]) if r.stdout.strip() else {}
            if r.returncode != 0 or "error" in out:
                raise RuntimeError(out.get("error") or (r.stderr or "writer failed")[:300])
            done = {"status": "done"}
            for k in keep:
                if k in out:
                    done[k] = out[k]
            with PENDING_LOCK:
                PENDING[pid] = done
        except Exception as e:
            with PENDING_LOCK:
                PENDING[pid] = {"status": "error", "error": str(e)[:300]}
        # bump rev so SSE clients refresh even if the file did not change
        bump_rev(req.get("ws"))
    threading.Thread(target=run, daemon=True).start()
    return {"queued": True, "wake": "headless", "pending": pid}


WARMED = [0.0]


def warm_local():
    """Keep the local definer model resident so the first Definition click is not the slow one.

    One token, fire and forget, at most every 15 minutes; silent when Ollama is not running."""
    import urllib.request
    if time.time() - WARMED[0] < 900:
        return
    WARMED[0] = time.time()
    def go():
        try:
            base = os.environ.get("BLACKBOARD_OLLAMA", "http://127.0.0.1:11434")
            tags = json.load(urllib.request.urlopen(base + "/api/tags", timeout=1.5)).get("models") or []
            if not tags:
                return
            model = os.environ.get("BLACKBOARD_DEFINE_LOCAL") or tags[0]["name"]
            body = json.dumps({"model": model, "prompt": "hi", "stream": False, "think": False,
                               "keep_alive": "30m", "options": {"num_predict": 1}}).encode()
            r = urllib.request.Request(base + "/api/generate", data=body, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(r, timeout=120).read()
        except Exception:
            pass
    threading.Thread(target=go, daemon=True).start()


DEFINE_CACHE = {}
DEFINE_INFLIGHT = {}
DEFINE_LOCK = threading.Lock()


DEFS_DIR = os.path.join(HOME_DIR, "defs")
PRECOMPUTED = set()
USER_BUSY = threading.Semaphore(1)


def defs_file(path, slug):
    d = os.path.join(DEFS_DIR, slug or "_")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, os.path.basename(path).split("-")[0] + ".json")


def defs_load(path, slug):
    try:
        with open(defs_file(path, slug)) as f:
            return json.load(f)
    except Exception:
        return {}


def defs_save(path, slug, term, out):
    """Definitions survive restarts: a lesson pays for a term once, ever."""
    try:
        d = defs_load(path, slug)
        d[term] = out
        tmp = defs_file(path, slug) + ".tmp"
        with open(tmp, "w") as f:
            json.dump(d, f, ensure_ascii=False)
        os.replace(tmp, defs_file(path, slug))
    except Exception as e:
        sys.stderr.write(f"defs_save: {e}\n")


def run_definer(path, req):
    r = subprocess.run([sys.executable, os.path.join(BOARD, "..", "bin", "define.py"), path, json.dumps(req)],
                       capture_output=True, text=True, timeout=90)
    out = json.loads((r.stdout or "{}").strip().splitlines()[-1]) if r.stdout.strip() else {}
    if r.returncode != 0 or "error" in out or not out.get("text"):
        return {"error": (out.get("error") or (r.stderr or "definer failed").strip())[:200]}
    return out


TERM_RX = [
    re.compile(r"\*\*([^*\n]{2,60})\*\*"),        # **bold term**
    re.compile(r"^\|\s*([^|\n]{2,60}?)\s*\|", re.M),  # first column of a table
    re.compile(r"==([^=\n]{2,60})=="),              # words already asked about
    re.compile(r"`([A-Za-z][^`\n]{1,40})`"),        # inline code
]
TERM_SKIP = re.compile(r"^(exam|note|why|how|what|the|and|for|step \d+|\d+[.)]?|[^A-Za-z]*)$", re.I)
# schedule tables are the other thing built out of "| key |" rows, and their keys are dates
TERM_DATE = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|mon|tue|wed|thu|fri|sat|sun|"
                       r"week|date|due|today|tomorrow|deadline|test|quiz|homework|hw\d?)\b|\d{1,2}\s*[-\u2013]\s*\d{1,2}", re.I)
# emphasis is used for advice too ("**as large as possible**"): those open with a function word
TERM_OPENER = re.compile(r"^(as|if|when|that|which|every|all|each|any|not|never|always|only|both|"
                         r"one|two|three|first|last|next|then|so|but|and|or|do|don't|make|keep|use|"
                         r"read|write|check|note|remember|this|these|those|it|its|you|your)\b", re.I)


def lesson_terms(src, cap=40):
    """Terms a student is likely to select: the lesson's own emphasis, headings and table keys.

    A phrase earns a slot by being a name, not a sentence: table keys always count, and an
    emphasised phrase counts when it opens like a noun and the lesson uses it more than once."""
    seen, out = set(), []
    low = src.lower()
    for i, rx in enumerate(TERM_RX):
        table_key = i == 1
        for m in rx.finditer(src):
            t = re.sub(r"\s+", " ", m.group(1)).strip(" .,:;*_$\\")
            if not t or len(t.split()) > 5 or len(t) > 60:
                continue
            if TERM_SKIP.match(t) or not re.search(r"[A-Za-z]{3}", t):
                continue
            if re.search(r"[$\\{}]", t) or re.search(r"\d\s*,\s*\d", t):   # formulas and value lists
                continue
            if TERM_OPENER.match(t) or TERM_DATE.search(t):
                continue
            if not table_key and low.count(t.lower()) < 2:
                continue
            k = t.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append(t)
            if len(out) >= cap:
                return out
    return out


def local_ready():
    """A local model is installed and Ollama is up."""
    import urllib.request
    try:
        base = os.environ.get("BLACKBOARD_OLLAMA", "http://127.0.0.1:11434")
        return bool(json.load(urllib.request.urlopen(base + "/api/tags", timeout=1.5)).get("models"))
    except Exception:
        return False


def precompute(path, slug):
    """Define the lesson's own terms in the background, so the click is a cache hit.

    Runs one at a time and yields to any click the student makes: a real request takes the
    semaphore, this loop waits for it. Only with a local model: 40 terms through the cloud
    CLI would be minutes of work and quota for definitions nobody asked for."""
    if not local_ready():
        return
    key = (path, os.path.getmtime(path) if os.path.exists(path) else 0)
    if key in PRECOMPUTED:
        return
    PRECOMPUTED.add(key)

    def go():
        try:
            src = open(path).read()
        except Exception:
            return
        disk = defs_load(path, slug)
        for term in lesson_terms(src):
            k = term.lower()
            with DEFINE_LOCK:
                known = (path, k) in DEFINE_CACHE
            if known or k in disk:
                continue
            m = re.search(re.escape(term), src)
            line = src[:m.start()].count("\n") + 1 if m else 1
            with USER_BUSY:                       # a click always goes first
                out = run_definer(path, {"text": term, "line": line})
            if "error" in out:
                continue
            with DEFINE_LOCK:
                DEFINE_CACHE[(path, k)] = out
            defs_save(path, slug, k, out)
            time.sleep(0.2)
    threading.Thread(target=go, daemon=True).start()


def define(req):
    """Synchronous, small and fast: the page waits on this with a popup open.

    Three caches sit in front of the model: memory, the on-disk definitions file for this
    lesson (filled by precompute while the student reads), and one in-flight gate so a hover
    prefetch followed by a click runs the model once. Nothing is written to the lesson file."""
    text = (req.get("text") or "").strip()
    if not text:
        return {"error": "no selection"}
    if len(text.split()) > 5 or len(text) > 80:
        return {"error": "select 1-5 words"}
    slug = req.get("ws") or state().get("slug") or ""
    wsp = ws(req.get("ws"))
    lesson = req.get("lesson") or current(req.get("ws"))
    path = lesson_path(lesson, wsp)
    if not path:
        return {"error": "lesson not found"}

    term = re.sub(r"\s+", " ", text).strip().lower()
    key = (path, term)
    with DEFINE_LOCK:
        hit = DEFINE_CACHE.get(key)
        if hit:
            return dict(hit, cached=True)
        ev = DEFINE_INFLIGHT.get(key)
        mine = ev is None
        if mine:
            DEFINE_INFLIGHT[key] = ev = threading.Event()
    if not mine:
        # the page prefetched this on hover and the answer is still coming:
        # wait for that one instead of running the model twice
        ev.wait(timeout=75)
        with DEFINE_LOCK:
            hit = DEFINE_CACHE.get(key)
        return dict(hit, cached=True) if hit else {"error": "definition timed out"}

    disk = defs_load(path, slug).get(term)
    if disk:
        with DEFINE_LOCK:
            DEFINE_CACHE[key] = disk
            DEFINE_INFLIGHT.pop(key, None)
        ev.set()
        return dict(disk, cached=True)

    out = None
    try:
        with USER_BUSY:                      # precompute waits while a real click is served
            out = run_definer(path, req)
    except subprocess.TimeoutExpired:
        out = {"error": "definition timed out"}
    except Exception as e:
        out = {"error": str(e)[:200]}
    finally:
        with DEFINE_LOCK:
            if out and "error" not in out:
                if len(DEFINE_CACHE) > 600:
                    DEFINE_CACHE.clear()
                DEFINE_CACHE[key] = out       # cache first, then wake the waiters
            DEFINE_INFLIGHT.pop(key, None)
        ev.set()
    if out and "error" not in out:
        defs_save(path, slug, term, out)
    return out


def bump_rev(slug=None):
    try:
        st = state(); now = int(time.time() * 1000); st["rev"] = now
        w = (st.get("workspaces") or {}).get(slug) if slug else None
        if w is not None:
            w["rev"] = now
        with open(STATE, "w") as f:
            json.dump(st, f)
    except Exception:
        pass


def set_fold(req):
    path = lesson_path(req.get("lesson") or current(req.get("ws")), ws(req.get("ws")))
    eid, folded = req.get("id"), bool(req.get("folded"))
    if not path or not eid:
        return {"error": "no lesson/id"}
    s = open(path).read()
    m = re.search(rf"^(::: exp {re.escape(eid)})([^\n]*)$", s, re.M)
    if not m:
        return {"error": "id not found"}
    flags = [f for f in m.group(2).split() if f != "folded"]
    if folded:
        flags.append("folded")
    s = s[:m.start()] + m.group(1) + (" " + " ".join(flags) if flags else "") + s[m.end():]
    open(path, "w").write(s)
    return {"ok": True, "id": eid, "folded": folded}


def remove_exp(req):
    path = lesson_path(req.get("lesson") or current(req.get("ws")), ws(req.get("ws")))
    r = subprocess.run([sys.executable, os.path.join(BOARD, "..", "bin", "exp-remove.py"), path, req.get("id", "")],
                       capture_output=True, text=True)
    return {"ok": r.returncode == 0, "out": (r.stdout or r.stderr).strip()}


# ---------- study chat: one Claude Code session per lesson ----------
# ChatThread, one per lesson, at $WS/reference/chat/<lesson-id>.json:
#   {"session_id": str | None,
#    "messages": [{"role": "user" | "assistant", "text": str, "steps": [{"tool": str, "label": str}], "ts": str}]}
# The file is what the panel shows; the Claude Code session it names is what the model remembers.
CHAT_SYSTEM = os.path.join(BOARD, "chat-system.md")
CHAT_TOOLS = "Read,Grep,Glob,WebSearch,WebFetch,Edit,Write"
TURNS, TURNS_LOCK = {}, threading.Lock()


def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def chat_file(wsp, lid):
    return os.path.join(wsp, "reference", "chat", f"{lid}.json")


def chat_load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"session_id": None, "messages": []}


def chat_save(path, thread):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(thread, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def _here(p, wsp):
    """A path as the student reads it: relative inside the workspace, ~ for home."""
    p, base, home = str(p or ""), wsp.rstrip(os.sep) + os.sep, os.path.expanduser("~") + os.sep
    return p[len(base):] if p.startswith(base) else "~/" + p[len(home):] if p.startswith(home) else p


STEP_LABELS = {
    "Read": lambda i, w: f"Reading {_here(i.get('file_path'), w)}" + (f", pages {i['pages']}" if i.get("pages") else ""),
    "Grep": lambda i, w: f"Searching for “{i.get('pattern', '')}”" + (f" in {_here(i['path'], w)}" if i.get("path") else ""),
    "Glob": lambda i, w: f"Finding files {i.get('pattern', '')}",
    "WebSearch": lambda i, w: f"Searching the web: {i.get('query', '')}",
    "WebFetch": lambda i, w: "Opening " + re.sub(r"^https?://(www\.)?", "", str(i.get("url", "")))[:80],
    "Edit": lambda i, w: f"Editing {_here(i.get('file_path'), w)}",
    "Write": lambda i, w: f"Writing {_here(i.get('file_path'), w)}",
}


class Turn:
    """One running reply: the `claude -p` process and what it has streamed so far."""

    def __init__(self, proc, wsp):
        self.proc, self.wsp = proc, wsp
        self.text, self.steps = "", []
        self.session_id = None
        self.end = None       # ("done", {}) or ("error", {"message"}) once the result line arrives
        self.stopped = False

    def say(self, text):
        self.text += text
        return ("delta", {"text": text})

    def feed(self, line):
        """One stream-json line in, the panel's live events (step, delta) out. The result line only sets .end."""
        kind = line.get("type")
        if kind == "system" and line.get("subtype") == "init":
            self.session_id = line.get("session_id")
        elif kind == "stream_event":
            e = line.get("event") or {}
            block, delta = e.get("content_block") or {}, e.get("delta") or {}
            if e.get("type") == "content_block_start" and block.get("type") == "text" and self.text and not self.text.endswith("\n\n"):
                return [self.say("\n\n")]      # text after a tool call starts a new paragraph
            if e.get("type") == "content_block_delta" and delta.get("type") == "text_delta" and delta.get("text"):
                return [self.say(delta["text"])]
        elif kind == "assistant":
            out = []
            for c in (line.get("message") or {}).get("content") or []:
                if c.get("type") == "tool_use":
                    name = c.get("name", "")
                    label = STEP_LABELS[name](c.get("input") or {}, self.wsp) if name in STEP_LABELS else name
                    self.steps.append({"tool": name, "label": label})
                    out.append(("step", self.steps[-1]))
            return out
        elif kind == "result":
            if line.get("is_error"):
                msg = line.get("result") or "; ".join(map(str, line.get("errors") or [])) or line.get("subtype") or "error"
                self.end = ("error", {"message": str(msg)[:300]})
            else:
                self.end = ("done", {})
        return []


SOURCE_REF = re.compile(r"`([^`\n]+)`|\]\(([^)\s]+)\)|(https?://[^\s)>\]`]+)")
_course_index = {}


def course_root(wsp):
    """The course folder: the one holding learn/, else the workspace itself."""
    return os.path.dirname(wsp.rstrip(os.sep)) if os.path.basename(wsp.rstrip(os.sep)) == "learn" else wsp


def course_files(wsp):
    """Every file under the course folder (depth <= 4), cached for 60 s. A Sources line often names a bare file."""
    root = course_root(wsp)
    hit = _course_index.get(root)
    if hit and time.time() - hit[0] < 60:
        return hit[1]
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [] if dp[len(root):].count(os.sep) >= 4 else [d for d in dns if not d.startswith(".") and d not in ("node_modules", "assets", "chat", "__pycache__")]
        out += [os.path.join(dp, f) for f in fns if not f.startswith(".")]
        if len(out) > 5000:
            break
    _course_index[root] = (time.time(), out)
    return out


def resolve_source(ref, wsp):
    """The URL, or the existing files a Sources reference names (path, glob or bare file name); [] for code like `javac`."""
    if re.match(r"https?://", ref):
        return [ref]
    if not ("/" in ref or "*" in ref or re.search(r"\.[A-Za-z0-9]{1,5}$", ref)):
        return []
    ref = os.path.expanduser(ref)
    for base in [ref] if os.path.isabs(ref) else [os.path.join(wsp, ref), os.path.join(course_root(wsp), ref)]:
        found = sorted(glob.glob(os.path.normpath(base)))
        if found:
            return found[:20]
    if "/" not in ref:
        return sorted(p for p in course_files(wsp) if fnmatch.fnmatch(os.path.basename(p), ref))[:20]
    return []


def lesson_sources(wsp, lpath):
    """(paths and URLs the lesson was written from, the lesson's own sources text), from its `::: sources` block (or `## Sources`) and
    RESOURCES.md. The writer receipt (reference/lesson-writer-NNNN.json) records the model choice, not sources."""
    def read(p):
        try:
            with open(p, encoding="utf-8") as f:
                return f.read()
        except OSError:
            return ""
    text = read(lpath)
    # a `::: sources` drop-down near the top (its file paths may sit in an HTML comment inside it), or an older
    # lesson's trailing `## Sources` section
    m = re.search(r"^::: sources[^\n]*\n(.*?)^:::\s*$", text, re.S | re.M) or re.search(r"^## Sources[^\n]*\n(.*?)(?=^#{1,2} |\Z)", text, re.S | re.M)
    cited = m.group(1).strip() if m else ""
    out = []
    for doc in (cited, read(os.path.join(wsp, "RESOURCES.md"))):
        for r in SOURCE_REF.finditer(doc):
            for p in resolve_source((r.group(1) or r.group(2) or r.group(3)).strip().rstrip(".,;:"), wsp):
                if p not in out:
                    out.append(p)
    return out[:40], cited[:3000]


# files the board may show in its source viewer: documents and images only (no svg or html, which could run script)
SOURCE_VIEW_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".txt", ".md", ".csv", ".tex"}
SOURCE_TRY_EXTS = ("", ".pdf", ".png", ".jpg", ".jpeg", ".md", ".txt", ".pdf.txt", ".docx.txt", ".pptx.txt")
SOURCE_COMMENT = re.compile(r"<!--\s*source:\s*(\S+)(.*?)-->", re.S)


def source_file(ref, wsp):
    """The viewable file a source reference names (`exams2/fa18-kj-e2.pdf`, `review/exam2-2026-1019`,
    `../sources/x.pdf`), looked up in sources/, the workspace, lessons/ and the course folder, in that order.
    None unless its real path sits inside the course folder, outside any hidden folder, with a viewable extension."""
    ref = urllib.parse.unquote(str(ref or "")).strip().split("#")[0].strip().rstrip(".,;:)")
    if not ref or "\0" in ref or os.path.isabs(ref) or ref.startswith("~") or len(ref) > 400:
        return None
    root = os.path.realpath(course_root(wsp))
    for base in (os.path.join(wsp, "sources"), wsp, lessons_dir(wsp), root):
        for ext in SOURCE_TRY_EXTS:
            p = os.path.realpath(os.path.join(base, ref + ext))
            if not p.startswith(root + os.sep) or not os.path.isfile(p):
                continue
            if any(part.startswith(".") for part in os.path.relpath(p, root).split(os.sep)):
                continue
            low = p.lower()
            # text pulled out of a PDF (`x.pdf.txt`, or `x.txt` beside `x.pdf`) opens the PDF itself
            for orig in ((p[:-4],) if low.endswith((".pdf.txt", ".docx.txt", ".pptx.txt")) else (p[:-4] + ".pdf",) if low.endswith(".txt") else ()):
                if orig.lower().endswith(".pdf") and os.path.isfile(orig):
                    return orig
            if any(low.endswith(e) for e in SOURCE_VIEW_EXTS):
                return p
    if "/" not in ref:  # a bare file name (`sp10-lw-s2`): the first match anywhere in the course folder
        for ext in SOURCE_TRY_EXTS:
            hits = sorted(p for p in course_files(wsp) if os.path.basename(p) == ref + ext)
            if hits:
                return source_file(os.path.relpath(hits[0], root), wsp) if not os.path.isabs(os.path.relpath(hits[0], root)) else None
    return None


def source_entry(ref, wsp, slug, page=None):
    """How the board links one source reference: its viewer URL (under /w/<slug>/source/), name and kind."""
    p = source_file(ref, wsp)
    if not p:
        return {"ref": ref, "found": False, "name": os.path.basename(ref.rstrip("/")) or ref}
    root = os.path.realpath(course_root(wsp))
    rel = os.path.relpath(p, root)
    srcdir = os.path.realpath(os.path.join(wsp, "sources"))
    shown = os.path.relpath(p, srcdir) if p.startswith(srcdir + os.sep) else rel
    ext = os.path.splitext(p)[1].lower()
    kind = "pdf" if ext == ".pdf" else "image" if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp") else "text"
    url = (f"/w/{urllib.parse.quote(slug, safe='')}" if slug else "") + "/source/" + urllib.parse.quote(rel)
    return {"ref": ref, "found": True, "path": shown, "name": os.path.basename(p), "kind": kind, "url": url, "page": page}


def cited_files(wsp, lpath, slug):
    """Every file the lesson cites, for the Sources drop-down: links and code spans in its sources block, then the
    `<!-- source: … -->` comment before each problem (with its first page). An official solution file (`…-s2`) brings
    its exam (`…-e2`) along, so the practice exam itself is one click away."""
    try:
        with open(lpath, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return []
    refs = []
    _, cited = lesson_sources(wsp, lpath)
    for r in SOURCE_REF.finditer(cited):
        ref = (r.group(1) or r.group(2) or "").strip()
        if ref and not re.match(r"https?://", ref) and ("/" in ref or re.search(r"\.[A-Za-z0-9]{1,5}$", ref)):
            refs.append((ref, None))
    for m in SOURCE_COMMENT.finditer(text):
        pg = re.search(r"\bpp?\.\s*(\d+)", m.group(2))
        refs.append((m.group(1).rstrip(".,;:"), int(pg.group(1)) if pg else None))
    out, seen = [], set()
    def add(ref, page):
        e = source_entry(ref, wsp, slug, page)
        key = e.get("url") or ("missing:" + ref)
        if key not in seen:
            seen.add(key)
            out.append(e)
    for ref, page in refs:
        exam = re.sub(r"-s(\d)(\.pdf)?$", r"-e\1\2", ref)
        if exam != ref and source_file(exam, wsp):
            add(exam, None)
        add(ref, page)
    return out[:200]


def chat_prompt(lid, lpath, wsp, text, viewing=None):
    """The turn as the model sees it: where the user is on the board, the lesson's sources, then the message."""
    with open(lpath, encoding="utf-8") as f:
        src = f.read()
    title = front_matter(src).get("title") or (re.findall(r"^# (.+)$", src, re.M) or [lid])[0]
    sources, cited = lesson_sources(wsp, lpath)
    ctx = [f"[Board: the user is reading lesson {lid}, “{title}”, at {lpath}.]"]
    if sources:
        ctx.append("Sources for this lesson:\n" + "\n".join(f"- {s}" for s in sources))
    also = [p for p in (os.path.join(wsp, "RESOURCES.md"), os.path.join(wsp, "sources") + os.sep) if os.path.exists(p)]
    if also:
        ctx.append("Also in this workspace: " + ", ".join(also))
    if cited:
        ctx.append("The lesson's own Sources section:\n" + cited)
    if viewing:
        ctx.append(f"[Viewing: the user has {viewing} open beside this chat. A question like \"this problem\" is about that file: read it first.]")
    return "\n\n".join(ctx) + "\n\n---\n\n" + text


def chat_allowed(wsp, sources):
    """What the session may do without a prompt: read the workspace, TEMPLATES.md and the exact files the lesson
    cites, search the web, and fetch only the sites the lesson cites. Anything else would prompt, and
    --permission-prompts none denies it. Edit and Write are approved by acceptEdits inside the workspace only."""
    rules = [f"Read(/{os.path.realpath(wsp)}/**)", f"Read(/{os.path.join(ROOT, 'TEMPLATES.md')})", "WebSearch"]
    for s in sources:
        if s.startswith(("http://", "https://")):
            host = urllib.parse.urlsplit(s).hostname
            rule = host and f"WebFetch(domain:{host})"
        else:
            p = os.path.realpath(s)
            rule = f"Read(/{p}/**)" if os.path.isdir(p) else f"Read(/{p})"
        if rule and rule not in rules:
            rules.append(rule)
    return ",".join(rules)


def chat_command(session_id, resume, allowed):
    """`claude -p` for one turn. The prompt goes in on stdin, so no flag can swallow it."""
    with open(CHAT_SYSTEM, encoding="utf-8") as f:
        system = f.read().replace("{templates}", os.path.join(ROOT, "TEMPLATES.md"))
    return ["claude", "-p", "--output-format", "stream-json", "--verbose", "--include-partial-messages",
            "--model", os.environ.get("BLACKBOARD_CHAT_MODEL", "opus"), "--effort", "medium",
            "--tools", CHAT_TOOLS, "--allowedTools", allowed,
            "--permission-mode", "acceptEdits", "--permission-prompts", "none",
            # the user's own CLAUDE.md, hooks and MCP servers belong to their coding sessions, not this panel
            "--setting-sources", "project,local", "--strict-mcp-config",
            "--append-system-prompt", system] + (["--resume", session_id] if resume else ["--session-id", session_id])


def chat_finish(key, turn, stderr, code):
    """Save the reply with whatever arrived and return how the turn ended: ("done", {...}) or ("error", {...})."""
    thread = chat_load(key)
    if turn.session_id:
        thread["session_id"] = turn.session_id
    end, text = turn.end, turn.text.strip()
    if turn.stopped:
        end, text = ("done", {"stopped": True}), text + "\n\n_Stopped._"
    elif end is None:
        msg = (stderr.strip().splitlines() or [f"claude exited with code {code}"])[-1][:300]
        if "No conversation found" in stderr:
            thread["session_id"] = None
            msg = "The earlier session could not be resumed. Send again to start a fresh one."
        end = ("error", {"message": msg})
    if end[0] == "error":
        text += f"\n\n_Error: {end[1]['message']}_"
    thread["messages"].append({"role": "assistant", "text": text.strip(), "steps": turn.steps, "ts": utc_now()})
    chat_save(key, thread)
    with TURNS_LOCK:
        TURNS.pop(key, None)
    return end


def stop_turn(turn):
    turn.stopped = True
    for sig, wait in ((signal.SIGTERM, 3), (signal.SIGKILL, 0)):
        if turn.proc.poll() is not None:
            return
        try:
            os.killpg(turn.proc.pid, sig)
            turn.proc.wait(timeout=wait or None)
        except (OSError, subprocess.TimeoutExpired):
            pass


def wake(req):
    st = state()
    k = req.get("kind")
    if k == "explain":
        return headless("explain.py", req, keep=("id",))
    if k == "quiz":
        req = dict(req, op="generate")
        return headless("quiz.py", req, keep=("ids", "n"))
    if k == "grade":
        req = dict(req, op="grade")
        return headless("quiz.py", req, keep=("item", "score", "rationale", "missing"), timeout=120)
    if k == "fold":
        return set_fold(req)
    if k == "remove":
        return remove_exp(req)
    if k in ("predict", "mcq"):
        # click logging only; no agent wake
        return {"queued": True, "wake": "none"}
    cmd = host_command(req)
    layout, agent = st.get("layout", "tab"), st.get("agent", "claude")
    if layout == "cmux" and st.get("cli_surface"):
        try:
            subprocess.run(["cmux", "send", "--surface", st["cli_surface"], cmd + "\n"], check=False, timeout=5)
            return {"queued": True, "wake": "cmux", "command": cmd}
        except Exception as e:
            return {"queued": True, "wake": "cmux-failed", "command": cmd, "error": str(e)}
    if agent == "codex":
        return {"queued": True, "fallback": "paste", "command": cmd}
    return {"queued": True, "wake": "waiter", "command": cmd}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith("text") or ctype == "application/json" else ""))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def foreign(self):
        """A request sent by some other web page. The chat can read files and edit lessons, so only the board's own
        pages (and local tools, which send no Origin) may reach it."""
        origin = self.headers.get("Origin")
        return bool(origin) and origin not in (f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}")

    def page(self, mode, lid, slug=""):
        warm_local()
        try:
            p = lesson_path(lid or current(slug or None), ws(slug or None))
            if p:
                precompute(p, slug or state().get("slug") or "")
        except Exception as e:
            sys.stderr.write(f"precompute: {e}\n")
        with open(TMPL) as f:
            html = f.read()
        html = html.replace("__MODE__", mode).replace("__LESSON__", lid or "").replace("__WS__", slug or "")
        self.send(200, html, "text/html")

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        path = u.path
        st = state()
        # /w/<slug>/... pins a page to one workspace; the same routes without the prefix use the last rendered one
        slug = ""
        m = re.match(r"^/w/([a-z0-9-]+)(/.*)?$", path)
        if m:
            slug, path = m.group(1), (m.group(2) or "/")
            if slug not in workspaces() and slug not in (state().get("workspaces") or {}):
                return self.send(404, "no such workspace", "text/plain")
        # short links: /m -> math1552's lesson grid, /m/3 -> its lesson 0003 (any unique slug prefix)
        m = re.match(r"^/([a-z]+[0-9]*)(?:/(\d{1,4}))?/?$", path)
        if not slug and m and m.group(1) not in ("lessons", "health", "events", "api", "assets", "lib", "anim", "w"):
            hits = [s for s in workspaces() if s.startswith(m.group(1))]
            if len(hits) == 1:
                dest = f"/w/{hits[0]}/lessons" + (f"/{int(m.group(2)):04d}" if m.group(2) else "")
                self.send_response(302)
                self.send_header("Location", dest)
                self.end_headers()
                return
        slug = slug or qs.get("ws", [""])[0]
        if path == "/api/lesson-video" and slug and slug not in workspaces() and slug not in (st.get("workspaces") or {}):
            return self.send(200, {"available": False, "error": "Workspace not found."})
        wsp = ws(slug)
        if path == "/health":
            return self.send(200, "ok", "text/plain")
        if path == "/":
            # bare address = the all-lessons menu; /w/<slug>/ still follows that course's current lesson
            return self.page("lesson", "", slug) if slug else self.page("grid", "", "")
        if path == "/lessons":
            return self.page("grid", "", slug)
        m = re.match(r"^/lessons/(\d{4})$", path)
        if m:
            return self.page("lesson", m.group(1), slug)
        if path == "/api/pending":
            with PENDING_LOCK:
                return self.send(200, PENDING)
        if path == "/api/state":
            w = (st.get("workspaces") or {}).get(slug, {}) if slug else st
            page_files = (TMPL, os.path.join(BOARD, "fig.js"), os.path.join(BOARD, "lesson-video.js"),
                          os.path.join(BOARD, "lesson-video.css"))
            body = {"ws": wsp, "slug": slug or slug_of(wsp), "current": current(slug), "agent": w.get("agent", st.get("agent", "claude")),
                    "page_version": int(max(os.path.getmtime(p) for p in page_files if os.path.isfile(p))),
                    "layout": w.get("layout", st.get("layout", "tab")), "streaming": bool(w.get("streaming", st.get("streaming"))),
                    "lessons": lessons_meta(wsp), "brainstorm": w.get("brainstorm"),
                    "end_card": {"image": bool(end_card_path()), "key": slug_of(wsp) if wsp else ""}}
            if qs.get("all"):
                body["workspaces"] = hub()
            return self.send(200, body)
        if path == "/api/search":
            return self.send(200, search(qs.get("q", [""])[0], int(qs.get("limit", ["30"])[0] or 30)))
        if path == "/api/answers":
            return self.send(200, answers(qs.get("id", [current(slug)])[0], wsp))
        if path == "/api/lesson":
            lid = qs.get("id", [current(slug)])[0]
            frm = int(qs.get("from", ["0"])[0] or 0)
            h = qs.get("hash", [""])[0]
            return self.send(200, read_lesson(lid, frm, h, wsp))
        if path == "/api/lesson-video":
            return self.send(200, lesson_video(qs.get("id", [current(slug)])[0], wsp, slug))
        if path == "/events":
            return self.events(qs.get("id", [current(slug)])[0], slug)
        if path == "/api/chat":
            if self.foreign():
                return self.send(403, {"error": "the chat answers only the board"})
            lid = qs.get("lesson", [""])[0]
            if not re.fullmatch(r"\d{4}", lid):
                return self.send(400, {"error": "lesson must be NNNN"})
            key = chat_file(wsp, lid)
            thread = chat_load(key)
            with TURNS_LOCK:
                turn = TURNS.get(key)
            thread.update(running=bool(turn), pending={"text": turn.text, "steps": turn.steps} if turn else None)
            return self.send(200, thread)
        if path == "/api/sources":
            p = lesson_path(qs.get("id", [current(slug)])[0], wsp)
            return self.send(200, {"files": cited_files(wsp, p, slug) if p else []})
        if path == "/api/source-check":
            if self.foreign():
                return self.send(403, {"error": "only the board may check sources"})
            return self.send(200, {r: source_entry(r, wsp, slug) for r in qs.get("p", [])[:30]})
        if path.startswith("/source/"):
            # the source viewer: a file the lesson cites, confined to the course folder (see source_file)
            if self.foreign():
                return self.send(403, "only the board may open sources", "text/plain")
            p = source_file(urllib.parse.unquote(path[len("/source/"):]), wsp)
            return self.static(p, cors=False) if p else self.send(404, "not found on this Mac", "text/plain")
        if path.startswith("/assets/"):
            assets = os.path.realpath(os.path.join(lessons_dir(wsp), "assets"))
            if not assets.startswith(os.path.realpath(wsp) + os.sep):
                return self.send(404, "missing", "text/plain")
            return self.static(os.path.join(assets, os.path.basename(path)), assets)
        if path.startswith("/lib/"):
            lib = {"rough.js": os.path.join(ROOT, "node_modules", "roughjs", "bundled", "rough.js"), "fig.js": os.path.join(BOARD, "fig.js"),
                   "lesson-video.js": os.path.join(BOARD, "lesson-video.js"), "lesson-video.css": os.path.join(BOARD, "lesson-video.css"),
                   "slate.jpg": next((x for x in (os.path.join(BOARD, "slate-custom.jpg"), os.path.join(BOARD, "slate.jpg")) if os.path.exists(x)), "")}.get(os.path.basename(path))
            if lib: return self.static(lib)
        if path in ("/favicon.svg", "/favicon.ico"):
            return self.static(os.path.join(BOARD, "favicon.svg"))
        if path == "/apple-touch-icon.png":
            return self.static(os.path.join(BOARD, "app-icon.png"))
        if path == "/end-card.jpg":
            p = end_card_path()
            return self.static(p) if p else self.send(404, "no end card", "text/plain")
        if path.startswith("/anim/"):
            rel = os.path.normpath(path[len("/anim/"):])
            if rel.startswith(".."):
                return self.send(404, "no", "text/plain")
            return self.static(os.path.join(BOARD, "anim", rel))
        return self.send(404, "not found", "text/plain")

    def do_HEAD(self):
        if re.sub(r"^/w/[^/]+(?=/|$)", "", urllib.parse.urlparse(self.path).path) == "/events":
            return self.send(405, "", "text/plain")
        return self.do_GET()

    def static(self, p, confined_to=None, cors=True):
        if confined_to and not os.path.realpath(p).startswith(os.path.realpath(confined_to) + os.sep):
            return self.send(404, "missing", "text/plain")
        if not os.path.isfile(p):
            return self.send(404, "missing", "text/plain")
        ext = os.path.splitext(p)[1].lower()
        ctype = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".svg": "image/svg+xml",
                 ".mp4": "video/mp4", ".webp": "image/webp", ".txt": "text/plain", ".md": "text/plain",
                 ".js": "text/javascript", ".css": "text/css", ".pdf": "application/pdf", ".csv": "text/plain",
                 ".tex": "text/plain"}.get(ext, "application/octet-stream")
        try:
            with open(p, "rb") as f:
                size = os.fstat(f.fileno()).st_size
                start, end, code = 0, size - 1, 200
                range_header = self.headers.get("Range")
                if range_header is not None:
                    match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
                    if not match or not any(match.groups()):
                        code = 416
                    else:
                        first, last = match.groups()
                        if len(first) > 32 or len(last) > 32:
                            code = 416
                        elif first:
                            start = int(first)
                            end = int(last) if last else size - 1
                            if start >= size or end < start:
                                code = 416
                            else:
                                end = min(end, size - 1)
                        else:
                            suffix = int(last)
                            if suffix == 0 or size == 0:
                                code = 416
                            else:
                                start = max(0, size - suffix)
                                end = size - 1
                        if code != 416:
                            code = 206
                self.send_response(code)
                self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith("text") else ""))
                self.send_header("Accept-Ranges", "bytes")
                if cors:
                    self.send_header("Access-Control-Allow-Origin", "*")
                else:
                    self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "no-store")
                if code == 416:
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.send_header("Content-Length", "0")
                else:
                    if code == 206:
                        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                    self.send_header("Content-Length", str(end - start + 1))
                self.end_headers()
                if self.command == "HEAD" or code == 416:
                    return
                f.seek(start)
                remaining = end - start + 1
                while remaining:
                    chunk = f.read(min(64 * 1024, remaining))
                    if not chunk:
                        return
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            return
        except OSError:
            return

    def events(self, lid, slug=""):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        last = None
        last_state = None
        try:
            while True:
                st = state()
                w = (st.get("workspaces") or {}).get(slug, {}) if slug else st
                cur = current(slug)
                p = lesson_path(lid or cur, ws(slug))
                sig = None
                if p and os.path.exists(p):
                    s = os.stat(p)
                    sig = (s.st_mtime_ns, s.st_size)
                bs = w.get("brainstorm") or {}
                ssig = (cur, w.get("streaming", st.get("streaming")), w.get("rev", st.get("rev")), bs.get("rev"))
                if sig != last or ssig != last_state:
                    last, last_state = sig, ssig
                    payload = json.dumps({"current": cur, "streaming": bool(w.get("streaming", st.get("streaming"))), "size": sig[1] if sig else 0, "brainstorm": bs or None})
                    self.wfile.write(f"event: change\ndata: {payload}\n\n".encode())
                    self.wfile.flush()
                else:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                time.sleep(0.3)
        except (BrokenPipeError, ConnectionResetError, OSError):
            return

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.end_headers()

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        n = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(n) if n else b""
        if u.path == "/ask":
            try:
                req = json.loads(raw.decode() or "{}")
            except Exception:
                return self.send(400, {"error": "bad json"})
            req["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            req.setdefault("lesson", current(req.get("ws")))
            # dedupe: same explain text+block+lesson within 120 s is a repeat click, not a new question
            if req.get("kind") == "explain":
                try:
                    key = (req.get("text"), req.get("block"), req.get("lesson"), req.get("depth"), req.get("parent"), req.get("grow"))
                    now = time.time()
                    for line in reversed(open(QUEUE).read().splitlines()[-20:]):
                        r = json.loads(line)
                        if r.get("kind") == "explain" and (r.get("text"), r.get("block"), r.get("lesson"), r.get("depth"), r.get("parent"), r.get("grow")) == key \
                           and now - calendar.timegm(time.strptime(r.get("ts", "1970-01-01T00:00:00Z"), "%Y-%m-%dT%H:%M:%SZ")) < 120:
                            return self.send(200, {"queued": False, "duplicate": True})
                except Exception as e:
                    sys.stderr.write(f"dedupe error: {e}\n")
            with open(QUEUE, "a") as f:
                f.write(json.dumps(req, ensure_ascii=False) + "\n")
            if req.get("kind") == "mcq":
                log_mcq(req)
            return self.send(200, wake(req))
        if u.path == "/open":
            # in-app browser panes (Claude desktop) turn window.open into same-tab navigation, so the page asks
            # the bridge to open its own lesson links in the default browser instead; nothing but board URLs
            try:
                urls = json.loads(raw.decode() or "{}").get("urls") or []
            except Exception:
                return self.send(400, {"error": "bad json"})
            ok = [x for x in urls[:60] if re.match(rf"^http://(localhost|127\.0\.0\.1):{PORT}/w/[a-z0-9-]+/lessons/\d{{4}}$", str(x))]
            for x in ok:
                subprocess.Popen(["open", x]) if sys.platform == "darwin" else subprocess.Popen(["xdg-open", x])
                time.sleep(0.15)
            return self.send(200, {"opened": len(ok)})
        if u.path == "/define":
            try:
                req = json.loads(raw.decode() or "{}")
            except Exception:
                return self.send(400, {"error": "bad json"})
            return self.send(200, define(req))
        if u.path == "/api/listen":
            # The mic lives on the bridge, not in the page: bin/listen.sh uses on-device
            # Apple Speech, so it works in every host (cmux WKWebView, Claude app, Codex
            # app) rather than only in Chrome, which is all the Web Speech API would give.
            if not LISTEN_LOCK.acquire(blocking=False):
                return self.send(200, {"error": "already listening"})
            try:
                sh = os.path.join(BOARD, "..", "bin", "listen.sh")
                r = subprocess.run([sh], capture_output=True, text=True, timeout=90)
                text = (r.stdout or "").strip()
                if r.returncode != 0 or not text:
                    return self.send(200, {"error": (r.stderr or "no transcript").strip()[:200]})
                return self.send(200, {"text": text})
            except subprocess.TimeoutExpired:
                return self.send(200, {"error": "listening timed out"})
            except Exception as e:
                return self.send(200, {"error": str(e)[:200]})
            finally:
                LISTEN_LOCK.release()
        if u.path == "/render":
            # render.sh pokes this after updating state.json; bump rev so SSE clients reload
            bump_rev(urllib.parse.parse_qs(u.query).get("ws", [None])[0])
            return self.send(200, {"ok": True})
        if u.path in ("/chat", "/chat/stop", "/chat/new"):
            if self.foreign():
                return self.send(403, {"error": "the chat answers only the board"})
            try:
                req = json.loads(raw.decode() or "{}")
            except Exception:
                return self.send(400, {"error": "bad json"})
            lid, wsp = str(req.get("lesson") or ""), ws(req.get("ws"))
            if not re.fullmatch(r"\d{4}", lid) or not lesson_path(lid, wsp):
                return self.send(404, {"error": "no such lesson"})
            key = chat_file(wsp, lid)
            if u.path == "/chat":
                return self.chat(req, lid, wsp, key)
            with TURNS_LOCK:
                turn = TURNS.get(key)
            if u.path == "/chat/stop":
                if turn:
                    stop_turn(turn)
                return self.send(200, {"stopped": bool(turn)})
            if turn:
                return self.send(409, {"error": "a reply is still running"})
            if os.path.exists(key):
                os.replace(key, key[:-len(".json")] + "-" + time.strftime("%Y%m%d-%H%M%S") + ".json")
            return self.send(200, {"ok": True})
        return self.send(404, {"error": "no"})

    def chat(self, req, lid, wsp, key):
        """POST /chat: run one turn of this lesson's session and stream it back as SSE on this response.
        A page that goes away mid-reply does not stop it: the reply still finishes and is saved."""
        text, selection = (req.get("text") or "").strip(), (req.get("selection") or "").strip()
        if not text and not selection:
            return self.send(400, {"error": "empty message"})
        if not shutil.which("claude"):
            return self.send(503, {"error": "Claude Code (claude) is not installed"})
        said = ("> " + selection.replace("\n", "\n> ") + "\n\n" if selection else "") + text
        viewing = re.sub(r"[\x00-\x1f\[\]]", " ", str(req.get("viewing") or ""))[:300].strip()
        prompt = chat_prompt(lid, lesson_path(lid, wsp), wsp, said, viewing)
        with TURNS_LOCK:
            if key in TURNS:
                return self.send(409, {"error": "a reply is already running for this lesson"})
            thread = chat_load(key)
            thread["messages"].append({"role": "user", "text": said, "steps": [], "ts": utc_now()})
            chat_save(key, thread)
            sid = thread.get("session_id") or str(uuid.uuid4())
            err = tempfile.TemporaryFile(mode="w+")
            env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDECODE")}
            allowed = chat_allowed(wsp, lesson_sources(wsp, lesson_path(lid, wsp))[0])
            proc = subprocess.Popen(chat_command(sid, bool(thread.get("session_id")), allowed), cwd=wsp, env=env,
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err, text=True, bufsize=1,
                                    start_new_session=True)
            turn = TURNS[key] = Turn(proc, wsp)
        try:
            proc.stdin.write(prompt)
            proc.stdin.close()
        except OSError:
            pass
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        live = [True]

        def emit(event, data):
            if not live[0]:
                return
            try:
                self.wfile.write(f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode())
                self.wfile.flush()
            except OSError:
                live[0] = False
        for raw in proc.stdout:
            try:
                line = json.loads(raw)
            except ValueError:
                continue
            for event, data in turn.feed(line):
                emit(event, data)
        proc.wait()
        err.seek(0)
        emit(*chat_finish(key, turn, err.read(), proc.returncode))
        err.close()


def main():
    warm_local()
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    srv.daemon_threads = True
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
