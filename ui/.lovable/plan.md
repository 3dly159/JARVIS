
## J.A.R.V.I.S. Control Center — Plan

Build a dark-theme HUD dashboard adapted to the React + TanStack Start + Tailwind stack. All design tokens from your spec become CSS custom properties in `src/styles.css` and Tailwind theme variables, so utility classes like `bg-bg-primary`, `text-accent`, etc. work out of the box.

### Design tokens & typography
- Replace existing color variables in `src/styles.css` with the JARVIS palette (bg-primary `#000810`, accent `#00b4ff`, status colors, etc.) — kept in `oklch` per project rules but matching the hex spec.
- Load **Rajdhani** (400/500/600/700) and **Share Tech Mono** from Google Fonts in `__root.tsx`.
- Register `--font-display` (Rajdhani) and `--font-mono` (Share Tech Mono) in the Tailwind `@theme` block.
- Add HUD-specific keyframes: `pulse-orb`, `scan-line`, `fade-scale-in`, plus `prefers-reduced-motion` overrides.

### Layout shell
- `src/components/jarvis/Header.tsx` — fixed 56px top bar: logo glyph, "J.A.R.V.I.S. Control Center" title, `OrbIndicator`, fullscreen + settings icon buttons. `role="banner"`.
- `src/components/jarvis/Sidebar.tsx` — 260px (300px ≥ xl), collapses to 60px icon-only at <1024px; off-canvas drawer at <480px. Uses shadcn `Sidebar` primitives wrapped in JARVIS styling. Active item gets right accent bar.
- `src/components/jarvis/Shell.tsx` — composes Header + Sidebar + main grid (24px padding, responsive 1/2/3/4-column widget grid).

### Routes (each with own `head()` meta)
- `/` — **Dashboard**: 4-column stat widget grid (System Status, Active Processes, Memory Load, Network), a real-time "Activity Feed" card, and a large "System Vitals" panel with mini bars.
- `/system` — **System**: CPU/memory/disk tables, process list with badges.
- `/logs` — **Logs**: scrolling table with mono timestamps, severity badges (info/warning/error/success), search field.
- `/settings` — **Settings**: form groups (text, select, switch), modal trigger for "Advanced Configuration".
- `/design-preview` — **Storybook-style** page showcasing every component with all variants in isolation.

### Component library (under `src/components/jarvis/`)
`OrbIndicator`, `NavItem`, `Widget` (header + body slots, hover lift), `StatTile`, `DataTable`, `Badge` (success/warning/error/info), `IconButton`, `JarvisModal`, `FormGroup`, `Tooltip` wrapper, `LoadingSpinner` (rotating ring with accent glow), `ScanLine` decorative overlay.

### Orb state + WebSocket hook
- `src/hooks/useOrbState.ts` — manages state (`idle | listening | speaking | thinking | error`), maps each to a status color, applies the 150ms pulse on change.
- `src/hooks/useJarvisSocket.ts` — accepts a WS URL via env var (`VITE_JARVIS_WS_URL`); falls back to a mock state cycler when the URL is empty so the UI is alive in preview. Clean reconnect logic. **Reserved for when you share the endpoint** — wiring point is a single line.
- Debug control in `/design-preview` lets you manually trigger each orb state.

### Accessibility
- Sidebar nav: `role="navigation"`, items expose `aria-current="page"` via TanStack `activeProps`.
- Modal: focus trap, `Esc` to close, `role="dialog"` + `aria-modal`, restores focus on close.
- All icon buttons have `aria-label` + tooltip.
- Visible 2px accent focus ring; verified ≥4.5:1 contrast on text/background pairs.
- `prefers-reduced-motion` disables pulse, scan-line, modal scale.

### Out of scope for v1 (call out, don't build)
- Real WS endpoint wiring (stubbed, ready to plug in)
- Persisted user settings
- Toast notification system (shadcn `sonner` already in repo — we'll just style it to match)
