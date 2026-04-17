import { createFileRoute } from "@tanstack/react-router";
import { Wrench } from "lucide-react";
import { Shell } from "@/components/jarvis/Shell";
import { Widget } from "@/components/jarvis/Widget";
import { JBadge } from "@/components/jarvis/Badge";

export const Route = createFileRoute("/tools")({
  head: () => ({
    meta: [
      { title: "Tools — J.A.R.V.I.S. Control Center" },
      { name: "description", content: "External tools and integrations available to the assistant." },
      { property: "og:title", content: "Tools — J.A.R.V.I.S. Control Center" },
      {
        property: "og:description",
        content: "External tools and integrations available to the assistant.",
      },
    ],
  }),
  component: ToolsPage,
});

interface Tool {
  id: string;
  name: string;
  provider: string;
  status: "connected" | "available" | "error";
  calls: number;
  description: string;
}

const TOOLS: Tool[] = [
  { id: "t1", name: "HTTP Fetch", provider: "core", status: "connected", calls: 14_223, description: "Make authenticated HTTP requests to any endpoint." },
  { id: "t2", name: "File System", provider: "core", status: "connected", calls: 8_104, description: "Read, write, and traverse files in the workspace." },
  { id: "t3", name: "Shell Exec", provider: "core", status: "connected", calls: 2_910, description: "Execute shell commands in a sandboxed environment." },
  { id: "t4", name: "GitHub", provider: "integration", status: "connected", calls: 612, description: "Manage repositories, issues, and pull requests." },
  { id: "t5", name: "Slack", provider: "integration", status: "available", calls: 0, description: "Post messages and read channels." },
  { id: "t6", name: "Database", provider: "integration", status: "error", calls: 145, description: "Query and mutate the project database." },
];

const STATUS_VARIANT = {
  connected: "success",
  available: "info",
  error: "error",
} as const;

function ToolsPage() {
  return (
    <Shell>
      <div className="mb-5">
        <h1 className="font-display text-2xl font-semibold tracking-wide text-text-primary">
          Tool Belt
        </h1>
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-text-muted">
          integrations · execution
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {TOOLS.map((t) => (
          <Widget
            key={t.id}
            title={t.name}
            icon={<Wrench className="h-4 w-4 text-accent" />}
            action={<JBadge variant={STATUS_VARIANT[t.status]}>{t.status}</JBadge>}
          >
            <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-text-muted">
              {t.provider}
            </p>
            <p className="mb-3 mt-2 text-sm leading-relaxed text-text-secondary">{t.description}</p>
            <div className="flex items-center justify-between border-t border-border-light pt-2 font-mono text-[11px] uppercase tracking-[0.2em] text-text-muted">
              <span>calls</span>
              <span className="text-text-secondary">{t.calls.toLocaleString()}</span>
            </div>
          </Widget>
        ))}
      </div>
    </Shell>
  );
}
