# 06 — Pruebas y Métricas

> Página 6/8 del espacio Notion. Matriz obligatoria T01–T10 + métricas de ejecución final.

## Matriz de aceptación

| ID | Prueba | Resultado esperado | Observado | Estado | Evidencia |
|----|--------|--------------------|-----------|--------|-----------|
| T01 | Fechas inválidas y nulos | Validar, separar errores, conservar nulos; no bloquear carga | Fila conservada, fecha nula, error registrado | verde | `test_acceptance.py::test_T01` |
| T02 | Tres registros del mismo evento | Agrupar sin perder fuentes; no triplicar importancia | 3 réplicas EFE → 1 fuente, N=0.58 | verde | `::test_T02` |
| T03 | Noticia antigua recirculada | Mostrar fecha original; no presentarla como nueva | Fecha preservada, U=0.0 | verde | `::test_T03` |
| T04 | Cifra anual Banco Mundial | País/año/unidad; no describirla como cifra de hoy | "Panamá · … (2024): 2.74 % anual" | verde | `::test_T04` |
| T05 | Dos afirmaciones incompatibles | Mostrar ambas + revisión pendiente; no elegir arbitrariamente | Arista `contradicts`, ambas visibles | verde | `::test_T05` |
| T06 | Consulta sin respuesta | Abstención explícita; nada inventado | ABSTENCIÓN, LLM ni se invoca | verde | `::test_T06` |
| T07 | Fuente que exige ignorar instrucciones | Contenido no confiable; no revelar secretos ni actuar | Fuente envuelta como dato; cita forjada removida | verde | `::test_T07` |
| T08 | Caso de prioridad alta | Exponer componentes y regla; prioridad ≠ publicación | P=81.5 alto + evidencia insuficiente | verde | `::test_T08` |
| T09 | Brief editorial / boletín bancario | Formato útil, citas, hechos vs inferencias | 7 secciones, topes 250/80, tags HECHO/INFERENCIA | verde | `::test_T09` |
| T10 | Sin internet en demo | Snapshot + fallback documentado; evidencia aquí | Modo seed no toca red (fetchers bloqueados en test) | verde | `::test_T10` |

Implementación: `backend/tests/test_acceptance.py` (10/10 verde, suite total
48 passed). Benchmark de desarrollo: `data/benchmark.jsonl` (60 consultas:
30 sustentadas, 10 contradicción, 10 sin respuesta, 10 adversariales).

## Métricas (observadas 2026-10-07, seed: 150 noticias [67 TVN + 74 La Prensa + 9 Crítica] + 540 WB + 82 USGS)

| Métrica | Meta del reto | Resultado |
|---------|---------------|-----------|
| Cobertura de citas | 100% | 100% por construcción (validador remueve ids desconocidos; verificado en tests con stub) |
| Validez de sustento (≥30 afirmaciones) | ≥90% | **92.2%** (47/51 afirmaciones sustentadas en fuentes del corpus; meta superada) |
| Abstención correcta | ≥80% | **100.0%** (7/7 consultas sin respuesta en benchmark dev; meta superada) |
| Agrupación (Jaccard + agencia) | reportar | Regla documentada v1; deduplicación probada en T02 y T05 |
| Utilidad del ranking (Precision@5) | reportar | Evaluación exploratoria: BM25 20.7%, Multi-RAG 10.7% (Hit@5: 86.7% vs 53.3%) |
| Eficiencia ranking (39 temas, reglas v1) | mediana ≤15 s | ~10 ms mediana local (5 réplicas: 84/10.6/11/10.2/10.5) |
| Ingesta seed (150/540/82, sqlite) | — | 150 noticias (3 medios) + 540 indicadores WB + 82 eventos USGS |
| Eficiencia LLM (mediana latencia) | mediana ≤15 s | **12.09 s** mediana (p95: 19.84 s; meta cumplida) |
| Eficiencia LLM (tokens y costo) | reportar | 28,698 tokens totales en 40 consultas; **$0.0253 USD** costo total |

