# EvidentIA — Changelog

Registro de cada feature entregada y cada modificación al sistema, con timestamp
ISO 8601 (UTC), autor, descripción y archivos afectados.

## Convención

```markdown
## [YYYY-MM-DDTHH:MM:SSZ] Título corto
- **Autor:** AI | humano:<nombre>
- **Roadmap:** Fase X, tarea Y.Z (o "—" si no aplica)
- **Descripción:** qué cambió y por qué.
- **Archivos:** lista de rutas afectadas.
```

## Entradas

### [2026-10-07T00:00:00Z] Snapshot seed real + casos + métricas (2.7, 6.3–6.4, 7.5–7.6)

- **Autor:** AI
- **Roadmap:** Fase 2 tarea 2.7; Fase 6 tareas 6.3–6.4; Fase 7 tareas 7.5–7.6
- **Descripción:** Snapshot `data/seed/` con datos reales: 40 titulares TVN
  (feed `tvn-2.com/rss` descubierto y verificado, 151 entradas), 540 obs. Banco
  Mundial (6 países × 6 indicadores × 15 años), 82 sismos USGS 2024 + manifest
  SHA-256. GDELT bloqueado por 429 (reintento programado tras cooldown; el seed
  acepta merge incremental con `--only`). Endurecimiento: `fetchers/_http.py`
  (reintentos 10/30/90 s ante timeouts/429/5xx) en WB/USGS; `fetch_seed_data.py`
  con `--only` y merge. Benchmark 60 consultas construido. Ingesta seed e2e:
  9.9 s, 0 descartadas, 97 entidades + 98 relaciones. Ranking: 39 temas,
  ~10 ms. 5 fichas trazables (una con evidencia insuficiente). Scoring v1
  congelado con limitación documentada (D08). Suite: 48 passed.
- **Archivos:**
  - `data/seed/*`, `data/benchmark.jsonl`
  - `backend/src/evidentia/ingestion/fetchers/_http.py`, `worldbank.py`, `usgs.py`
  - `backend/src/evidentia/config.py` (`tvn_rss_url` por defecto)
  - `scripts/fetch_seed_data.py`, `.env.example`
  - `docs/casos/caso_001.md` … `caso_005.md`, `docs/DECISIONS.md` (D08)
  - `docs/notion/03-catalogo-de-datos.md`, `05-casos-y-evidencias.md`,
    `06-pruebas-y-metricas.md`

### [2026-10-07T00:00:00Z] Fase 7 (parcial): proxy, Makefile, sync Notion, benchmark builder

- **Autor:** AI
- **Roadmap:** Fase 7, tareas 7.1–7.4 hechas (7.2 pendiente de `up` real sin Docker);
  7.5–7.6 esperan el snapshot 2.7
- **Descripción:** nginx (`:8080` app, `:8001` API) + servicio `proxy` en compose;
  `Makefile` con 10 targets; `scripts/sync_notion.py` (166 bloques en dry-run,
  subida real pendiente de token); `scripts/build_benchmark.py` (60 consultas,
  se ejecuta al completar 2.7); README con puertos finales y make.
- **Archivos:** `docker/nginx.conf`, `docker/Dockerfile.proxy`,
  `docker-compose.yml`, `Makefile`, `scripts/sync_notion.py`,
  `scripts/build_benchmark.py`, `README.md`

### [2026-10-07T00:00:00Z] Fase 5: frontend Nuxt (build verificado; smoke en vivo bloqueado por sandbox)

- **Autor:** AI
- **Roadmap:** Fase 5, tareas 5.1–5.5
- **Descripción:** Nuxt 3 + Vite + Tailwind + componentes estilo Shadcn (Button,
  Badge, Card, Input, Textarea); páginas bandeja (`/`), proyectos (`/projects`),
  workspace (`/projects/[id]`: árbol, evidencias, borrador, revisión),
  ingesta (`/ingest`); BFF `server/api/[...path].ts` hacia FastAPI;
  descarga de brief en Markdown; `frontend/Dockerfile` (npm, dos etapas) y
  servicio `frontend` en compose. Toolchain: **npm** (bun bloqueado por EPERM en
  este entorno; `package-lock.json` versionado). Verificación: `nuxt build` OK
  (bundle 2.9 MB); el smoke del dev-server no es posible aquí (el sandbox niega
  bind de puertos) — arranque local pendiente de verificar en máquina del usuario
  con `npm run dev` → <http://localhost:3000>.
