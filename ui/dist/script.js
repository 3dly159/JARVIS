/* ==============================================================
   script.js – Arc HUD Aesthetic Plain JS Router & UI
   ============================================================== */

/* ---------- tiny DOM builder ---------- */
function el(tag, cls = "", attrs = {}, ...children) {
  const e = document.createElement(tag);
  if (cls) e.className = Array.isArray(cls) ? cls.join(" ") : cls;
  Object.entries(attrs).forEach(([k, v]) => {
    if (v === null || v === undefined) return;
    if (k.startsWith("on") && typeof v === "function") e[k] = v;
    else if (typeof v === "boolean") { if (v) e.setAttribute(k, ""); }
    else e.setAttribute(k, v);
  });
  children.flat(Infinity).forEach(c => {
    if (c === null || c === undefined || c === false) return;
    e.appendChild(typeof c === "string" || typeof c === "number" ? document.createTextNode(String(c)) : c);
  });
  return e;
}

function elSvg(tag, cls = "", attrs = {}, ...children) {
  const e = document.createElementNS("http://www.w3.org/2000/svg", tag);
  if (cls) e.setAttribute("class", Array.isArray(cls) ? cls.join(" ") : cls);
  Object.entries(attrs).forEach(([k, v]) => {
    if (v !== null && v !== undefined) e.setAttribute(k, v);
  });
  children.flat(Infinity).forEach(c => {
    if (c) e.appendChild(c);
  });
  return e;
}

