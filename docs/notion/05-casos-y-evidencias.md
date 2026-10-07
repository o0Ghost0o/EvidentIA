# 05 — Casos y Evidencias

> Página 5/8 del espacio Notion. Mínimo exigido: 5 fichas trazables, incluyendo un
> caso sin evidencia suficiente. Fichas fuente en `docs/casos/caso_*.md`.

## Fichas

| ID | Modalidad | Tema | Puntaje (R/I/U/N/E) | Evidencia | Revisión | Revisora |
|----|-----------|------|---------------------|-----------|----------|----------|
| caso_001 | TVN | Traslados presupuestarios ~$100M | 60.5 (0.3/0.5/1.0/1.0/0.4) | parcial | en revisión | editora-demo |
| caso_002 | TVN | Aprehensión exdirector CSS | 60.5 (0.3/0.5/1.0/1.0/0.4) | parcial | en revisión | editora-demo |
| caso_003 | TVN | Caso Pandora: detención provisional | 60.5 (0.3/0.5/1.0/1.0/0.4) | parcial | en revisión | editora-demo |
| caso_004 | TVN | Rating del noticiero (consulta sin corpus) | n/a | insuficiente | requiere evidencia | editora-demo |
| caso_005 | Banca | Obra pública MOP + PIB Panamá | 60.5 (0.3/0.5/1.0/1.0/0.4) | suficiente | en revisión | analista-demo |

Fichas fuente: `docs/casos/caso_001.md` … `docs/casos/caso_005.md` (verificadas
contra `data/seed/` del 2026-10-07: 40 noticias TVN, 540 obs. Banco Mundial,
82 eventos USGS; GDELT pendiente de cuota 429).

## Formato de ficha (contrato `fichas.jsonl`)

`id_caso, modalidad, ids_fuente, afirmaciones, citas, puntaje, componentes,
estado_evidencia, borrador, estado_revision.`

Cada ficha incluye: qué se reporta, quién lo reporta, qué está respaldado, qué falta
comprobar y qué acción se recomienda; el borrador cita por afirmación y distingue
hechos, declaraciones, inferencias e hipótesis.
