// Course route on the board: Lesson N of T with Previous / Next by the folder's study order (never `prev:`), the route's
// last lesson going back to the course, an older lesson outside the route keeping only All lessons, Continue studying
// from the last lesson opened, and the end of the video offering Practice / Next lesson / Back to course without moving on.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const tmpl=fs.readFileSync(path.join(__dirname,'../board/board.html.tmpl'),'utf8');
const js=fs.readFileSync(path.join(__dirname,'../board/lesson-video.js'),'utf8');
const grab=(src,name)=>{const a=src.indexOf('function '+name+'(');assert(a>0,name);const b=src.indexOf('\nfunction ',a+10);return src.slice(a,b);};
const plain=x=>JSON.parse(JSON.stringify(x));
const ctx={num:x=>typeof x==='number'&&isFinite(x),esc:s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')};vm.createContext(ctx);
for(const f of ['seqNav','contPick','navHtml'])vm.runInContext(grab(tmpl,f),ctx);
for(const f of ['endedAt','endLinks','routeHtml'])vm.runInContext(grab(js,f),ctx);

// the route is the configured order; 0001 is an older lesson that stays in the folder but not on the route
const seq={title:'Exam 3',total:3,lessons:[{id:'0006',title:'Variables'},{id:'0007',title:'Methods'},{id:'0008',title:'Programs'}]};
let n=plain(ctx.seqNav(seq,'0006','cs1331'));
assert.deepEqual(n,{all:'/w/cs1331/lessons',i:0,total:3,prev:null,next:{id:'0007',title:'Methods',href:'/w/cs1331/lessons/0007'},last:false},'first lesson');
n=plain(ctx.seqNav(seq,'0007','cs1331'));
assert.equal(n.prev.href,'/w/cs1331/lessons/0006'); assert.equal(n.next.href,'/w/cs1331/lessons/0008'); assert.equal(n.i+1,2);
n=plain(ctx.seqNav(seq,'0008','cs1331'));
assert.equal(n.next,null,'no Next after the last lesson'); assert.equal(n.last,true); assert.equal(n.prev.title,'Methods');
n=plain(ctx.seqNav(seq,'0001','cs1331'));
assert.deepEqual([n.i,n.prev,n.next,n.all],[-1,null,null,'/w/cs1331/lessons'],'an older lesson outside the route: All lessons only');
assert.equal(ctx.seqNav({lessons:[{id:'0006',title:''}]},'0006','').all,'/lessons','no folder slug: the plain hub');
assert.equal(ctx.seqNav({lessons:[{id:'0006',title:''},{id:'0009'}]},'0006','x').next.title,'Lesson 0009','untitled lesson');
assert.equal(ctx.seqNav(null,'0006','x').total,0,'no route at all');

// Continue studying: the last lesson opened, with where its video is; otherwise the start of the route
const route=seq.lessons;
assert.deepEqual(plain(ctx.contPick(route,null)),{i:0,label:'Start studying',note:''});
assert.deepEqual(plain(ctx.contPick(route,{id:'0007',at:1})),{i:1,label:'Continue studying',note:''});
assert.deepEqual(plain(ctx.contPick(route,{id:'0007',vt:252.4})),{i:1,label:'Continue studying',note:'Video at 4:12'});
assert.equal(ctx.contPick(route,{id:'0008',vt:600,vend:true}).note,'Video watched to the end');
assert.equal(ctx.contPick(route,{id:'0001',vt:30}).label,'Start studying','a lesson no longer on the route');

// a reload after the video ended stays ended; a pause shortly before the end is only a place to resume
assert.equal(ctx.endedAt({t:12,ended:true},600),true);
assert.equal(ctx.endedAt({t:599.97},600),true,'saved on the last frame before the ended flag existed');
assert.equal(ctx.endedAt({t:598.5},600),false);
assert.equal(ctx.endedAt({},600),false); assert.equal(ctx.endedAt(null,600),false);

// end of the video: Practice first (only when the lesson has a quiz), then the next lesson or the way back to the course
const mid=plain(ctx.seqNav(seq,'0007','cs1331')), last=plain(ctx.seqNav(seq,'0008','cs1331')), old=plain(ctx.seqNav(seq,'0001','cs1331'));
assert.deepEqual(plain(ctx.endLinks(mid,true)),[{a:'practice',label:'Practice this lesson',pri:true},{href:'/w/cs1331/lessons/0008',label:'Next lesson',title:'Programs'}]);
assert.deepEqual(plain(ctx.endLinks(last,true))[1],{href:'/w/cs1331/lessons',label:'Back to course'});
assert.deepEqual(plain(ctx.endLinks(mid,false)),[{a:'toread',label:'Back to the lesson'},{href:'/w/cs1331/lessons/0008',label:'Next lesson',title:'Programs',pri:true}],'no quiz: no dead Practice');
assert.equal(ctx.endLinks(old,true)[1].label,'All lessons');
assert.equal(ctx.endLinks(null,true).length,1,'a plain board: Practice only');
// the compact top row names the next lesson for screen readers; the page's last section is the titled pager
let h=ctx.navHtml(mid);
assert.match(h.top,/<a class="lnnext" href="\/w\/cs1331\/lessons\/0008" title="Programs" aria-label="Next lesson: Programs">Next ›<\/a>/);
assert.match(h.bot,/rel="prev"><span>‹ Previous<\/span><b>Variables<\/b>/); assert.match(h.bot,/rel="next"><span>Next ›<\/span><b>Programs<\/b>/);
h=ctx.navHtml(last); assert(!/lnnext/.test(h.top),'no top Next on the last lesson'); assert.match(h.bot,/href="\/w\/cs1331\/lessons"><span>Last lesson of the route<\/span><b>Back to course<\/b>/);
h=ctx.navHtml(old); assert.equal(h.bot,'','an older lesson has no pager'); assert(!/lnpos/.test(h.top));
// Watch keeps the course route (the text and its rows are hidden there): All lessons, the place, Previous and Next
const r=ctx.routeHtml(mid);
assert.match(r,/href="\/w\/cs1331\/lessons">‹ All lessons<\/a>/); assert.match(r,/Lesson <b>2<\/b> of 3/);
assert.match(r,/href="\/w\/cs1331\/lessons\/0006" rel="prev" title="Variables" aria-label="Previous lesson: Variables">‹ Prev<\/a>/);
assert.match(r,/href="\/w\/cs1331\/lessons\/0008" rel="next" title="Programs" aria-label="Next lesson: Programs">Next ›<\/a>/);
assert.match(ctx.routeHtml(last),/href="\/w\/cs1331\/lessons">Back to course<\/a>/); assert(!/rel="next"/.test(ctx.routeHtml(last)));
assert(!/rel="prev"/.test(ctx.routeHtml(plain(ctx.seqNav(seq,'0006','cs1331')))),'no Previous on the first lesson');
assert.equal(ctx.routeHtml(old),'<a class="lv-rall" href="/w/cs1331/lessons">‹ All lessons</a>','an older lesson: All lessons only');
assert.equal(ctx.routeHtml(null),'','a plain board: no route');
assert.match(ctx.routeHtml(plain(ctx.seqNav({lessons:[{id:'0001',title:'A <b>'},{id:'0002',title:'"x"'}]},'0001','w'))),/aria-label="Next lesson: &quot;x&quot;"/,'titles escaped');
// the route never reuses the player's in-lesson Next explanation
assert(!/navNext\(\)/.test(grab(js,'routeHtml')+grab(js,'paintRoute')));
// nothing moves on by itself: the player never navigates, the end card only holds links
assert(!/location\.(href|assign|replace)\s*[=(]/.test(js),'the video never changes page');
console.log('lesson route ok');
