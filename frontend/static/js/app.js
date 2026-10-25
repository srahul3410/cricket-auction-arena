const $ = s => document.querySelector(s), app = $('#app');
let S = null, me = JSON.parse(localStorage.getItem('arena') || 'null'), view = 'home', sock = null;
const cr = l => '₹' + (l / 100).toFixed(2).replace(/\.?0+$/, '') + ' cr';
const esc = t => String(t).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function toast(m){const t=$('#toast');t.textContent=m;t.style.display='block';setTimeout(()=>t.style.display='none',2500)}
async function api(u, body){const r=await fetch(u,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const d=await r.json();if(!r.ok)throw new Error(d.error||'Request failed');return d}
function connect(){ if(!me||sock) return; sock=io(); sock.on('connect',()=>sock.emit('hello',{token:me.token}));
  sock.on('state',s=>{S=s;if(view==='home'&&s.status!=='lobby')view='auction';render()}); sock.on('err',toast); }
const act=(kind,amount)=>sock.emit('action',{token:me.token,kind,amount});
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{view=b.dataset.v;render()});
async function render(){ ({home,players,auction,report}[view])(); }
function home(){
  if(me&&S) return app.innerHTML=`<div class="panel"><h2>Room ${S.code}</h2><p class="mute">Share this code. Teams joined: ${Object.values(S.teams).map(t=>esc(t.name)).join(', ')} (${Object.keys(S.teams).length}/${S.settings.teams})</p>
   ${me.host?`<button class="primary" id="go">Start auction</button>`:'<p>Waiting for the host to start.</p>'}</div>`, $('#go')&&($('#go').onclick=()=>act('start'));
  app.innerHTML=`<div class="grid"><form class="panel" id="c"><h2>Create room</h2><label>Your team name<br><input name="team" required maxlength="24"></label>
   <p><label>Teams<br><select name="teams"><option>2</option><option>3</option><option>4</option></select></label></p>
   <p><label>Player pool<br><select name="pool"><option value="mixed">Mixed</option><option value="active">Active only</option><option value="retired">Retired legends only</option></select></label></p>
   <p><label>Purse (crore)<br><input name="purse" type="number" value="100" min="10"></label></p><p><label>Squad size<br><input name="squad" type="number" value="15" min="1"></label></p>
   <p><label>Seconds per lot<br><input name="countdown" type="number" value="15" min="5"></label></p><button class="primary">Create room</button></form>
   <form class="panel" id="j"><h2>Join room</h2><label>Room code<br><input name="code" required maxlength="5" style="text-transform:uppercase"></label>
   <p><label>Your team name<br><input name="team" required maxlength="24"></label></p><button class="primary">Join room</button></form></div>`;
  $('#c').onsubmit=async e=>{e.preventDefault();const f=Object.fromEntries(new FormData(e.target));
    try{me=await api('/api/rooms',{team:f.team,teams:+f.teams,pool:f.pool,purse:Math.round(+f.purse*100),squad:+f.squad,countdown:+f.countdown});localStorage.setItem('arena',JSON.stringify(me));connect()}catch(x){toast(x.message)}};
  $('#j').onsubmit=async e=>{e.preventDefault();const f=Object.fromEntries(new FormData(e.target));
    try{me=await api(`/api/rooms/${f.code.toUpperCase()}/join`,{team:f.team});localStorage.setItem('arena',JSON.stringify(me));connect()}catch(x){toast(x.message)}};
}
async function players(){ app.innerHTML=`<div class="row"><input id="q" placeholder="Search players" aria-label="Search players"><select id="r"><option value="">All roles</option><option>Batter</option><option>Bowler</option><option>All-rounder</option><option>Wicketkeeper</option></select></div><div id="t"></div>`;
  const load=async()=>{const p=await api(`/api/players?q=${encodeURIComponent($('#q').value)}&role=${$('#r').value}`);
   $('#t').innerHTML=p.length?`<table><tr><th>Name<th>Country<th>Role<th>Status<th>Base<th>Stats</tr>${p.map(x=>`<tr><td>${esc(x.name)}<td>${esc(x.country)}<td>${x.role}<td>${x.status}<td>${cr(x.base_lakh)}<td class="mute">${x.stats?'available':'unavailable'}</tr>`).join('')}</table>`:'<p class="mute">No players match. Clear the search or role filter.</p>'};
  $('#q').oninput=load;$('#r').onchange=load;load(); }
