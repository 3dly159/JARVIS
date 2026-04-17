import { createFileRoute } from "@tanstack/react-router";
import { Shell } from "@/components/jarvis/Shell";
import { Widget } from "@/components/jarvis/Widget";
import { DataTable, type Column } from "@/components/jarvis/DataTable";
import { JBadge } from "@/components/jarvis/Badge";
import { StatTile } from "@/components/jarvis/StatTile";

export const Route = createFileRoute("/tasks")({
  head: () => ({
    meta: [
      { title: "Tasks — J.A.R.V.I.S. Control Center" },
      { name: "description", content: "Background tasks queue and execution status." },
      { property: "og:title", content: "Tasks — J.A.R.V.I.S. Control Center" },
      { property: "og:description", content: "Background tasks queue and execution status." },
    ],
  }),
  component: TasksPage,
});

type Status = "queued" | "running" | "completed" | "failed";

interface Task extends Record<string, unknown> {
  id: string;
  name: string;
  agent: string;
  status: Status;
  progress: string;
  eta: string;
}

const TASKS: Task[] = [
  { id: "T-1043", name: "Index sensor archive", agent: "indexer", status: "running", progress: "62%", eta: "2m 14s" },
  { id: "T-1042", name: "Sync calendar events", agent: "calendar", status: "completed", progress: "100%", eta: "—" },
  { id: "T-1041", name: "Compile weekly report", agent: "reporter", status: "queued", progress: "0%", eta: "pending" },
  { id: "T-1040", name: "Probe perimeter cameras", agent: "security", status: "running", progress: "34%", eta: "5m 02s" },
  { id: "T-1039", name: "Backup vault snapshot", agent: "vault", status: "failed", progress: "—", eta: "retry queued" },
  { id: "T-1038", name: "Train classifier v3", agent: "ml-core", status: "completed", progress: "100%", eta: "—" },
];

const STATUS_VARIANT: Record<Status, "info" | "success" | "warning" | "error"> = {
  queued: "info",
  running: "warning",
  completed: "success",
  failed: "error",
};

const COLUMNS: Column<Task>[] = [
  { key: "id", header: "ID", className: "font-mono text-xs" },
  { key: "name", header: "Task" },
  { key: "agent", header: "Agent", className: "font-mono text-xs text-text-muted" },
  {
    key: "status",
    header: "Status",
    render: (r) => <JBadge variant={STATUS_VARIANT[r.status]}>{r.status}</JBadge>,
  },
  { key: "progress", header: "Progress", className: "font-mono text-xs" },
  { key: "eta", header: "ETA", className: "font-mono text-xs text-text-secondary" },
];

function TasksPage() {
  const counts = TASKS.reduce(
    (acc, t) => {
      acc[t.status] += 1;
      return acc;
    },
    { queued: 0, running: 0, completed: 0, failed: 0 } as Record<Status, number>,
  );

  return (
    <Shell>
      <div className="mb-5">
        <h1 className="font-display text-2xl font-semibold tracking-wide text-text-primary">
          Task Queue
        </h1>
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-text-muted">
          orchestrator · live
        </p>
      </div>

      <div className="mb-5 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatTile label="Queued" value={counts.queued} />
        <StatTile label="Running" value={counts.running} accentColor="var(--warning)" />
        <StatTile label="Completed" value={counts.completed} accentColor="var(--success)" />
        <StatTile label="Failed" value={counts.failed} accentColor="var(--error)" />
      </div>

      <Widget title="Active & recent tasks">
        <DataTable columns={COLUMNS} rows={TASKS} />
      </Widget>
    </Shell>
  );
}
