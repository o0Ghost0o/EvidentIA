"""SHA-256 manifest (``manifest.json``) for the frozen data snapshot."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_FILES = ["noticias.csv", "indicadores.csv", "eventos.geojson", "fichas.jsonl"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(
    processed_dir: Path,
    counts: dict[str, int],
    queries: dict[str, object],
    source: str,
    version: str = "v1",
) -> dict:
    """Build the manifest dict; hashes are computed over processed files."""
    files: dict[str, dict[str, object]] = {}
    for name in MANIFEST_FILES:
        path = processed_dir / name
        if path.exists():
            files[name] = {
                "sha256": sha256_file(path),
                "rows": counts.get(name, 0),
            }
    return {
        "version": version,
        "fecha_corte_UTC": datetime.now(timezone.utc).isoformat(),
        "source": source,  # live | seed
        "consultas": queries,
        "cantidad_por_archivo": counts,
        "archivos": files,
        "licencias_condiciones": {
            "noticias.csv": "Titulares/enlaces; sin republicación de contenidos de terceros.",
            "indicadores.csv": "Banco Mundial CC BY 4.0 (salvo excepciones en metadatos).",
            "eventos.geojson": "USGS; solo hechos sísmicos.",
            "fichas.jsonl": "Casos de evaluación trazables de EvidentIA.",
        },
        "transformaciones": [
            "normalizacion fechas a ISO 8601 UTC",
            "deduplicacion por URL + similitud de titular (Jaccard >= 0.85) / clave natural",
            "ventana de 90 dias en feeds RSS de noticias",
            "ids deterministicos id_noticia=<origen>-sha256(url)[:12]",
        ],
    }


def write_manifest(processed_dir: Path, manifest: dict) -> Path:
    path = processed_dir / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
