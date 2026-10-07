"""T-04 corpus tests: 90-day RSS window, title-similarity dedup, seed floor."""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

from evidentia.ingestion import validators
from evidentia.ingestion.fetchers.rss import rss_rows

SEED_NEWS = Path(__file__).resolve().parents[2] / "data" / "seed" / "noticias.csv"


def _feed(entries: list[str]) -> str:
    items = "".join(entries)
    return f"<?xml version='1.0'?><rss version='2.0'><channel>{items}</channel></rss>"


def _item(title: str, link: str, published: datetime | None) -> str:
    date = f"<pubDate>{format_datetime(published)}</pubDate>" if published else ""
    return f"<item><title>{title}</title><link>{link}</link>{date}</item>"


def test_rss_window_drops_old_keeps_recent_and_undated() -> None:
    now = datetime.now(timezone.utc)
    xml = _feed([
        _item("Reciente", "https://ej.com/a", now - timedelta(days=5)),
        _item("Vieja", "https://ej.com/b", now - timedelta(days=200)),
        _item("Sin fecha", "https://ej.com/c", None),
    ])
    rows = rss_rows(xml, medio="Prueba", origen="prueba", days=90)
    urls = {r["url"] for r in rows}
    assert "https://ej.com/a" in urls  # inside window
    assert "https://ej.com/c" in urls  # undated → retained
    assert "https://ej.com/b" not in urls  # older than 90 days → dropped
    assert all(r["medio"] == "Prueba" and r["origen"] == "prueba" for r in rows)


def test_near_duplicate_titles_collapse_distinct_titles_survive() -> None:
    rows = [
        {"titulo": "Aprueban bono de 120 balboas para jubilados", "url": "https://x.com/1", "origen": "a"},
        {"titulo": "Aprueban bono de 150 balboas para jubilados", "url": "https://x.com/2", "origen": "b"},
        {"titulo": "Canal de Panamá amplía su capacidad de tránsito", "url": "https://x.com/3", "origen": "c"},
    ]
    res = validators.validate_news(rows)
    assert len(res.valid) == 2  # the two bono headlines collapse to one
    assert any(e["reason"] == "near-duplicate title" for e in res.errors)


def test_seed_corpus_meets_t04_floor() -> None:
    assert SEED_NEWS.exists(), "seed noticias.csv missing"
    with SEED_NEWS.open(encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("titulo")]
    urls = {r["url"] for r in rows}
    by_origen = Counter(r["origen"] for r in rows)
    assert len(urls) >= 100, f"expected >=100 unique, got {len(urls)}"
    assert by_origen["tvn"] >= 20, f"expected >=20 TVN, got {by_origen['tvn']}"
    assert len({r["medio"] for r in rows}) >= 2, "expected multiple outlets"
