'use strict';
/* ═══════════════════════════════════════════════════════════════
   J.A.R.V.I.S. — app.js
   Energy Orb UI wired to FastAPI backend
═══════════════════════════════════════════════════════════════ */

const MODES = { BOOT:'BOOT', STANDBY:'STANDBY', LISTENING:'LISTENING', THINKING:'THINKING', SPEAKING:'SPEAKING' };

// ── State ────────────────────────────────────────────────────────────────
const state = {
  mode: MODES.BOOT,
  config: { autoListen: true, browserTts: false },
  chatWs: null,
  stateWs: null,
  isStreaming: false,
  pendingEntry: null,
  audioQueue: [],
  isPlayingAudio: false,
  pttRecorder: null,
  pttStream: null,
  pttChunks: [],
  autoListenAfterSpeak: false,
};

// ── DOM ──────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const orbCanvas    = $('orbCanvas');
const orbStatusEl  = $('orbStatus');
const transcriptIn = $('transcriptInner');
const connDot      = $('connectionDot');
const connLabel    = $('connectionLabel');
const textInput    = $('textInput');
const sendBtn      = $('sendBtn');
const micBtn       = $('micBtn');

// ══════════════════════════════════════════════════════════════════════════
// ORB RENDERER
// ══════════════════════════════════════════════════════════════════════════
class OrbRenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.dpr = window.devicePixelRatio || 1;
    this.colorMap = {
      [MODES.BOOT]:      { r:0,   g:180, b:255 },
      [MODES.STANDBY]:   { r:0,   g:180, b:255 },
      [MODES.LISTENING]: { r:255, g:119, b:0   },
      [MODES.THINKING]:  { r:180, g:100, b:255 },
      [MODES.SPEAKING]:  { r:0,   g:255, b:136 },
    };
    this.currentColor = { r:0, g:180, b:255 };
    this.targetColor  = { r:0, g:180, b:255 };
    this.rings = Array.from({length:9}, () => ({
      tiltX: Math.random()*Math.PI, tiltY: Math.random()*Math.PI,
      tiltZ: Math.random()*Math.PI, speed: 0.003+Math.random()*0.007,
      phase: Math.random()*Math.PI*2,
    }));
    this.filaments = Array.from({length:28}, (_,i) => ({
      angle: (i/28)*Math.PI*2, len: 0.2+Math.random()*0.6,
      speed: 0.5+Math.random()*2, phase: Math.random()*Math.PI*2,
      thickness: 0.5+Math.random()*0.8,
    }));
    this.particles = Array.from({length:60}, () => this._newParticle());
    this.amplitude = 0; this.targetAmplitude = 0; this.t = 0;
    this.resize();
    window.addEventListener('resize', () => this.resize());
    this._raf();
  }

  resize() {
    const size = Math.min(window.innerWidth, window.innerHeight) * 0.44;
    this.size = size;
    this.canvas.width  = size * this.dpr;
    this.canvas.height = size * this.dpr;
    this.canvas.style.width  = size + 'px';
    this.canvas.style.height = size + 'px';
    this.ctx.scale(this.dpr, this.dpr);
    this.cx = size/2; this.cy = size/2; this.r = size*0.36;
  }

  _newParticle() {
    const angle = Math.random()*Math.PI*2;
    const dist = this.r ? (this.r*(0.9+Math.random()*0.4)) : 80;
    return { x: Math.cos(angle)*dist, y: Math.sin(angle)*dist,
             vx: (Math.random()-0.5)*0.4, vy: (Math.random()-0.5)*0.4,
             life: Math.random(), maxLife: 0.6+Math.random()*1.8, size: 0.8+Math.random()*1.4 };
  }

  setMode(mode) {
    const c = this.colorMap[mode] || this.colorMap[MODES.STANDBY];
    this.targetColor = {...c};
    this.targetAmplitude = {
      [MODES.BOOT]:0.15, [MODES.STANDBY]:0.08, [MODES.LISTENING]:0.55,
      [MODES.THINKING]:0.35, [MODES.SPEAKING]:0.75,
    }[mode] ?? 0.1;
  }

  _lerpColor() {
    const k = 0.04;
    this.currentColor.r += (this.targetColor.r - this.currentColor.r)*k;
    this.currentColor.g += (this.targetColor.g - this.currentColor.g)*k;
    this.currentColor.b += (this.targetColor.b - this.currentColor.b)*k;
  }

  _rgb(a=1) {
    const {r,g,b} = this.currentColor;
    return `rgba(${r|0},${g|0},${b|0},${a})`;
  }

  _drawCore() {
    const {ctx,cx,cy,r,t} = this;
    const breathe = 1+Math.sin(t*1.8)*0.04+this.amplitude*0.12;
    const cr = r*breathe;
    const corona = ctx.createRadialGradient(cx,cy,cr*0.5,cx,cy,cr*1.6);
    corona.addColorStop(0, this._rgb(0.08+this.amplitude*0.1));
    corona.addColorStop(0.4, this._rgb(0.04));
    corona.addColorStop(1, this._rgb(0));
    ctx.beginPath(); ctx.arc(cx,cy,cr*1.6,0,Math.PI*2);
    ctx.fillStyle=corona; ctx.fill();
    const glow = ctx.createRadialGradient(cx,cy,0,cx,cy,cr);
    glow.addColorStop(0, this._rgb(0.55+this.amplitude*0.3));
    glow.addColorStop(0.35, this._rgb(0.18));
    glow.addColorStop(1, this._rgb(0.04));
    ctx.beginPath(); ctx.arc(cx,cy,cr,0,Math.PI*2);
    ctx.fillStyle=glow; ctx.fill();
    const core = ctx.createRadialGradient(cx,cy,0,cx,cy,cr*0.28);
    core.addColorStop(0, this._rgb(0.95));
    core.addColorStop(0.6, this._rgb(0.5));
    core.addColorStop(1, this._rgb(0));
    ctx.beginPath(); ctx.arc(cx,cy,cr*0.28,0,Math.PI*2);
    ctx.fillStyle=core; ctx.fill();
  }

  _drawRings() {
    const {ctx,cx,cy,r,t} = this;
    const scale = 1+this.amplitude*0.15;
    this.rings.forEach(ring => {
      ring.phase += ring.speed;
      const cosX=Math.cos(ring.tiltX+t*0.1), sinX=Math.sin(ring.tiltX+t*0.1);
      const cosZ=Math.cos(ring.tiltZ+ring.phase*0.5), sinZ=Math.sin(ring.tiltZ+ring.phase*0.5);
      ctx.beginPath();
      for (let i=0; i<=80; i++) {
        const theta=(i/80)*Math.PI*2;
        let px=Math.cos(theta), py=Math.sin(theta);
        const py2=py*cosX, pz=py*sinX;
        const px3=px*cosZ-py2*sinZ, py3=px*sinZ+py2*cosZ;
        const rx=cx+px3*r*scale, ry=cy+py3*r*scale*0.9;
        i===0?ctx.moveTo(rx,ry):ctx.lineTo(rx,ry);
      }
      ctx.strokeStyle=this._rgb(0.12+this.amplitude*0.18);
      ctx.lineWidth=0.8+this.amplitude*0.5; ctx.stroke();
    });
  }

  _drawFilaments() {
    const {ctx,cx,cy,r,t} = this; const amp=this.amplitude;
    this.filaments.forEach(f => {
      const base=r*(1.0+Math.sin(t*f.speed+f.phase)*0.05);
      const tip=base+r*(f.len*(0.15+amp*0.7))*(0.5+0.5*Math.sin(t*f.speed*0.7+f.phase));
      const bx=cx+Math.cos(f.angle)*base, by=cy+Math.sin(f.angle)*base;
      const tx2=cx+Math.cos(f.angle)*tip, ty2=cy+Math.sin(f.angle)*tip;
      const grad=ctx.createLinearGradient(bx,by,tx2,ty2);
      grad.addColorStop(0,this._rgb(0.5+amp*0.3)); grad.addColorStop(1,this._rgb(0));
      ctx.beginPath(); ctx.moveTo(bx,by); ctx.lineTo(tx2,ty2);
      ctx.strokeStyle=grad; ctx.lineWidth=f.thickness+amp*0.8; ctx.stroke();
    });
  }

  _drawParticles() {
    const {ctx,cx,cy} = this; const amp=this.amplitude;
    this.particles.forEach((p,i) => {
      p.life+=0.008+amp*0.015; p.x+=p.vx*(1+amp*2); p.y+=p.vy*(1+amp*2);
      if (p.life>=p.maxLife||Math.hypot(p.x,p.y)>this.r*2.2) { this.particles[i]=this._newParticle(); return; }
      const alpha=Math.sin((p.life/p.maxLife)*Math.PI)*(0.3+amp*0.4);
      ctx.beginPath(); ctx.arc(cx+p.x,cy+p.y,p.size*(1-p.life/p.maxLife*0.5),0,Math.PI*2);
      ctx.fillStyle=this._rgb(alpha); ctx.fill();
    });
  }

  _raf() {
    requestAnimationFrame(()=>{
      this.t+=0.016;
      this.amplitude+=(this.targetAmplitude-this.amplitude)*0.05;
      this.amplitude+=(Math.random()-0.5)*0.01*this.targetAmplitude;
      this.amplitude=Math.max(0,Math.min(1,this.amplitude));
      this._lerpColor();
      const {ctx,canvas}=this;
      ctx.clearRect(0,0,canvas.width,canvas.height);
      this._drawRings(); this._drawFilaments(); this._drawCore(); this._drawParticles();
      this._raf();
    });
  }
}

