// node capture.mjs check                 → strict load: SPLIT.json order + every scene registered by its file (exit 1 if not)
// node capture.mjs qa <t...>             → qa/t_<t>.png stills
// node capture.mjs scene <id> [n]        → n evenly spaced stills of one scene + all cue starts (qa/<id>_*.png)
// node capture.mjs all [workers]         → render every frame into chunks/*.mp4 (resumable) + chunks/list.txt
// node capture.mjs serve [port]          → serve this directory for preview: http://127.0.0.1:<port>/index.html?t=12
// Workers: argument, else VIDEO_WORKERS, else min(4, cpus). VIDEO_CHUNK_SECONDS (default 60) sets the resume unit.
// Captions are not drawn into frames: the board overlays captions.json on the video. VIDEO_BURN_CAPTIONS=1 burns them in
// (from captions.json when present, else the timeline's spoken subtitle chunks); then build-map --captions-burned-in.
import { chromium } from 'playwright';
import { spawn, spawnSync } from 'node:child_process';
import crypto from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import url from 'node:url';

const ROOT = path.dirname(url.fileURLToPath(import.meta.url));
const W = 1920, H = 1080;
const BURN = process.env.VIDEO_BURN_CAPTIONS === '1';
const [mode, ...args] = process.argv.slice(2);
const die = msg => { console.error(msg); process.exit(1); };
const MODES = ['check', 'qa', 'scene', 'all', 'serve'];
if (!MODES.includes(mode)) die(`usage: node capture.mjs ${MODES.join('|')} ...`);
const readTL = () => {
  try { return JSON.parse(fs.readFileSync(path.join(ROOT, 'timeline.json'))); }
  catch (e) { die(`cannot read timeline.json (${e.message}): run python3 tts.py first`); }
};

// ---------- static server (SPLIT.json cannot be fetched from file://) ----------
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml' };
function serve(port = 0) {
  const srv = http.createServer((req, res) => {
    const rel = decodeURIComponent(new URL(req.url, 'http://x').pathname).replace(/^\/+/, '') || 'index.html';
    const file = path.resolve(ROOT, rel);
    if (file !== ROOT && !file.startsWith(ROOT + path.sep)) { res.writeHead(403); return res.end(); }
    fs.readFile(file, (err, buf) => {
      if (err) { res.writeHead(404); return res.end(); }
      res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
      res.end(buf);
    });
  });
  return new Promise(ok => srv.listen(port, '127.0.0.1', () => ok(srv)));
}

