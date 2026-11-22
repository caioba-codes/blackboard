// Redo rounds: the row counts the lesson's missed items (Missed it, or a wrong latest multiple-choice pick) and a round
// shows only those, in lesson order, each check-in under the problem it answers; a Got it leaves the next round but is not
// pulled out of the current one; with nothing missed the round says "No misses left."
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../board/board.html.tmpl'),'utf8');
const fn=name=>{const a=source.indexOf('function '+name+'(');assert(a>0,name);return source.slice(a,source.indexOf('\nfunction ',a+10));};
const stmt=p=>{const a=source.indexOf(p);assert(a>0,p);return source.slice(a,source.indexOf(';\n',a)+1);};
const ctx={};vm.createContext(ctx);
vm.runInContext([stmt('const missedIds='),stmt('const redoRowHtml='),stmt('const redoHeadHtml='),fn('redoPlan')].join('\n').replace(/^const /gm,'var '),ctx);
const plain=x=>JSON.parse(JSON.stringify(x));

// the bridge's outcome map, and the lesson's quiz items in reading order
const outcomes={'c-a':{kind:'self',result:'got'},'c-b':{kind:'self',result:'missed'},'c-c':{kind:'self',result:'missed'},
  q1:{kind:'mcq',result:'missed'},q2:{kind:'mcq',result:'got'},'c-d':{kind:'self',result:'missed'},q3:{kind:'mcq',result:'missed'}};
const order=['c-a','c-b','c-c','q1','c-d','q2','q3','c-e'];
const round=ctx.missedIds(order,outcomes);
assert.deepEqual(plain(round),['c-b','c-c','q1','c-d','q3'],'missed items in lesson order; got and unmarked items stay out');

// a lesson: chapter heading, an official problem (label, its text, a figure) and its three-row check-in, teaching text,
// an unlabeled Your turn, a labeled multiple choice, a quiz block of multiple choice, a worked example then a Your turn
const blocks=[
  {kind:'stop',own:false,items:[]},                       // 0  ## Chapter 1
  {kind:'label',own:false,items:[]},                      // 1  Official · Fall 2021 Exam 3, Q1
  {kind:'body',own:false,items:[]},                       // 2  the problem's text
  {kind:'body',own:false,items:[]},                       // 3  its figure
  {kind:'stop',own:true,items:['c-a','c-b','c-c']},       // 4  ::: checkin (a), (b), (c)
  {kind:'body',own:false,items:[]},                       // 5  teaching paragraph
  {kind:'stop',own:true,items:['c-d']},                   // 6  ::: checkin Your turn, no label
  {kind:'label',own:false,items:[]},                      // 7  Written by Claude
  {kind:'stop',own:true,items:['q1']},                    // 8  ::: mcq q1
  {kind:'stop',own:false,items:['q2','q3']},              // 9  ::: quiz with two multiple choice
  {kind:'label',own:false,items:[]},                      // 10 Official · … (a worked example)
  {kind:'stop',own:false,items:[]},                       // 11 **Worked example · …** and its steps
  {kind:'stop',own:true,items:['c-e']},                   // 12 ::: checkin Your turn
];
assert.deepEqual(plain(ctx.redoPlan(blocks,round)),{ctx:[1,2,3,7],
  items:[[4,'c-b'],[4,'c-c'],[6,'c-d'],[8,'q1'],[9,'q3']]},
  'only the missed rows show, the problem above a check-in or multiple choice shows whole, nothing above a quiz item or an unlabeled Your turn');
// a Got it during the round: the round keeps the item, the next round drops it
outcomes['c-b']={kind:'self',result:'got'};
assert.deepEqual(plain(ctx.redoPlan(blocks,round).items.map(x=>x[1])),['c-b','c-c','c-d','q1','q3'],'not pulled away mid-round');
const next=ctx.missedIds(order,outcomes);
assert.deepEqual(plain(next),['c-c','q1','c-d','q3'],'Next round recomputes without it');
// Missed it keeps an item; a wrong pick on a multiple choice that was right puts it in
outcomes.q2={kind:'mcq',result:'missed'};
assert.deepEqual(plain(ctx.missedIds(order,outcomes)),['c-c','q1','c-d','q2','q3']);
// empty round
assert.deepEqual(plain(ctx.redoPlan(blocks,[])),{ctx:[],items:[]});
assert.equal(ctx.redoHeadHtml(0,0),'<span class="rdt">No misses left.</span><button type="button" class="rdback">Back to lesson</button>');
assert.equal(ctx.redoHeadHtml(5,4),'<span class="rdt">Redo · <span class="rdn">4 missed</span></span><button type="button" class="rdnext">Next round</button><button type="button" class="rdback">Back to lesson</button>');
assert.equal(ctx.redoRowHtml(3),'<span>3 missed problems</span> · <button type="button" class="rdgo">Redo them</button>');
assert.equal(ctx.redoRowHtml(1),'<span>1 missed problem</span> · <button type="button" class="rdgo">Redo it</button>');
console.log('PASS: redo rounds list the missed items in lesson order with their problems, keep a round fixed, and end at "No misses left."');

// wiring: the page hides everything but the round's marks; the round is applied from its fixed ids after every render;
// the row's count is the missed count XP computes; leaving to a heading or a flag ends the round
assert(source.includes('html.redo main>:not(#redohead,.rd-path,.rd-ctx){display:none}'));
assert(source.includes('html.redo .rd-path>:not(.rd-path,.rd){display:none}'));
assert(/function redoApply\(\)\{[\s\S]*?redoPlan\(bl\.map[\s\S]*?redo\.ids\);/.test(source),'a round applies its fixed ids');
assert(source.includes("redo.open=true; redo.ids=missedNow();"),'opening recomputes');
assert(source.includes("paintOutcomes(); if(redo.open)redoApply(); if(r.reset)restoreOutcomes();"));
assert(source.includes("redoPaint(missedIds(qs.map(e=>e.dataset.item),outcomes).length);"));
assert.equal((source.match(/\n  redoClose\(false\);\n/g)||[]).length,2,'tocGo and flagGo leave the round first');
console.log('PASS: the round is drawn in place from its fixed ids, re-applied after a re-render, and left for any jump');