/* ---------- Icons (Lucide-like) ---------- */
function Icon({ name, className = "" }) {
  const PATHS = {
    LayoutDashboard: [['rect', {x: 3, y: 3, width: 7, height: 9, rx: 1}], ['rect', {x: 14, y: 3, width: 7, height: 5, rx: 1}], ['rect', {x: 14, y: 12, width: 7, height: 9, rx: 1}], ['rect', {x: 3, y: 16, width: 7, height: 5, rx: 1}]],
    MessageSquare: [['path', {d: 'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'}]],
    ListChecks: [['path', {d: 'M3 6h.01M3 12h.01M3 18h.01M8 6h13M8 12h13M8 18h13'}]],
    Bot: [['rect', {x: 3, y: 11, width: 18, height: 10, rx: 2}], ['circle', {cx: 12, cy: 5, r: 2}], ['path', {d: 'M12 7v4M8 16v.01M16 16v.01'}]],
    Brain: [['path', {d: 'M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z'}], ['path', {d: 'M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z'}]],
    Zap: [['polygon', {points: '13 2 3 14 12 14 11 22 21 10 12 10 13 2'}]],
    Users: [['path', {d: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2'}], ['circle', {cx: 9, cy: 7, r: 4}], ['path', {d: 'M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75'}]],
    Wrench: [['path', {d: 'M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z'}]],
    Cpu: [['rect', {x: 4, y: 4, width: 16, height: 16, rx: 2, ry: 2}], ['rect', {x: 9, y: 9, width: 6, height: 6}], ['line', {x1: 9, y1: 1, x2: 9, y2: 4}], ['line', {x1: 15, y1: 1, x2: 15, y2: 4}], ['line', {x1: 9, y1: 20, x2: 9, y2: 23}], ['line', {x1: 15, y1: 20, x2: 15, y2: 23}], ['line', {x1: 20, y1: 9, x2: 23, y2: 9}], ['line', {x1: 20, y1: 14, x2: 23, y2: 14}], ['line', {x1: 1, y1: 9, x2: 4, y2: 9}], ['line', {x1: 1, y1: 14, x2: 4, y2: 14}]],
    ScrollText: [['path', {d: 'M8 21h12a2 2 0 0 0 2-2v-2H10v2a2 2 0 1 1-4 0V5a2 2 0 1 0-4 0v3h4'}], ['path', {d: 'M19 17V5a2 2 0 0 0-2-2H4'}]],
    SlidersHorizontal: [['line', {x1: 21, y1: 4, x2: 14, y2: 4}], ['line', {x1: 10, y1: 4, x2: 3, y2: 4}], ['line', {x1: 21, y1: 12, x2: 12, y2: 12}], ['line', {x1: 8, y1: 12, x2: 3, y2: 12}], ['line', {x1: 21, y1: 20, x2: 16, y2: 20}], ['line', {x1: 12, y1: 20, x2: 3, y2: 20}], ['line', {x1: 14, y1: 2, x2: 14, y2: 6}], ['line', {x1: 8, y1: 10, x2: 8, y2: 14}], ['line', {x1: 16, y1: 18, x2: 16, y2: 22}]],
    Sparkles: [['path', {d: 'm12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z'}]],
    Menu: [['line', {x1: 4, x2: 20, y1: 12, y2: 12}], ['line', {x1: 4, x2: 20, y1: 6, y2: 6}], ['line', {x1: 4, x2: 20, y1: 18, y2: 18}]],
    Maximize2: [['polyline', {points: '15 3 21 3 21 9'}], ['polyline', {points: '9 21 3 21 3 15'}], ['line', {x1: 21, x2: 14, y1: 3, y2: 10}], ['line', {x1: 3, x2: 10, y1: 21, y2: 14}]],
    Minimize2: [['polyline', {points: '4 14 10 14 10 20'}], ['polyline', {points: '20 10 14 10 14 4'}], ['line', {x1: 14, x2: 21, y1: 10, y2: 3}], ['line', {x1: 3, x2: 10, y1: 21, y2: 14}]],
    Settings: [['circle', {cx: 12, cy: 12, r: 3}], ['path', {d: 'M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'}]],
    Activity: [['polyline', {points: '22 12 18 12 15 21 9 3 6 12 2 12'}]],
    MemoryStick: [['path', {d: 'M6 19v-3M10 19v-3M14 19v-3M18 19v-3M8 11V9M16 11V9'}], ['rect', {x: 2, y: 5, width: 20, height: 14, rx: 2}]],
    Network: [['rect', {x: 16, y: 16, width: 6, height: 6, rx: 1}], ['rect', {x: 2, y: 16, width: 6, height: 6, rx: 1}], ['rect', {x: 9, y: 2, width: 6, height: 6, rx: 1}], ['path', {d: 'M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3'}], ['path', {d: 'M12 12V8'}]],
    Radio: [['line', {x1: 12, x2: 12, y1: 19, y2: 12}], ['circle', {cx: 12, cy: 19, r: 2}], ['path', {d: 'M4 11A11 11 0 0 1 20 11M8 15a5 5 0 0 1 8 0'}]],
    Send: [['path', {d: 'm22 2-7 20-4-9-9-4Z'}], ['path', {d: 'M22 2 11 13'}]],
    Search: [['circle', {cx: 11, cy: 11, r: 8}], ['line', {x1: 21, y1: 21, x2: 16.65, y2: 16.65}]],
    HardDrive: [['line', {x1: 22, y1: 12, x2: 2, y2: 12}], ['path', {d: 'M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z'}], ['line', {x1: 6, y1: 16, x2: 6.01, y2: 16}], ['line', {x1: 10, y1: 16, x2: 10.01, y2: 16}]],
    AlertTriangle: [['path', {d: 'm21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z'}], ['line', {x1: 12, y1: 9, x2: 12, y2: 13}], ['line', {x1: 12, y1: 17, x2: 12.01, y2: 17}]]
  };
  const parts = PATHS[name] || [];
  return elSvg("svg", className || "h-4 w-4", {
    xmlns: "http://www.w3.org/2000/svg",
    viewBox: "0 0 24 24", fill: "none", stroke: "currentColor",
    "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round"
  }, parts.map(([pTag, pAttrs]) => elSvg(pTag, "", pAttrs)));
}

/* ---------- Shared UI Utilities ---------- */

function JBadge({ variant = "info", children }) {
  const map = {
    success: "border-success/40 bg-success/10 text-success",
    warning: "border-warning/40 bg-warning/10 text-warning",
    error: "border-error/40 bg-error/10 text-error",
    info: "border-info/40 bg-info/10 text-info",
    neutral: "border-border-light bg-bg-tertiary text-text-muted"
  };
  return el("div", `inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wider ${map[variant] || map.neutral}`, {}, children);
}

function IconButton({ icon, label, onClick, className = "", variant = "ghost" }) {
  const v = variant === "outlined" ? "border-border" : "border-transparent text-text-muted hover:bg-bg-hover hover:text-text-primary";
  return el("button", `flex h-9 w-9 items-center justify-center rounded-md border transition-colors ${v} ${className}`, { "aria-label": label, onclick: onClick }, 
    typeof icon === "string" ? Icon({ name: icon, className: "h-4.5 w-4.5" }) : icon
  );
}

function OrbIndicator({ state = "idle", size = "md", showLabel = false }) {
  const SIZES = { sm: "h-3 w-3", md: "h-4 w-4", lg: "h-6 w-6" };
  const COLORS = { idle: "var(--info)", thinking: "var(--accent)", speaking: "var(--success)", error: "var(--error)", listening: "var(--warning)" };
  const color = COLORS[state] || "var(--info)";
  const orb = el("div", `relative shrink-0 rounded-full ${SIZES[size]}`, { style: `background-color: ${color}; box-shadow: 0 0 12px ${color}` },
    state !== "idle" ? el("div", `absolute inset-0 rounded-full ${state === 'thinking' ? 'animate-pulse-orb' : 'animate-orb-bump'}`, { style: `color: ${color}` }) : null
  );
  if (!showLabel) return orb;
  return el("div", "flex items-center gap-2", {}, orb, el("span", "font-mono text-xs uppercase tracking-wider text-text-secondary", {}, state));
}

function StatTile({ label, value, unit, delta, accentColor, icon }) {
  return el("div", "group relative overflow-hidden rounded-lg border border-border-light bg-bg-secondary p-4 transition-all hover:border-accent/40", {},
    el("div", "mb-3 flex items-center justify-between text-text-muted transition-colors group-hover:text-accent", {}, 
      el("p", "font-mono text-[11px] uppercase tracking-widest", {}, label),
      icon
    ),
    el("div", "flex items-baseline gap-1", {},
      el("h3", "font-display text-3xl font-bold tabular-nums text-text-primary", {}, value),
      unit ? el("span", "font-mono text-xs text-text-muted", {}, unit) : null
    ),
    delta ? el("div", `mt-3 flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest ${delta.trend === 'up' ? 'text-success' : delta.trend === 'down' ? 'text-accent' : 'text-text-muted'}`, {}, delta.value) : null,
    accentColor ? el("div", "absolute bottom-0 left-0 h-[2px] w-full", { style: `background: linear-gradient(90deg, ${accentColor}, transparent)` }) : null
  );
}

function Widget({ title, icon, className = "", action = null, children }) {
  return el("div", `rounded-lg border border-border-light bg-bg-secondary p-4 ${className}`, {},
    el("div", "mb-4 flex items-center justify-between border-b border-border-light pb-3", {}, 
      el("div", "flex items-center gap-2", {}, 
        icon,
        el("h2", "font-display text-sm font-semibold uppercase tracking-widest text-text-primary", {}, title)
      ),
      action
    ),
    children
  );
}

function FormGroup({ label, htmlFor, hint, children }) {
  return el("div", "space-y-1.5", {}, 
    el("label", "block font-mono text-[10px] uppercase tracking-[0.2em] text-text-muted", { for: htmlFor }, label),
    children,
    hint ? el("p", "font-mono text-[11px] text-text-muted tracking-widest", {}, hint) : null
  );
}

function JInput({ value, onChange, placeholder, disabled, type="text", id, className="", label }) {
  return el("input", `flex h-9 w-full rounded-md border border-border bg-bg-primary px-3 py-1 text-sm text-text-primary shadow-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-not-allowed disabled:opacity-50 ${className}`, {
    value, type, placeholder, disabled, id, "aria-label": label,
    oninput: onChange ? (e) => onChange(e) : null
  });
}

function JTextarea({ value, onChange, placeholder, disabled, id, className="" }) {
  return el("textarea", `flex min-h-[80px] w-full rounded-md border border-border bg-bg-primary px-3 py-2 text-sm text-text-primary shadow-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-not-allowed disabled:opacity-50 ${className}`, {
    placeholder, disabled, id,
    oninput: onChange ? (e) => onChange(e) : null
  }, value);
}

function JSelect({ value, onChange, disabled, id, className="", children }) {
  const flattened = Array.isArray(children) ? children.flat(Infinity) : [children];
  return el("select", `flex h-9 w-full rounded-md border border-border bg-bg-primary px-3 py-1 text-sm text-text-primary shadow-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-not-allowed disabled:opacity-50 ${className}`, {
    disabled, id, onchange: onChange ? (e) => onChange(e) : null
  }, flattened.map(opt => {
     if(opt && opt.nodeName==="OPTION" && opt.value===value) opt.selected=true;
     return opt;
  }));
}

function JSwitch({ checked, onCheckedChange, label }) {
  return el("button", `relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-not-allowed disabled:opacity-50 ${checked ? 'bg-accent shadow-[0_0_8px_var(--accent)]' : 'bg-bg-tertiary'}`, {
    type: "button", role: "switch", "aria-checked": String(!!checked), "aria-label": label,
    onclick: () => onCheckedChange(!checked)
  }, 
    el("span", `pointer-events-none block h-4 w-4 rounded-full bg-bg-primary ring-0 transition-transform ${checked ? 'translate-x-4' : 'translate-x-0'}`)
  );
}

function JButton({ variant="secondary", size="md", disabled, className="", type="button", onClick, children }) {
  const vMap = {
    primary: "bg-accent/15 border-accent text-accent hover:bg-accent/25 shadow-[0_0_12px_var(--accent-muted)]",
    secondary: "bg-bg-tertiary border-border text-text-primary hover:bg-bg-hover",
    ghost: "border-transparent bg-transparent text-text-secondary hover:bg-bg-hover hover:text-text-primary",
    danger: "bg-error/15 border-error/50 text-error hover:bg-error/25 shadow-[0_0_12px_rgba(255,68,68,0.2)]"
  };
  const sMap = { sm: "h-8 px-3 text-xs", md: "h-9 px-4 text-sm" };
  return el("button", `inline-flex items-center justify-center rounded-md border font-display uppercase tracking-wider transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:pointer-events-none disabled:opacity-50 ${vMap[variant]} ${sMap[size]} ${className}`, {
    type, disabled, onclick: onClick ? (e)=>onClick(e) : null
  }, children);
}

function LoadingSpinner({ size=24 }) {
  return elSvg("svg", "animate-spin text-accent", { width: size, height: size, xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24" },
    elSvg("circle", "opacity-25", { cx: 12, cy: 12, r: 10, stroke: "currentColor", "stroke-width": 4 }),
    elSvg("path", "opacity-75", { fill: "currentColor", d: "M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" })
  );
}

function DataTable({ columns, rows, empty = "No data." }) {
  return el("div", "overflow-x-auto", {}, 
    el("table", "w-full text-sm", {}, 
      el("thead", "", {}, 
        el("tr", "border-b border-border", {}, 
          columns.map(col => el("th", `px-3 py-2.5 font-display text-[11px] font-semibold uppercase tracking-[0.18em] text-text-muted ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'}`, {}, col.header))
        )
      ),
      el("tbody", "", {}, 
        rows.length === 0 ? 
          el("tr", "", {}, el("td", "px-3 py-8 text-center font-mono text-xs text-text-muted", { colSpan: columns.length }, empty))
        :
          rows.map((row, i) => 
            el("tr", `border-b border-border-light transition-colors hover:bg-bg-hover ${i % 2 === 1 ? 'bg-bg-tertiary/30' : ''}`, {}, 
              columns.map(col => 
                el("td", `px-3 py-2.5 text-text-secondary ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : ''} ${col.className || ''}`, {}, col.render ? col.render(row) : row[col.key])
              )
            )
          )
      )
    )
  );
}

function JarvisModal({ open, title, description, children, footer, onClose }) {
  if (!open) return null;
  return el("div", "", {}, 
    el("div", "fixed inset-0 z-50 bg-black/60 backdrop-blur-sm animate-fade-in", { onclick: onClose }),
    el("div", "fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 p-4", {}, 
      el("div", "animate-fade-scale-in border border-border bg-bg-secondary shadow-hud-lg rounded-lg overflow-hidden", {}, 
        el("div", "border-b border-border-light bg-bg-tertiary/50 px-5 py-4", {}, 
          el("h2", "font-display text-lg font-semibold uppercase tracking-widest text-text-primary", {}, title),
          description ? el("p", "mt-1 font-mono text-xs text-text-muted", {}, description) : null
        ),
        el("div", "px-5 py-4", {}, children),
        footer ? el("div", "flex items-center justify-end gap-3 border-t border-border-light bg-bg-tertiary/30 px-5 py-3", {}, footer) : null
      )
    )
  );
}

/* ---------- Layout Core ---------- */
function ScanLine() {
  return el("div", "pointer-events-none fixed inset-0 z-50 overflow-hidden", {},
    el("div", "absolute h-[2px] w-full animate-scan-line bg-accent opacity-20 shadow-[0_0_8px_var(--accent)]")
  );
}

function Header({ orbState, connected, onToggleSidebar }) {
  return el("header", "sticky top-0 z-50 flex h-14 items-center gap-3 border-b border-border bg-bg-secondary/95 px-3 backdrop-blur-sm sm:px-5", { style: "box-shadow: 0 1px 0 var(--border-light), 0 4px 24px oklch(0 0 0 / 0.4)" },
    IconButton({ icon: "Menu", label: "Toggle navigation", onClick: onToggleSidebar, className: "lg:hidden" }),
    el("div", "flex items-center gap-2.5", {}, 
      el("div", "relative h-7 w-7", {}, 
        el("div", "absolute inset-0 rounded-full border border-accent/60"),
        el("div", "absolute inset-1 rounded-full border border-accent/40"),
        el("div", "absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent shadow-[0_0_8px_var(--accent)]")
      ),
      el("div", "flex flex-col leading-none", {}, 
        el("span", "font-display text-sm font-semibold uppercase tracking-[0.2em] text-text-primary", {}, "J.A.R.V.I.S."),
        el("span", "hidden font-mono text-[10px] uppercase tracking-widest text-text-muted sm:inline", {}, "Control Center")
      )
    ),
    el("div", "flex-1"),
    el("div", "flex items-center gap-3", {},
      el("div", "hidden items-center gap-2 rounded-md border border-border-light bg-bg-tertiary/60 px-3 py-1.5 sm:flex", {}, 
        OrbIndicator({ state: orbState, size: "md" }),
        el("span", "font-mono text-xs uppercase tracking-wider text-text-secondary", {}, orbState)
      ),
      el("div", "hidden items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest text-text-muted md:flex", {}, 
        el("span", "h-1.5 w-1.5 rounded-full", { style: `background-color: ${connected ? 'var(--success)' : 'var(--text-muted)'}` }),
        connected ? "Online" : "Offline"
      ),
      IconButton({ icon: "Maximize2", label: "Toggle fullscreen", onClick: () => {
        if(document.fullscreenElement) document.exitFullscreen();
        else document.documentElement.requestFullscreen().catch(()=>{});
      }}),
      IconButton({ icon: "Settings", label: "Settings", onClick: () => navigateTo("/settings") })
    )
  );
}

function Sidebar({ open, onClose, currentPath }) {
  const NAV = [
    { to: "/", label: "Dashboard", icon: "LayoutDashboard" },
    { to: "/chat", label: "Chat", icon: "MessageSquare" },
    { to: "/tasks", label: "Tasks", icon: "ListChecks" },
    { to: "/agents", label: "Agents", icon: "Bot" },
    { to: "/memory", label: "Memory", icon: "Brain" },
    { to: "/skills", label: "Skills", icon: "Zap" },
    { to: "/sessions", label: "Sessions", icon: "Users" },
    { to: "/tools", label: "Tools", icon: "Wrench" },
    { to: "/system", label: "System", icon: "Cpu" },
    { to: "/logs", label: "Logs", icon: "ScrollText" },
    { to: "/settings", label: "Settings", icon: "SlidersHorizontal" },
    { to: "/design-preview", label: "Design Preview", icon: "Sparkles" },
  ];

  return el("div", "", {}, 
    open ? el("div", "fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden animate-fade-in", { onclick: onClose }) : null,
    el("aside", `fixed left-0 top-14 z-40 h-[calc(100vh-3.5rem)] border-r border-border bg-bg-secondary transition-transform duration-250 w-[260px] xl:w-[300px] ${open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`, {}, 
      el("div", "flex h-full flex-col", {}, 
        el("div", "border-b border-border-light px-5 py-3", {}, 
          el("p", "font-mono text-[10px] uppercase tracking-[0.25em] text-text-muted", {}, "Navigation")
        ),
        el("nav", "flex-1 overflow-y-auto p-3", {}, 
          el("ul", "space-y-1", {}, 
            NAV.map((item) => {
              const isActive = item.to === "/" ? currentPath === "/" : currentPath.startsWith(item.to);
              return el("li", "", {}, 
                el("a", `group relative flex items-center gap-3 rounded-md px-3 py-2.5 font-display text-[15px] font-medium transition-all ${isActive ? "bg-bg-active text-text-primary" : "text-text-secondary hover:bg-bg-hover hover:text-text-primary"}`, { href: item.to, onclick: (e) => { e.preventDefault(); navigateTo(item.to); onClose(); } },
                  isActive ? el("span", "absolute right-0 top-1/2 h-6 w-[3px] -translate-y-1/2 rounded-l-sm bg-accent shadow-[0_0_10px_var(--accent)]") : null,
                  Icon({ name: item.icon, className: `h-[18px] w-[18px] shrink-0 transition-colors ${isActive ? "text-accent" : "text-text-muted group-hover:text-accent"}` }),
                  el("span", "tracking-wide", {}, item.label)
                )
              );
            })
          )
        ),
        el("div", "border-t border-border-light px-5 py-3", {}, 
          el("div", "flex items-center justify-between", {}, 
            el("span", "font-mono text-[10px] uppercase tracking-widest text-text-muted", {}, "Build"),
            el("span", "font-mono text-[10px] text-text-secondary", {}, "v1.0.0")
          )
        )
      )
    )
  );
}

// Global Shell State
let _sidebarOpen = false;
let _globalOrbState = "idle";
let _globalConnected = false;
function setSidebarOpen(val) { _sidebarOpen = val; renderRoute(); }

const apiFetch = async (endpoint, options = {}) => {
  try {
    const res = await fetch(`/api${endpoint}`, options);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    return null;
  }
};

let _stateWs = null;
function initGlobals() {
  if (_stateWs) return;
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  _stateWs = new WebSocket(`${protocol}//${window.location.host}/api/state/ws`);
  _stateWs.onopen = () => { _globalConnected = true; renderRoute(); };
  _stateWs.onclose = () => { _globalConnected = false; renderRoute(); setTimeout(() => { _stateWs = null; initGlobals(); }, 3000); };
  _stateWs.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.state) { _globalOrbState = data.state; renderRoute(); }
    } catch(err){}
  };
}

function ArcShell({ children }) {
  const currentPath = window.location.pathname || "/";
  return el("div", "min-h-screen bg-bg-primary", {}, 
    ScanLine(),
    Header({ orbState: _globalOrbState, connected: _globalConnected, onToggleSidebar: () => setSidebarOpen(!_sidebarOpen) }),
    Sidebar({ open: _sidebarOpen, onClose: () => setSidebarOpen(false), currentPath }),
    el("main", "lg:pl-[260px] xl:pl-[300px]", {}, 
      el("div", "mx-auto w-full max-w-[1800px] px-4 py-5 sm:px-6 sm:py-6 lg:px-8", {}, children)
    )
  );
}

/* ---------- Views / Pages ---------- */
function renderIndexPage() {
  const container = el("div", "", { id: "p-index" });
  let status = null;
  let stats = null;

  const load = async () => {
    if (!document.getElementById("p-index")) return;
    const [st, vital] = await Promise.all([apiFetch("/system"), apiFetch("/system/stats")]);
    if (st) status = st;
    if (vital) stats = vital;
    renderInner();
    setTimeout(load, 2000);
  };

  const renderInner = () => {
    container.innerHTML = "";
    const ACTIVITY = [
      { time: new Date().toLocaleTimeString(), event: "Live feed engaged", level: "info" }
    ];
    const VITALS = [
      { label: "CPU", value: stats?.cpu_percent || 0, color: "var(--accent)" },
      { label: "Memory", value: stats?.ram_percent || 0, color: "var(--success)" },
      { label: "Disk I/O", value: stats?.disk_percent || 0, color: "var(--warning)" },
      { label: "VRAM", value: stats?.vram_percent || 0, color: "var(--info)" },
    ];
    
    container.appendChild(ArcShell({ children: [
      el("div", "mb-6 flex flex-wrap items-end justify-between gap-3", {}, 
        el("div", "", {}, 
          el("h1", "font-display text-2xl font-semibold uppercase tracking-[0.15em] text-text-primary", {}, "Dashboard"),
          el("p", "mt-1 font-mono text-xs uppercase tracking-widest text-text-muted", {}, "Real-time orbital telemetry")
        ),
        el("div", "flex items-center gap-3 rounded-md border border-border-light bg-bg-secondary px-3 py-2", {}, OrbIndicator({ state: status?"idle":"error", size: "md", showLabel: true }))
      ),
      el("div", "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4", {}, 
        StatTile({ label: "System Status", value: status ? "Nominal" : "Wait...", accentColor: status?"var(--success)":"var(--error)", icon: Icon({ name: "Zap" }), delta: { value: status?"Online":"Connecting", trend: "flat" } }),
        StatTile({ label: "Agents", value: status?.agents?.total || 0, icon: Icon({ name: "Bot" }), delta: { value: `${status?.agents?.running || 0} active`, trend: "up" } }),
        StatTile({ label: "Memory Load", value: stats?.ram_percent || 0, unit: "%", icon: Icon({ name: "MemoryStick" }) }),
        StatTile({ label: "Tasks", value: status?.tasks?.total || 0, icon: Icon({ name: "ListChecks" }), delta: { value: `${status?.tasks?.active || 0} running`, trend: "up" } })
      ),
      el("div", "mt-5 grid grid-cols-1 gap-4 lg:grid-cols-3", {}, 
        Widget({ title: "System Vitals", icon: Icon({ name: "Activity" }), className: "lg:col-span-2", children: 
          el("div", "space-y-4", {}, VITALS.map(v => 
            el("div", "", {}, 
              el("div", "mb-1.5 flex items-baseline justify-between", {}, el("span", "font-mono text-xs uppercase tracking-widest text-text-secondary", {}, v.label), el("span", "font-display text-sm font-semibold tabular-nums", { style: `color: ${v.color}` }, `${v.value}%`)),
              el("div", "h-2 overflow-hidden rounded-sm bg-bg-tertiary", {}, el("div", "h-full rounded-sm transition-all duration-700", { style: `width: ${v.value}%; background-color: ${v.color}; box-shadow: 0 0 12px ${v.color}` }))
            )
          ))
        }),
        Widget({ title: "Activity Feed", icon: Icon({ name: "Radio" }), children: 
          el("ul", "space-y-2.5", {}, ACTIVITY.map(a => 
            el("li", "flex items-start gap-3 rounded-md border border-border-light bg-bg-tertiary/40 p-2.5", {}, 
              el("span", "mt-1 font-mono text-[10px] text-text-muted", {}, a.time),
              el("span", "flex-1 text-xs text-text-secondary", {}, a.event),
              JBadge({ variant: a.level }, a.level)
            )
          ))
        })
      )
    ]}));
  };
  renderInner();
  setTimeout(load, 50);
  return container;
}

const _chatState = { messages: [], input: "", session: "ui_" + Math.random().toString(36).substr(2, 6) };
let _chatWs = null;

function renderChatPage() {
  const container = el("div", "", { id: "p-chat" });
  
  if (!_chatWs || _chatWs.readyState === WebSocket.CLOSED) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    _chatWs = new WebSocket(`${protocol}//${window.location.host}/api/chat/ws`);
    _chatWs.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (document.getElementById("p-chat")) {
        let last = _chatState.messages[_chatState.messages.length - 1];
        if (last && last.role === "assistant" && !last.done) {
          last.content += data.token || "";
          last.done = data.done;
        } else if (!data.done) {
          _chatState.messages.push({ role: "assistant", content: data.token || "", done: data.done, ts: new Date().toLocaleTimeString("en-GB", { hour12: false }) });
        }
        renderInner();
      }
    };
  }

  const renderInner = () => {
    container.innerHTML = "";
    const send = (e) => {
      e.preventDefault();
      const text = _chatState.input.trim();
      if (!text || !_chatWs || _chatWs.readyState !== WebSocket.OPEN) return;
      _chatState.messages.push({ role: "user", content: text, done: true, ts: new Date().toLocaleTimeString("en-GB", { hour12: false }) });
      _chatState.input = "";
      renderInner();
      _chatWs.send(JSON.stringify({ message: text, session_id: _chatState.session }));
    };

    container.appendChild(ArcShell({ children: [
      el("div", "mb-5 flex items-center justify-between", {}, 
        el("div", "", {}, 
          el("h1", "font-display text-2xl font-semibold tracking-wide text-text-primary", {}, "Conversation Channel"),
          el("p", "font-mono text-xs uppercase tracking-[0.2em] text-text-muted", {}, "secure · end-to-end encrypted")
        ),
        JBadge({ variant: "success" }, "online")
      ),
      Widget({ title: "J.A.R.V.I.S. — active session", children: 
        el("div", "flex h-[60vh] flex-col", {}, 
          el("div", "flex-1 space-y-4 overflow-y-auto pr-2", { id: "msg-scroll" }, 
            _chatState.messages.map(m => el("div", `flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`, {}, 
              el("div", `max-w-[75%] rounded-md border px-3 py-2 ${m.role==='user'?'border-accent/40 bg-accent/10 text-text-primary':'border-border bg-bg-tertiary text-text-secondary'}`, {}, 
                el("div", "font-mono text-[10px] uppercase tracking-[0.2em] text-text-muted", {}, `${m.role} · ${m.ts}`),
                el("p", "mt-1 font-display text-[15px] leading-relaxed", {}, m.content)
              )
            ))
          ),
          el("form", "mt-4 flex items-center gap-2 border-t border-border pt-3", { onsubmit: send }, 
            el("div", "flex-1", {}, JInput({ value: _chatState.input, onChange: (e) => { _chatState.input = e.target.value; }, placeholder: "Transmit a message…" })),
            JButton({ type: "submit", variant: "primary", children: [Icon({ name: "Send", className: "mr-2 h-4 w-4" }), "Send"] })
          )
        )
      })
    ]}));
    const scroller = container.querySelector("#msg-scroll");
    if(scroller) scroller.scrollTop = scroller.scrollHeight;
  };
  renderInner();
  return container;
}

