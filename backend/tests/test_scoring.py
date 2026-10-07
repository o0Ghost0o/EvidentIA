"""Fase 4 tests: deterministic scoring, dedup labels, contradictions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from evidentia.scoring import score as scoring
from evidentia.scoring.deduplication import (
    find_numeric_contradictions,
    label_group,
)


def test_score_formula_matches_manual_calc() -> None:
    now = datetime.now(timezone.utc)
    res = scoring.score_topic(
        title="Panamá aprueba ampliación del Canal",
        group_size=3, primary_sources=2, published_at=now,
        modalidad="tvn", has_indicator=True, titular_only=True,
    )
    c = res["components"]
    expected = round(30 * c["R"] + 25 * c["I"] + 20 * c["U"] + 15 * c["N"] + 10 * c["E"], 2)
    assert res["P"] == expected
    assert res["rules_version"] == "v1"
    assert res["evidence_state"] == "suficiente"
    assert all(0.0 <= v <= 1.0 for v in c.values())


def test_bands_have_no_overlap() -> None:
    assert scoring.band(0.0) == "bajo"
    assert scoring.band(39.99) == "bajo"
    assert scoring.band(40.0) == "medio"
    assert scoring.band(69.99) == "medio"
    assert scoring.band(70.0) == "alto"
    assert scoring.band(100.0) == "alto"


def test_urgency_decay_and_unknown() -> None:
    now = datetime.now(timezone.utc)
    assert scoring.urgency(now) == 1.0
    assert scoring.urgency(now - timedelta(days=60)) == 0.0
    assert scoring.urgency(None) == 0.3
    mid = scoring.urgency(now - timedelta(days=10))
    assert 0.0 < mid < 1.0


def test_novelty_penalises_replicas() -> None:
    assert scoring.novelty(1) == 1.0
    assert scoring.novelty(4) == 0.5
    assert scoring.novelty(9) < scoring.novelty(4)


def test_evidence_state_matrix() -> None:
    assert scoring.evidence_state(0) == "insuficiente"
    assert scoring.evidence_state(1, titular_only=True) == "insuficiente"
    assert scoring.evidence_state(1, titular_only=False) == "parcial"
    assert scoring.evidence_state(2) == "suficiente"
    assert scoring.evidence_state(1, has_indicator=True) == "suficiente"


def test_label_group_repetition_vs_corroboration() -> None:
    assert label_group([{"agencia_primaria": None}])["label"] == "single"
    rep = label_group([
        {"agencia_primaria": "EFE"}, {"agencia_primaria": "EFE"},
    ])
    assert rep["label"] == "repetition" and rep["primary_sources"] == 1
    cor = label_group([
        {"agencia_primaria": "EFE"}, {"agencia_primaria": None},
    ])
    assert cor["label"] == "independent_corroboration" and cor["primary_sources"] == 2


def test_numeric_contradictions() -> None:
    members = [
        {"id_noticia": "a", "titulo": "Inflación llega a 3.5% en Panamá"},
        {"id_noticia": "b", "titulo": "Inflación de Panamá cierra en 5.1%"},
        {"id_noticia": "c", "titulo": "Panamá aprueba ampliación del Canal"},
    ]
    hits = find_numeric_contradictions(members)
    assert len(hits) == 1
    assert {hits[0]["a_id"], hits[0]["b_id"]} == {"a", "b"}
    assert hits[0]["unit"] == "%"
    assert find_numeric_contradictions(members[1:]) == []
    # Same numbers, no contradiction.
    same = [
        {"id_noticia": "a", "titulo": "Bono de 100 balboas aprobado"},
        {"id_noticia": "b", "titulo": "Aprueban bono de 100 balboas"},
    ]
    assert find_numeric_contradictions(same) == []
