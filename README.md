# EvidentIA — Copiloto de Entorno y Verificación Trazable

Prototipo para el reto **hackIAthon Panamá 4ta edición — TVN Media**
("De la señal a la decisión"): convierte noticias públicas e indicadores oficiales
en una bandeja de temas priorizados, fichas de evidencia y borradores con citas,
para decisión humana. Modalidad principal: **editorial TVN**; extensión: **boletín
bancario de entorno**.

En lugar de un chat genérico, EvidentIA organiza el trabajo en
**Proyectos de Investigación/Evaluación** con un árbol de evidencia auditable:
cada afirmación factual enlaza su fuente, fecha y alcance; sin evidencia suficiente,
el sistema se abstiene explícitamente.

## Stack

| Capa | Tecnología |
|------|------------|
| Backend | Python 3.12, FastAPI, SQLModel, Dramatiq + Redis |
| Datos | PostgreSQL (estructurado), Qdrant (vectores), FastEmbed local |
| IA | Multi-RAG + Light GraphRAG, LLM Together.ai (con abstención sin key/offline) |
| Frontend | Nuxt 3, Vue 3, Vite, Shadcn-vue, TailwindCSS |
| Deploy | Docker Compose + nginx, `docker compose up --build` |

## Arranque rápido

```bash
cp .env.example .env        # opcional: defaults funcionales incluidos
docker compose up --build  # o: make up
```

- App: <http://localhost:8080> · API directa: <http://localhost:8001> (docs en `/docs`)
- Sin `TOGETHER_API_KEY`, la generación responde abstención estructurada y el resto
  opera con el snapshot local (`USE_SEED_SNAPSHOT=true` para demo offline).
- Comandos: `make setup|dev|test|ingest|seed|benchmark|build|up|down|notion`.

## Desarrollo local (backend)

Gestor de paquetes: **uv** (único; dependencias fijadas en `backend/uv.lock`).

```bash
cd backend
uv sync                  # crea .venv local e instala dependencias fijadas
uv run pytest            # suite de tests
uv run uvicorn evidentia.main:app --reload   # API en http://localhost:8000
```

## Documentación

- Reto: [docs/reto/](docs/reto/) · Roadmap: [docs/ROADMAP.md](docs/ROADMAP.md)
- Cambios: [docs/CHANGELOG.md](docs/CHANGELOG.md) · Decisiones: [docs/DECISIONS.md](docs/DECISIONS.md)
- Páginas Notion (Markdown): [docs/notion/](docs/notion/) · Casos: [docs/casos/](docs/casos/)

## Contrato de datos

`noticias.csv`, `indicadores.csv`, `eventos.geojson`, `fichas.jsonl`, `manifest.json`
(SHA-256). Detalle de fuentes, licencias y transformaciones en
[docs/notion/03-catalogo-de-datos.md](docs/notion/03-catalogo-de-datos.md).
