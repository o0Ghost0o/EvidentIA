# Walkthrough: Renderizado Markdown, Carga por Esquema con Plantillas, Trazabilidad de Duplicados y Almacenamiento Persistente en Coolify

## Resumen de la Implementación
Se abordaron e implementaron los cuatro requerimientos solicitados por el usuario:
1. **Renderizado de Markdown en el Reporte Oficial (`/jurado`):** Visualización formateada en HTML del reporte con tipografía rica, tablas estilizadas, bloques de código legibles y badges de estado; **sin vista dividida (*no split view*)**, con selector entre Vista Renderizada (por defecto) y Código Markdown crudo.
2. **Carga Manual de Archivos por Esquema (`/ingest`):** Interfaz para subir datos validados de las 4 familias (`noticias.csv`, `indicadores.csv`, `eventos.geojson`, `fichas.jsonl`) con validación de esquemas y actualización de base de datos e índices.
3. **Descarga de Plantillas Oficiales:** Botón en cada familia que descarga archivos de plantilla con datos de muestra válidos (`plantilla_noticias.csv`, `plantilla_indicadores.csv`, `plantilla_eventos.geojson`, `plantilla_fichas.jsonl`).
4. **Trazabilidad de Carga con `upload_id`, Timestamp y Detección de Duplicados:** Cada subida genera un identificador único con marca de tiempo UTC, estado (`completado`, `advertencias`, `error`), bandera y conteo de duplicados colapsados, con tabla histórica y modal interactivo de detalle.
5. **Solución Permanente de Almacenamiento Persistente en Coolify:** Se resolvió de raíz la causa de `"seed file missing"` observada en Dev (`/tmp/cmux-drop-0e445457-32d0-479b-bd77-17472d5f8a76.png`) añadiendo una capa inmutable `/app/seed_frozen` en el contenedor y auto-aprovisionamiento del volumen persistente `/app/data` en el arranque.

---

## 1. Renderizado de Markdown en `/jurado` (Sin Split View)
- **Librería Utilizada:** `marked` instalada vía `bun add marked`.
- **Diseño Unificado (Single View):**
  - Ocupa el 100% del contenedor en una sola columna limpia (eliminando el bloque `<pre>` como única opción).
  - Selector de vista en la barra superior: `[ Vista Renderizada (Default) | Código Markdown (.md) ]`.
  - Estilos tipográficos completos con `:deep(...)` para títulos (`h1`-`h4`), párrafos, tablas con bordes y alternancia de filas, bloques de código monospace, citas y listas.
  - Se mantienen los botones `Copiar Texto` y `Descargar archivo .md`.

---

## 2. Ingesta: Carga de Archivos y Plantillas Descargables
- **4 Tarjetas de Carga en `/ingest`:**
  - **Noticias de Prensa (`noticias.csv`):** Validación de URLs activas, medios, titulares y alcance.
  - **Indicadores Banco Mundial (`indicadores.csv`):** Validación de tuplas `(pais_iso3, indicador_id, anio)`.
  - **Eventos Geofísicos USGS (`eventos.geojson`):** Validación de FeatureCollection y coordenadas.
  - **Fichas Editoriales (`fichas.jsonl`):** Validación línea por línea de casos, afirmaciones y puntajes.
- **Descarga de Plantillas:**
  - Endpoint `GET /ingest/templates/{family}` en [`ingest.py`](file:///home/pedrocarreras/dev/EvidentIA/backend/src/evidentia/api/ingest.py).
  - Archivos creados en [`backend/data/templates/`](file:///home/pedrocarreras/dev/EvidentIA/backend/data/templates/) y [`data/templates/`](file:///home/pedrocarreras/dev/EvidentIA/data/templates/).

---

## 3. Trazabilidad de Cargas y Detección de Duplicados
- **Endpoint `POST /ingest/upload`:**
  - Genera `upload_id` único: `upl-YYYYMMDD-HHMMSS-xxxxxx`.
  - Registra timestamp UTC, total de filas, válidas, descartadas y estado (`completed`, `completed_with_warnings`, `failed`).
  - Audita errores con `"duplicate"` para detectar URLs repetidas, títulos cuasi-idénticos (Jaccard > 0.85), observaciones de indicadores repetidas y eventos duplicados.
  - Persiste el historial en `data/processed/upload_history.json`.
- **Tabla de Historial en `/ingest`:**
  - Muestra identificador, fecha, archivo, conteo de filas y estado.
  - Columna de duplicados: chip verde `✓ Sin duplicados` o chip ámbar `⚠️ N duplicados detectados` con botón para abrir el modal de auditoría.

---

## 4. Solución Definitiva de Almacenamiento Persistente en Coolify
- **Causa Raíz:** En Coolify, el volumen persistente montado en `/app/data` enmascara los archivos copiados en el contenedor durante la construcción (`COPY data/seed ./data/seed`). Si el volumen en el host estaba inicialmente vacío, `data/seed` quedaba sin archivos.
- **Solución Implementada:**
  1. [`backend/Dockerfile`](file:///home/pedrocarreras/dev/EvidentIA/backend/Dockerfile): Añadido `COPY data/seed /app/seed_frozen` fuera del punto de montaje `/app/data`.
  2. [`backend/src/evidentia/config.py`](file:///home/pedrocarreras/dev/EvidentIA/backend/src/evidentia/config.py): Función `ensure_seed_files()` que auto-copia los archivos desde `/app/seed_frozen` hacia el volumen persistente si no existen.
  3. [`backend/src/evidentia/main.py`](file:///home/pedrocarreras/dev/EvidentIA/backend/src/evidentia/main.py): Invocación de `ensure_seed_files()` en el arranque del servidor (`lifespan`).
  4. [`backend/src/evidentia/ingestion/pipeline.py`](file:///home/pedrocarreras/dev/EvidentIA/backend/src/evidentia/ingestion/pipeline.py): Fallback dinámico a `/app/seed_frozen` si un archivo es requerido durante la ingesta.

---

## 5. Verificación
1. **Pruebas Automatizadas de Backend:**
   - `uv run pytest tests/test_upload.py`: 2/2 pruebas pasando (descarga de plantillas, subida con detección de duplicados e historial).
   - `uv run pytest`: 82/82 pruebas pasando (100% green).
2. **Compilación Frontend:**
   - `bun run build`: Construcción limpia de cliente y servidor Nitro con 0 errores.
3. **Control de Versiones y Despliegue:**
   - Commit `91ed83a` sincronizado en `origin dev` y `gitea dev`.
   - Despliegue en cola en Coolify (`dev-evidentia.vertexdc.com`, deployment `s2qicbdznezbfzxyywtuflwy`).
