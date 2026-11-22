// Self-marking: every check-in answer ends with Got it / Missed it, each row gets a stable id from its own text (same text,
// same id; an edit, a new id; exact duplicates a -2 suffix), and a Got it counts like a right multiple-choice pick in the
// chapter stars and XP.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../board/board.html.tmpl'),'utf8');
const fn=name=>{const a=source.indexOf('function '+name+'(');assert(a>0,name);return source.slice(a,source.indexOf('\nfunction ',a+10));};
const line=p=>{const a=source.indexOf(p);assert(a>0,p);return source.slice(a,source.indexOf('\n',a));};
const ctx={md:s=>s,mdInline:s=>s,esc:s=>s,mdBlocks:s=>s,outcomes:{}};vm.createContext(ctx);
vm.runInContext([fn('textHash'),line('const ckId='),line('const occurrenceIds='),line('const quizItems='),line('const itemResult='),fn('tocStats'),fn('container')]
  .join('\n').replace(/^const /gm,'var '),ctx);
const ids=raw=>[...ctx.container(raw).matchAll(/data-ck="([^"]+)"/g)].map(m=>m[1]);

const lesson='::: checkin\n- What is $1+1$? || $2$\n- Fill in the grey boxes. || Done.\n:::';
const html=ctx.container(lesson);
assert.deepEqual(ids(lesson),['c-uy8fbv','c-1h0fueu']);
assert.equal((html.match(/<div class="smark" role="group" aria-label="Mark this answer"><button type="button" class="smbtn" data-r="got" aria-pressed="false">Got it<\/button><button type="button" class="smbtn" data-r="missed" aria-pressed="false">Missed it<\/button><\/div><\/details>/g)||[]).length,2,'both rows end with the two buttons, after the answer');
assert.deepEqual(ids(lesson),ids(lesson),'a re-render keeps the ids');
assert.deepEqual(ids('::: checkin\n-   What is $1+1$?   ||   $2$\n:::'),['c-uy8fbv'],'spacing does not change the id');
assert.deepEqual(ids('::: checkin\n- What is $1+2$? || $2$\n:::'),['c-ph10n0'],'an edited question is a new item');
assert.deepEqual(ids('::: checkin\n- What is $1+1$? || $3$\n:::'),['c-uy8fcs'],'an edited answer is a new item');
assert.deepEqual(ids('::: checkin\n- Same row || x\n- Same row || x\n:::'),['c-divuyb','c-divuyb'],'exact duplicates share a base id');
assert.deepEqual(ctx.occurrenceIds(['c-a','c-b','c-a','c-a']),['c-a','c-b','c-a-2','c-a-3'],'then get -2, -3 in reading order');
console.log('PASS: check-in rows end with Got it / Missed it and keep ids derived from their text; duplicates get a suffix');

// chapter stars: a Got it counts like a right pick; Missed it and unmarked rows do not
const el=item=>({dataset:{item}});
const blk={querySelectorAll:sel=>(assert.equal(sel,'.mcqi, .check > details'),[el('q1'),el('c-uy8fbv'),el('c-1h0fueu'),el('q2')])};
ctx.outcomes={q1:{kind:'mcq',result:'got'},'c-uy8fbv':{kind:'self',result:'got'},'c-1h0fueu':{kind:'self',result:'missed'},q2:{kind:'mcq',result:'missed'}};
assert.deepEqual({...ctx.tocStats({blocks:[blk]})},{total:4,right:2});
ctx.outcomes['c-1h0fueu']={kind:'self',result:'got'};
assert.deepEqual({...ctx.tocStats({blocks:[blk]})},{total:4,right:3},'changing Missed it to Got it adds a star');
// wiring: XP reads the same outcomes; a render paints them, a reset refetches them after pending marks land
assert(source.includes("const got=qs.filter(e=>itemResult(e)==='got').length+"));
assert(source.includes("paintOutcomes(); if(r.reset)restoreOutcomes();"));
assert(/async function restoreOutcomes\(\)\{\n  if\(!lessonId\)return;\n  await logQ;/.test(source));
console.log('PASS: Got it counts in chapter stars and XP like a right multiple-choice pick');