- **Archivos:** `frontend/` (package.json, nuxt.config, tailwind, Dockerfile,
  .env.example, app/layouts/pages/components/server/composables), `docker-compose.yml`

### [2026-10-07T00:00:00Z] Fase 6 (parcial): suite de aceptación T01–T10 en verde

- **Autor:** AI
- **Roadmap:** Fase 6, tareas 6.1–6.2 hechas; 6.3–6.4 pendientes del snapshot
- **Descripción:** `backend/tests/test_acceptance.py` con los 10 casos del reto;
  cambio de producto: `title_tokens` ignora tokens puramente numéricos para que
  variantes numéricas agrupen y sus diferencias emerjan como `contradicts`
  (test de regresión en `test_graph.py`). Suite total: 48 passed.
  Pendiente: `data/benchmark.jsonl` (60 consultas, se construye desde el snapshot
  cuando 2.7 complete) y tabla de métricas observadas.
- **Archivos:** `backend/tests/test_acceptance.py`, `test_graph.py`,
  `backend/src/evidentia/graph/relations.py`

### [2026-10-07T00:00:00Z] Fase 4: scoring, casos y generación TVN/Banca

- **Autor:** AI
- **Roadmap:** Fase 4, tareas 4.1–4.7
- **Descripción:** Scoring `P=30R+25I+20U+15N+10E` (reglas v1 documentadas,
  bandas sin solape, desempate U→ID); estados de evidencia independientes;
  etiquetas repetición/corroboración/single + `contradicts` numérico heurístico
  (misma unidad, distinto valor) cableado al grafo; `GET /ranking`;
  CRUD de casos + evidencias + notas de revisión (5 estados, la nota mueve el
  estado); `GET /cases/{id}/tree` y `GET /evidence/tree`; sintetizador Together.ai
  con fuentes envueltas como datos, taxonomía HECHO/DECLARACIÓN/INFERENCIA/
  HIPÓTESIS, validación de citas (ids desconocidos removidos y reportados) y
  abstención estructurada (sin key / sin evidencia / fallo proveedor);
  builders TVN (brief 250, guion, copy 80) y Banca (boletín 250) con topes
  verificados y render Markdown. Suite: 37 passed.
- **Archivos:**
  - `backend/src/evidentia/scoring/__init__.py`, `score.py`, `deduplication.py`
  - `backend/src/evidentia/generation/__init__.py`, `synthesizer.py`
  - `backend/src/evidentia/briefs/__init__.py`, `tvn.py`, `banca.py`
  - `backend/src/evidentia/api/ranking.py`, `api/cases.py`, `api/evidence.py`, `main.py`
  - `backend/src/evidentia/graph/relations.py` (contradicts)
  - `backend/tests/test_scoring.py`, `test_generation.py`, `test_cases_api.py`

### [2026-10-07T00:00:00Z] Fase 3: Multi-RAG + Light GraphRAG

- **Autor:** AI
- **Roadmap:** Fase 3, tareas 3.1–3.7
- **Descripción:** 4 colecciones Qdrant (noticias/indicadores × hijos/padres) con
  docstore persistente; FastEmbed lazy + HashEmbeddings deterministas para tests;
  chunking padre/hijo con metadatos de trazabilidad; ParentChildRetriever y
  MultiRAGRetriever (índices A+B); indexación idempotente con borrado por root_id;
  NER spaCy `es_core_news_sm` con fallback regex; detección de agencias
  (EFE/Reuters/AFP/AP/DPA/Xinhua/Europa Press); agrupación de eventos por Jaccard;
  relaciones same_event/source_of/corroborates/mentions; persistencia relacional +
  árbol de evidencia NetworkX; `count_primary_sources` (CU-03: N réplicas = 1 fuente).
  `contradicts` se almacena/sirve pero su regla de detección llega con extracción de
  claims (Fase 4). Hooks post-ingesta (index+grafo) best-effort en pipeline.
  Suite: 17 passed (Qdrant `:memory:`).
- **Archivos:**
  - `backend/src/evidentia/retrieval/__init__.py`, `embeddings.py`, `store.py`,
    `chunking.py`, `retriever.py`, `indexing.py`
  - `backend/src/evidentia/graph/__init__.py`, `entities.py`, `relations.py`,
    `graph_service.py`
  - `backend/src/evidentia/ingestion/pipeline.py` (hooks), `backend/src/evidentia/main.py`
  - `backend/tests/test_retrieval.py`, `backend/tests/test_graph.py`

