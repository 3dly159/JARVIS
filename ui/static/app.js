/* J.A.R.V.I.S. — Frontend App */

const API = '';
let ws = null;
let currentPanel = 'chat';
let settings = {};

// ── Init ──────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initChat();
  checkStatus();
  loadPanel('chat');
  setInterval(checkStatus, 10000);
});

// ── Navigation ────────────────────────────────────────────────────────────

function initNav() {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      loadPanel(btn.dataset.panel);
    });
  });
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const group = btn.closest('section');
      group.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      group.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      group.querySelector(`#memory-${btn.dataset.tab}`).classList.add('active');
      if (btn.dataset.tab === 'daily') loadDailyLog();
      if (btn.dataset.tab === 'palace') loadPalace();
    });
  });
}

function loadPanel(name) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById(`panel-${name}`)?.classList.add('active');
  currentPanel = name;
  if (name === 'tasks')    loadTasks();
  if (name === 'agents')   loadAgents();
  if (name === 'memory')   loadDailyLog();
  if (name === 'system')   loadSystem();
  if (name === 'settings') loadSettings();
}

// ── Status ────────────────────────────────────────────────────────────────

async function checkStatus() {
  try {
    const r = await fetch(`${API}/health`);
    const data = await r.json();
    setStatus(data.status === 'online' ? 'online' : 'offline', data.status);
  } catch {
    setStatus('offline', 'Offline');
  }
}

function setStatus(state, text) {
  const dot = document.getElementById('status-dot');
  const txt = document.getElementById('status-text');
  dot.className = `dot ${state}`;
  txt.textContent = text;
}

// ── Chat ──────────────────────────────────────────────────────────────────

function initChat() {
  const input = document.getElementById('chat-input');
  const btn = document.getElementById('send-btn');

  btn.addEventListener('click', sendMessage);
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  connectWS();
}

function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/api/chat/ws`);
  ws.onopen  = () => setStatus('online', 'Online');
  ws.onclose = () => { setStatus('offline', 'Reconnecting...'); setTimeout(connectWS, 3000); };
  ws.onerror = () => setStatus('offline', 'Error');

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.error) {
      appendToken(data.error, true);
      finalizeJarvisMsg();
      return;
    }
    if (data.token) appendToken(data.token, false);
    if (data.done)  finalizeJarvisMsg();
  };
}

let currentJarvisMsg = null;

function sendMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;

  addMessage('user', text);
  input.value = '';

  // Start streaming JARVIS response
  currentJarvisMsg = addMessage('jarvis', '');
  currentJarvisMsg.querySelector('.msg-bubble').classList.add('streaming');

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ message: text }));
  } else {
    // Fallback to REST
    fetch(`${API}/api/chat/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    })
    .then(r => r.json())
    .then(data => {
      if (currentJarvisMsg) {
        currentJarvisMsg.querySelector('.msg-bubble').textContent = data.response || data.error;
        finalizeJarvisMsg();
      }
    });
  }
}

function addMessage(role, text) {
  const container = document.getElementById('chat-messages');
  const msg = document.createElement('div');
  msg.className = `msg ${role}`;
  msg.innerHTML = `<div class="msg-label">${role === 'user' ? 'You' : 'JARVIS'}</div>
                   <div class="msg-bubble">${escHtml(text)}</div>`;
  container.appendChild(msg);
  container.scrollTop = container.scrollHeight;
  return msg;
}

function appendToken(token, isError) {
  if (!currentJarvisMsg) currentJarvisMsg = addMessage('jarvis', '');
  const bubble = currentJarvisMsg.querySelector('.msg-bubble');
  bubble.textContent += token;
  document.getElementById('chat-messages').scrollTop = 9999;
}

function finalizeJarvisMsg() {
  if (currentJarvisMsg) {
    currentJarvisMsg.querySelector('.msg-bubble').classList.remove('streaming');
    currentJarvisMsg = null;
  }
}

// ── Tasks ─────────────────────────────────────────────────────────────────

