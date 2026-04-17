import { Maximize2, Minimize2, Settings, Menu } from "lucide-react";
import { useEffect, useState } from "react";
import { OrbIndicator } from "./OrbIndicator";
import { IconButton } from "./IconButton";
import { ORB_LABELS, type OrbState } from "@/hooks/useOrbState";

interface HeaderProps {
  orbState: OrbState;
  onToggleSidebar: () => void;
  connected: boolean;
}

export function Header({ orbState, onToggleSidebar, connected }: HeaderProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  const toggleFullscreen = () => {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      document.documentElement.requestFullscreen().catch(() => {});
    }
  };

  return (
    <header
      role="banner"
      className="sticky top-0 z-50 flex h-14 items-center gap-3 border-b border-border bg-bg-secondary/95 px-3 backdrop-blur-sm sm:px-5"
      style={{ boxShadow: "0 1px 0 var(--border-light), 0 4px 24px oklch(0 0 0 / 0.4)" }}
    >
      <IconButton label="Toggle navigation" onClick={onToggleSidebar} className="lg:hidden">
        <Menu className="h-5 w-5" />
      </IconButton>

      {/* Logo glyph */}
      <div className="flex items-center gap-2.5">
        <div className="relative h-7 w-7">
          <div className="absolute inset-0 rounded-full border border-accent/60" />
          <div className="absolute inset-1 rounded-full border border-accent/40" />
          <div className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent shadow-[0_0_8px_var(--accent)]" />
        </div>
        <div className="flex flex-col leading-none">
          <span className="font-display text-sm font-semibold uppercase tracking-[0.2em] text-text-primary">
            J.A.R.V.I.S.
          </span>
          <span className="hidden font-mono text-[10px] uppercase tracking-widest text-text-muted sm:inline">
            Control Center
          </span>
        </div>
      </div>

      <div className="flex-1" />

      {/* Orb status + connection pill */}
      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-2 rounded-md border border-border-light bg-bg-tertiary/60 px-3 py-1.5 sm:flex">
          <OrbIndicator state={orbState} size="md" />
          <span className="font-mono text-xs uppercase tracking-wider text-text-secondary">
            {ORB_LABELS[orbState]}
          </span>
        </div>
        <div className="hidden items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest text-text-muted md:flex">
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: connected ? "var(--success)" : "var(--text-muted)" }}
          />
          {connected ? "Online" : "Offline"}
        </div>

        <IconButton label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"} onClick={toggleFullscreen}>
          {isFullscreen ? <Minimize2 className="h-4.5 w-4.5" /> : <Maximize2 className="h-4.5 w-4.5" />}
        </IconButton>
        <IconButton label="Settings">
          <Settings className="h-4.5 w-4.5" />
        </IconButton>
      </div>
    </header>
  );
}