if (mode === 'serve') {
  const srv = await serve(+(args[0] || 8137));
  console.log(`preview: http://127.0.0.1:${srv.address().port}/index.html?t=0   (?play to play, Ctrl-C to stop)`);
} else {
  if (mode === 'all') {   // frames and finish.sh must use one complete tts.py output, never a half-replaced one
    const v = spawnSync('python3', ['tts.py', '--verify'], { cwd: ROOT, encoding: 'utf8' });
    if (v.status !== 0) die(`RENDER_FAILED: ${(v.stderr || v.stdout || v.error?.message || '').trim()}`);
  }
  const TL = readTL();
  const FPS = TL.fps;
  const srv = await serve();
  const BASE = `http://127.0.0.1:${srv.address().port}/index.html`;
  const strict = mode === 'all' || mode === 'check';

  async function open(browser) {
    const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
    const errs = [], fatal = [];
    page.on('pageerror', e => { errs.push(String(e)); fatal.push(String(e)); });
    page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    const q = [strict && 'strict', BURN && 'burn'].filter(Boolean);
    await page.goto(BASE + (q.length ? '?' + q.join('&') : ''), { waitUntil: 'networkidle' });
    await page.waitForFunction(() => window.VIDEO_OK !== undefined, null, { timeout: 60000 });
    const st = await page.evaluate(() => ({ ok: window.VIDEO_OK, errors: window.VIDEO_ERRORS, warnings: window.VIDEO_WARNINGS }));
    return { page, errs, fatal, ...st };
  }
  async function shot(page, t, file) {
    await page.evaluate(t => { window.seek(t); return new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))); }, t);
    return page.screenshot(file ? { path: file } : { type: 'jpeg', quality: 93 });
  }
  const loadOrDie = async browser => {
    const o = await open(browser);
    if (o.warnings.length) console.log('WARNINGS:\n' + o.warnings.join('\n'));
    if (!o.ok) { await browser.close(); srv.close(); die('LOAD_FAILED:\n' + o.errors.join('\n')); }
    return o;
  };
  const browser = await chromium.launch({ args: ['--font-render-hinting=none'] });
  fs.mkdirSync(path.join(ROOT, 'qa'), { recursive: true });
  let failed = false;

  if (mode === 'check') {
    const { errs, fatal } = await loadOrDie(browser);
    if (errs.length) console.log('ERRORS:\n' + errs.join('\n'));
    if (fatal.length) failed = true;
    else console.log(`CHECK_OK: ${TL.scenes.length} scenes registered in SPLIT.json order, ${TL.total}s at ${FPS} fps`);
  } else if (mode === 'qa') {
    const { page, errs } = await loadOrDie(browser);
    for (const t of args.map(Number)) await shot(page, t, path.join(ROOT, 'qa', `t_${t.toFixed(2)}.png`));
    if (errs.length) console.log('ERRORS:\n' + errs.join('\n'));
  } else if (mode === 'scene') {
    const sc = TL.scenes.find(s => s.id === args[0]);
    if (!sc) { await browser.close(); srv.close(); die(`no scene ${args[0]} in timeline.json`); }
    const n = +(args[1] || 0);
    const { page, errs } = await loadOrDie(browser);
    const ts = new Set();
    // just after each cue start settles, and at each cue end
    for (const c of Object.values(sc.cues)) { ts.add(+(c.s + 1.2).toFixed(2)); ts.add(+(c.e - 0.05).toFixed(2)); }
    for (let i = 0; i < n; i++) ts.add(+(sc.dur * (i + 0.5) / n).toFixed(2));
    ts.add(+(sc.dur - 0.1).toFixed(2));
    for (const lt of [...ts].sort((a, b) => a - b)) {
      if (lt < 0 || lt > sc.dur) continue;
      await shot(page, sc.start + lt, path.join(ROOT, 'qa', `${sc.id}_${lt.toFixed(2).padStart(6, '0')}.png`));
    }
    console.log(`${sc.id}: ${ts.size} stills, dur ${sc.dur}s`);
    if (errs.length) console.log('ERRORS:\n' + errs.join('\n'));
  } else if (mode === 'all') {
    failed = !(await renderAll(TL, FPS, browser, open, shot, loadOrDie));
  }
  await browser.close();
  srv.close();
  if (failed) process.exit(1);
}

