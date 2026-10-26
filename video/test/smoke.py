#!/usr/bin/env python3
"""End-to-end smoke test of the video runtime on the generic sample, with no paid API call.

A local mock of the ElevenLabs endpoint returns short tone MP3s with an even character alignment, so the real
tts.py request, cache, quota-stop and resume code runs. Then: SPLIT checks, stills, a resumable chunked render,
finish.sh (H.264/AAC/faststart/loudness/SRT) and render.sh locking. Failures are injected at the real boundaries:
a process killed at a cue's metadata write, ffmpeg / node replaced on PATH by scripts that fail or exit early,
a render killed outright, concurrent renders.

  python3 video/test/smoke.py [--keep] [--quick]
Needs node, npm (or VIDEO_NODE_MODULES=<dir with playwright>), ffmpeg/ffprobe, a Playwright Chromium, network
for the Google Fonts / KaTeX CDN. --quick skips the full render, finish.sh and render.sh.
"""
import argparse, base64, fcntl, http.server, json, os, shutil, signal, struct, subprocess, sys, tempfile, threading, time, types

VIDEO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME = ["engine.js", "style.css", "index.html", "capture.mjs", "tts.py", "finish.sh", "render.sh", "package.json"]
FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""), flush=True)
    if not ok:
        FAILS.append(name)
    return ok


def environ(env=None):
    e = dict(os.environ)
    e.pop("ELEVENLABS_API_KEY", None)
    e["BLACKBOARD_TTS_ENGINE"] = "elevenlabs"   # the mock exercises the ElevenLabs path, never the local Kokoro
    e.update(env or {})
    return e


def run(cmd, cwd, env=None, timeout=900):
    """A hung command is a failure (returncode None), not a hung test: its whole process group is killed."""
    t = time.time()
    p = subprocess.Popen(cmd, cwd=cwd, env=environ(env), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         start_new_session=True)
    try:
        out, err = p.communicate(timeout=timeout)
        code = p.returncode
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        out, err = p.communicate()
        code, err = None, err + f"\nTIMEOUT: still running after {timeout}s"
    return types.SimpleNamespace(returncode=code, stdout=out, stderr=err, out=out + err, secs=time.time() - t)


def shim(root, name, body, path=None):
    """A directory holding one executable <name> script, put first on PATH (default os.environ's); returns that PATH."""
    d = os.path.join(root, f"shim-{name}-{abs(hash(body))}")
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, name)
    open(f, "w").write("#!/bin/sh\n" + body + "\n")
    os.chmod(f, 0o755)
    return d + os.pathsep + (path or os.environ["PATH"])


def hold(path):
    """Take the exclusive kernel lock render.sh uses on <path>; close the returned file to release it."""
    f = open(path, "a")
    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return f


def free(path):
    try:
        hold(path).close()
        return True
    except OSError:
        return False


def finished(p, secs):
    """Exit code of a Popen started with start_new_session, or -1 after killing its group when it overruns."""
    try:
        return p.wait(timeout=secs)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        p.wait()
        return -1


def gone(pgid, secs=10):
    """True once no live (non-zombie) process is left in the group."""
    deadline = time.time() + secs
    while time.time() < deadline:
        ps = subprocess.run(["ps", "-A", "-o", "pgid=,stat="], capture_output=True, text=True).stdout.split("\n")
        if not any(l.split()[0] == str(pgid) and not l.split()[1].startswith("Z") for l in ps if l.strip()):
            return True
        time.sleep(0.05)
    return False


# ---------- mock ElevenLabs ----------
class Mock:
    def __init__(self):
        self.requests, self.fail_after, self.lock = [], None, threading.Lock()
        mock = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                with mock.lock:
                    n = len(mock.requests)
                    mock.requests.append({"path": self.path, "key": self.headers.get("xi-api-key"), "body": body})
                if mock.fail_after is not None and n >= mock.fail_after:
                    out = json.dumps({"detail": {"status": "quota_exceeded", "message": "This request exceeds your quota."}}).encode()
                    self.send_response(401)
                else:
                    out = json.dumps(tone(body["text"])).encode()
                    self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(out)))
                self.end_headers()
                self.wfile.write(out)

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"


