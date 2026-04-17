import { createFileRoute } from "@tanstack/react-router";
import { Activity, Cpu, MemoryStick, Network, Radio, Zap } from "lucide-react";
import { Shell } from "@/components/jarvis/Shell";
import { Widget } from "@/components/jarvis/Widget";
import { StatTile } from "@/components/jarvis/StatTile";
import { JBadge } from "@/components/jarvis/Badge";
import { OrbIndicator } from "@/components/jarvis/OrbIndicator";
import { useJarvisSocket } from "@/hooks/useJarvisSocket";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard — J.A.R.V.I.S. Control Center" },
      { name: "description", content: "Live orbital telemetry and system status overview." },
      { property: "og:title", content: "Dashboard — J.A.R.V.I.S. Control Center" },
      { property: "og:description", content: "Live orbital telemetry and system status overview." },
    ],
  }),
  component: DashboardPage,
});

const ACTIVITY = [
  { time: "14:02:18", event: "Voice command processed", level: "info" as const },
  { time: "14:01:55", event: "Perimeter scan complete", level: "success" as const },
  { time: "14:01:32", event: "Memory bank optimized", level: "success" as const },
  { time: "14:00:48", event: "Anomaly detected — sector 7G", level: "warning" as const },
  { time: "14:00:11", event: "Network handshake established", level: "info" as const },
  { time: "13:59:42", event: "Diagnostics passed", level: "success" as const },
];

const VITALS = [
  { label: "CPU", value: 42, color: "var(--accent)" },
  { label: "GPU", value: 67, color: "var(--info)" },
  { label: "Memory", value: 58, color: "var(--success)" },
  { label: "Disk I/O", value: 23, color: "var(--warning)" },
  { label: "Network", value: 81, color: "var(--accent-hover)" },
];

function DashboardPage() {
  const { orbState } = useJarvisSocket();

  return (
    <Shell>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold uppercase tracking-[0.15em] text-text-primary">
            Dashboard
          </h1>
          <p className="mt-1 font-mono text-xs uppercase tracking-widest text-text-muted">
            Real-time orbital telemetry
          </p>
        </div>
        <div className="flex items-center gap-3 rounded-md border border-border-light bg-bg-secondary px-3 py-2">
          <OrbIndicator state={orbState} size="md" showLabel />
        </div>
      </div>

      {/* Stat grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="System Status"
          value="Nominal"
          accentColor="var(--success)"
          icon={<Zap className="h-4 w-4" />}
          delta={{ value: "Stable 14h", trend: "flat" }}
        />
        <StatTile
          label="Active Processes"
          value={1284}
          delta={{ value: "+ 12 since 13:00", trend: "up" }}
          icon={<Cpu className="h-4 w-4" />}
        />
        <StatTile
          label="Memory Load"
          value="58"
          unit="%"
          delta={{ value: "− 4% / 1h", trend: "down" }}
          icon={<MemoryStick className="h-4 w-4" />}
        />
        <StatTile
          label="Network"
          value="912"
          unit="Mb/s"
          delta={{ value: "+ 88 Mb/s", trend: "up" }}
          icon={<Network className="h-4 w-4" />}
        />
      </div>

      {/* Vitals + Activity */}
      <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Widget
          title="System Vitals"
          icon={<Activity className="h-4 w-4" />}
          className="lg:col-span-2"
        >
          <div className="space-y-4">
            {VITALS.map((v) => (
              <div key={v.label}>
                <div className="mb-1.5 flex items-baseline justify-between">
                  <span className="font-mono text-xs uppercase tracking-widest text-text-secondary">
                    {v.label}
                  </span>
                  <span
                    className="font-display text-sm font-semibold tabular-nums"
                    style={{ color: v.color }}
                  >
                    {v.value}%
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-sm bg-bg-tertiary">
                  <div
                    className="h-full rounded-sm transition-all duration-700"
                    style={{
                      width: `${v.value}%`,
                      backgroundColor: v.color,
                      boxShadow: `0 0 12px ${v.color}`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Widget>

        <Widget title="Activity Feed" icon={<Radio className="h-4 w-4" />}>
          <ul className="space-y-2.5">
            {ACTIVITY.map((a, i) => (
              <li
                key={i}
                className="flex items-start gap-3 rounded-md border border-border-light bg-bg-tertiary/40 p-2.5"
              >
                <span className="mt-1 font-mono text-[10px] text-text-muted">{a.time}</span>
                <span className="flex-1 text-xs text-text-secondary">{a.event}</span>
                <JBadge variant={a.level}>{a.level}</JBadge>
              </li>
            ))}
          </ul>
        </Widget>
      </div>
    </Shell>
  );
}
