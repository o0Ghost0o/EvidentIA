# 03 — Catálogo de Datos

> Página 3/8 del espacio Notion. Paquete: "Panamá · Señales y Evidencias v1".

## Fuentes

| Familia | Fuente | URL / API | Cobertura | Campos | Licencia / condiciones |
|---------|--------|-----------|-----------|--------|------------------------|
| A. Noticias | TVN RSS público | Feed RSS de TVN Panamá | Titulares+enlaces 30 días (ampliar a 90 si faltan) | titulo, url, medio, idioma, fechas, tema, origen | Metadatos; sin republicación de artículos/videos/imágenes sin autorización |
| A. Noticias | GDELT DOC 2.0 API | `api.gdeltproject.org` | Query "Panama", logística, turismo, economía, eventos naturales; máx 250/consulta, dividir por fechas | titulo, url, medio, idioma, fechas | No transfiere derechos de los medios enlazados |
| B. Indicadores | Banco Mundial Indicators API v2 | `api.worldbank.org` | PAN/CRI/COL/DOM/MEX/GTM × 6 indicadores × 2010–2024 (conservar nulos) | pais_iso3, indicador_id, anio, valor, unidad, fuente_url | CC BY 4.0 gral., salvo excepciones en metadatos |
| C. Sismos | USGS Earthquake Catalog | `earthquake.usgs.gov` | 2024-01-01–2024-12-31, lat 5–12, lon −86–−76, mag ≥ 3 | id, magnitude, time, updated, lon/lat, depth, place, status, url | Solo hechos sísmicos; la caja no equivale a Panamá |
| D. Banca (opcional) | SBP estadísticas/informes | `superbancos.gob.pa` | 12 informes mensuales 2024 o período documentado | serie, período, unidad, página origen | Uso informativo; validar reutilización |

Indicadores Banco Mundial: `NY.GDP.MKTP.KD.ZG` (PIB), `FP.CPI.TOTL.ZG` (inflación),
`SL.UEM.TOTL.ZS` (desempleo), `SP.POP.TOTL` (población), `IT.NET.USER.ZS` (internet),
`NE.EXP.GNFS.ZS` (exportaciones/PIB).

## Archivos del contrato de datos

- `noticias.csv`: id_noticia, titulo, url, medio, idioma, fecha_publicacion,
  fecha_deteccion, fecha_extraccion, tema, origen, alcance_texto.
- `indicadores.csv`: pais_iso3, indicador_id, anio, valor (nullable), unidad,
  fuente_url, fecha_extraccion, licencia.
- `eventos.geojson`: id, magnitude, time, updated, longitude, latitude, depth,
  place, status, URL.
- `fichas.jsonl`: id_caso, modalidad, ids_fuente, afirmaciones, citas, puntaje,
  componentes, estado_evidencia, borrador, estado_revision.
- `manifest.json`: versión, fecha_corte_UTC, consultas, cantidad por archivo,
  licencia/condiciones, SHA-256, transformaciones.

## Transformaciones aplicadas

1. Normalización de fechas a ISO 8601 UTC; filas inválidas → reporte de calidad, no bloqueo.
2. Deduplicación por URL + similitud de titular; se conservan todas las fuentes del grupo.
3. Clasificación temática: economía, logística/Canal, turismo, servicios públicos,
   eventos naturales, regulación.
4. Detección de agencia primaria (EFE/Reuters/AFP/AP/…) vs medio; réplicas = 1 procedencia.

## Hash del snapshot

Se publica en `data/manifest.json` tras la primera ingesta (SHA-256 por archivo).
Snapshot offline de respaldo: `data/seed/` (ver T10).