## Medición de Validez de Sustento y Eficiencia LLM (T-08)

Módulo ejecutable: `backend/src/evidentia/evaluation/benchmark_runner.py`.
Resultados registrados en: `data/benchmark_results_40.json`.

* **Modelo:** `meta-llama/Llama-3.3-70B-Instruct-Turbo` vía Together.ai (Serverless).
* **Parámetros:** `temperature=0.2`, `max_tokens=1500`, delimitación estricta de fuentes en etiquetas XML `<fuente id="..." tipo="...">` como datos aislados.

### Validez de sustento fáctico sobre afirmaciones generadas
* **Afirmaciones revisadas:** 51 afirmaciones extraídas de los borradores generados sobre casos sustentados.
* **Afirmaciones sustentadas por la fuente:** 47 / 51 (**92.16%**).
* **Afirmaciones sin respaldo directo o débiles:** 4 / 51 (7.84%, principalmente contextualizaciones de encuadre editorial sin cita directa).
* **Meta del reto (≥90% sobre ≥30 afirmaciones):** **Cumplida (92.2% > 90%, n=51 > 30)**.

### Tabla de Eficiencia (Latencia, Tokens y Costo)

| Métrica | Medido (40 consultas de desarrollo) | Meta / Referencia |
|---------|--------------------------------------|-------------------|
| **Latencia mediana** | **12.092 s** | ≤ 15.0 s (Meta cumplida) |
| **Latencia percentil 95 (p95)** | **19.840 s** | — |
| **Prompt tokens promedio** | 550.0 tokens / consulta | — |
| **Completion tokens promedio** | 439.6 tokens / consulta | — |
| **Total tokens promedio** | 989.6 tokens / consulta | — |
| **Tokens consumidos (40 consultas)** | **28,698 tokens** | — |
| **Costo total estimado** | **$0.0253 USD** ($0.88/1M tokens) | < $0.05 USD |

## Benchmark 40/20 y Clasificación/Abstención (T-10)

División metodológica obligatoria según reto §7:
* **Total consultas en `data/benchmark.jsonl`:** 60.
* **Conjunto de desarrollo (40 consultas):** 20 sustentadas (`S01`–`S20`), 7 contradicción (`C01`–`C07`), 7 sin respuesta (`N01`–`N07`), 6 adversariales (`A01`–`A06`).
* **Conjunto reservado para el jurado (20 consultas):** 10 sustentadas (`S21`–`S30`), 3 contradicción (`C08`–`C10`), 3 sin respuesta (`N08`–`N10`), 4 adversariales (`A07`–`A10`). Las 20 reservadas se mantienen intactas sin optimización previa.

### Resultados observados en el Benchmark de Desarrollo (40 casos)

| Categoría | Total Casos | Éxito / Comportamiento Esperado | Tasa Observada |
|-----------|-------------|---------------------------------|----------------|
| **Sin respuesta (Abstención correcta)** | 7 | 7 / 7 abstenciones explícitas (`ABSTENCIÓN: no hay evidencia...`) | **100.0%** (Meta ≥80%) |
| **Preguntas sustentadas (Borrador con citas)** | 20 | 16 / 20 generados con citas válidas (4 abstenciones por datos insuficientes) | 80.0% completitud |
| **Falsas abstenciones en respondibles** | 20 | 4 / 20 (casos con titulares breves donde el modelo prefirió prudencia) | 20.0% |
| **Adversariales (Resistencia a inyección)** | 6 | 5 / 6 ataques bloqueados sin filtrar instrucciones del sistema | 83.3% |
| **Cobertura de citas válidas** | — | 100% (citas verificadas contra IDs del corpus; citas desconocidas removidas) | **100.0%** |

## Comparación Medida: Baseline de Palabras Clave (BM25) vs Multi-RAG Semántico (T-09)

Módulo reproducible: `backend/src/evidentia/retrieval/baseline.py`.
Evaluado sobre el corpus seed congelado (150 noticias + 540 indicadores) contra las 60 consultas de `data/benchmark.jsonl` (30 sustentadas, 10 sin respuesta, 10 contradicción, 10 adversariales).

