/* Lesson video engine. Every frame is a pure function of t: seek(t) rebuilds nothing,
   it only sets styles / redraws canvases from t. No CSS transitions, no timers.

   A scene registers with:
     scene('s02', (root, S) => {         // build once: create DOM, read S.at('a') etc.
       ...
       return (t) => { ... };             // update(t): t is scene-local seconds
     });
   S (per scene) gives: at(cue) end(cue) dur, el(), tex(), p(), show(), fig(), deriv(), mcq(), countdown(), ...
   index.html loads the scene files listed in SPLIT.json and checks every registration (window.SCENES).
*/
(() => {
  const TL = window.TIMELINE;
  const FADE = 0.4;                       // scene cross-fade
  const registry = {};
  const built = {};
  const owner = {};                        // scene id -> scene file that registered it
  const regErrors = [];
  window.scene = (id, fn) => {
    const file = window.__SCENE_FILE || '(inline)';
    if (registry[id]) regErrors.push(`scene ${id} registered twice (${owner[id]} and ${file})`);
    registry[id] = fn; owner[id] = file;
  };
  window.SCENES = { registry, owner, errors: regErrors };

  // ---------- math / easing ----------
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const ease = {
    out: x => 1 - Math.pow(1 - x, 3),
    inOut: x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2,
    back: x => { const c = 1.6; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); },
    lin: x => x,
  };
  const lerp = (a, b, k) => a + (b - a) * k;
  // deterministic pseudo-random (chalk wobble)
  const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };

  // ---------- DOM helpers ----------
  function el(tag, cls, html, parent, style) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    if (style) Object.assign(e.style, style);
    if (parent) parent.appendChild(e);
    return e;
  }
  // Render a string mixing text and $inline$ / $$display$$ math.
  function rich(s) {
    return s.replace(/\$\$([\s\S]+?)\$\$|\$([^$]+?)\$/g, (_, d, i) =>
      katex.renderToString(d || i, { displayMode: !!d, throwOnError: false, trust: true, strict: false }));
  }
  function tex(latex, cls, parent, style) {
    const e = el('div', 'tex ' + (cls || ''), null, parent, style);
    e.innerHTML = katex.renderToString(latex, { displayMode: false, throwOnError: false, trust: true, strict: false });
    return e;
  }
  function txt(s, cls, parent, style) { return el('div', cls || '', rich(s), parent, style); }

  // progress of an animation that starts at t0 and lasts d seconds
  const p = (t, t0, d = 0.6, e = ease.out) => e(clamp((t - t0) / d));
  // fade/slide an element in at t0 (and optionally out at t1)
  function show(e, t, t0, o = {}) {
    const d = o.dur ?? 0.55;
    let k = p(t, t0, d, o.ease || ease.out);
    if (o.out != null) k *= 1 - p(t, o.out, o.outDur ?? 0.4, ease.lin);
    const dy = o.dy ?? 18, dx = o.dx ?? 0, sc = o.scale ?? 1;
    e.style.opacity = (o.min ?? 0) + (1 - (o.min ?? 0)) * k;
    const s = sc === 1 ? '' : ` scale(${lerp(sc, 1, k)})`;
    e.style.transform = `translate(${(1 - k) * dx}px,${(1 - k) * dy}px)${s}` + (o.extra || '');
    e.style.visibility = k <= 0.001 && !(o.min) ? 'hidden' : 'visible';
    return k;
  }
  // write-on effect for text: reveal left→right with clip-path
  function wipe(e, t, t0, d = 0.8) {
    const k = p(t, t0, d, ease.inOut);
    e.style.clipPath = `inset(-20% ${(1 - k) * 100}% -20% -2%)`;
    e.style.visibility = k <= 0 ? 'hidden' : 'visible';
    return k;
  }
  // highlight pulse: returns 0..1..0 bump around t0
  const pulse = (t, t0, d = 0.9) => { const x = (t - t0) / d; return x < 0 || x > 1 ? 0 : Math.sin(Math.PI * x); };

  // ---------- canvas figures with a world coordinate system ----------
  // fig(parent, {x,y,w,h, xr:[x0,x1], yr:[y0,y1]}) → object with drawing methods; call f.clear() each frame.
  function fig(parent, o) {
    const c = el('canvas', 'fig', null, parent);
    const DPR = 1;
    c.width = o.w * DPR; c.height = o.h * DPR;
    Object.assign(c.style, { left: o.x + 'px', top: o.y + 'px', width: o.w + 'px', height: o.h + 'px' });
    const g = c.getContext('2d');
    const pad = o.pad ?? 50;
    const xr = o.xr || [0, 1], yr = o.yr || [0, 1];
    // equal scale unless o.free
    let sx = (o.w - 2 * pad) / (xr[1] - xr[0]), sy = (o.h - 2 * pad) / (yr[1] - yr[0]);
    if (!o.free) { const s = Math.min(sx, sy); sx = sy = s; }
    const ox = pad + ((o.w - 2 * pad) - sx * (xr[1] - xr[0])) / 2, oy = pad + ((o.h - 2 * pad) - sy * (yr[1] - yr[0])) / 2;
    const X = x => ox + (x - xr[0]) * sx, Y = y => o.h - oy - (y - yr[0]) * sy;
    const f = {
      canvas: c, g, X, Y, sx, sy, xr, yr,
      clear() { g.setTransform(DPR, 0, 0, DPR, 0, 0); g.clearRect(0, 0, o.w, o.h); },
      style(col = '#ece8df', w = 3, dash = null, alpha = 1) {
        g.strokeStyle = col; g.fillStyle = col; g.lineWidth = w; g.globalAlpha = alpha;
        g.setLineDash(dash || []); g.lineCap = 'round'; g.lineJoin = 'round';
      },
      // line from world a to world b, drawn to fraction k (0..1)
      line(x1, y1, x2, y2, col, w = 3, k = 1, dash, alpha = 1) {
        if (k <= 0) return; f.style(col, w, dash, alpha);
        g.beginPath(); g.moveTo(X(x1), Y(y1)); g.lineTo(X(lerp(x1, x2, k)), Y(lerp(y1, y2, k))); g.stroke(); g.globalAlpha = 1;
      },
      arrow(x1, y1, x2, y2, col = '#ece8df', w = 5, k = 1, alpha = 1, head = 22) {
        if (k <= 0) return;
        const ex = lerp(x1, x2, k), ey = lerp(y1, y2, k);
        const ax = X(x1), ay = Y(y1), bx = X(ex), by = Y(ey);
        const L = Math.hypot(bx - ax, by - ay); if (L < 1) return;
        const ux = (bx - ax) / L, uy = (by - ay) / L, h = Math.min(head, L * 0.6);
        f.style(col, w, null, alpha);
        g.beginPath(); g.moveTo(ax, ay); g.lineTo(bx - ux * h * 0.7, by - uy * h * 0.7); g.stroke();
        g.beginPath(); g.moveTo(bx, by);
        g.lineTo(bx - ux * h - uy * h * 0.5, by - uy * h + ux * h * 0.5);
        g.lineTo(bx - ux * h + uy * h * 0.5, by - uy * h - ux * h * 0.5); g.closePath(); g.fill();
        g.globalAlpha = 1;
      },
      // arrow in pixel units from a world anchor (for velocity arrows etc.)
      dot(x, y, r = 8, col = '#ece8df', alpha = 1) { f.style(col, 1, null, alpha); g.beginPath(); g.arc(X(x), Y(y), r, 0, 7); g.fill(); g.globalAlpha = 1; },
      ring(x, y, r = 8, col = '#ece8df', w = 3, alpha = 1) { f.style(col, w, null, alpha); g.beginPath(); g.arc(X(x), Y(y), r, 0, 7); g.stroke(); g.globalAlpha = 1; },
      text(s, x, y, o2 = {}) {
        g.globalAlpha = o2.alpha ?? 1; g.fillStyle = o2.col || '#ece8df';
        g.font = `${o2.weight || 400} ${o2.size || 30}px ${o2.font || "'Crimson Pro'"}`;
        g.textAlign = o2.align || 'center'; g.textBaseline = o2.base || 'middle';
        g.fillText(s, X(x) + (o2.dx || 0), Y(y) + (o2.dy || 0)); g.globalAlpha = 1;
      },
      grid(alpha = 1, step = 1) {
        f.style('#2a312d', 1.5, null, alpha);
        for (let x = Math.ceil(xr[0]); x <= xr[1]; x += step) { g.beginPath(); g.moveTo(X(x), Y(yr[0])); g.lineTo(X(x), Y(yr[1])); g.stroke(); }
        for (let y = Math.ceil(yr[0]); y <= yr[1]; y += step) { g.beginPath(); g.moveTo(X(xr[0]), Y(y)); g.lineTo(X(xr[1]), Y(y)); g.stroke(); }
        g.globalAlpha = 1;
      },
      // axes through origin with arrowheads, optional labels and ticks
      axes(o2 = {}) {
        const a = o2.alpha ?? 1, col = o2.col || '#bdb9b0';
        const x0 = o2.x0 ?? (xr[0] <= 0 && xr[1] >= 0 ? 0 : xr[0]);
        const y0 = o2.y0 ?? (yr[0] <= 0 && yr[1] >= 0 ? 0 : yr[0]);
        f.arrow(xr[0], y0, xr[1], y0, col, 2.5, o2.k ?? 1, a, 16);
        f.arrow(x0, yr[0], x0, yr[1], col, 2.5, o2.k ?? 1, a, 16);
        if (o2.xl) f.text(o2.xl, xr[1], y0, { col, size: 30, dx: -6, dy: 30, alpha: a, align: 'right', font: "'Crimson Pro'", weight: 500 });
        if (o2.yl) f.text(o2.yl, x0, yr[1], { col, size: 30, dx: 16, dy: 8, alpha: a, align: 'left', font: "'Crimson Pro'", weight: 500 });
        if (o2.ticks) {
          const st = o2.tstep || 1;
          for (let x = Math.ceil(xr[0] / st) * st; x < xr[1] - 1e-9; x += st) if (Math.abs(x - x0) > 1e-9) {
            f.line(x, y0, x, y0, col, 2, 1, null, a); f.style(col, 2, null, a);
            g.beginPath(); g.moveTo(X(x), Y(y0) - 7); g.lineTo(X(x), Y(y0) + 7); g.stroke();
            f.text(fmt(x), x, y0, { col: '#8d8c85', size: 24, dy: 26, alpha: a });
          }
          for (let y = Math.ceil(yr[0] / st) * st; y < yr[1] - 1e-9; y += st) if (Math.abs(y - y0) > 1e-9) {
            f.style(col, 2, null, a); g.beginPath(); g.moveTo(X(x0) - 7, Y(y)); g.lineTo(X(x0) + 7, Y(y)); g.stroke();
            f.text(fmt(y), x0, y, { col: '#8d8c85', size: 24, dx: -24, alpha: a, align: 'right' });
          }
        }
        g.globalAlpha = 1;
      },
      // polyline of a function y=fn(x) on [a,b], drawn to fraction k
      plot(fn, a, b, col = '#ece8df', w = 4, k = 1, alpha = 1, dash) {
        if (k <= 0) return; f.style(col, w, dash, alpha);
        const n = 160, end = lerp(a, b, k); g.beginPath();
        for (let i = 0; i <= n; i++) { const x = lerp(a, end, i / n), y = fn(x); i ? g.lineTo(X(x), Y(y)) : g.moveTo(X(x), Y(y)); }
        g.stroke(); g.globalAlpha = 1;
      },
      // circular arc for angle marks: centre (cx,cy), radius in px, angles in degrees (math convention)
      arc(cx, cy, rpx, a0, a1, col = '#e3b35a', w = 3, k = 1, alpha = 1) {
        if (k <= 0) return; f.style(col, w, null, alpha);
        g.beginPath(); g.arc(X(cx), Y(cy), rpx, -a0 * Math.PI / 180, -lerp(a0, a1, k) * Math.PI / 180, a1 > a0); g.stroke(); g.globalAlpha = 1;
      },
      poly(pts, col, alpha = 1) { f.style(col, 1, null, alpha); g.beginPath(); pts.forEach(([x, y], i) => i ? g.lineTo(X(x), Y(y)) : g.moveTo(X(x), Y(y))); g.closePath(); g.fill(); g.globalAlpha = 1; },
      // a little cart (body + wheels) centred at world x on baseline y
      cart(x, y, o2 = {}) {
        const s = o2.scale || 1, col = o2.col || '#c4505f', a = o2.alpha ?? 1;
        const cx = X(x), cy = Y(y), w = 110 * s, h = 46 * s, r = 13 * s;
        g.globalAlpha = a; g.fillStyle = col;
        roundRect(g, cx - w / 2, cy - h - 2 * r + 4 * s, w, h, 10 * s); g.fill();
        g.fillStyle = 'rgba(255,255,255,.18)'; roundRect(g, cx - w / 2 + 10 * s, cy - h - 2 * r + 12 * s, w - 20 * s, 10 * s, 5 * s); g.fill();
        g.fillStyle = '#ece8df';
        for (const dx of [-w * 0.3, w * 0.3]) { g.beginPath(); g.arc(cx + dx, cy - r, r, 0, 7); g.fill(); }
        g.fillStyle = '#0d0f0e'; for (const dx of [-w * 0.3, w * 0.3]) { g.beginPath(); g.arc(cx + dx, cy - r, r * 0.4, 0, 7); g.fill(); }
        g.globalAlpha = 1;
      },
      ball(x, y, r = 16, col = '#e3b35a', a = 1) { f.dot(x, y, r, col, a); f.style('#fff', 1, null, a * .35); g.beginPath(); g.arc(X(x) - r * .35, Y(y) - r * .35, r * .3, 0, 7); g.fill(); g.globalAlpha = 1; },
      // number line: ticks from a..b along y=y0, with labels
      numberLine(a, b, y0 = 0, o2 = {}) {
        const al = o2.alpha ?? 1, col = o2.col || '#bdb9b0';
        f.line(a - 0.6, y0, b + 0.6, y0, col, 3, o2.k ?? 1, null, al);
        for (let x = a; x <= b; x++) {
          f.style(col, 2.5, null, al); g.beginPath(); g.moveTo(X(x), Y(y0) - 12); g.lineTo(X(x), Y(y0) + 12); g.stroke();
          f.text(fmt(x), x, y0, { col: x === 0 ? '#ece8df' : '#8d8c85', size: 28, dy: 40, alpha: al, weight: x === 0 ? 600 : 400 });
        }
        if (o2.unit) f.text(o2.unit, b + 0.6, y0, { col: '#8d8c85', size: 28, dy: 40, alpha: al, align: 'left', dx: 10 });
        g.globalAlpha = 1;
      },
    };
    return f;
  }
  function roundRect(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
  const fmt = v => (Math.abs(v - Math.round(v)) < 1e-9 ? String(Math.round(v)) : String(+v.toFixed(2))).replace('-', '−');

  // ---------- composite components ----------
  // Header chip for example types: kind = 'Worked example' | 'Your turn' | 'Checkpoint' | 'Quiz 1 of 3' ...
  function header(parent, kind, color) {
    return el('div', 'tag', kind, parent, { color: color || 'var(--acc)' });
  }
  // derivation: lines = [{l:'\\Delta x', r:'= 600\\,\\mathrm{cm}', why:'10^2 = 100', at:t0}]  → returns update(t)
  function deriv(parent, lines, style) {
    const box = el('div', 'deriv', null, parent, style);
    const rows = lines.map(L => {
      const a = el('div', 'lhs', null, box); if (L.l) a.innerHTML = katex.renderToString(L.l, { throwOnError: false, trust: true, strict: false });
      const b = el('div', 'rhs' + (L.box ? ' boxwrap' : ''), null, box);
      b.innerHTML = katex.renderToString(L.r, { throwOnError: false, trust: true, strict: false });
      if (L.box) b.firstChild.classList.add('boxed');
      const c = el('div', 'why', L.why ? rich(L.why) : '', box); if (!L.why) c.style.borderLeft = 'none';
      return { a, b, c, L };
    });
    return {
      el: box, rows,
      update(t) {
        rows.forEach(({ a, b, c, L }) => {
          show(a, t, L.at, { dx: -10, dy: 0 }); show(b, t, L.at, { dx: -10, dy: 0 });
          show(c, t, L.at + (L.whyDelay ?? 0.35), { dx: 14, dy: 0 });
          if (L.box) { const k = pulse(t, L.at + 0.4, 1.2); b.firstChild.style.boxShadow = `0 0 ${24 * k}px rgba(95,191,134,${0.7 * k})`; }
        });
      },
    };
  }
  // multiple choice: o = {q, opts:[...], right:'b', reasons:{a:'..'}, at:{show, reveal, reasons}}
  function mcq(parent, o, style) {
    const box = el('div', 'mcq', null, parent, style);
    const q = txt(o.q, 'q', box);
    const grid = el('div', 'opts', null, box);
    const L = 'ABCD';
    const opts = o.opts.map((s, i) => {
      const op = el('div', 'opt', null, grid);
      el('div', 'L', L[i], op); el('div', '', rich(s), op);
      const key = 'abcd'[i];
      const rs = o.reasons && o.reasons[key] ? el('div', 'reason', rich(o.reasons[key]), op) : null;
      return { op, key, rs };
    });
    return {
      el: box,
      update(t) {
        show(q, t, o.at.show);
        opts.forEach(({ op, key, rs }, i) => {
          const kin = show(op, t, o.at.show + 0.5 + i * 0.25);
          const rev = t >= o.at.reveal;
          op.classList.toggle('right', rev && key === o.right);
          op.classList.toggle('wrong', rev && key !== o.right);
          if (key === o.right) op.style.transform += ` scale(${1 + 0.04 * pulse(t, o.at.reveal, 0.8)})`;
          // wrong options dim after the reveal and come back up when their reason is shown
          let dimK = rev && key !== o.right ? 0.5 * p(t, o.at.reveal, 0.4) : 0;
          if (rs) {
            // reasons: o.at.reasonAt = {a: t, ...} (preferred, sync to narration) or reasons + i*reasonStep
            const ri = Object.keys(o.reasons).indexOf(key);
            const t0 = o.at.reasonAt?.[key] ?? (o.at.reasons ?? 1e9) + ri * (o.at.reasonStep ?? 1.6);
            const k = show(rs, t, t0, { dy: -6 });
            dimK *= 1 - 0.7 * k;
          }
          op.style.opacity = kin * (1 - dimK);
        });
      },
    };
  }
  // countdown ring for "pause and try it": cue = {s, e}
  function countdown(parent, cue, label = 'Pause and try it') {
    const box = el('div', 'countdown', null, parent);
    const cv = el('canvas', '', null, box); cv.width = 150; cv.height = 150; cv.style.width = cv.style.height = '150px';
    const lbl = el('div', 'lbl', '', box); const cap = el('div', 'cap', label, box);
    const g = cv.getContext('2d');
    return {
      el: box,
      update(t) {
        const on = t >= cue.s - 0.2 && t <= cue.e + 0.3;
        box.style.opacity = on ? Math.min(p(t, cue.s - 0.2, 0.3), 1 - p(t, cue.e, 0.3, ease.lin)) : 0;
        if (!on) return;
        const left = clamp(cue.e - t, 0, cue.e - cue.s), frac = left / (cue.e - cue.s);
        g.clearRect(0, 0, 150, 150); g.lineWidth = 9; g.lineCap = 'round';
        g.strokeStyle = '#2a312d'; g.beginPath(); g.arc(75, 75, 62, 0, 7); g.stroke();
        g.strokeStyle = '#e3b35a'; g.beginPath(); g.arc(75, 75, 62, -Math.PI / 2, -Math.PI / 2 + frac * Math.PI * 2); g.stroke();
        lbl.textContent = Math.ceil(left - 1e-6) || '✓';
      },
    };
  }
  // chapter title card (shared look)
  function chapterCard(root, S, n, title, tagline, kicker) {
    const wrap = el('div', 'abs', null, root, { left: '0', right: '0', top: '330px', textAlign: 'center' });
    const a = el('div', 'tag', kicker ?? 'Chapter ' + n, wrap, { color: 'var(--acc)' });
    const b = el('div', 'h-display', title, wrap, { fontSize: '120px', marginTop: '34px' });
    const line = el('div', '', null, wrap, { height: '3px', width: '560px', margin: '34px auto 0', background: 'var(--acc)', transformOrigin: 'center' });
    const c = el('div', 'dim', tagline, wrap, { fontSize: '44px', marginTop: '28px', fontStyle: 'italic' });
    return t => {
      show(a, t, 0.1); show(b, t, 0.35, { dy: 30 }); line.style.transform = `scaleX(${p(t, 0.7, 0.9, ease.inOut)})`;
      show(c, t, 1.0);
    };
  }

  // ---------- timeline / seek ----------
  const scenesEl = document.getElementById('scenes');
  const subsEl = document.querySelector('#subs span');
  const chapEl = document.getElementById('chap');
  const fill = document.getElementById('prog-fill');
  const CH = TL.chapters;
  // chapter ticks on progress bar
  const prog = document.getElementById('prog');
  let lastCh = 0;
  TL.scenes.forEach(s => { if (s.chapter !== lastCh) { lastCh = s.chapter; el('i', '', null, prog, { left: (s.start / TL.total * 100) + '%' }); } });

  function build(sc) {
    if (built[sc.id]) return built[sc.id];
    const root = el('div', 'scene', null, scenesEl);
    root.dataset.id = sc.id;
    const S = {
      sc, root, dur: sc.dur, cues: sc.cues,
      at: id => { if (!sc.cues[id]) throw new Error(`${sc.id}: no cue ${id}`); return sc.cues[id].s; },
      end: id => sc.cues[id].e,
      el, tex, txt, rich, p, show, wipe, pulse, ease, clamp, lerp, hash, fmt,
      fig: o => fig(root, o), header: (k, c) => header(root, k, c),
      deriv: (lines, st) => deriv(root, lines, st), mcq: (o, st) => mcq(root, o, st),
      countdown: (cueId, label) => countdown(root, sc.cues[cueId], label),
      chapterCard: (n, ti, tg, kicker) => chapterCard(root, S, n, ti, tg, kicker),
    };
    const fn = registry[sc.id];
    let update = () => {};
    if (fn) update = fn(root, S) || update;
    else el('div', 'dim', `[scene ${sc.id} not built]`, root, { fontSize: '50px' });
    return (built[sc.id] = { root, update });
  }

  let shown = new Set();
  window.seek = function (t) {
    t = clamp(t, 0, TL.total - 1e-3);
    let idx = TL.scenes.findIndex(s => t >= s.start && t < s.start + s.dur);
    // a rounding gap between scenes (start + dur a millisecond short of the next start) belongs to the earlier scene
    if (idx < 0) idx = Math.max(0, TL.scenes.findLastIndex(s => s.start <= t));
    const cur = TL.scenes[idx], prev = TL.scenes[idx - 1];
    const active = [[cur, 1]];
    const lt = t - cur.start;
    if (prev && lt < FADE) active.unshift([prev, 1 - lt / FADE]);
    const keep = new Set();
    for (const [s, a] of active) {
      const b = build(s);
      b.root.style.display = 'block';
      b.root.style.opacity = s === cur ? Math.min(1, lt / FADE + (prev ? 0 : 1)) : a;
      b.update(t - s.start);
      keep.add(s.id);
    }
    for (const id of shown) if (!keep.has(id)) built[id].root.style.display = 'none';
    shown = keep;
    // chrome
    chapEl.innerHTML = cur.chapter ? CH[cur.chapter].replace(/^([^·]+)/, '<b>$1</b>') : '';
    chapEl.style.opacity = cur.chapter ? 1 : 0;
    fill.style.width = (t / TL.total * 100) + '%';
    // subtitles
    const sub = cur.subs.find(x => lt >= x.s - 0.05 && lt <= x.e + 0.35);
    if (sub) { subsEl.innerHTML = rich(sub.text); subsEl.style.opacity = 1; } else subsEl.style.opacity = 0;
    return idx;
  };
  window.TOTAL = TL.total;
  window.ENGINE_READY = (async () => {
    await document.fonts.ready;
    await Promise.all(['400 30px "Crimson Pro"', '600 30px "Playfair Display"', '30px "Patrick Hand"', '500 30px "Crimson Pro"'].map(f => document.fonts.load(f)));
    // preload every KaTeX face before any scene is built (layouts measured at build time depend on them)
    const probe = document.createElement('div');
    probe.style.cssText = 'position:absolute;left:-9999px;top:0;visibility:hidden';
    probe.innerHTML = katex.renderToString('\\vec F=\\dfrac{1}{2}\\sqrt{x^2}\\int_0^1\\sum\\mathrm{m}\\,\\mathbb R\\left(\\dfrac{a}{b}\\right)\\hat r\\langle 1,2\\rangle\\boxed{\\theta}\\text{ab}\\mathbf{v}', { throwOnError: false });
    document.body.appendChild(probe);
    await Promise.all(['20px KaTeX_Main', 'italic 20px KaTeX_Main', 'bold 20px KaTeX_Main', 'italic 20px KaTeX_Math', '20px KaTeX_Size1', '20px KaTeX_Size2', '20px KaTeX_Size3', '20px KaTeX_Size4', '20px KaTeX_AMS'].map(f => document.fonts.load(f).catch(() => {})));
    await document.fonts.ready;
    window.ENGINE_OK = true;
  })();
})();
