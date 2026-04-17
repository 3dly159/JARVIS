import { useState } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { ScanLine } from "./ScanLine";
import { useJarvisSocket } from "@/hooks/useJarvisSocket";

interface ShellProps {
  children: React.ReactNode;
}

export function Shell({ children }: ShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { orbState, connected } = useJarvisSocket();

  return (
    <div className="min-h-screen bg-bg-primary">
      <ScanLine />
      <Header
        orbState={orbState}
        connected={connected}
        onToggleSidebar={() => setSidebarOpen((o) => !o)}
      />
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <main className="lg:pl-[260px] xl:pl-[300px]">
        <div className="mx-auto w-full max-w-[1800px] px-4 py-5 sm:px-6 sm:py-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
}
