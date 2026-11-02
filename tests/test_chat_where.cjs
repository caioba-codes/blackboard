// The chip under the chat box says what the chat will assume: the video's time, chapter and scene, else the section in
// view. Each message carries it as `where` unless the chip was tapped away for that message.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../board/board.html.tmpl'),'utf8');
const a=source.indexOf('function chatWhereLabel(w)'),b=source.indexOf('\nfunction ',a+10);
const ctx={};vm.createContext(ctx);vm.runInContext(source.slice(a,b),ctx);
assert.equal(ctx.chatWhereLabel({source:'video',time:'2:06:20',chapter:'Chapter 5 · Multiplexers',segment:'Your turn: constants 1,0,0,0 → which gate (sp12)',practice:{label:'Your turn: which gate? (sp12)'}}),'Video 2:06:20 · Ch 5 · Your turn: which gate? (sp12)');
assert.equal(ctx.chatWhereLabel({source:'video',time:'0:04:10',chapter:'Chapter 1 · Bases',segment:'Read hexadecimal'}),'Video 0:04:10 · Ch 1 · Read hexadecimal');
assert.equal(ctx.chatWhereLabel({source:'reading',chapter:'Chapter 2 · Signed',section:{heading:'Negate'}}),'Reading · Ch 2 · Negate');
assert.equal(ctx.chatWhereLabel({source:'reading',chapter:'Quiz',section:{heading:'Quiz'}}),'Reading · Quiz');
assert.equal(ctx.chatWhereLabel(null),'');
assert(source.includes('viewing:srcViewing()},WS?{ws:WS}:{},chatWhereSend()))'),'every message sends where');
assert(/LessonVideo&&typeof LessonVideo\.context==='function'\?LessonVideo\.context\(\):null; \}catch\(_\)/.test(source),'works before lesson-video.js has context()');
assert(source.includes("$('#chatwhere').onclick=()=>{ chat.whereOff=true;"),'tapping the chip leaves it out of the next message');
console.log('PASS: the chat chip names the video scene or the section in view, and each message sends it as where');
