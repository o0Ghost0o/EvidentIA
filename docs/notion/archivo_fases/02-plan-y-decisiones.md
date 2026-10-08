# 02 — Plan y Decisiones

> Página 2/8 del espacio Notion. Mínimo exigido: 8 tareas y 3 decisiones justificadas.

## Backlog (estado inicial 2026-10-07)

| # | Tarea | Responsable | Estado |
|---|-------|-------------|--------|
| 1 | Esqueleto `docs/` + roadmap + changelog + decisiones | AI | hecho |
| 2 | Bootstrap backend (FastAPI, SQLModel, config, compose, `/health`) | AI | pendiente |
| 3 | Ingesta GDELT/Banco Mundial/USGS + validadores + `manifest.json` | AI | pendiente |
| 4 | Snapshot offline `data/seed/` + reporte de calidad | AI | pendiente |
| 5 | Multi-RAG (Qdrant doble índice) + embeddings locales | AI | pendiente |
| 6 | Light GraphRAG: entidades, relaciones, agencia-vs-medio, árbol de evidencia | AI | pendiente |
| 7 | Scoring `P=30R+25I+20U+15N+10E`, ranking y casos/proyectos | AI | pendiente |
| 8 | Generación TVN (brief/guion/copy) + Banca (boletín) con citas y abstención | AI | pendiente |
| 9 | Frontend Nuxt: dashboard, workspace, árbol, ficha, ingesta, export Markdown | AI | pendiente |
| 10 | Suite T01–T10 + benchmark 60 consultas + métricas | AI | pendiente |
| 11 | Docker final + Makefile + `sync_notion.py` + 5 fichas + pitch | AI | pendiente |

Cronología: ver [docs/ROADMAP.md](../ROADMAP.md) (Fases 0–7) y
[docs/CHANGELOG.md](../CHANGELOG.md) para el registro fechado de avances.

## Decisiones (resumen; detalle en `docs/DECISIONS.md`)

1. **D01 — Stack:** FastAPI + SQLModel + Qdrant + Nuxt + Dramatiq + Postgres + Redis
   en Docker Compose. Despliegue uniforme, contratos tipados, ingestas asíncronas.
2. **D02 — Espacio de Proyecto, no chatbot:** la UI se organiza en proyectos de
   investigación con árbol de evidencia auditable; reduce alucinación exigible.
3. **D03 — LLM Together.ai con abstención estructurada sin key/offline:** arranque sin
   secretos, T10 verificable, resto del sistema operativo con snapshot local.
4. **D04 — Embeddings locales (FastEmbed):** recuperación semántica offline, sin costo.
5. **D05 — Descarga en vivo + snapshot congelado:** reproducibilidad doble (receta + datos).
6. **D06 — Notion como Markdown + script de sync:** documentación versionada desde el día uno.
7. **D07 — Light GraphRAG relacional:** entidades/relaciones en PostgreSQL, sin servicio
   de grafos adicional.
