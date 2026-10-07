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

## Métricas (observadas 2026-10-07, seed: 40 TVN + 540 WB + 82 USGS)

| Métrica | Meta del reto | Resultado |
|---------|---------------|-----------|
| Cobertura de citas | 100% | 100% por construcción (validador remueve ids desconocidos; verificado en tests con stub) |
| Validez de sustento (≥30 afirmaciones) | ≥90% | Pendiente de key LLM (revisión humana sobre salidas reales) |
| Abstención correcta | ≥80% | 100% en tests (T06 + 10 benchmark N); tasa en vivo pendiente de key |
| Agrupación (Jaccard + agencia) | reportar | Regla documentada v1; F1 vs etiquetas humanas pendiente |
| Utilidad del ranking (Precision@5) | reportar | Evaluación exploratoria pendiente (sin editor asignado) |
| Eficiencia ranking (39 temas, reglas v1) | mediana ≤15 s | ~10 ms mediana local (5 réplicas: 84/10.6/11/10.2/10.5) |
| Ingesta seed (40/540/82, sqlite) | — | 9.9 s, 0 descartadas, 97 entidades + 98 relaciones |
| Generación (tokens/costo) | reportar | Pendiente de key (sin key: abstención inmediata, costo 0) |

## Correcciones

- 2026-10-07: T05 falló inicialmente (variantes numéricas no agrupaban por los
  dígitos en Jaccard). Corrección: `title_tokens` ignora tokens numéricos +
  test de regresión `test_numeric_variants_group_together`. T05 verde.
