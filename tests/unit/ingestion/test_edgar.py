from __future__ import annotations

from meridian.ingestion.edgar import EdgarClient


def test_edgar_fixture_load() -> None:
    client = EdgarClient(demo_mode=True)
    filing = client.get_latest_filing("AAPL", "10-K")
    assert filing.ticker == "AAPL"
    assert filing.form_type == "10-K"
    assert len(filing.text_chunks) == 5


def test_edgar_chunking_correctness() -> None:
    client = EdgarClient(demo_mode=True)
    text = " ".join(["word"] * 120)
    chunks = client.chunk_text(text, chunk_size=50)
    assert len(chunks) > 1
    assert all(isinstance(chunk, str) and chunk for chunk in chunks)
