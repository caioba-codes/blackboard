/* Lesson podcast: the Listen view. Mounted only when the lesson's front matter has `podcast: assets/<file>.mp3`; the
   transcript is the sibling `<file>.transcript.json` ([{p, t, s}]: paragraph index, start seconds, sentence), made by
   bin/podcast_align.py. Listen hides the lesson text and shows a player over the transcript: the sentence being said
   is lit and kept in view (not for 5 s after the reader scrolls), and tapping a sentence plays from there.
   Space plays or pauses and the left and right arrows move 15 s while Listen is open.
   A lesson that also has a video gets a Listen button in the video's Read/Watch switch instead of a card of its own.
   Position, speed and view live in this browser only (localStorage), never in learning records. */
(function(){
'use strict';
const SPEEDS=[.8,1,1.25,1.5,1.75,2], SKIP=15, HOLD=5000;
const root=document.documentElement;
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const fmt=t=>{ t=Math.max(0,Math.floor(t||0)); const h=Math.floor(t/3600),m=Math.floor(t%3600/60),s=t%60; return (h?h+':'+String(m).padStart(2,'0'):m)+':'+String(s).padStart(2,'0'); };
const svg=(d,x)=>`<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"${x||''}>${d}</svg>`;
const STROKE=' fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"';
const I={
  play:svg('<path d="M5 3.1v9.8L12.8 8z" fill="currentColor"/>'),
  pause:svg('<path d="M4.4 3h2.5v10H4.4zM9.1 3h2.5v10H9.1z" fill="currentColor"/>'),
  back:svg('<path d="M3.4 8.6A4.8 4.8 0 1 0 5 4.6"/><path d="M5.6 2.2 4.6 4.8l2.7.6"/><text x="8.2" y="10.4" font-size="5" text-anchor="middle" fill="currentColor" stroke="none" font-family="inherit">15</text>',STROKE),
  fwd:svg('<path d="M12.6 8.6A4.8 4.8 0 1 1 11 4.6"/><path d="M10.4 2.2l1 2.6-2.7.6"/><text x="7.8" y="10.4" font-size="5" text-anchor="middle" fill="currentColor" stroke="none" font-family="inherit">15</text>',STROKE),
  read:svg('<path d="M2.5 3.5c2-.6 3.9-.4 5.5.8 1.6-1.2 3.5-1.4 5.5-.8v9c-2-.6-3.9-.4-5.5.8-1.6-1.2-3.5-1.4-5.5-.8z"/><path d="M8 4.3v9"/>',STROKE),
  listen:svg('<path d="M2.8 10V8.4a5.2 5.2 0 0 1 10.4 0V10"/><rect x="2.2" y="9.2" width="2.8" height="4.2" rx="1"/><rect x="11" y="9.2" width="2.8" height="4.2" rx="1"/>',STROKE),
};
let ctx=null, L=null;

function load(){ try{ return JSON.parse(localStorage.getItem(L.key)||'{}')||{}; }catch(_){ return {}; } }
function save(){ if(!L)return; try{ localStorage.setItem(L.key,JSON.stringify({mode:L.mode,t:Math.round(L.audio.currentTime*10)/10,rate:L.audio.playbackRate})); }catch(_){} }
function assetUrl(p){ return p.startsWith('http')||p.startsWith('/')?p:(ctx.wsb||'')+'/assets/'+p.replace(/^assets\//,''); }

function refresh(c){
  if(!c||!c.main||!c.lessonId)return;
  ctx=c;
  const p=c.fm&&typeof c.fm.podcast==='string'?c.fm.podcast.trim():'';
  if(!p||!/\.(mp3|m4a)$/i.test(p))return;
  if(!L)mount(assetUrl(p));
  place(); [400,1500,4000].forEach(ms=>setTimeout(place,ms));   // the video's switch, if any, mounts later
}

function modes(cls,labels){
  return `<div class="lv-modes ll-modes ${cls}" role="radiogroup" aria-label="Lesson view">${[['read','Read',I.read,'Read the lesson'],['listen','Listen',I.listen,'Listen to the podcast']]
    .map(([k,l,ic,t])=>`<button type="button" role="radio" data-llmode="${k}" aria-checked="false" title="${t}"${labels?'':` aria-label="${l}"`}>${ic}${labels?`<span>${l}</span>`:''}</button>`).join('')}</div>`;
}

function mount(url){
  const audio=new Audio(); audio.preload='metadata'; audio.src=url;
  L={audio,url,key:`ll:${ctx.ws||''}:${ctx.lessonId}`,rows:[],spans:[],i:-1,mode:'read',held:0,progUntil:0,readY:0,lastSave:0};
  const saved=load();
  if(SPEEDS.includes(saved.rate))audio.playbackRate=saved.rate;
  audio.addEventListener('loadedmetadata',()=>{ if(saved.t>0&&saved.t<audio.duration-1&&!L.restored){ audio.currentTime=saved.t; } L.restored=true; paint(); });

  const panel=document.createElement('section'); panel.id='llpanel'; panel.className='ll-panel'; panel.hidden=true; panel.setAttribute('aria-label','Lesson podcast');
  panel.innerHTML=`<div class="ll-head"><b>Podcast</b>${modes('ll-pmodes',true)}</div>
<div class="ll-bar">
  <div class="ll-ctl">
    <button type="button" class="ll-b ll-back" title="Back ${SKIP} s (←)" aria-label="Back ${SKIP} seconds">${I.back}</button>
    <button type="button" class="ll-b ll-play" title="Play (space)" aria-label="Play">${I.play}</button>
    <button type="button" class="ll-b ll-fwd" title="Forward ${SKIP} s (→)" aria-label="Forward ${SKIP} seconds">${I.fwd}</button>
    <button type="button" class="ll-rate" title="Speed" aria-label="Playback speed">1×</button>
  </div>
  <div class="ll-scrub"><span class="ll-cur">0:00</span><input type="range" class="ll-range" min="0" max="1" step="0.1" value="0" aria-label="Position"><span class="ll-dur">0:00</span></div>
</div>
<div class="ll-tx" aria-live="off"><p class="ll-note">Loading the transcript…</p></div>`;
  document.body.insertBefore(panel,ctx.main);
  L.panel=panel; L.tx=panel.querySelector('.ll-tx'); L.range=panel.querySelector('.ll-range');
  L.playBtn=panel.querySelector('.ll-play'); L.rateBtn=panel.querySelector('.ll-rate');

  panel.querySelector('.ll-back').onclick=()=>skip(-SKIP);
  panel.querySelector('.ll-fwd').onclick=()=>skip(SKIP);
  L.playBtn.onclick=toggle;
  L.rateBtn.onclick=()=>{ const k=SPEEDS.indexOf(audio.playbackRate); audio.playbackRate=SPEEDS[(k+1)%SPEEDS.length]; paint(); save(); };
  L.range.addEventListener('input',()=>{ L.scrubbing=true; panel.querySelector('.ll-cur').textContent=fmt(+L.range.value); });
  L.range.addEventListener('change',()=>{ L.scrubbing=false; seek(+L.range.value); });
  L.tx.addEventListener('click',e=>{ const s=e.target.closest('.ll-s'); if(!s)return; seek(+s.dataset.t); L.held=0; audio.play().catch(()=>{}); });
  ['play','pause','ratechange','durationchange','ended'].forEach(ev=>audio.addEventListener(ev,()=>{ paint(); if(ev!=='play')save(); }));
  audio.addEventListener('timeupdate',()=>{ tick(); if(Date.now()-L.lastSave>2000){ L.lastSave=Date.now(); save(); } });
  audio.addEventListener('seeked',()=>tick(true));
  addEventListener('pagehide',save);

  // a scroll we did not start pauses following the voice for a few seconds
  addEventListener('scroll',()=>{ if(L.mode==='listen'&&Date.now()>L.progUntil)L.held=Date.now(); },{passive:true});
  addEventListener('wheel',()=>{ if(L.mode==='listen')L.held=Date.now(); },{passive:true});
  addEventListener('touchmove',()=>{ if(L.mode==='listen')L.held=Date.now(); },{passive:true});

  document.addEventListener('click',e=>{
    const b=e.target.closest&&e.target.closest('[data-llmode]'); if(b){ e.preventDefault(); setMode(b.dataset.llmode); return; }
    const v=e.target.closest&&e.target.closest('.lv-modes [data-mode]'); if(v&&L.mode==='listen')setMode('read',{keepVideo:true});
  },true);
  addEventListener('keydown',onKey,true);

  if('mediaSession' in navigator){
    try{
      navigator.mediaSession.setActionHandler('seekbackward',()=>skip(-SKIP));
      navigator.mediaSession.setActionHandler('seekforward',()=>skip(SKIP));
      navigator.mediaSession.setActionHandler('play',()=>audio.play());
      navigator.mediaSession.setActionHandler('pause',()=>audio.pause());
    }catch(_){}
  }

  const tUrl=url.replace(/\.(mp3|m4a)$/i,'.transcript.json');
  fetch(tUrl,{cache:'no-store'}).then(r=>r.ok?r.json():Promise.reject()).then(rows=>{
    if(!Array.isArray(rows)||!rows.length)throw 0;
    L.rows=rows.filter(r=>r&&typeof r.s==='string'&&isFinite(r.t)).sort((a,b)=>a.t-b.t);
    let html='', para=null;
    L.rows.forEach((r,k)=>{ if(r.p!==para){ html+=(para===null?'':'</p>')+'<p>'; para=r.p; } html+=`<span class="ll-s" data-i="${k}" data-t="${r.t}">${esc(r.s)}</span> `; });
    L.tx.innerHTML=html+'</p>'; L.spans=[...L.tx.querySelectorAll('.ll-s')]; L.i=-1; tick(true);
  }).catch(()=>{ L.tx.innerHTML='<p class="ll-note">No transcript for this podcast yet. The audio still plays.</p>'; });

  if(saved.mode==='listen')setMode('listen',{init:true});
  paint();
}

// the card under the lesson title, or a Listen button in the video's switch when the lesson has a video
function place(){
  if(!L||!ctx)return;
  const video=document.querySelector('.lv-intro:not(.ll-intro)');
  if(video){
    if(L.intro){ L.intro.remove(); L.intro=null; }
    document.querySelectorAll('.lv-modes:not(.ll-modes)').forEach(g=>{
      if(g.querySelector('[data-llmode]'))return;
      const labels=!!g.querySelector('button span');
      g.insertAdjacentHTML('beforeend',`<button type="button" role="radio" data-llmode="listen" aria-checked="false" title="Listen to the podcast"${labels?'':' aria-label="Listen"'}>${I.listen}${labels?'<span>Listen</span>':''}</button>`);
    });
  } else {
    if(!L.intro){
      const el=document.createElement('div'); el.className='lv-intro ll-intro';
      el.innerHTML=`<span class="lv-ic" aria-hidden="true">${I.listen}</span><div class="lv-itx"><b>Podcast</b><span class="lv-imeta ll-imeta">Live captions</span></div>${modes('lv-imodes',true)}`;
      L.intro=el;
    }
    if(L.intro.parentElement!==ctx.main){
      const head=[...ctx.main.children].filter(c=>c.matches('.top,.hero,p.credit:not(.imgcredits),#title,.byline')).pop();
      if(head)head.after(L.intro); else ctx.main.prepend(L.intro);
    }
  }
  paint();
}

function setMode(mode,o={}){
  if(mode===L.mode&&!o.init){ paint(); return; }
  const prev=L.mode; L.mode=mode;
  if(mode==='listen'){
    if(!o.init)L.readY=window.scrollY;
    if(root.classList.contains('lv-watch')){ const r=document.querySelector('.lv-modes [data-mode="read"]'); if(r)r.click(); }
    root.classList.add('ll-listen'); L.panel.hidden=false;
    L.held=0; L.progUntil=Date.now()+600; window.scrollTo(0,0); requestAnimationFrame(()=>follow(true));
  } else {
    root.classList.remove('ll-listen'); L.panel.hidden=true; L.audio.pause();
    if(prev==='listen'&&!o.keepVideo)window.scrollTo(0,L.readY);
  }
  paint(); if(!o.init)save();
}

function toggle(){ if(L.audio.paused)L.audio.play().catch(()=>{}); else L.audio.pause(); }
function seek(t){ const d=L.audio.duration; L.audio.currentTime=Math.max(0,isFinite(d)?Math.min(t,d-0.05):t); L.held=0; tick(true); }
function skip(d){ seek(L.audio.currentTime+d); }

function onKey(e){
  if(!L||L.mode!=='listen'||e.defaultPrevented||e.metaKey||e.ctrlKey||e.altKey||e.isComposing)return;
  const t=e.target; if(t&&t.closest&&t.closest('input:not(.ll-range),textarea,select,[contenteditable=""],[contenteditable="true"],#chat,#srcview'))return;
  if(e.key===' '||e.code==='Space')toggle();
  else if(e.key==='ArrowLeft')skip(-SKIP);
  else if(e.key==='ArrowRight')skip(SKIP);
  else return;
  e.preventDefault(); e.stopImmediatePropagation();
}

// which sentence is being said: the last one starting at or before now
function at(t){ const R=L.rows; let lo=0,hi=R.length-1,ans=-1; while(lo<=hi){ const m=(lo+hi)>>1; if(R[m].t<=t+0.05){ans=m;lo=m+1;} else hi=m-1; } return ans; }
function tick(force){
  if(!L)return;
  const t=L.audio.currentTime, d=L.audio.duration;
  if(!L.scrubbing){ L.range.value=String(t); L.panel.querySelector('.ll-cur').textContent=fmt(t); }
  if(isFinite(d)&&+L.range.max!==d){ L.range.max=String(d); }
  const i=L.rows.length?at(t):-1;
  if(i!==L.i||force){
    if(L.spans[L.i])L.spans[L.i].classList.remove('on');
    L.i=i; if(L.spans[i])L.spans[i].classList.add('on');
    follow(force);
  }
}
// keep the lit sentence in the middle third of what is visible under the sticky player
function follow(force){
  if(L.mode!=='listen'||!L.spans[L.i])return;
  if(!force&&Date.now()-L.held<HOLD)return;
  const s=L.spans[L.i].getBoundingClientRect(), bar=L.panel.querySelector('.ll-bar').getBoundingClientRect();
  const top=bar.bottom, h=innerHeight-top;
  if(s.top<top+h*.15||s.bottom>top+h*.7){
    L.progUntil=Date.now()+900;
    window.scrollTo({top:window.scrollY+s.top-top-h*.3,behavior:force?'auto':'smooth'});
  }
}

function paint(){
  if(!L)return;
  const a=L.audio, d=a.duration;
  document.querySelectorAll('[data-llmode]').forEach(b=>b.setAttribute('aria-checked',String(b.dataset.llmode===L.mode)));
  if(L.mode==='listen')document.querySelectorAll('.lv-modes [data-mode]').forEach(b=>b.setAttribute('aria-checked','false'));
  L.playBtn.innerHTML=a.paused?I.play:I.pause; L.playBtn.setAttribute('aria-label',a.paused?'Play':'Pause'); L.playBtn.title=(a.paused?'Play':'Pause')+' (space)';
  L.rateBtn.textContent=(a.playbackRate===1?'1':String(a.playbackRate))+'×';
  if(isFinite(d)){ L.panel.querySelector('.ll-dur').textContent=fmt(d); L.range.max=String(d); }
  const meta=document.querySelector('.ll-imeta'); if(meta&&isFinite(d))meta.textContent=`${fmt(d)} · live captions`+(a.currentTime>1&&a.currentTime<d-1?` · at ${fmt(a.currentTime)}`:'');
  if('mediaSession' in navigator&&window.MediaMetadata&&!L.meta){ try{ navigator.mediaSession.metadata=new MediaMetadata({title:(ctx.fm&&ctx.fm.title)||'Lesson podcast',artist:'Blackboard'}); L.meta=true; }catch(_){} }
}

window.LessonListen={refresh,active:()=>!!L&&L.mode==='listen'};
})();