async function loadTasks() {
  const list = document.getElementById('tasks-list');
  list.innerHTML = '<div style="color:var(--text-dim)">Loading...</div>';
  try {
    const tasks = await fetch(`${API}/api/tasks/`).then(r => r.json());
    list.innerHTML = tasks.length ? '' : '<div style="color:var(--text-dim)">No tasks.</div>';
    tasks.forEach(t => {
      const pct = t.steps?.length ? Math.round(t.completed_steps?.length / t.steps.length * 100) : (t.status === 'done' ? 100 : 0);
      list.innerHTML += `
        <div class="task-card">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div class="task-title">${escHtml(t.title)}</div>
            <span class="badge badge-${t.status}">${t.status}</span>
          </div>
          <div class="task-meta">
            <span>Priority: ${t.priority}</span>
            <span>${t.completed_steps?.length || 0}/${t.steps?.length || 0} steps</span>
            ${t.deadline ? `<span>Due: ${new Date(t.deadline).toLocaleDateString()}</span>` : ''}
          </div>
          ${t.description ? `<div style="font-size:12px;color:var(--text-dim);margin-top:6px">${escHtml(t.description)}</div>` : ''}
          <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div>
        </div>`;
    });
  } catch (e) {
    list.innerHTML = `<div style="color:var(--danger)">Error: ${e.message}</div>`;
  }
}

