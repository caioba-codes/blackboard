#!/usr/bin/env python3
"""Narrate every cue of script.json, then build timeline.json + timeline.js from the measured audio.

Narrators: Kokoro-82M (local, Apache-2.0, no key; the default) or ElevenLabs (when ELEVENLABS_API_KEY is set).
audio/<scene>_<cue>.wav (Kokoro) or .mp3 (ElevenLabs) + .json (timing). Re-runs skip cues whose engine, model,
voice, settings and text did not change, so an interrupted or quota-stopped run resumes where it stopped.
timeline.json: scenes with absolute start/dur, cues with scene-local s/e, subtitle chunks per sentence.
tts.done: sha256 of timeline.json, timeline.js and narration.wav, written last; render refuses any other set.

  python3 tts.py               narrate what is missing, then write timeline.json, timeline.js, narration.wav, tts.done
  python3 tts.py --check       report cached / missing cues without calling the API (exit 0 = all cached)
  python3 tts.py --verify      exit 0 only if the three published files are the set tts.done fingerprints
  python3 tts.py --workers 3   parallel ElevenLabs requests (default 3)
  python3 tts.py --engine kokoro|elevenlabs   force a narrator (default auto, or BLACKBOARD_TTS_ENGINE)

auto: ElevenLabs when ELEVENLABS_API_KEY is set or every cue is already cached from it, else Kokoro.
Kokoro lives outside the project: $BLACKBOARD_TTS_HOME (default ~/.cache/blackboard)/tts-venv and kokoro/,
installed by the skill's bin/setup_tts.sh. Voice: BLACKBOARD_TTS_VOICE, else script.json "kokoroVoice", else
am_michael; speed BLACKBOARD_TTS_SPEED (1.0). ElevenLabs: voice from script.json "voice"; overrides
ELEVENLABS_MODEL, ELEVENLABS_API_BASE.
Exit codes: 0 ok, 2 usage/script error or no narrator available (TTS_BLOCKED), 3 quota or auth refused by the
API, 4 other API or narrator failure.
"""
import argparse, base64, concurrent.futures as cf, hashlib, json, os, re, subprocess, sys, tempfile, threading, time
import urllib.error, urllib.request, wave

ROOT = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(ROOT, "audio")
MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_v4")
VOICE = "XrExE9yKIg1WjnnlVkGX"   # default when script.json has no "voice"
VOICE_SETTINGS = {"stability": 0.55, "similarity_boost": 0.8, "style": 0.15, "speed": 0.97}
OUTPUT_FORMAT = "mp3_44100_192"
API_BASE = os.environ.get("ELEVENLABS_API_BASE", "https://api.elevenlabs.io").rstrip("/")
FPS = 30
GAP = 0.45          # silence between cues
HEAD, TAIL = 0.6, 0.9  # scene padding
SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")
DONE = os.path.join(ROOT, "tts.done")
PUBLISHED = ("script.json", "timeline.json", "timeline.js", "narration.wav")

TTS_HOME = os.path.expanduser(os.environ.get("BLACKBOARD_TTS_HOME", "~/.cache/blackboard"))
KOKORO_PY = os.path.join(TTS_HOME, "tts-venv", "bin", "python")
KOKORO_FILES = (os.path.join(TTS_HOME, "kokoro", "kokoro-v1.0.onnx"), os.path.join(TTS_HOME, "kokoro", "voices-v1.0.bin"))
KOKORO_MODEL = "kokoro-v1.0"
KOKORO_VOICE = "am_michael"   # Caio picked it over af_heart and bf_emma (2026-10-26)
KOKORO_SPEED = float(os.environ.get("BLACKBOARD_TTS_SPEED", "1.0"))
KOKORO_GAP = {".": 0.3, "?": 0.3, "!": 0.3, ":": 0.25}   # silence after a sentence; 0.12 s after a comma split
INSTALL_HINT = ("install the free local narrator with: sh ~/.claude/skills/blackboard/bin/setup_tts.sh "
                "(or set ELEVENLABS_API_KEY)")


