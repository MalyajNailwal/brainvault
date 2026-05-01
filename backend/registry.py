"""JSON-based file deduplication registry — no database needed."""
import hashlib
import json
from pathlib import Path
from typing import Dict
from config import REGISTRY_PATH


def _load_registry() -> Dict[str, str]:
    """Load the registry mapping file_path -> sha256_hash."""
    if not REGISTRY_PATH.exists():
        return {}
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_registry(registry: Dict[str, str]) -> None:
    """Persist registry to disk."""
    try:
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)
    except OSError:
        pass


def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file (first 8 MB for speed)."""
    hasher = hashlib.sha256()
    path = Path(file_path)
    if not path.exists():
        return ""
    try:
        # Read in chunks, cap at ~8 MB for large files
        with open(path, "rb") as f:
            remaining = 8 * 1024 * 1024
            while remaining > 0:
                chunk = f.read(min(65536, remaining))
                if not chunk:
                    break
                hasher.update(chunk)
                remaining -= len(chunk)
    except OSError:
        return ""
    return hasher.hexdigest()


def is_file_processed(file_path: str) -> bool:
    """Check if file (by hash) has already been processed."""
    registry = _load_registry()
    current_hash = compute_file_hash(file_path)
    if not current_hash:
        return False
    return registry.get(file_path) == current_hash


def mark_file_processed(file_path: str) -> None:
    """Mark a file as processed by storing its hash."""
    registry = _load_registry()
    file_hash = compute_file_hash(file_path)
    if file_hash:
        registry[file_path] = file_hash
        _save_registry(registry)


def remove_file_entry(file_path: str) -> None:
    """Remove a file from the registry (e.g., on deletion)."""
    registry = _load_registry()
    if file_path in registry:
        del registry[file_path]
        _save_registry(registry)


def list_processed_files() -> Dict[str, str]:
    """Return full registry dict."""
    return _load_registry()