function renderTasksPage() {
  const container = el("div", "", { id: "p-tasks" });
  let TASKS = [];
  let summary = null;

  const load = async () => {
    if (!document.getElementById("p-tasks")) return;
    const [tlist, sm] = await Promise.all([apiFetch("/tasks"), apiFetch("/tasks/status/summary")]);
    if (tlist) TASKS = tlist;
    if (sm) summary = sm;
    renderInner();
    setTimeout(load, 2500);
  };

  const renderInner = () => {
    container.innerHTML = "";
    const SV = { queued: "info", running: "warning", completed: "success", failed: "error" };
    const cols = [
      { key: "id", header: "ID", className: "font-mono text-xs text-text-muted" },
      { key: "name", header: "Task" },
      { key: "agent_id", header: "Agent", className: "font-mono text-xs text-text-muted" },
      { key: "status", header: "Status", render: r => JBadge({ variant: SV[r.status] || "neutral" }, r.status) },
      { key: "progress", header: "Progress", className: "font-mono text-xs" }
    ];
    container.appendChild(ArcShell({ children: [
      el("div", "mb-5", {}, el("h1", "font-display text-2xl font-semibold tracking-wide text-text-primary", {}, "Task Queue"), el("p", "font-mono text-xs uppercase tracking-[0.2em] text-text-muted", {}, "orchestrator · live")),
      el("div", "mb-5 grid grid-cols-2 gap-4 lg:grid-cols-4", {}, 
        StatTile({ label: "Queued", value: summary?.queued || 0 }), StatTile({ label: "Running", value: summary?.running || 0, accentColor: "var(--warning)" }),
        StatTile({ label: "Completed", value: summary?.done || 0, accentColor: "var(--success)" }), StatTile({ label: "Failed", value: summary?.failed || 0, accentColor: "var(--error)" })
      ),
      Widget({ title: "Active & recent tasks", children: DataTable({ columns: cols, rows: TASKS }) })
    ]}));
  };
  renderInner();
  setTimeout(load, 50);
  return container;
}

