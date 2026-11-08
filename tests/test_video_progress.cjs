// Video progress card: the stage line with its real counts, the measured time left, a stall, and a stage with no total.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const js=fs.readFileSync(path.join(__dirname,'../board/lesson-video.js'),'utf8');
const grab=name=>{const a=js.indexOf('function '+name+'(');assert(a>0,name);const b=js.indexOf('\nfunction ',a+10);return js.slice(a,b);};
const ctx={num:x=>typeof x==='number'&&isFinite(x)};vm.createContext(ctx);
for(const f of ['n0','left','progressText'])vm.runInContext(grab(f),ctx);
const stages=(cur)=>['script','narration','scenes','render','review','import'].map(k=>({key:k,label:k[0].toUpperCase()+k.slice(1),...(cur[k]||{})}));

let d={stage:'narration',stageIndex:2,stageCount:6,eta:3840,stalled:false,now:5000,lastProgress:4990,
  stages:stages({narration:{done:412,total:1899,unit:'lines',percent:21.7}})};
assert.deepEqual({...ctx.progressText(d)},{line:'Narration · 412 / 1,899 lines · 21%',meta:'Stage 2 of 6 · about 1 h 4 min left in narration'});

d={...d,stage:'render',stageIndex:4,eta:45,stages:stages({render:{done:37,total:247,unit:'chunks',percent:15}})};
assert.equal(ctx.progressText(d).line,'Render · 37 / 247 chunks · 15%');
assert.equal(ctx.progressText(d).meta,'Stage 4 of 6 · under a minute left in render');

d={...d,eta:null,stalled:true,now:5000,lastProgress:5000-14*60};
assert.equal(ctx.progressText(d).meta,'Stage 4 of 6 · no new progress for 14 min','a stall replaces the time left');

d={stage:'scenes',stageIndex:3,stageCount:6,eta:null,stalled:false,stages:stages({scenes:{done:0,total:null,unit:'modules',percent:0}})};
assert.deepEqual({...ctx.progressText(d)},{line:'Scenes',meta:'Stage 3 of 6'},'no SPLIT.json yet: no made-up total');

d={stage:'render',stageIndex:4,stageCount:6,eta:null,stalled:false,stages:stages({render:{done:247,total:247,unit:'chunks',percent:100,note:'joining and muxing'}})};
assert.equal(ctx.progressText(d).line,'Render · 247 / 247 chunks · joining and muxing');
console.log('video progress card ok');
