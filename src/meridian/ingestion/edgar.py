from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from meridian.settings import FIXTURES_DIR, is_demo_mode


class EdgarFiling(BaseModel):
    ticker: str
    form_type: str
    filed_date: str
    accession_number: str
    text_chunks: list[str]


@dataclass(slots=True)
class EdgarClient:
    demo_mode: bool | None = None
    fixtures_root: Path = FIXTURES_DIR / "edgar"

    def __post_init__(self) -> None:
        if self.demo_mode is None:
            self.demo_mode = is_demo_mode()

    def get_latest_filing(self, ticker: str, form_type: str) -> EdgarFiling:
        if self.demo_mode:
            path = self.fixtures_root / f"{ticker}_{form_type}.json"
            if not path.exists():
                raise FileNotFoundError(f"EDGAR fixture not found: {path}")
            return EdgarFiling.model_validate(json.loads(path.read_text(encoding="utf-8")))
        raise RuntimeError("Live EDGAR fetch is not implemented for this milestone")

    def chunk_text(self, text: str, chunk_size: int = 4000) -> list[str]:
        words = re.split(r"\s+", text.strip())
        chunks: list[str] = []
        bucket: list[str] = []
        size = 0
        for word in words:
            token_len = len(word) + 1
            if size + token_len > chunk_size and bucket:
                chunks.append(" ".join(bucket))
                bucket = [word]
                size = token_len
                continue
            bucket.append(word)
            size += token_len
        if bucket:
            chunks.append(" ".join(bucket))
        return chunks