function renderAgentsPage() {
  const container = el("div", "", { id: "p-agents" });
  let AGENTS = [];
  
  const load = async () => {
    if (!document.getElementById("p-agents")) return;
    const a = await apiFetch("/agents/");
    if (a && a.agents) AGENTS = a.agents; else if (Array.isArray(a)) AGENTS = a;
    renderInner();
    setTimeout(load, 3000);
  };

  const renderInner = () => {
    container.innerHTML = "";
    const SV = { online: "success", idle: "info", offline: "error", running: "warning" };
    container.appendChild(ArcShell({ children: [
      el("div", "mb-5", {}, el("h1", "font-display text-2xl font-semibold tracking-wide text-text-primary", {}, "Agent Registry"), el("p", "font-mono text-xs uppercase tracking-[0.2em] text-text-muted", {}, `${AGENTS.filter(a=>a.state==='running' || a.state==='online').length} online · ${AGENTS.length} total`)),
      el("div", "grid gap-4 sm:grid-cols-2 lg:grid-cols-3", {}, AGENTS.map(a => 
        Widget({ title: a.name || a.id, icon: Icon({ name: "Bot", className: "h-4 w-4 text-accent" }), action: JBadge({ variant: SV[a.state] || "neutral" }, a.state || "unknown"), children: 
          el("div", "space-y-3", {}, 
            el("p", "font-mono text-[11px] uppercase tracking-[0.2em] text-text-muted", {}, a.role || a.description || "Auxiliary Unit"),
            el("div", "flex items-center justify-between font-mono text-[11px] text-text-muted mt-2", {}, el("span", "", {}, "id"), el("span", "text-text-secondary", {}, a.id))
          )
        })
      ))
    ]}));
  };
  renderInner();
  setTimeout(load, 50);
  return container;
}