### [2026-10-07T00:00:00Z] Fase 2: ingesta, validación y manifest (código; snapshot en curso)

- **Autor:** AI
- **Roadmap:** Fase 2, tareas 2.1–2.6 hechas; 2.7 en curso (fetch del snapshot
  afectado por rate-limit 429 de GDELT; reintento en marcha)
- **Descripción:** Fetchers GDELT (throttle 8 s + backoff 30/90/240 s ante 429),
  World Bank (6 países × 6 indicadores × 2010–2024, nulos explícitos), USGS
  (GeoJSON 2024, caja regional) y TVN RSS (opcional por `TVN_RSS_URL`); validadores
  T01 (fechas inválidas/nulos no bloquean, solo faltas de identidad descartan);
  `manifest.json` con SHA-256; pipeline fetch→validate→files→DB→manifest+reporte;
  actor Dramatiq + servicio `worker` en compose; `POST /ingest/run` (sync/async),
  `GET /ingest/quality-report`; `scripts/fetch_seed_data.py` tolerante a fallos
  parciales. Suite: 10 passed.
- **Archivos:**
  - `backend/src/evidentia/ingestion/fetchers/*.py`, `validators.py`, `manifest.py`,
    `pipeline.py`, `dramatiq_actors.py`
  - `backend/src/evidentia/api/ingest.py`, `config.py` (`tvn_rss_url`), `main.py`
  - `backend/tests/conftest.py`, `backend/tests/test_ingestion.py`
  - `scripts/fetch_seed_data.py`, `docker-compose.yml` (worker), `.env.example`
  - `.gitignore` (nuevo), `README.md` (uv como único gestor)

### [2026-10-07T00:00:00Z] Fase 1: bootstrap del backend y base de datos

- **Autor:** AI
- **Roadmap:** Fase 1, tareas 1.1–1.7 (1.5 parcial: compose con infra+backend; worker/frontend/nginx crecen en Fases 2/5/7)
- **Descripción:** FastAPI + SQLModel + pydantic-settings con defaults desplegables;
  8 modelos (noticias, indicadores, eventos, entidades, relaciones, casos, evidencias,
  notas); `/health` y `/ready`; `docker-compose.yml` (postgres, qdrant, redis, backend);
  `.env.example`; `backend/Dockerfile` (uv, spaCy `es_core_news_sm` en build);
  `uv.lock` (205 paquetes); 3 smoke tests en verde. `docker compose up` pendiente de
  verificación (sin Docker en este entorno).
- **Archivos:**
  - `backend/pyproject.toml`, `backend/uv.lock`, `backend/Dockerfile`
  - `backend/src/evidentia/__init__.py`, `config.py`, `db.py`, `models.py`, `main.py`
  - `backend/src/evidentia/api/__init__.py`, `api/health.py`
  - `backend/tests/test_smoke.py`
  - `docker-compose.yml`, `.env.example`

### [2026-10-07T00:00:00Z] Fase 0: esqueleto de documentación y roadmap inicial

- **Autor:** AI
- **Roadmap:** Fase 0, tareas 0.1–0.6
- **Descripción:** Se crea la carpeta `docs/`, se copia el PDF del reto a
  `docs/reto/`, y se redactan `ROADMAP.md` (v1.0.0), `CHANGELOG.md`,
  `DECISIONS.md`, las 8 páginas Notion en Markdown y el `README.md` del proyecto.
- **Archivos:**
  - `docs/reto/hackIAthon - reto TVN Media.pdf`
  - `docs/ROADMAP.md`
  - `docs/CHANGELOG.md`
  - `docs/DECISIONS.md`
  - `docs/notion/01-inicio-del-reto.md`
  - `docs/notion/02-plan-y-decisiones.md`
  - `docs/notion/03-catalogo-de-datos.md`
  - `docs/notion/04-diseno-de-solucion.md`
  - `docs/notion/05-casos-y-evidencias.md`
  - `docs/notion/06-pruebas-y-metricas.md`
  - `docs/notion/07-riesgos-y-etica.md`
  - `docs/notion/08-presentacion-al-jurado.md`
  - `README.md`
