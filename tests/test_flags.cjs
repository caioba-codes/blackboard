// Flags on the page: a stored flag finds its item again after the lesson is rewritten (anchor, then the same label, then
// the same opening words), shows "moved or removed" when nothing matches, and list rows escape what they print.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../board/board.html.tmpl'),'utf8');
const a=source.indexOf('const FLAG_ICON='),b=source.indexOf('async function flagPost(');
assert(a>0&&b>a,'flag helpers present');
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const ctx={esc,Date};vm.createContext(ctx);vm.runInContext(source.slice(a,b).replace(/^(const|let) /gm,'var '),ctx);
const key=t=>ctx.flagNorm(t).slice(0,48);
const T=(anchor,kind,label,needle)=>({anchor,kind,label,needle,key:key(needle||label)});
const page=[T('s-chapter-2-signed-numbers','chapter','Chapter 2 · Signed Numbers'),
  T('f-official-fall-2018-exam-2-q3b-2','question','Official · Fall 2018 Exam 2, Q3b'),
  T('q-r10oc1a','question','Official · Practice set 08ns_01, row 3'),
  T('f-fill-in-the-grey-boxes','question','Fill in the grey boxes for 3A916.')];
const R=f=>ctx.flagResolve(f,page);
assert.equal(R({anchor:'q-r10oc1a',kind:'question'}),page[2],'by anchor');
assert.equal(R({anchor:'f-official-fall-2018-exam-2-q3b',kind:'question',label:'Official · Fall 2018 Exam 2, Q3b'}),page[1],'same label under a new anchor');
assert.equal(R({anchor:'q-old-id',kind:'question',label:'',needle:key('Fill in the grey boxes for 3A916. Then explain')}),page[3],'same opening words');
assert.equal(R({anchor:'s-chapter-2-signed-numbers-and-ranges',kind:'chapter',label:'Chapter 2 · Signed Numbers and Ranges',needle:key('Chapter 2 · Signed Numbers')}),page[0],'renamed heading by its opening words');
assert.equal(R({anchor:'f-x',kind:'example',label:'Official · Fall 2018 Exam 2, Q3b'}),null,'kind must match');
assert.equal(R({anchor:'f-official-spring-1999-exam-2-q9',kind:'question',label:'Official · Spring 1999 Exam 2, Q9',needle:key('Official · Spring 1999 Exam 2, Q9')}),null,'gone');
assert.equal(R({anchor:'f-y',kind:'question',needle:'fill'}),null,'a needle under 8 letters never matches');
assert.equal(ctx.flagSlug('Official · Fall 2018 Exam 2, Q3b'),'official-fall-2018-exam-2-q3b');
assert.equal(ctx.flagNorm('Décimal $426$, Q3b'),'decimal426q3b');
// rows
const row=ctx.flagRow({id:'ab',anchor:'q-1',kind:'question',label:'<b>x</b>',chapter:'Chapter 1 · "A"',note:'<i>n</i>',added:new Date().toISOString(),gone:true},{href:'/w/ece/lessons/0010#flag=q-1',ws:'ece',lesson:'ECE · 0010',q:'x'});
assert(!/<b>x|<i>n/.test(row),'label and note escaped');
assert.match(row,/moved or removed/); assert.match(row,/class="flrow gone"/); assert.match(row,/href="\/w\/ece\/lessons\/0010#flag=q-1"/);
assert.match(row,/ECE · 0010 · Chapter 1 · &quot;A&quot; · <span title="[^"]*">flagged just now<\/span>/);
assert.match(row,/aria-label="Unflag &lt;b&gt;x&lt;\/b&gt;"/);
assert(!/flagged/.test(ctx.flagRow({id:'c',anchor:'s-a',kind:'chapter',label:'Ch',chapter:'Ch',added:''},{href:'#s-a'}).replace(/class="fl\w+/g,'')),'no date, no chapter repeat');
// wiring: the flag button never leaks into the level map labels; f only fires outside text fields and outside the video
assert(source.includes("c.querySelectorAll('.tag,.katex-mathml,.chalkdeco,.flagbtn')"));
assert(source.includes("t.host.append(b)"),'appended, so "p > strong:first-child" still finds worked examples');
assert(/else if\(e\.key==='f'&&flagTargets\.length&&!document\.documentElement\.matches\('\.lv-watch,\.lv-fsmode'\)/.test(source));
console.log('PASS: flags resolve by anchor, label, then opening words; missing ones read "moved or removed"; rows escape their text');