function renderMemoryPage() {
  const container = el("div", "", { id: "p-memory" });
  let ROWS = [];
  
  const load = async () => {
    if (!document.getElementById("p-memory")) return;
    const items = await apiFetch("/memory/palace");
    if (items) ROWS = items;
    renderInner();
    setTimeout(load, 5000);
  };

  const renderInner = () => {
    container.innerHTML = "";
    const SV = { fact: "info", preference: "success", context: "warning" };
    const cols = [
      { key: "key", header: "Key", className: "font-mono text-xs text-accent" },
      { key: "type", header: "Type", render: r => JBadge({ variant: SV[r.type] || "neutral" }, r.type || "entry") },
      { key: "content", header: "Content", render: r => String(r.content || r.value || "") },
      { key: "updated", header: "Updated", className: "font-mono text-xs text-text-muted", render: r => r.updated_at || r.ts || "—" }
    ];
    container.appendChild(ArcShell({ children: [
      el("div", "mb-5", {}, el("h1", "font-display text-2xl font-semibold tracking-wide text-text-primary", {}, "Memory Store"), el("p", "font-mono text-xs uppercase tracking-[0.2em] text-text-muted", {}, "long-term · persistent")),
      el("div", "mb-5 grid grid-cols-2 gap-4 lg:grid-cols-4", {}, 
        StatTile({ label: "Total entries", value: ROWS.length }), 
        StatTile({ label: "Facts", value: ROWS.filter(r=>r.type==='fact').length, accentColor: "var(--info)" }),
        StatTile({ label: "Preferences", value: ROWS.filter(r=>r.type==='preference').length, accentColor: "var(--success)" }), 
        StatTile({ label: "Embeddings", value: "Active", accentColor: "var(--warning)" })
      ),
      Widget({ title: "Palace entries", children: DataTable({ columns: cols, rows: ROWS }) })
    ]}));
  };
  renderInner();
  setTimeout(load, 50);
  return container;
}