class Stop(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


def load_script(path):
    try:
        with open(path) as f:
            s = json.load(f)
    except (OSError, ValueError) as e:
        raise Stop(2, f"cannot read {path}: {e}")
    errs = []
    for k in ("title", "chapters", "scenes"):
        if k not in s:
            errs.append(f"missing key {k!r}")
    if errs:
        raise Stop(2, "script.json: " + "; ".join(errs))
    if not isinstance(s["chapters"], list) or not s["chapters"]:
        errs.append("chapters must be a non-empty list")
    seen = set()
    for sc in s["scenes"]:
        sid = sc.get("id")
        if not isinstance(sid, str) or not SAFE_ID.match(sid):
            errs.append(f"bad scene id {sid!r}")
            continue
        if sid in seen:
            errs.append(f"duplicate scene id {sid}")
        seen.add(sid)
        ch = sc.get("chapter")
        if not isinstance(ch, int) or not 0 <= ch < len(s["chapters"]):
            errs.append(f"{sid}: chapter {ch!r} is not an index into chapters")
        cues = sc.get("cues") or []
        if not cues:
            errs.append(f"{sid}: no cues")
        cseen = set()
        for c in cues:
            cid = c.get("id")
            if not isinstance(cid, str) or not SAFE_ID.match(cid):
                errs.append(f"{sid}: bad cue id {cid!r}")
                continue
            if cid in cseen:
                errs.append(f"{sid}: duplicate cue id {cid}")
            cseen.add(cid)
            if ("say" in c) == ("pause" in c):
                errs.append(f"{sid}.{cid}: needs exactly one of say / pause")
            elif "say" in c and not (isinstance(c["say"], str) and c["say"].strip()):
                errs.append(f"{sid}.{cid}: empty say")
            elif "pause" in c and not (isinstance(c["pause"], (int, float)) and c["pause"] > 0):
                errs.append(f"{sid}.{cid}: pause must be > 0 seconds")
    if errs:
        raise Stop(2, "script.json:\n  " + "\n  ".join(errs))
    return s


def cache_key(voice, text, model=MODEL, settings=None, fmt=OUTPUT_FORMAT):
    """Everything that changes the audio: model, voice, voice settings, output format, text."""
    blob = json.dumps({"model": model, "voice": voice, "settings": settings or VOICE_SETTINGS, "format": fmt, "text": text},
                      sort_keys=True, ensure_ascii=False)
    return "v2:" + hashlib.sha256(blob.encode()).hexdigest()


def kokoro_key(voice, text):
    blob = json.dumps({"engine": "kokoro", "model": KOKORO_MODEL, "voice": voice, "speed": KOKORO_SPEED,
                       "gaps": KOKORO_GAP, "text": text}, sort_keys=True, ensure_ascii=False)
    return "kokoro1:" + hashlib.sha256(blob.encode()).hexdigest()


def kokoro_available():
    return os.access(KOKORO_PY, os.X_OK) and all(os.path.isfile(f) for f in KOKORO_FILES)


def legacy_key(voice, text):
    # Projects narrated before the cache key covered the settings used sha1(model + voice + text) with exactly
    # these defaults; accept such audio only while the defaults are still in force.
    if MODEL == "eleven_v4" and VOICE_SETTINGS == {"stability": 0.55, "similarity_boost": 0.8, "style": 0.15, "speed": 0.97} \
            and OUTPUT_FORMAT == "mp3_44100_192":
        return hashlib.sha1((MODEL + voice + text).encode()).hexdigest()
    return None


def cached(path, voice, text):
    meta = path + ".json"
    if path.endswith(".wav"):   # Kokoro cue
        try:
            with open(meta) as f:
                m = json.load(f)
        except (OSError, ValueError):
            return False
        return os.path.exists(path) and bool(m.get("alignment")) and m.get("hash") == kokoro_key(voice, text)
    if not (os.path.exists(path) and os.path.exists(meta)):
        return False
    try:
        with open(meta) as f:
            m = json.load(f)
    except ValueError:
        return False
    if not m.get("alignment"):
        return False
    h = m.get("hash")
    if h == cache_key(voice, text):
        return True
    if h is not None and h == legacy_key(voice, text):
        m["hash"] = cache_key(voice, text)        # upgrade in place, audio unchanged
        atomic_write(meta, json.dumps(m).encode())
        return True
    return False


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def verify_done():
    """None when the current script and published timing/audio match one successful run, else why not."""
    try:
        with open(DONE) as f:
            want = json.load(f)
    except (OSError, ValueError):
        return "tts.done is missing: run python3 tts.py (cached cues make no API call)"
    for n in PUBLISHED:
        p = os.path.join(ROOT, n)
        if not os.path.exists(p) or file_sha256(p) != want.get(n):
            return f"{n} is not the file tts.done fingerprints (a tts.py run failed or was interrupted): rerun python3 tts.py"
    return None


def atomic_write(path, data):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-")
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def api_error(e):
    """(code, message) for an HTTPError; code 3 = quota/auth (do not retry), None = retryable."""
    try:
        body = e.read().decode(errors="replace")
    except Exception:
        body = ""
    status = ""
    try:
        d = json.loads(body).get("detail")
        status = (d.get("status") or d.get("code") or "") if isinstance(d, dict) else ""
    except Exception:
        pass
    msg = f"HTTP {e.code} {status} {body[:400]}".strip()
    if e.code in (401, 402, 403) or "quota" in status or "credit" in status or "quota" in body.lower():
        return 3, msg
    if e.code == 429 or e.code >= 500:
        return None, msg
    return 4, msg


stop_event = threading.Event()


def tts(path, voice, text, key):
    if stop_event.is_set():
        return
    body = json.dumps({"text": text, "model_id": MODEL, "voice_settings": VOICE_SETTINGS}).encode()
    url = f"{API_BASE}/v1/text-to-speech/{voice}/with-timestamps?output_format={OUTPUT_FORMAT}"
    last = ""
    for attempt in range(6):
        if stop_event.is_set():
            return
        try:
            req = urllib.request.Request(url, body, {"xi-api-key": key, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                r = json.load(resp)
            break
        except urllib.error.HTTPError as e:
            code, last = api_error(e)
            if code:
                stop_event.set()
                raise Stop(code, f"{os.path.basename(path)}: {last}")
        except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError) as e:  # network / bad JSON
            last = repr(e)
        if attempt < 5:
            time.sleep(3 * (attempt + 1))
    else:
        stop_event.set()
        raise Stop(4, f"{os.path.basename(path)}: failed after 6 attempts: {last}")
    al = r.get("alignment") or r.get("normalized_alignment")
    if not r.get("audio_base64") or not al:
        stop_event.set()
        raise Stop(4, f"{os.path.basename(path)}: response without audio or alignment")
    # the metadata is the commit marker that makes the cue count as cached: drop the old one before the audio
    # changes, write the new one last, so an interruption in between leaves the cue missing, never mismatched
    if os.path.exists(path + ".json"):
        os.remove(path + ".json")
    atomic_write(path, base64.b64decode(r["audio_base64"]))
    atomic_write(path + ".json", json.dumps({"hash": cache_key(voice, text), "model": MODEL, "voice": voice,
                                             "settings": VOICE_SETTINGS, "text": text, "alignment": al}).encode())
    print("tts", os.path.basename(path), flush=True)


def pieces(text):
    """(start, end) inclusive char spans of the subtitle chunks: sentences, long ones split at commas."""
    out = []
    for m in re.finditer(r"[^.?!:]+[.?!:]?", text):
        seg = m.group(0)
        if not seg.strip():
            continue
        parts = re.split(r"(?<=,)\s", seg) if len(seg) > 95 else [seg]
        pos = m.start()
        for p in parts:
            a = text.find(p, pos)
            b = a + len(p) - 1
            pos = b + 1
            a2 = a + (len(p) - len(p.lstrip()))
            if a2 <= b:
                out.append((a2, b))
    return out


def kokoro_alignment(text, spans):
    """Character timing built from each chunk's measured (start, end) in the audio, spread linearly inside it."""
    st, en = [0.0] * len(text), [0.0] * len(text)
    prev = 0
    for (a, b), (s0, s1) in zip(pieces(text), spans):
        for i in range(prev, a):                  # whitespace between chunks: at the previous chunk's end
            st[i] = en[i] = en[i - 1] if i else 0.0
        step = (s1 - s0) / (b - a + 1)
        for i in range(a, b + 1):
            st[i], en[i] = round(s0 + step * (i - a), 4), round(s0 + step * (i - a + 1), 4)
        prev = b + 1
    for i in range(prev, len(text)):
        st[i] = en[i] = en[i - 1] if i else 0.0
    return {"characters": list(text), "character_start_times_seconds": st, "character_end_times_seconds": en}


KOKORO_HELPER = r"""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
req = json.load(sys.stdin)
k = Kokoro(req["model"], req["voices"])
for job in req["jobs"]:
    out, t, sr = [], 0.0, 24000
    spans = []
    for text, gap in zip(job["pieces"], job["gaps"]):
        a, sr = k.create(text, voice=job["voice"], speed=job["speed"], lang=job["lang"])
        spans.append([round(t, 4), round(t + len(a) / sr, 4)])
        out.append(a)
        t += len(a) / sr
        if gap:
            out.append(np.zeros(int(gap * sr), dtype=np.float32))
            t += gap
    sf.write(job["tmp"], np.concatenate(out), sr, subtype="PCM_16", format="WAV")
    print(json.dumps({"tmp": job["tmp"], "spans": spans}), flush=True)
"""


def kokoro_synth(jobs):
    """Render [{"tmp", "pieces", "gaps", "voice", "speed", "lang"}] with the Kokoro venv; yields {"tmp", "spans"}."""
    req = {"model": KOKORO_FILES[0], "voices": KOKORO_FILES[1], "jobs": jobs}
    p = subprocess.run([KOKORO_PY, "-I", "-c", KOKORO_HELPER], input=json.dumps(req), capture_output=True, text=True)
    done = [json.loads(line) for line in p.stdout.splitlines() if line.startswith("{")]
    if p.returncode:
        raise Stop(4, f"TTS_FAILED: Kokoro exited {p.returncode} after {len(done)} of {len(jobs)} cues: {p.stderr.strip()[-600:]}")
    return done


def kokoro_run(missing, voice):
    jobs = []
    for path, _, text in missing:
        ps = pieces(text)
        gaps = [KOKORO_GAP.get(text[a:b + 1].rstrip()[-1:], 0.12) for a, b in ps[:-1]] + [0]
        jobs.append({"path": path, "text": text, "tmp": os.path.join(AUD, ".tmp-" + os.path.basename(path)),
                     "pieces": [text[a:b + 1].strip() for a, b in ps], "gaps": gaps, "voice": voice, "speed": KOKORO_SPEED,
                     "lang": "en-gb" if voice[:1] == "b" else "en-us"})
    by_tmp = {j["tmp"]: j for j in jobs}
    for r in kokoro_synth([{k: v for k, v in j.items() if k not in ("path", "text")} for j in jobs]):
        j = by_tmp[r["tmp"]]
        if os.path.exists(j["path"] + ".json"):
            os.remove(j["path"] + ".json")
        os.replace(j["tmp"], j["path"])
        atomic_write(j["path"] + ".json", json.dumps({"hash": kokoro_key(voice, j["text"]), "engine": "kokoro",
                                                       "model": KOKORO_MODEL, "voice": voice, "speed": KOKORO_SPEED,
                                                       "text": j["text"], "spans": r["spans"],
                                                       "alignment": kokoro_alignment(j["text"], r["spans"])}).encode())
        print("tts", os.path.basename(j["path"]), flush=True)


def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).decode())


