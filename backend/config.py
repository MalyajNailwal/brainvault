"""BrainVault configuration — cross-platform paths & settings."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the same directory as this file
load_dotenv(Path(__file__).parent / ".env")

# ── Cross-platform Desktop path ─────────────────────────────────────
def get_desktop_path() -> Path:
    """Return the user's Desktop folder, works on Windows, macOS, Linux."""
    if sys.platform == "win32":
        # Windows: use USERPROFILE or HOMEPATH
        home = Path.home()
        desktop = home / "Desktop"
        if desktop.exists():
            return desktop
        # Fallback for OneDrive Desktop
        onedrive_desktop = home / "OneDrive" / "Desktop"
        if onedrive_desktop.exists():
            return onedrive_desktop
        return desktop
    else:
        # macOS / Linux
        return Path.home() / "Desktop"

# ── Vault folder ────────────────────────────────────────────────────
VAULT_DIR = get_desktop_path() / "BrainVault"
VAULT_DIR.mkdir(parents=True, exist_ok=True)

# ── RAG storage (hidden app data) ───────────────────────────────────
RAG_STORAGE_DIR = Path.home() / ".brainvault" / "rag_storage"
RAG_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# ── Deduplication registry (JSON file, no DB) ───────────────────────
REGISTRY_PATH = Path.home() / ".brainvault" / "processed_files.json"
REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Supported file extensions ───────────────────────────────────────
SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt",
    ".xlsx", ".xls", ".png", ".jpg", ".jpeg",
    ".webp", ".gif", ".bmp", ".tiff", ".txt", ".md"
}

# ── LLM / Vision config via OpenRouter ──────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemini-flash-1.5")
VISION_MODEL = os.getenv("VISION_MODEL", "google/gemini-flash-1.5")

# ── Embedding config via OpenAI ─────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBED_BASE_URL = os.getenv("EMBED_BASE_URL", "https://api.openai.com/v1")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIM = int(os.getenv("EMBED_DIM", "1536"))

# ── API validation helper ───────────────────────────────────────────
def check_api_keys() -> list[str]:
    """Return list of missing / empty required API keys."""
    missing = []
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.startswith("sk-or-v1-your"):
        missing.append("OPENROUTER_API_KEY")
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-your-openai"):
        missing.append("OPENAI_API_KEY")
    return missing
