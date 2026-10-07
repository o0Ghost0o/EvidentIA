"""TVN editorial package builder (modalidad principal).

Output contract (challenge §3):
  brief ≤250 words, proposed title, public-interest angle, 3 research
  questions, sources + pending verifications, 45–60s script draft, digital
  copy ≤80 words. No invented interviews, quotes, images or claims.
"""

from __future__ import annotations

from evidentia.generation.synthesizer import (
    EvidenceDoc,
    Synthesis,
    Synthesiser,
    cap_words,
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
        if line.startswith("## "):
            current = line[3:].strip().lower()
            sections[current] = ""
        elif current:
            sections[current] += line + "\n"
    return {k: v.strip() for k, v in sections.items()}


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
        }
    sections = _split_sections(synth.text)
    brief = cap_words(sections.get("brief", ""), 250)
    copy = cap_words(sections.get("copy digital", ""), 80)
    return {
        "modalidad": "tvn",
        "abstained": False,
        "titulo_propuesto": sections.get("título propuesto", ""),
        "brief": brief,
        "enfoque": sections.get("enfoque de interés público", ""),
        "preguntas": sections.get("preguntas de investigación", ""),
        "fuentes_y_verificaciones": sections.get("fuentes y verificaciones pendientes", ""),
        "guion": sections.get("guion 45-60 segundos", ""),
        "copy_digital": copy,
        "titular_only": synth.titular_only,
        "citations_valid": synth.citations_valid,
        "citations_dropped": synth.citations_dropped,
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