async function createTask() {
  const title = prompt('Task title:');
  if (!title) return;
  await fetch(`${API}/api/tasks/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, priority: 5 })
  });
  loadTasks();
}

// ── Agents ────────────────────────────────────────────────────────────────

async function loadAgents() {
  try {
    const [agents, status] = await Promise.all([
      fetch(`${API}/api/agents/`).then(r => r.json()),
      fetch(`${API}/api/agents/status`).then(r => r.json()),
    ]);

    document.getElementById('agents-stats').innerHTML =
      `<span>${status.running || 0}/${status.max_parallel || 5} running</span>
       <span>${status.total || 0}/${status.max_agents || 20} total</span>`;

    const list = document.getElementById('agents-list');
    list.innerHTML = agents.length ? '' : '<div style="color:var(--text-dim);padding:20px">No agents active.</div>';
    agents.forEach(a => {
      list.innerHTML += `
        <div class="agent-card">
          <div class="agent-info">
            <div class="agent-name">${escHtml(a.name)} <span class="badge badge-${a.status}">${a.status}</span></div>
            <div class="agent-task">${escHtml(a.task || '—')}</div>
          </div>
          <button class="btn-danger" onclick="killAgent('${a.id}')">Kill</button>
        </div>`;
    });
  } catch (e) {
    document.getElementById('agents-list').innerHTML = `<div style="color:var(--danger);padding:20px">Error loading agents.</div>`;
  }
}

async function killAgent(id) {
  await fetch(`${API}/api/agents/${id}`, { method: 'DELETE' });
  loadAgents();
}

// ── Memory ────────────────────────────────────────────────────────────────

async function loadDailyLog() {
  try {
    const data = await fetch(`${API}/api/memory/today`).then(r => r.json());
    document.getElementById('daily-log-content').textContent = data.content || '(empty)';
  } catch {
    document.getElementById('daily-log-content').textContent = 'Error loading log.';
  }
}

async function loadPalace() {
  try {
    const items = await fetch(`${API}/api/memory/palace`).then(r => r.json());
    renderPalaceItems(items);
  } catch { }
}

async function searchPalace() {
  const q = document.getElementById('palace-query').value.trim();
  if (!q) return loadPalace();
  try {
    const items = await fetch(`${API}/api/memory/palace/search?q=${encodeURIComponent(q)}`).then(r => r.json());
    renderPalaceItems(items);
  } catch { }
}

function renderPalaceItems(items) {
  const div = document.getElementById('palace-items');
  div.innerHTML = items.length ? '' : '<div style="color:var(--text-dim)">No items.</div>';
  items.forEach(item => {
    div.innerHTML += `
      <div class="palace-item">
        <div class="palace-item-title">${escHtml(item.title)}</div>
        <div style="font-size:12px;color:var(--text-dim);margin:4px 0">${escHtml((item.content||'').slice(0,120))}${item.content?.length > 120 ? '...' : ''}</div>
        <div class="palace-item-tags">${(item.tags||[]).map(t => `#${t}`).join(' ')}</div>
      </div>`;
  });
}

// ── System ────────────────────────────────────────────────────────────────

async function loadSystem() {
  try {
    const stats = await fetch(`${API}/api/system/stats`).then(r => r.json());
    const div = document.getElementById('system-stats');
    div.innerHTML = '';

    const cards = [
      ['CPU', stats.cpu_percent, '%'],
      ['RAM', stats.ram_percent, `% (${stats.ram_used_gb}/${stats.ram_total_gb}GB)`],
      ['VRAM', stats.vram_percent, `% (${stats.vram_used_gb}/${stats.vram_total_gb}GB)`],
      ['Disk', stats.disk_percent, `% (${stats.disk_used_gb}/${stats.disk_total_gb}GB)`],
      ['JARVIS CPU', stats.jarvis_cpu, '%'],
      ['JARVIS RAM', stats.jarvis_ram_mb, 'MB'],
    ];

    cards.forEach(([label, val, unit]) => {
      if (val === undefined) return;
      div.innerHTML += `
        <div class="stat-card">
          <div class="stat-label">${label}</div>
          <div><span class="stat-value">${typeof val === 'number' ? val.toFixed(1) : val}</span><span class="stat-unit"> ${unit}</span></div>
        </div>`;
    });

    const notifs = await fetch(`${API}/api/system/notifications`).then(r => r.json());
    const nl = document.getElementById('notif-list');
    nl.innerHTML = notifs.slice(-10).reverse().map(n =>
      `<div style="padding:8px 24px;border-bottom:1px solid var(--border);font-size:13px">
        <span style="color:var(--text-dim);font-size:11px">${new Date(n.time).toLocaleTimeString()}</span>
        <span class="badge badge-${n.priority === 'urgent' ? 'stalled' : n.priority === 'warning' ? 'pending' : 'active'}" style="margin:0 8px">${n.priority}</span>
        ${escHtml(n.message)}
      </div>`
    ).join('') || '<div style="padding:16px 24px;color:var(--text-dim)">No notifications.</div>';
  } catch (e) {
    document.getElementById('system-stats').innerHTML = `<div style="padding:20px;color:var(--danger)">Error loading stats.</div>`;
  }
}

// ── Settings ──────────────────────────────────────────────────────────────

async function loadSettings() {
  try {
    settings = await fetch(`${API}/api/settings/`).then(r => r.json());
    const form = document.getElementById('settings-form');
    form.innerHTML = '';

    const sections = {
      'LLM': [
        { key: 'llm.model',       label: 'Model',       desc: 'Ollama model name' },
        { key: 'llm.ollama_host', label: 'Ollama Host',  desc: 'Ollama API endpoint' },
        { key: 'llm.temperature', label: 'Temperature',  desc: '0.0 (precise) – 1.0 (creative)', type: 'number', step: 0.1 },
      ],
      'Voice': [
        { key: 'voice.tts_voice',  label: 'TTS Voice',   desc: 'Edge TTS voice name' },
        { key: 'voice.stt_model',  label: 'Whisper Model', desc: 'tiny.en / base.en / small.en' },
        { key: 'voice.wake_word',  label: 'Wake Word',   desc: 'Phrase to activate JARVIS' },
        { key: 'voice.hotkey',     label: 'Hotkey',      desc: 'Keyboard shortcut (e.g. ctrl+space)' },
      ],
      'Notifications': [
        { key: 'notifications.quiet_hours_start', label: 'Quiet Start', desc: 'HH:MM' },
        { key: 'notifications.quiet_hours_end',   label: 'Quiet End',   desc: 'HH:MM' },
      ],
      'Agents': [
        { key: 'agents.max_agents',   label: 'Max Agents',   type: 'number' },
        { key: 'agents.max_parallel', label: 'Max Parallel', type: 'number' },
      ],
    };

    Object.entries(sections).forEach(([sectionName, fields]) => {
      let html = `<div class="settings-section"><h3>${sectionName}</h3>`;
      fields.forEach(f => {
        const val = getNestedVal(settings, f.key) ?? '';
        const type = f.type || 'text';
        html += `
          <div class="setting-row">
            <div><div class="setting-label">${f.label}</div>${f.desc ? `<div class="setting-desc">${f.desc}</div>` : ''}</div>
            <input type="${type}" ${f.step ? `step="${f.step}"` : ''} data-key="${f.key}" value="${escHtml(String(val))}">
          </div>`;
      });
      html += '</div>';
      form.innerHTML += html;
    });
  } catch (e) {
    document.getElementById('settings-form').innerHTML = `<div style="color:var(--danger)">Error loading settings.</div>`;
  }
}

async function saveSettings() {
  const inputs = document.querySelectorAll('#settings-form input[data-key]');
  const updates = [];
  inputs.forEach(input => {
    const key = input.dataset.key;
    let value = input.value;
    if (input.type === 'number') value = parseFloat(value);
    updates.push({ key, value });
  });

  try {
    await fetch(`${API}/api/settings/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ updates })
    });
    alert('Settings saved. Changes applied live.');
  } catch (e) {
    alert('Error saving settings: ' + e.message);
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────

function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function getNestedVal(obj, dotPath) {
  return dotPath.split('.').reduce((o, k) => o?.[k], obj);
}

// Auto-refresh active panel every 30s
setInterval(() => {
  if (currentPanel === 'tasks')  loadTasks();
  if (currentPanel === 'agents') loadAgents();
  if (currentPanel === 'system') loadSystem();
}, 30000);