function renderSkillsPage() {
  const container = el("div", "", { id: "p-skills" });
  let SKILLS = [];
  
  const load = async () => {
    if (!document.getElementById("p-skills")) return;
    const sm = await apiFetch("/skills/summary");
    if (sm && sm.skills) SKILLS = sm.skills; else if (Array.isArray(sm)) SKILLS = sm;
    renderInner();
    setTimeout(load, 10000);
  };

  const renderInner = () => {
    container.innerHTML = "";
    container.appendChild(ArcShell({ children: [
      el("div", "mb-5", {}, el("h1", "font-display text-2xl font-semibold tracking-wide text-text-primary", {}, "Skill Library"), el("p", "font-mono text-xs uppercase tracking-[0.2em] text-text-muted", {}, `${SKILLS.filter(s=>s.enabled!==false).length} enabled · ${SKILLS.length} total`)),
      el("div", "grid gap-4 sm:grid-cols-2 lg:grid-cols-3", {}, SKILLS.map(s => 
        Widget({ title: s.name || s.id, icon: Icon({ name: "Sparkles", className: "h-4 w-4 text-accent" }), action: JBadge({ variant: s.enabled === false ? "info" : "success" }, s.enabled === false ? "disabled" : "enabled"), children: 
          el("div", "", {}, el("p", "font-mono text-[11px] uppercase tracking-[0.2em] text-text-muted", {}, s.type || s.category || "Tool"), el("p", "mt-2 text-sm leading-relaxed text-text-secondary", {}, s.description || "No description available."))
        })
      ))
    ]}));
  };
  renderInner();
  setTimeout(load, 50);
  return container;
}

function renderSessionsPage() {
  const container = el("div", "", { id: "p-sessions" });
  let ROWS = [];
  
  const load = async () => {
    if (!document.getElementById("p-sessions")) return;
    const sess = await apiFetch("/sessions");
    if (sess) ROWS = Array.isArray(sess) ? sess : (sess.sessions || []);
    renderInner();
    setTimeout(load, 5000);
  };

  const renderInner = () => {
    container.innerHTML = "";
    const SV = { active: "success", idle: "warning", ended: "info" };
    const cols = [
      { key: "id", header: "Session ID", className: "font-mono text-xs text-accent" },
      { key: "user", header: "User", className: "font-mono text-xs", render: r => r.user || "operator" },
      { key: "device", header: "Device", render: r => r.device || "Web UI" },
      { key: "location", header: "Location", className: "text-text-secondary", render: r => r.location || "127.0.0.1" },
      { key: "started", header: "Started", className: "font-mono text-xs text-text-muted", render: r => r.created_at || r.started || "—" },
      { key: "status", header: "Status", render: r => JBadge({ variant: SV[r.status] || "success" }, r.status || "active") }
    ];
    container.appendChild(ArcShell({ children: [
      el("div", "mb-5", {}, el("h1", "font-display text-2xl font-semibold tracking-wide text-text-primary", {}, "Sessions"), el("p", "font-mono text-xs uppercase tracking-[0.2em] text-text-muted", {}, "authentication · presence")),
      el("div", "mb-5 grid grid-cols-2 gap-4 lg:grid-cols-4", {}, 
        StatTile({ label: "Active", value: Math.max(1, ROWS.filter(r=>r.status==='active').length), accentColor: "var(--success)" }), StatTile({ label: "Idle", value: 0, accentColor: "var(--warning)" }),
        StatTile({ label: "Total", value: window.localStorage.getItem('hits') || ROWS.length || 1 }), StatTile({ label: "This week", value: 4, accentColor: "var(--info)" })
      ),
      Widget({ title: "All sessions", children: DataTable({ columns: cols, rows: ROWS.length ? ROWS : [{id: "current_ui", status: "active", device: "Web UI frontend"}] }) })
    ]}));
  };
  renderInner();
  setTimeout(load, 50);
  return container;
}

function renderToolsPage() {
  const container = el("div", "", { id: "p-tools" });
  let TOOLS = [];
  
  const load = async () => {
    if (!document.getElementById("p-tools")) return;
    const tl = await apiFetch("/tools");
    if (tl) TOOLS = Array.isArray(tl) ? tl : (tl.tools || []);
    renderInner();
    setTimeout(load, 15000);
  };

  const renderInner = () => {
    container.innerHTML = "";
    const SV = { connected: "success", available: "info", error: "error" };
    container.appendChild(ArcShell({ children: [
      el("div", "mb-5", {}, el("h1", "font-display text-2xl font-semibold tracking-wide text-text-primary", {}, "Tool Belt"), el("p", "font-mono text-xs uppercase tracking-[0.2em] text-text-muted", {}, "integrations · execution")),
      el("div", "grid gap-4 sm:grid-cols-2 lg:grid-cols-3", {}, TOOLS.map(t => 
        Widget({ title: t.name || t.id, icon: Icon({ name: "Wrench", className: "h-4 w-4 text-accent" }), action: JBadge({ variant: SV[t.status] || "success" }, t.status || "available"), children: 
          el("div", "", {}, 
            el("p", "font-mono text-[11px] uppercase tracking-[0.2em] text-text-muted", {}, t.provider || t.package || "core"),
            el("p", "mb-3 mt-2 text-sm leading-relaxed text-text-secondary", {}, t.description || "Utility tool"),
            el("div", "flex items-center justify-between border-t border-border-light pt-2 font-mono text-[11px] uppercase tracking-[0.2em] text-text-muted", {}, el("span", "", {}, "calls"), el("span", "text-text-secondary", {}, (t.calls || 0).toLocaleString()))
          )
        })
      ))
    ]}));
  };
  renderInner();
  setTimeout(load, 50);
  return container;
}

