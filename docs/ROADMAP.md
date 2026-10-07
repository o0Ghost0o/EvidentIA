# EvidentIA — Roadmap de Ejecución Estratégica

> **Reto:** hackIAthon Panamá 4ta edición — TVN Media ("De la señal a la decisión")
> **Producto:** Copiloto de Entorno y Verificación Trazable
> **Versión del roadmap:** v1.0.0 — 2026-10-07T00:00:00Z (versión inicial, ITMT)
> **Fuente del reto:** [docs/reto/hackIAthon - reto TVN Media.pdf](reto/hackIAthon%20-%20reto%20TVN%20Media.pdf)

Cualquier modificación a este roadmap se registra en la sección
[Registro de modificaciones](#registro-de-modificaciones) con timestamp ISO 8601.
Cada entrega se registra además en [CHANGELOG.md](CHANGELOG.md) y las
decisiones técnicas en [DECISIONS.md](DECISIONS.md).

---

## 1. Visión General del Producto: *Copiloto de Entorno y Verificación Trazable*

- **Core conceptual:** En lugar de un simple chat conversacional ("full agéntico"),
  el flujo se basa en un **Espacio de Proyecto / Ficha de Evaluación**. El usuario
  inicia un caso/tema, el sistema explora el grafo de procedencia y evidencia, y
  construye un árbol de relaciones verificables donde el analista/periodista puede
  auditar y marcar evidencias manualmente.
- **Flujo de ingesta/categorización:** tipo Zendesk/knowledge base de noticias —
  bandeja de entrada priorizada con scoring determinista y reproducible.
- **Reducción de ruido en RAG:** filtrado estructurado por proyectos, mapas/árboles
  de evidencia y trazabilidad estricta (toda afirmación factual cita ID/fuente/fecha).
- **Cumplimiento de rúbrica:** cero alucinación, abstención explícita ante falta de
  evidencia, trazabilidad obligatoria y documentación en **Notion Business**.

---

## 2. Mapa de fases

```
[ FASE 1: Setup & Ingesta ] ──> [ FASE 2: Multi-RAG & Light Graph ] ──> [ FASE 3: UI de Proyecto ] ──> [ FASE 4: Notion & Pitch ]
   - Notion (8 páginas)            - Ingesta de fuentes comunes             - Árbol de evidencia (grafo)   - Matriz T01-T10
   - Calidad del snapshot          - Cálculo score determinista             - Ficha de verificación        - Demo ejecutable
   - Manifest & Hashes             - Filtro de agencias vs medios           - Borrador (TVN/Banca)         - Guion de 10 min
```

### Fase 1: Setup de Infraestructura, Calidad de Datos y Notion (T0)

1. **Configuración de Notion Business (requisito de admisión):**
   Crear la estructura auditada de 8 páginas: *Inicio del Reto*, *Plan y Decisiones*
   (mínimo 8 tareas y 3 decisiones justificadas), *Catálogo de Datos*,
   *Diseño de Solución*, *Casos y Evidencias*, *Pruebas y Métricas*,
   *Riesgos y Ética*, y *Presentación al Jurado*.
2. **Pipeline de Ingesta y Reporte de Calidad (Etapa 1 del prototipo):**
   Carga de fuentes (`noticias.csv`, `indicadores.csv`, `eventos.geojson`).
   Validación automática: verificación de IDs, URLs, fechas, nulos y emisión del
   reporte con hashes SHA-256 (`manifest.json`).

### Fase 2: Motor Multi-RAG + Light GraphRAG (El Cerebro)

1. **Doble Recuperador Vectorial (Multi-RAG):**
   - **Índice A:** Noticias y actualidad local/macroeconómica.
   - **Índice B:** Indicadores oficiales estructurados y contexto normativo.
2. **Capa Relacional / Light GraphRAG (entidades y relaciones en SQL + grafo en memoria):**
   - Resolver el problema de **repetición vs. corroboración independiente**
     (detectar si varias notas replican una misma agencia como EFE/Reuters;
     contabilizar 1 sola fuente primaria).
   - Cruces controlados entre eventos/noticias e indicadores económicos sin forzar
     correlaciones artificiales.
3. **Scoring Determinista y Detección de Contradicciones:**
   - Implementación de la fórmula de priorización reproducible para la bandeja de entrada.
   - Reglas de abstención explícita si la evidencia es insuficiente o basada solo en titulares.

### Fase 3: Experiencia de Usuario basada en "Proyectos" y Árbol de Evidencias

1. **Espacio de Trabajo / Proyecto:**
   - El analista abre un "Proyecto de Investigación/Evaluación".
   - Visualización del grafo como un árbol o mapa de procedencia: artículos vinculados,
     entidades y fuentes primarias.
2. **Marcado y Ficha de Evidencia:**
   - Posibilidad de marcar nodos como evidencia corroborada de forma visual/manual.
   - Generación de la ficha técnica con citas estructuradas y enlaces a fuentes.
3. **Salida Específica de la Modalidad:**
   - **TVN (Editorial):** Propuesta de titulares contextualizados, resumen web y copys
     sociales con advertencia de revisión.
   - **Banca (Extensión):** Señales de entorno, impacto en sectores y preguntas para seguimiento.

### Fase 4: Pruebas Rigurosas, Banco de Casos y Pitch Final

1. **Ejecución y Documentación de Pruebas (T01–T10):**
   Casos de prueba obligatorios: deduplicación, abstención ante falta de datos,
   resistencia a prompt injection y latencia medible. Asegurar el modo offline/fallback
   local requerido por el jurado.
2. **Población de Casos en Notion:**
   Registrar al menos 5 fichas trazables completas (incluyendo obligatoriamente un caso
   con evidencia insuficiente).
3. **Pitch de 10 Minutos (Desde Notion):**
   Estructurar el recorrido exacto: 1 min problema y usuario, 1 min datos públicos,
   4 min demo interactiva (mostrando el árbol de evidencias, las citas y el caso de
   abstención), 2 min arquitectura/baseline, 1 min impacto/valor y 1 min límites/próximos pasos.

---

## 3. Plan operativo detallado (checklist de ejecución)

Estados: `pendiente` · `en-progreso` · `hecho` · `modificado`

### Fase 0 — Documentación inicial y roadmap

| # | Tarea | Estado |
|---|-------|--------|
| 0.1 | Crear carpeta `docs/` y copiar el PDF del reto a `docs/reto/` | hecho (2026-10-07) |
| 0.2 | Crear `docs/ROADMAP.md` (este archivo) | hecho (2026-10-07) |
| 0.3 | Crear `docs/CHANGELOG.md` con convención de registro | hecho (2026-10-07) |
| 0.4 | Crear `docs/DECISIONS.md` con decisiones iniciales | hecho (2026-10-07) |
| 0.5 | Crear las 8 páginas Notion en Markdown (`docs/notion/`) | hecho (2026-10-07) |
| 0.6 | Actualizar `README.md` con visión, stack y arranque | hecho (2026-10-07) |

### Fase 1 — Bootstrap del backend y base de datos

| # | Tarea | Estado |
|---|-------|--------|
| 1.1 | `backend/pyproject.toml` con dependencias fijadas | hecho (2026-10-07) |
| 1.2 | `config.py` con defaults desplegables (Qdrant/Postgres/Redis locales) | hecho (2026-10-07) |
| 1.3 | `db.py` con engine SQLModel, sesiones y lifespan | hecho (2026-10-07) |
| 1.4 | Modelos SQLModel: noticias, indicadores, eventos, entidades, relaciones, casos, evidencias, notas | hecho (2026-10-07) |
| 1.5 | `docker-compose.yml`: postgres, qdrant, redis, backend (+worker/frontend/nginx en Fases 2/5/7) | hecho parcial (2026-10-07) |
| 1.6 | `.env.example` con defaults funcionales | hecho (2026-10-07) |
| 1.7 | Endpoint `GET /health` y arranque limpio con `docker compose up --build` | hecho (2026-10-07) |

### Fase 2 — Ingesta, validación y manifest

| # | Tarea | Estado |
|---|-------|--------|
| 2.1 | Fetchers: GDELT (noticias), Banco Mundial (indicadores), USGS (sismos) | hecho (2026-10-07) |
| 2.2 | Validadores: IDs, URLs, fechas ISO 8601, nulos, UTF-8 | hecho (2026-10-07) |
| 2.3 | Generar `noticias.csv`, `indicadores.csv`, `eventos.geojson`, `fichas.jsonl` | hecho (2026-10-07) |
| 2.4 | Generar `manifest.json` con SHA-256 y metadatos de corte | hecho (2026-10-07) |
| 2.5 | `POST /ingest/run` (encola trabajo Dramatiq) | hecho (2026-10-07) |
| 2.6 | `GET /ingest/quality-report` | hecho (2026-10-07) |
| 2.7 | Snapshot mínimo offline en `data/seed/` (T10) | en-progreso (2026-10-07) |

### Fase 3 — Multi-RAG + Light GraphRAG

| # | Tarea | Estado |
|---|-------|--------|
| 3.1 | Colecciones Qdrant: noticias e indicadores (hijos + padres) | hecho (2026-10-07) |
| 3.2 | Chunking + embeddings locales (FastEmbed) | hecho (2026-10-07) |
| 3.3 | Indexación con metadatos de trazabilidad | hecho (2026-10-07) |
| 3.4 | MultiRAGRetriever: doble índice + distinción agencia vs medio + agrupación | hecho (2026-10-07) |
| 3.5 | Extracción de entidades (spaCy + reglas) | hecho (2026-10-07) |
| 3.6 | Entidades/relaciones en PostgreSQL + grafo en memoria | hecho (2026-10-07) |
| 3.7 | Servicio de árbol de evidencia (nodos + aristas tipadas) | hecho (2026-10-07) |

### Fase 4 — Scoring, casos y generación

| # | Tarea | Estado |
|---|-------|--------|
| 4.1 | Scoring `P = 30R + 25I + 20U + 15N + 10E` con componentes explicados | hecho (2026-10-07) |
| 4.2 | Deduplicación: repetición vs corroboración independiente | hecho (2026-10-07) |
| 4.3 | `GET /ranking` | hecho (2026-10-07) |
| 4.4 | CRUD de casos/proyectos + vinculación de evidencias | hecho (2026-10-07) |
| 4.5 | Generadores TVN (brief 250 palabras, guion, copy) y Banca (boletín) | hecho (2026-10-07) |
| 4.6 | Sintetizador con citas `[id_fuente:campo]` y abstención explícita | hecho (2026-10-07) |
| 4.7 | Estados de revisión humana (5 estados del reto) | hecho (2026-10-07) |

### Fase 5 — Frontend

| # | Tarea | Estado |
|---|-------|--------|
| 5.1 | Nuxt 3 + Vite + Tailwind + Shadcn-vue | hecho (2026-10-07) |
| 5.2 | Páginas: dashboard, proyectos, workspace, ingesta, brief | hecho (2026-10-07) |
| 5.3 | Componentes: RankingTable, EvidenceTree, CaseCard, BriefView, IngestPanel | hecho (2026-10-07) |
| 5.4 | BFF Nuxt (`server/api/*`) como proxy al backend | hecho (2026-10-07) |
| 5.5 | Exportación de ficha/brief a Markdown | hecho (2026-10-07) |

### Fase 6 — Tests y métricas

| # | Tarea | Estado |
|---|-------|--------|
| 6.1 | Tests de aceptación T01–T10 | hecho (2026-10-07) |
| 6.2 | Tests unitarios: scoring, deduplicación, grafo, retrieval | hecho (2026-10-07) |
| 6.3 | `data/benchmark.jsonl` (60 consultas) | pendiente |
| 6.4 | Métricas: citas, abstención, agrupación, Precision@5, latencia/costo | pendiente |

### Fase 7 — Deploy, casos y pitch

| # | Tarea | Estado |
|---|-------|--------|
| 7.1 | Dockerfiles multistage (backend + frontend) | pendiente |
| 7.2 | Compose final con healthchecks y volúmenes | pendiente |
| 7.3 | Makefile: setup, dev, test, ingest, build, up, down | pendiente |
| 7.4 | `scripts/sync_notion.py` | pendiente |
| 7.5 | 5 fichas trazables en `docs/casos/` (una con evidencia insuficiente) | pendiente |
| 7.6 | Pitch de 10 min en `docs/notion/08-presentacion-al-jurado.md` | pendiente |

---

## 4. Criterio de terminación global

- `docker compose up --build` levanta backend, worker Dramatiq, frontend, Qdrant,
  Redis, Postgres y nginx sin intervención manual (solo `.env` opcional).
- La suite `pytest` pasa T01–T10.
- La UI permite cargar datos, ver ranking, abrir una ficha, generar un brief/boletín
  y exportar la ficha como Markdown.
- `docs/` contiene el PDF del reto, roadmap, changelog, decisiones y las 8 páginas Notion.

---

## 5. Registro de modificaciones

| Timestamp (UTC) | Autor | Cambio |
|-----------------|-------|--------|
| 2026-10-07T00:00:00Z | AI | Fases 2 (código) y 3 hechas; `contradicts` difiere su regla a Fase 4; seed 2.7 en curso por 429 de GDELT. |
| 2026-10-07T00:00:00Z | AI | Fase 1 hecha: compose crece por fases (worker→F2, frontend→F5, nginx→F7) para que cada fase verifique `up --build` en verde. |
| 2026-10-07T00:00:00Z | AI | Versión inicial v1.0.0 (ITMT): roadmap estratégico + plan operativo Fases 0–7. |
