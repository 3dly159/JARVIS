import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard,
  Cpu,
  ScrollText,
  SlidersHorizontal,
  Sparkles,
  MessageSquare,
  ListChecks,
  Bot,
  Brain,
  Zap,
  Users,
  Wrench,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  to:
    | "/"
    | "/chat"
    | "/tasks"
    | "/agents"
    | "/memory"
    | "/skills"
    | "/sessions"
    | "/tools"
    | "/system"
    | "/logs"
    | "/settings"
    | "/design-preview";
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV: NavItem[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/tasks", label: "Tasks", icon: ListChecks },
  { to: "/agents", label: "Agents", icon: Bot },
  { to: "/memory", label: "Memory", icon: Brain },
  { to: "/skills", label: "Skills", icon: Zap },
  { to: "/sessions", label: "Sessions", icon: Users },
  { to: "/tools", label: "Tools", icon: Wrench },
  { to: "/system", label: "System", icon: Cpu },
  { to: "/logs", label: "Logs", icon: ScrollText },
  { to: "/settings", label: "Settings", icon: SlidersHorizontal },
  { to: "/design-preview", label: "Design Preview", icon: Sparkles },
];

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden animate-fade-in"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        role="navigation"
        aria-label="Main navigation"
        className={cn(
          "fixed left-0 top-14 z-40 h-[calc(100vh-3.5rem)] border-r border-border bg-bg-secondary transition-transform duration-250",
          "w-[260px] xl:w-[300px]",
          "lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-full flex-col">
          <div className="border-b border-border-light px-5 py-3">
            <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-text-muted">
              Navigation
            </p>
          </div>

          <nav className="flex-1 overflow-y-auto p-3">
            <ul className="space-y-1">
              {NAV.map((item) => {
                const Icon = item.icon;
                const isActive =
                  item.to === "/" ? pathname === "/" : pathname.startsWith(item.to);
                return (
                  <li key={item.to}>
                    <Link
                      to={item.to}
                      onClick={onClose}
                      aria-current={isActive ? "page" : undefined}
                      className={cn(
                        "group relative flex items-center gap-3 rounded-md px-3 py-2.5 font-display text-[15px] font-medium transition-all",
                        "text-text-secondary hover:bg-bg-hover hover:text-text-primary",
                        isActive && "bg-bg-active text-text-primary",
                      )}
                    >
                      {isActive && (
                        <span
                          aria-hidden="true"
                          className="absolute right-0 top-1/2 h-6 w-[3px] -translate-y-1/2 rounded-l-sm bg-accent shadow-[0_0_10px_var(--accent)]"
                        />
                      )}
                      <Icon
                        className={cn(
                          "h-[18px] w-[18px] shrink-0 transition-colors",
                          isActive ? "text-accent" : "text-text-muted group-hover:text-accent",
                        )}
                      />
                      <span className="tracking-wide">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          <div className="border-t border-border-light px-5 py-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
                Build
              </span>
              <span className="font-mono text-[10px] text-text-secondary">v1.0.0</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
