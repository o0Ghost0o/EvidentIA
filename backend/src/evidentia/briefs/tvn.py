"""TVN editorial package builder (modalidad principal).

Output contract (challenge §3):
  brief ≤250 words, proposed title, public-interest angle, 3 research
  questions, sources + pending verifications, 45–60s script draft, digital
  copy ≤80 words. No invented interviews, quotes, images or claims.
"""

from __future__ import annotations

import re

from evidentia.generation.schemas import TvnBriefSchema
from evidentia.generation.synthesizer import (
    EvidenceDoc,
    Synthesis,
    Synthesiser,
    cap_words,
    extract_sentence_breakdown,
)

INSTRUCTION = """Redacta el paquete editorial en EXACTAMENTE este formato:

## Título propuesto
<una línea>

## Brief
<máximo 250 palabras: qué se reporta, quién lo reporta, qué está respaldado>

## Enfoque de interés público
<2-3 líneas>

## Preguntas de investigación
1. <pregunta>
2. <pregunta>
3. <pregunta>

## Fuentes y verificaciones pendientes
<viñetas con citas [id:campo] y qué falta comprobar>

## Guion 45-60 segundos
<texto locutable, sin atribuir declaraciones no citadas>

## Copy digital
<máximo 80 palabras>
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
            # Ignore template placeholder echoes like "<una línea>" or "<máximo 250 palabras: ...>"
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


def parse_tvn_schema(text: str) -> TvnBriefSchema:
    """Parse either JSON or Markdown into a validated Pydantic TvnBriefSchema."""
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
            return TvnBriefSchema.model_validate_json(json_candidate)
        except Exception:
            pass

    sec = _split_sections(text)
    return TvnBriefSchema(
        titulo_propuesto=sec.get("título propuesto", ""),
        brief=sec.get("brief", ""),
        enfoque=sec.get("enfoque de interés público", ""),
        preguntas=sec.get("preguntas de investigación", ""),
        fuentes_y_verificaciones=sec.get("fuentes y verificaciones pendientes", ""),
        guion=sec.get("guion 45-60 segundos", "") or sec.get("guion", ""),
        copy_digital=sec.get("copy digital", "") or sec.get("copy_digital", ""),
    )


def build_tvn_package(
    docs: list[EvidenceDoc], synthesiser: Synthesiser | None = None
) -> dict:
    synth: Synthesis = (synthesiser or Synthesiser()).generate(INSTRUCTION, docs)
    if synth.abstained:
        return {
            "modalidad": "tvn",
            "abstained": True,
            "reason": synth.reason,
            "text": synth.text,
            "sentence_breakdown": [],
            "sentences": [],
        }
    parsed: TvnBriefSchema = parse_tvn_schema(synth.text)
    brief = cap_words(parsed.brief, 250)
    copy = cap_words(parsed.copy_digital, 80)
    guion = parsed.guion
    allowed_ids = {d.source_id for d in docs}
    breakdown = extract_sentence_breakdown(
        sections={"brief": brief, "guion": guion, "copy_digital": copy},
        allowed_ids=allowed_ids,
    )
    preguntas_str = _format_lines_or_str(parsed.preguntas, numbered=True)
    fuentes_str = _format_lines_or_str(parsed.fuentes_y_verificaciones, numbered=False)

    return {
        "modalidad": "tvn",
        "abstained": False,
        "titulo_propuesto": parsed.titulo_propuesto,
        "brief": brief,
        "enfoque": parsed.enfoque,
        "preguntas": preguntas_str,
        "fuentes_y_verificaciones": fuentes_str,
        "guion": guion,
        "copy_digital": copy,
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


def render_markdown(package: dict, case_title: str = "") -> str:
    """Render the package as review-ready Markdown."""
    if package.get("abstained"):
        return f"# Borrador TVN — {case_title}\n\n> {package['text']}\n"
    lines = [
        f"# Paquete editorial — {case_title or 'borrador'}",
        "",
        "> BORRADOR PARA REVISIÓN HUMANA — no publicar sin verificación.",
    ]
    if package.get("titular_only"):
        lines.append("> AVISO: basado únicamente en titular/metadatos.")
    lines += [
        "",
        f"## Título propuesto\n{package['titulo_propuesto']}",
        "",
        f"## Brief\n{package['brief']}",
        "",
        f"## Enfoque\n{package['enfoque']}",
        "",
        f"## Preguntas\n{package['preguntas']}",
        "",
        f"## Fuentes y pendientes\n{package['fuentes_y_verificaciones']}",
        "",
        f"## Guion\n{package['guion']}",
        "",
        f"## Copy digital\n{package['copy_digital']}",
    ]
    return "\n".join(lines) + "\n"