// ---------- full render: fixed-size chunks, each renamed into place only when complete ----------
async function renderAll(TL, FPS, browser, open, shot, loadOrDie) {
  const cpus = os.cpus().length;
  const want = +(args[0] || process.env.VIDEO_WORKERS || Math.min(4, cpus));
  if (!Number.isInteger(want) || want < 1) die(`workers must be a positive integer, got ${args[0] || process.env.VIDEO_WORKERS}`);
  const workers = Math.min(want, cpus);
  const chunkFrames = Math.round(+(process.env.VIDEO_CHUNK_SECONDS || 60) * FPS);
  if (!(chunkFrames > 0)) die('VIDEO_CHUNK_SECONDS must be > 0');
  const total = Math.ceil(TL.total * FPS);
  const nChunks = Math.ceil(total / chunkFrames);
  const CH = path.join(ROOT, 'chunks');

  // strict load once up front: a broken SPLIT or missing scene stops before any frame is rendered
  const probe = await loadOrDie(browser);
  await probe.page.close();

  // Everything that changes a frame: the files the page loads, local assets and this renderer.
  // A different fingerprint discards old chunks.
  const split = JSON.parse(fs.readFileSync(path.join(ROOT, 'SPLIT.json')));
  const files = d => fs.existsSync(path.join(ROOT, d)) ? fs.readdirSync(path.join(ROOT, d), { withFileTypes: true })
    .flatMap(e => e.isDirectory() ? files(path.join(d, e.name)) : e.isFile() ? [path.join(d, e.name)] : []).sort() : [];
  const inputs = ['timeline.json', 'timeline.js', 'engine.js', 'style.css', 'index.html', 'capture.mjs', 'SPLIT.json',
    ...Object.keys(split).filter(f => split[f].length).map(f => `scenes/${f}.js`), ...files('assets'),
    ...(BURN && fs.existsSync(path.join(ROOT, 'captions.json')) ? ['captions.json'] : [])];
  const h = crypto.createHash('sha256');
  for (const f of inputs) { h.update(f + '\0'); h.update(fs.readFileSync(path.join(ROOT, f))); }
  const plan = { fingerprint: h.digest('hex'), fps: FPS, total, chunkFrames, encoder: 'libx264 medium crf17 yuv420p' };
  if (BURN) plan.captions = 'burned';
  const planFile = path.join(CH, 'plan.json');
  let old = null;
  try { old = JSON.parse(fs.readFileSync(planFile)); } catch {}
  if (!old || JSON.stringify(old) !== JSON.stringify(plan)) {
    fs.rmSync(CH, { recursive: true, force: true });
    fs.mkdirSync(CH, { recursive: true });
    fs.writeFileSync(planFile, JSON.stringify(plan, null, 1));
  }
  fs.rmSync(path.join(CH, 'list.txt'), { force: true });
  for (const f of fs.readdirSync(CH)) if (f.includes('.part')) fs.rmSync(path.join(CH, f));
  const name = i => `c${String(i).padStart(4, '0')}.mp4`;
  const todo = [...Array(nChunks).keys()].filter(i => !fs.existsSync(path.join(CH, name(i))));
  console.log(`render: ${total} frames, ${nChunks} chunks (${nChunks - todo.length} already done), ${Math.min(workers, todo.length)} workers`);

  const toRender = todo.reduce((n, i) => n + Math.min(total, (i + 1) * chunkFrames) - i * chunkFrames, 0);
  let done = 0, ok = true; const t0 = Date.now();
  const queue = [...todo];
  await Promise.all([...Array(Math.min(workers, todo.length)).keys()].map(async w => {
    const { page, errs, fatal } = await open(browser);
    while (ok && queue.length) {
      const i = queue.shift();
      const a = i * chunkFrames, b = Math.min(total, a + chunkFrames);
      const out = path.join(CH, name(i)), part = path.join(CH, `c${String(i).padStart(4, '0')}.part.mp4`);
      const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', String(FPS), part], { stdio: ['pipe', 'inherit', 'inherit'] });
      const closed = new Promise(r => { ff.on('close', r); ff.on('error', e => { console.error(`ffmpeg: ${e.message}`); r(-1); }); });
      ff.stdin.on('error', () => {});
      // ffmpeg can exit before or during a write; its pipe then never drains, so a write also waits for the pipe to close
      let gone = false;
      const pipeGone = new Promise(r => { ff.stdin.once('close', r); closed.then(r); }).then(() => { gone = true; });
      try {
        for (let f = a; f < b; f++) {
          const buf = await shot(page, f / FPS);
          if (!gone && !ff.stdin.write(buf)) await Promise.race([new Promise(r => ff.stdin.once('drain', r)), pipeGone]);
          if (gone) throw new Error(`ffmpeg closed its input at frame ${f} of chunk ${i}`);
          if (++done % 600 === 0) {
            const el = (Date.now() - t0) / 1000;
            console.log(`frames ${done}/${toRender}  ${(done / el).toFixed(1)} fps  eta ${((toRender - done) / (done / el) / 60).toFixed(1)} min`);
          }
          if (fatal.length) throw new Error(`page errors in chunk ${i}:\n` + fatal.slice(0, 20).join('\n'));
        }
      } catch (e) { console.error(`worker ${w}: ${e.message}`); ok = false; }
      ff.stdin.end();
      const code = await closed;
      if (ok && code === 0) fs.renameSync(part, out);
      else { fs.rmSync(part, { force: true }); if (code !== 0) { console.error(`ffmpeg exited ${code} on chunk ${i}`); ok = false; } }
    }
    if (errs.length > fatal.length) console.log(`worker ${w} console errors:\n` + errs.filter(e => !fatal.includes(e)).slice(0, 20).join('\n'));
    await page.close();
  }));
  if (!ok) { console.log('RENDER_FAILED (finished chunks kept; rerun to resume)'); return false; }
  const list = [...Array(nChunks).keys()].map(i => `file '${name(i)}'`).join('\n') + '\n';
  fs.writeFileSync(path.join(CH, 'list.txt'), list);
  console.log('RENDER_DONE');
  return true;
}
