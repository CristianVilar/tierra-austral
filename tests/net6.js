// Escenarios del multijugador: ventanas de invitados, tratos entre humanos, 7, desconexión, permisos
const {JSDOM}=require('jsdom');const fs=require('fs');const {CompressionStream,DecompressionStream}=require('stream/web');
const HTML=fs.readFileSync('/home/claude/game/index.html','utf8');
const errs=[];let fails=0;
process.on('unhandledRejection',e=>{errs.push('UN '+(e&&e.stack||e));console.log('UNHANDLED',String(e&&e.stack||e).slice(0,500));});
const ok=(c,m)=>{if(!c)fails++;console.log(c?'OK  ':'FALLA',m);};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const rooms={};
function transport(){return{
  async create(c){if(rooms[c])return false;rooms[c]={cl:[],status:'lobby'};return true;},
  async exists(c){return !!rooms[c]&&rooms[c].status!=='ended';},
  setStatus(c,s){if(rooms[c])rooms[c].status=s;},
  setList(c,o){if(rooms[c])Object.assign(rooms[c],o);},
  async list(){return Object.entries(rooms).filter(([c,r])=>r.pub&&r.status==='lobby').map(([c,r])=>({code:c,host_name:r.host_name,n:r.n,mx:r.mx}));},
  async open(code,onMsg){const me={onMsg,dead:false};rooms[code].cl.push(me);
    return{send:m=>{if(me.dead)return;const j=JSON.stringify(m);for(const o of rooms[code].cl)if(o!==me&&!o.dead)setTimeout(()=>{if(!o.dead)o.onMsg(JSON.parse(j));},1);},close:()=>{me.dead=true;}};}};}
function mk(name){
  const dom=new JSDOM(HTML,{runScripts:'dangerously',pretendToBeVisual:true,url:'https://test.local/',beforeParse(w){
    w.AudioContext=undefined;w.CompressionStream=CompressionStream;w.DecompressionStream=DecompressionStream;w.TextEncoder=TextEncoder;w.TextDecoder=TextDecoder;Object.defineProperty(w,'crypto',{value:require('crypto').webcrypto,configurable:true});w.Response=Response;w.__T=transport();}});
  const w=dom.window,ev=w.eval;
  w.addEventListener('error',e=>errs.push(name+': '+e.message));w.onerror=m=>errs.push(name+': '+String(m));
  ev("NETT=__T;NET.beatMs=60;NET.pingMs=60;NET.offMs=6000;NET.staleMs=500;NET.lostMs=600;");
  return{name,dom,w,ev,$:s=>w.document.querySelector(s),$$:s=>[...w.document.querySelectorAll(s)]};
}
async function until(f,ms=3000,step=12){const t=Date.now();while(Date.now()-t<ms){try{if(f())return true;}catch(e){}await sleep(step);}return false;}
const click=el=>el&&el.dispatchEvent(new el.ownerDocument.defaultView.MouseEvent('click',{bubbles:true,cancelable:true}));
const cons=c=>c.ev("RES.every(r=>G.bank[r]+G.players.reduce((s,p)=>s+p.res[r],0)===19)");
const J=x=>JSON.stringify(x);
const give=(A,pid,o)=>A.ev(`(function(){const p=G.players[${pid}],o=${J(o)};for(const r in o){p.res[r]+=o[r];G.bank[r]-=o[r];}})()`);
const clear=A=>A.ev("(function(){for(const p of G.players)for(const r of RES){G.bank[r]+=p.res[r];p.res[r]=0;}})()");
const res=(A,pid)=>J(A.ev(`G.players[${pid}].res`));
// crea sala con 3 humanos + 1 IA, coloca el inicio por API y deja a todos en el turno 0 en fase roll
async function room(rules){
  const A=mk('Ana'),B=mk('Beto'),C=mk('Caro');
  await A.ev("netCreate('Ana')");const code=A.ev("NET.code");
  await B.ev(`netJoin('${code}','Beto')`);await C.ev(`netJoin('${code}','Caro')`);
  await until(()=>A.ev("NET.roster.length")===3&&C.ev("NET.seat")===2);
  A.ev("NET.inLobby=false;showStart();document.getElementById('c-speed').value='0';");
  A.ev("startFromForm()");
  await until(()=>B.ev("NET.started")&&C.ev("NET.started"));
  // colocar a todos rápido (API del motor)
  A.ev(`(function(){G.rules={...G.rules,...${J(rules||{})}};G.phase='setupBot';G.busy=false;
    G.setupSeq.forEach((pid,idx)=>{G.cur=pid;const l=legalSettle(pid,true),v=l[(idx*7)%l.length];placeSettle(pid,v,true);if(idx>=G.n)grantStart(pid,v);const rl=legalRoads(pid,v);placeRoad(pid,rl[0],true);});
    G.setupIdx=G.setupSeq.length;beginPlay();G.fresh=null;})()`);
  await until(()=>A.ev("G.phase")==='roll'&&A.ev("G.cur")===0);
  return{A,B,C,code,P:[A,B,C]};
}
// pone el turno en un asiento, en fase main, con el motor en reposo
const turn=async(R,seat,ph)=>{R.A.ev(`(function(){G.cur=${seat};G.phase='${ph||'main'}';G.mode=null;G.busy=false;G.devPlayed=false;G.undo=null;G.msg='';render();})()`);await sleep(120);};
const btn=(P,oc)=>P.$$(`[data-oc="${oc}"]`).find(b=>!b.disabled);

