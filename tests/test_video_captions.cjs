// Lesson video captions on the board: the overlay finds the caption at the video's time with the renderer's window,
// renders $math$ with KaTeX and escapes text, starts off on a video with burned-in captions, has a remembered CC
// toggle, sits on the picture (fullscreen and the chat layout included), and LessonVideo.context() has the chat's shape.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const js=fs.readFileSync(path.join(__dirname,'../board/lesson-video.js'),'utf8');
const css=fs.readFileSync(path.join(__dirname,'../board/lesson-video.css'),'utf8');
const grab=name=>{const a=js.indexOf('function '+name+'(');assert(a>0,name);const b=js.indexOf('\nfunction ',a+10);return js.slice(a,b);};
const ctx={S:null,console};ctx.window=ctx;vm.createContext(ctx);
vm.runInContext(js.match(/const esc=[^\n]*\n/)[0].replace('const ','var ')+js.match(/const num=[^\n]*\n/)[0].replace('const ','var ')+
  js.match(/function fmt\(t\)[^\n]*\n/)[0],ctx);
for(const f of ['capsUrl','usableCaps','capAt','capHtml','context','sectionAt'])vm.runInContext(grab(f),ctx);

// the track sits beside the MP4
assert.equal(ctx.capsUrl('/w/ece/assets/0010-lecture.mp4'),'/w/ece/assets/0010-lecture.captions.json');
// unusable cues are dropped, the rest sorted
const cues=ctx.usableCaps({cues:[{s:3,e:4,text:'b'},{s:1,e:2,text:'$I_5 = 0$.'},{s:5,e:4,text:'bad'},{s:6,e:7,text:' '}]});
assert.deepEqual(cues.map(c=>c.s),[1,3]);
assert.equal(ctx.usableCaps({cues:[]}),null);

// the renderer's window: 0.05 s early, 0.35 s late, nothing between
ctx.S={caps:cues};
assert.equal(ctx.capAt(0.94),null); assert.equal(ctx.capAt(0.96).text,'$I_5 = 0$.'); assert.equal(ctx.capAt(2.3).text,'$I_5 = 0$.');
assert.equal(ctx.capAt(2.5),null); assert.equal(ctx.capAt(3.5).text,'b');

// math through KaTeX, text escaped
ctx.katex={renderToString:(t)=>`<k>${t}</k>`};
assert.equal(ctx.capHtml('Row 5: $I_5 = 0$ <b>'),'Row 5: <k>I_5 = 0</k> &lt;b&gt;');
delete ctx.katex;
assert.equal(ctx.capHtml('$a<b$'),'a&lt;b','no KaTeX: the TeX is shown as escaped text');

// context(): null until played or seeked; then the chat's fields
const seg={id:'q',label:'Your turn: 8:1 mux',start:7500,end:7560,line:1337,p:{pauseAt:7520,revealAt:7525},i:0};
ctx.ctx={main:{querySelectorAll:()=>[]}};
ctx.S={touched:false,caps:[{s:7528,e:7529.5,text:'$I_5 = 0$.'}],segs:[seg],chaps:[{title:'Chapter 5 · Multiplexers',start:0}],
  video:{paused:true,currentTime:7529},meta:true,gate:null,ended:false,sync:true,granted:new Set(),pendingT:0};
vm.runInContext('var cur=()=>S.meta?S.video.currentTime:S.pendingT; function segAt(){return 0;} function chapAt(){return 0;}',ctx);
assert.equal(ctx.context(),null,'nothing before the reader plays or seeks');
ctx.S.touched=true;
const c=ctx.context();
assert.deepEqual(Object.keys(c),['t','time','chapter','segment','line','section','caption','paused','practice']);
assert.equal(c.time,'2:05:29'); assert.equal(c.caption,'$I_5 = 0$.'); assert.equal(c.chapter,'Chapter 5 · Multiplexers');
assert.equal(c.segment,'Your turn: 8:1 mux'); assert.equal(c.line,1337); assert.equal(c.paused,true);
assert.equal(c.practice,null,'past the reveal: no practice gate');
ctx.S.video.currentTime=7522;
assert.deepEqual({...ctx.context().practice},{label:'Your turn: 8:1 mux',revealed:false},'inside the question before its answer');
assert(/heading:c\.textContent/.test(js)&&/return \{id:best\.h\.id\|\|null,heading/.test(js),'section is {id, heading}');
assert(/new CustomEvent\('lessonvideo:context',\{detail:context\(\)\}\)/.test(js),'lessonvideo:context event carries the same object');
assert(/window\.LessonVideo=\{refresh,context,owns:/.test(js));

// CC: a toggle in the minimal bar, remembered per browser, off by default on a burned-in video, key C
assert(/class="lv-ib lv-ccb" data-a="cc" aria-pressed="false"/.test(js),'CC button in the control bar');
assert(/CC_KEY=burned=>burned\?'bb-video:cc-burned':'bb-video:cc'/.test(js));
assert(/S\.cc=on===null\?!S\.m\.captionsBurnedIn:on==='1'/.test(js),'default: on, off when captions are burned in');
assert(/\(k==='c'\|\|k==='C'\)&&S\.caps\)setCC\(!S\.cc\)/.test(js));
// on the picture, like the old burned box; above the bar while it shows; the burned box covered when on
assert(/\.lv-cc\{position:absolute;z-index:1;left:var\(--lv-cx/.test(css));
assert(/\.lv-cct\{[^}]*background:rgba\(0,0,0,\.62\)[^}]*font-family:var\(--body\)/.test(css),'translucent dark box in the lesson font');
assert(/\.lv-cct\{[^}]*var\(--acc\)/.test(css),'lesson accent');
assert(/\.lv-panel:not\(\.lv-idle\) \.lv-cc\{bottom:max\(/.test(css),'captions rise above the control bar');
assert(/\.lv-ccband\{[^}]*background:var\(--lv-frame/.test(css)&&/S\.band2\.hidden=!\(c&&S\.m\.captionsBurnedIn\)/.test(js),"opaque band over burned captions");
assert(/\.lv-mask\{[^}]*height:max\(3px,calc\(var\(--lv-ch,0px\) \* \.0105\)\)/.test(css),'the old progress strip and its ticks are masked');
assert(/S\.mask\.hidden=!S\.barBurned/.test(js),'only when the track says progressBarBurnedIn');
// full screen and the chat layout resize the stage: the picture box is re-measured
assert(/new ResizeObserver\(fitCaptions\)\.observe\(S\.stage\)/.test(js));
assert(/html\.lv-fsmode \.lv-stage\{flex:1/.test(css),'full screen stage holds the overlay');
console.log('PASS: caption overlay timing, KaTeX, CC toggle, placement, progress mask, context() shape');
