import { createFileRoute } from "@tanstack/react-router";
import { Cpu, HardDrive, MemoryStick } from "lucide-react";
import { Shell } from "@/components/jarvis/Shell";
import { Widget } from "@/components/jarvis/Widget";
import { DataTable, type Column } from "@/components/jarvis/DataTable";
import { JBadge } from "@/components/jarvis/Badge";

export const Route = createFileRoute("/system")({
  head: () => ({
    meta: [
      { title: "System — J.A.R.V.I.S. Control Center" },
      { name: "description", content: "Hardware inventory, processes, and resource utilization." },
      { property: "og:title", content: "System — J.A.R.V.I.S. Control Center" },
      { property: "og:description", content: "Hardware inventory, processes, and resource utilization." },
    ],
  }),
  component: SystemPage,
});

interface CpuRow extends Record<string, unknown> {
  core: string;
  load: string;
  temp: string;
  status: "success" | "warning" | "error";
}

interface DiskRow extends Record<string, unknown> {
  mount: string;
  used: string;
  total: string;
  pct: number;
}

interface ProcRow extends Record<string, unknown> {
  pid: number;
  name: string;
  cpu: string;
  mem: string;
  state: "info" | "success" | "warning";
}

const CPU_ROWS: CpuRow[] = [
  { core: "Core 00", load: "38%", temp: "52°C", status: "success" },
  { core: "Core 01", load: "44%", temp: "55°C", status: "success" },
  { core: "Core 02", load: "78%", temp: "71°C", status: "warning" },
  { core: "Core 03", load: "21%", temp: "48°C", status: "success" },
  { core: "Core 04", load: "92%", temp: "84°C", status: "error" },
  { core: "Core 05", load: "33%", temp: "51°C", status: "success" },
];

const DISK_ROWS: DiskRow[] = [
  { mount: "/", used: "284 GB", total: "1 TB", pct: 28 },
  { mount: "/data", used: "1.4 TB", total: "4 TB", pct: 35 },
  { mount: "/archive", used: "8.2 TB", total: "10 TB", pct: 82 },
];

const PROC_ROWS: ProcRow[] = [
  { pid: 1024, name: "jarvis-core", cpu: "12.4%", mem: "1.2 GB", state: "success" },
  { pid: 1881, name: "voice-pipeline", cpu: "8.1%", mem: "640 MB", state: "info" },
  { pid: 2042, name: "perimeter-scan", cpu: "4.7%", mem: "320 MB", state: "info" },
  { pid: 2210, name: "memory-banks", cpu: "2.3%", mem: "2.1 GB", state: "success" },
  { pid: 2384, name: "neural-cache", cpu: "21.0%", mem: "4.8 GB", state: "warning" },
];

const cpuCols: Column<CpuRow>[] = [
  { key: "core", header: "Core", className: "font-mono" },
  { key: "load", header: "Load", align: "right" },
  { key: "temp", header: "Temp", align: "right" },
  {
    key: "status",
    header: "Status",
    align: "right",
    render: (r) => (
      <JBadge variant={r.status}>
        {r.status === "success" ? "OK" : r.status === "warning" ? "WARN" : "CRIT"}
      </JBadge>
    ),
  },
];

const procCols: Column<ProcRow>[] = [
  { key: "pid", header: "PID", className: "font-mono text-text-muted" },
  { key: "name", header: "Process", className: "font-mono text-text-primary" },
  { key: "cpu", header: "CPU", align: "right" },
  { key: "mem", header: "Memory", align: "right" },
  {
    key: "state",
    header: "State",
    align: "right",
    render: (r) => <JBadge variant={r.state}>{r.state}</JBadge>,
  },
];

function SystemPage() {
  return (
    <Shell>
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold uppercase tracking-[0.15em] text-text-primary">
          System
        </h1>
        <p className="mt-1 font-mono text-xs uppercase tracking-widest text-text-muted">
          Hardware inventory & resource map
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Widget title="CPU Cores" icon={<Cpu className="h-4 w-4" />}>
          <DataTable columns={cpuCols} rows={CPU_ROWS} />
        </Widget>

        <Widget title="Disks" icon={<HardDrive className="h-4 w-4" />}>
          <div className="space-y-4">
            {DISK_ROWS.map((d) => (
              <div key={d.mount}>
                <div className="mb-1.5 flex items-baseline justify-between">
                  <span className="font-mono text-sm text-text-primary">{d.mount}</span>
                  <span className="font-mono text-xs text-text-muted">
                    {d.used} / {d.total}
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-sm bg-bg-tertiary">
                  <div
                    className="h-full"
                    style={{
                      width: `${d.pct}%`,
                      backgroundColor:
                        d.pct > 80 ? "var(--warning)" : "var(--accent)",
                      boxShadow: `0 0 8px ${d.pct > 80 ? "var(--warning)" : "var(--accent)"}`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Widget>

        <Widget title="Memory Allocation" icon={<MemoryStick className="h-4 w-4" />} className="lg:col-span-2">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-md border border-border-light bg-bg-tertiary/50 p-4">
              <p className="font-mono text-[10px] uppercase tracking-widest text-text-muted">Used</p>
              <p className="mt-1 font-display text-2xl text-text-primary tabular-nums">37.2 <span className="text-sm text-text-muted">GB</span></p>
            </div>
            <div className="rounded-md border border-border-light bg-bg-tertiary/50 p-4">
              <p className="font-mono text-[10px] uppercase tracking-widest text-text-muted">Cached</p>
              <p className="mt-1 font-display text-2xl text-text-primary tabular-nums">12.8 <span className="text-sm text-text-muted">GB</span></p>
            </div>
            <div className="rounded-md border border-border-light bg-bg-tertiary/50 p-4">
              <p className="font-mono text-[10px] uppercase tracking-widest text-text-muted">Free</p>
              <p className="mt-1 font-display text-2xl text-success tabular-nums">14.0 <span className="text-sm text-text-muted">GB</span></p>
            </div>
          </div>
        </Widget>

        <Widget title="Active Processes" className="lg:col-span-2">
          <DataTable columns={procCols} rows={PROC_ROWS} />
        </Widget>
      </div>
    </Shell>
  );
}
