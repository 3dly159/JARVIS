import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Cpu, AlertTriangle } from "lucide-react";
import { Shell } from "@/components/jarvis/Shell";
import { Widget } from "@/components/jarvis/Widget";
import { StatTile } from "@/components/jarvis/StatTile";
import { JBadge } from "@/components/jarvis/Badge";
import { OrbIndicator } from "@/components/jarvis/OrbIndicator";
import { LoadingSpinner } from "@/components/jarvis/LoadingSpinner";
import { IconButton } from "@/components/jarvis/IconButton";
import { JarvisModal } from "@/components/jarvis/JarvisModal";
import {
  FormGroup,
  JInput,
  JSelect,
  JSwitch,
  JButton,
} from "@/components/jarvis/FormGroup";
import { DataTable, type Column } from "@/components/jarvis/DataTable";
import { useJarvisSocket } from "@/hooks/useJarvisSocket";
import type { OrbState } from "@/hooks/useOrbState";

export const Route = createFileRoute("/design-preview")({
  head: () => ({
    meta: [
      { title: "Design Preview — J.A.R.V.I.S. Control Center" },
      { name: "description", content: "Component gallery showcasing every JARVIS UI primitive in isolation." },
      { property: "og:title", content: "Design Preview — J.A.R.V.I.S. Control Center" },
      { property: "og:description", content: "Component gallery showcasing every JARVIS UI primitive in isolation." },
    ],
  }),
  component: DesignPreview,
});

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-8">
      <div className="mb-3 flex items-center gap-2">
        <span className="h-px flex-1 bg-border-light" />
        <h2 className="font-mono text-[10px] uppercase tracking-[0.3em] text-text-muted">{title}</h2>
        <span className="h-px flex-1 bg-border-light" />
      </div>
      <div className="rounded-lg border border-border bg-bg-secondary/40 p-4">{children}</div>
    </section>
  );
}

interface SampleRow extends Record<string, unknown> {
  id: string;
  name: string;
  load: string;
  status: "success" | "warning" | "error";
}

const SAMPLE: SampleRow[] = [
  { id: "0x01", name: "core", load: "12%", status: "success" },
  { id: "0x02", name: "voice", load: "8%", status: "success" },
  { id: "0x03", name: "scan", load: "47%", status: "warning" },
  { id: "0x04", name: "auth", load: "92%", status: "error" },
];

const cols: Column<SampleRow>[] = [
  { key: "id", header: "ID", className: "font-mono text-text-muted" },
  { key: "name", header: "Name", className: "font-mono text-text-primary" },
  { key: "load", header: "Load", align: "right" },
  {
    key: "status",
    header: "Status",
    align: "right",
    render: (r) => <JBadge variant={r.status}>{r.status}</JBadge>,
  },
];

