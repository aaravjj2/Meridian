from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from meridian.settings import ROOT_DIR

try:
    import chromadb
except Exception:  # pragma: no cover - fallback path for constrained environments
    chromadb = None


def _tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[A-Za-z0-9_\-]+", text.lower()) if token]


def _embed(text: str, dims: int = 32) -> list[float]:
    vector = [0.0] * dims
    for token in _tokenize(text):
        bucket = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16) % dims
        vector[bucket] += 1.0
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0.0:
        return vector
    return [v / norm for v in vector]


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True))


@dataclass(slots=True)
class SearchResult:
    doc_id: str
    text: str
    metadata: dict[str, Any]
    score: float


class VectorStore:
    def __init__(
        self,
        persist_dir: str | Path | None = None,
        collection_name: str = "meridian_docs",
    ) -> None:
        self.persist_dir = Path(persist_dir or (ROOT_DIR / "data" / "processed" / "chroma_db"))
        self.collection_name = collection_name
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._fallback_docs: dict[str, tuple[str, dict[str, Any], list[float]]] = {}

        self._collection = None
        if chromadb is not None:
            client = chromadb.PersistentClient(path=str(self.persist_dir))
            self._collection = client.get_or_create_collection(name=self.collection_name)

    def upsert(self, doc_id: str, text: str, metadata: dict[str, Any]) -> None:
        embedding = _embed(text)
        if self._collection is not None:
            self._collection.upsert(
                ids=[doc_id],
                documents=[text],
                embeddings=[embedding],
                metadatas=[metadata],
            )
            return
        self._fallback_docs[doc_id] = (text, metadata, embedding)

    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        query_embedding = _embed(query)

        if self._collection is not None:
            result = self._collection.query(query_embeddings=[query_embedding], n_results=top_k)
            ids = result.get("ids", [[]])[0]
            docs = result.get("documents", [[]])[0]
            metas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]

            output: list[SearchResult] = []
            for doc_id, text, meta, distance in zip(ids, docs, metas, distances, strict=False):
                score = 1.0 - float(distance)
                output.append(
                    SearchResult(
                        doc_id=str(doc_id),
                        text=str(text),
                        metadata=dict(meta or {}),
                        score=score,
                    )
                )
            return output

        scored: list[SearchResult] = []
        for doc_id, (text, metadata, embedding) in self._fallback_docs.items():
            scored.append(
                SearchResult(
                    doc_id=doc_id,
                    text=text,
                    metadata=metadata,
                    score=_cosine(query_embedding, embedding),
                )
            )
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]


def seed_default_documents(store: VectorStore) -> None:
    docs = [
        (
            "fred_t10y2y",
            "T10Y2Y tracks the slope between the 10-year and 2-year Treasury yields.",
            {"type": "fred", "id": "T10Y2Y"},
        ),
        (
            "fred_cpi",
            "CPIAUCSL captures broad inflation trends in the U.S. consumer basket.",
            {"type": "fred", "id": "CPIAUCSL"},
        ),
        (
            "meridian_method",
            "Meridian ranks prediction market dislocations by comparing market and macro-derived fair value.",
            {"type": "methodology", "id": "macrofair"},
        ),
        (
            "calendar_macro",
            "Macro event cadence includes CPI, FOMC decisions, payrolls, and GDP releases.",
            {"type": "calendar", "id": "macro_events"},
        ),
    ]
    for doc_id, text, metadata in docs:
        store.upsert(doc_id=doc_id, text=text, metadata=metadata)