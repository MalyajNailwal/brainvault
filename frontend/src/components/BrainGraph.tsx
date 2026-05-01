import { useEffect, useRef, useCallback } from "react";
import ForceGraph2D from "react-force-graph-2d";
import type { GraphData } from "../hooks/useSocket";

interface Props {
  data: GraphData;
}

export default function BrainGraph({ data }: Props) {
  const fgRef = useRef<any>(null);

  // Auto-fit when data changes
  useEffect(() => {
    if (fgRef.current && data.nodes.length > 0) {
      const timer = setTimeout(() => {
        fgRef.current?.zoomToFit(400, 20);
      }, 600);
      return () => clearTimeout(timer);
    }
  }, [data]);

  const drawNode = useCallback(
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const label = node.name || node.id;
      const fontSize = Math.max(8, 11 / globalScale);
      const radius = Math.sqrt(node.val || 4) * 3;

      // Glow shadow
      ctx.shadowBlur = 12;
      ctx.shadowColor = node.color || "#3b82f6";

      // Node circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = node.color || "#3b82f6";
      ctx.fill();
      ctx.shadowBlur = 0;

      // White border on hover/selected (react-force-graph handles selection state)
      if (node.__selected) {
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2 / globalScale;
        ctx.stroke();
      }

      // Label
      if (globalScale > 0.5) {
        ctx.font = `${fontSize}px 'JetBrains Mono', monospace`;
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillStyle = "#e2e8f0";
        ctx.fillText(label, node.x, node.y + radius + 2);
      }
    },
    []
  );

  if (data.nodes.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-vault-muted">
        <p className="text-5xl mb-4">🧠</p>
        <p className="text-sm">Your brain is empty</p>
        <p className="text-xs mt-2 text-vault-muted/60">
          Add documents to see the knowledge graph
        </p>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative">
      {/* Stats overlay */}
      {data.stats && (
        <div className="absolute top-3 left-3 z-10 bg-vault-bg/80 backdrop-blur-sm px-3 py-1.5 rounded-md text-[11px] text-vault-muted border border-vault-border">
          {data.stats.total_nodes} nodes · {data.stats.total_links} connections
        </div>
      )}

      {/* Connection status */}
      <div className="absolute top-3 right-3 z-10 text-[10px] text-vault-muted bg-vault-bg/80 backdrop-blur-sm px-2 py-1 rounded-md border border-vault-border">
        Click node to focus · Click background to reset
      </div>

      <ForceGraph2D
        ref={fgRef}
        graphData={data}
        nodeId="id"
        nodeLabel={(node: any) =>
          `${node.name}\nType: ${node.type}\n${node.description?.slice(0, 100) || ""}`
        }
        nodeCanvasObject={drawNode}
        nodeCanvasObjectMode={() => "replace"}
        linkColor={() => "#1e293b"}
        linkWidth={1}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        linkDirectionalParticles={1}
        linkDirectionalParticleSpeed={0.003}
        linkDirectionalParticleColor={() => "#475569"}
        backgroundColor="#020817"
        onNodeClick={(node: any) => {
          fgRef.current?.centerAt(node.x, node.y, 700);
          fgRef.current?.zoom(5, 700);
        }}
        onBackgroundClick={() => {
          fgRef.current?.zoomToFit(500, 30);
        }}
        warmupTicks={30}
        cooldownTicks={100}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
      />
    </div>
  );
}
