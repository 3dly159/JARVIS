import { createFileRoute } from "@tanstack/react-router";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Shell } from "@/components/jarvis/Shell";
import { Widget } from "@/components/jarvis/Widget";
import { DataTable, type Column } from "@/components/jarvis/DataTable";
import { JBadge } from "@/components/jarvis/Badge";
import { JInput } from "@/components/jarvis/FormGroup";

export const Route = createFileRoute("/logs")({
  head: () => ({
    meta: [
      { title: "Logs — J.A.R.V.I.S. Control Center" },
      { name: "description", content: "Real-time event log stream with severity filtering." },
      { property: "og:title", content: "Logs — J.A.R.V.I.S. Control Center" },
      { property: "og:description", content: "Real-time event log stream with severity filtering." },
    ],
  }),
  component: LogsPage,
});

type Level = "info" | "success" | "warning" | "error";

interface LogRow extends Record<string, unknown> {
  ts: string;
  level: Level;
  source: string;
  message: string;
}

const LOGS: LogRow[] = [
  { ts: "14:03:22.481", level: "info", source: "core", message: "Voice intent classifier loaded model v2.3.1" },
  { ts: "14:03:18.044", level: "success", source: "scan", message: "Perimeter sweep complete — 0 anomalies" },
  { ts: "14:03:11.902", level: "warning", source: "thermal", message: "Core 4 temperature exceeds 80°C" },
  { ts: "14:03:05.317", level: "info", source: "net", message: "Handshake with relay-7 successful" },
  { ts: "14:02:58.220", level: "error", source: "auth", message: "Failed authentication attempt from 10.0.4.18" },
  { ts: "14:02:51.118", level: "success", source: "memory", message: "Garbage collection freed 1.2 GB" },
  { ts: "14:02:44.005", level: "info", source: "voice", message: "User session opened — operator: T. Stark" },
  { ts: "14:02:38.812", level: "warning", source: "disk", message: "/archive at 82% capacity" },
  { ts: "14:02:30.444", level: "info", source: "core", message: "Heartbeat OK — uptime 14h 22m" },
  { ts: "14:02:22.071", level: "success", source: "ai", message: "Inference batch processed — 1024 tokens" },
  { ts: "14:02:15.918", level: "info", source: "ui", message: "Widget refresh cycle 0x9F2A" },
  { ts: "14:02:09.330", level: "error", source: "net", message: "Packet drop detected — interface eth0" },
];

const cols: Column<LogRow>[] = [
  { key: "ts", header: "Timestamp", className: "font-mono text-xs text-text-muted whitespace-nowrap" },
  {
    key: "level",
    header: "Level",
    render: (r) => <JBadge variant={r.level}>{r.level}</JBadge>,
  },
  { key: "source", header: "Source", className: "font-mono text-xs text-accent" },
  { key: "message", header: "Message", className: "text-text-secondary" },
];

function LogsPage() {
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState<Level | "all">("all");

  const filtered = useMemo(
    () =>
      LOGS.filter(
        (l) =>
          (level === "all" || l.level === level) &&
          (query === "" ||
            l.message.toLowerCase().includes(query.toLowerCase()) ||
            l.source.toLowerCase().includes(query.toLowerCase())),
      ),
    [query, level],
  );

  const levels: (Level | "all")[] = ["all", "info", "success", "warning", "error"];

  return (
    <Shell>
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold uppercase tracking-[0.15em] text-text-primary">
          Event Log
        </h1>
        <p className="mt-1 font-mono text-xs uppercase tracking-widest text-text-muted">
          Live system event stream
        </p>
      </div>

      <Widget>
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
            <JInput
              type="search"
              placeholder="Search messages or sources…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-9"
              aria-label="Search logs"
            />
          </div>
          <div className="flex gap-1">
            {levels.map((l) => (
              <button
                key={l}
                type="button"
                onClick={() => setLevel(l)}
                className={`rounded-md border px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest transition-colors ${
                  level === l
                    ? "border-accent bg-accent/15 text-accent"
                    : "border-border bg-bg-tertiary text-text-muted hover:border-border-dark hover:text-text-secondary"
                }`}
              >
                {l}
              </button>
            ))}
          </div>
        </div>

        <div className="max-h-[60vh] overflow-y-auto">
          <DataTable columns={cols} rows={filtered} empty="No matching log entries." />
        </div>
        <div className="mt-3 flex items-center justify-between font-mono text-[10px] uppercase tracking-widest text-text-muted">
          <span>{filtered.length} entries</span>
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-success" />
            Live
          </span>
        </div>
      </Widget>
    </Shell>
  );
}
