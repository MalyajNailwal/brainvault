"""Extract graph nodes & edges from LightRAG internal storage."""
import logging
from typing import Any
from config import RAG_STORAGE_DIR

logger = logging.getLogger(__name__)

# Color map for entity types
TYPE_COLORS = {
    "person": "#f97316",
    "organization": "#3b82f6",
    "concept": "#8b5cf6",
    "location": "#10b981",
    "event": "#ec4899",
    "image": "#06b6d4",
    "table": "#f59e0b",
    "equation": "#6366f1",
    "unknown": "#64748b",
}


def get_graph_data() -> dict[str, Any]:
    """
    Read the LightRAG knowledge graph from internal storage APIs
    and return nodes/links compatible with react-force-graph-2d.
    """
    nodes: list[dict] = []
    links: list[dict] = []

    try:
        # Import LightRAG components inside function to avoid
        # heavy import at module load time.
        from lightrag import LightRAG
        from lightrag.kg.shared_storage import initialize_pipeline_status

        # We create a minimal LightRAG instance to access existing storage.
        # No LLM/embedding needed for read-only graph extraction.
        rag = LightRAG(working_dir=str(RAG_STORAGE_DIR))

        # Initialize storages (this loads existing data if present)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(rag.initialize_storages())
        loop.run_until_complete(initialize_pipeline_status())

        # Access the internal graph storage
        graph_storage = rag.chunk_entity_relation_graph
        if graph_storage is None:
            return {"nodes": [], "links": []}

        # Fetch all nodes
        all_nodes = loop.run_until_complete(graph_storage.get_all_nodes())
        for node_id in all_nodes:
            node_data = loop.run_until_complete(graph_storage.get_node(node_id))
            if not node_data:
                continue
            entity_type = (node_data.get("entity_type") or "unknown").lower()
            nodes.append({
                "id": node_id,
                "name": node_data.get("entity_name", node_id),
                "type": entity_type,
                "description": node_data.get("description", ""),
                "color": TYPE_COLORS.get(entity_type, TYPE_COLORS["unknown"]),
                "val": 4 + min(node_data.get("source_id", "").count(","), 6),
            })

        # Fetch all edges
        all_edges = loop.run_until_complete(graph_storage.get_all_edges())
        for edge in all_edges:
            parts = edge.split("->")
            if len(parts) != 2:
                continue
            source, target = parts[0].strip(), parts[1].strip()
            edge_data = loop.run_until_complete(graph_storage.get_edge(source, target))
            if not edge_data:
                continue
            links.append({
                "source": source,
                "target": target,
                "label": edge_data.get("keywords", ""),
                "value": max(float(edge_data.get("weight", 1.0)), 0.1),
            })

    except Exception as e:
        logger.warning(f"Graph read failed: {e}")
        return {"nodes": [], "links": []}

    return {
        "nodes": nodes,
        "links": links,
        "stats": {
            "total_nodes": len(nodes),
            "total_links": len(links),
        },
    }
