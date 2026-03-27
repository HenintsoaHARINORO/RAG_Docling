# embeddings/ollama.py — Ollama embedding helpers

import logging
import time

import requests
from langchain_core.embeddings import Embeddings

from config import (
    EMBED_DOC_SLEEP,
    EMBED_MODEL,
    EMBED_RETRIES,
    EMBED_RETRY_SLEEP,
    EMBED_TIMEOUT,
    OLLAMA_URL,
)

logger = logging.getLogger(__name__)

_WARMUP_PROBE_INTERVAL = 2
_WARMUP_MAX_ATTEMPTS   = 15

# keep_alive: -1 tells Ollama never to evict this model between requests
_EMBED_PAYLOAD_BASE = {"model": EMBED_MODEL, "keep_alive": -1}


# ---------------------------------------------------------------------------
# Low-level helper
# ---------------------------------------------------------------------------

def embed_one(text: str, retries: int = EMBED_RETRIES) -> list[float]:
    for attempt in range(retries):
        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/embed",
                json={**_EMBED_PAYLOAD_BASE, "input": text},
                timeout=EMBED_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            # Guard against empty embeddings (Ollama OOM returns 200 but empty)
            embeddings = data.get("embeddings", [])
            if not embeddings:
                raise RuntimeError("Ollama returned empty embeddings (possible OOM)")
            return embeddings[0]
        except Exception as exc:
            wait = EMBED_RETRY_SLEEP * (attempt + 1)
            logger.warning(
                "Embedding attempt %d/%d failed: %s — retrying in %ds",
                attempt + 1, retries, exc, wait,
            )
            time.sleep(wait)

    raise RuntimeError(f"Embedding failed after {retries} attempts")

def warmup_embedder() -> None:
    """
    Poll Ollama until nomic-embed-text is loaded and pinned in memory.
    Uses keep_alive: -1 so the model stays resident for all subsequent calls.
    """
    for attempt in range(1, _WARMUP_MAX_ATTEMPTS + 1):
        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/embed",
                json={**_EMBED_PAYLOAD_BASE, "input": "warmup"},
                timeout=EMBED_TIMEOUT,
            )
            resp.raise_for_status()
            logger.info("Embedding model pinned and ready (probe %d/%d).", attempt, _WARMUP_MAX_ATTEMPTS)
            return
        except Exception as exc:
            logger.info(
                "Waiting for embedding model… probe %d/%d (%s)",
                attempt, _WARMUP_MAX_ATTEMPTS, exc,
            )
            time.sleep(_WARMUP_PROBE_INTERVAL)

    logger.warning("Embedding model did not confirm ready — proceeding anyway.")


# ---------------------------------------------------------------------------
# LangChain-compatible embeddings class
# ---------------------------------------------------------------------------

class DirectOllamaEmbeddings(Embeddings):
    """Calls the Ollama embed API directly, one document at a time."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        results = []
        for i, text in enumerate(texts):
            logger.info("Embedding chunk %d/%d", i + 1, len(texts))
            results.append(embed_one(text))
            time.sleep(EMBED_DOC_SLEEP)
        return results

    def embed_query(self, text: str) -> list[float]:
        return embed_one(text)