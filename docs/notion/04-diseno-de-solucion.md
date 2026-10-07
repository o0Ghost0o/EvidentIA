# 04 — Diseño de Solución

> Página 4/8 del espacio Notion.

## Arquitectura

```
Fuentes públicas / snapshot → validación y normalización → almacenamiento
  → búsqueda y agrupación → motor de priorización → generación con evidencias
  → interfaz (Proyecto + árbol) → revisión humana → registro en Notion
```

| Capa | Tecnología |
|------|------------|
| API | FastAPI (Python 3.12), SQLModel, Pydantic Settings |
| Estructurado | PostgreSQL: noticias, indicadores, eventos, entidades, relaciones, casos, evidencias |
| Vectores | Qdrant: `news_children`/`news_parents`, `indicator_children`/`indicator_parents` |
| Embeddings | FastEmbed local (`BAAI/bge-base-en-v1.5`), sin API key |
| LLM | Together.ai por defecto (configurable); abstención estructurada sin key/offline |
| Cola | Dramatiq + Redis (ingestas y enriquecimientos) |
| Grafo | Light GraphRAG: relaciones en Postgres + árbol en memoria |
| Frontend | Nuxt 3, Vue 3, Vite, Shadcn-vue, TailwindCSS, TypeScript |
| Proxy/deploy | nginx + Docker Compose |

## Modelo de datos (SQLModel)

`NewsArticle`, `Indicator`, `GeoEvent`, `Entity`, `Relation`, `Case`,
`EvidenceItem`, `VerificationNote`. Relaciones tipadas: `mentions`, `same_event`,
`source_of`, `contradicts`, `corroborates`.

## Reglas

- **Scoring:** `P = 30R + 25I + 20U + 15N + 10E`, componentes 0–1 documentados;
  rangos bajo [0,40), medio [40,70), alto [70,100); desempate: urgencia, luego ID.
  Versión de reglas visible en `/ranking`.
- **Evidencia (independiente del puntaje):** insuficiente / parcial / suficiente
  para el borrador. Prioridad alta + evidencia insuficiente ⇒ investigar, no publicar.
- **Agencia vs medio:** N réplicas de una agencia = 1 procedencia; corroboración
  independiente solo con fuentes propias distintas.
- **Restricción titular:** si solo hay titular/metadatos, la salida lo declara
  ("basado únicamente en titular/metadatos"); no simula lectura completa.
- **Revisión humana:** nuevo → en revisión → requiere evidencia → aprobado como
  borrador / descartado. Aprobar ≠ publicar.

## Modelos, prompts y versiones

- Clasificación semántica / similitud / NER / recuperación semántica como capacidad
  ML/NLP sustantiva (mínimo una, documentada con baseline de palabras clave).
- Prompts de generación: instrucciones separadas del contenido de fuentes; salida
  estructurada con citas `[id_fuente:campo]` y vacíos; taxonomía
  hecho/declaración/inferencia/hipótesis.
- Se documentan proveedor, versión, parámetros, costo medido y limitaciones.

## Límites del sistema

Sin internet: retrieval + ranking + fichas con snapshot; generación LLM degradada a
abstención estructurada. Sin veredictos verdadero/falso. Sin datos personales ni
paywalls. Sin decisiones financieras automatizadas.
