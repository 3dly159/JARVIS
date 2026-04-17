import { createFileRoute } from "@tanstack/react-router";
import { Shell } from "@/components/jarvis/Shell";
import { Widget } from "@/components/jarvis/Widget";
import { DataTable, type Column } from "@/components/jarvis/DataTable";
import { JBadge } from "@/components/jarvis/Badge";
import { StatTile } from "@/components/jarvis/StatTile";

export const Route = createFileRoute("/memory")({
  head: () => ({
    meta: [
      { title: "Memory — J.A.R.V.I.S. Control Center" },
      { name: "description", content: "Persistent memory store: facts, preferences, and embeddings." },
      { property: "og:title", content: "Memory — J.A.R.V.I.S. Control Center" },
      {
        property: "og:description",
        content: "Persistent memory store: facts, preferences, and embeddings.",
      },
    ],
  }),
  component: MemoryPage,
});

interface MemoryRow extends Record<string, unknown> {
  key: string;
  type: "fact" | "preference" | "context";
  content: string;
  updated: string;
}

const ROWS: MemoryRow[] = [
  { key: "user.name", type: "fact", content: "Anthony Stark", updated: "2d ago" },
  { key: "user.coffee", type: "preference", content: "Espresso, double, no sugar", updated: "5h ago" },
  { key: "lab.dressCode", type: "context", content: "Casual; safety glasses required", updated: "1w ago" },
  { key: "schedule.morning", type: "preference", content: "Briefing at 07:00 sharp", updated: "12h ago" },
  { key: "vehicle.primary", type: "fact", content: "Audi R8 — license STARK1", updated: "3w ago" },
];

const TYPE_VARIANT = {
  fact: "info",
  preference: "success",
  context: "warning",
} as const;

const COLUMNS: Column<MemoryRow>[] = [
  { key: "key", header: "Key", className: "font-mono text-xs text-accent" },
  {
    key: "type",
    header: "Type",
    render: (r) => <JBadge variant={TYPE_VARIANT[r.type]}>{r.type}</JBadge>,
  },
  { key: "content", header: "Content" },
  { key: "updated", header: "Updated", className: "font-mono text-xs text-text-muted" },
];

function MemoryPage() {
  return (
    <Shell>
      <div className="mb-5">
        <h1 className="font-display text-2xl font-semibold tracking-wide text-text-primary">
          Memory Store
        </h1>
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-text-muted">
          long-term · persistent
        </p>
      </div>

      <div className="mb-5 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatTile label="Total entries" value={1284} />
        <StatTile label="Facts" value={612} accentColor="var(--info)" />
        <StatTile label="Preferences" value={188} accentColor="var(--success)" />
        <StatTile label="Embeddings" value="34.2k" accentColor="var(--warning)" />
      </div>

      <Widget title="Recent entries">
        <DataTable columns={COLUMNS} rows={ROWS} />
      </Widget>
    </Shell>
  );
}