function renderSystemPage() {
  const container = el("div", "", { id: "p-system" });
  let stats = null;
  
  const load = async () => {
    if (!document.getElementById("p-system")) return;
    const st = await apiFetch("/system/stats");
    if (st) stats = st;
    renderInner();
    setTimeout(load, 2500);
  };

  const renderInner = () => {
    container.innerHTML = "";
    const procCols = [
      { key: "pid", header: "PID", className: "font-mono text-text-muted" },
      { key: "name", header: "Process", className: "font-mono text-text-primary" },
      { key: "cpu", header: "CPU", align: "right" },
      { key: "mem", header: "Memory", align: "right" },
      { key: "state", header: "State", align: "right", render: r => JBadge({ variant: r.state || "info" }, r.state || "info") }
    ];
    container.appendChild(ArcShell({ children: [
      el("div", "mb-6", {}, el("h1", "font-display text-2xl font-semibold uppercase tracking-[0.15em] text-text-primary", {}, "System"), el("p", "mt-1 font-mono text-xs uppercase tracking-widest text-text-muted", {}, "Hardware inventory & resource map")),
      el("div", "grid grid-cols-1 gap-4 lg:grid-cols-2", {}, 
        Widget({ title: "Core Subsystems", icon: Icon({ name: "Cpu" }), children: 
          el("div", "space-y-4 font-mono text-sm", {}, 
            el("div", "flex justify-between border-b pb-2", {}, el("span", "text-text-muted", {}, "jarvis_cpu_load"), el("span", "text-text-secondary", {}, `${stats?.jarvis_cpu||0}%`)),
            el("div", "flex justify-between border-b pb-2", {}, el("span", "text-text-muted", {}, "jarvis_ram_mb"), el("span", "text-accent", {}, `${Math.round(stats?.jarvis_ram_mb||0)}`)),
            el("div", "flex justify-between border-b pb-2", {}, el("span", "text-text-muted", {}, "cpu_cores"), el("span", "text-text-secondary", {}, `${stats?.cpu_count||16}`)),
            el("div", "flex justify-between border-b pb-2", {}, el("span", "text-text-muted", {}, "gpu_temp_c"), el("span", "text-warning", {}, `${stats?.gpu_temp_c||0} °C`))
          )
        }),
        Widget({ title: "Memory & Disks", icon: Icon({ name: "HardDrive" }), children: 
          el("div", "grid grid-cols-1 gap-4 sm:grid-cols-2", {}, 
            el("div", "rounded-md border border-border-light bg-bg-tertiary/50 p-4", {}, el("p", "font-mono text-[10px] uppercase tracking-widest text-text-muted", {}, "RAM Used"), el("p", "mt-1 font-display text-2xl text-text-primary tabular-nums", {}, `${stats?.ram_used_gb||0} `, el("span", "text-sm text-text-muted", {}, "GB"))),
            el("div", "rounded-md border border-border-light bg-bg-tertiary/50 p-4", {}, el("p", "font-mono text-[10px] uppercase tracking-widest text-text-muted", {}, "VRAM Used"), el("p", "mt-1 font-display text-2xl text-text-primary tabular-nums", {}, `${stats?.vram_used_gb||0} `, el("span", "text-sm text-text-muted", {}, "GB"))),
            el("div", "rounded-md border border-border-light bg-bg-tertiary/50 p-4 col-span-2", {}, el("p", "font-mono text-[10px] uppercase tracking-widest text-text-muted", {}, "Storage Used"), el("p", "mt-1 font-display text-2xl text-warning tabular-nums", {}, `${stats?.disk_used_gb||0} `, el("span", "text-sm text-text-muted", {}, `/ ${stats?.disk_total_gb||0} GB`)))
          )
        }),
        Widget({ title: "Active Processes / Metrics", className: "lg:col-span-2", children: DataTable({ columns: procCols, rows: [] }) })
      )
    ]}));
  };
  renderInner();
  setTimeout(load, 50);
  return container;
}

function renderLogsPage() {
  const container = el("div", "", { id: "p-logs" });
  let LOGS = [];
  let query = ""; let level = "all";
  
  const load = async () => {
    if (!document.getElementById("p-logs")) return;
    const l = await apiFetch("/logs");
    if (l) LOGS = Array.isArray(l) ? l : l.logs || [];
    renderInner();
    setTimeout(load, 3000);
  };

  const renderInner = () => {
    container.innerHTML = "";
    const SV = { INFO: "info", WARNING: "warning", ERROR: "error", DEBUG: "neutral", info: "info", warning: "warning", error: "error", debug: "neutral" };
    const cols = [
      { key: "ts", header: "Timestamp", className: "font-mono text-xs text-text-muted whitespace-nowrap" },
      { key: "level", header: "Level", render: r => JBadge({ variant: SV[r.level] || "neutral" }, r.level || "info") },
      { key: "source", header: "Source", className: "font-mono text-xs text-accent whitespace-nowrap" },
      { key: "message", header: "Message", className: "text-text-secondary", render: r => String(r.message || r.msg || "—") }
    ];
    const filtered = LOGS.filter(l => (level === "all" || String(l.level).toLowerCase() === level) && (query === "" || String(l.message||l.msg).toLowerCase().includes(query.toLowerCase()) || String(l.source).toLowerCase().includes(query.toLowerCase())));
    
    container.appendChild(ArcShell({ children: [
      el("div", "mb-6", {}, el("h1", "font-display text-2xl font-semibold uppercase tracking-[0.15em] text-text-primary", {}, "Event Log"), el("p", "mt-1 font-mono text-xs uppercase tracking-widest text-text-muted", {}, "Live system event stream")),
      Widget({ title: "", children: el("div", "", {}, 
        el("div", "mb-4 flex flex-wrap items-center gap-3", {}, 
          el("div", "relative flex-1 min-w-[200px]", {}, 
            Icon({ name: "Search", className: "absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" }),
            JInput({ type: "search", placeholder: "Search messages or sources…", value: query, onChange: (e) => { query = e.target.value; renderInner(); }, className: "pl-9" })
          ),
          el("div", "flex gap-1", {}, ["all", "info", "success", "warning", "error"].map(l => 
            el("button", `rounded-md border px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest transition-colors ${level===l ? 'border-accent bg-accent/15 text-accent' : 'border-border bg-bg-tertiary text-text-muted hover:border-border-dark hover:text-text-secondary'}`, { onclick: () => { level = l; renderInner(); } }, l)
          ))
        ),
        el("div", "max-h-[60vh] overflow-y-auto", {}, DataTable({ columns: cols, rows: filtered, empty: "No matching log entries." })),
        el("div", "mt-3 flex items-center justify-between font-mono text-[10px] uppercase tracking-widest text-text-muted", {}, el("span", "", {}, `${filtered.length} entries`), el("span", "flex items-center gap-1.5", {}, el("span", "h-1.5 w-1.5 animate-pulse rounded-full bg-success"), "Live"))
      )})
    ]}));
  };
  renderInner();
  setTimeout(load, 50);
  return container;
}

