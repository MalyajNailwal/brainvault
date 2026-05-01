import { useState, useRef, useEffect } from "react";
import { api } from "../api/client";

interface Message {
  role: "user" | "ai";
  text: string;
  mode?: string;
}

const MODES = ["hybrid", "local", "global", "naive"] as const;
type Mode = (typeof MODES)[number];

const MODE_DESCRIPTIONS: Record<Mode, string> = {
  hybrid: "Best of both — recommended",
  local: "Focused, specific answers",
  global: "Broad, thematic answers",
  naive: "Simple vector search",
};

const STORAGE_KEY = "brainvault_chat_history";

function loadHistory(): Message[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    // ignore
  }
  return [
    {
      role: "ai",
      text: "Hi! Add some documents to your vault and then ask me anything about them 🧠",
    },
  ];
}

function saveHistory(messages: Message[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  } catch {
    // ignore
  }
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>(loadHistory);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<Mode>("hybrid");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    saveHistory(messages);
  }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const q = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setLoading(true);

    try {
      const res = await api.post("/chat", { question: q, mode });
      setMessages((m) => [
        ...m,
        { role: "ai", text: res.data.answer, mode: res.data.mode },
      ]);
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        "❌ Error connecting to backend. Is the server running?";
      setMessages((m) => [...m, { role: "ai", text: msg }]);
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = () => {
    const welcome: Message = {
      role: "ai",
      text: "Hi! Add some documents to your vault and then ask me anything about them 🧠",
    };
    setMessages([welcome]);
    saveHistory([welcome]);
  };

  return (
    <div className="flex flex-col h-full gap-3">
      {/* Mode selector */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <p className="text-[10px] text-vault-muted uppercase tracking-wider">Query Mode</p>
          <button
            onClick={clearHistory}
            className="text-[10px] text-vault-muted hover:text-vault-accent transition-colors"
          >
            Clear chat
          </button>
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {MODES.map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              title={MODE_DESCRIPTIONS[m]}
              className={`px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
                mode === m
                  ? "bg-vault-accent text-vault-bg"
                  : "bg-vault-border text-vault-muted hover:text-vault-text"
              }`}
            >
              {m}
            </button>
          ))}
        </div>
        <p className="text-[10px] text-vault-muted/70 mt-1">{MODE_DESCRIPTIONS[mode]}</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto min-h-0 flex flex-col gap-2 pr-1">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`px-3 py-2.5 rounded-xl max-w-[92%] text-[13px] leading-relaxed whitespace-pre-wrap ${
              m.role === "user"
                ? "self-end bg-blue-600 text-white"
                : "self-start bg-vault-border text-vault-text"
            }`}
          >
            {m.text}
            {m.mode && (
              <span className="block text-[10px] text-vault-muted mt-1.5 opacity-70">
                [{m.mode}]
              </span>
            )}
          </div>
        ))}
        {loading && (
          <div className="self-start bg-vault-border text-vault-muted px-3 py-2.5 rounded-xl text-[13px]">
            <span className="inline-flex items-center gap-2">
              <span className="animate-pulse">🧠</span> Thinking...
            </span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2 shrink-0">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          placeholder="Ask anything about your documents..."
          className="flex-1 px-3.5 py-2.5 bg-vault-panel border border-vault-border rounded-lg text-[13px] text-vault-text placeholder:text-vault-muted/50 outline-none focus:border-vault-accent transition-colors"
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          className={`px-4 py-2.5 rounded-lg text-[13px] font-medium transition-all ${
            loading || !input.trim()
              ? "bg-vault-border text-vault-muted cursor-not-allowed"
              : "bg-vault-accent text-vault-bg hover:brightness-110"
          }`}
        >
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
