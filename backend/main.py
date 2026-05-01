"""BrainVault FastAPI backend with native WebSocket support."""
import asyncio
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import VAULT_DIR, SUPPORTED_EXTENSIONS, check_api_keys
from rag_engine import rag_engine
from graph_utils import get_graph_data
from watcher import FolderWatcher
from registry import mark_file_processed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="BrainVault API", version="0.1.0")

# ── CORS ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Active WebSocket connections ────────────────────────────────────
active_connections: list[WebSocket] = []

async def broadcast(message: dict[str, Any]) -> None:
    """Send a JSON message to all connected WebSocket clients."""
    dead = []
    for ws in active_connections:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in active_connections:
            active_connections.remove(ws)


# ── File processing with notifications ──────────────────────────────
async def process_and_notify(file_path: str) -> None:
    """Process a single file and broadcast updates to all clients."""
    filename = Path(file_path).name

    await broadcast({"type": "file_status", "file": filename, "status": "processing"})

    result = await rag_engine.process_file(file_path)

    if result["status"] == "success":
        mark_file_processed(file_path)
        graph_data = get_graph_data()
        await broadcast({"type": "file_status", "file": filename, "status": "done"})
        await broadcast({"type": "graph_update", "data": graph_data})
        logger.info(f"Processed: {filename}")
    else:
        await broadcast({
            "type": "file_status",
            "file": filename,
            "status": "error",
            "error": result.get("error", "Unknown error"),
        })
        logger.error(f"Failed: {filename} — {result.get('error')}")


# ── Watcher lifecycle ───────────────────────────────────────────────
watcher = FolderWatcher(process_callback=process_and_notify)

@app.on_event("startup")
async def startup_event():
    missing = check_api_keys()
    if missing:
        logger.warning(f"Missing API keys: {', '.join(missing)}")
        logger.warning("Please set them in backend/.env and restart the server.")
    else:
        logger.info("All API keys configured.")

    loop = asyncio.get_event_loop()
    watcher.start(loop)
    logger.info(f"BrainVault ready. Vault: {VAULT_DIR}")

@app.on_event("shutdown")
async def shutdown_event():
    watcher.stop()


# ── REST Routes ─────────────────────────────────────────────────────

class VaultInfoResponse(BaseModel):
    vault_path: str
    files: list[dict[str, Any]]
    total_files: int

@app.get("/vault/info", response_model=VaultInfoResponse)
async def vault_info():
    """Return vault folder path and file list with metadata."""
    files = []
    for f in VAULT_DIR.iterdir():
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "extension": f.suffix.lower(),
                "modified": f.stat().st_mtime,
            })
    files.sort(key=lambda x: x["modified"], reverse=True)
    return {
        "vault_path": str(VAULT_DIR),
        "files": files,
        "total_files": len(files),
    }


@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """Upload files via UI drag-and-drop. Saves to vault & triggers processing."""
    results = []
    for upload in files:
        ext = Path(upload.filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            results.append({"file": upload.filename, "status": "skipped", "reason": "unsupported format"})
            continue

        dest = VAULT_DIR / upload.filename
        # Handle duplicate filenames
        counter = 1
        while dest.exists():
            stem = Path(upload.filename).stem
            dest = VAULT_DIR / f"{stem}_{counter}{ext}"
            counter += 1

        content = await upload.read()
        dest.write_bytes(content)
        results.append({"file": dest.name, "status": "saved"})

        # Trigger processing (watcher will also catch it, but this is faster)
        asyncio.create_task(process_and_notify(str(dest)))

    return {"results": results}


@app.get("/graph")
async def get_graph():
    """Return current knowledge graph data."""
    return get_graph_data()


class QueryRequest(BaseModel):
    question: str
    mode: str = "hybrid"

class QueryResponse(BaseModel):
    answer: str
    mode: str

@app.post("/chat", response_model=QueryResponse)
async def chat(req: QueryRequest):
    """Ask a question against the knowledge graph."""
    valid_modes = {"local", "global", "hybrid", "naive", "mix", "bypass"}
    if req.mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Choose from: {', '.join(valid_modes)}")

    answer = await rag_engine.query(req.question, mode=req.mode)
    return {"answer": answer, "mode": req.mode}


@app.get("/health")
async def health():
    missing = check_api_keys()
    return {
        "status": "ok" if not missing else "missing_keys",
        "vault": str(VAULT_DIR),
        "vault_exists": VAULT_DIR.exists(),
        "missing_keys": missing,
    }


# ── Native WebSocket ────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    active_connections.append(ws)
    logger.info(f"WebSocket client connected. Total: {len(active_connections)}")

    # Send current graph immediately on connect
    try:
        graph_data = get_graph_data()
        await ws.send_json({"type": "graph_update", "data": graph_data})
    except Exception:
        pass

    try:
        while True:
            # Keep connection alive; clients can send ping/heartbeat if needed
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        if ws in active_connections:
            active_connections.remove(ws)
        logger.info(f"WebSocket client disconnected. Total: {len(active_connections)}")
