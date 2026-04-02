from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from meridian.settings import FIXTURES_DIR, is_demo_mode


POSITIVE = {
    "cooling",
    "disinflation",
    "resilient",
    "growth",
    "stabilized",
    "soft-landing",
}
NEGATIVE = {
    "recession",
    "stress",
    "spike",
    "deteriorating",
    "layoffs",
    "default",
}


class NewsArticle(BaseModel):
    title: str
    url: str
    published_at: str
    snippet: str
    sentiment_score: float


@dataclass(slots=True)
class NewsClient:
    demo_mode: bool | None = None
    fixtures_root: Path = FIXTURES_DIR / "news"

    def __post_init__(self) -> None:
        if self.demo_mode is None:
            self.demo_mode = is_demo_mode()

    def fetch(self, topic: str, days_back: int = 7) -> list[NewsArticle]:
        slug = self.topic_slug(topic)
        if self.demo_mode:
            path = self.fixtures_root / f"{slug}.json"
            if not path.exists():
                raise FileNotFoundError(f"News fixture not found: {path}")
            records = json.loads(path.read_text(encoding="utf-8"))
            articles = []
            for row in records:
                if "sentiment_score" not in row:
                    row["sentiment_score"] = self.sentiment_score(row.get("snippet", ""))
                articles.append(NewsArticle.model_validate(row))
            return articles
        raise RuntimeError("Live news fetch is not implemented for this milestone")

    def sentiment_score(self, text: str) -> float:
        words = {w.lower() for w in re.findall(r"[A-Za-z\-]+", text)}
        pos_hits = len(words & POSITIVE)
        neg_hits = len(words & NEGATIVE)
        score = (pos_hits - neg_hits) / 4
        return max(-1.0, min(1.0, score))

    def topic_slug(self, topic: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", topic.strip().lower()).strip("-")
        return slug
