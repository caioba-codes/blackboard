/* Lesson video: a lesson's narrated video beside the board, kept in step with the text.
   Mounted only when the bridge reports a manifest for this lesson (/api/lesson-video); a lesson without one gets
   nothing from this file. The board calls LessonVideo.refresh(ctx) after every render (first load, append, rebuild).
   Playback position, speed and view live in this browser only: never learning records, answers or XP.

   Views: Read (the board as always), Watch (the video alone, with its list of explanations), Both (video fixed on the
   left and the text on the right on wide screens; video stuck above the text on narrow ones).

   Segment `step` (1-based) never reveals anything by itself: in a check-in answer opened after the practice gate it
   advances the step-by-step reveal to that step (never backwards); otherwise it marks that row of the block's single
   aligned derivation when the row is already on screen. Anything put inside a lesson block is textless and appended
   last, so block text signatures (definitions, pending Explain notes, place restore) never change.

   Captions: the video frames carry no captions; the player overlays the caption track installed beside the MP4
   (NNNN-lecture.captions.json, the narration in the lesson's notation with KaTeX math), synced to the video's time.
   CC turns them on or off (remembered in this browser). A video rendered with its captions burned in
   (captionsBurnedIn) starts with CC off; turned on, an opaque band hides the burned caption box under the overlay. A track that says
   progressBarBurnedIn hides the old in-frame progress strip at the bottom of the picture.

   LessonVideo.context(): what the reader is looking at in the video, for the chat (null until the video is played or
   seeked on this page); a `lessonvideo:context` event on window carries the same object whenever it changes. */
