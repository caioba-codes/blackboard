// Problem labels (TEMPLATES.md, Official problems): an Official label links into the source viewer at its page and sits
// on its own small line; "Written by Claude" too; a verbatim official MCQ may keep a count other than four (bin/lint.py).
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),cp=require('node:child_process'),os=require('node:os');
const source=fs.readFileSync(path.join(__dirname,'../board/board.html.tmpl'),'utf8');
const a=source.indexOf('function provLabels(html)'),b=source.indexOf('\nfunction ',a+10);
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const ctx={esc,WSB:'/w/ece2020',decodeURI,encodeURI,JSON};vm.createContext(ctx);vm.runInContext(source.slice(a,b),ctx);
const off=ctx.provLabels('<p><a href="src:exams2/fa18-kj-e2.pdf#page=6">Official · Fall 2018 Exam 2, Q3b</a></p>');
assert.match(off,/^<p class="plabel"><a class="srclink plabel-i" href="\/w\/ece2020\/source\/exams2\/fa18-kj-e2.pdf"/);
const f=JSON.parse(off.match(/data-src="([^"]+)"/)[1].replace(/&quot;/g,'"'));
assert.equal(f.page,6); assert.equal(f.kind,'pdf'); assert.equal(f.path,'exams2/fa18-kj-e2.pdf');
assert.equal(ctx.provLabels('<p><em>Written by Claude</em></p>'),'<p class="plabel">Written by Claude</p>');
assert.match(ctx.provLabels('<em>Written by Claude</em> Integrate x.'),/^<span class="plabel-i">Written by Claude<\/span>Integrate x\./);
assert(ctx.provLabels('<p>see <a href="https://x.org">x</a></p>').includes('href="https://x.org"'),'web links untouched');
// lint
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'lbl-')); fs.mkdirSync(path.join(dir,'lessons')); fs.mkdirSync(path.join(dir,'sources/exams2'),{recursive:true});
fs.writeFileSync(path.join(dir,'sources/exams2/e.pdf'),'%PDF');
const lesson=path.join(dir,'lessons/0001-x.md');
const run=t=>{fs.writeFileSync(lesson,t);return cp.spawnSync('python3',[path.join(__dirname,'../bin/lint.py'),lesson],{encoding:'utf8'}).stderr;};
let w=run('# T\n\n::: mcq q1 a\nStem\n- a\n- b\n- c\n- d\n:::\n');
assert.match(w,/without a label/);
w=run('# T\n\n[Official · Fall 2018 Exam 2, Q1](src:exams2/e.pdf#page=2)\n\n::: mcq q1 a\nStem\n- a\n- b\n- c\n- d\n- e\n:::\n');
assert(!/without a label|options;/.test(w),w);
w=run('# T\n\n*Written by Claude*\n\n::: mcq q1 a\nStem\n- a\n- b\n- c\n:::\n');
assert.match(w,/3 options/);
w=run('# T\n\n[Official · X](src:exams2/missing.pdf#page=1)\n\n::: checkin\n- Q || A\n:::\n');
assert.match(w,/is not a file/);
w=run('# T\n\n::: checkin\n- [Official · X](src:exams2/e.pdf#page=1) Q || A\n- Q2 || A2\n:::\n');
assert.match(w,/check-in item without a label/); assert.equal((w.match(/check-in item without/g)||[]).length,1);
console.log('PASS: problem labels link to the source page; lint flags unlabeled problems, missing sources and non-official option counts');
