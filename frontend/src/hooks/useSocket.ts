import { useEffect, useRef, useState, useCallback } from "react";

export interface FileStatus {
  file: string;
  status: "processing" | "done" | "error";
  error?: string;
}

export interface GraphNode {
  id: string;
  name: string;
  type: string;
  description: string;
  color: string;
  val: number;
}

export interface GraphLink {
  source: string;
  target: string;
  label: string;
  value: number;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  stats?: { total_nodes: number; total_links: number };
}

export interface WsMessage {
  type: "file_status" | "graph_update";
  file?: string;
  status?: string;
  error?: string;
  data?: GraphData;
}

export function useSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [fileStatuses, setFileStatuses] = useState<Record<string, FileStatus>>({});
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });

  const connect = useCallback(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onopen = () => {
      setConnected(true);
      console.log("[WebSocket] Connected");
    };

    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data);
        if (msg.type === "file_status" && msg.file) {
          setFileStatuses((prev) => ({
            ...prev,
            [msg.file!]: {
              file: msg.file!,
              status: msg.status as FileStatus["status"],
              error: msg.error,
            },
          }));
        } else if (msg.type === "graph_update" && msg.data) {
          setGraphData(msg.data);
        }
      } catch (e) {
        console.warn("[WebSocket] Invalid message:", event.data);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log("[WebSocket] Disconnected");
      // Auto-reconnect after 3s
      setTimeout(connect, 3000);
    };

    ws.onerror = (err) => {
      console.error("[WebSocket] Error:", err);
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected, fileStatuses, graphData, setGraphData };
}