let orb;

// ══════════════════════════════════════════════════════════════════════════
// MODE MANAGEMENT
// ══════════════════════════════════════════════════════════════════════════
function setMode(mode) {
  state.mode = mode;
  if (orb) orb.setMode(mode);
  const labels = {
    [MODES.BOOT]:      'INITIALIZING...',
    [MODES.STANDBY]:   'SAY "HEY JARVIS" OR CLICK',
    [MODES.LISTENING]: 'LISTENING...',
    [MODES.THINKING]:  'PROCESSING...',
    [MODES.SPEAKING]:  'SPEAKING...',
  };
  orbStatusEl.textContent = labels[mode] || '';
  orbStatusEl.className = 'orb-status ' + ({
    [MODES.LISTENING]:'listening',
    [MODES.THINKING]: 'thinking',
    [MODES.SPEAKING]: 'speaking',
  }[mode] || '');
  // Update connection indicator
  if (mode === MODES.THINKING) { connDot.className='connection-dot thinking'; connLabel.textContent='THINKING'; }
  else if (mode === MODES.LISTENING) { connDot.className='connection-dot listening'; connLabel.textContent='LISTENING'; }
  else if (mode === MODES.SPEAKING)  { connDot.className='connection-dot online'; connLabel.textContent='SPEAKING'; }
  else if (mode === MODES.STANDBY)   { connDot.className='connection-dot online'; connLabel.textContent='ONLINE'; }
}

