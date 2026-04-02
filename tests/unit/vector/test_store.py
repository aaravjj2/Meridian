from __future__ import annotations

from meridian.vector.store import VectorStore


def test_vector_store_upsert_and_search_roundtrip(tmp_path) -> None:
    store = VectorStore(persist_dir=tmp_path / "chroma")
    store.upsert("doc-1", "yield curve inversion and equities", {"type": "note"})
    store.upsert("doc-2", "inflation cooling and policy easing", {"type": "note"})

    results = store.search("yield curve", top_k=1)
    assert len(results) == 1
    assert results[0].doc_id == "doc-1"