(function(){
'use strict';
const SPEEDS=[.5,.75,1,1.25,1.5,2], SKIP=10, WIDE=1080, TOPBAR=70;
const root=document.documentElement, reduced=matchMedia('(prefers-reduced-motion: reduce)');
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const num=x=>typeof x==='number'&&isFinite(x);
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function fmt(t){ t=Math.max(0,Math.floor(t||0)); const h=Math.floor(t/3600), m=Math.floor(t%3600/60), s=t%60; return (h?h+':'+String(m).padStart(2,'0'):m)+':'+String(s).padStart(2,'0'); }
const svg=(d,extra)=>`<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"${extra||''}>${d}</svg>`;
const STROKE=' fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"';
const I={
  play:svg('<path d="M5 3.1v9.8L12.8 8z" fill="currentColor"/>'),
  pause:svg('<path d="M4.4 3h2.5v10H4.4zM9.1 3h2.5v10H9.1z" fill="currentColor"/>'),
  back:svg('<path d="M3.4 8.6A4.8 4.8 0 1 0 5 4.6"/><path d="M5.6 2.2 4.6 4.8l2.7.6"/><text x="8.2" y="10.4" font-size="5" text-anchor="middle" fill="currentColor" stroke="none" font-family="inherit">10</text>',STROKE),
  fwd:svg('<path d="M12.6 8.6A4.8 4.8 0 1 1 11 4.6"/><path d="M10.4 2.2l1 2.6-2.7.6"/><text x="7.8" y="10.4" font-size="5" text-anchor="middle" fill="currentColor" stroke="none" font-family="inherit">10</text>',STROKE),
  prev:svg('<path d="M3.6 3.2v9.6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M12.6 3.4 5.6 8l7 4.6z" fill="currentColor"/>'),
  next:svg('<path d="M12.4 3.2v9.6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M3.4 3.4 10.4 8l-7 4.6z" fill="currentColor"/>'),
  fs:svg('<path d="M2.8 6V2.8H6M10 2.8h3.2V6M13.2 10v3.2H10M6 13.2H2.8V10"/>',STROKE),
  fsx:svg('<path d="M6 2.8V6H2.8M13.2 6H10V2.8M10 13.2V10h3.2M2.8 10H6v3.2"/>',STROKE),
  more:svg('<circle cx="3.5" cy="8" r="1.3" fill="currentColor"/><circle cx="8" cy="8" r="1.3" fill="currentColor"/><circle cx="12.5" cy="8" r="1.3" fill="currentColor"/>'),
  read:svg('<path d="M2.5 3.5c2-.6 3.9-.4 5.5.8 1.6-1.2 3.5-1.4 5.5-.8v9c-2-.6-3.9-.4-5.5.8-1.6-1.2-3.5-1.4-5.5-.8z"/><path d="M8 4.3v9"/>',STROKE),
  watch:svg('<rect x="1.8" y="3.2" width="12.4" height="9.6" rx="1.6"/><path d="M6.6 6v4l3.4-2z" fill="currentColor" stroke="none"/>',STROKE),
  both:svg('<rect x="1.8" y="3.2" width="12.4" height="9.6" rx="1.6"/><path d="M8.2 3.2v9.6"/><path d="M3.8 6.4v3.2l2.5-1.6z" fill="currentColor" stroke="none"/><path d="M10 6.2h2.4M10 8h2.4M10 9.8h1.6"/>',STROKE),
  cc:svg('<rect x="1.6" y="3.4" width="12.8" height="9.2" rx="1.8" fill="none" stroke="currentColor" stroke-width="1.4"/><text x="8" y="10.4" font-size="5.4" font-weight="700" text-anchor="middle" fill="currentColor" font-family="inherit">CC</text>'),
  wfh:svg('<circle cx="8" cy="8" r="6.4" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M6.5 5.3v5.4L10.9 8z" fill="currentColor"/>')
};
let ctx=null, S=null, probe=null;

// ---------- manifest ----------
function apiUrl(){ return `/api/lesson-video?id=${encodeURIComponent(ctx.lessonId)}${ctx.ws?'&ws='+encodeURIComponent(ctx.ws):''}`; }
function fetchManifest(){ return fetch(apiUrl(),{cache:'no-store'}).then(r=>r.ok?r.json():null).catch(()=>null); }
// the bridge validates the manifest; this only refuses anything the player could not use safely
function usable(m){
  if(!m||m.available!==true||typeof m.videoUrl!=='string'||!m.videoUrl.startsWith('/')||!num(m.duration)||m.duration<=0||!Array.isArray(m.segments)||!m.segments.length)return false;
  let prev=0;
  return m.segments.every(s=>{
    const p=s&&s.practice;
    const ok=!!s&&typeof s.id==='string'&&typeof s.label==='string'&&num(s.start)&&num(s.end)&&s.start>=prev-1e-6&&s.end>s.start&&Number.isInteger(s.line)
      &&(!p||(num(p.pauseAt)&&num(p.revealAt)&&p.pauseAt>=s.start&&p.revealAt>p.pauseAt&&p.revealAt<=s.end+1e-6));
    if(ok)prev=s.end; return ok;
  });
}
function refresh(c){
  if(!c||!c.main||!c.lessonId)return;
  ctx=c;
  if(!probe)probe=fetchManifest().then(m=>{ if(usable(m))mount(m); });
  // a rebuilt lesson may no longer match the video: ask again whether the map still holds
  else if(S&&c.reset&&!c.first)fetchManifest().then(m=>{ if(S)setSync(!!(m&&m.available&&m.mappingValid)); });
  probe.then(()=>{ if(S)decorate(); });
}

// ---------- state ----------
function load(){ try{ return JSON.parse(localStorage.getItem(S.key)||'null')||{}; }catch(_){ return {}; } }
function save(){
  if(!S)return; S.saveAt=performance.now();
  const t=S.gate?S.gate.p.pauseAt:cur();
  try{ localStorage.setItem(S.key,JSON.stringify({mode:S.mode,t:Math.round(t*100)/100,rate:S.rate,loop:S.loop,muted:S.video.muted})); }catch(_){}
}
function persistSoon(){ if(performance.now()-S.saveAt>2000)save(); }
const cur=()=>S.meta?S.video.currentTime:S.pendingT;
function segAt(t){ const a=S.segs; let lo=0,hi=a.length-1,ans=0; while(lo<=hi){ const m=(lo+hi)>>1; if(a[m].start<=t+1e-3){ans=m;lo=m+1;} else hi=m-1; } return ans; }

function mount(m){
  const segs=m.segments.map((s,i)=>({id:s.id,label:s.label,start:s.start,end:s.end,line:s.line,step:Number.isInteger(s.step)&&s.step>0?s.step:null,p:s.practice||null,i}));
  S={m,segs,prac:segs.filter(s=>s.p),dur:m.duration,key:`bb-video:v1:${ctx.ws||''}:${ctx.lessonId}:${String(m.lessonSha256||m.version||'').slice(0,12)}`,
    mode:'read',sync:!!m.mappingValid,follow:false,detach:'mode',i:-1,targets:[],first:new Map(),
    armed:new Set(),granted:new Set(),gate:null,ended:false,err:false,errMsg:'',src:false,meta:false,pendingT:0,prevT:0,
    scrub:false,scrubT:0,scrubRaf:0,loop:false,rate:1,raf:0,saveAt:0,readY:0,ignoreUntil:0,autoY:0,waitT:0,lastSec:-1,
    menuOpen:false,introVis:true,band:null,intro:null,io:null,opened:new Map()};
  S.prac.forEach(s=>S.armed.add(s.id));
  const saved=load();
  S.rate=SPEEDS.includes(saved.rate)?saved.rate:1; S.loop=!!saved.loop;
  S.pendingT=num(saved.t)?clamp(saved.t,0,Math.max(0,S.dur-.5)):0; S.prevT=S.pendingT;
  build(); S.video.muted=!!saved.muted;
  root.classList.add('lv-on');
  wire();
  setMode(['read','watch','both'].includes(saved.mode)?saved.mode:'read',{init:true});
  paintTime(S.pendingT,true); setSeg(segAt(S.pendingT),'init'); paintPlay(); paintMenu(); paintCards(); paintFoot();
  loadCaptions();
}

// ---------- captions: an overlay in the lesson's notation, synced to the video ----------
const CC_KEY=burned=>burned?'bb-video:cc-burned':'bb-video:cc';
function capsUrl(u){ return u.replace(/\.mp4(?=$|[?#])/i,'.captions.json'); }
function usableCaps(d){
  if(!d||!Array.isArray(d.cues)||!d.cues.length)return null;
  const cues=d.cues.filter(c=>c&&num(c.s)&&num(c.e)&&c.e>c.s&&typeof c.text==='string'&&c.text.trim()).sort((a,b)=>a.s-b.s);
  return cues.length?cues:null;
}
function loadCaptions(){
  return fetch(capsUrl(S.m.videoUrl),{cache:'no-store'}).then(r=>r.ok?r.json():null).catch(()=>null).then(d=>{
    const cues=usableCaps(d); if(!S||!cues)return;
    S.caps=cues; S.barBurned=d.progressBarBurnedIn===true;
    let on=null; try{ on=localStorage.getItem(CC_KEY(S.m.captionsBurnedIn)); }catch(_){}
    S.cc=on===null?!S.m.captionsBurnedIn:on==='1';
    S.ccBtn.hidden=false; S.mask.hidden=!S.barBurned;
    fitCaptions(); paintCC(cur(),true);
  });
}
// the caption at time t: the same window the renderer used for burned captions (0.05 s early, 0.35 s late)
function capAt(t){
  const a=S.caps; if(!a)return null; let lo=0,hi=a.length-1,k=-1;
  while(lo<=hi){ const m=(lo+hi)>>1; if(a[m].s-.05<=t){k=m;lo=m+1;} else hi=m-1; }
  for(let j=k;j>=0&&j>k-3;j--)if(t<=a[j].e+.35)return a[j];
  return null;
}
// text with $inline$ math rendered by the board's KaTeX; plain text escaped
function capHtml(s){
  const K=window.katex; let out='', last=0; const re=/\$\$([\s\S]+?)\$\$|\$([^$]+?)\$/g; let m;
  while((m=re.exec(s))){ out+=esc(s.slice(last,m.index)); const tex=m[1]||m[2];
    try{ out+=K?K.renderToString(tex,{displayMode:false,throwOnError:false,strict:false}):esc(tex); }catch(_){ out+=esc(tex); }
    last=re.lastIndex; }
  return out+esc(s.slice(last));
}
function paintCC(t,force){
  if(!S||!S.capEl)return;
  const c=S.cc&&S.caps?capAt(t):null;
  if(c===S.capCur&&!force)return;
  S.capCur=c;
  // over burned-in captions an opaque band hides the burned box while the overlay shows (the text itself rises above
  // the control bar like any caption)
  S.capEl.hidden=!c; S.band2.hidden=!(c&&S.m.captionsBurnedIn);
  S.capText.innerHTML=c?capHtml(c.text):'';
}
function setCC(on){
  S.cc=!!on; try{ localStorage.setItem(CC_KEY(S.m.captionsBurnedIn),S.cc?'1':'0'); }catch(_){}
  paintCCBtn(); paintCC(cur(),true); say(S.cc?'Captions on':'Captions off');
}
function paintCCBtn(){ if(!S.ccBtn)return; S.ccBtn.setAttribute('aria-pressed',String(!!S.cc)); const l=S.cc?'Turn captions off':'Turn captions on'; S.ccBtn.setAttribute('aria-label',l); S.ccBtn.title=l+' (C)'; }
// the picture inside the stage (object-fit: contain): captions and the progress-strip mask are placed on it
function fitCaptions(){
  if(!S||!S.stage)return;
  const w=S.stage.clientWidth, h=S.stage.clientHeight; if(!w||!h)return;
  const vw=S.video.videoWidth||16, vh=S.video.videoHeight||9, k=Math.min(w/vw,h/vh), cw=vw*k, ch=vh*k;
  const st=S.stage.style;
  st.setProperty('--lv-cw',cw.toFixed(1)+'px'); st.setProperty('--lv-ch',ch.toFixed(1)+'px');
  st.setProperty('--lv-cx',((w-cw)/2).toFixed(1)+'px'); st.setProperty('--lv-cy',((h-ch)/2).toFixed(1)+'px');
  st.setProperty('--lv-barh',(S.bar.offsetHeight||0)+'px');
  paintCCBtn();
}

// ---------- context for the chat: what the reader is looking at in the video ----------
function sectionAt(line){
  let best=null;
  ctx.main.querySelectorAll('.blk[data-line] h2, .blk[data-line] h3').forEach(h=>{
    const b=h.closest('.blk[data-line]'); if(!b||h.closest('.fold,.quiz,.mcqi,details'))return;
    if(+b.dataset.line<=line&&(!best||+b.dataset.line>=best.l))best={l:+b.dataset.line,h};
  });
  if(!best)return null;
  const c=best.h.cloneNode(true); c.querySelectorAll('.tag,.katex-mathml,.chalkdeco,.flagbtn,.lv-wfh').forEach(x=>x.remove());
  return {id:best.h.id||null,heading:c.textContent.replace(/\s+/g,' ').trim()};
}
function context(){
  if(!S||!S.touched)return null;
  const t=S.gate?S.gate.p.pauseAt:cur(), s=S.segs[segAt(t)], c=S.caps?capAt(t):null;
  const g=S.gate||(s&&s.p&&t<s.p.revealAt&&!S.granted.has(s.id)?s:null);
  return {t:Math.round(t*100)/100,time:fmt(t),chapter:(S.chaps[chapAt(t)]||{}).title||'',segment:s?s.label:'',
    line:s?s.line:null,section:s&&S.sync?sectionAt(s.line):null,caption:c?c.text:null,
    paused:S.video.paused||!!S.gate||S.ended,practice:g?{label:g.label,revealed:false}:null};
}
function emit(){
  if(!S||!S.touched)return;
  clearTimeout(S.emitT);
  S.emitT=setTimeout(()=>{ try{ window.dispatchEvent(new CustomEvent('lessonvideo:context',{detail:context()})); }catch(_){} },60);
}

// ---------- DOM ----------
function modesHtml(cls,labels){
  return `<div class="lv-modes ${cls}" role="radiogroup" aria-label="Lesson view">${[['read','Read',I.read,'Read the lesson'],['watch','Watch',I.watch,'Watch the video'],['both','Both',I.both,'Video beside the text']]
    .map(([k,l,ic,t])=>`<button type="button" role="radio" data-mode="${k}" aria-checked="false" tabindex="-1" title="${t}"${labels?'':` aria-label="${l}"`}>${ic}${labels?`<span>${l}</span>`:''}</button>`).join('')}</div>`;
}
function build(){
  const p=document.createElement('section'); p.id='lvpanel'; p.className='lv-panel'; p.setAttribute('aria-label','Video lesson'); p.tabIndex=-1; p.hidden=true;
  // minimal, like a streaming player: the controls sit on the video and fade while it plays; the rest lives in More
  p.innerHTML=`<div class="lv-stage" tabindex="-1"><video playsinline preload="metadata" aria-label="Lesson video"></video>
<button type="button" class="lv-big" data-a="play" tabindex="-1" aria-hidden="true">${I.play}</button>
<div class="lv-mask" hidden aria-hidden="true"></div>
<div class="lv-ccband" hidden aria-hidden="true"></div>
<div class="lv-cc" hidden aria-hidden="true"><span class="lv-cct"></span></div>
<div class="lv-spin" hidden aria-hidden="true"></div>
<div class="lv-card lv-gate" role="group" aria-label="Your turn" hidden><p class="lv-ck">Your turn</p><p class="lv-ct">Pause here and work it out. The answer comes next.</p><div class="lv-cb"><button type="button" class="lv-btn pri" data-a="continue">Continue to the answer</button><button type="button" class="lv-btn" data-a="replayq">Replay the question</button></div></div>
<div class="lv-card lv-err" role="alert" hidden><p class="lv-ck">Video unavailable</p><p class="lv-ct lv-errt"></p><div class="lv-cb"><button type="button" class="lv-btn pri" data-a="retry">Try again</button><button type="button" class="lv-btn" data-a="toread">Read the lesson</button></div></div>
<div class="lv-card lv-end" hidden><p class="lv-ck">End of the video</p><div class="lv-cb"><button type="button" class="lv-btn pri" data-a="restart">Watch again</button><button type="button" class="lv-btn" data-a="toread">Back to the lesson</button></div></div>
<div class="lv-bar"><div class="lv-tl"><div class="lv-zones" aria-hidden="true"></div><input type="range" class="lv-range" min="0" max="${S.dur}" step="0.1" value="0" aria-label="Video position"><div class="lv-tip" hidden aria-hidden="true"><b class="lv-tipc"></b><span class="lv-tipt"></span></div></div>
<div class="lv-ctl"><button type="button" class="lv-ib lv-play" data-a="play" aria-label="Play" title="Play (Space)">${I.play}</button>
<span class="lv-time"><span class="lv-el">0:00</span><span class="lv-du"> / ${fmt(S.dur)}</span><span class="lv-ch"></span></span>
<button type="button" class="lv-chip lv-follow" data-a="follow" hidden title="Scroll the text back to what the video is saying">Follow</button>
<label class="lv-speed" title="Playback speed (Shift+&lt; and Shift+&gt;)"><span class="lv-sr">Playback speed</span><select>${SPEEDS.map(r=>`<option value="${r}">${r}×</option>`).join('')}</select></label>
<div class="lv-more"><button type="button" class="lv-ib" data-a="more" aria-label="More video options" aria-expanded="false" aria-controls="lvmenu" title="More">${I.more}</button>
<div class="lv-menu" id="lvmenu" hidden><button type="button" data-a="back">Back 10 seconds<kbd>←</kbd></button><button type="button" data-a="fwd">Forward 10 seconds<kbd>→</kbd></button><button type="button" data-a="prev">Previous explanation<kbd>⇧←</kbd></button><button type="button" data-a="next">Next explanation<kbd>⇧→</kbd></button><button type="button" data-a="replay">Replay this explanation<kbd>R</kbd></button><button type="button" data-a="loop" aria-pressed="false">Loop this explanation</button><button type="button" data-a="mute" aria-pressed="false">Mute</button><button type="button" data-a="pip" hidden>Picture in picture</button><button type="button" data-a="read">Read from here</button></div></div>
<button type="button" class="lv-ib lv-ccb" data-a="cc" aria-pressed="false" aria-label="Turn captions on" title="Captions (C)" hidden>${I.cc}</button>
<button type="button" class="lv-ib" data-a="fs" aria-label="Full screen" title="Full screen (F)">${I.fs}</button></div></div>
</div>
<ol class="lv-list" aria-label="Explanations in this video">${S.segs.map(s=>`<li><button type="button" data-a="seg" data-i="${s.i}"><span class="lv-lt">${fmt(s.start)}</span><span class="lv-ll">${esc(s.label)}</span>${s.p?'<span class="lv-tag">Your turn</span>':''}</button></li>`).join('')}</ol>
<div class="lv-sr lv-live" aria-live="polite"></div>`;
  document.body.insertBefore(p,ctx.main);
  const q=s=>p.querySelector(s);
  Object.assign(S,{panel:p,video:q('video'),stage:q('.lv-stage'),big:q('.lv-big'),spin:q('.lv-spin'),gateEl:q('.lv-gate'),errEl:q('.lv-err'),endEl:q('.lv-end'),
    bar:q('.lv-bar'),range:q('.lv-range'),tip:q('.lv-tip'),tl:q('.lv-tl'),zones:q('.lv-zones'),chEl:q('.lv-ch'),playBtn:q('.lv-play'),el:q('.lv-el'),speed:q('.lv-speed select'),moreBtn:q('[data-a="more"]'),menu:q('.lv-menu'),
    fsBtn:q('[data-a="fs"]'),prevBtn:q('[data-a="prev"]'),nextBtn:q('[data-a="next"]'),readBtn:q('[data-a="read"]'),followBtn:q('.lv-follow'),
    list:q('.lv-list'),live:q('.lv-live'),gateBtn:q('[data-a="continue"]'),capEl:q('.lv-cc'),band2:q('.lv-ccband'),capText:q('.lv-cct'),ccBtn:q('.lv-ccb'),mask:q('.lv-mask')});
  S.speed.value=String(S.rate);
  if(!(document.pictureInPictureEnabled&&!S.video.disablePictureInPicture))q('[data-a="pip"]').remove(); else q('[data-a="pip"]').hidden=false;
  buildZones();
  // the same switch, compact, in the top bar: shown whenever the one in the lesson header is off screen
  const top=document.createElement('div'); top.innerHTML=modesHtml('lv-topmodes',false); S.top=top.firstElementChild; S.top.hidden=true;
  const zoom=document.getElementById('zoomctl'), bar=document.getElementById('topbar');
  if(zoom)zoom.after(S.top); else if(bar)bar.prepend(S.top);
}

// ---------- chapters: the seek bar's zones ----------
// One zone per lesson chapter (each `## ` heading of the lesson source), like a video site's chapter markers. A segment
// belongs to the chapter whose heading is the last one at or above its line, or to the chapter its label names
// ("Chapter 3 card", "Practice exam intro", "Quiz 1: …"): a map made from an older lesson keeps working when the lines
// have drifted. Chapters never go back in time (a recap pointing at its chapter's heading stays where it is), and a
// jump forward needs a label or two segments in a row that agree. Segments before the first heading are the
// introduction. Without the lesson source the bar is one zone.
function headingsOf(src){
  const out=[]; let fence=null;
  (typeof src==='string'?src.split('\n'):[]).forEach((t,k)=>{
    const f=t.match(/^\s*(```|~~~)/); if(f){ fence=fence===null?f[1]:fence===f[1]?null:fence; return; }
    if(fence!==null)return;
    const m=t.match(/^##[ \t]+(.+?)[ \t#]*$/); if(!m)return;
    const title=m[1].replace(/\s*\{#[^}]*\}\s*$/,'').replace(/[*_`]/g,'').replace(/\[([^\]]*)\]\([^)]*\)/g,'$1').trim();
    if(!title)return;
    const n=title.match(/^chapter\s+(\d+)\b/i), tail=title.split(/\s+[·:—–-]\s+/).slice(1).join(' · ');
    out.push({line:k+1,title,n:n?n[1]:null,tail:tail.toLowerCase(),full:title.toLowerCase()});
  });
  return out;
}
function chaptersOf(segs,src){
  const hs=headingsOf(src);
  if(!hs.length||!segs.length)return [{title:'',i0:0}];
  const starts=(l,t)=>l.startsWith(t)&&!/[a-z0-9]/.test(l.charAt(t.length));
  const byLabel=s=>{ const l=s.label.trim().toLowerCase(); for(let k=hs.length-1;k>=0;k--){ const h=hs[k];
    if(h.n&&new RegExp('^chapter\\s+'+h.n+'\\b').test(l))return k;
    if((h.tail.length>=4&&starts(l,h.tail))||starts(l,h.full))return k; } return -2; };
  const byLine=s=>{ let a=-1; hs.forEach((h,k)=>{ if(h.line<=s.line)a=k; }); return a; };
  // a label counts only next to its heading (at most one chapter early), so a generic title cannot pull a zone far forward
  const raw=segs.map(s=>{ const k=byLabel(s), b=byLine(s); return k>-2&&b>=k-1?{k,lab:true}:{k:b,lab:false}; });
  const of=[]; let cur=raw[0].k;
  raw.forEach((r,i)=>{
    if(r.k>cur&&(r.lab||i===raw.length-1||raw[i+1].k>=r.k))cur=r.k;
    of.push(cur);
  });
  const out=[];
  of.forEach((k,i)=>{ if(!out.length||out[out.length-1].k!==k)out.push({k,title:k<0?'Introduction':hs[k].title,i0:i}); });
  return out.map(({title,i0})=>({title,i0}));
}
function buildZones(){
  S.srcSeen=ctx.src;
  S.chaps=chaptersOf(S.segs,ctx.src).map((c,j,a)=>({title:c.title,start:j?S.segs[c.i0].start:0,end:j<a.length-1?S.segs[a[j+1].i0].start:S.dur}));
  S.zones.innerHTML=S.chaps.map((c,j)=>{ const zs=c.start/S.dur*100, zw=Math.max(.0001,(c.end-c.start)/S.dur*100);
    return `<div class="lv-z${j?'':' first'}${j===S.chaps.length-1?' last':''}" style="left:${zs.toFixed(4)}%;width:${zw.toFixed(4)}%;--zs:${zs.toFixed(4)};--zw:${zw.toFixed(4)}"><i></i></div>`; }).join('');
  S.chapI=-1; S.hoverZ=-1;
  if(S.el)paintTime(cur(),true);
}
function chapAt(t){ const a=S.chaps; let j=0; while(j<a.length-1&&a[j+1].start<=t+1e-3)j++; return j; }
function buildIntro(){
  const el=document.createElement('div'); el.className='lv-intro'; el.setAttribute('role','group'); el.setAttribute('aria-label','Video lesson');
  el.innerHTML=`<span class="lv-ic" aria-hidden="true">${I.play}</span><div class="lv-itx"><b>Video lesson</b><span class="lv-imeta">${fmt(S.dur)}${S.m.captionsBurnedIn?' · captions in the video':''}</span><span class="lv-ist" hidden></span></div>${modesHtml('lv-imodes',true)}`;
  return el;
}

// ---------- lesson decoration (every render) ----------
function decorate(){
  const main=ctx.main; if(!main)return;
  if(ctx.src!==S.srcSeen)buildZones();
  intro();
  const blks=[...main.querySelectorAll('.blk[data-line]')].filter(b=>!b.parentElement.closest('.blk')).map(b=>({b,line:+b.dataset.line})).sort((a,b)=>a.line-b.line);
  const title=main.querySelector('#title'), last=blks.length?blks[blks.length-1].line:0;
  // a segment points at the greatest rendered block line <= its source line; lines before the first block are the title
  const src=typeof ctx.src==='string'?ctx.src.split('\n'):null;
  S.targets=S.segs.map(s=>{
    if(ctx.streaming&&s.line>last)return null;   // not written yet
    let lo=0,hi=blks.length-1,ans=-1; while(lo<=hi){ const m=(lo+hi)>>1; if(blks[m].line<=s.line){ans=m;lo=m+1;} else hi=m-1; }
    return ans<0?title:(nested(blks[ans],s.line,src)||blks[ans].b);
  });
  S.first=new Map();
  if(S.sync)S.targets.forEach((b,i)=>{ if(isAnchor(b)&&!S.first.has(b))S.first.set(b,i); });
  main.querySelectorAll('.lv-wfh').forEach(btn=>{ if(S.first.get(btn.parentElement)!==+btn.dataset.seg)btn.remove(); });
  S.first.forEach((i,b)=>{
    if(b.querySelector(':scope>.lv-wfh'))return;
    const s=S.segs[i], btn=document.createElement('button');
    btn.type='button'; btn.className='lv-wfh'; btn.dataset.seg=String(i); btn.innerHTML=I.wfh;
    btn.setAttribute('aria-label',`Watch from here: ${s.label}, at ${fmt(s.start)}`); btn.title=`Watch from here · ${fmt(s.start)}`;
    b.appendChild(btn);
  });
  paintHighlight(); applyStep(S.i);
  // the board may have just restored the reader's place: that scroll is not the reader leaving the video
  S.ignoreUntil=performance.now()+400; S.autoY=window.scrollY;
}
// A container block (::: quiz) renders several questions from one source block: a cue line inside a `::: mcq <item>`
// points at that question, found by its item id, not at the top of the whole block. Needs the lesson source text.
function nested(e,line,src){
  if(!src||line<=e.line||e.b.querySelectorAll('.mcqi[data-item]').length<1)return null;
  for(let k=line;k>e.line;k--){
    const t=src[k-1]; if(t===undefined)return null;
    if(k<line&&/^:::\s*$/.test(t))return null;   // the cue sits after a closed container, not inside it
    const m=t.match(/^::: mcq\s+(\S+)/);
    if(m){ const q=[...e.b.querySelectorAll('.mcqi[data-item]')].find(x=>x.dataset.item===m[1]); return q||null; }
  }
  return null;
}
const isAnchor=el=>!!el&&el.nodeType===1&&el.matches('.blk,.mcqi');
function intro(){
  const main=ctx.main;
  if(!S.intro)S.intro=buildIntro();
  if(S.intro.parentElement!==main){
    const head=[...main.children].filter(c=>c.matches('.top,.hero,p.credit:not(.imgcredits),#title,.byline')).pop();
    if(head)head.after(S.intro); else main.prepend(S.intro);
    if('IntersectionObserver' in window){
      if(!S.io)S.io=new IntersectionObserver(es=>{ S.introVis=es[es.length-1].isIntersecting; paintTopModes(); },{rootMargin:`-${TOPBAR}px 0px 0px 0px`});
      S.io.disconnect(); S.io.observe(S.intro);
    }
  }
  paintModes(); paintIntro();
}
function setSync(v){ if(S.sync===v)return; S.sync=v; if(!v){ S.follow=false; } decorate(); paintFoot(); paintIntro(); }

// ---------- views ----------
function placeAnchor(){ const b=[...ctx.main.querySelectorAll('.blk')].find(x=>x.getBoundingClientRect().bottom>TOPBAR+10); return b?{el:b,top:b.getBoundingClientRect().top}:null; }
function restoreAnchor(a){ if(a&&a.el.isConnected){ const dy=a.el.getBoundingClientRect().top-a.top; if(Math.abs(dy)>1)window.scrollTo(0,window.scrollY+dy); } }
function inView(b){ const r=b.getBoundingClientRect(), top=topOffset(); return r.bottom>top+20&&r.top<innerHeight-40; }
function setMode(mode,o={}){
  const prev=S.mode;
  if(!o.init&&mode===prev){ paintModes(); return; }
  const anchor=!o.init&&prev!=='watch'?placeAnchor():null;
  if(!o.init&&prev!=='watch')S.readY=window.scrollY;
  S.mode=mode;
  root.classList.toggle('lv-watch',mode==='watch'); root.classList.toggle('lv-both',mode==='both');
  S.panel.hidden=mode==='read';
  if(mode==='read'){ if(!S.video.paused)S.video.pause(); closeMenu(); exitFs(); }
  else { ensureSrc(); if(S.err)retry(); }
  layout(); paintModes(); paintHighlight(); paintCards();
  S.ignoreUntil=performance.now()+500;
  const tgt=S.sync?S.targets[S.i]:null;
  if(o.init){ S.follow=false; S.detach='mode'; }   // after a reload the text stays put until Play
  else if(mode==='watch')window.scrollTo(0,0);
  else if(mode==='both'&&prev==='watch'){ if(tgt){ attach(); snapTo(tgt,false); } else window.scrollTo(0,S.readY); }
  else if(mode==='both'){ restoreAnchor(anchor); if(tgt&&inView(tgt)){ S.follow=true; S.detach=''; } else { S.follow=false; S.detach='mode'; } }
  else if(prev==='watch')window.scrollTo(0,S.readY);
  else restoreAnchor(anchor);
  S.autoY=window.scrollY; applyStep(S.i); paintFoot(); paintIntro();
  if(!o.init&&o.persist!==false)save();
}
function layout(){
  const cw=parseFloat(getComputedStyle(root).getPropertyValue('--chatw'))||0, avail=innerWidth-cw;
  const side=S.mode==='both'&&avail>=WIDE;
  root.classList.toggle('lv-side',side); root.classList.toggle('lv-stack',S.mode==='both'&&!side);
  if(side)root.style.setProperty('--lvw',Math.round(clamp(Math.min(avail-780,(innerHeight-270)*16/9),360,760))+'px');
  // Watch: the video as large as the window allows, its list of explanations beside it when there is room
  const wide=S.mode==='watch'&&avail>=1100; root.classList.toggle('lv-wwide',wide);
  if(S.mode==='watch')root.style.setProperty('--lvtw',Math.round(clamp(Math.min(1120,avail-(wide?380:32),(innerHeight-(wide?250:300))*16/9),260,1120))+'px');
}
function topOffset(){ return S.mode==='both'&&root.classList.contains('lv-stack')?TOPBAR+S.panel.offsetHeight+12:TOPBAR+14; }
function paintModes(){
  document.querySelectorAll('.lv-modes [data-mode]').forEach(b=>{ const on=b.dataset.mode===S.mode; b.setAttribute('aria-checked',String(on)); b.tabIndex=on?0:-1; });
  paintTopModes();
}
function paintTopModes(){ if(S.top)S.top.hidden=S.mode!=='watch'&&S.introVis&&!!S.intro&&S.intro.isConnected; }
function paintIntro(){
  if(!S.intro)return;
  const st=S.intro.querySelector('.lv-ist'), t=cur(); let msg='';
  if(S.err)msg='The video could not be played. Choose Watch to try again.';
  else if(!S.sync)msg='The lesson changed after this video was made, so the video plays without following the text.';
  else if(t>5&&t<S.dur-5)msg=`Resume at ${fmt(t)}`;
  st.textContent=msg; st.hidden=!msg; st.classList.toggle('warn',S.err||!S.sync);
}

// ---------- following the text ----------
function attach(){ S.follow=true; S.detach=''; paintFoot(); }
function detach(why){ if(!S.follow&&S.detach===why)return; S.follow=false; S.detach=why; paintFoot(); }
function scrollByAuto(dy,smooth){
  const sm=smooth&&!reduced.matches;
  S.ignoreUntil=performance.now()+(sm?1400:300);
  window.scrollTo({top:Math.max(0,window.scrollY+dy),behavior:sm?'smooth':'auto'});
  if(!sm)S.autoY=window.scrollY;
}
// exact place: the block's top a little below the free top edge; when the explained row of a long derivation would then
// sit below the screen, that row is placed in the upper third instead
function rowOf(b){ const r=S.targets[S.i]===b?stepRow(S.i):null; return r&&r.b===b?r.rect:null; }
function snapDy(b){
  const top=topOffset(), free=Math.max(120,innerHeight-top), r=b.getBoundingClientRect(), row=rowOf(b);
  let dy=r.top-(top+free*.1);
  if(row&&row.bottom-dy>innerHeight-16)dy=row.top-(top+free*.35);
  return dy;
}
function snapTo(b,smooth){ const dy=snapDy(b); if(Math.abs(dy)>6)scrollByAuto(dy,smooth); }
// while playing: move only when the block (or its explained row) is not already comfortably on screen
function followTo(b){
  const top=topOffset(), free=innerHeight-top, r=rowOf(b)||b.getBoundingClientRect();
  if(r.top>=top&&r.top<=top+free*.55&&(r.bottom<=innerHeight-8||r.bottom-r.top>free*.8))return;
  snapTo(b,true);
}
function snapCurrent(smooth){ if(S.mode==='both'&&S.sync&&S.follow){ const b=S.targets[S.i]; if(b)snapTo(b,!!smooth); } }
function flash(b){ if(!b||!b.classList)return; b.classList.remove('lv-flash'); void b.offsetWidth; b.classList.add('lv-flash'); setTimeout(()=>b.classList.remove('lv-flash'),1800); }
function paintHighlight(){
  const want=S.mode==='both'&&S.sync?S.targets[S.i]:null;
  ctx.main.querySelectorAll('.lv-cur').forEach(x=>{ if(x!==want)x.classList.remove('lv-cur'); });
  if(isAnchor(want))want.classList.add('lv-cur');
  if(!want)clearBand();
}

// ---------- steps ----------
function clearBand(){ if(S.band){ S.band.remove(); S.band=null; } }
const grantedBlk=b=>S.prac.some(s=>S.granted.has(s.id)&&S.targets[s.i]===b);
function applyStep(i){
  clearBand();
  const s=S.segs[i]; if(!s||!s.step||!S.sync)return;
  const b=S.targets[i]; if(!b||!b.classList.contains('blk'))return;
  const box=b.querySelector('.check>details[open]>div');
  if(box&&box._rv&&grantedBlk(b)){ if(box._rv.k<s.step&&ctx.rvGo)ctx.rvGo(box,s.step); return; }
  if(S.mode!=='both')return;
  const row=stepRow(i); if(!row)return;
  const br=b.getBoundingClientRect(), sc=b.offsetHeight/(br.height||1), q=row.rect;
  const band=document.createElement('div'); band.className='lv-band'; band.setAttribute('aria-hidden','true');
  Object.assign(band.style,{top:((q.top-br.top)*sc-3)+'px',height:((q.bottom-q.top)*sc+6)+'px',left:((q.left-br.left)*sc)+'px',width:((q.right-q.left)*sc)+'px'});
  b.appendChild(band); S.band=band;
}
// the on-screen row of segment i's step in its block's single aligned derivation (client coordinates), or null
function stepRow(i){
  const s=S.segs[i]; if(!s||!s.step||!S.sync||!ctx.rvGroups)return null;
  const b=S.targets[i]; if(!b||!b.classList.contains('blk'))return null;
  const mrs=[...b.querySelectorAll('.mathrow')].filter(mr=>!mr.closest('details,.fold,.mcqi,.quiz,.check'));
  if(mrs.length!==1||!mrs[0].getClientRects().length)return null;
  const mr=mrs[0], g=(ctx.rvGroups(mr)||[])[s.step-1];
  if(!g||!g.length||g.some(c=>c.hosts.some(h=>h.style.visibility==='hidden')))return null;
  const mrr=mr.getBoundingClientRect();
  const left=Math.max(mrr.left,Math.min(...g.map(c=>c.left))-10), right=Math.min(mrr.right,Math.max(...g.map(c=>c.right))+10);
  if(right<=left)return null;
  return {b,rect:{top:Math.min(...g.map(c=>c.top)),bottom:Math.max(...g.map(c=>c.bottom)),left,right}};
}

// ---------- practice gate ----------
// a question pauses before its answer; only an explicit choice (Continue, Play at the gate, dragging the timeline into
// the answer) goes on. Going back before the pause re-arms it; a restored position never reveals.
function gateHit(a,b){ for(const s of S.prac){ if(!S.armed.has(s.id))continue; const p=s.p; if(b>=p.pauseAt-.04&&(b<p.revealAt||a<p.pauseAt))return s; } return null; }
function showGate(s){
  S.gate=s; const v=S.video;
  if(!v.paused)v.pause();
  if(S.meta&&Math.abs(v.currentTime-s.p.pauseAt)>.05)v.currentTime=s.p.pauseAt; else if(!S.meta)S.pendingT=s.p.pauseAt;
  S.prevT=s.p.pauseAt; paintTime(s.p.pauseAt,true); setSeg(s.i,'gate'); paintCards(); paintPlay();
  say('Paused before the answer. Work it out, then choose Continue to the answer.');
  const a=document.activeElement;
  if(S.mode!=='read'&&(!a||a===document.body||S.panel.contains(a)))S.gateBtn.focus({preventScroll:true});
}
function grant(s){
  S.granted.add(s.id);
  if(!S.sync)return;
  const b=S.targets[s.i]; if(!b||!b.classList.contains('blk'))return;
  const ds=[...b.querySelectorAll('.check>details')];
  if(ds.length===1&&!ds[0].open){   // several questions in one block: the reader picks
    const d=ds[0]; d.open=true; S.opened.set(s.id,d);
    // the reader closing it takes it back: a later re-open is theirs and is never closed by the player
    const off=()=>{ if(d.open)return; if(S.opened.get(s.id)===d)S.opened.delete(s.id); d.removeEventListener('toggle',off); };
    d.addEventListener('toggle',off);
  }
  setTimeout(()=>applyStep(S.i),80);   // the board sets up the step-by-step answer on toggle
}
function unopen(s){
  const d=S.opened.get(s.id); if(!d)return;
  S.opened.delete(s.id);
  if(!d.isConnected||!d.open)return;   // a rebuild already replaced it, or the reader closed it
  const box=d.querySelector(':scope>div'); if(box&&box._rv)box._rv.k=Math.min(1,box._rv.plan.steps.length);   // next open starts at step 1 again
  d.open=false;
}
function cont(){
  const s=S.gate; if(!s)return;
  S.gate=null; S.armed.delete(s.id); grant(s);
  rawSeek(s.p.revealAt); paintCards(); play();
}
function replayQ(){
  const s=S.gate||S.segs[S.i]; S.gate=null;
  let t=s.start; if(s.p&&s.p.pauseAt-s.start<1&&s.i>0)t=S.segs[s.i-1].start;   // the question was asked before this segment
  attach(); seek(t,'replay'); play();
}

// ---------- playback ----------
function ensureSrc(){ if(!S.src){ S.src=true; S.video.src=S.m.videoUrl; } }
function rawSeek(t){ S.ended=false; S.prevT=t; if(S.meta)S.video.currentTime=t; else S.pendingT=t; paintTime(t,true); setSeg(segAt(t),'seek'); }
// kind: nav | replay | skip | scrub | preview | restore | loop | media
function seek(t,kind,from){
  t=clamp(t,0,Math.max(0,S.dur-.05));
  if(from===undefined)from=cur();
  let gate=null;
  for(const s of S.prac){
    const p=s.p;
    if(t<p.pauseAt-.01){ S.armed.add(s.id); S.granted.delete(s.id); unopen(s); continue; }
    if(!S.armed.has(s.id)||gate)continue;
    if(kind==='scrub'&&t<s.end){ S.armed.delete(s.id); grant(s); }
    else if((kind==='skip'||kind==='media')&&from<p.pauseAt-.01)gate=s;   // a skip never jumps over a question
    else if((kind==='skip'||kind==='media')&&t>from&&from<s.end){ S.armed.delete(s.id); grant(s); }   // skipping on from the pause is a choice
    else if(kind==='restore'&&t<s.end)gate=s;   // a restored position inside a question's segment (even past revealAt) waits at its pause
  }
  if(gate)t=gate.p.pauseAt;
  if(S.gate&&!gate)S.gate=null;
  rawSeek(t);
  if(gate)showGate(gate);
  paintCards(); paintPlay();
  if(kind==='nav'||kind==='replay'||kind==='scrub'||kind==='media')snapCurrent();
  else if(kind==='skip'&&S.mode==='both'&&S.sync&&S.follow&&S.targets[S.i])followTo(S.targets[S.i]);
  if(kind!=='preview')save();
  if(kind!=='restore'&&kind!=='preview'){ S.touched=true; emit(); }
}
function play(){
  if(S.gate)return cont();
  ensureSrc();
  if(S.err){ retry(); }
  if(S.ended){ S.ended=false; seek(0,'nav'); }
  if(!S.follow&&S.detach==='mode'&&S.sync){ attach(); snapCurrent(true); }
  const pr=S.video.play();
  if(pr&&pr.catch)pr.catch(e=>{ if(e&&e.name==='AbortError')return; paintPlay(); if(e&&e.name==='NotAllowedError')say('Press Play to start the video.'); });
}
function toggle(){ if(S.gate)return cont(); if(S.video.paused||S.ended)play(); else S.video.pause(); }
function skip(d){ const t=cur(); seek(t+d,'skip',t); }
function navPrev(){ const s=S.segs[S.i]; let j=S.i; if(cur()-s.start<3&&j>0)j--; attach(); seek(S.segs[j].start,'nav'); }
function navNext(){ if(S.i<S.segs.length-1){ attach(); seek(S.segs[S.i+1].start,'nav'); } }
function replaySeg(){ const s=S.segs[S.i]; if(!s)return; attach(); seek(s.start,'replay'); play(); }
function stepRate(d){ const i=clamp(SPEEDS.indexOf(S.rate)+d,0,SPEEDS.length-1); setRate(SPEEDS[i]); say(`Speed ${SPEEDS[i]}×`); }
function setRate(r){ S.rate=r; S.video.defaultPlaybackRate=S.video.playbackRate=r; S.speed.value=String(r); save(); }
function retry(){ S.err=false; S.pendingT=S.prevT; S.meta=false; paintCards(); paintIntro(); S.video.load(); }
function watchFrom(i){ const s=S.segs[i]; if(!s)return; if(S.mode==='read')setMode('both'); attach(); seek(s.start,'nav'); play(); }
function readFrom(){
  const b=S.sync?S.targets[S.i]:null;
  if(!S.video.paused)S.video.pause();
  if(S.mode==='watch')setMode('read');
  if(b){ attach(); scrollByAuto(snapDy(b),false); flash(b); }
}
function loop(){ if(S.raf)return; const f=()=>{ S.raf=0; if(S.video.paused)return; tick(); S.raf=requestAnimationFrame(f); }; S.raf=requestAnimationFrame(f); }
function tick(){
  const t=S.video.currentTime;
  if(!S.scrub){
    const g=gateHit(S.prevT,t); if(g)return showGate(g);
    const s=S.segs[S.i];
    if(S.loop&&s&&t>=s.end-.06&&s.end<S.dur-.05)return seek(s.start,'loop');
  }
  S.prevT=t; paintTime(t); setSeg(segAt(t),'play');
}
function setSeg(i,why){
  if(i===S.i||!S.segs[i])return;
  const old=S.targets[S.i]; S.i=i; const s=S.segs[i];
  S.nextBtn.disabled=i>=S.segs.length-1;
  S.list.querySelectorAll('[aria-current]').forEach(x=>x.removeAttribute('aria-current'));
  const li=S.list.querySelector(`[data-i="${i}"]`);
  if(li){ li.setAttribute('aria-current','true'); const L=S.list, y=li.parentElement.offsetTop; if(S.mode==='watch'&&L.clientHeight&&(y<L.scrollTop||y+li.offsetHeight>L.scrollTop+L.clientHeight))L.scrollTop=Math.max(0,y-L.clientHeight/3); }
  paintHighlight(); applyStep(i); emit();
  const b=S.targets[i];
  if(why==='play'&&S.mode==='both'&&S.sync&&S.follow&&b&&(b!==old||S.band))followTo(b);   // next block, or the next row of the same derivation
}
function onError(){
  const e=S.video.error; if(!e)return;
  S.err=true; waiting(false);
  S.errMsg=e.code===2?'The video stopped loading. Check that the board is still running, then try again.':'This browser could not play the video file.';
  S.errEl.querySelector('.lv-errt').textContent=S.errMsg;
  paintCards(); paintPlay(); paintIntro(); say(S.errMsg);
  if(S.mode==='watch'){ setMode('read',{persist:false}); toast('The video could not be played, so the lesson text is back.'); }
}
function waiting(on){ clearTimeout(S.waitT); if(on)S.waitT=setTimeout(()=>{ S.spin.hidden=false; },350); else S.spin.hidden=true; }
// Full screen is the whole board page with the player filling it (html.lv-fsmode), so the chat button stays on screen
// and the chat opens on the right with the video beside it. Where the browser refuses page full screen the same layout
// fills the window instead; an iPhone, which has no page full screen, gets the system player.
const fsEl=()=>document.fullscreenElement||document.webkitFullscreenElement||null;
const fsOn=()=>root.classList.contains('lv-fsmode');
function setFsMode(on){ root.classList.toggle('lv-fsmode',on); paintFs(); layout(); wake(); }
function exitFs(){
  if(!fsOn())return;
  const d=document;
  if(fsEl()===root){ if(d.exitFullscreen)d.exitFullscreen().catch(()=>{}); else if(d.webkitExitFullscreen)d.webkitExitFullscreen(); }
  setFsMode(false);
}
function toggleFs(){
  if(fsOn())return exitFs();
  if(S.mode==='read')return;
  if(!root.requestFullscreen&&!root.webkitRequestFullscreen&&S.video.webkitEnterFullscreen&&/iPhone|iPod/.test(navigator.userAgent))return S.video.webkitEnterFullscreen();
  setFsMode(true);
  try{
    const r=root.requestFullscreen?root.requestFullscreen({navigationUI:'hide'}):root.webkitRequestFullscreen&&root.webkitRequestFullscreen();
    if(r&&r.catch)r.catch(()=>{});
  }catch(_){}
}
function togglePip(){
  if(document.pictureInPictureElement)document.exitPictureInPicture().catch(()=>{});
  else{ ensureSrc(); S.video.requestPictureInPicture&&S.video.requestPictureInPicture().catch(()=>say('Picture in picture is not available right now.')); }
}

// ---------- paint ----------
function paintTime(t,force){
  if(!S.scrub)S.range.value=String(t);
  paintCC(t);
  S.tl.style.setProperty('--p',(t/S.dur*100).toFixed(3)+'%');
  const sec=Math.floor(t);
  if(sec!==S.lastSec||force){
    S.lastSec=sec; S.el.textContent=fmt(t);
    const s=S.segs[segAt(t)], j=chapAt(t), c=S.chaps[j].title;
    if(j!==S.chapI){ S.chapI=j; S.chEl.textContent=c; S.chEl.hidden=!c; S.chEl.title=c; [...S.zones.children].forEach((z,k)=>z.classList.toggle('cur',k===j)); }
    S.range.setAttribute('aria-valuetext',`${fmt(t)} of ${fmt(S.dur)}${c?', '+c:''}${s&&s.label!==c?', '+s.label:''}`);
  }
}
function paintBuffered(){
  const b=S.video.buffered, t=S.video.currentTime; let end=0;
  for(let k=0;k<b.length;k++)if(b.start(k)<=t+.5&&b.end(k)>=t){ end=b.end(k); break; }
  S.tl.style.setProperty('--b',(end/S.dur*100).toFixed(3)+'%');
}
function paintPlay(){
  const playing=!S.video.paused&&!S.ended;
  const lab=S.gate?'Continue to the answer':playing?'Pause':'Play';
  S.playBtn.innerHTML=playing?I.pause:I.play; S.playBtn.setAttribute('aria-label',lab); S.playBtn.title=lab+' (Space)';
  S.panel.classList.toggle('lv-playing',playing);
  paintCards();
}
function paintCards(){
  if(!S.gateEl)return;
  S.gateEl.hidden=!S.gate; S.errEl.hidden=!S.err||!!S.gate; S.endEl.hidden=!S.ended||!!S.gate||S.err;
  const card=!!S.gate||S.err||S.ended;
  S.big.hidden=card||!S.video.paused;
  S.stage.classList.toggle('lv-carded',card);
}
function paintMenu(){
  if(!S.menu)return;
  const lp=S.menu.querySelector('[data-a="loop"]'), mu=S.menu.querySelector('[data-a="mute"]');
  lp.setAttribute('aria-pressed',String(S.loop)); mu.setAttribute('aria-pressed',String(S.video.muted)); mu.textContent=S.video.muted?'Unmute':'Mute';
  S.panel.classList.toggle('lv-looping',S.loop);
}
function paintFoot(){
  if(!S.readBtn)return;
  S.readBtn.hidden=!S.sync;
  S.followBtn.hidden=!(S.sync&&S.mode==='both'&&!S.follow);
}
function paintFs(){
  const on=fsOn();
  S.fsBtn.innerHTML=on?I.fsx:I.fs; const lab=on?'Exit full screen':'Full screen'; S.fsBtn.setAttribute('aria-label',lab); S.fsBtn.title=lab+' (F)';
  S.panel.classList.toggle('lv-fs',on);
}
// controls fade while the video plays and come back on any pointer move, tap or key
function wake(){
  if(!S||!S.panel)return;
  S.panel.classList.remove('lv-idle'); clearTimeout(S.idleT);
  if(!S.video.paused)S.idleT=setTimeout(idle,2600);
}
function idle(){
  if(S.video.paused||S.menuOpen||S.scrub||S.gate||S.ended||S.bar.matches(':hover')||S.bar.querySelector(':focus-visible'))return wake();
  S.panel.classList.add('lv-idle'); hideTip();
}
function openMenu(){ S.menuOpen=true; S.menu.hidden=false; S.menu.style.maxHeight=Math.max(120,S.stage.clientHeight-64)+'px'; S.moreBtn.setAttribute('aria-expanded','true'); paintMenu(); S.menu.querySelector('button')?.focus({preventScroll:true}); }
function closeMenu(focus){ if(!S.menuOpen)return; S.menuOpen=false; S.menu.hidden=true; S.moreBtn.setAttribute('aria-expanded','false'); if(focus)S.moreBtn.focus({preventScroll:true}); }
function say(t){ S.live.textContent=''; setTimeout(()=>{ S.live.textContent=t; },30); }
function toast(t){ const el=document.getElementById('toast'); if(!el)return say(t); el.textContent=t; el.style.display='block'; clearTimeout(S.toastT); S.toastT=setTimeout(()=>{ el.style.display='none'; },4200); }
// hover (or a touch drag): the chapter under the pointer grows, and a tip names it with the time there
function tipAt(x,t){
  const r=S.range.getBoundingClientRect();
  if(t===undefined)t=clamp((x-r.left-7)/Math.max(1,r.width-14),0,1)*S.dur;
  else x=r.left+7+t/S.dur*(r.width-14);
  const j=chapAt(t), c=S.chaps[j].title||(S.segs[segAt(t)]||{}).label||'';
  S.tip.querySelector('.lv-tipc').textContent=c; S.tip.querySelector('.lv-tipt').textContent=fmt(t); S.tip.hidden=false;
  if(j!==S.hoverZ){ const zs=S.zones.children; if(zs[S.hoverZ])zs[S.hoverZ].classList.remove('hov'); if(zs[j])zs[j].classList.add('hov'); S.hoverZ=j; }
  const tr=S.tl.getBoundingClientRect(), sc=S.tl.offsetWidth/(tr.width||1), w=S.tip.offsetWidth;
  S.tl.style.setProperty('--h',(t/S.dur*100).toFixed(3)+'%');
  S.tip.style.left=clamp((x-tr.left)*sc-w/2,0,Math.max(0,S.tl.offsetWidth-w))+'px';
}
function hideTip(){ if(!S.tip)return; S.tip.hidden=true; const z=S.zones.children[S.hoverZ]; if(z)z.classList.remove('hov'); S.hoverZ=-1; S.tl.style.setProperty('--h','0%'); }

// ---------- events ----------
function act(a,el){
  switch(a){
    case 'play': return toggle();
    case 'back': return skip(-SKIP);
    case 'fwd': return skip(SKIP);
    case 'prev': closeMenu(); return navPrev();
    case 'next': closeMenu(); return navNext();
    case 'more': return S.menuOpen?closeMenu(true):openMenu();
    case 'fs': return toggleFs();
    case 'cc': return setCC(!S.cc);
    case 'replay': closeMenu(); return replaySeg();
    case 'loop': S.loop=!S.loop; paintMenu(); save(); return say(S.loop?'Looping this explanation':'Loop off');
    case 'mute': S.video.muted=!S.video.muted; paintMenu(); return save();
    case 'pip': closeMenu(); return togglePip();
    case 'read': closeMenu(); exitFs(); return readFrom();
    case 'follow': attach(); return snapCurrent(true);
    case 'continue': return cont();
    case 'replayq': return replayQ();
    case 'retry': return retry();
    case 'toread': exitFs(); return setMode('read');
    case 'restart': S.ended=false; attach(); seek(0,'nav'); return play();
    case 'seg': attach(); seek(S.segs[+el.dataset.i].start,'nav'); return play();
  }
}
function owns(e){
  if(!S||S.mode==='read'||e.defaultPrevented||e.metaKey||e.ctrlKey||e.altKey||e.isComposing)return false;
  const t=e.target instanceof Element?e.target:document.body;
  if(t.closest('input:not(.lv-range),textarea,select,[contenteditable]:not([contenteditable="false"]),#chat'))return false;
  if(fsOn())return !t.closest('#chat');
  const fs=fsEl(); if(fs)return false;
  if(S.panel.contains(t))return true;
  return S.mode==='watch'&&!t.closest('#toc,#topresults,.lv-modes');
}
function wire(){
  const v=S.video, p=S.panel;
  v.addEventListener('loadedmetadata',()=>{ fitCaptions(); S.meta=true; if(num(v.duration)&&v.duration>0)S.dur=v.duration; S.range.max=String(S.dur); buildZones(); v.defaultPlaybackRate=v.playbackRate=S.rate; seek(S.pendingT,'restore'); });
  v.addEventListener('play',()=>{ if(S.gate)return cont(); S.ended=false; S.touched=true; paintPlay(); loop(); wake(); emit(); });   // Play from system controls at the gate = Continue
  v.addEventListener('playing',()=>{ waiting(false); paintPlay(); });
  v.addEventListener('pause',()=>{ wake(); paintPlay(); save(); paintIntro(); if(!S.scrub)snapCurrent(); emit(); });
  v.addEventListener('waiting',()=>waiting(true));
  v.addEventListener('canplay',()=>waiting(false));
  v.addEventListener('seeked',()=>{
    waiting(false);
    // a seek this player did not make (picture-in-picture or system controls) follows the same gate rules
    if(!S.scrub&&S.meta&&Math.abs(v.currentTime-S.prevT)>1)seek(v.currentTime,'media',S.prevT);
  });
  v.addEventListener('timeupdate',()=>{ if(!v.paused&&!S.scrub){ if(document.hidden)tick(); persistSoon(); } paintBuffered(); });
  v.addEventListener('progress',paintBuffered);
  v.addEventListener('ratechange',()=>{ if(v.playbackRate!==S.rate&&SPEEDS.includes(v.playbackRate)){ S.rate=v.playbackRate; S.speed.value=String(S.rate); save(); } });
  v.addEventListener('volumechange',paintMenu);
  v.addEventListener('ended',()=>{ if(S.loop&&S.segs[S.i]){ seek(S.segs[S.i].start,'loop'); return play(); } S.ended=true; paintPlay(); save(); });
  v.addEventListener('error',onError);
  // the board's text-selection drag must not start on the player (a timeline drag would select the math beside it)
  p.addEventListener('mousedown',e=>e.stopPropagation());
  // touching the player gives it the keyboard (Safari does not focus a clicked button)
  p.addEventListener('pointerdown',e=>{ S.ptr=e.pointerType; S.tapWoke=p.classList.contains('lv-idle'); wake(); setTimeout(()=>{ if(!p.contains(document.activeElement))p.focus({preventScroll:true}); },0); });
  p.addEventListener('pointermove',e=>{ if(e.pointerType!=='touch')wake(); });
  S.stage.addEventListener('pointerleave',e=>{ if(e.pointerType==='touch'||S.video.paused)return; clearTimeout(S.idleT); S.idleT=setTimeout(idle,700); });
  p.addEventListener('keydown',wake);
  p.addEventListener('click',e=>{
    if(S.tapWoke&&S.ptr==='touch'&&(e.target===v||e.target===S.stage)){ S.tapWoke=false; return; }   // a tap on faded controls only brings them back
    const b=e.target.closest('[data-a]');
    if(b&&p.contains(b)){ e.stopPropagation(); return act(b.dataset.a,b); }
    if(S.menuOpen&&!e.target.closest('.lv-more'))closeMenu();
    if(e.target===v||e.target===S.stage)toggle();
  });
  S.stage.addEventListener('dblclick',e=>{ if(e.target===v||e.target===S.stage)toggleFs(); });
  S.speed.addEventListener('change',()=>setRate(+S.speed.value));
  const r=S.range;
  r.addEventListener('pointerdown',e=>{ S.scrub=true; S.scrubPtr=e.pointerType; });
  r.addEventListener('input',()=>{
    S.scrub=true; S.scrubT=+r.value; paintTime(S.scrubT,true);
    if(S.scrubPtr==='touch')tipAt(0,S.scrubT);
    if(!S.scrubRaf)S.scrubRaf=requestAnimationFrame(()=>{ S.scrubRaf=0; seek(S.scrubT,'preview'); });
  });
  r.addEventListener('change',()=>{ S.scrub=false; seek(+r.value,'scrub'); });
  const endScrub=()=>setTimeout(()=>{ if(S.scrubPtr==='touch')hideTip(); S.scrubPtr=''; if(S.scrub){ S.scrub=false; paintTime(cur(),true); } },0);
  r.addEventListener('pointerup',endScrub); r.addEventListener('pointercancel',endScrub);
  S.tl.addEventListener('pointermove',e=>{ if(e.pointerType!=='touch')tipAt(e.clientX); });
  S.tl.addEventListener('pointerleave',e=>{ if(e.pointerType!=='touch')hideTip(); });
  // leaving page full screen (Esc, the browser's own control) leaves the player's full screen too
  const fsChange=()=>{ if(fsEl()===root)S.fsReal=true; else if(S.fsReal){ S.fsReal=false; if(fsOn())setFsMode(false); } paintFs(); };
  document.addEventListener('fullscreenchange',fsChange); document.addEventListener('webkitfullscreenchange',fsChange);
  document.addEventListener('pointerdown',e=>{ if(S.menuOpen&&!e.target.closest('.lv-more'))closeMenu(); });
  // Watch from here (beside lesson blocks)
  ctx.main.addEventListener('click',e=>{ const b=e.target.closest('.lv-wfh'); if(!b)return; e.preventDefault(); e.stopPropagation(); watchFrom(+b.dataset.seg); });
  // the view switch: header card and top bar
  document.addEventListener('click',e=>{
    const b=e.target.closest&&e.target.closest('.lv-modes [data-mode]'); if(!b)return;
    const g=b.closest('.lv-modes'); setMode(b.dataset.mode); focusMode(g,b.dataset.mode);
  });
  document.addEventListener('keydown',e=>{
    const b=e.target.closest&&e.target.closest('.lv-modes [data-mode]'); if(!b)return;
    const g=b.closest('.lv-modes'), bs=[...g.querySelectorAll('[data-mode]')]; let i=bs.indexOf(b);
    if(e.key==='ArrowRight'||e.key==='ArrowDown')i=(i+1)%bs.length; else if(e.key==='ArrowLeft'||e.key==='ArrowUp')i=(i+bs.length-1)%bs.length;
    else if(e.key==='Home')i=0; else if(e.key==='End')i=bs.length-1; else return;
    e.preventDefault(); e.stopPropagation(); setMode(bs[i].dataset.mode); focusMode(g,bs[i].dataset.mode);
  },true);
  // keyboard: only when the player has focus, in Watch, or in full screen; never while typing
  document.addEventListener('keydown',e=>{
    if(e.key==='Escape'&&S.menuOpen){ e.preventDefault(); return closeMenu(true); }
    if(e.key==='Escape'&&fsOn()&&!fsEl()&&!(e.target instanceof Element&&e.target.closest('#chat'))){ e.preventDefault(); return exitFs(); }
    if(!owns(e))return;
    const k=e.key, onCtl=e.target instanceof Element&&e.target.closest('button,a,summary');
    let done=true;
    if(k===' '||k==='k'||k==='K'){ if(onCtl&&k===' ')return; toggle(); }
    else if(k==='ArrowLeft'||k==='ArrowRight'){ const d=k==='ArrowRight'?1:-1; if(e.shiftKey)d>0?navNext():navPrev(); else skip(d*SKIP); }
    else if(k===']')navNext(); else if(k==='[')navPrev();
    else if(k==='f'||k==='F')toggleFs();
    else if((k==='c'||k==='C')&&S.caps)setCC(!S.cc);
    else if(k==='r'||k==='R')replaySeg();
    else if(k==='>'||k==='<')stepRate(k==='>'?1:-1);
    else done=false;
    if(done){ e.preventDefault(); e.stopPropagation(); }
  });
  // the reader taking over the scroll releases the follow; "Follow the video" re-attaches
  const intent=e=>{ if(S.mode!=='both'||!S.follow)return; if(e.target instanceof Element&&e.target.closest('#lvpanel,#chat,#toc,#topresults'))return; detach('user'); };
  window.addEventListener('wheel',intent,{passive:true});
  window.addEventListener('touchmove',intent,{passive:true});
  document.addEventListener('keydown',e=>{
    if(!['PageUp','PageDown','Home','End','ArrowUp','ArrowDown',' '].includes(e.key)||owns(e))return;
    if(e.target instanceof Element&&e.target.closest('input,textarea,select,button,[contenteditable],#chat'))return;
    intent(e);
  });
  document.addEventListener('pointerdown',e=>{ if(e.target instanceof Element&&e.target.closest('.rail'))intent({target:document.body}); },true);
  // a jump from Contents: in Watch it brings the text back first, in Both it is the reader leaving the video
  document.addEventListener('click',e=>{
    if(!(e.target instanceof Element)||!e.target.closest('#toc a[data-id],#toc-ticks .tick'))return;
    if(S.mode==='watch')setMode('read'); else if(S.mode==='both'&&S.follow)detach('user');
  },true);
  window.addEventListener('scroll',()=>{
    if(S.mode!=='both')return;
    if(performance.now()<S.ignoreUntil){ S.autoY=window.scrollY; return; }
    if(S.follow&&Math.abs(window.scrollY-S.autoY)>160)detach('user');
  },{passive:true});
  if('ResizeObserver' in window)new ResizeObserver(fitCaptions).observe(S.stage);
  let rt=0; window.addEventListener('resize',()=>{ layout(); fitCaptions(); clearTimeout(rt); rt=setTimeout(()=>{ applyStep(S.i); if(S.mode==='both')S.autoY=window.scrollY; },160); });
  window.addEventListener('pagehide',save);
  document.addEventListener('visibilitychange',()=>{ if(document.hidden)save(); });
  if('mediaSession' in navigator){
    const set=(a,f)=>{ try{ navigator.mediaSession.setActionHandler(a,f); }catch(_){} };
    set('play',()=>play()); set('pause',()=>S.video.pause()); set('seekbackward',()=>skip(-SKIP)); set('seekforward',()=>skip(SKIP));
    set('previoustrack',navPrev); set('nexttrack',navNext); set('seekto',d=>{ if(d&&num(d.seekTime))seek(d.seekTime,'scrub'); });
  }
}
function focusMode(g,mode){
  const vis=x=>x&&x.getClientRects().length>0;
  let b=g.querySelector(`[data-mode="${mode}"]`);
  if(!vis(b))b=[...document.querySelectorAll(`.lv-modes [data-mode="${mode}"]`)].find(vis);
  if(b)b.focus({preventScroll:true});
}

window.LessonVideo={refresh,context};
})();
