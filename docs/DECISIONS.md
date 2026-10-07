# EvidentIA — Decisiones técnicas y de producto

Registro de decisiones (ADR ligero). Cada decisión incluye fecha, contexto,
decisión adoptada, alternativas descartadas y consecuencias. Mínimo exigido por
el reto: 3 decisiones justificadas.

## D01 — 2026-10-07 — Stack principal del prototipo

- **Estado:** aceptada
- **Contexto:** El reto exige un prototipo ejecutable, reproducible y desplegable
  con un recorrido completo (ingesta → ranking → ficha → borrador → revisión).
- **Decisión:** Backend en Python 3.12 con FastAPI + SQLModel; **uv como único
  gestor de paquetes Python** (`pyproject.toml` + `uv.lock` fijado); vectores en Qdrant;
  frontend en Nuxt 3 (Vue 3, Vite, Shadcn-vue, TailwindCSS); trabajos en segundo
  plano con Dramatiq + Redis; PostgreSQL como fuente de verdad estructurada;
  nginx como proxy; todo orquestado con Docker Compose.
- **Alternativas descartadas:** notebook interactivo (válido para el reto pero sin
  la experiencia de "proyecto/árbol de evidencia" que propone la visión);
  Celery (más pesado que Dramatiq para este alcance).
- **Consecuencias:** Despliegue uniforme con `docker compose up --build`; contratos
  tipados entre capas; el worker permite ingestas largas sin bloquear la API.

## D02 — 2026-10-07 — Espacio de Proyecto en lugar de chat conversacional

- **Estado:** aceptada
- **Contexto:** La visión del producto prioriza auditabilidad: el periodista/analista
  debe ver de dónde viene cada afirmación y marcar evidencia manualmente.
- **Decisión:** La unidad de trabajo de la UI es el **Proyecto de
  Investigación/Evaluación** con árbol de evidencia navegable, ficha de verificación
  y estados de revisión humana. No se construye un chatbot genérico.
- **Alternativas descartadas:** chat "full agéntico" sobre el corpus (mayor riesgo
  de alucinación y menor trazabilidad exigible por la rúbrica).
- **Consecuencias:** El backend expone casos, evidencias vinculadas y briefs como
  recursos de primera clase; la generación siempre cita fuentes recuperadas.

## D03 — 2026-10-07 — Estrategia de LLM: Together.ai con degradación local controlada

- **Estado:** aceptada
- **Contexto:** La generación de briefs/boletines requiere un LLM, pero el despliegue
  debe funcionar "tal cual" y la demo debe sobrevivir sin internet (T10).
- **Decisión:** Proveedor por defecto Together.ai (configurable por `LLM_*` en `.env`).
  Si no hay API key o no hay conectividad, los endpoints de generación responden con
  una **abstención explícita estructurada** (no texto inventado) y el resto del
  sistema (ingesta, ranking, fichas, árbol) sigue operativo con el snapshot local.
- **Alternativas descartadas:** exigir API key para arrancar (rompe "desplegar tal
  cual" y T10); empaquetar un LLM local pesado por defecto (imagen Docker enorme,
  latencia alta en CPU).
- **Consecuencias:** Arranque sin secretos; T10 verificable; el costo/latencia del
  LLM se mide y documenta solo cuando hay key configurada.

## D04 — 2026-10-07 — Embeddings locales con FastEmbed (sin API key)

- **Estado:** aceptada
- **Contexto:** La recuperación semántica es la capacidad ML/NLP sustantiva del
  sistema y debe funcionar offline.
- **Decisión:** Embeddings generados localmente con FastEmbed
  (`BAAI/bge-base-en-v1.5` por defecto, configurable). Sin dependencia de APIs externas.
- **Alternativas descartadas:** embeddings vía API (rompen el modo offline y añaden
  costo por ingesta).
- **Consecuencias:** La imagen del backend incluye el runtime de embeddings; los
  modelos se descargan en el build para que `docker compose up` no requiera red.

## D05 — 2026-10-07 — Datos: descarga en vivo con snapshot congelado de respaldo

- **Estado:** aceptada
- **Contexto:** El reto pide datos públicos reproducibles (GDELT, Banco Mundial,
  USGS) más un `manifest.json` con hashes; la demo debe funcionar sin internet.
- **Decisión:** `scripts/fetch_seed_data.py` descarga el paquete en el primer arranque
  con internet; además se versiona un snapshot mínimo en `data/seed/` que se usa
  cuando `USE_SEED_SNAPSHOT=true` o no hay conectividad. El manifiesto registra
  versión, fecha de corte, consultas, conteos, licencias y SHA-256.
- **Alternativas descartadas:** solo-descarga (frágil en la demo); solo-snapshot
  (datos rancios, menos volumen para RAG).
- **Consecuencias:** Reproducibilidad doble: receta de descarga + snapshot congelado;
  T10 se prueba con el snapshot.

## D06 — 2026-10-07 — Superficie Notion como Markdown + script de sincronización

- **Estado:** aceptada
- **Contexto:** Notion Business es requisito de admisión, pero aún no hay token ni
  espacio provisionado al inicio del proyecto.
- **Decisión:** Mantener las 8 páginas obligatorias como Markdown en `docs/notion/`
  desde el día uno, y proveer `scripts/sync_notion.py` para publicarlas vía Notion
  API cuando existan `NOTION_TOKEN` y `NOTION_PARENT_PAGE_ID`.
- **Alternativas descartadas:** esperar al token para documentar (incumple "registro
  durante la ejecución"); automatizar la carga como paso obligatorio (el reto lo
  marca opcional).
- **Consecuencias:** La documentación es versionable en Git desde el inicio y la
  subida a Notion es un paso mecánico posterior.

## D07 — 2026-10-07 — Light GraphRAG relacional (sin base de grafos dedicada)

- **Estado:** aceptada
- **Contexto:** Se necesita procedencia (agencia vs medio), agrupación de eventos y
  árbol de evidencia, con despliegue simple en Compose.
- **Decisión:** Entidades y relaciones tipadas en PostgreSQL (SQLModel) + construcción
  del árbol/vecindario en memoria. Sin Neo4j ni servicio de grafos adicional.
- **Alternativas descartadas:** base de grafos dedicada (un servicio más que operar
  para un grafo de cientos de nodos).
- **Consecuencias:** Menos infraestructura; consultas de vecindario implementadas en
  la capa de servicio; migración futura posible si el grafo escala.
