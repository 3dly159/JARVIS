import { useEffect, useRef, useState } from "react";
import type { OrbState } from "./useOrbState";

interface JarvisMessage {
  type: "state";
  orbState: OrbState;
}

const ORB_CYCLE: OrbState[] = ["idle", "listening", "thinking", "speaking", "idle"];

/**
 * Connects to the JARVIS WebSocket endpoint when VITE_JARVIS_WS_URL is set.
 * Otherwise cycles through mock orb states so the preview stays alive.
 *
 * To wire a real endpoint, set VITE_JARVIS_WS_URL in your environment — the
 * single line below will pick it up.
 */
export function useJarvisSocket() {
  const [orbState, setOrbState] = useState<OrbState>("idle");
  const [connected, setConnected] = useState(false);
  const [manualOverride, setManualOverride] = useState<OrbState | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Read the optional WS URL from Vite env. Empty / undefined → mock mode.
  const wsUrl = (import.meta.env.VITE_JARVIS_WS_URL as string | undefined) ?? "";

  useEffect(() => {
    if (manualOverride) {
      setOrbState(manualOverride);
      return;
    }

    if (!wsUrl) {
      // Mock mode: cycle through states every 3.5s
      let i = 0;
      const interval = setInterval(() => {
        i = (i + 1) % ORB_CYCLE.length;
        setOrbState(ORB_CYCLE[i]);
      }, 3500);
      return () => clearInterval(interval);
    }

    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;
        ws.onopen = () => setConnected(true);
        ws.onclose = () => {
          setConnected(false);
          reconnectTimer = setTimeout(connect, 2000);
        };
        ws.onerror = () => setOrbState("error");
        ws.onmessage = (e) => {
          try {
            const msg = JSON.parse(e.data) as JarvisMessage;
            if (msg.type === "state" && msg.orbState) {
              setOrbState(msg.orbState);
            }
          } catch {
            /* ignore malformed */
          }
        };
      } catch {
        setOrbState("error");
      }
    };

    connect();

    return () => {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, [wsUrl, manualOverride]);

  return {
    orbState,
    connected: wsUrl ? connected : true,
    isMock: !wsUrl,
    setManualOverride,
  };
}
