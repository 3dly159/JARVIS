import { createFileRoute } from "@tanstack/react-router";
import { Sparkles } from "lucide-react";
import { Shell } from "@/components/jarvis/Shell";
import { Widget } from "@/components/jarvis/Widget";
import { JBadge } from "@/components/jarvis/Badge";

export const Route = createFileRoute("/skills")({
  head: () => ({
    meta: [
      { title: "Skills — J.A.R.V.I.S. Control Center" },
      { name: "description", content: "Installed capabilities and skill modules." },
      { property: "og:title", content: "Skills — J.A.R.V.I.S. Control Center" },
      { property: "og:description", content: "Installed capabilities and skill modules." },
    ],
  }),
  component: SkillsPage,
});

interface Skill {
  id: string;
  name: string;
  category: string;
  version: string;
  enabled: boolean;
  description: string;
}

const SKILLS: Skill[] = [
  { id: "s1", name: "Code Synthesis", category: "Engineering", version: "2.4.1", enabled: true, description: "Generate, refactor, and review source code across languages." },
  { id: "s2", name: "Image Vision", category: "Perception", version: "1.8.0", enabled: true, description: "Analyze images, OCR, and recognize objects." },
  { id: "s3", name: "Calendar Sync", category: "Productivity", version: "0.9.3", enabled: true, description: "Read and modify calendar events across providers." },
  { id: "s4", name: "Voice Synthesis", category: "Audio", version: "3.1.0", enabled: false, description: "High-fidelity text-to-speech with emotional inflection." },
  { id: "s5", name: "Web Recon", category: "Research", version: "2.0.5", enabled: true, description: "Search, browse, and extract content from the open web." },
  { id: "s6", name: "Workshop Control", category: "Hardware", version: "1.2.0", enabled: false, description: "Interface with fabrication equipment and CNC tools." },
];

function SkillsPage() {
  return (
    <Shell>
      <div className="mb-5">
        <h1 className="font-display text-2xl font-semibold tracking-wide text-text-primary">
          Skill Library
        </h1>
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-text-muted">
          {SKILLS.filter((s) => s.enabled).length} enabled · {SKILLS.length} installed
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {SKILLS.map((s) => (
          <Widget
            key={s.id}
            title={s.name}
            icon={<Sparkles className="h-4 w-4 text-accent" />}
            action={
              <JBadge variant={s.enabled ? "success" : "info"}>
                {s.enabled ? "enabled" : "disabled"}
              </JBadge>
            }
          >
            <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-text-muted">
              {s.category} · v{s.version}
            </p>
            <p className="mt-2 text-sm leading-relaxed text-text-secondary">{s.description}</p>
          </Widget>
        ))}
      </div>
    </Shell>
  );
}