// ══════════════════════════════════════════════════════════════════════════
// WEBSOCKETS
// ══════════════════════════════════════════════════════════════════════════
function connectChatWS() {
  const proto = location.protocol==='https:'?'wss':'ws';
  state.chatWs = new WebSocket(`${proto}://${location.host}/api/chat/ws`);
  state.chatWs.onopen  = () => { connDot.className='connection-dot online'; connLabel.textContent='ONLINE'; };
  state.chatWs.onclose = () => { connDot.className='connection-dot'; connLabel.textContent='OFFLINE'; setTimeout(connectChatWS, 3000); };
  state.chatWs.onmessage = e => {
    const data = JSON.parse(e.data);
    if (data.error) { addEntry('assistant', data.error); setMode(MODES.STANDBY); return; }
    if (data.token) appendToken(data.token);
    if (data.done)  finalizeEntry();
  };
}

function connectStateWS() {
  const proto = location.protocol==='https:'?'wss':'ws';
  const ws = new WebSocket(`${proto}://${location.host}/api/state/ws`);
  ws.onmessage = e => {
    const data = JSON.parse(e.data);
    const modeMap = { standby:MODES.STANDBY, listening:MODES.LISTENING, thinking:MODES.THINKING, speaking:MODES.SPEAKING };
    if (data.state && modeMap[data.state]) setMode(modeMap[data.state]);
  };
  ws.onclose = () => setTimeout(connectStateWS, 3000);
  state.stateWs = ws;
}

