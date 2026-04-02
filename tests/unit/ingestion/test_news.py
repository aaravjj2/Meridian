from __future__ import annotations

from meridian.ingestion.news import NewsClient


def test_news_topic_slug_normalisation() -> None:
    client = NewsClient(demo_mode=True)
    assert client.topic_slug("Fed Rate Decision") == "fed-rate-decision"
    assert client.topic_slug("recession risk") == "recession-risk"


def test_sentiment_scorer_directionality() -> None:
    client = NewsClient(demo_mode=True)
    pos = client.sentiment_score("disinflation and resilient growth")
    neg = client.sentiment_score("recession stress and layoffs")
    assert pos > 0
    assert neg < 0


def test_news_fetch_fixture_with_sentiment() -> None:
    client = NewsClient(demo_mode=True)
    articles = client.fetch("fed rate decision", days_back=7)
    assert len(articles) >= 2
    assert all(-1.0 <= article.sentiment_score <= 1.0 for article in articles)
