"""Tests for Benchmark 40/20 runner, metrics, and claim support verification."""

from __future__ import annotations

import json
from pathlib import Path

from evidentia.evaluation.benchmark_runner import (
    load_corpus_dict,
    split_benchmark,
)


def test_benchmark_40_20_split_distribution() -> None:
    bench_file = Path("data/benchmark.jsonl")
    assert bench_file.exists()
    dev_queries, reserved_queries = split_benchmark(bench_file)

    assert len(dev_queries) == 40
    assert len(reserved_queries) == 20
    assert len(dev_queries) + len(reserved_queries) == 60

    dev_types = [q["tipo"] for q in dev_queries]
    assert dev_types.count("sustentada") == 20
    assert dev_types.count("contradiccion") == 7
    assert dev_types.count("sin_respuesta") == 7
    assert dev_types.count("adversarial") == 6

    res_types = [q["tipo"] for q in reserved_queries]
    assert res_types.count("sustentada") == 10
    assert res_types.count("contradiccion") == 3
    assert res_types.count("sin_respuesta") == 3
    assert res_types.count("adversarial") == 4


def test_benchmark_results_metrics_compliance() -> None:
    results_file = Path("data/benchmark_results_40.json")
    assert results_file.exists(), "Benchmark results file must exist"

    data = json.loads(results_file.read_text(encoding="utf-8"))
    eff = data["efficiency"]
    supp = data["support_validity"]
    acc = data["benchmark_40_accuracy"]

    # Efficiency contracts
    assert eff["median_latency_seconds"] <= 15.0
    assert eff["meets_latency_target"] is True
    assert eff["total_tokens_consumed"] > 0
    assert eff["total_cost_usd"] > 0

    # Support validity contracts (>=30 claims, >=90% validity)
    assert supp["reviewed_claims_count"] >= 30
    assert supp["support_validity_rate"] >= 0.90
    assert supp["meets_target"] is True

    # Abstention contracts (>=80% abstention on unanswerable)
    assert acc["unanswerable_total"] == 7
    assert acc["correct_abstentions"] == 7
    assert acc["abstention_rate"] >= 0.80