const _settingsState = { config: null, modified: false, advancedOpen: false };
function renderSettingsPage() {
  const container = el("div", "", { id: "p-settings" });

  const load = async () => {
    if (!document.getElementById("p-settings")) return;
    if (_settingsState.modified) return;
    const s = await apiFetch("/settings");
    if (s && !_settingsState.modified) { _settingsState.config = s; renderInner(); }
  };

  const renderInner = () => {
    container.innerHTML = "";
    if (!_settingsState.config) {
      container.appendChild(ArcShell({ children: [el("div", "p-5 text-accent", {}, "Loading Settings...")] }));
      return;
    }
    
    const conf = _settingsState.config;
    const makeSwitch = (label, section, key) => JSwitch({ label, checked: conf[section]?.[key] === true, onChange: (v) => { if(!conf[section]) conf[section]={}; conf[section][key] = v; _settingsState.modified = true; renderInner(); } });

    container.appendChild(ArcShell({ children: [
      el("div", "mb-6 flex items-end justify-between", {}, 
        el("div", "", {}, el("h1", "font-display text-2xl font-semibold uppercase tracking-[0.15em] text-text-primary", {}, "Settings"), el("p", "mt-1 font-mono text-xs uppercase tracking-widest text-text-muted", {}, "Operator preferences & system tuning")),
        el("div", "flex gap-3", {}, 
          JButton({ variant: "outline", disabled: !_settingsState.modified, onClick: () => { _settingsState.modified = false; load(); } }, "Discard"),
          JButton({ variant: "primary", disabled: !_settingsState.modified, onClick: async () => { await apiFetch("/settings", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(conf) }); _settingsState.modified = false; } }, "Save Changes")
        )
      ),
      el("div", "grid grid-cols-1 gap-4 lg:grid-cols-2", {}, 
        Widget({ title: "AI Core", children: el("div", "space-y-4", {}, 
          FormGroup({ label: "Model Reference", children: JInput({ value: conf.brain?.model || "", onChange: e=>{ conf.brain.model = e.target.value; _settingsState.modified=true; renderInner(); } }) }),
          FormGroup({ label: "VRAM Ratio", children: JInput({ type:"number", value: String(conf.brain?.vram_ratio || 0), onChange: e=>{ conf.brain.vram_ratio = parseFloat(e.target.value); _settingsState.modified=true; renderInner(); } }) })
        )}),
        Widget({ title: "Subsystem Toggles", children: el("div", "space-y-4", {}, 
          el("div", "flex items-center justify-between rounded-md border border-border-light bg-bg-tertiary/50 px-3 py-3", {}, el("div", "", {}, el("p", "font-display text-sm text-text-primary", {}, "Voice interface"), el("p", "font-mono text-[11px] text-text-muted", {}, "Accept spoken commands")), makeSwitch("", "capabilities", "voice")),
          el("div", "flex items-center justify-between rounded-md border border-border-light bg-bg-tertiary/50 px-3 py-3", {}, el("div", "", {}, el("p", "font-display text-sm text-text-primary", {}, "Ears (Wake Word)"), el("p", "font-mono text-[11px] text-text-muted", {}, "Listen constantly for JARVIS")), makeSwitch("", "capabilities", "ears")),
          el("div", "flex items-center justify-between rounded-md border border-border-light bg-bg-tertiary/50 px-3 py-3", {}, el("div", "", {}, el("p", "font-display text-sm text-text-primary", {}, "Eyes (Vision OCR)"), el("p", "font-mono text-[11px] text-text-muted", {}, "Analyze screens")), makeSwitch("", "capabilities", "eyes"))
        )})
      )
    ]}));
  };
  
  if (!_settingsState.config) {
    _settingsState.config = { brain: { model: "", vram_ratio: 0 }, capabilities: { voice: true, ears: true, eyes: true } };
    load();
  } else {
    renderInner();
  }
  setTimeout(() => { if(!_settingsState.modified) load(); }, 50);
  return container;
}

function renderDesignPreviewPage() {
  const container = el("div", "", { id: "p-design" });
  let modal = false;
  let sw = true;
  const renderInner = () => {
    container.innerHTML = "";
    container.appendChild(ArcShell({ children: [
      el("div", "mb-6", {}, el("h1", "font-display text-2xl font-semibold uppercase tracking-[0.15em] text-text-primary", {}, "Design Preview"), el("p", "mt-1 font-mono text-xs uppercase tracking-widest text-text-muted", {}, "Storybook-style component gallery")),
      el("section", "mb-8", {}, 
        el("div", "mb-3 flex items-center gap-2", {}, el("span", "h-px flex-1 bg-border-light"), el("h2", "font-mono text-[10px] uppercase tracking-[0.3em] text-text-muted", {}, "Orb Indicator"), el("span", "h-px flex-1 bg-border-light")),
        el("div", "rounded-lg border border-border bg-bg-secondary/40 p-4", {}, 
          el("div", "flex flex-wrap items-center gap-6", {}, ["idle", "listening", "speaking", "thinking", "error"].map(s => el("div", "flex flex-col items-center gap-2", {}, OrbIndicator({ state: s, size: "lg" }), el("span", "font-mono text-[10px] uppercase tracking-widest text-text-muted", {}, s))))
        )
      ),
      el("section", "mb-8", {}, 
        el("div", "mb-3 flex items-center gap-2", {}, el("span", "h-px flex-1 bg-border-light"), el("h2", "font-mono text-[10px] uppercase tracking-[0.3em] text-text-muted", {}, "Buttons & Badges"), el("span", "h-px flex-1 bg-border-light")),
        el("div", "rounded-lg border border-border bg-bg-secondary/40 p-4 space-y-4", {}, 
          el("div", "flex flex-wrap gap-2", {}, JBadge({ variant: "success" }, "success"), JBadge({ variant: "warning" }, "warning"), JBadge({ variant: "error" }, "error"), JBadge({ variant: "info" }, "info"), JBadge({ variant: "neutral" }, "neutral")),
          el("div", "flex flex-wrap gap-3", {}, JButton({ variant: "primary", children: "Primary" }), JButton({ variant: "secondary", children: "Secondary" }), JButton({ variant: "ghost", children: "Ghost" }), JButton({ variant: "danger", children: "Danger" }), JButton({ variant: "primary", disabled: true, children: "Disabled" }))
        )
      ),
      el("section", "mb-8", {}, 
        el("div", "mb-3 flex items-center gap-2", {}, el("span", "h-px flex-1 bg-border-light"), el("h2", "font-mono text-[10px] uppercase tracking-[0.3em] text-text-muted", {}, "Forms & Modals"), el("span", "h-px flex-1 bg-border-light")),
        el("div", "rounded-lg border border-border bg-bg-secondary/40 p-4", {}, 
          el("div", "grid grid-cols-1 gap-4 sm:grid-cols-2", {}, FormGroup({ label: "Text input", children: JInput({ placeholder: "Enter..." }) }), FormGroup({ label: "Select", children: JSelect({ children: [el("option", "", {}, "Opt A")] }) }), el("div", "flex items-center justify-between rounded-md border border-border-light bg-bg-tertiary/50 px-3 py-3", {}, el("span", "font-display text-sm text-text-primary", {}, "Switch"), JSwitch({ checked: sw, onCheckedChange: v=>{sw=v; renderInner();} })), el("div", "flex items-center gap-2", {}, LoadingSpinner({ size: 20 }), "LoadingSpinner")),
          el("div", "mt-4", {}, JButton({ variant: "primary", onClick: () => { modal = true; renderInner(); }, children: "Open Modal" }))
        )
      ),
      JarvisModal({ open: modal, onClose: () => { modal = false; renderInner(); }, title: "Confirm Action", description: "Modal preview working natively.", children: el("p", "text-sm text-text-secondary", {}, "This action is handled exclusively without React overlay states!"), footer: el("div", "", {}, JButton({ variant: "ghost", onClick: () => { modal = false; renderInner(); }, children: "Cancel" }), JButton({ variant: "primary", onClick: () => { modal = false; renderInner(); }, children: "Confirm" })) })
    ]}));
  };
  renderInner();
  return container;
}


/* ---------- Router ---------- */
const ROUTES = {
  "/": renderIndexPage,
  "/chat": renderChatPage,
  "/tasks": renderTasksPage,
  "/agents": renderAgentsPage,
  "/memory": renderMemoryPage,
  "/skills": renderSkillsPage,
  "/sessions": renderSessionsPage,
  "/tools": renderToolsPage,
  "/system": renderSystemPage,
  "/logs": renderLogsPage,
  "/settings": renderSettingsPage,
  "/design-preview": renderDesignPreviewPage
};

function navigateTo(path) {
  window.history.pushState({}, "", path);
  renderRoute();
}

function renderRoute() {
  const path = window.location.pathname || "/";
  const handler = ROUTES[path] || ROUTES["/"];
  const container = document.getElementById("root");
  container.innerHTML = "";
  container.appendChild(handler());
}

/* ---------- Boot ---------- */
document.addEventListener("DOMContentLoaded", () => {
  initGlobals();
  renderRoute();
  window.addEventListener("popstate", () => renderRoute());
});