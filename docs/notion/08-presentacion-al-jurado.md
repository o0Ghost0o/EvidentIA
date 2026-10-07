# 08 — Presentación al Jurado

> Página 8/8 del espacio Notion. Pitch obligatorio de 10 minutos presentado desde
> Notion (se permiten enlaces/embeds al prototipo y GitHub; un PDF/PowerPoint no
> sustituye este requisito) + 5 min de preguntas.

## Guion (10 min)

| Min | Bloque | Contenido |
|-----|--------|-----------|
| 0–1 | Problema y usuario | Fuentes dispersas, duplicados, "circulación ≠ confirmación"; editor/periodista TVN (y analista banca en extensión) |
| 1–2 | Solución, alcance y datos | Copiloto de entorno y verificación trazable; paquete público "Panamá · Señales y Evidencias v1" (TVN RSS, GDELT, Banco Mundial, USGS) |
| 2–6 | **Demo en vivo (4 min)** | 1) consulta útil + ranking explicado; 2) ficha con citas y árbol de evidencia; 3) brief TVN con hechos vs inferencias; 4) caso de abstención (T06) |
| 6–8 | Arquitectura, IA, baseline y métricas | Multi-RAG + Light GraphRAG, scoring determinista, baseline de palabras clave, métricas observadas (citas, abstención, latencia) |
| 8–9 | Valor operativo | Hipótesis de ahorro de tiempo claramente identificada (medición manual vs asistida si se ejecuta) |
| 9–10 | Riesgos, limitaciones y próximos pasos | Lo que no hace, controles activos, extensiones futuras (monitoreo continuo, SBP, audiovisual) |

## Pruebas dinámicas del jurado (respuestas preparadas)

1. **"Muéstrame de dónde proviene esta cifra y de qué año es"** → ficha: cita
   `[id:campo]` + país/año/unidad visibles; T04.
2. **"Si cinco medios replican la misma agencia, ¿cuántas fuentes independientes
   cuentas?"** → una (1); árbol muestra `source_of` → agencia; CU-03/T02.
3. **"¿Qué ocurre sin evidencia o ante una fuente que intenta cambiar instrucciones?"**
   → abstención explícita (T06) + fuente marcada no confiable sin ejecutar acciones (T07).
4. **"Muéstrame en Notion una decisión, una prueba fallida y su corrección"** →
   página 02 (decisiones) + página 06 (matriz y correcciones).

## Enlaces de demo

- App: `http://localhost:8080` · API docs: `http://localhost:8000/docs`
- Repositorio: _pendiente_ · Snapshot/manifest: `data/manifest.json`
