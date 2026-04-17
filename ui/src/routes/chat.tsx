import { createFileRoute } from "@tanstack/react-router";
import { useRef, useState } from "react";
import { Send } from "lucide-react";
import { Shell } from "@/components/jarvis/Shell";
import { Widget } from "@/components/jarvis/Widget";
import { JBadge } from "@/components/jarvis/Badge";
import { JButton, JInput } from "@/components/jarvis/FormGroup";

export const Route = createFileRoute("/chat")({
  head: () => ({
    meta: [
      { title: "Chat — J.A.R.V.I.S. Control Center" },
      { name: "description", content: "Conversational interface with the J.A.R.V.I.S. assistant." },
      { property: "og:title", content: "Chat — J.A.R.V.I.S. Control Center" },
      {
        property: "og:description",
        content: "Conversational interface with the J.A.R.V.I.S. assistant.",
      },
    ],
  }),
  component: ChatPage,
});

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  ts: string;
}

const SEED: Message[] = [
  {
    id: "m1",
    role: "assistant",
    content: "Good evening. All systems are nominal. How may I assist you?",
    ts: "20:14:02",
  },
  {
    id: "m2",
    role: "user",
    content: "Run a diagnostic on the network interface.",
    ts: "20:14:31",
  },
  {
    id: "m3",
    role: "assistant",
    content:
      "Diagnostic complete. Interface eth0 reports 0% packet loss across 1,000 probes. Latency is averaging 12ms.",
    ts: "20:14:34",
  },
];

function ChatPage() {
  const [messages, setMessages] = useState<Message[]>(SEED);
  const [input, setInput] = useState("");
  const idRef = useRef(SEED.length);

  const send = (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    idRef.current += 1;
    const ts = new Date().toLocaleTimeString("en-GB", { hour12: false });
    const userMsg: Message = { id: `m${idRef.current}`, role: "user", content: text, ts };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setTimeout(() => {
      idRef.current += 1;
      setMessages((prev) => [
        ...prev,
        {
          id: `m${idRef.current}`,
          role: "assistant",
          content: "Acknowledged. Processing your request.",
          ts: new Date().toLocaleTimeString("en-GB", { hour12: false }),
        },
      ]);
    }, 600);
  };

  return (
    <Shell>
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-wide text-text-primary">
            Conversation Channel
          </h1>
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-text-muted">
            secure · end-to-end encrypted
          </p>
        </div>
        <JBadge variant="success">online</JBadge>
      </div>

      <Widget title="J.A.R.V.I.S. — active session">
        <div className="flex h-[60vh] flex-col">
          <div className="flex-1 space-y-4 overflow-y-auto pr-2">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[75%] rounded-md border px-3 py-2 ${
                    m.role === "user"
                      ? "border-accent/40 bg-accent/10 text-text-primary"
                      : "border-border bg-bg-tertiary text-text-secondary"
                  }`}
                >
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-text-muted">
                    {m.role} · {m.ts}
                  </div>
                  <p className="mt-1 font-display text-[15px] leading-relaxed">{m.content}</p>
                </div>
              </div>
            ))}
          </div>

          <form onSubmit={send} className="mt-4 flex items-center gap-2 border-t border-border pt-3">
            <div className="flex-1">
              <JInput
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Transmit a message…"
                aria-label="Message"
              />
            </div>
            <JButton type="submit">
              <Send className="mr-2 h-4 w-4" />
              Send
            </JButton>
          </form>
        </div>
      </Widget>
    </Shell>
  );
}