// ══════════════════════════════════════════════════════════════════════════
// CHAT
// ══════════════════════════════════════════════════════════════════════════
function sendMessage(text) {
  text = text.trim();
  if (!text) return;
  addEntry('user', text);
  state.pendingEntry = addEntry('assistant', '');
  state.pendingEntry.classList.add('streaming');
  setMode(MODES.THINKING);
  if (state.chatWs && state.chatWs.readyState === WebSocket.OPEN) {
    state.chatWs.send(JSON.stringify({message: text}));
  } else {
    fetch('/api/chat/', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})})
      .then(r=>r.json()).then(d=>{ if(state.pendingEntry){ updateEntry(state.pendingEntry, d.response||d.error); finalizeEntry(); } });
  }
}

function appendToken(token) {
  if (!state.pendingEntry) state.pendingEntry = addEntry('assistant', '');
  const el = state.pendingEntry.querySelector('.t-text');
  el.textContent += token;
  transcriptIn.scrollTop = 9999;
}

function finalizeEntry() {
  if (state.pendingEntry) {
    state.pendingEntry.classList.remove('streaming');
    const text = state.pendingEntry.querySelector('.t-text').textContent;
    // Queue TTS
    queueTts(text);
    state.pendingEntry = null;
  }
  setMode(MODES.SPEAKING);
}

// ══════════════════════════════════════════════════════════════════════════
// TTS
// ══════════════════════════════════════════════════════════════════════════
function queueTts(text) {
  if (!text.trim()) return;
  // Split into sentences for lower latency
  const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
  sentences.forEach(s => state.audioQueue.push(s.trim()));
  if (!state.isPlayingAudio) processAudioQueue();
}

async function processAudioQueue() {
  if (state.audioQueue.length === 0) {
    state.isPlayingAudio = false;
    setMode(MODES.STANDBY);
    if (state.config.autoListen) setTimeout(startPTT, 600);
    return;
  }
  state.isPlayingAudio = true;
  setMode(MODES.SPEAKING);
  const text = state.audioQueue.shift();
  try {
    const res = await fetch('/api/voice/speak', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({text})
    });
    if (!res.ok) throw new Error('TTS failed');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.onended = () => { URL.revokeObjectURL(url); processAudioQueue(); };
    audio.onerror = () => { browserTts(text); processAudioQueue(); };
    await audio.play();
  } catch(e) {
    if (state.config.browserTts) browserTts(text);
    processAudioQueue();
  }
}

function browserTts(text) {
  if (!('speechSynthesis' in window)) return;
  const utt = new SpeechSynthesisUtterance(text);
  const voices = speechSynthesis.getVoices();
  const v = voices.find(v=>v.lang.startsWith('en-GB'))||voices.find(v=>v.lang.startsWith('en'));
  if (v) utt.voice = v;
  speechSynthesis.speak(utt);
}

// ══════════════════════════════════════════════════════════════════════════
// MICROPHONE — Push to Talk + Wake Word via server-side Whisper
// ══════════════════════════════════════════════════════════════════════════
async function startPTT() {
  if (state.mode === MODES.LISTENING) return;
  setMode(MODES.LISTENING);
  micBtn.classList.add('active');
  try {
    state.pttStream = await navigator.mediaDevices.getUserMedia({audio:true});
    state.pttChunks = [];
    state.pttRecorder = new MediaRecorder(state.pttStream, {mimeType:'audio/webm'});
    state.pttRecorder.ondataavailable = e => { if (e.data.size>0) state.pttChunks.push(e.data); };
    state.pttRecorder.onstop = handlePTTStop;
    state.pttRecorder.start();
    // Auto-stop after 10s
    setTimeout(stopPTT, 10000);
  } catch(e) {
    setMode(MODES.STANDBY); micBtn.classList.remove('active');
  }
}

function stopPTT() {
  if (state.pttRecorder && state.pttRecorder.state==='recording') {
    state.pttRecorder.stop();
  }
  if (state.pttStream) { state.pttStream.getTracks().forEach(t=>t.stop()); state.pttStream=null; }
  micBtn.classList.remove('active');
}

async function handlePTTStop() {
  if (state.pttChunks.length===0) { setMode(MODES.STANDBY); return; }
  setMode(MODES.THINKING);
  const blob = new Blob(state.pttChunks, {type:'audio/webm'});
  state.pttChunks = [];
  const formData = new FormData();
  formData.append('file', blob, 'audio.webm');
  try {
    const res = await fetch('/api/voice/transcribe', {method:'POST', body:formData});
    const data = await res.json();
    if (data.text && data.text.trim()) {
      sendMessage(data.text);
    } else {
      setMode(MODES.STANDBY);
    }
  } catch(e) {
    setMode(MODES.STANDBY);
  }
}