function DesignPreview() {
  const [modal, setModal] = useState(false);
  const [sw, setSw] = useState(true);
  const { orbState, setManualOverride, isMock } = useJarvisSocket();

  const orbStates: OrbState[] = ["idle", "listening", "speaking", "thinking", "error"];

  return (
    <Shell>
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold uppercase tracking-[0.15em] text-text-primary">
          Design Preview
        </h1>
        <p className="mt-1 font-mono text-xs uppercase tracking-widest text-text-muted">
          Storybook-style component gallery
        </p>
      </div>

      <Section title="Orb Indicator — All States">
        <div className="flex flex-wrap items-center gap-6">
          {orbStates.map((s) => (
            <div key={s} className="flex flex-col items-center gap-2">
              <OrbIndicator state={s} size="lg" />
              <span className="font-mono text-[10px] uppercase tracking-widest text-text-muted">{s}</span>
            </div>
          ))}
        </div>
        <div className="mt-5 flex flex-wrap items-center gap-2 border-t border-border-light pt-4">
          <span className="font-mono text-[10px] uppercase tracking-widest text-text-muted mr-2">
            Live override {isMock && "(mock)"}:
          </span>
          {orbStates.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setManualOverride(s)}
              className={`rounded-md border px-3 py-1 font-mono text-[10px] uppercase tracking-widest transition-colors ${
                orbState === s
                  ? "border-accent bg-accent/15 text-accent"
                  : "border-border bg-bg-tertiary text-text-muted hover:border-border-dark hover:text-text-secondary"
              }`}
            >
              {s}
            </button>
          ))}
          <button
            type="button"
            onClick={() => setManualOverride(null)}
            className="rounded-md border border-border bg-bg-tertiary px-3 py-1 font-mono text-[10px] uppercase tracking-widest text-text-secondary hover:border-border-dark"
          >
            auto
          </button>
        </div>
      </Section>

      <Section title="Stat Tiles">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatTile label="System" value="Nominal" accentColor="var(--success)" />
          <StatTile label="Processes" value={1284} delta={{ value: "+12", trend: "up" }} icon={<Cpu className="h-4 w-4" />} />
          <StatTile label="Memory" value={58} unit="%" delta={{ value: "−4%", trend: "down" }} />
          <StatTile label="Faults" value={3} accentColor="var(--warning)" delta={{ value: "stable", trend: "flat" }} icon={<AlertTriangle className="h-4 w-4" />} />
        </div>
      </Section>

      <Section title="Badges">
        <div className="flex flex-wrap gap-2">
          <JBadge variant="success">success</JBadge>
          <JBadge variant="warning">warning</JBadge>
          <JBadge variant="error">error</JBadge>
          <JBadge variant="info">info</JBadge>
          <JBadge variant="neutral">neutral</JBadge>
        </div>
      </Section>

      <Section title="Buttons">
        <div className="flex flex-wrap gap-3">
          <JButton variant="primary">Primary</JButton>
          <JButton variant="secondary">Secondary</JButton>
          <JButton variant="ghost">Ghost</JButton>
          <JButton variant="danger">Danger</JButton>
          <JButton variant="primary" disabled>Disabled</JButton>
          <JButton variant="primary" size="sm">Small</JButton>
        </div>
      </Section>

      <Section title="Form Controls">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormGroup label="Text input" htmlFor="dp-text">
            <JInput id="dp-text" placeholder="Enter callsign…" />
          </FormGroup>
          <FormGroup label="Select" htmlFor="dp-sel">
            <JSelect id="dp-sel">
              <option>Option Alpha</option>
              <option>Option Beta</option>
            </JSelect>
          </FormGroup>
          <div className="flex items-center justify-between rounded-md border border-border-light bg-bg-tertiary/50 px-3 py-3">
            <span className="font-display text-sm text-text-primary">Switch</span>
            <JSwitch checked={sw} onCheckedChange={setSw} label="Demo switch" />
          </div>
          <div className="flex items-center gap-2">
            <LoadingSpinner size={20} />
            <span className="font-mono text-xs text-text-muted">LoadingSpinner</span>
          </div>
        </div>
      </Section>

      <Section title="Widget & Table">
        <Widget title="Sample Widget" icon={<Cpu className="h-4 w-4" />}>
          <DataTable columns={cols} rows={SAMPLE} />
        </Widget>
      </Section>

      <Section title="Icon Buttons">
        <div className="flex gap-2">
          <IconButton label="Action 1"><Cpu className="h-4 w-4" /></IconButton>
          <IconButton label="Action 2" variant="outlined"><AlertTriangle className="h-4 w-4" /></IconButton>
        </div>
      </Section>

      <Section title="Modal">
        <JButton variant="primary" onClick={() => setModal(true)}>Open modal</JButton>
        <JarvisModal
          open={modal}
          onClose={() => setModal(false)}
          title="Confirm Action"
          description="This action cannot be undone."
          footer={
            <>
              <JButton variant="ghost" onClick={() => setModal(false)}>Cancel</JButton>
              <JButton variant="primary" onClick={() => setModal(false)}>Confirm</JButton>
            </>
          }
        >
          <p className="text-sm text-text-secondary">
            Are you certain you want to proceed? J.A.R.V.I.S. will execute the requested
            sequence and update orbital telemetry accordingly.
          </p>
        </JarvisModal>
      </Section>
    </Shell>
  );
}
