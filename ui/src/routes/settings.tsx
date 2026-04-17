import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Shell } from "@/components/jarvis/Shell";
import { Widget } from "@/components/jarvis/Widget";
import {
  FormGroup,
  JInput,
  JSelect,
  JSwitch,
  JButton,
  JTextarea,
} from "@/components/jarvis/FormGroup";
import { JarvisModal } from "@/components/jarvis/JarvisModal";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings — J.A.R.V.I.S. Control Center" },
      { name: "description", content: "Configure operator profile, voice, and system behavior." },
      { property: "og:title", content: "Settings — J.A.R.V.I.S. Control Center" },
      { property: "og:description", content: "Configure operator profile, voice, and system behavior." },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [autoRespond, setAutoRespond] = useState(false);
  const [telemetry, setTelemetry] = useState(true);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  return (
    <Shell>
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold uppercase tracking-[0.15em] text-text-primary">
          Settings
        </h1>
        <p className="mt-1 font-mono text-xs uppercase tracking-widest text-text-muted">
          Operator preferences & system tuning
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Widget title="Operator Profile">
          <div className="space-y-4">
            <FormGroup label="Display name" htmlFor="name">
              <JInput id="name" defaultValue="T. Stark" />
            </FormGroup>
            <FormGroup label="Clearance level" htmlFor="clearance">
              <JSelect id="clearance" defaultValue="alpha">
                <option value="alpha">Alpha — Full access</option>
                <option value="beta">Beta — Standard</option>
                <option value="gamma">Gamma — Restricted</option>
              </JSelect>
            </FormGroup>
            <FormGroup label="Notes" htmlFor="notes" hint="Visible only to your sessions.">
              <JTextarea id="notes" placeholder="Personal annotations…" />
            </FormGroup>
          </div>
        </Widget>

        <Widget title="Behavior">
          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-md border border-border-light bg-bg-tertiary/50 px-3 py-3">
              <div>
                <p className="font-display text-sm text-text-primary">Voice interface</p>
                <p className="font-mono text-[11px] text-text-muted">Accept spoken commands</p>
              </div>
              <JSwitch checked={voiceEnabled} onCheckedChange={setVoiceEnabled} label="Voice interface" />
            </div>
            <div className="flex items-center justify-between rounded-md border border-border-light bg-bg-tertiary/50 px-3 py-3">
              <div>
                <p className="font-display text-sm text-text-primary">Auto-respond</p>
                <p className="font-mono text-[11px] text-text-muted">Acknowledge all queries automatically</p>
              </div>
              <JSwitch checked={autoRespond} onCheckedChange={setAutoRespond} label="Auto-respond" />
            </div>
            <div className="flex items-center justify-between rounded-md border border-border-light bg-bg-tertiary/50 px-3 py-3">
              <div>
                <p className="font-display text-sm text-text-primary">Telemetry</p>
                <p className="font-mono text-[11px] text-text-muted">Send anonymized diagnostics</p>
              </div>
              <JSwitch checked={telemetry} onCheckedChange={setTelemetry} label="Telemetry" />
            </div>
          </div>
        </Widget>

        <Widget title="Network" className="lg:col-span-2">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormGroup label="Relay endpoint" htmlFor="relay">
              <JInput id="relay" defaultValue="wss://relay.jarvis.local:8443" className="font-mono text-xs" />
            </FormGroup>
            <FormGroup label="Reconnect interval" htmlFor="reconnect">
              <JSelect id="reconnect" defaultValue="2000">
                <option value="1000">1 second</option>
                <option value="2000">2 seconds</option>
                <option value="5000">5 seconds</option>
              </JSelect>
            </FormGroup>
          </div>
          <div className="mt-5 flex flex-wrap gap-2">
            <JButton variant="primary">Save changes</JButton>
            <JButton variant="secondary" onClick={() => setAdvancedOpen(true)}>
              Advanced configuration…
            </JButton>
            <JButton variant="ghost">Reset</JButton>
          </div>
        </Widget>
      </div>

      <JarvisModal
        open={advancedOpen}
        onClose={() => setAdvancedOpen(false)}
        title="Advanced Configuration"
        description="Modify low-level orbital parameters. Changes apply immediately."
        footer={
          <>
            <JButton variant="ghost" onClick={() => setAdvancedOpen(false)}>
              Cancel
            </JButton>
            <JButton variant="primary" onClick={() => setAdvancedOpen(false)}>
              Apply
            </JButton>
          </>
        }
      >
        <div className="space-y-4">
          <FormGroup label="Inference precision" htmlFor="prec">
            <JSelect id="prec" defaultValue="fp16">
              <option value="fp32">FP32 — Maximum</option>
              <option value="fp16">FP16 — Balanced</option>
              <option value="int8">INT8 — Performance</option>
            </JSelect>
          </FormGroup>
          <FormGroup label="Heartbeat interval (ms)" htmlFor="hb">
            <JInput id="hb" type="number" defaultValue={2000} />
          </FormGroup>
          <FormGroup label="Debug verbosity" htmlFor="verb">
            <JSelect id="verb" defaultValue="info">
              <option value="error">Error only</option>
              <option value="warn">Warnings</option>
              <option value="info">Info</option>
              <option value="debug">Debug — Verbose</option>
            </JSelect>
          </FormGroup>
        </div>
      </JarvisModal>
    </Shell>
  );
}
