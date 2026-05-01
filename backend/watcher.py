"""Watchdog folder monitor with deduplication support."""
import asyncio
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

from config import VAULT_DIR, SUPPORTED_EXTENSIONS
from registry import is_file_processed, mark_file_processed

logger = logging.getLogger(__name__)


class VaultEventHandler(FileSystemEventHandler):
    """
    Handles file creation/modification events in the Vault folder.
    Deduplicates via SHA-256 hash registry.
    """

    def __init__(self, process_callback, loop: asyncio.AbstractEventLoop):
        self.process_callback = process_callback
        self.loop = loop
        self._processing: set[str] = set()

    def on_created(self, event):
        if event.is_directory:
            return
        self._handle_file(event.src_path)

    def on_modified(self, event):
        # Some editors write via temp file + rename, which triggers
        # both created AND modified. We handle both to be safe.
        if event.is_directory:
            return
        self._handle_file(event.src_path)

    def _handle_file(self, src_path: str):
        path = Path(src_path)
        ext = path.suffix.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            return
        if path.name.startswith(".") or path.name.startswith("~$"):
            # Skip hidden files and Office temp files
            return
        if path.name in self._processing:
            return

        # Deduplication check
        if is_file_processed(src_path):
            logger.info(f"Skipping already-processed file: {path.name}")
            return

        self._processing.add(path.name)
        logger.info(f"New file detected: {path.name}")

        # Schedule async processing in the running event loop
        asyncio.run_coroutine_threadsafe(
            self._process_and_release(src_path),
            self.loop,
        )

    async def _process_and_release(self, file_path: str):
        """Wrap callback to release the processing lock afterwards."""
        try:
            await self.process_callback(file_path)
        finally:
            path = Path(file_path)
            self._processing.discard(path.name)


class FolderWatcher:
    """Manages the watchdog observer lifecycle."""

    def __init__(self, process_callback):
        self.process_callback = process_callback
        self.observer: Observer | None = None

    def start(self, loop: asyncio.AbstractEventLoop):
        self.observer = Observer()
        handler = VaultEventHandler(self.process_callback, loop)
        self.observer.schedule(handler, str(VAULT_DIR), recursive=True)
        self.observer.start()
        logger.info(f"Watching vault: {VAULT_DIR}")

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Vault watcher stopped.")
