# 01 — Inicio del Reto

> Página 1/8 del espacio Notion (versión Markdown en `docs/notion/`).
> Sincronización: `scripts/sync_notion.py` cuando exista token.

## Equipo

| Rol | Responsable |
|-----|-------------|
| Producto / Editorial | _pendiente_ |
| Backend / IA | _pendiente_ |
| Frontend | _pendiente_ |
| Datos / Evaluación | _pendiente_ |

## Modalidad elegida

**TVN · principal (editorial)** como modalidad recomendada; **Banca** como extensión
del mismo núcleo (boletín de entorno, sin evaluar clientes ni ejecutar decisiones
financieras).

## Problema

Un equipo editorial debe revisar fuentes dispersas, eliminar duplicados, ubicar los
hechos en contexto y preparar piezas con rapidez. La circulación de una noticia no
equivale a su confirmación: varios medios pueden repetir una misma fuente.

## Usuario

- **Editor/a y periodista (TVN):** agenda priorizada, ficha de investigación,
  preguntas pendientes y borradores por formato.
- **Productor/a digital (TVN):** propuestas de titulares, resumen web y copy social,
  siempre sujetos a revisión.
- **Analista de estudios económicos (Banca, extensión):** boletín de entorno, señales
  y preguntas para seguimiento.

## Alcance

**Incluye (MVP):** ingesta de noticias + indicadores oficiales; normalización,
búsqueda, clasificación temática, agrupación de duplicados, detección de faltantes y
contradicciones; bandeja priorizada, ficha de evidencia, consultas en español y
entregable de la modalidad (paquete editorial TVN).

**No incluye:** rating/audiencia real, veredictos de veracidad, datos personales,
paywalls, producción audiovisual automática ni integración con emisión.

## Criterios de éxito

1. Pasar de fuentes dispersas a un tema investigable con evidencia y borrador responsable.
2. 100% de afirmaciones factuales con cita identificable; abstención explícita sin evidencia.
3. T01–T10 en verde + demo reproducible sin internet (snapshot local).
4. Pitch de 10 minutos presentado desde Notion.

## Accesos

- Demo local: `http://localhost:8080` (vía `docker compose up --build`)
- Repositorio: _URL de GitHub con acceso al jurado (pendiente de publicar)_
- Datos: `data/` + `manifest.json` (ver página 3, Catálogo de Datos)
