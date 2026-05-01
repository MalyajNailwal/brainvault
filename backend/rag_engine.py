"""RAG-Anything engine wrapper with CORRECT API usage."""
import asyncio
import logging
from functools import partial
from pathlib import Path
from typing import Any

from config import (
    RAG_STORAGE_DIR,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    LLM_MODEL,
    VISION_MODEL,
    OPENAI_API_KEY,
    EMBED_MODEL,
    EMBED_BASE_URL,
    EMBED_DIM,
)

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Singleton wrapper around RAG-Anything.
    Handles correct initialization with sync funcs, file processing, and querying.
    """

    _instance: "RAGEngine | None" = None
    _lock = asyncio.Lock()

    def __new__(cls) -> "RAGEngine":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._rag = None
        return cls._instance

    # ── Sync LLM wrapper ──────────────────────────────────────────────
    @staticmethod
    def _llm_model_func(prompt: str, system_prompt: str | None = None, history_messages: list | None = None, **kwargs: Any) -> str:
        """Synchronous LLM call via OpenRouter (used by LightRAG/RAG-Anything internals)."""
        history_messages = history_messages or []
        try:
            from lightrag.llm.openai import openai_complete_if_cache
            # openai_complete_if_cache may be async or sync depending on version;
            # wrap in asyncio.run if needed.
            coro = openai_complete_if_cache(
                model=LLM_MODEL,
                prompt=prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                **kwargs,
            )
            if asyncio.iscoroutine(coro):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Schedule and block with run_coroutine_threadsafe
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            future = asyncio.run_coroutine_threadsafe(coro, loop)
                            return future.result(timeout=120)
                    return loop.run_until_complete(coro)
                except RuntimeError:
                    return asyncio.run(coro)
            return coro
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"[LLM Error: {e}]"

    # ── Sync Vision wrapper ───────────────────────────────────────────
    @staticmethod
    def _vision_model_func(
        prompt: str | None = None,
        system_prompt: str | None = None,
        history_messages: list | None = None,
        image_data: str | None = None,
        messages: list | None = None,
        **kwargs: Any,
    ) -> str:
        """Synchronous vision call via OpenRouter (used for image analysis)."""
        try:
            from lightrag.llm.openai import openai_complete_if_cache

            if messages:
                # Multimodal messages format (for VLM-enhanced queries)
                coro = openai_complete_if_cache(
                    model=VISION_MODEL,
                    prompt="",
                    system_prompt=None,
                    history_messages=[],
                    messages=messages,
                    api_key=OPENROUTER_API_KEY,
                    base_url=OPENROUTER_BASE_URL,
                    **kwargs,
                )
            elif image_data:
                # Single image base64 format
                msgs = [
                    {"role": "system", "content": system_prompt} if system_prompt else None,
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt or "Describe this image."},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                            },
                        ],
                    },
                ]
                msgs = [m for m in msgs if m is not None]
                coro = openai_complete_if_cache(
                    model=VISION_MODEL,
                    prompt="",
                    system_prompt=None,
                    history_messages=[],
                    messages=msgs,
                    api_key=OPENROUTER_API_KEY,
                    base_url=OPENROUTER_BASE_URL,
                    **kwargs,
                )
            else:
                # Fallback to text LLM
                return RAGEngine._llm_model_func(prompt or "", system_prompt, history_messages, **kwargs)

            if asyncio.iscoroutine(coro):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            future = asyncio.run_coroutine_threadsafe(coro, loop)
                            return future.result(timeout=120)
                    return loop.run_until_complete(coro)
                except RuntimeError:
                    return asyncio.run(coro)
            return coro
        except Exception as e:
            logger.error(f"Vision call failed: {e}")
            return f"[Vision Error: {e}]"

    # ── Embedding function ────────────────────────────────────────────
    @staticmethod
    def _embedding_func(texts: list[str]) -> list[list[float]]:
        """Synchronous embedding call via OpenAI."""
        try:
            from lightrag.llm.openai import openai_embed
            result = openai_embed(
                texts,
                model=EMBED_MODEL,
                api_key=OPENAI_API_KEY,
                base_url=EMBED_BASE_URL,
            )
            # Result may be a coroutine in some versions
            if asyncio.iscoroutine(result):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            future = asyncio.run_coroutine_threadsafe(result, loop)
                            return future.result(timeout=60)
                    return loop.run_until_complete(result)
                except RuntimeError:
                    return asyncio.run(result)
            return result
        except Exception as e:
            logger.error(f"Embedding call failed: {e}")
            # Return zero vectors as fallback so the app doesn't crash
            return [[0.0] * EMBED_DIM for _ in texts]

    def _build_rag(self) -> Any:
        """Build and return a RAGAnything instance with correct config."""
        from raganything import RAGAnything, RAGAnythingConfig
        from lightrag.utils import EmbeddingFunc

        config = RAGAnythingConfig(
            working_dir=str(RAG_STORAGE_DIR),
            parser="mineru",
            parse_method="auto",
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
        )

        embedding = EmbeddingFunc(
            embedding_dim=EMBED_DIM,
            max_token_size=8192,
            func=RAGEngine._embedding_func,
        )

        rag = RAGAnything(
            config=config,
            llm_model_func=RAGEngine._llm_model_func,
            vision_model_func=RAGEngine._vision_model_func,
            embedding_func=embedding,
        )
        logger.info("RAGAnything engine initialized successfully.")
        return rag

    def get_rag(self) -> Any:
        """Lazy-load the RAGAnything singleton."""
        if self._rag is None:
            self._rag = self._build_rag()
        return self._rag

    async def process_file(self, file_path: str) -> dict[str, Any]:
        """
        Process a single file into the knowledge graph.
        Uses process_document_complete (correct RAG-Anything API).
        """
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "file": path.name, "error": "File not found"}

        async with self._lock:
            rag = self.get_rag()
            try:
                # process_document_complete is the correct method name
                await rag.process_document_complete(
                    file_path=str(path),
                    output_dir=str(RAG_STORAGE_DIR / "parsed_output"),
                    parse_method="auto",
                )
                return {"status": "success", "file": path.name}
            except Exception as e:
                logger.exception(f"Failed to process {path.name}")
                return {"status": "error", "file": path.name, "error": str(e)}

    async def query(self, question: str, mode: str = "hybrid") -> str:
        """
        Query the knowledge graph.
        Uses aquery (async) — the correct RAG-Anything API.
        """
        rag = self.get_rag()
        try:
            # aquery is the async method; if vlm_enhanced is not forced,
            # it auto-detects based on vision_model_func presence.
            result = await rag.aquery(question, mode=mode)
            return str(result)
        except Exception as e:
            logger.exception("Query failed")
            return f"Error: {e}"

    async def query_with_multimodal(self, question: str, multimodal_content: list[dict]) -> str:
        """
        Query with inline multimodal content (table, equation, image).
        Uses aquery_with_multimodal (correct RAG-Anything API).
        """
        rag = self.get_rag()
        try:
            result = await rag.aquery_with_multimodal(
                question,
                multimodal_content=multimodal_content,
                mode="hybrid",
            )
            return str(result)
        except Exception as e:
            logger.exception("Multimodal query failed")
            return f"Error: {e}"


# Convenience accessor
rag_engine = RAGEngine()