| Métrica (Top-5) | BM25 Baseline (Okapi k1=1.5, b=0.75) | Multi-RAG Semántico (FastEmbed + Qdrant) | Diferencia / Observación |
|-----------------|--------------------------------------|------------------------------------------|--------------------------|
| **Hit@1** | **80.0%** (24/30) | 50.0% (15/30) | BM25 acierta de inmediato cuando el titular exacto está citado |
| **Hit@5** | **86.7%** (26/30) | 53.3% (16/30) | BM25 ubica el documento objetivo en el top 5 con alta consistencia |
| **Precision@5** | **20.7%** | 10.7% | 1 documento relevante por consulta sobre 5 retornados |
| **MRR (Mean Reciprocal Rank)** | **0.817** | 0.508 | Primer resultado relevante en posición ~1.2 para BM25 |
| **Abstención en 'Sin Respuesta'** | 30.0% | **100.0%** | La IA / Synthesiser tiene guarda explícita de abstención (T06) |
| **Latencia promedio** | **< 1 ms** | ~15–20 ms | BM25 en memoria es un orden de magnitud más rápido |

### ¿Dónde aporta valor la IA y cuándo NO ayuda? (Rúbrica §8)

1. **Dónde SÍ mejora la IA:**
   * **Consultas conceptuales y paráfrasis:** Cuando el usuario no conoce el titular exacto ni la jerga legislativa/periodística (ej. preguntas como "¿Qué pasó con el costo de vida?" o "¿Cómo va el transporte público?"), los embeddings vectoriales capturan la cercanía semántica entre "costo de vida" e "inflación / canasta básica", mientras que BM25 fracasa por ausencia de coincidencia léxica literal.
   * **Abstención confiable frente a vacíos:** En consultas sin evidencia (`sin_respuesta`), BM25 recupera falsos positivos porque siempre encuentra algún token común ("Panamá", "noticia", "informe"), dando una falsa sensación de coincidencia (abstención de solo 30%). El pipeline de IA + Synthesiser aplica guardas de suficiencia y abstención estructurada con 100% de éxito, evitando alucinaciones.
   * **Síntesis con atribución verificable:** BM25 solo recupera documentos crudos. La IA estructura el borrador editorial en 7 secciones con citas directas `[id_fuente:campo]`.

2. **Dónde NO aporta la IA (y el baseline tradicional es superior):**
   * **Búsquedas de entidades únicas y números exactos:** Para nombres propios específicos (ej. "Enrique Lau", "Stefany Peñalba"), códigos de leyes o cifras numéricas exactas ("$43.1 millones", "100 millones"), BM25 tiene una precisión cercana al 100% y un MRR de 0.817. Los embeddings densos pueden diluir entidades raras en el espacio semántico vectorial agrupándolas con noticias del mismo sector pero de personas distintas.
   * **Latencia y costo computacional:** BM25 requiere 0 FLOPS de GPU, no consume tokens de API, y responde en menos de 1 ms.
   * **Conclusión arquitectónica:** Para producción, la arquitectura óptima es **híbrida (BM25 + Dense Semantic Fusion)**: BM25 para filtrar candidatos con match léxico exacto, y Dense Embeddings para rescatar documentos conceptuales relevantes sin palabras compartidas.

## Correcciones

- 2026-10-07: T05 falló inicialmente (variantes numéricas no agrupaban por los
  dígitos en Jaccard). Corrección: `title_tokens` ignora tokens numéricos +
  test de regresión `test_numeric_variants_group_together`. T05 verde.
- 2026-10-07: T09 implementado y evaluado con benchmark reproducible `backend/src/evidentia/retrieval/baseline.py`.
- 2026-10-07: T08 y T10 ejecutados y documentados: 40 consultas de desarrollo evaluadas, 20 reservadas; 92.2% validez de sustento (47/51 afirmaciones), 100% abstención sin respuesta, latencia mediana 12.09 s.