function auction(){
  if(!S) return app.innerHTML='<p class="mute">Create or join a room from Home first.</p>';
  const c=S.current, mine=S.teams[me.team];
  const teams=Object.entries(S.teams).map(([id,t])=>`<div class="panel"><b>${esc(t.name)}${id===me.team?' (you)':''}</b><div class="mute">${cr(t.purse)} left · ${t.squad.length}/${S.settings.squad} players</div><div class="meter"><i style="width:${t.purse/S.settings.purse*100}%"></i></div></div>`).join('');
  let lot = S.status==='finished'?'<h2>Auction finished</h2><p>Open Team report for the analysis.</p>':S.status==='lobby'?'<p>Waiting in lobby.</p>':
   c?`<h2>${esc(c.player.name)}</h2><div class="mute">${esc(c.player.country)} · ${c.player.role} · base ${cr(c.player.base_lakh)} · stats ${c.player.stats?'available':'unavailable'}</div>
     <div class="bid">${c.bidder?cr(c.bid):'No bids'}</div><div>${c.bidder?'Leading: '+esc(S.teams[c.bidder].name):'Opening bid '+cr(c.next_bid)}</div><div class="clock" aria-live="off">${Math.ceil(c.left)}s${S.status==='paused'?' (paused)':''}</div>
     <button class="primary big" id="bid" ${S.status!=='live'||c.bidder===me.team?'disabled':''}>Bid ${cr(c.next_bid)}</button>`:`<h2>Between lots</h2>${me.host&&!S.settings.auto?'<button class="primary" id="nx">Next player</button>':'<p class="mute">Next player is coming up.</p>'}`;
  app.innerHTML=`<div class="panel lot">${lot}</div>${me.host&&S.status!=='finished'?`<div class="row"><button id="pz">Pause</button><button id="rs">Resume</button>${S.status==='between'?'<button id="nx2">Next player</button>':''}</div>`:''}
   <div class="grid">${teams}</div><div class="panel log"><b>Activity</b>${S.log.slice().reverse().map(l=>`<div>${esc(l.msg)}</div>`).join('')}</div>`;
  const on=(i,f)=>$(i)&&($(i).onclick=f); on('#bid',()=>act('bid',c.next_bid)); on('#pz',()=>act('pause')); on('#rs',()=>act('resume')); on('#nx',()=>act('next')); on('#nx2',()=>act('next'));
}
async function report(){
  if(!me) return app.innerHTML='<p class="mute">Join a room to see the report.</p>';
  app.innerHTML=`<div class="row"><select id="f"><option>T20</option><option>ODI</option><option>Test</option></select></div><div id="rep"><p class="mute">Loading…</p></div>`;
  const load=async()=>{const d=await api(`/api/rooms/${me.code}/analysis?format=${$('#f').value}`);
   $('#rep').innerHTML=`<p class="mute">${esc(d.disclaimer)} Explanation source: ${d.explanation.source}.</p><div class="grid">`+Object.entries(d.results).map(([n,r])=>`<div class="panel"><h3>${esc(n)}: ${r.total}/100</h3><p class="mute">${esc(d.explanation.text[n])}</p>
     <p>Confidence: <b>${r.confidence}</b>. ${esc(r.data_note)}</p><table>${Object.entries(r.categories).map(([k,v])=>`<tr><td>${k} (${r.weights[k]}%)<td>${v.score}<td class="mute">${esc(v.why)}</tr>`).join('')}</table>
     <p><b>Suggested XI</b></p><ol>${r.playing_xi.map(p=>`<li>${esc(p.name)} <span class="mute">${p.role}</span></li>`).join('')}</ol>${r.missing.length?`<p>Gaps: ${r.missing.join(', ')}</p>`:''}</div>`).join('')+'</div>'};
  $('#f').onchange=load; load(); }
connect(); render();
