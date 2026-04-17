import { createFileRoute } from "@tanstack/react-router";
import { Bot } from "lucide-react";
import { Shell } from "@/components/jarvis/Shell";
import { Widget } from "@/components/jarvis/Widget";
import { JBadge } from "@/components/jarvis/Badge";

export const Route = createFileRoute("/agents")({
  head: () => ({
    meta: [
      { title: "Agents — J.A.R.V.I.S. Control Center" },
      { name: "description", content: "Autonomous agents registry and status." },
      { property: "og:title", content: "Agents — J.A.R.V.I.S. Control Center" },
      { property: "og:description", content: "Autonomous agents registry and status." },
    ],
  }),
  component: AgentsPage,
});

interface Agent {
  id: string;
  name: string;
  role: string;
  state: "online" | "idle" | "offline";
  load: number;
}

const AGENTS: Agent[] = [
  { id: "a1", name: "Sentinel", role: "Perimeter watch", state: "online", load: 42 },
  { id: "a2", name: "Archivist", role: "Document indexing", state: "online", load: 18 },
  { id: "a3", name: "Quartermaster", role: "Inventory & logistics", state: "idle", load: 4 },
  { id: "a4", name: "Cartographer", role: "Map & geo data", state: "online", load: 27 },
  { id: "a5", name: "Diplomat", role: "External comms", state: "idle", load: 0 },
  { id: "a6", name: "Forge", role: "Build pipelines", state: "offline", load: 0 },
];

const STATE_VARIANT = {
  online: "success",
  idle: "info",
  offline: "error",
} as const;

function AgentsPage() {
  return (
    <Shell>
      <div className="mb-5">
        <h1 className="font-display text-2xl font-semibold tracking-wide text-text-primary">
          Agent Registry
        </h1>
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-text-muted">
          {AGENTS.filter((a) => a.state === "online").length} online ·{" "}
          {AGENTS.length} total
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {AGENTS.map((a) => (
          <Widget
            key={a.id}
            title={a.name}
            icon={<Bot className="h-4 w-4 text-accent" />}
            action={<JBadge variant={STATE_VARIANT[a.state]}>{a.state}</JBadge>}
          >
            <div className="space-y-3">
              <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-text-muted">
                {a.role}
              </p>
              <div>
                <div className="mb-1 flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.2em] text-text-muted">
                  <span>Load</span>
                  <span className="text-text-secondary">{a.load}%</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-bg-tertiary">
                  <div
                    className="h-full bg-accent shadow-[0_0_8px_var(--accent)]"
                    style={{ width: `${a.load}%` }}
                  />
                </div>
              </div>
              <div className="flex items-center justify-between font-mono text-[11px] text-text-muted">
                <span>id</span>
                <span className="text-text-secondary">{a.id}</span>
              </div>
            </div>
          </Widget>
        ))}
      </div>
    </Shell>
  );
}