def chunks(text, al):
    """Split narration into subtitle chunks (sentences, long ones split at commas) with times."""
    joined = "".join(al["characters"])
    st, en = al["character_start_times_seconds"], al["character_end_times_seconds"]
    return [{"text": joined[a:b + 1].strip(), "s": st[a], "e": en[b]} for a, b in pieces(joined)]


def kokoro_voice(script):
    return os.environ.get("BLACKBOARD_TTS_VOICE") or script.get("kokoroVoice") or KOKORO_VOICE


def jobs_for(script, engine="elevenlabs"):
    voice, ext = (kokoro_voice(script), "wav") if engine == "kokoro" else (script.get("voice") or VOICE, "mp3")
    return [(os.path.join(AUD, f"{sc['id']}_{cue['id']}.{ext}"), voice, cue["say"])
            for sc in script["scenes"] for cue in sc["cues"] if "say" in cue]


def choose_engine(script, requested=None):
    """(engine, reason). Raises Stop(2, TTS_BLOCKED …) when no narrator can produce the missing cues."""
    req = (requested or os.environ.get("BLACKBOARD_TTS_ENGINE") or "auto").strip().lower()
    if req not in ("auto", "kokoro", "elevenlabs"):
        raise Stop(2, f"unknown TTS engine {req!r}: use auto, kokoro or elevenlabs")
    if req != "auto":
        return req, "requested"
    if os.environ.get("ELEVENLABS_API_KEY", "").strip():
        return "elevenlabs", "ELEVENLABS_API_KEY is set"
    for eng in ("elevenlabs", "kokoro"):
        jobs = jobs_for(script, eng)
        if jobs and all(cached(*j) for j in jobs):
            return eng, "every cue already cached"
    if kokoro_available():
        return "kokoro", "local Kokoro (no key needed)"
    raise Stop(2, "TTS_BLOCKED: no narrator: Kokoro is not installed and ELEVENLABS_API_KEY is not set; " + INSTALL_HINT)


