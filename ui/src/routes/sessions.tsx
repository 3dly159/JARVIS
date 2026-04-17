import { createFileRoute } from "@tanstack/react-router";
import { Shell } from "@/components/jarvis/Shell";
import { Widget } from "@/components/jarvis/Widget";
import { DataTable, type Column } from "@/components/jarvis/DataTable";
import { JBadge } from "@/components/jarvis/Badge";
import { StatTile } from "@/components/jarvis/StatTile";

export const Route = createFileRoute("/sessions")({
  head: () => ({
    meta: [
      { title: "Sessions — J.A.R.V.I.S. Control Center" },
      { name: "description", content: "Active and historical user sessions." },
      { property: "og:title", content: "Sessions — J.A.R.V.I.S. Control Center" },
      { property: "og:description", content: "Active and historical user sessions." },
    ],
  }),
  component: SessionsPage,
});

interface SessionRow extends Record<string, unknown> {
  id: string;
  user: string;
  device: string;
  location: string;
  started: string;
  status: "active" | "idle" | "ended";
}

const ROWS: SessionRow[] = [
  { id: "sess_a91", user: "tony.stark", device: "Workshop terminal", location: "Malibu, CA", started: "2h 14m ago", status: "active" },
  { id: "sess_a90", user: "tony.stark", device: "Mark XLII HUD", location: "—", started: "5h 02m ago", status: "idle" },
  { id: "sess_a89", user: "p.potts", device: "Stark Phone", location: "New York, NY", started: "1d ago", status: "ended" },
  { id: "sess_a88", user: "h.hogan", device: "SUV console", location: "En route", started: "1d ago", status: "ended" },
  { id: "sess_a87", user: "tony.stark", device: "Penthouse panel", location: "New York, NY", started: "3d ago", status: "ended" },
];

const STATUS_VARIANT = {
  active: "success",
  idle: "warning",
  ended: "info",
} as const;

const COLUMNS: Column<SessionRow>[] = [
  { key: "id", header: "Session ID", className: "font-mono text-xs text-accent" },
  { key: "user", header: "User", className: "font-mono text-xs" },
  { key: "device", header: "Device" },
  { key: "location", header: "Location", className: "text-text-secondary" },
  { key: "started", header: "Started", className: "font-mono text-xs text-text-muted" },
  {
    key: "status",
    header: "Status",
    render: (r) => <JBadge variant={STATUS_VARIANT[r.status]}>{r.status}</JBadge>,
  },
];

function SessionsPage() {
  return (
    <Shell>
      <div className="mb-5">
        <h1 className="font-display text-2xl font-semibold tracking-wide text-text-primary">
          Sessions
        </h1>
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-text-muted">
          authentication · presence
        </p>
      </div>

      <div className="mb-5 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatTile label="Active" value={1} accentColor="var(--success)" />
        <StatTile label="Idle" value={1} accentColor="var(--warning)" />
        <StatTile label="Today" value={5} />
        <StatTile label="This week" value={28} accentColor="var(--info)" />
      </div>

      <Widget title="All sessions">
        <DataTable columns={COLUMNS} rows={ROWS} />
      </Widget>
    </Shell>
  );
}
