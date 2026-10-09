"""Banca environment bulletin builder (extension).

Output contract (challenge §3): summary ≤250 words, potentially related
sectors, time horizon, evidence, 3 analyst questions. Observation separated
from impact hypotheses; no buy/sell advice, no inferred losses/defaults.
"""

from __future__ import annotations

import re

from evidentia.generation.schemas import BancaBulletinSchema
from evidentia.generation.synthesizer import (
    EvidenceDoc,
    Synthesis,
    Synthesiser,
    cap_words,
    extract_sentence_breakdown,
)

INSTRUCTION = """Redacta el boletín de entorno bancario en EXACTAMENTE este formato:

## Resumen
<máximo 250 palabras: señales observadas en fuentes públicas, citando indicadores macroeconómicos de contexto>

## Sectores potencialmente relacionados
<viñetas de sectores de actividad económica posiblemente impactados>

## Horizonte temporal
<una línea: corto, mediano o largo plazo justificando según las fuentes>

## Evidencia
<viñetas con citas [id_fuente:campo] o [id_fuente]; separa explícitamente [OBSERVACIÓN] (datos fácticos de fuentes) de [HIPÓTESIS DE IMPACTO] (posibles efectos)>

## Preguntas para el analista
1. <pregunta analítica 1>
2. <pregunta analítica 2>
3. <pregunta analítica 3>

Reglas obligatorias para banca:
- Al citar indicadores macroeconómicos del Banco Mundial, cita país/año/unidad exactos y jamás describas una cifra anual histórica como 'actual' o 'de hoy'.
- Estrictamente prohibido: dar recomendaciones de compra/venta o inversión, o inferir pérdidas, impagos o exposición de carteras inexistentes. Señales para análisis, nunca veredictos.
"""


def _split_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = ""
    for line in text.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("## "):
            current = trimmed[3:].strip().lower()
            sections[current] = ""
        elif current:
            # Ignore template placeholder echoes like "<máximo 250 palabras: ...>"
            if re.match(r"^<[^>]+>$", trimmed):
                continue
            sections[current] += line + "\n"
    return {k: v.strip() for k, v in sections.items()}


def _format_lines_or_str(val: list[str] | str, numbered: bool = False) -> str:
    if isinstance(val, str):
        return val.strip()
    if not val:
        return ""
    if numbered:
        return "\n".join(f"{i + 1}. {q}" for i, q in enumerate(val))
    return "\n".join(f"- {item}" for item in val)


def parse_banca_schema(text: str) -> BancaBulletinSchema:
    """Parse either JSON or Markdown into a validated Pydantic BancaBulletinSchema."""
    trimmed = text.strip()
    json_candidate = None
    if "```json" in trimmed:
        m = re.search(r"```json\s*(.*?)\s*```", trimmed, re.DOTALL)
        if m:
            json_candidate = m.group(1).strip()
    elif "```" in trimmed:
        m = re.search(r"```\s*(.*?)\s*```", trimmed, re.DOTALL)
        if m:
            json_candidate = m.group(1).strip()

    if not json_candidate:
        start_idx = trimmed.find("{")
        end_idx = trimmed.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_candidate = trimmed[start_idx : end_idx + 1]

    if json_candidate:
        try:
            return BancaBulletinSchema.model_validate_json(json_candidate)
        except Exception:
            pass

    sec = _split_sections(text)
    return BancaBulletinSchema(
        resumen=sec.get("resumen", ""),
        sectores=sec.get("sectores potencialmente relacionados", ""),
        horizonte=sec.get("horizonte temporal", ""),
        evidencia=sec.get("evidencia", ""),
        preguntas=sec.get("preguntas para el analista", ""),
    )


def build_banca_bulletin(
    docs: list[EvidenceDoc], synthesiser: Synthesiser | None = None
) -> dict:
    synth: Synthesis = (synthesiser or Synthesiser()).generate(INSTRUCTION, docs)
    if synth.abstained:
        return {
            "modalidad": "banca",
            "abstained": True,
            "reason": synth.reason,
            "text": synth.text,
            "sentence_breakdown": [],
            "sentences": [],
        }
    parsed: BancaBulletinSchema = parse_banca_schema(synth.text)
    resumen = cap_words(parsed.resumen, 250)
    allowed_ids = {d.source_id for d in docs}
    evidencia_str = _format_lines_or_str(parsed.evidencia, numbered=False)
    sectores_str = _format_lines_or_str(parsed.sectores, numbered=False)
    preguntas_str = _format_lines_or_str(parsed.preguntas, numbered=True)
    breakdown = extract_sentence_breakdown(
        sections={"resumen": resumen, "evidencia": evidencia_str},
        allowed_ids=allowed_ids,
    )
    return {
        "modalidad": "banca",
        "abstained": False,
        "resumen": resumen,
        "sectores": sectores_str,
        "horizonte": parsed.horizonte,
        "evidencia": evidencia_str,
        "preguntas": preguntas_str,
        "titular_only": synth.titular_only,
        "citations_valid": synth.citations_valid,
        "citations_dropped": synth.citations_dropped,
        "sentence_breakdown": breakdown,
        "sentences": breakdown,
        "prompt_tokens": synth.prompt_tokens,
        "completion_tokens": synth.completion_tokens,
        "total_tokens": synth.total_tokens,
        "latency_ms": synth.latency_ms,
        "raw": synth.text,
    }


def render_markdown(bulletin: dict, case_title: str = "") -> str:
    """Render the bulletin as review-ready Markdown."""
    if bulletin.get("abstained"):
        return f"# Boletín banca — {case_title}\n\n> {bulletin['text']}\n"
    lines = [
        f"# Boletín de entorno — {case_title or 'borrador'}",
        "",
        "> BORRADOR PARA REVISIÓN HUMANA — señales, no recomendaciones.",
    ]
    if bulletin.get("titular_only"):
        lines.append("> AVISO: basado únicamente en titular/metadatos.")
    lines += [
        "",
        f"## Resumen\n{bulletin['resumen']}",
        "",
        f"## Sectores\n{bulletin['sectores']}",
        "",
        f"## Horizonte\n{bulletin['horizonte']}",
        "",
        f"## Evidencia\n{bulletin['evidencia']}",
        "",
        f"## Preguntas\n{bulletin['preguntas']}",
    ]
    return "\n".join(lines) + "\n"