def build_timeline(script, engine="elevenlabs"):
    t, scenes, concat = 0.0, [], []
    for sc in script["scenes"]:
        local, cues, subs = HEAD, {}, []
        for cue in sc["cues"]:
            if "pause" in cue:
                d = cue["pause"]
                cues[cue["id"]] = {"s": local, "e": local + d, "pause": True}
            else:
                p = os.path.join(AUD, f"{sc['id']}_{cue['id']}.{'wav' if engine == 'kokoro' else 'mp3'}")
                d = dur(p)
                cues[cue["id"]] = {"s": local, "e": local + d}
                with open(p + ".json") as f:
                    al = json.load(f)["alignment"]
                for c in chunks(cue["say"], al):
                    subs.append({"text": c["text"], "s": local + c["s"], "e": local + c["e"]})
                concat.append((t + local, p))
            local += d + GAP
        sd = local - GAP + TAIL
        scenes.append({"id": sc["id"], "chapter": sc["chapter"], "start": round(t, 3), "dur": round(round(t + sd, 3) - round(t, 3), 3), "cues": cues, "subs": subs})
        t += sd
    tl = {"title": script["title"], "subtitle": script.get("subtitle", ""), "chapters": script["chapters"],
          "total": round(t, 3), "fps": FPS, "scenes": scenes}
    return tl, concat, t


