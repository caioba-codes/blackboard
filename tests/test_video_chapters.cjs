// Lesson video seek bar: one zone per lesson chapter (## heading), found from segment lines or chapter-naming labels,
// never going back in time; the bar has no per-segment ticks; full screen keeps the chat reachable.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const js=fs.readFileSync(path.join(__dirname,'../board/lesson-video.js'),'utf8');
const css=fs.readFileSync(path.join(__dirname,'../board/lesson-video.css'),'utf8');
const grab=name=>{const a=js.indexOf('function '+name+'(');assert(a>0,name);const b=js.indexOf('\nfunction ',a+10);return js.slice(a,b);};
const ctx={};vm.createContext(ctx);
for(const f of ['headingsOf','chaptersOf'])vm.runInContext(grab(f),ctx);
const titles=(segs,src)=>ctx.chaptersOf(segs,src).map(c=>`${c.title}@${c.i0}`).join(' | ');

// a lesson source: title, intro, three chapters, a fenced block that must not count, a quiz
const lines=Array(60).fill('text');
const put=(n,t)=>{lines[n-1]=t;};
put(1,'# Lesson'); put(10,'## Chapter 1 · Bases'); put(20,'## Chapter 2 · Signed Numbers'); put(25,'```'); put(26,'## not a heading'); put(27,'```');
put(30,'## Chapter 3 · Practice Exam'); put(40,'## Formula Sheet'); put(50,'## Quiz');
const src=lines.join('\n');
assert.equal(ctx.headingsOf(src).map(h=>h.line).join(),'10,20,30,40,50','fenced ## is not a heading');
const seg=(label,line)=>({label,line});

// a map whose lines match the lesson
const exact=[seg('Title',1),seg('Plan',3),seg('Ch1 card',10),seg('Bases idea',12),seg('Chapter 1 recap',10),
  seg('Ch2 card',20),seg('Ranges',22),seg('Ch3 card',30),seg('Exam rules',33),seg('Quiz 1: decimal',51),seg('Quiz 2',53)];
assert.equal(titles(exact,src),'Introduction@0 | Chapter 1 · Bases@2 | Chapter 2 · Signed Numbers@5 | Chapter 3 · Practice Exam@7 | Quiz@9',
  'one zone per chapter the video covers; a recap pointing back at its heading stays in its chapter; an uncovered chapter has no zone');

// a map made from an older lesson: every line a few lines early, chapter cards named by their labels
const stale=[seg('Title card',1),seg('Plan',3),seg('Chapter 1 · Bases',8),seg('Idea',9),seg('Chapter 2 card',18),seg('Ranges',19),
  seg('Practice exam intro',27),seg('Rules',28),seg('Quiz & recap card',47),seg('Quiz 1: decimal',48)];
assert.equal(titles(stale,src),'Introduction@0 | Chapter 1 · Bases@2 | Chapter 2 · Signed Numbers@4 | Chapter 3 · Practice Exam@6 | Quiz@8',
  'labels that name a chapter start it even when the lines have drifted');

// a generic label far from its heading cannot pull a zone forward; one stray line forward is ignored
const stray=[seg('Intro',1),seg('Ch1',11),seg('Quiz yourself',12),seg('Aside',45),seg('More ch1',13),seg('Ch2',21)];
assert.equal(titles(stray,src),'Introduction@0 | Chapter 1 · Bases@1 | Chapter 2 · Signed Numbers@5');

// no source, or no ## headings: the bar is one zone
assert.equal(ctx.chaptersOf(exact,undefined).length,1);
assert.equal(ctx.chaptersOf(exact,'# Only a title\ntext').length,1);

// the bar: zones, no per-segment tick strip, accessible slider with the chapter in its value text
assert(!/lv-ticks/.test(js)&&!/lv-ticks/.test(css),'no tick strip under the bar');
assert(/type="range" class="lv-range"/.test(js),'the native range input stays the slider (role slider, keyboard seeking)');
assert(/aria-valuetext',`\$\{fmt\(t\)\} of \$\{fmt\(S\.dur\)\}\$\{c\?', '\+c:''\}/.test(js),'value text names the chapter');
assert(/\.lv-z\.hov\{height:8px/.test(css),'the hovered zone grows');
assert(/var\(--acc\) 0 var\(--p\)/.test(css),'played part in the lesson accent');
assert(!/gold|201,171,98/.test(css),'no fixed gold: the player uses the lesson accent');
// full screen: the page, not the video, so the chat button and panel stay usable
assert(/root\.requestFullscreen/.test(js)&&!/S\.panel\.requestFullscreen|p\.requestFullscreen/.test(js),'page full screen, not the panel');
assert(/html\.lv-fsmode #lvpanel\{[^}]*right:var\(--chatw,0px\)/.test(css),'the video shrinks left of an open chat in full screen');
console.log('PASS: chapter zones from headings and labels, no ticks, accent fill, page full screen keeps the chat');
