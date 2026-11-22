// Step sources: a phrase tagged in the quoted problem ([words]{#id}) lights when a solution step citing it ({@id}) is shown.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../board/board.html.tmpl'),'utf8');
// the board's whole script must parse: one duplicate name (a let and a function) blanks every lesson
const boardScript=[...source.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).sort((a,b)=>b.length-a.length)[0];
assert.doesNotThrow(()=>new vm.Script(boardScript),'board script parses');
const grab=name=>{const a=source.indexOf('function '+name+'(');assert(a>0,name);const b=source.indexOf('\nfunction ',a+10);return source.slice(a,b);};
const ctx={};vm.createContext(ctx);
vm.runInContext(source.match(/^const GTAG=.*$/m)[0].replace(/^const /,'var '),ctx);
vm.runInContext(source.match(/^const GLINE=.*$/m)[0].replace(/^const /,'var '),ctx);
vm.runInContext(source.match(/^const before=.*$/m)[0].replace(/^const /,'var '),ctx);
for(const f of ['srcIds','stripRefs','texRefs','stepSrcMd','codeName','srcTags','srcCodeLines','rvSrc'])vm.runInContext(grab(f),ctx);

// tags wrap the problem's words without changing them
const g=ctx.stepSrcMd('The machine [starts in state E]{#start} and must [output 1 on XYZ]{#out}.');
assert.equal(g,'The machine <span class="gtag" data-g="start">starts in state E</span> and must <span class="gtag" data-g="out">output 1 on XYZ</span>.');
assert.equal(g.replace(/<[^>]+>/g,''),'The machine starts in state E and must output 1 on XYZ.','the quoted words are unchanged');
// a step's refs become an empty marker; several ids in one ref
assert.equal(ctx.stepSrcMd('Start at E, from the first line. {@start}'),'Start at E, from the first line. <span class="gref" data-refs="start"></span>');
assert.match(ctx.stepSrcMd('Go through B. {@start @out}'),/data-refs="start out"/);
// fenced code is left as written, and a lesson without tags is untouched
const code='```java\nint[] a = {1};\nString s = "[x]{#y} {@y}";\n```';
assert.equal(ctx.stepSrcMd('x {@a}\n\n'+code),'x <span class="gref" data-refs="a"></span>\n\n'+code);
const old='Plain [link](http://x) and a set {1, 2} and $x$.';
assert.equal(ctx.stepSrcMd(old),old,'old lessons render exactly as before');
// in math: an empty \htmlData mark carries the ids; copy/Explain read the TeX with the ref removed
assert.equal(ctx.texRefs('x &= E && \\text{start state} {@start}'),'x &= E && \\text{start state} \\htmlData{gref=start}{}');
assert.equal(ctx.stripRefs('x &= E && \\text{start state} {@start}'),'x &= E && \\text{start state}');
assert.equal(ctx.texRefs('\\frac{1}{2}'),'\\frac{1}{2}');
assert.deepEqual([...ctx.srcIds('@a  b @c')],['a','b','c']);

// code lines: {@L3}, {@L3-5}, {@node:L2-4}; a named fence keeps its code, loses only the name from its info string
assert.match(ctx.stepSrcMd('Line 3 builds the node. {@node:L2-4 @L3}'),/data-refs="node:L2-4 L3"/);
const named='```java {#node}\nclass Node {\n  int v;\n}\n```';
const wrapped=ctx.codeName(named);
assert.equal(wrapped,'<div class="gcode" data-gcode="node">\n\n```java\nclass Node {\n  int v;\n}\n```\n\n</div>');
assert.equal(ctx.codeName('```java\nint x;\n```'),'```java\nint x;\n```','an unnamed fence is untouched');
assert.equal(JSON.stringify('L3 L3-5 node:L2'.split(' ').map(x=>[...x.match(ctx.GLINE).slice(1)])),JSON.stringify([[null,'3',null],[null,'3','5'],['node','2',null]]));
assert(!ctx.GLINE.test('start'),'a word tag is not a line ref');