// ══════════════════════════════════════════════════════════════════════════
// TRANSCRIPT
// ══════════════════════════════════════════════════════════════════════════
function addEntry(role, text) {
  const el = document.createElement('div');
  el.className = `t-entry ${role}`;
  const label = role==='user'?'YOU':'JARVIS';
  el.innerHTML = `<div class="t-role">${label}</div><div class="t-text">${esc(text)}</div>`;
  transcriptIn.appendChild(el);
  transcriptIn.scrollTop = 9999;
  while (transcriptIn.children.length > 40) transcriptIn.firstChild.remove();
  return el;
}

function updateEntry(el, text) {
  if (!el) return;
  el.querySelector('.t-text').textContent = text;
  transcriptIn.scrollTop = 9999;
}

function esc(t) { return (t||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

// ══════════════════════════════════════════════════════════════════════════
// DASHBOARD
// ══════════════════════════════════════════════════════════════════════════
async function openDashboard() {
  $('dashboardOverlay').classList.add('active');
  loadDashData();
}

async function loadDashData() {
  // Tasks
  try {
    const tasks = await fetch('/api/tasks/').then(r=>r.json());
    const active = tasks.filter(t=>t.status==='active'||t.status==='pending');
    $('dashTasksBody').innerHTML = active.length
      ? active.map(t=>`<div class="dash-stat"><span class="dash-stat-label">${esc(t.title.slice(0,30))}</span><span class="dash-stat-val">${t.status}</span></div>`).join('')
      : '<div style="color:rgba(0,180,255,0.3)">No active tasks</div>';
  } catch(e) { $('dashTasksBody').innerHTML = '<div style="color:#ff4466">Error</div>'; }

  // Agents
  try {
    const status = await fetch('/api/agents/status').then(r=>r.json());
    $('dashAgentsBody').innerHTML = `
      <div class="dash-stat"><span class="dash-stat-label">Running</span><span class="dash-stat-val">${status.running||0}/${status.max_parallel||5}</span></div>
      <div class="dash-stat"><span class="dash-stat-label">Total</span><span class="dash-stat-val">${status.total||0}/${status.max_agents||20}</span></div>
      <div class="dash-stat"><span class="dash-stat-label">Done</span><span class="dash-stat-val">${status.done||0}</span></div>`;
  } catch(e) { $('dashAgentsBody').innerHTML = '<div style="color:#ff4466">Error</div>'; }

  // System
  try {
    const stats = await fetch('/api/system/stats').then(r=>r.json());
    $('dashSystemBody').innerHTML = [
      ['CPU',  `${stats.cpu_percent?.toFixed(1)||'?'}%`],
      ['RAM',  `${stats.ram_percent?.toFixed(1)||'?'}% (${stats.ram_used_gb||'?'}GB)`],
      ['VRAM', stats.vram_percent ? `${stats.vram_percent.toFixed(1)}%` : 'N/A'],
      ['JARVIS RAM', `${stats.jarvis_ram_mb||'?'} MB`],
    ].map(([l,v])=>`<div class="dash-stat"><span class="dash-stat-label">${l}</span><span class="dash-stat-val">${v}</span></div>`).join('');
  } catch(e) { $('dashSystemBody').innerHTML = '<div style="color:#ff4466">Error</div>'; }

  // Memory
  try {
    const mem = await fetch('/api/memory/today').then(r=>r.json());
    const lines = (mem.content||'').split('\n').filter(l=>l.trim()).slice(-8);
    $('dashMemoryBody').innerHTML = lines.length
      ? `<pre style="font-size:0.72rem;white-space:pre-wrap;color:rgba(255,255,255,0.6)">${esc(lines.join('\n'))}</pre>`
      : '<div style="color:rgba(0,180,255,0.3)">No entries today</div>';
  } catch(e) { $('dashMemoryBody').innerHTML = '<div style="color:#ff4466">Error</div>'; }
}

// ══════════════════════════════════════════════════════════════════════════
// SETTINGS
// ══════════════════════════════════════════════════════════════════════════
async function openSettings() {
  try {
    const cfg = await fetch('/api/settings/').then(r=>r.json());
    $('cfgVoice').value    = cfg.voice?.tts_voice || 'en-GB-RyanNeural';
    $('cfgWhisper').value  = cfg.voice?.stt_model || 'base.en';
    $('cfgWakeWord').value = cfg.voice?.wake_word || 'hey jarvis';
    $('cfgAutoListen').checked  = state.config.autoListen !== false;
    $('cfgBrowserTts').checked  = state.config.browserTts || false;
  } catch(e) {}
  $('settingsModal').classList.add('active');
}

async function saveSettings() {
  const updates = [
    {key:'voice.tts_voice',  value: $('cfgVoice').value},
    {key:'voice.stt_model',  value: $('cfgWhisper').value},
    {key:'voice.wake_word',  value: $('cfgWakeWord').value},
  ];
  await fetch('/api/settings/', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({updates})});
  state.config.autoListen = $('cfgAutoListen').checked;
  state.config.browserTts = $('cfgBrowserTts').checked;
  $('settingsModal').classList.remove('active');
}

// ══════════════════════════════════════════════════════════════════════════
// BOOT
// ══════════════════════════════════════════════════════════════════════════
function boot() {
  const steps = [
    {pct:20, msg:'LOADING NEURAL CORES...'},
    {pct:45, msg:'STARTING STT ENGINE...'},
    {pct:65, msg:'LOADING VOICE SYNTHESIS...'},
    {pct:85, msg:'CONNECTING TO OLLAMA...'},
    {pct:100, msg:'ALL SYSTEMS ONLINE'},
  ];
  let progress=0, stepIdx=0;
  const ticker = setInterval(() => {
    if (progress < (steps[stepIdx]?.pct ?? 100)) progress = Math.min(progress+1, steps[stepIdx]?.pct ?? 100);
    $('bootProgress').style.width = progress+'%';
    if (stepIdx < steps.length && progress >= steps[stepIdx].pct) {
      $('bootStatus').textContent = steps[stepIdx].msg;
      stepIdx++;
    }
    if (progress >= 100) {
      clearInterval(ticker);
      setTimeout(() => {
        $('bootOverlay').classList.remove('visible');
        setMode(MODES.STANDBY);
        connectChatWS();
        connectStateWS();
      }, 600);
    }
  }, 25);
}

// ══════════════════════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  orb = new OrbRenderer(orbCanvas);
  orb.setMode(MODES.BOOT);

  // Orb click → PTT toggle
  orbCanvas.addEventListener('click', () => {
    if (state.mode===MODES.STANDBY)   { startPTT(); }
    else if (state.mode===MODES.LISTENING) { stopPTT(); }
    else if (state.mode===MODES.SPEAKING)  {
      state.audioQueue=[];
      if (window.speechSynthesis) speechSynthesis.cancel();
      state.isPlayingAudio=false;
      setMode(MODES.STANDBY);
    }
  });

  // Text input
  sendBtn.addEventListener('click', () => { sendMessage(textInput.value); textInput.value=''; });
  textInput.addEventListener('keydown', e => {
    if (e.key==='Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(textInput.value); textInput.value=''; }
  });

  // Mic PTT button
  micBtn.addEventListener('mousedown', startPTT);
  micBtn.addEventListener('mouseup',   stopPTT);
  micBtn.addEventListener('touchstart', e => { e.preventDefault(); startPTT(); });
  micBtn.addEventListener('touchend',   stopPTT);

  // Nav buttons
  $('dashboardBtn').addEventListener('click', openDashboard);
  $('closeDashboard').addEventListener('click', () => $('dashboardOverlay').classList.remove('active'));
  $('dashboardOverlay').addEventListener('click', e => { if(e.target===$('dashboardOverlay')) $('dashboardOverlay').classList.remove('active'); });
  $('settingsBtn').addEventListener('click', openSettings);
  $('closeSettings').addEventListener('click', () => $('settingsModal').classList.remove('active'));
  $('saveSettings').addEventListener('click', saveSettings);
  $('settingsModal').addEventListener('click', e => { if(e.target===$('settingsModal')) $('settingsModal').classList.remove('active'); });

  // Fullscreen
  $('fullscreenBtn').addEventListener('click', () => {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen();
    else document.exitFullscreen();
  });

  boot();
});