def write_track(concat, total, out, rate=48000):
    """Write a mono 16-bit WAV of `total` seconds with each (start seconds, audio path) clip placed at its start."""
    import wave
    n_total, cursor = int(round(total * rate)), 0
    zero = bytes(2 * rate)
    def silence(n):
        while n > 0:
            k = min(n, rate)
            w.writeframes(zero[:2 * k])
            n -= k
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        for at, path in sorted(concat):
            pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"],
                                 capture_output=True, check=True).stdout
            begin = int(round(at * rate))
            if begin > cursor:
                silence(begin - cursor); cursor = begin
            skip = cursor - begin                      # a clip may not start before the previous one ended
            frames = pcm[2 * skip:2 * max(skip, min(len(pcm) // 2, n_total - begin))]
            w.writeframes(frames); cursor += len(frames) // 2
        silence(n_total - cursor)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report cached/missing cues, no API calls")
    ap.add_argument("--verify", action="store_true", help="check that the published files form one complete run")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--engine", choices=("auto", "kokoro", "elevenlabs"))
    a = ap.parse_args(argv)
    if a.verify:
        why = verify_done()
        if why:
            print("TTS_INCOMPLETE: " + why, file=sys.stderr)
            return 1
        print("TTS_OK: " + ", ".join(PUBLISHED) + " match tts.done")
        return 0
    if a.workers < 1:
        raise Stop(2, "--workers must be >= 1")
    script = load_script(os.path.join(ROOT, "script.json"))
    os.makedirs(AUD, exist_ok=True)
    try:
        engine, why = choose_engine(script, a.engine)
    except Stop:
        if not a.check:
            raise
        engine, why = "kokoro", "no narrator installed: " + INSTALL_HINT
    jobs = jobs_for(script, engine)
    missing = [j for j in jobs if not cached(*j)]
    model = KOKORO_MODEL if engine == "kokoro" else MODEL
    print(f"cues: {len(jobs)} spoken, {len(jobs) - len(missing)} cached, {len(missing)} to narrate "
          f"(engine {engine}: {why}; model {model}, voice {jobs[0][1] if jobs else '-'})", flush=True)
    if a.check:
        for p, _, _ in missing:
            print("missing", os.path.basename(p))
        return 0 if not missing else 1
    if missing and engine == "kokoro":
        if not kokoro_available():
            raise Stop(2, f"TTS_BLOCKED: Kokoro is not installed and {len(missing)} cue(s) need narration; " + INSTALL_HINT)
        kokoro_run(missing, jobs[0][1])
        left = sum(1 for j in jobs if not cached(*j))
        if left:
            raise Stop(4, f"TTS_FAILED: {left} of {len(jobs)} cues still missing after the Kokoro run; rerun tts.py")
    elif missing:
        key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
        if not key:
            raise Stop(2, f"ELEVENLABS_API_KEY is not set and {len(missing)} cue(s) need narration")
        with cf.ThreadPoolExecutor(a.workers) as ex:
            futs = [ex.submit(tts, p, v, txt, key) for p, v, txt in missing]
            errs = []
            for fu in cf.as_completed(futs):
                try:
                    fu.result()
                except Stop as e:
                    errs.append(e)
        if errs:
            left = sum(1 for j in jobs if not cached(*j))
            e = min(errs, key=lambda x: x.code)
            raise Stop(e.code, f"{'TTS_QUOTA_OR_AUTH' if e.code == 3 else 'TTS_FAILED'}: {e}\n"
                               f"{len(jobs) - left} of {len(jobs)} cues are cached; rerun tts.py to resume the other {left}.")

    tl, concat, t = build_timeline(script, engine)
    data = json.dumps(tl, indent=1)
    # narration track: place each clip at its absolute time. Clips never overlap (cues are sequential), so the
    # track is written once, left to right: silence up to each clip's start, then the clip decoded to 48 kHz mono.
    # (An ffmpeg amix of every clip padded to full length costs clips x duration and stalls on long videos.)
    tmp = os.path.join(ROOT, ".narration.tmp.wav")
    write_track(concat, t, tmp)
    # publish only after the WAV is built, then fingerprint the set; a failure before this leaves the previous set
    atomic_write(os.path.join(ROOT, "timeline.json"), data.encode())
    atomic_write(os.path.join(ROOT, "timeline.js"), ("window.TIMELINE=" + data + ";\n").encode())
    os.replace(tmp, os.path.join(ROOT, "narration.wav"))
    atomic_write(DONE, json.dumps({n: file_sha256(os.path.join(ROOT, n)) for n in PUBLISHED}, indent=1).encode())
    print(f"timeline: {len(tl['scenes'])} scenes, {t/60:.1f} min")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Stop as e:
        print(str(e), file=sys.stderr)
        sys.exit(e.code)