// a tiny DOM: elements in document order, each knowing its card
const FOLLOW=4; let order=0;
const node=(o)=>Object.assign({pos:order++,compareDocumentPosition(other){return other.pos>this.pos?FOLLOW:2;}},o);
const card=(sel,kids)=>{ const c=node({sel,kids:[]}); kids.forEach(k=>{k.card=c;c.kids.push(k);}); c.querySelectorAll=()=>c.kids.filter(k=>k.dataset&&k.dataset.g); return c; };
// a problem quoted over two pages: two labels, two given cards, each with its own tag; then an mcq stem with a tag
const t1=node({dataset:{g:'start'},closest:()=>c1}), c1=card('.given',[t1]);
const t2=node({dataset:{g:'out'},closest:()=>c2}), c2=card('.given',[t2]);
const pre1=node({}), pre2=node({named:'node'});
const step=node({});
const mt=node({dataset:{g:'stem'},closest:()=>mc}), mc=card('.mcqi .q',[mt]);
ctx.Node={DOCUMENT_POSITION_FOLLOWING:FOLLOW};
ctx.main={querySelectorAll:q=>q==='[data-g]'?[t1,t2,mt]:q.includes('data-gcode="node"')?[pre2]:[pre1,pre2]};
assert.equal(ctx.srcTags(step,['start','out']).map(t=>t.dataset.g).join(),'start,out','a step cites tags on both pages of its problem');
assert.equal(ctx.srcTags(step,['stem']).length,0,'a later mcq stem is not part of this problem');
assert.equal(ctx.srcCodeLines(step,['node:L2-4'])[0].pre,pre2,'a named block');
assert.deepEqual(JSON.parse(JSON.stringify(ctx.srcCodeLines(step,['L3']).map(l=>[l.from,l.to]))),[[3,3]],'the last code block before the step');
assert.equal(ctx.srcTags(step,['L3']).length,0,'line refs are not tags');

// Next step lights the refs of the step just shown; Show all / before step 1 lights nothing
const lit=[];let cleared=0;
delete ctx.main; Object.assign(ctx,{GSRC:{el:null},srcLight:(el,ids)=>lit.push([el.name,[...ids]]),srcClear:()=>{cleared++;},
  stepRefs:(el,row)=>(el.refs&&el.refs[row==null?'all':row])||[]});
const box={contains:()=>true,_rv:{k:1,items:[{el:{name:'lead',refs:{all:['arr']}}},{el:{name:'grid',refs:{all:['start']}}},{el:{name:'rows',refs:{0:[],1:['out']}}}],
  plan:{lead:[{i:0,row:null}],steps:[[{i:1,row:null}],[{i:2,row:0}],[{i:2,row:1}]]}}};
ctx.rvSrc(box); assert.deepEqual(lit.pop(),['grid',['arr','start']],'step 1 lights its lead line (a code label) and the setup');
box._rv.k=2; ctx.GSRC.el={}; ctx.rvSrc(box); assert.equal(lit.length,0); assert.equal(cleared,1,'a step citing nothing clears the light');
box._rv.k=3; ctx.rvSrc(box); assert.deepEqual(lit.pop(),['rows',['out']],'row 2 lights the output requirement');
box._rv.k=0; ctx.GSRC.el={}; ctx.rvSrc(box); assert.equal(cleared,2,'nothing is lit before the first step (a Your turn after a wrong pick)');

// wiring: Next lights, Show all and closing clear, opening lights step 1, links are wired on every re-fit, md() runs it
assert(source.includes("rvGo(box,st.k+1); rvSrc(box);"));
assert(source.includes("rvGo(box,n); if(GSRC.el&&box.contains(GSRC.el))srcClear();"));
assert(source.includes("if(!d.open&&GSRC.el&&d.contains(GSRC.el))srcClear();"));
assert(source.includes("whyWire(); srcWire();"));
assert(source.includes("marked.parse(stepSrcMd(s2)"));
assert(source.includes("main.addEventListener('focusin'")&&source.includes("main.addEventListener('click',e=>{ const h=srcHost"),'keyboard and tap');
assert(/@media print\{\.gchip,\.gline\{display:none\}/.test(source),"print shows no chip and no line band");
// video engine: quoted text shows tags as lightable words and never shows a ref; S.src lights only inside its spans
const engine=fs.readFileSync(path.join(__dirname,'../video/engine.js'),'utf8');
const vctx={};vm.createContext(vctx);
vm.runInContext(engine.match(/^\s*const srcMarkup = .*$/m)[0].replace(/const /,'var '),vctx);
const fa=engine.indexOf('  function src(root'),fb=engine.indexOf('\n  }\n',fa)+4;vm.runInContext(engine.slice(fa,fb),vctx);
assert.equal(vctx.srcMarkup('Start at E. {@start}'),'Start at E. ');
assert.equal(vctx.srcMarkup('The machine [starts in state E]{#start}.'),'The machine <span class="gtag" data-g="start">starts in state E</span>.');
const tagEl={on:false,classList:{toggle:(k,v)=>{tagEl.on=v;}}};
const vroot={querySelectorAll:q=>q.includes('"start"')?[tagEl]:[]};
vctx.src(vroot,'start',1,[[2,4]]); assert.equal(tagEl.on,false,'not lit before its step (a Your turn before the pause)');
vctx.src(vroot,'start',3,[[2,4]]); assert.equal(tagEl.on,true,'lit while its step is narrated');
vctx.src(vroot,['start'],4,[[2,4]]); assert.equal(tagEl.on,false,'cleared when the next step starts');
assert(engine.includes("src: (ids, t, spans) => src(root, ids, t, spans),"),'scenes get S.src');
console.log('PASS: step sources tag the problem, steps cite it, Next step lights it, old lessons are unchanged');
