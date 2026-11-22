// Step sources: a phrase tagged in the quoted problem ([words]{#id}) lights when a solution step citing it ({@id}) is shown.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../board/board.html.tmpl'),'utf8');
const grab=name=>{const a=source.indexOf('function '+name+'(');assert(a>0,name);const b=source.indexOf('\nfunction ',a+10);return source.slice(a,b);};
const ctx={};vm.createContext(ctx);
vm.runInContext(source.match(/^const GTAG=.*$/m)[0].replace(/^const /,'var '),ctx);
for(const f of ['srcIds','stripRefs','texRefs','stepSrcMd','rvSrc'])vm.runInContext(grab(f),ctx);

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

// Next step lights the refs of the step just shown; Show all / before step 1 lights nothing
const lit=[];let cleared=0;
Object.assign(ctx,{GSRC:{el:null},srcLight:(el,ids)=>lit.push([el.name,[...ids]]),srcClear:()=>{cleared++;},
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
assert(/@media print\{\.gchip\{display:none\}/.test(source),'print shows no chip');
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