def tone(text):
    d = max(0.8, 0.055 * len(text))
    with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
        subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"sine=frequency=330:duration={d:.3f}:sample_rate=44100",
                               "-af", "volume=0.3", "-c:a", "libmp3lame", "-b:a", "192k", f.name])
        audio = open(f.name, "rb").read()
    n = len(text)
    st = [round(d * 0.95 * i / n, 3) for i in range(n)]
    return {"audio_base64": base64.b64encode(audio).decode(),
            "alignment": {"characters": list(text), "character_start_times_seconds": st,
                          "character_end_times_seconds": [round(x + d * 0.95 / n, 3) for x in st]}}


def boxes(path):
    out, f = [], open(path, "rb")
    while True:
        h = f.read(8)
        if len(h) < 8:
            return out
        size, typ = struct.unpack(">I4s", h)
        if size == 1:
            size = struct.unpack(">Q", f.read(8))[0] - 8
        out.append(typ.decode())
        f.seek(size - 8, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="video-smoke-")
    P = os.path.join(tmp, "project")
    os.makedirs(P)
    for f in RUNTIME:
        shutil.copy2(os.path.join(VIDEO, f), P)
    for f in ("script.json", "SPLIT.json"):
        shutil.copy2(os.path.join(VIDEO, "sample", f), P)
    shutil.copytree(os.path.join(VIDEO, "sample", "scenes"), os.path.join(P, "scenes"))
    os.makedirs(os.path.join(P, "assets"))   # local visual inputs are fingerprinted with the scenes
    asset = os.path.join(P, "assets", "mark.svg")
    open(asset, "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><circle cx="5" cy="5" r="4"/></svg>\n')
    print("project:", P)

    # ---- syntax ----
    for f in ["engine.js", "capture.mjs"] + [f"scenes/{x}" for x in os.listdir(os.path.join(P, "scenes"))]:
        r = run(["node", "--check", f], P)
        check(f"node --check {f}", r.returncode == 0, r.out)
    for f in ["finish.sh", "render.sh"]:
        r = run(["bash", "-n", f], P)
        check(f"bash -n {f}", r.returncode == 0, r.out)
    r = run([sys.executable, "-m", "py_compile", "tts.py"], P)
    check("py_compile tts.py", r.returncode == 0, r.out)

    # ---- tts: no key, quota stop, resume, cache ----
    r = run([sys.executable, "tts.py", "--check"], P)
    check("tts --check reports 7 missing cues, exit 1", r.returncode == 1 and r.out.count("missing ") == 7, r.out)
    r = run([sys.executable, "tts.py"], P)
    check("tts without ELEVENLABS_API_KEY stops with exit 2", r.returncode == 2 and "ELEVENLABS_API_KEY is not set" in r.out, r.out)
    m = Mock()
    env = {"ELEVENLABS_API_KEY": "test-key", "ELEVENLABS_API_BASE": m.base}
    m.fail_after = 2
    r = run([sys.executable, "tts.py", "--workers", "1"], P, env)
    check("quota refusal stops with exit 3 and a resume hint", r.returncode == 3 and "TTS_QUOTA_OR_AUTH" in r.out
          and "quota_exceeded" in r.out and "2 of 7 cues are cached" in r.out, r.out)
    check("no timeline written after a quota stop", not os.path.exists(os.path.join(P, "timeline.json")))
    m.fail_after, m.requests = None, []
    r = run([sys.executable, "tts.py"], P, env)
    check("resume narrates only the 5 missing cues", r.returncode == 0 and len(m.requests) == 5, f"{len(m.requests)} requests\n{r.out}")
    q = m.requests[0]
    check("request carries model, voice and voice settings", q["key"] == "test-key"
          and q["path"].startswith("/v1/text-to-speech/XrExE9yKIg1WjnnlVkGX/with-timestamps?output_format=mp3_44100_192")
          and q["body"]["model_id"] == "eleven_v4"
          and q["body"]["voice_settings"] == {"stability": 0.55, "similarity_boost": 0.8, "style": 0.15, "speed": 0.97}, json.dumps(q)[:300])
    tl = json.load(open(os.path.join(P, "timeline.json")))
    js = open(os.path.join(P, "timeline.js")).read()
    check("timeline.js mirrors timeline.json", js.startswith("window.TIMELINE=") and json.loads(js[len("window.TIMELINE="):].rstrip().rstrip(";")) == tl)
    think = tl["scenes"][3]["cues"]["think"]
    check("timeline shape (4 scenes, 30 fps, pause cue)", len(tl["scenes"]) == 4 and tl["fps"] == 30 and think.get("pause") is True
          and abs(think["e"] - think["s"] - 2) < 1e-9 and all(s["subs"] for s in tl["scenes"]), json.dumps(tl)[:300])
    m.requests = []
    r = run([sys.executable, "tts.py"], P, env)
    check("rerun is fully cached (0 requests)", r.returncode == 0 and not m.requests, r.out)
    # changing one cue's text re-narrates exactly that cue
    sp = os.path.join(P, "script.json")
    orig_script = open(sp).read()
    s = json.loads(orig_script)
    s["scenes"][2]["cues"][2]["say"] = "So the sum is four, three."
    open(sp, "w").write(json.dumps(s))
    r = run([sys.executable, "tts.py"], P, env)
    check("edited cue text re-narrates that cue only", r.returncode == 0 and len(m.requests) == 1 and m.requests[0]["body"]["text"].startswith("So the"), r.out)
    open(sp, "w").write(orig_script)
    run([sys.executable, "tts.py"], P, env)   # back to the original text (one more request)
    m.requests = []
    # settings are part of the cache key: a different model must miss every cue
    r = run([sys.executable, "tts.py", "--check"], P, dict(env, ELEVENLABS_MODEL="eleven_other"))
    check("different model invalidates the cache", r.returncode == 1 and r.out.count("missing ") == 7, r.out)
    # legacy cache entries (sha1 of model+voice+text) are reused, not re-bought
    import hashlib
    meta = os.path.join(P, "audio", "s00_a.mp3.json")
    d = json.load(open(meta))
    d["hash"] = hashlib.sha1(("eleven_v4" + "XrExE9yKIg1WjnnlVkGX" + d["text"]).encode()).hexdigest()
    json.dump(d, open(meta, "w"))
    r = run([sys.executable, "tts.py"], P, env)
    check("legacy cache entry reused and upgraded", r.returncode == 0 and not m.requests and json.load(open(meta))["hash"].startswith("v2:"), r.out)
    r = run([sys.executable, "tts.py", "--verify"], P)
    check("tts --verify accepts the files of a complete run", r.returncode == 0 and "TTS_OK" in r.out, r.out)

    # killed after an edited cue's new audio replaced the old, before its metadata: the cue must not count as
    # cached under its old text, and the next run narrates it again
    cue = f"{s['scenes'][2]['id']}_{s['scenes'][2]['cues'][2]['id']}.mp3"
    open(sp, "w").write(json.dumps(s))
    crash = ("import os, runpy, sys\nreal = os.replace\n"
             "def replace(a, b):\n    if b.endswith('.mp3.json'):\n        os._exit(99)\n    real(a, b)\n"
             "os.replace = replace\nsys.argv = ['tts.py']\nrunpy.run_path('tts.py', run_name='__main__')\n")
    r = run([sys.executable, "-c", crash], P, env)
    killed = r.returncode == 99
    open(sp, "w").write(orig_script)
    r = run([sys.executable, "tts.py", "--check"], P)
    check("killed between a cue's audio and metadata: the cue is missing, not cached", killed and r.returncode == 1
          and r.out.count("missing ") == 1 and f"missing {cue}" in r.out, f"killed={killed}\n{r.out}")
    m.requests = []
    r = run([sys.executable, "tts.py"], P, env)
    check("the next run narrates that cue again", r.returncode == 0 and len(m.requests) == 1
          and m.requests[0]["body"]["text"] == json.loads(orig_script)["scenes"][2]["cues"][2]["say"], r.out)

    # Narration assembly failure preserves the old files, but the changed script must block their reuse.
    published = ("timeline.json", "timeline.js", "narration.wav")
    before = {f: open(os.path.join(P, f), "rb").read() for f in published}
    open(sp, "w").write(json.dumps(s))
    r = run([sys.executable, "tts.py"], P, dict(env, PATH=shim(tmp, "ffmpeg", "exit 1")))
    after = {f: open(os.path.join(P, f), "rb").read() for f in published}
    v = run([sys.executable, "tts.py", "--verify"], P)
    check("failed narration assembly preserves old files but blocks reuse for the changed script", r.returncode not in (0, None)
          and after == before and v.returncode != 0 and "script.json" in v.out, f"tts exit {r.returncode}, changed: {[f for f in published if after[f] != before[f]]}\n{v.out}")
    open(sp, "w").write(orig_script)
    r = run([sys.executable, "tts.py"], P, env)
    check("tts with the restored script", r.returncode == 0, r.out)
    tl = json.load(open(os.path.join(P, "timeline.json")))
    m.srv.shutdown()

    # ---- node deps ----
    nm = os.environ.get("VIDEO_NODE_MODULES")
    if nm:
        os.symlink(nm, os.path.join(P, "node_modules"))
    else:
        r = run(["npm", "install", "--no-audit", "--no-fund", "--silent"], P, timeout=600)
        if not check("npm install", r.returncode == 0, r.out):
            return finish(tmp, a.keep)

    # ---- SPLIT loading ----
    r = run(["node", "capture.mjs", "check"], P)
    check("capture check: SPLIT order and registrations", r.returncode == 0 and "CHECK_OK: 4 scenes" in r.out, r.out)
    spl = os.path.join(P, "SPLIT.json")
    good = open(spl).read()
    for name, bad, expect in [
        ("SPLIT out of order", {"tip-to-tail": ["s01", "s02"], "opening": ["s00"], "checkpoint": ["s03"]}, "order differs"),
        ("SPLIT missing a scene", {"opening": ["s00"], "tip-to-tail": ["s01", "s02"]}, "missing: s03"),
        ("SPLIT duplicate scene", {"opening": ["s00", "s01"], "tip-to-tail": ["s01", "s02"], "checkpoint": ["s03"]}, "duplicated: s01"),
        ("SPLIT scene given to the wrong file", {"opening": ["s00", "s01"], "tip-to-tail": ["s02"], "checkpoint": ["s03"]}, "registers scenes SPLIT.json gives elsewhere: s01"),
    ]:
        open(spl, "w").write(json.dumps(bad))
        r = run(["node", "capture.mjs", "check"], P)
        check(f"check rejects {name}", r.returncode == 1 and "LOAD_FAILED" in r.out and expect in r.out, r.out)
    open(spl, "w").write(good)
    sc = os.path.join(P, "scenes", "checkpoint.js")
    good_sc = open(sc).read()
    open(sc, "w").write("// not built yet\n")
    r = run(["node", "capture.mjs", "check"], P)
    check("strict check rejects an unregistered scene", r.returncode == 1 and "does not register: s03" in r.out, r.out)
    r = run(["node", "capture.mjs", "scene", "s02", "1"], P)
    check("lenient preview of s02 warns about s03 and still renders", r.returncode == 0 and "WARNINGS" in r.out and "s02:" in r.out, r.out)
    open(sc, "w").write(good_sc)

    # ---- stills ----
    shutil.rmtree(os.path.join(P, "qa"), ignore_errors=True)
    r = run(["node", "capture.mjs", "scene", "s03", "1"], P)
    pngs = sorted(f for f in os.listdir(os.path.join(P, "qa")) if f.startswith("s03_"))
    ok = r.returncode == 0 and "ERRORS" not in r.out and pngs
    if ok:
        w, h = struct.unpack(">II", open(os.path.join(P, "qa", pngs[-1]), "rb").read()[16:24])
        ok = (w, h) == (1920, 1080)
    check("scene stills at 1920x1080 without page errors", ok, r.out)
    t_mid = tl["scenes"][2]["start"] + tl["scenes"][2]["cues"]["c"]["e"]
    run(["node", "capture.mjs", "qa", f"{t_mid:.2f}", "1.0"], P)
    print("stills:", os.path.join(P, "qa"))

    # a narration.wav that is not the one tts.py published with this timeline is refused before any frame or mux
    wav = os.path.join(P, "narration.wav")
    good_wav = open(wav, "rb").read()
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", "3", wav])
    r = run(["node", "capture.mjs", "all", "1"], P, timeout=120)
    check("capture all refuses a timeline/WAV set tts.py did not complete", r.returncode == 1 and "TTS_INCOMPLETE" in r.out
          and not os.path.exists(os.path.join(P, "chunks")), r.out)
    r = run(["bash", "finish.sh"], P)
    check("finish.sh refuses it too", r.returncode == 1 and "TTS_INCOMPLETE" in r.out, r.out)
    open(wav, "wb").write(good_wav)

    if a.quick:
        return finish(tmp, a.keep)

    # ---- render, resume, finish ----
    env = {"VIDEO_CHUNK_SECONDS": "4"}
    # an encoder that dies before or while a frame is written must fail the render, not leave it waiting on the pipe
    for how, body in [("before reading", "exit 1"), ("partway through a frame", "head -c 100000 >/dev/null; exit 1")]:
        r = run(["node", "capture.mjs", "all", "1"], P, dict(env, PATH=shim(tmp, "ffmpeg", body)), timeout=90)
        kept = [f for f in os.listdir(os.path.join(P, "chunks")) if f.endswith(".mp4")] if os.path.isdir(os.path.join(P, "chunks")) else []
        check(f"ffmpeg exiting {how} fails the render (RENDER_FAILED, no chunk kept)", r.returncode == 1 and "RENDER_FAILED" in r.out
              and not kept, r.out[-600:])
    r = run(["node", "capture.mjs", "all", "0"], P, env)
    check("workers must be positive", r.returncode == 1 and "positive integer" in r.out, r.out)
    r = run(["node", "capture.mjs", "all", "2"], P, env)
    chunks = sorted(f for f in os.listdir(os.path.join(P, "chunks")) if f.endswith(".mp4"))
    n = -(-round(tl["total"] * 30) // 120)
    check(f"render {len(chunks)} chunks with 2 workers", r.returncode == 0 and "RENDER_DONE" in r.out and len(chunks) == n, r.out)
    first = r.secs
    r = run(["node", "capture.mjs", "all", "2"], P, env)
    check("rerender skips finished chunks", r.returncode == 0 and f"({n} already done)" in r.out, r.out)
    os.remove(os.path.join(P, "chunks", chunks[1]))
    r = run(["node", "capture.mjs", "all", "2"], P, env)
    check("resume renders only the missing chunk", r.returncode == 0 and f"({n - 1} already done)" in r.out, r.out)
    print(f"render secs: full {first:.1f}, resume one chunk {r.secs:.1f}")
    open(asset, "a").write("<!-- edited -->\n")
    r = run(["node", "capture.mjs", "all", "2"], P, env)
    check("editing a local asset discards the old chunks", r.returncode == 0 and "(0 already done)" in r.out, r.out)
    r = run(["bash", "finish.sh"], P)
    check("finish.sh", r.returncode == 0, r.out)
    print(r.out.strip())
    pr = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                             "stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt,sample_rate:format=duration",
                                             "-of", "json", os.path.join(P, "final.mp4")]))
    v = next(x for x in pr["streams"] if x["codec_type"] == "video")
    au = next(x for x in pr["streams"] if x["codec_type"] == "audio")
    dur = float(pr["format"]["duration"])
    # 4:2:0 full range (yuvj420p), exactly what the proven lesson renders carry (JPEG frames piped into x264)
    check("final.mp4 H.264 1920x1080 30fps 4:2:0 + AAC 48k", v["codec_name"] == "h264" and (v["width"], v["height"]) == (1920, 1080)
          and v["r_frame_rate"] == "30/1" and v["pix_fmt"] in ("yuvj420p", "yuv420p") and au["codec_name"] == "aac" and au["sample_rate"] == "48000", json.dumps(pr))
    check("final.mp4 duration matches timeline", abs(dur - tl["total"]) < 0.2, f"{dur} vs {tl['total']}")
    bx = boxes(os.path.join(P, "final.mp4"))
    check("faststart: moov before mdat", "moov" in bx and "mdat" in bx and bx.index("moov") < bx.index("mdat"), str(bx))
    lo = subprocess.run(["ffmpeg", "-hide_banner", "-i", os.path.join(P, "final.mp4"), "-af", "ebur128=peak=true", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    summ = lo[lo.rfind("Summary:"):]
    I = float(summ.split("I:")[1].split("LUFS")[0])
    TP = float(summ.split("Peak:")[1].split("dBFS")[0])
    check(f"loudness I={I} LUFS, true peak {TP} dBFS (target -16, -1.5)", abs(I + 16) <= 1.0 and TP <= -1.0, summ)
    srt = open(os.path.join(P, "final.srt")).read()
    check("final.srt has one entry per subtitle chunk", srt.count(" --> ") == sum(len(s["subs"]) for s in tl["scenes"]), srt[:200])

    # ---- render.sh locking ----
    # a render killed outright (no cleanup) leaves its lock behind; then several renders start at once, each
    # delayed differently between steps (rm sleeps 0-0.9 s by pid, like a loaded machine): exactly one may render,
    # every other one must exit 75
    lock = os.path.join(P, ".render.lock")
    admitted = os.path.join(tmp, "admitted")
    slow = shim(tmp, "node", 'echo "$$" >> "%s"; sleep "${HOLD:-3}"; exit 1' % admitted)
    slow = shim(tmp, "rm", 'sleep "0.$(( $$ % 10 ))"; exec /bin/rm "$@"', slow)
    results = []
    for _ in range(3):
        open(admitted, "w").close()
        p = subprocess.Popen(["bash", "render.sh", P, "1"], cwd=P, env=environ(dict(env, PATH=slow, HOLD="60")),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        deadline = time.time() + 30
        while not open(admitted).read() and time.time() < deadline:
            time.sleep(0.1)
        os.killpg(p.pid, signal.SIGKILL)
        p.wait()
        dead = gone(p.pid)
        open(admitted, "w").close()
        ps = [subprocess.Popen(["bash", "render.sh", P, "1"], cwd=P, env=environ(dict(env, PATH=slow)),
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True) for _ in range(8)]
        codes = sorted(finished(q, 60) for q in ps)
        results.append((dead, len(open(admitted).read().split()), codes))
    check("after a killed render, 8 concurrent renders admit exactly one (3 rounds)",
          all(dead and n == 1 and codes == [1] + [75] * 7 for dead, n, codes in results), str(results))
    f = hold(lock)
    r = run(["bash", "render.sh", P, "2"], P, env, timeout=60)
    check("render.sh refuses a held project lock at once (exit 75)", r.returncode == 75 and r.secs < 10 and "lock busy" in r.out, r.out)
    f.close()
    shared = os.path.join(tmp, "shared.lock")
    f = hold(shared)
    r = run(["bash", "render.sh", P, "2"], P, dict(env, VIDEO_RENDER_LOCK=shared, VIDEO_RENDER_LOCK_WAIT="6"), timeout=60)
    check("busy shared lock: bounded wait then exit 75", r.returncode == 75 and 5 <= r.secs < 20 and "lock busy" in r.out, f"{r.secs:.1f}s {r.out}")
    f.close()
    open(shared, "w").write("999999\n")   # left behind by a dead holder: content alone never blocks
    open(os.path.join(P, "capture.mjs"), "a").write("// edited renderer\n")
    r = run(["bash", "render.sh", P, "2"], P, dict(env, VIDEO_RENDER_LOCK=shared), timeout=900)
    log = open(os.path.join(P, "render.log")).read()
    check("render.sh takes the locks a dead render left, rerenders after a renderer edit and finishes", r.returncode == 0
          and os.path.exists(os.path.join(P, "RENDERED")) and "(0 already done)" in log and free(lock) and free(shared)
          and os.path.exists(os.path.join(P, "qa", "sheet_1.jpg")), r.out + log[-600:])
    return finish(tmp, a.keep)


def finish(tmp, keep):
    print(f"\n{'ALL PASS' if not FAILS else 'FAILED: ' + ', '.join(FAILS)}")
    if not keep and not FAILS:
        shutil.rmtree(tmp)
    else:
        print("kept:", tmp)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
