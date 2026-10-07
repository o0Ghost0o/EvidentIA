"""Dramatiq broker and ingestion actors.

Worker entrypoint (see docker-compose ``worker`` service)::

    dramatiq evidentia.ingestion.dramatiq_actors --processes 1 --threads 2

The broker connects lazily, so importing this module is safe without Redis.
"""

from __future__ import annotations

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from evidentia.config import get_settings

broker = RedisBroker(url=get_settings().redis_url)
dramatiq.set_broker(broker)


@dramatiq.actor(max_retries=1, time_limit=30 * 60 * 1000, queue_name="default")
def run_ingestion_job(use_seed: bool = False) -> dict:
    """Background ingestion job; returns the quality report summary."""
    from evidentia.ingestion.pipeline import run_ingestion

    report = run_ingestion(use_seed=use_seed)
    return {
        "source": report["source"],
        "families": {
            name: {"valid": fam["valid"], "dropped": fam["dropped"]}
            for name, fam in report["families"].items()
        },
        "warnings": report["warnings"],
    }