(async()=>{
  // --- sala pública y expulsión en la antesala
  const A=mk('Ana'),B=mk('Beto'),X=mk('Xavi');
  await A.ev("netCreate('Ana')");const code=A.ev("NET.code");
  ok(!rooms[code].pub,'la sala nace privada');
  A.ev("netSetPub(true)");await sleep(50);
  ok(rooms[code].pub===true&&rooms[code].host_name==='Ana','al marcarla pública aparece en la lista');
  await X.ev("showPublicRooms()");await until(()=>X.$('#publist')&&/Sala de Ana/.test(X.$('#publist').textContent));
  ok(/Sala de Ana/.test(X.$('#publist').textContent),'otro jugador ve la sala en «Salas abiertas»');
  const jb=X.$$('#publist button')[0];click(jb);
  ok(await until(()=>X.ev("NET.seat")===1),'entra a la sala sin escribir el código');
  ok(await until(()=>A.ev("NET.roster.length")===2&&rooms[code].n===2),'la lista muestra 2 jugadores');
  await B.ev(`netJoin('${code}','Beto')`);ok(await until(()=>A.ev("NET.roster.length")===3),'entra Beto');
  const xid=A.ev("NET.roster.find(r=>r.seat===1).id");
  A.ev(`netKick('${xid}')`);
  ok(await until(()=>X.ev("NET.role")===null),'el anfitrión expulsa a Xavi y él vuelve al menú');
  ok(A.ev("NET.roster.length")===2&&A.ev("NET.roster.map(r=>r.seat).join()")==='0,1','los asientos se reacomodan');
  await X.ev(`netJoin('${code}','Xavi')`);await sleep(300);
  ok(A.ev("NET.roster.length")===2,'un expulsado no puede volver a entrar');
  // --- partida: voto para reemplazar a quien no responde
  const C=mk('Caro');await C.ev(`netJoin('${code}','Caro')`);await until(()=>A.ev("NET.roster.length")===3);
  A.ev("NET.inLobby=false;showStart();document.getElementById('c-speed').value='0';");A.ev("startFromForm()");
  await until(()=>B.ev("NET.started")&&C.ev("NET.started"));
  ok(rooms[code].status==='playing','al empezar sale de la lista (estado playing)');
  A.ev("(function(){G.paused=true;})()");
  C.ev("clearInterval(NET.hb)"); // Caro deja de dar señales
  ok(await until(()=>B.$('#stalebar')&&/Caro no responde/.test(B.$('#stalebar').textContent),3000),'los demás ven «Caro no responde» antes de los 20 s');
  ok(!!A.$('#stalebar'),'el anfitrión también lo ve (con botón para expulsar)');
  ok(!C.$('#stalebar'),'Caro no ve el aviso sobre sí misma');
  ok(A.ev("G.cfg.humans.includes(2)"),'todavía la juega Caro');
  click(B.$$('#stalebar button')[0]);await sleep(200);
  ok(A.ev("G.cfg.humans.includes(2)"),'un solo voto no alcanza (1/2)');
  click(A.$$('#stalebar button')[0]);
  ok(await until(()=>!A.ev("G.cfg.humans.includes(2)")),'con mayoría un bot juega por Caro');
  ok(await until(()=>!B.$('#stalebar')),'el aviso desaparece');
  // --- expulsar en plena partida
  const bid=A.ev("NET.roster.find(r=>r.name==='Beto').id");
  A.ev(`netKick('${bid}')`);
  ok(await until(()=>B.ev("NET.role")===null),'el anfitrión expulsa a Beto en plena partida');
  ok(!A.ev("G.cfg.humans.includes(1)"),'su asiento pasa a bot');
  console.log('errores',errs.length,errs.slice(0,5),'FALLAS',fails);process.exit(0);
})();
