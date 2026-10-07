"""Banca environment bulletin builder (extension).

Output contract (challenge §3): summary ≤250 words, potentially related
sectors, time horizon, evidence, 3 analyst questions. Observation separated
from impact hypotheses; no buy/sell advice, no inferred losses/defaults.
"""

from __future__ import annotations

from evidentia.generation.synthesizer import (
    EvidenceDoc,
    Synthesis,
    Synthesiser,
    cap_words,
)

INSTRUCTION = """Redacta el boletín de entorno en EXACTAMENTE este formato:

## Resumen
<máximo 250 palabras: señales observadas en fuentes públicas>

## Sectores potencialmente relacionados
<viñetas>

## Horizonte temporal
<línea: corto/mediano/largo plazo según las fuentes>

## Evidencia
<viñetas con citas [id:campo]; separa OBSERVACIÓN de HIPÓTESIS DE IMPACTO>

## Preguntas para el analista
1. <pregunta>
2. <pregunta>
3. <pregunta>

Prohibido: recomendar compra/venta, inferir pérdidas, impagos o exposición de carteras.
"""


def _split_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = ""
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip().lower()
            sections[current] = ""
        elif current:
            sections[current] += line + "\n"
    return {k: v.strip() for k, v in sections.items()}


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
        }
    sections = _split_sections(synth.text)
    return {
        "modalidad": "banca",
        "abstained": False,
        "resumen": cap_words(sections.get("resumen", ""), 250),
        "sectores": sections.get("sectores potencialmente relacionados", ""),
        "horizonte": sections.get("horizonte temporal", ""),
        "evidencia": sections.get("evidencia", ""),
        "preguntas": sections.get("preguntas para el analista", ""),
        "titular_only": synth.titular_only,
        "citations_valid": synth.citations_valid,
        "citations_dropped": synth.citations_dropped,
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
