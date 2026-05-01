import { useEffect } from "react";
import { api } from "./api/client";
import { useSocket } from "./hooks/useSocket";
import VaultPanel from "./components/VaultPanel";
import BrainGraph from "./components/BrainGraph";
import ChatPanel from "./components/ChatPanel";

export default function App() {
  const { connected, fileStatuses, graphData, setGraphData } = useSocket();

  // Load initial graph on mount
  useEffect(() => {
    api
      .get("/graph")
      .then((res) => {
        if (res.data) setGraphData(res.data);
      })
      .catch((err) => console.error("Failed to load graph:", err));
  }, [setGraphData]);

  return (
    <div className="h-screen w-screen bg-vault-bg text-vault-text font-mono flex flex-col overflow-hidden">
      {/* Header */}
      <header className="h-12 shrink-0 flex items-center gap-3 px-5 border-b border-vault-border bg-vault-bg z-20">
        <span className="text-xl">🧠</span>
        <span className="text-base font-bold text-vault-accent">BrainVault</span>
        <span className="text-xs text-vault-muted hidden sm:inline">
          — your personal knowledge graph
        </span>
        <div className="ml-auto flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${connected ? "bg-green-500" : "bg-red-500"}`}
            title={connected ? "Connected" : "Disconnected"}
          />
          <span className="text-[10px] text-vault-muted uppercase tracking-wider">
            {connected ? "Live" : "Reconnecting..."}
          </span>
        </div>
      </header>

      {/* Main 3-panel grid */}
      <main className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-[280px_1fr_340px]">
        {/* Left: Vault */}
        <aside className="border-r border-vault-border p-4 overflow-hidden flex flex-col min-h-0">
          <h2 className="text-[10px] text-vault-muted uppercase tracking-wider mb-3 shrink-0">
            📁 Vault
          </h2>
          <div className="flex-1 min-h-0 overflow-hidden">
            <VaultPanel fileStatuses={fileStatuses} />
          </div>
        </aside>

        {/* Center: Graph */}
        <section className="relative overflow-hidden min-h-0">
          <BrainGraph data={graphData} />
        </section>

        {/* Right: Chat */}
        <aside className="border-l border-vault-border p-4 overflow-hidden flex flex-col min-h-0">
          <h2 className="text-[10px] text-vault-muted uppercase tracking-wider mb-3 shrink-0">
            💬 Chat
          </h2>
          <div className="flex-1 min-h-0 overflow-hidden">
            <ChatPanel />
          </div>
        </aside>
      </main>
    </div>
  );
}
