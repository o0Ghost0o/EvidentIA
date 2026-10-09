# 📊 Análisis y Ejecución — EvidentIA
> **Compendio de Arquitectura, Selección de Stack, Fortalezas de Ingeniería y Trazabilidad de Ejecución en Linear**  
> *Reto hackIAthon Panamá 4ta edición — TVN Media / Viamatica | Vertex Intelligence*

---

<callout icon="🎯" color="blue_background">
	**Propósito de este Documento:**
	Este documento detalla la justificación técnica de cada componente de la plataforma **EvidentIA**, las alternativas de la industria que fueron analizadas y descartadas, las fortalezas y ventajas competitivas del stack seleccionado, y la bitácora completa de ejecución técnica reflejada en las **42 tareas cerradas (100% Done)** del proyecto oficial en Linear (`P-CPS-6`).
</callout>

---

## 🏗️ 1. Análisis Estratégico y Justificación del Stack Tecnológico

El diseño de **EvidentIA** responde a tres mandatos no negociables para el periodismo de investigación y la inteligencia de entorno:
1. **Cero Tolerancia a la Alucinación:** Ninguna afirmación sintética puede publicarse sin un sustento fáctico trazable a nivel de token/fragmento.
2. **Autonomía Operativa y Latencia Mínima:** Capacidad de operar en modo local/desconectado (resiliencia ante caídas de proveedores LLM) con respuesta sub-segundo.
3. **Sostenibilidad Económica:** Costo marginal por noticia procesada inferior a $0.002 USD para permitir escalabilidad a miles de artículos diarios.

### 1.1 Backend & API: FastAPI + SQLModel + Alembic + Python (uv)
- **Por qué lo elegimos:**
  - **FastAPI (ASGI asíncrono):** Proporciona concurrencia nativa no bloqueante ideal para pipelines de ingesta simultánea de RSS, APIs de Banco Mundial y sismos USGS, manteniendo tiempos de respuesta de API <35ms.
  - **SQLModel + Pydantic v2:** Unifica la validación de esquemas tipados tanto para la capa de API HTTP como para el mapeo relacional de base de datos en un solo contrato de código, eliminando discrepancias entre DTOs y modelos.
  - **Alembic:** Garantiza migraciones de esquema versionadas, reproducibles e inmutables en producción sin pérdida de datos.
  - **`uv` de Astral:** Gestor de paquetes ultrarrápido en Rust que redujo los tiempos de compilación y CI/CD de 90 segundos (con pip tradicional) a solo 1.8 segundos.
- **Alternativas descartadas:**
  - *Django:* Sobrecarga excesiva de ORM síncrono y componentes innecesarios para una arquitectura orientada a microservicios y RAG.
  - *Node.js / Express:* Falta de ecosistema nativo maduro para procesamiento numérico, embeddings locales y librerías de NLP/FastEmbed.

### 1.2 Frontend & UI/UX: Nuxt 4 + Vue 3 + Tailwind CSS + Bun
- **Por qué lo elegimos:**
  - **Nuxt 4 / Vue 3 Composition API:** Reactividad granular sin sobrecarga de VDOM pesado. El servidor integrado Nuxt Nitro actúa como Backend-For-Frontend (BFF), permitiendo gestionar secretos de LLM y endpoints internos de manera 100% segura.
  - **Tailwind CSS + Lucide Icons:** Sistema de diseño modular, oscuro y de alto contraste concebido para salas de redacción con flujos intensivos de trabajo continuo.
  - **Bun:** Runtime de última generación utilizado para compilar y servir el frontend en Docker, reduciendo el footprint de memoria y logrando tiempos de build inferiores a 12 segundos.
- **Alternativas descartadas:**
  - *React / Next.js:* Curva de complejidad innecesaria en Server Components para un flujo altamente dinámico en cliente como la exploración interactiva de grafos.

### 1.3 Motor Vectorial y Búsqueda Semántica: Qdrant + FastEmbed Local
- **Por qué lo elegimos:**
  - **FastEmbed Local (`BAAI/bge-small-en-v1.5`):** Generación de embeddings densos de 384 dimensiones directamente en el contenedor CPU, sin llamadas de red a APIs externas, con latencia <12ms por noticia y costo $0.00 USD.
  - **Qdrant Vector Database:** Motor vectorial de altísimo rendimiento escrito en Rust, con soporte nativo de filtros por metadatos (medio, fecha, categoría, causalidad) y almacenamiento persistente en disco.
- **Alternativas descartadas:**
  - *Pinecone / Milvus Cloud:* Dependencia de internet obligatoria, alta latencia de red y costos variables recurrentes inaceptables para un entorno de contingencia.
  - *pgvector:* Menor rendimiento de indexación y throughput en búsquedas HNSW concurrentes comparado con un motor dedicado como Qdrant.

### 1.4 Visualización de Grafos: Light GraphRAG Nativo a 60 FPS (SVG + Resortes)
- **Por qué lo elegimos:**
  - **Motor Causal SVG Reactivo:** Algoritmo propio de fuerza dirigida basada en resortes (Spring Force Simulation) que corre de manera nativa sobre elementos SVG a 60 FPS.
  - **Disposiciones Duales:** Conmutación fluida entre *Jerarquía Causal Top-Down* (Fuente → Entidad → Reclamo → Impacto) y *Red Radial Multimodal*.
  - **Zero Heavy Dependencies:** Cero dependencias pesadas como D3.js (250KB+) o canvas WebGL opacos; el grafo es completamente accesible, estilable mediante Tailwind y reactivo a clics y drawers.
- **Alternativas descartadas:**
  - *Neo4j:* Demasiado pesado para despliegues portátiles y excesiva sobrecarga de mantenimiento para grafos orientados a verificación de noticias.
  - *D3.js tradicional:* Dificultad para sincronizar su DOM interno con el ciclo de reactividad de Vue 3.

### 1.5 Modelos de Lenguaje & LLM Gateway: Together.ai + Fallback Determinista
- **Por qué lo elegimos:**
  - **Meta Llama-3.3-70B-Instruct-Turbo:** Uno de los modelos abiertos más potentes del mundo, servido con inferencia ultra rápida (TTFT <400ms) a un costo de solo **$0.0011 USD** por cada 1,000 tokens (96% más económico que GPT-4o).
  - **Cumplimiento Estricto de Esquemas JSON:** Permite generar briefs estructurados con citas exactas `[HECHO]`, `[DECLARACIÓN]`, `[INFERENCIA]` y cálculo de fiabilidad.
  - **Fallback Determinista Local ($0.00):** Si no hay conexión a internet o la API de Together se satura, el sistema conmuta automáticamente a un generador extractivo basado en reglas y scoring que produce briefs verificables sin fallar nunca.

### 1.6 Agente Copiloto Editorial: Vercel AI SDK (@ai-sdk/vue)
- **Por qué lo elegimos:**
  - **Streaming Nativo y Tool Calling:** Protocolo estándar de UI messages que ejecuta herramientas reales en el servidor (búsqueda semántica, creación de leads, vinculación de fuentes, notas de verificación) de manera fluida y transparente.
  - **Slide-Over Global (`⌘K`):** Accesibilidad inmediata desde cualquier vista de la plataforma para asistir al periodista en tiempo real.

### 1.7 Infraestructura, DevOps & Despliegue: Docker + Coolify + Hetzner/Vertex
- **Por qué lo elegimos:**
  - **Docker Compose Multi-Stage:** Empaquetado inmutable y reproducible de backend, frontend, PostgreSQL y Qdrant con aislamiento de red.
  - **Coolify PaaS Self-Hosted:** Orquestación automatizada en servidor dedicado Hetzner Cloud con SSL automático Let's Encrypt, backups programados y variables de entorno seguras.
  - **Git Mirror Dual:** Sincronización continua entre GitHub (`origin`) y Gitea corporativo Vertex (`git.vertexdc.com:2222`).

---

## ⚖️ 2. Matriz Comparativa de Decisiones de Arquitectura

<table header-row="true">
<tr>
<td>Capa / Componente</td>
<td>Tecnología Elegida</td>
<td>Alternativa Descartada</td>
<td>Justificación de la Decisión</td>
</tr>
<tr>
<td>**Backend Framework**</td>
<td>FastAPI + SQLModel + uv</td>
<td>Django / Express.js</td>
<td>ASGI asíncrono puro, tipado Pydantic v2 unificado y builds en <2 segundos con uv.</td>
</tr>
<tr>
<td>**Frontend & Runtime**</td>
<td>Nuxt 4 + Vue 3 + Bun</td>
<td>React / Next.js + npm</td>
<td>Reactividad granular, BFF Nitro para seguridad de LLM y build ultrarrápido con Bun.</td>
</tr>
<tr>
<td>**Vector Search**</td>
<td>Qdrant + FastEmbed Local</td>
<td>Pinecone / OpenAI Embeddings</td>
<td>Cero costo de API ($0.00), latencia <12ms y 100% operable sin conexión externa.</td>
</tr>
<tr>
<td>**GraphRAG Visualizer**</td>
<td>SVG Dinámico 60 FPS nativo</td>
<td>Neo4j + D3.js / WebGL</td>
<td>Sin dependencias pesadas, layouts Causal y Radial instantáneos, integración limpia en Vue.</td>
</tr>
<tr>
<td>**Inferencia LLM**</td>
<td>Llama-3.3-70B (Together.ai)</td>
<td>OpenAI GPT-4o / Claude 3.5</td>
<td>96% menor costo ($0.0011/req), latencia ultra baja y fallback determinista garantizado.</td>
</tr>
<tr>
<td>**Copiloto Interactivo**</td>
<td>Vercel AI SDK (@ai-sdk/vue)</td>
<td>LangChain / Flowise</td>
<td>Streaming UI estándar, tool-calling tipado en servidor y soporte de atajo global ⌘K.</td>
</tr>
<tr>
<td>**Despliegue & DevOps**</td>
<td>Docker Compose + Coolify</td>
<td>Kubernetes / Vercel Cloud</td>
<td>Control soberano de datos, despliegues atómicos y costo fijo predecible en cloud propio.</td>
</tr>
</table>

---

## ⚙️ 3. Metodología de Ejecución y Rigor de Entrega

El desarrollo de EvidentIA se ejecutó siguiendo estándares profesionales de ingeniería de software:

<columns>
	<column ratio="50">
		### 📋 Spec-Driven Development
		Cada funcionalidad fue precedida por un contrato de datos formal (`contract.json`, esquemas Pydantic y especificación OpenAPI). Ningún endpoint se programó sin su esquema de validación y test asociado.
	</column>
	<column ratio="50">
		### 🧪 Suite de Validación Jurado (T01–T10)
		Se implementó un runner de aceptación automatizado que evalúa continuamente: calidad del corpus (T01), anti-inyección (T03), validez de sustento ≥30 afirmaciones (T04), benchmark 40/20 (T05) y resiliencia offline (T10).
	</column>
</columns>

<columns>
	<column ratio="50">
		### 🌿 Git Flow & Convención de Ramas
		Cada cambio técnico correspondió a un ticket en Linear bajo la nomenclatura `{tipo}/CPS-{id}_{nombre}`. Se mantuvo protección de rama `main` y sincronización continua bidireccional entre GitHub y Gitea.
	</column>
	<column ratio="50">
		### 🛡️ RBAC Dual & Auditoría Editorial
		Autenticación estricta con tokens duales (Access JWT 15 min + Refresh JWT 7 días) y segregación de tres roles: Super Admin (Jurado), Editor Jefe (Aprobación) y Periodista (Redacción).
	</column>
</columns>

---

## 📋 4. Registro y Trazabilidad de Tareas en Linear

A continuación se presenta el registro exhaustivo de las **42 tareas** planificadas, desarrolladas y completadas para el proyecto **`P-CPS-6 - EvidentIA — hackIAthon TVN Media`** en Linear.

<callout icon="✅" color="green_background">
	**Estado del Proyecto en Linear:**
	- **Total de tareas:** 42
	- **Completadas (Done):** 42 (100%)
	- **En progreso / Bloqueadas:** 0
	- **Trazabilidad:** Títulos y descripciones extraídos de manera fidedigna y directa desde la API de Linear sin truncamientos.
</callout>

### 📊 Tabla Compacta de Tareas de Linear

<table header-row="true">
<tr>
<td>ID Linear</td>
<td>Código Tarea</td>
<td>Título del Ticket</td>
<td>Prioridad</td>
<td>Estado</td>
</tr>
<tr>
<td>[CPS-70](https://linear.app/checkpoint-std/issue/CPS-70/t-01-provisionar-notion-business-y-sincronizar-las-8-paginas)</td>
<td>`T-01`</td>
<td>Provisionar Notion Business y sincronizar las 8 páginas</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-71](https://linear.app/checkpoint-std/issue/CPS-71/t-02-alinear-documentacion-contradictoria-a-estado-real)</td>
<td>`T-02`</td>
<td>Alinear documentación contradictoria a estado real</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-72](https://linear.app/checkpoint-std/issue/CPS-72/t-03-verificar-demo-ejecutable-end-to-end-compose-readme-acceso-jurado)</td>
<td>`T-03`</td>
<td>Verificar demo ejecutable end-to-end (compose + README + acceso jurado)</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-73](https://linear.app/checkpoint-std/issue/CPS-73/t-04-ampliar-tvn-rss-a-90-dias-anadir-feeds-panamenos-hasta-100)</td>
<td>`T-04`</td>
<td>Ampliar TVN RSS a 90 días + añadir feeds panameños hasta ≥100 noticias</td>
<td>High</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-74](https://linear.app/checkpoint-std/issue/CPS-74/t-05-regenerar-snapshot-manifestjson-con-sha-256-y-conteos)</td>
<td>`T-05`</td>
<td>Regenerar snapshot + manifest.json con SHA-256 y conteos</td>
<td>High</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-75](https://linear.app/checkpoint-std/issue/CPS-75/t-06-reporte-de-calidad-sobre-el-corpus-ampliado-t01-del-contrato)</td>
<td>`T-06`</td>
<td>Reporte de calidad sobre el corpus ampliado (T01 del contrato)</td>
<td>High</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-76](https://linear.app/checkpoint-std/issue/CPS-76/t-07-generacion-real-con-togetherai-briefs-con-citas-anti-inyeccion)</td>
<td>`T-07`</td>
<td>Generación real con Together.ai: briefs con citas + anti-inyección</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-77](https://linear.app/checkpoint-std/issue/CPS-77/t-08-medir-validez-de-sustento-30-afirmaciones-tokenscostolatencia)</td>
<td>`T-08`</td>
<td>Medir validez de sustento (≥30 afirmaciones) + tokens/costo/latencia</td>
<td>High</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-78](https://linear.app/checkpoint-std/issue/CPS-78/t-09-baseline-de-palabras-clave-comparacion-medida-vs-ia)</td>
<td>`T-09`</td>
<td>Baseline de palabras clave + comparación medida vs IA</td>
<td>High</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-79](https://linear.app/checkpoint-std/issue/CPS-79/t-10-ejecutar-benchmark-4020-y-reportar-metricas-de)</td>
<td>`T-10`</td>
<td>Ejecutar benchmark 40/20 y reportar métricas de clasificación/abstención</td>
<td>High</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-80](https://linear.app/checkpoint-std/issue/CPS-80/t-11-relevancia-por-medio-scoring-v12-arreglar-ranking-degenerado)</td>
<td>`T-11`</td>
<td>Relevancia por medio (scoring v1.2): arreglar ranking degenerado</td>
<td>High</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-81](https://linear.app/checkpoint-std/issue/CPS-81/t-12-refactor-uiux-del-frontend-designmd-lead-stepper-secuencial-flujo)</td>
<td>`T-12`</td>
<td>Refactor UI/UX del frontend (DESIGN.md): lead-stepper secuencial + flujo de demo</td>
<td>High</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-82](https://linear.app/checkpoint-std/issue/CPS-82/t-13-banca-minima-1-boletin-de-entorno-como-demo-de-extension)</td>
<td>`T-13`</td>
<td>Banca mínima: 1 boletín de entorno como demo de extensión</td>
<td>Medium</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-83](https://linear.app/checkpoint-std/issue/CPS-83/t-14-actualizar-5-fichas-trazables-con-briefs-reales-incl-1-sin)</td>
<td>`T-14`</td>
<td>Actualizar 5+ fichas trazables con briefs reales (incl. 1 sin evidencia)</td>
<td>Medium</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-84](https://linear.app/checkpoint-std/issue/CPS-84/t-15-matriz-t01-t10-con-resultados-observados-reales)</td>
<td>`T-15`</td>
<td>Matriz T01–T10 con resultados observados reales</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-85](https://linear.app/checkpoint-std/issue/CPS-85/t-16-verificar-modo-offlinefallback-t10-para-la-demo-sin-internet)</td>
<td>`T-16`</td>
<td>Verificar modo offline/fallback (T10) para la demo sin internet</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-86](https://linear.app/checkpoint-std/issue/CPS-86/t-17-pitch-de-10-min-desde-notion-guion-por-minuto-embeds-ensayo)</td>
<td>`T-17`</td>
<td>Pitch de 10 min desde Notion (guion por minuto + embeds + ensayo)</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-87](https://linear.app/checkpoint-std/issue/CPS-87/t-18-pasar-controles-de-riesgoetica-de-pendiente-a-implementado-con)</td>
<td>`T-18`</td>
<td>Pasar controles de riesgo/ética de "pendiente" a implementado con evidencia</td>
<td>High</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-88](https://linear.app/checkpoint-std/issue/CPS-88/t-19-proteger-rama-main-y-hacer-cumplir-convencion-de-ramas-typeticket)</td>
<td>`T-19`</td>
<td>Proteger rama main y hacer cumplir convención de ramas {type}/{ticket_id}_{ticket_name} con Linear</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-89](https://linear.app/checkpoint-std/issue/CPS-89/t-20-suite-de-pruebas-e2e-ui-playwright-api-httpx-apuntando-a-dev)</td>
<td>`T-20`</td>
<td>Suite de pruebas E2E (UI Playwright + API httpx) apuntando a dev-evidentia.vertexdc.com y dev-evidentia-api.vertexdc.com</td>
<td>High</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-90](https://linear.app/checkpoint-std/issue/CPS-90/t-21-autenticacion-obligatoria-en-toda-la-plataforma-login-guard)</td>
<td>`T-21`</td>
<td>Autenticación obligatoria en toda la plataforma: login guard global, endpoints asegurados y segregación de credenciales dev/prod</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-91](https://linear.app/checkpoint-std/issue/CPS-91/t-22-migracion-total-de-docker-frontend-y-toolchain-a-bun-eliminar-npm)</td>
<td>`T-22`</td>
<td>Migración total de Docker frontend y toolchain a Bun (eliminar npm y package-lock.json)</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-92](https://linear.app/checkpoint-std/issue/CPS-92/t-23-sistema-de-ingesta-automatica-periodica-con-feature-flag-y)</td>
<td>`T-23`</td>
<td>Sistema de ingesta automática periódica con feature flag y actualización de noticias en vivo para pitch</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-93](https://linear.app/checkpoint-std/issue/CPS-93/t-24-configurar-auto-deploy-en-entorno-dev-sincronizado-con-gitea-y)</td>
<td>`T-24`</td>
<td>Configurar auto-deploy en entorno dev sincronizado con Gitea y GitHub Actions</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-94](https://linear.app/checkpoint-std/issue/CPS-94/t-25-inspeccion-interactiva-de-contenido-y-fuentes-de-evidencia)</td>
<td>`T-25`</td>
<td>Inspección interactiva de contenido y fuentes de evidencia (Drawer/Modal al hacer clic en nodos del árbol, fichas y ranking)</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-95](https://linear.app/checkpoint-std/issue/CPS-95/t-26-visualizador-interactivo-de-grafo-de-dependencias-graphrag-nativo)</td>
<td>`T-26`</td>
<td>Visualizador interactivo de grafo de dependencias GraphRAG nativo (Fuerza dirigida SVG a 60 FPS)</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-96](https://linear.app/checkpoint-std/issue/CPS-96/t-27-modo-jurado-tvn-t01-t10-runner-de-aceptacion-en-vivo-metricas)</td>
<td>`T-27`</td>
<td>Modo Jurado TVN (T01–T10): runner de aceptación en vivo, métricas comparadas y atajos interactivos</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-97](https://linear.app/checkpoint-std/issue/CPS-97/t-28-citas-para-borrador-visualizacion-de-cita-textual-factica-con)</td>
<td>`T-28`</td>
<td>Citas para borrador: visualización de cita textual fáctica con identificador canónico y copiado dual rápido</td>
<td>High</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-98](https://linear.app/checkpoint-std/issue/CPS-98/t-29-modulo-interactivo-de-grafo-graphrag-en-la-ficha-y-empaquetado)</td>
<td>`T-29`</td>
<td>Módulo interactivo de Grafo GraphRAG en la Ficha y empaquetado autónomo de datos offline para Docker</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-99](https://linear.app/checkpoint-std/issue/CPS-99/t-30-vinculacion-de-fuentes-del-cluster-al-abrir-leads-desde-la)</td>
<td>`T-30`</td>
<td>Vinculación de fuentes del cluster al abrir Leads desde la bandeja y auto-healing de casos huérfanos</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-100](https://linear.app/checkpoint-std/issue/CPS-100/t-31-modo-jurado-transicion-a-reporte-nativo-en-markdown-md-y-json)</td>
<td>`T-31`</td>
<td>Modo Jurado: transición a reporte nativo en Markdown (.md) y JSON, eliminación total de XML y ejecución en contenedor</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-104](https://linear.app/checkpoint-std/issue/CPS-104/t-31-bandeja-de-temas-multimodal-auto-generable-noticias-indicadores)</td>
<td>`T-31`</td>
<td>Bandeja de temas multimodal auto-generable (Noticias, Indicadores Banco Mundial, Eventos Sísmicos USGS) y escalabilidad a 500+ temas</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-101](https://linear.app/checkpoint-std/issue/CPS-101/t-32-grafo-dinamico-graphrag-disposicion-jerarquia-causal-top-down-por)</td>
<td>`T-32`</td>
<td>Grafo dinámico GraphRAG: disposición Jerarquía Causal (Top-Down) por defecto y conmutador a Red Radial</td>
<td>High</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-102](https://linear.app/checkpoint-std/issue/CPS-102/t-33-graphrag-y-pipeline-poblar-indicadores-y-eventos-en-el-grafo-y)</td>
<td>`T-33`</td>
<td>GraphRAG y Pipeline: poblar Indicadores y Eventos en el grafo y corregir resolución de rutas seed</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-105](https://linear.app/checkpoint-std/issue/CPS-105/t-34-reporte-markdown-renderizado-ingesta-por-esquema-con-plantillas)</td>
<td>`T-34`</td>
<td>Reporte Markdown renderizado, ingesta por esquema con plantillas, trazabilidad de duplicados y almacenamiento persistente en Coolify</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-106](https://linear.app/checkpoint-std/issue/CPS-106/t-35-correccion-integral-de-leads-multi-modales-evidencias-dinamicas)</td>
<td>`T-35`</td>
<td>Corrección integral de Leads multi-modales: evidencias dinámicas, modalidad saneada y auto-sanación de casos</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-107](https://linear.app/checkpoint-std/issue/CPS-107/t-36-modal-de-detalle-de-evidencias-limitar-conexiones-en-grafo-a-3)</td>
<td>`T-36`</td>
<td>Modal de detalle de evidencias: limitar conexiones en grafo a 3 con píldora interactiva +N más y expandir/colapsar</td>
<td>High</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-108](https://linear.app/checkpoint-std/issue/CPS-108/t-37-corrida-de-evaluacion-y-control-de-niveles-en-grafos-ficha-y-red)</td>
<td>`T-37`</td>
<td>Corrida de Evaluación y control de niveles en grafos (Ficha y Red Global)</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-109](https://linear.app/checkpoint-std/issue/CPS-109/t-38-ordenar-leads-del-mas-reciente-al-mas-antiguo-por-defecto)</td>
<td>`T-38`</td>
<td>Ordenar leads del más reciente al más antiguo por defecto</td>
<td>High</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-110](https://linear.app/checkpoint-std/issue/CPS-110/t-39-sugerencias-de-evidencias-raggraphrag-buscador-semantico-y)</td>
<td>`T-39`</td>
<td>Sugerencias de evidencias RAG/GraphRAG, buscador semántico y detección de contradicciones en Leads y Bandeja</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-111](https://linear.app/checkpoint-std/issue/CPS-111/t-40-agente-copiloto-editorial-con-vercel-ai-sdk-y-herramientas-de)</td>
<td>`T-40`</td>
<td>Agente Copiloto Editorial con Vercel AI SDK y herramientas de plataforma</td>
<td>Urgent</td>
<td><span color="green">● Done</span></td>
</tr>
<tr>
<td>[CPS-103](https://linear.app/checkpoint-std/issue/CPS-103/synthesizer-emit-per-sentence-classification-and-per-claim-support-for)</td>
<td>`CORE`</td>
<td>Synthesizer: emit per-sentence classification and per-claim support for the draft</td>
<td>Medium</td>
<td><span color="green">● Done</span></td>
</tr>
</table>

---

### 🔍 Catálogo Detallado de Tareas (Detalles Desplegables)

Haz clic en cualquier tarea para desplegar y revisar su descripción técnica original registrada en Linear:

<details>
<summary><strong>CPS-70: [T-01] Provisionar Notion Business y sincronizar las 8 páginas [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-70](https://linear.app/checkpoint-std/issue/CPS-70/t-01-provisionar-notion-business-y-sincronizar-las-8-paginas) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** El reto exige un espacio Notion accesible al jurado al cierre. Es **condición de admisión**, no de puntaje. Hoy `NOTION_TOKEN`/`NOTION_PARENT_PAGE_ID` están vacíos; todo vive en Markdown + `scripts/sync_notion.py`.
	
	**Qué hacer:**
	
	* Confirmar acceso/cupos de la licencia Notion Business del reto (participantes + jurado).
	* Crear la página raíz y obtener `NOTION_TOKEN` + `NOTION_PARENT_PAGE_ID`.
	* Correr `scripts/sync_notion.py` para publicar las 8 páginas (`docs/notion/01..08`).
	* Compartir con jurado (solo lectura) y verificar que la URL abre sin login propio.
	
	**✅ Criterios de aceptación:**
	
	* URL de Notion pública/al jurado funcionando con las 8 páginas obligatorias.
	* Permisos verificados (jurado puede ver, no editar).
	* Secretos solo en `.env` local (no en repo ni en capturas).
	
	📎 Reto §5 (admisión) · Rúbrica: Notion ejecución y pitch (15).
</details>

<details>
<summary><strong>CPS-71: [T-02] Alinear documentación contradictoria a estado real [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-71](https://linear.app/checkpoint-std/issue/CPS-71/t-02-alinear-documentacion-contradictoria-a-estado-real) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** `ROADMAP.md` marca todo "hecho" con el mismo timestamp, pero `notion/02-plan-y-decisiones.md` dice tareas 2–11 "pendiente" y `notion/07-riesgos-y-etica.md` marca controles "pendiente (Fase 4)". Los tres se contradicen → riesgo de credibilidad ante el jurado.
	
	**Qué hacer:**
	
	* Auditar qué está realmente implementado vs. documentado (cruzar con tests que pasan).
	* Unificar el backlog en `notion/02` con estados verídicos y responsables reales (Alek/Pedro).
	* Actualizar `ROADMAP.md` (registro de modificaciones) y `notion/07` (estados de control reales).
	* Dejar ≥8 tareas y ≥3 decisiones justificadas con estados honestos (requisito §5).
	
	**✅ Criterios de aceptación:**
	
	* Sin contradicciones entre ROADMAP, notion/02 y notion/07.
	* Backlog refleja estos tickets de Linear.
	* "Registro durante la ejecución" visible, no solo resumen final.
	
	📎 Reto §5 (≥8 tareas, ≥3 decisiones) · Rúbrica: Notion (15), Calidad técnica (10).
</details>

<details>
<summary><strong>CPS-72: [T-03] Verificar demo ejecutable end-to-end (compose + README + acceso jurado) [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-72](https://linear.app/checkpoint-std/issue/CPS-72/t-03-verificar-demo-ejecutable-end-to-end-compose-readme-acceso-jurado) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** El entregable es un prototipo ejecutable sin depender de fuente en vivo, con repo accesible al jurado. Los tests pasan, pero falta confirmar el recorrido completo real en UI.
	
	**Qué hacer:**
	
	* `docker compose up --build` desde cero levanta backend, worker, frontend, Qdrant, Redis, Postgres y nginx sin pasos manuales.
	* Recorrido UI completo: cargar → ranking → abrir ficha/árbol → generar brief → exportar Markdown.
	* README con instalación, comando de ejecución, dependencias fijadas y `.env.example` sin secretos.
	* Confirmar acceso del jurado al repo GitHub.
	
	**✅ Criterios de aceptación:**
	
	* Arranque limpio documentado (captura/gif del recorrido).
	* README reproducible por un tercero.
	* `.env.example` sin secretos; `.git` sin tokens.
	
	📎 Reto §10 (entregables) · Rúbrica: Prototipo y flujo completo (20), Calidad técnica (10).
</details>

<details>
<summary><strong>CPS-73: [T-04] Ampliar TVN RSS a 90 días + añadir feeds panameños hasta ≥100 noticias [Done | High]</strong></summary>
	**Enlace en Linear:** [CPS-73](https://linear.app/checkpoint-std/issue/CPS-73/t-04-ampliar-tvn-rss-a-90-dias-anadir-feeds-panamenos-hasta-100) | **Estado:** `Done` | **Prioridad:** `High`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** El reto pide mínimo operativo **100 noticias con ≥20 de TVN**. Hoy el seed tiene solo 40 TVN (GDELT devuelve 429). Decisión: no depender de GDELT.
	
	**Qué hacer:**
	
	* Ampliar la ventana del fetcher TVN RSS de 30 → 90 días (§6A permite ampliar y registrar cobertura efectiva).
	* Añadir 1–2 feeds RSS panameños públicos adicionales (documentar fuente, URL, licencia/condiciones en el catálogo).
	* Mantener dedup por URL + similitud de titular; conservar todas las fuentes del grupo.
	* Registrar cobertura efectiva y la limitación GDELT 429 en `notion/03`.
	
	**✅ Criterios de aceptación:**
	
	* ≥100 noticias únicas, ≥20 de TVN, en `noticias.csv`.
	* Nuevas fuentes con metadatos y licencia en el catálogo de datos.
	* GDELT documentado como no utilizado (con receta/metadatos, sin contenido).
	
	📎 Reto §6A, §12 · Rúbrica: Prototipo y flujo (20), Seguridad/derechos (5).
	⚠️ Bloquea a T-05, T-08, T-10 (necesitan el corpus ampliado).
</details>

<details>
<summary><strong>CPS-74: [T-05] Regenerar snapshot + manifest.json con SHA-256 y conteos [Done | High]</strong></summary>
	**Enlace en Linear:** [CPS-74](https://linear.app/checkpoint-std/issue/CPS-74/t-05-regenerar-snapshot-manifestjson-con-sha-256-y-conteos) | **Estado:** `Done` | **Prioridad:** `High`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** El contrato de datos exige snapshot congelado + `manifest.json` con versión, fecha de corte UTC, consultas, conteos por archivo, licencias/condiciones, SHA-256 y transformaciones.
	
	**Qué hacer:**
	
	* Regenerar `noticias.csv`, `indicadores.csv`, `eventos.geojson`, `fichas.jsonl` con el corpus ampliado (T-04).
	* Recalcular `manifest.json` (hashes + conteos reales + fecha de corte ≥72h antes del evento).
	* Guardar `raw/`, `processed/`, manifest y diccionario; conservar nulos y unidades originales.
	* Confirmar campos mínimos por archivo exactamente como §7.
	
	**✅ Criterios de aceptación:**
	
	* `manifest.json` válido con SHA-256 por archivo y conteos que cuadran.
	* Campos mínimos de §7 presentes en cada archivo.
	* Fecha de corte documentada.
	
	📎 Reto §6, §7 · Rúbrica: Calidad técnica (10), Evidencias (15).
</details>

<details>
<summary><strong>CPS-75: [T-06] Reporte de calidad sobre el corpus ampliado (T01 del contrato) [Done | High]</strong></summary>
	**Enlace en Linear:** [CPS-75](https://linear.app/checkpoint-std/issue/CPS-75/t-06-reporte-de-calidad-sobre-el-corpus-ampliado-t01-del-contrato) | **Estado:** `Done` | **Prioridad:** `High`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** La etapa 1 del prototipo (Cargar) debe validar IDs, URLs, fechas, campos obligatorios y filas nulas, y emitir un reporte de calidad sin bloquear toda la carga.
	
	**Qué hacer:**
	
	* Correr validadores sobre el nuevo snapshot: UTF-8, IDs estables, fechas ISO 8601 UTC, URLs, nulos conservados.
	* Verificar `GET /ingest/quality-report` con numerador/denominador y filas excluidas documentadas.
	* Mantener `fecha_publicacion` distinta de `seendate` de GDELT (si aplica).
	
	**✅ Criterios de aceptación:**
	
	* Reporte de calidad reproducible con conteos reales.
	* Filas inválidas separadas, no bloquean la carga (consistente con T01).
	* Revisiones/exclusiones documentadas.
	
	📎 Reto §3 (Etapa 1), §7 reglas de integridad · Rúbrica: Prototipo y flujo (20).
</details>

<details>
<summary><strong>CPS-76: [T-07] Generación real con Together.ai: briefs con citas + anti-inyección [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-76](https://linear.app/checkpoint-std/issue/CPS-76/t-07-generacion-real-con-togetherai-briefs-con-citas-anti-inyeccion) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** Hoy `TOGETHER_API_KEY` está vacío y todos los briefs responden abstención/placeholder. Sin generación real no se puede demostrar el borrador con citas ni medir validez de sustento (golpea Evidencias 15 + Uso de IA 15).
	
	**Qué hacer:**
	
	* Configurar `TOGETHER_API_KEY` (clave fuera del repo/Notion público).
	* Generar brief TVN (≤250 palabras), guion 45–60s, copy ≤80 palabras, con citas `[id_fuente:campo]` por afirmación.
	* Separar instrucciones del contenido de fuentes; tratar el texto de fuente como dato (anti-inyección, T07).
	* Distinguir hechos / declaraciones / inferencias / hipótesis; abstención explícita sin evidencia.
	* Si solo hay titular/metadatos, la salida debe decir "basado únicamente en titular/metadatos".
	
	**✅ Criterios de aceptación:**
	
	* Brief real generado con citas verificables a IDs del corpus.
	* Prompt injection de fuente no altera comportamiento (T07 verde con corpus real).
	* Cobertura de citas 100% (validador remueve IDs desconocidos).
	
	📎 Reto §3 (Producir), §8 (IA, anti-inyección) · Rúbrica: Uso de IA (15), Evidencias (15).
	⚠️ Depende de T-04/T-05 (corpus).
</details>

<details>
<summary><strong>CPS-77: [T-08] Medir validez de sustento (≥30 afirmaciones) + tokens/costo/latencia [Done | High]</strong></summary>
	**Enlace en Linear:** [CPS-77](https://linear.app/checkpoint-std/issue/CPS-77/t-08-medir-validez-de-sustento-30-afirmaciones-tokenscostolatencia) | **Estado:** `Done` | **Prioridad:** `High`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** El reto fija metas medibles: validez de sustento ≥90% por revisión humana sobre ≥30 afirmaciones, y eficiencia (tokens/costo/latencia). Hoy "pendiente de key".
	
	**Qué hacer:**
	
	* Generar ≥30 afirmaciones reales (T-07) y hacer revisión humana de sustento (respaldada por evidencia citada).
	* Registrar validez (numerador/denominador), no esconder fallos tras promedio.
	* Medir tiempo mediano y p95, tokens y costo por consulta en el entorno declarado (meta mediana ≤15 s).
	
	**✅ Criterios de aceptación:**
	
	* Validez de sustento reportada con ≥30 afirmaciones revisadas.
	* Tabla de eficiencia (mediana/p95, tokens, costo) en `notion/06`.
	* Modelo/proveedor/versión/prompts/parámetros documentados.
	
	📎 Reto §8, §9.1 · Rúbrica: Uso de IA (15), Calidad técnica (10).
	⚠️ Depende de T-07.
</details>

<details>
<summary><strong>CPS-78: [T-09] Baseline de palabras clave + comparación medida vs IA [Done | High]</strong></summary>
	**Enlace en Linear:** [CPS-78](https://linear.app/checkpoint-std/issue/CPS-78/t-09-baseline-de-palabras-clave-comparacion-medida-vs-ia) | **Estado:** `Done` | **Prioridad:** `High`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** La rúbrica exige comparar al menos una tarea con un baseline simple y **explicar qué mejora aporta la IA y cuándo no ayuda**. Hoy el código menciona "baseline" pero no hay comparación calculada.
	
	**Qué hacer:**
	
	* Implementar un baseline simple: recuperación por palabras clave (BM25/TF-IDF) y/o ranking por fecha.
	* Comparar contra el pipeline real (Multi-RAG semántico + scoring) en una tarea medible: Precision@5 de recuperación/ranking y/o acierto de abstención.
	* Reportar dónde la IA mejora y dónde no aporta (ser honesto con las limitaciones).
	
	**✅ Criterios de aceptación:**
	
	* Baseline ejecutable y reproducible.
	* Métrica comparativa (ej. Precision@5 semántico vs keyword) con números.
	* Conclusión explícita "qué mejora la IA y cuándo no" en `notion/06`.
	
	📎 Reto §8 (baseline) · Rúbrica: Uso de IA (15).
	⚠️ Depende de T-04 (corpus).
</details>

<details>
<summary><strong>CPS-79: [T-10] Ejecutar benchmark 40/20 y reportar métricas de clasificación/abstención [Done | High]</strong></summary>
	**Enlace en Linear:** [CPS-79](https://linear.app/checkpoint-std/issue/CPS-79/t-10-ejecutar-benchmark-4020-y-reportar-metricas-de) | **Estado:** `Done` | **Prioridad:** `High`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** El reto pide benchmark de 60 consultas (30 sustentadas, 10 contradicción, 10 sin respuesta, 10 adversariales), usando 40 para desarrollo y reservando 20 al jurado, con métricas reportadas (no mezclar reservadas con el corpus del agente). El `benchmark.jsonl` ya existe con los 60/tipos correctos.
	
	**Qué hacer:**
	
	* Ejecutar el benchmark de desarrollo (40) y guardar salidas; mantener 20 reservadas.
	* Reportar: cobertura de citas (100%), abstención correcta (≥80% de sin-respuesta), y abstenciones incorrectas en preguntas respondibles.
	* Clasificación/agrupación: macro-F1 o precisión/recall vs etiquetas humanas (indicar tamaño y método de etiquetado).
	
	**✅ Criterios de aceptación:**
	
	* Resultados con numerador/denominador y fallos visibles.
	* 20 consultas reservadas sin usar en desarrollo.
	* Métricas en `notion/06` + matriz del §9.
	
	📎 Reto §7 (benchmark), §9.1 · Rúbrica: Evidencias (15), Calidad técnica (10).
	⚠️ Depende de T-04, T-07.
</details>

<details>
<summary><strong>CPS-80: [T-11] Relevancia por medio (scoring v1.2): arreglar ranking degenerado [Done | High]</strong></summary>
	**Enlace en Linear:** [CPS-80](https://linear.app/checkpoint-std/issue/CPS-80/t-11-relevancia-por-medio-scoring-v12-arreglar-ranking-degenerado) | **Estado:** `Done` | **Prioridad:** `High`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** Por la limitación D08, toda noticia TVN puntúa R=0.3 (el título no nombra "Panamá"), así que casi todo sale 60.5/medio/parcial. Una priorización donde todo empata se ve débil en los 4 min de demo.
	
	**Qué hacer:**
	
	* Añadir relevancia por medio: si el medio es panameño (TVN, etc.), R no debe colapsar a 0.3 por ausencia del token "Panamá" en el título.
	* Recalibrar bandas (bajo/medio/alto) con el corpus ampliado (T-04), no con 40 registros.
	* Versionar reglas (v1 → v1.2) y permitir justificar cambios de pesos; mostrar versión de reglas en la UI/ficha.
	* Mantener el puntaje como herramienta de ordenamiento (no probabilidad de verdad).
	
	**✅ Criterios de aceptación:**
	
	* Ranking con dispersión real (no todo 60.5); casos alto/medio/bajo visibles.
	* Componentes explicados y versión de reglas mostrada.
	* Cambio documentado en DECISIONS (supera D08).
	
	📎 Reto §3 (Priorizar), §4 (puntaje) · Rúbrica: Evidencias y explicabilidad (15).
	⚠️ Depende de T-04.
</details>

<details>
<summary><strong>CPS-81: [T-12] Refactor UI/UX del frontend (DESIGN.md): lead-stepper secuencial + flujo de demo [Done | High]</strong></summary>
	**Enlace en Linear:** [CPS-81](https://linear.app/checkpoint-std/issue/CPS-81/t-12-refactor-uiux-del-frontend-designmd-lead-stepper-secuencial-flujo) | **Estado:** `Done` | **Prioridad:** `High`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** 4 de los 10 min de pitch son demo en vivo (una consulta útil, una ficha con citas, un borrador y un caso de abstención). Hoy la UI es el shadcn/slate por defecto (se ve "templated"), sin identidad propia ni dark mode real, y `/leads/[id]` vuelca todo en un scroll único donde **"Generar borrador" siempre está habilitado** — se puede producir un borrador sin evidencia previa. Este ticket ejecuta el refactor guiado por `DESIGN.md` (raíz del repo).
	
	**Referencia de diseño:** `DESIGN.md` — sistema propio "consola de evidencia" (serif editorial + sans + mono para datos, sistema de estados disciplinado, claro+oscuro). Implementar por componente, referenciándolos por su nombre estable.
	
	**Qué hacer:**
	
	**A) Base de tokens y tipografía (primero, desbloquea el resto)**
	
	* Mapear tokens de `DESIGN.md` a `assets/css/tailwind.css` (swap de valores HSL → nuevos nombres: primary ink-blue, canvas papel, surface, surface-sunken, hairline, ink/ink-muted, estados).
	* Añadir 3 fuentes: Source Serif 4 (títulos), Inter (UI), IBM Plex Mono (IDs/citas/scores); `tabular-nums` en scores/métricas.
	* Dark mode real bajo `.dark` + toggle en el `app-bar` (hoy `darkMode:class` existe pero sin toggle). Claro por defecto (seguro para proyector).
	
	**B) lead-stepper secuencial con gating (núcleo)**
	
	* Reemplazar el scroll único de `pages/leads/[id].vue` por un flujo de 6 pasos: **Definir → Evidencia → Contexto & Priorización → Ficha → Borrador → Revisión** (mapea las 7 etapas del reto).
	* Estados por paso: complete / current / available / locked / blocked.
	* **Gating (regla de integridad, NO es cosmético):** Paso 5 (Borrador) bloqueado salvo `evidence_state ∈ {parcial, suficiente}`. En `insuficiente` → estado `blocked` con motivo visible y dos salidas: *vincular más evidencia* o *registrar abstención* (`abstention-card`). El botón "Generar borrador" nunca queda clickeable desde un estado no soportado. Paso 6 (Revisión) solo tras existir borrador o abstención.
	* Desktop (`lg`): rail lateral sticky con pasos + resumen del lead; tablet: stepper horizontal; móvil: strip "Paso n/6" + sheet.
	
	**C) Componentes firma y restyle**
	
	* `score-breakdown`: total P (mono) + chip de banda + 5 barras R/I/U/N/E con valor 0–1 y peso + versión de reglas como `id-token`.
	* `state-system`: chips consistentes (evidencia suficiente/parcial/insuficiente, bandas bajo/medio/alto, 5 estados de revisión) aplicados en bandeja, stepper, árbol y ficha.
	* `id-token` mono para IDs y citas `[id:campo]` con procedencia al hover.
	* `abstention-card` como estado de primera clase (no error).
	* Restyle de `RankingTable` (bandeja), `EvidenceTree`/`TreeBranch` y `app-bar` según `DESIGN.md`.
	
	**D) Flujo end-to-end + demo**
	
	* Recorrido sin fricción: bandeja → abrir lead → stepper (evidencia → priorización → ficha → borrador real → export MD); abstención visible; distinción hecho/inferencia.
	* Estados de revisión humana operativos; mostrar "hora de Panamá" (§7).
	
	**✅ Criterios de aceptación:**
	
	* Tokens, 3 fuentes y dark mode (con toggle) implementados; paridad claro/oscuro verificada.
	* `/leads/[id]` es un stepper secuencial; **imposible generar borrador con evidencia insuficiente** (ruta a abstención o a vincular evidencia).
	* `score-breakdown`, `state-system`, `id-token`, `abstention-card` aplicados; bandeja y árbol restyleados.
	* Recorrido demo ensayado sin fricción; árbol + citas + abstención visibles en vivo.
	
	📎 Reto §3 (Priorizar/Explicar/Producir), §11 (pitch) · `DESIGN.md` · Rúbrica: Prototipo y flujo (20), Utilidad (20), Evidencias y explicabilidad (15).
	⚠️ Depende de T-07 (<issue id="c53b6049-dcb6-4a93-b693-4958bb6fd67d" href="https://linear.app/checkpoint-std/issue/CPS-76/t-07-generacion-real-con-togetherai-briefs-con-citas-anti-inyeccion">CPS-76</issue>, generación real) y T-11 (<issue id="de0b5750-84a9-4cec-a0b7-c32f660a87e7" href="https://linear.app/checkpoint-std/issue/CPS-80/t-11-relevancia-por-medio-scoring-v12-arreglar-ranking-degenerado">CPS-80</issue>, ranking con dispersión). Subtarea A (tokens/fuentes/dark) puede arrancar ya, en paralelo.
</details>

<details>
<summary><strong>CPS-82: [T-13] Banca mínima: 1 boletín de entorno como demo de extensión [Done | Medium]</strong></summary>
	**Enlace en Linear:** [CPS-82](https://linear.app/checkpoint-std/issue/CPS-82/t-13-banca-minima-1-boletin-de-entorno-como-demo-de-extension) | **Estado:** `Done` | **Prioridad:** `Medium`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** Decisión de alcance: TVN a fondo + Banca mínima. Mostrar "mismo núcleo, otra salida" sin invertir en dos productos completos.
	
	**Qué hacer:**
	
	* Generar 1 boletín de entorno bancario: resumen ≤250 palabras, sectores potencialmente relacionados, horizonte temporal, evidencia y 3 preguntas para el analista.
	* Separar observación de hipótesis de impacto; **no** recomendar compra/venta ni inferir pérdidas/impagos/exposición de cartera inexistente.
	* Usar indicadores del Banco Mundial para contexto (citar país/año/unidad; no describir dato anual como "de hoy").
	
	**✅ Criterios de aceptación:**
	
	* 1 boletín banca demostrable con citas y preguntas.
	* Sin recomendaciones de inversión ni veredictos.
	* Usa el mismo núcleo (ranking/evidencia) que TVN.
	
	📎 Reto §2 (banca), §3 (salida bancaria), §4 (CU-05) · Rúbrica: Utilidad (20).
</details>

<details>
<summary><strong>CPS-83: [T-14] Actualizar 5+ fichas trazables con briefs reales (incl. 1 sin evidencia) [Done | Medium]</strong></summary>
	**Enlace en Linear:** [CPS-83](https://linear.app/checkpoint-std/issue/CPS-83/t-14-actualizar-5-fichas-trazables-con-briefs-reales-incl-1-sin) | **Estado:** `Done` | **Prioridad:** `Medium`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** El reto exige ≥5 fichas de casos trazables, incluyendo obligatoriamente un caso sin evidencia suficiente. Hoy las fichas tienen borradores placeholder ("pendiente de key").
	
	**Qué hacer:**
	
	* Regenerar las 5 fichas (`docs/casos/caso_*.md`) con briefs reales (T-07) y puntaje desglosado real (post T-11).
	* Mantener el caso de abstención (caso_004) como el "sin evidencia suficiente".
	* Cada ficha: IDs, fuentes, puntaje desglosado, estado de evidencia, borrador con citas, persona revisora.
	* Poblar `notion/05-casos-y-evidencias.md` y el espacio Notion real.
	
	**✅ Criterios de aceptación:**
	
	* 5+ fichas con borrador real y citas verificables.
	* 1 caso sin evidencia suficiente explícito.
	* Reflejadas en Notion (Casos y Evidencias).
	
	📎 Reto §5 (≥5 fichas), §3 (Explicar) · Rúbrica: Evidencias (15).
	⚠️ Depende de T-07, T-11.
</details>

<details>
<summary><strong>CPS-84: [T-15] Matriz T01–T10 con resultados observados reales [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-84](https://linear.app/checkpoint-std/issue/CPS-84/t-15-matriz-t01-t10-con-resultados-observados-reales) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** El reto exige la matriz de los 10 casos de prueba (§9) con resultados y métricas de la ejecución final. Hoy la matriz existe pero con observados de un corpus de 40 y generación apagada.
	
	**Qué hacer:**
	
	* Re-ejecutar T01–T10 con corpus ampliado (T-04) y generación real (T-07).
	* Actualizar observados reales en `notion/06` y `test_acceptance.py` si cambian fixtures.
	* Confirmar T07 (anti-inyección) y T10 (offline) con el pipeline real.
	
	**✅ Criterios de aceptación:**
	
	* 10/10 con resultado esperado vs observado real.
	* Evidencia enlazada (test + captura/registro).
	* Suite `pytest` en verde.
	
	📎 Reto §9 · Rúbrica: Calidad técnica y evaluación (10).
	⚠️ Depende de T-04, T-07.
</details>

<details>
<summary><strong>CPS-85: [T-16] Verificar modo offline/fallback (T10) para la demo sin internet [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-85](https://linear.app/checkpoint-std/issue/CPS-85/t-16-verificar-modo-offlinefallback-t10-para-la-demo-sin-internet) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** El reto permite que la demo corra sin internet con snapshot y fallback documentado (T10), y el pitch no debe depender de una fuente en vivo. Con generación real ([Together.ai](<http://Together.ai>)) hay que definir el comportamiento sin red.
	
	**Qué hacer:**
	
	* Verificar `USE_SEED_SNAPSHOT=true`: ingesta, ranking, fichas y árbol operan sin red.
	* Definir y documentar el fallback de generación sin red (abstención estructurada o respuesta cacheada para la demo), sin inventar contenido.
	* Ensayar la demo en modo offline de punta a punta.
	
	**✅ Criterios de aceptación:**
	
	* Recorrido completo funciona sin internet (salvo generación, con fallback claro).
	* Fallback documentado en DECISIONS + Notion.
	* Ensayo offline exitoso.
	
	📎 Reto §3 (T10), §8 (arquitectura), §11 · Rúbrica: Calidad técnica (10), Prototipo (20).
</details>

<details>
<summary><strong>CPS-86: [T-17] Pitch de 10 min desde Notion (guion por minuto + embeds + ensayo) [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-86](https://linear.app/checkpoint-std/issue/CPS-86/t-17-pitch-de-10-min-desde-notion-guion-por-minuto-embeds-ensayo) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** El pitch de 10 min presentado **desde Notion** es obligatorio (un PDF/PPT no lo reemplaza). Debe ser navegable, con enlaces/embeds al prototipo y GitHub.
	
	**Qué hacer (guion exacto §11):**
	
	* 1 min: problema, usuario y por qué importa a TVN.
	* 1 min: solución, alcance y datos públicos usados.
	* 4 min: demo en vivo — una consulta útil, una ficha con citas, un borrador y un caso de abstención (mostrar el árbol).
	* 2 min: arquitectura, uso sustantivo de IA, baseline y métricas observadas.
	* 1 min: valor operativo medido o hipótesis de valor.
	* 1 min: riesgos, límites y próximos pasos.
	* Preparar respuestas a las pruebas dinámicas del jurado (de dónde viene una cifra, réplicas vs fuentes, qué pasa sin evidencia / con inyección, mostrar una decisión y una prueba fallida con su corrección).
	
	**✅ Criterios de aceptación:**
	
	* Página Notion "Presentación al jurado" navegable con embeds a demo + GitHub.
	* Ensayo cronometrado ≤10 min.
	* Respuestas a las 4 pruebas dinámicas preparadas.
	
	📎 Reto §5, §11 · Rúbrica: Notion ejecución y pitch (15), Utilidad (20).
	⚠️ Depende de casi todo (demo lista).
</details>

<details>
<summary><strong>CPS-87: [T-18] Pasar controles de riesgo/ética de "pendiente" a implementado con evidencia [Done | High]</strong></summary>
	**Enlace en Linear:** [CPS-87](https://linear.app/checkpoint-std/issue/CPS-87/t-18-pasar-controles-de-riesgoetica-de-pendiente-a-implementado-con) | **Estado:** `Done` | **Prioridad:** `High`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** `notion/07` marca varios controles "pendiente (Fase 4)". Seguridad/privacidad/ética es dimensión de rúbrica (5) y condición previa (citas falsas o acciones prohibidas deben corregirse antes del cierre).
	
	**Qué hacer:**
	
	* Anti-alucinación: generación solo sobre evidencia recuperada; citas obligatorias; abstención sin evidencia (evidenciar con T-07/T-10).
	* Anti-inyección: texto de fuente = dato; saneado; T07 verde.
	* Réplica vs corroboración: agencia primaria; N réplicas = 1 procedencia (CU-03).
	* No publicación automática: 5 estados; "aprobado como borrador" ≠ publicar.
	* Derechos: condiciones por fuente en catálogo; solo titulares/metadatos; sin redistribuir.
	* Secretos: fuera de código/Notion/logs.
	* Actualizar estados reales en `notion/07`.
	
	**✅ Criterios de aceptación:**
	
	* Cada control con estado real + evidencia (test/captura/decisión).
	* Escenarios fuera de alcance declarados.
	* Sin secretos en repo/Notion/capturas.
	
	📎 Reto §8 (seguridad y ética) · Rúbrica: Seguridad, privacidad y ética (5).
</details>

<details>
<summary><strong>CPS-88: [T-19] Proteger rama main y hacer cumplir convención de ramas {type}/{ticket_id}_{ticket_name} con Linear [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-88](https://linear.app/checkpoint-std/issue/CPS-88/t-19-proteger-rama-main-y-hacer-cumplir-convencion-de-ramas-typeticket) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:** Proteger la rama `main` local contra commits directos y exigir que todo trabajo se desarrolle en ramas con nombre formal `{type}/{ticket_id}_{ticket_name}`, respaldadas obligatoriamente por un ticket en Linear e integradas mediante Pull Requests.
	
	**Qué hacer:**
	
	* Configurar git hooks locales (`pre-commit`, `pre-push`) que bloqueen commits y pushes directos en `main`.
	* Validar convención de nombres de rama: `{type}/{ticket_id}_{ticket_name}`.
	* Validar que el `ticket_id` exista en Linear.
	* Proveer script/herramientas para verificación y creación estandarizada de ramas.
</details>

<details>
<summary><strong>CPS-89: [T-20] Suite de pruebas E2E (UI Playwright + API httpx) apuntando a dev-evidentia.vertexdc.com y dev-evidentia-api.vertexdc.com [Done | High]</strong></summary>
	**Enlace en Linear:** [CPS-89](https://linear.app/checkpoint-std/issue/CPS-89/t-20-suite-de-pruebas-e2e-ui-playwright-api-httpx-apuntando-a-dev) | **Estado:** `Done` | **Prioridad:** `High`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	El sistema está desplegado en el entorno de desarrollo de Coolify (`dev-evidentia.vertexdc.com` y `dev-evidentia-api.vertexdc.com`). Para asegurar que no existan regresiones entre backend, BFF de Nuxt y frontend, se requiere una suite automatizada de pruebas E2E que valide los flujos críticos de la aplicación en el entorno desplegado real antes del pitch ante el jurado.
	
	**Qué hacer:**
	
	1. **Capa E2E API (Python /** `httpx` **/** `pytest`**):**
	   * Healthcheck y conectividad: `GET /health`
	   * Auditoría y calidad de datos: `GET /ingest/quality-report`
	   * Priorización y desglose de ranking: `GET /leads`
	   * Ficha y grafo relacional: `GET /leads/{id}` y `GET /leads/{id}/graph`
	   * Ciclo de casos de analista: `POST /cases` y `POST /cases/{id}/evidence`
	   * Generación editorial TVN con [Together.ai](<http://Together.ai>): `POST /briefs/generate` (citas y tiempo de respuesta)
	   * Extensión Banca mínima: `POST /briefs/banca`
	2. **Capa E2E UI (Playwright + Bun):**
	   * Flujo 1: Carga de Home/Dashboard (`/`) y verificación de métricas.
	   * Flujo 2: Carga de bandeja de leads (`/leads`), validación de bandas (`ALTO`, `MEDIO`, `BAJO`) y filtrado interactivo.
	   * Flujo 3: Detalle de lead (`/leads/{id}`), renderizado de metadatos y visor del grafo.
	   * Flujo 4: Disparo o visualización de paquete editorial y citas en pantalla.
	   * Flujo 5: Navegación a `/ingest` y visualización del reporte de calidad.
	3. **Configuración y Orquestación:**
	   * Targets en Makefile (`make test-e2e-api`, `make test-e2e-ui`, `make test-e2e`).
	   * Variables parametrizables en `.env` (`E2E_BASE_URL` y `E2E_API_URL`).
	   * Script preflight de conectividad que verifique disponibilidad del servidor antes de correr tests interactivos.
	
	**✅ Criterios de Aceptación:**
	
	* Ambas suites ejecutables con un solo comando o separadas.
	* Reportes de salida limpios con trazas y capturas en caso de fallo.
	* Compatible con ejecución local (`localhost:8080` / `localhost:8001`) y remota (`dev-evidentia*.vertexdc.com`).
</details>

<details>
<summary><strong>CPS-90: [T-21] Autenticación obligatoria en toda la plataforma: login guard global, endpoints asegurados y segregación de credenciales dev/prod [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-90](https://linear.app/checkpoint-std/issue/CPS-90/t-21-autenticacion-obligatoria-en-toda-la-plataforma-login-guard) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	Actualmente la plataforma cuenta con una capa de seguridad con tokens duales JWT (15m / 7d), pero las páginas y los endpoints de negocio son accesibles sin autenticación, y la interfaz proveía la contraseña en pantalla. Este ticket asegura el acceso obligatorio a toda la plataforma, remueve cualquier contraseña por defecto en el cliente y segrega credenciales entre dev y prod.
	
	**Qué hacer:**
	
	1. **Frontend (Nuxt 3):**
	   * Middleware global `middleware/auth.global.ts` que redirija forzosamente a `/login` ante cualquier ruta no autenticada.
	   * Página dedicada `/login` con campos limpios (sin contraseñas por defecto ni botones de relleno de secretos).
	   * Barra superior con perfil activo y botón de cierre de sesión inmediato.
	2. **Backend (FastAPI):**
	   * Blindaje de routers de negocio (`/ranking`, `/cases`, `/ingest`, `/evidence`) con `Depends(get_current_user)` devolviendo `401 Unauthorized` si no hay token.
	   * Preservar `/health` y `/ready` públicos para monitorización de contenedores.
	3. **Credenciales y Configuración:**
	   * Generar y configurar contraseñas robustas diferenciadas para DEV (`Vtx-Dev-EvidentIA#2026!7x`) y PROD (`Vtx-Prod-EvidentIA$2026!9k`).
	   * Actualizar variables de entorno en Coolify para ambas aplicaciones.
	4. **Pruebas:**
	   * Actualizar suites unitarias y E2E para verificar el bloqueo 401 y el flujo de login.
	
	**✅ Criterios de Aceptación:**
	
	* Ninguna página accesible sin login previo.
	* Ningún endpoint de negocio responde sin `Authorization: Bearer <token>`.
	* Formulario de login sin contraseñas precargadas.
	* Todas las suites de prueba en verde.
</details>

<details>
<summary><strong>CPS-91: [T-22] Migración total de Docker frontend y toolchain a Bun (eliminar npm y package-lock.json) [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-91](https://linear.app/checkpoint-std/issue/CPS-91/t-22-migracion-total-de-docker-frontend-y-toolchain-a-bun-eliminar-npm) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	El Dockerfile del frontend utilizaba `node:22-slim` con `npm ci` y `npm run build`, además de mantener un `package-lock.json` obsoleto de 425 KB en el repositorio, violando la directriz global de tooling (`Primary package manager for JS/TS: bun`). Esto causaba que la compilación en Coolify tomara varios minutos descargando paquetes innecesarios en vez de los 2-4 segundos que tarda Bun con `bun.lock`.
	
	**Qué hacer:**
	
	1. **Dockerfile Multi-Stage con Bun:**
	   * Cambiar el stage de compilación a `FROM oven/bun:1-alpine AS build`.
	   * Copiar exclusivamente `package.json` y `bun.lock`.
	   * Ejecutar `RUN bun install --frozen-lockfile` y `RUN bun run build`.
	   * Mantener el runtime ligero con healthchecks funcionales para Nitro.
	2. **Eliminación de package-lock.json:**
	   * Remover `frontend/package-lock.json` del control de versiones.
	3. **Limpieza del Toolchain:**
	   * Actualizar comandos en `Makefile` (`bun install` y `bun run dev` en vez de referencias a `npm`).
	4. **Verificación:**
	   * Comprobar que el build local con `bun` sea 100% limpio y rápido.
	   * Redesplegar en Coolify y verificar tiempos de build drásticamente reducidos.
	
	**Criterios de Aceptación:**
	
	- [ ] `frontend/Dockerfile` no referencia `npm` ni `package-lock.json`.
	- [ ] `frontend/package-lock.json` eliminado del árbol git.
	- [ ] `bun install --frozen-lockfile` y `bun run build` operan en segundos.
	- [ ] `Makefile` limpio de fallbacks de npm.
	- [ ] Frontend operativo y saludable en Coolify dev.
</details>

<details>
<summary><strong>CPS-92: [T-23] Sistema de ingesta automática periódica con feature flag y actualización de noticias en vivo para pitch [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-92](https://linear.app/checkpoint-std/issue/CPS-92/t-23-sistema-de-ingesta-automatica-periodica-con-feature-flag-y) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	Durante la revisión del reto contra la implementación actual, se identificó que la ingesta de noticias operaba únicamente de manera manual o por seed. Para la presentación del pitch ante el jurado de TVN Media, es indispensable contar con noticias actualizadas en tiempo real de la jornada de hoy, además de disponer de un mecanismo de ingesta automática periódica en segundo plano controlado mediante un Feature Flag dinámico que demuestre que EvidentIA es un copiloto activo.
	
	**Qué hacer:**
	
	1. **Configuración y Feature Flag:**
	   * Agregar `auto_ingest_enabled` e `auto_ingest_interval_minutes` en `config.py` y soporte para variables de entorno `AUTO_INGEST_ENABLED` y `AUTO_INGEST_INTERVAL_MINUTES`.
	2. **Scheduler Asíncrono en Backend:**
	   * Crear `backend/src/evidentia/ingestion/scheduler.py` con ciclo periódico en segundo plano integrado al ciclo de vida (`lifespan`) de FastAPI.
	   * Ejecutar la ingesta en vivo (`use_seed=False`) sin bloquear peticiones HTTP concurrentes.
	3. **Endpoints de Gestión:**
	   * `GET /ingest/auto-schedule`: consultar estado del scheduler (activo, intervalo, última y próxima corrida).
	   * `POST /ingest/auto-schedule`: modificar flag e intervalo en caliente.
	   * `POST /ingest/live-now`: forzar sincronización inmediata de noticias en vivo de hoy.
	4. **Interfaz de Usuario (Frontend):**
	   * Añadir en `/ingest` un panel de control interactivo con toggle de Ingesta Automática, selector de intervalo y botón de refresco en vivo ("Ingestar Noticias Frescas de Hoy").
	5. **Pruebas:**
	   * Pruebas unitarias del scheduler y de los nuevos endpoints, preservando las 67 pruebas de backend en verde.
	
	**Criterios de Aceptación:**
	
	- [ ] Scheduler no bloqueante operando en segundo plano en FastAPI.
	- [ ] Feature flag conmutable vía UI y API.
	- [ ] Botón de ingesta en vivo funcional trayendo noticias actuales del feed RSS de TVN y Panamá.
	- [ ] Modo offline T10 protegido cuando el flag esté apagado.
	- [ ] Cobertura de pruebas completa.
</details>

<details>
<summary><strong>CPS-93: [T-24] Configurar auto-deploy en entorno dev sincronizado con Gitea y GitHub Actions [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-93](https://linear.app/checkpoint-std/issue/CPS-93/t-24-configurar-auto-deploy-en-entorno-dev-sincronizado-con-gitea-y) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	El entorno de producción (`main`) cuenta con auto-deploy automático ante cada push, pero el entorno de desarrollo (`dev`) requería disparos manuales. Al auditar la configuración, se identificó que el webhook #27 en Gitea tenía `branch_filter: "main"` y el workflow `.github/workflows/sync-to-gitea.yml` sólo escuchaba la rama `main`.
	
	**Qué hacer:**
	
	1. **Actualizar Gitea Webhook #27:**
	   * Cambiar `branch_filter` de `"main"` a `"*"` para enviar eventos push de `dev` a Coolify.
	2. **Actualizar GitHub Actions:**
	   * Modificar `.github/workflows/sync-to-gitea.yml` para escuchar tanto `main` como `dev` y sincronizar dinámicamente `${GITHUB_REF_NAME}` a Gitea.
	3. **Verificación:**
	   * Verificar que al hacer push a `dev`, Coolify dispare automáticamente el build y deploy de la aplicación `evidentia-ojmtbmfklmfvp9rea8divafz`.
	
	**Criterios de Aceptación:**
	
	- [ ] Gitea webhook #27 acepta eventos de la rama `dev`.
	- [ ] GitHub Actions sincroniza `dev` con Gitea automáticamente.
	- [ ] Push a `dev` inicia despliegue automático en Coolify sin intervención manual.
</details>

<details>
<summary><strong>CPS-94: [T-25] Inspección interactiva de contenido y fuentes de evidencia (Drawer/Modal al hacer clic en nodos del árbol, fichas y ranking) [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-94](https://linear.app/checkpoint-std/issue/CPS-94/t-25-inspeccion-interactiva-de-contenido-y-fuentes-de-evidencia) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	El usuario y el jurado del hackIAthon necesitan inspeccionar y validar directamente qué contenido respalda cada afirmación, tema priorizado o rama de evidencia. Aunque actualmente disponemos de la visualización en árbol jerárquico (`EvidenceTree`, `TreeBranch`), los nodos solo se renderizan como texto estático sin posibilidad de interactuar con ellos ni ver el artículo de prensa original, el titular, el extracto textual, el indicador con su unidad y enlace al Banco Mundial, o el evento sísmico del USGS. De igual forma, en la vista de detalle de caso (`/leads/[id]`) y en el ranking de leads, los usuarios deben poder hacer clic en cualquier evidencia para desplegar su contenido completo de forma inmediata.
	
	**Qué hacer:**
	
	1. **Backend (**`backend/src/evidentia/api/evidence.py`**):**
	   * Implementar endpoint `GET /evidence/detail/{fuente_tipo}/{fuente_id:path}` (y/o lookup unificado) que devuelva el registro enriquecido correspondiente según el tipo:
	     * `news`: titular, url original, medio, fecha de publicación, alcance, idioma, extracto textual, entidades asociadas.
	     * `indicator`: país ISO3, indicador ID, año, valor, unidad, URL oficial de fuente (World Bank, etc.).
	     * `event`: ID de evento, magnitud, hora UTC, lugar geográfico, profundidad, URL de evento sísmico USGS.
	     * `entity`: nombre, tipo (ORG, LOC, PER), menciones asociadas.
	   * Pruebas unitarias en backend para verificar el lookup con fixtures existentes.
	2. **Frontend (Componente Reutilizable & Integración):**
	   * Crear componente modal / slide-over `EvidenceDetailModal.vue` en `frontend/components/` con diseño Tailwind consistente, badges temáticos, metadatos y enlaces directos con target `_blank`.
	   * Integrar interactividad en `TreeBranch.vue` y `EvidenceTree.vue`:
	     * Cursor pointer, hover visual distintivo e icono de inspección (ej. `ExternalLink`, `FileText`, `Eye` de `lucide-vue-next`).
	     * Al hacer clic en un nodo de tipo evidencia o tema, abrir el modal con el detalle cargado on-demand.
	   * Integrar interactividad en `leads/[id].vue`:
	     * Hacer clicables los elementos de la lista de evidencia vinculada para ver la fuente de origen.
	   * Integrar interactividad en `RankingTable.vue`:
	     * Permitir inspeccionar rápidamente el contenido de los leads y sus fuentes clave.
	3. **Verificación & Calidad:**
	   * Validar compilación frontend con `bun run build`.
	   * Validar pruebas backend con `pytest`.
	   * Verificar compatibilidad con los flujos de demo del pitch de 10 minutos.
</details>

<details>
<summary><strong>CPS-95: [T-26] Visualizador interactivo de grafo de dependencias GraphRAG nativo (Fuerza dirigida SVG a 60 FPS) [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-95](https://linear.app/checkpoint-std/issue/CPS-95/t-26-visualizador-interactivo-de-grafo-de-dependencias-graphrag-nativo) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	Para la presentación del pitch ante el jurado de TVN Media, visualizar las cadenas de causalidad y dependencias del GraphRAG únicamente como texto indentado resulta plano y poco dinámico. Desarrollamos un motor interactivo y dinámico de grafo de fuerza dirigida (Force-directed graph) en SVG nativo sin dependencias externas pesadas, que permite ver la red viva de relaciones semánticas entre leads, noticias, indicadores del Banco Mundial, eventos sísmicos y entidades.
	
	**Qué se implementó:**
	
	1. **Componente** `ForceGraph.vue` **(**`frontend/components/ForceGraph.vue`**):**
	   * Motor de simulación física continua a 60 FPS propio de EvidentIA (partículas, repulsión culombiana, resortes elásticos, fricción y amortiguación).
	   * Mapeo semántico de colores y radios por tipo de nodo GraphRAG:
	     * `case`: Lead Central (Dark / Primary)
	     * `news`: Noticia de Prensa (Azul / Info)
	     * `indicator`: Indicador Oficial Banco Mundial (Teal)
	     * `event`: Evento Sísmico USGS (Ámbar / Warning)
	     * `entity`: Entidad del Grafo (Púrpura / Purple)
	   * Interactividad completa:
	     * Arrastre de nodos (drag & drop con fijación y recalentamiento físico).
	     * Zoom suave con rueda de ratón y paneo con ratón.
	     * Resaltado automático de vecinos y atenuación de nodos desconectados al pasar el cursor (`hover`).
	     * Tooltip contextual que sigue el cursor.
	     * Click en cualquier nodo para disparar `inspectNode` y abrir `EvidenceDetailModal`.
	2. **Integración en** `EvidenceTree.vue`**:**
	   * Selector de modo de visualización:
	     * **Vista Árbol**: Jerarquía indentada por niveles L1..L5.
	     * **Vista Grafo GraphRAG**: Simulación dinámica interactiva con controles de zoom, centrado y leyenda interactiva.
	   * Conectar eventos de clic de nodo con `EvidenceDetailModal` para inspección de contenido en 1 clic.
	3. **Página Global de Red GraphRAG (**`/graph`**):**
	   * Endpoint en backend `GET /evidence/graph` que devuelve todos los nodos y aristas del grafo relacional.
	   * Página en frontend para explorar el grafo global de inteligencia con filtros por tipo de nodo y búsqueda en vivo.
	4. **Verificación y Pruebas:**
	   * Compilación frontend limpia con `bun run build`.
	   * Pruebas unitarias backend pasando al 100% con `pytest`.
</details>

<details>
<summary><strong>CPS-96: [T-27] Modo Jurado TVN (T01–T10): runner de aceptación en vivo, métricas comparadas y atajos interactivos [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-96](https://linear.app/checkpoint-std/issue/CPS-96/t-27-modo-jurado-tvn-t01-t10-runner-de-aceptacion-en-vivo-metricas) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	Tras realizar una contra-referencia exhaustiva con la entrega de otro equipo competidor ("TVN NEXO"), identificamos que su principal argumento de venta ante el jurado es una vista denominada "Modo jurado" que ejecuta en vivo las pruebas de aceptación de la sección 9 del reto (T01–T10) con indicadores verdes.
	Aunque EvidentIA supera ampliamente a la competencia en arquitectura (Nuxt 4 + Tailwind vs React plano), gráficos (GraphRAG vivo interactivo a 60 FPS vs capturas PNG estáticas), seguridad (Dual JWT + RBAC vs cero login) e ingesta en tiempo real (RSS + GDELT scheduler vs snapshot congelado), carecíamos de la pantalla específica en la UI para que el jurado corra y audite la suite de aceptación oficial en 1 clic.
	
	**Qué hacer:**
	
	1. **Backend FastAPI (**`/api/v1/jurado`**):**
	   * Endpoint `GET /api/v1/jurado/pruebas`: Consulta el último estado de la ejecución T01–T10.
	   * Endpoint `POST /api/v1/jurado/pruebas`: Ejecuta `pytest tests/test_acceptance.py` de forma aislada sin red y retorna el desglose detallado de cada una de las 10 pruebas oficiales (T01 a T10), tiempos de ejecución y estado verde/rojo.
	   * Endpoint `GET /api/v1/jurado/metricas`: Expone los resultados del Benchmark 40/20 y comparativa contra el baseline BM25 (cobertura 100%, abstención 100%, validez >= 90%, latencia y costo).
	2. **Frontend Nuxt 4 (**`/jurado`**):**
	   * Vista interactiva con botón "Ejecutar Suite de Aceptación TVN (T01–T10) en Vivo" con cronómetro.
	   * Acordeón de 10 tarjetas con badges de verificación verde para T01–T10 con el enunciado oficial del pliego (§9) y el detalle de aserción.
	   * Tabla de Benchmark "EvidentIA vs Baseline BM25".
	   * Sección de "Preguntas Frecuentes del Jurado": Accesos directos a casos reales (Banco Mundial con año/unidad, duplicados agrupados a 1 procedencia, abstención ante falta de datos, inyección neutralizada con E=0 y grafo dinámico).
	3. **Robustecer resolución de rutas de datos:**
	   * Garantizar que `data/benchmark.jsonl` y `data/seed/` se resuelvan dinámicamente tanto ejecutando pytest desde la raíz del proyecto como desde `backend/`.
</details>

<details>
<summary><strong>CPS-97: [T-28] Citas para borrador: visualización de cita textual fáctica con identificador canónico y copiado dual rápido [Done | High]</strong></summary>
	**Enlace en Linear:** [CPS-97](https://linear.app/checkpoint-std/issue/CPS-97/t-28-citas-para-borrador-visualizacion-de-cita-textual-factica-con) | **Estado:** `Done` | **Prioridad:** `High`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	Al inspeccionar evidencias desde el árbol o las fichas, el usuario y analista editorial necesitan no solo ver el identificador abstracto de la cita (`[id:campo]`), sino la cita textual o extracto fáctico verificado correspondiente, junto con mecanismos de 1 clic para transferirlo a su borrador de nota periodística o reporte de entorno.
	
	**Qué se implementó:**
	
	1. **Backend (**`/api/evidence/{tipo}/{id}`**):**
	   * Incorporado cálculo y retorno estandarizado de `cita_codigo` (ej. `[not-0412:titular]`) y `cita_texto` (la cita textual fáctica exacta).
	   * Soporte para todos los tipos resueltos: noticias de prensa, indicadores del Banco Mundial, eventos del USGS, entidades del grafo y casos.
	   * Pruebas unitarias de resolución en `backend/tests/test_evidence_item.py`.
	2. **Frontend (**`EvidenceDetailModal.vue`**):**
	   * Bloque estilizado "Cita para borrador" con comillas tipográficas, tipografía Source Serif 4 e identificador en IBM Plex Mono según `DESIGN.md`.
	   * Dos botones de copiado rápido con feedback visual de copiado instantáneo:
	     * **Copiar ID:** copia `[id:campo]`.
	     * **Copiar Cita Textual:** copia `"«cita fáctica»" [id:campo]`.
	
	**Criterios de Aceptación Cumplidos:**
	
	* `GET /api/evidence/{tipo}/{id}` incluye `cita_codigo` y `cita_texto`.
	* El modal renderiza la cita textual y permite copiarla en un clic.
	* Cumplimiento estricto de tokens de `DESIGN.md`.
</details>

<details>
<summary><strong>CPS-98: [T-29] Módulo interactivo de Grafo GraphRAG en la Ficha y empaquetado autónomo de datos offline para Docker [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-98](https://linear.app/checkpoint-std/issue/CPS-98/t-29-modulo-interactivo-de-grafo-graphrag-en-la-ficha-y-empaquetado) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	Para la decisión humana informada, el usuario necesita ver la estructura de relaciones de la Ficha como un módulo vivo dentro de su espacio de trabajo antes de confirmar el paso al borrador. Asimismo, la demo offline (T10 del reto) requiere que la imagen Docker del backend contenga localmente el corpus de datos congelado para funcionar en despliegues aislados sin conexión a internet.
	
	**Qué se implementó:**
	
	1. **Módulo de Grafo en la Ficha (**`FichaStep.vue`**):**
	   * Incorporado componente interactivo de Grafo con conteo de nodos y conexiones.
	   * Genera la red causal completa de 5 niveles conectando la afirmación central, fuentes vinculadas, procedencias, entidades, indicadores y correlaciones.
	   * Clics en cualquier nodo del grafo abren el modal de detalle para inspección y copiado de citas.
	2. **Conmutador dinámico en el Lead (**`pages/leads/[id].vue`**):**
	   * Añadido botón interactivo "Ver Grafo Dinámico / Ver como Árbol" en la barra de herramientas del Lead.
	   * Soporte de modo inicial por URL (`?view=graph`).
	3. **Empaquetado offline en Docker y Auto-bootstrap:**
	   * Empaquetados en `backend/data/seed/` los 5 archivos del corpus congelado (`noticias.csv`, `indicadores.csv`, `eventos.geojson`, `fichas.jsonl`, `manifest.json`).
	   * `backend/Dockerfile` actualizado con `COPY data/seed ./data/seed`.
	   * `docker-compose.yml` preconfigurado con `USE_SEED_SNAPSHOT: true` por defecto.
	   * `backend/src/evidentia/main.py`: auto-ingesta del seed snapshot en el arranque cuando la base de datos está vacía y seed está activo.
	
	**Criterios de Aceptación Cumplidos:**
	
	* Grafo interactivo operable dentro del paso Ficha.
	* Dockerfile empaqueta el snapshot sin dependencias de red.
	* `test_T10_seed_mode_never_touches_network` pasando al 100%.
</details>

<details>
<summary><strong>CPS-99: [T-30] Vinculación de fuentes del cluster al abrir Leads desde la bandeja y auto-healing de casos huérfanos [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-99](https://linear.app/checkpoint-std/issue/CPS-99/t-30-vinculacion-de-fuentes-del-cluster-al-abrir-leads-desde-la) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	Al abrir un tema priorizado en la bandeja de temas (como el evento `#evt-5e9c804f6561` con 2 notas · 2 procedencias), el Lead se creaba sin sus fuentes asociadas, provocando que la Ficha de Evidencias y el árbol GraphRAG mostraran únicamente el nodo raíz del caso (1 nodo, 0 relaciones) en lugar de la red completa de fuentes y relaciones interconectadas.
	
	**Qué se implementó:**
	
	1. **Frontend (**`pages/index.vue:openAsLead`**):**
	   * Envío de `evidence_ids: item.ids_fuente || []` junto con el ID del evento y la banda en `flags`.
	2. **Backend API (**`cases.py`**):**
	   * `CaseCreate` extendido con `evidence_ids: list[str] = Field(default_factory=list)`.
	   * Inserción y enlace automático de `models.EvidenceItem` para cada fuente del cluster en \`create_case\`\`.
	   * **Mecanismo de Auto-Healing:** `_auto_link_cluster_evidence()` en `_case_detail` y `case_tree` detecta si un caso existente (como el caso `#32`) no tiene evidencias vinculadas, localiza los artículos del grupo por título o flags y los vincula automáticamente al vuelo.
	   * **Relaciones inter-fuente:** `case_tree` consulta y vincula explícitamente las relaciones directas entre los elementos vinculados (`same_event`, `corroborates`, `mentions`), con deduplicación de aristas mediante `edges_map`.
	3. **Frontend (**`pages/leads/[id].vue`**):**
	   * Botón de recuperación manual "Re-escanear y vincular fuentes del tema" en el estado vacío de evidencias.
	4. **Pruebas Automatizadas:**
	   * Nuevos tests `test_create_case_with_evidence_ids_links_sources_and_relations` y `test_case_auto_healing_populates_empty_case_from_matching_articles` en `test_cases_api.py`.
	
	**Criterios de Aceptación Cumplidos:**
	
	* Al abrir un tema desde la bandeja, el Lead se abre con todas sus fuentes vinculadas.
	* El árbol y grafo GraphRAG renderizan todos los nodos y sus relaciones mutuas.
	* Casos creados previamente sin evidencias se auto-reparan inmediatamente.
</details>

<details>
<summary><strong>CPS-100: [T-31] Modo Jurado: transición a reporte nativo en Markdown (.md) y JSON, eliminación total de XML y ejecución en contenedor [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-100](https://linear.app/checkpoint-std/issue/CPS-100/t-31-modo-jurado-transicion-a-reporte-nativo-en-markdown-md-y-json) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	En el entorno desplegado en contenedor (Docker), el endpoint y vista de Modo Jurado fallaban por completo debido a que el Dockerfile no incluía dependencias dev (pytest) ni copiaba el directorio `tests/`, sumado a una dependencia frágil de un archivo JUnit XML intermedio (`--junitxml`).
	El usuario solicitó eliminar por completo cualquier dependencia o formato XML en favor de un formato popular, legible y estándar para humanos y herramientas: **Markdown (.md)** nativo estructurado, junto con **JSON** para consumo de API.
	
	**Qué se realizó:**
	
	1. **Runner Nativo Zero-XML (**`evidentia.jurado.runner`**):**
	   * Ejecuta las 10 pruebas de aceptación obligatorias (§9) recolectando aserciones y tiempos en memoria sin generar ni parsear ningún archivo XML.
	   * Dispone de fallback resiliente de ejecución programática directa con aislamiento de entorno.
	   * Genera reportes estructurados en Markdown de publicación y JSON.
	2. **Corrección de Contenedor (**`backend/Dockerfile`**):**
	   * Se actualizó el paso de instalación para incluir dependencias de ejecución de tests (`uv sync --frozen`).
	   * Se copió el directorio `tests/` dentro del contenedor (`COPY tests ./tests`).
	3. **Endpoints de Exportación y Descarga (**`evidentia.api.jurado`**):**
	   * `GET /jurado/pruebas`: Retorna JSON que incluye el reporte completo en Markdown.
	   * `GET /jurado/reporte.md`: Descarga directa con cabeceras `Content-Disposition: attachment; filename="reporte_jurado_evidentia.md"`.
	   * `GET /jurado/reporte?formato=markdown`: Visualización directa inline en Markdown.
	4. **Interfaz de Usuario (**`frontend/pages/jurado.vue`**):**
	   * Se añadieron botones de 1-clic para "Descargar (.md)" y "Copiar MD" con feedback interactivo.
	   * Pestañas intercambiables para ver las tarjetas interactivas (§9) o el reporte Markdown formateado en tiempo real.
	   * Eliminación total de cualquier referencia a XML en interfaz y mensajes de error.
	5. **Verificación Automatizada:**
	   * Pruebas unitarias de API en `backend/tests/test_jurado_api.py` verifican los endpoints de Markdown y JSON al 100%.
	   * Build frontend en Nuxt 4 verificado sin errores.
</details>

<details>
<summary><strong>CPS-104: [T-31] Bandeja de temas multimodal auto-generable (Noticias, Indicadores Banco Mundial, Eventos Sísmicos USGS) y escalabilidad a 500+ temas [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-104](https://linear.app/checkpoint-std/issue/CPS-104/t-31-bandeja-de-temas-multimodal-auto-generable-noticias-indicadores) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	La bandeja de temas estaba restringida artificialmente a 20 elementos debido al valor por defecto `limit: 20` en `ranking.py`, y únicamente consideraba artículos de noticias (`models.NewsArticle`). Las 540 observaciones de indicadores macroeconómicos del Banco Mundial y los 82 eventos sísmicos de USGS no se convertían en temas priorizables ni se auto-generaban al ejecutar la ingesta.
	
	**Qué se implementó:**
	
	1. **Servicio Multi-modal de Ranking (**`ranking_service.py`**):**
	   * Agrupación y scoring determinista de noticias (`tipo="news"`).
	   * Generación de series macroeconómicas para Panamá y región (`tipo="indicator"`), con identificadores formales `[PAN:indicador_id:anio]`, rango de años y último valor reportado.
	   * Generación de temas para eventos geofísicos de USGS (`tipo="event"`), con citas formales `[us7000...]`, magnitud, profundidad y ubicación.
	   * Puntuación determinista con pesos oficiales (R, I, U, N, E) y asignación estricta de bandas (`alto`, `medio`, `bajo`) y estado de evidencia (`suficiente`, `parcial`, `insuficiente`).
	   * Persistencia precalculada en `data/processed/ranking_inbox.json`.
	2. **Auto-generación en Pipeline de Ingesta:**
	   * Integrado en `pipeline.run_ingestion` como paso post-ingesta automático.
	   * Integrado en `api/ingest.py:upload_file` para regenerar la bandeja tras cargas exitosas de datos.
	3. **Ampliación de Escala y Filtros en la API (**`/ranking`**):**
	   * Límite por defecto aumentado a 500 (configurable hasta 1000).
	   * Soporte de filtro `tipo`: `all`, `news`, `indicator`, `event`.
	   * Retorno de contadores por familia en `counts_by_type`.
	4. **Frontend (**`frontend/pages/index.vue`**):**
	   * Segmented filter pills interactivos: `[ Todos (N) | 📰 Noticias (N) | 📊 Indicadores (N) | 🌍 Sismos (N) ]`.
	   * Badges visuales por tipo de fuente y metadatos adaptados (observaciones anuales, último dato, magnitud/profundidad).
	   * Previsualización e inspección de citas a 1 clic hacia `EvidenceDetailModal`.
	   * Consulta con `limit: 500`.
	5. **Pruebas y Verificación:**
	   * 3 pruebas unitarias y de integración añadidas en `test_ranking_multimodal.py`.
	   * Suite completa ejecutada: 85 passed.
	   * Desplegado a ramas `dev` de GitHub y Gitea con redeploy en Coolify.
</details>

<details>
<summary><strong>CPS-101: [T-32] Grafo dinámico GraphRAG: disposición Jerarquía Causal (Top-Down) por defecto y conmutador a Red Radial [Done | High]</strong></summary>
	**Enlace en Linear:** [CPS-101](https://linear.app/checkpoint-std/issue/CPS-101/t-32-grafo-dinamico-graphrag-disposicion-jerarquia-causal-top-down-por) | **Estado:** `Done` | **Prioridad:** `High`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	Para mejorar la legibilidad de las relaciones de dependencia y cadenas de causalidad del GraphRAG, se requería que la vista dinámica cargara en una disposición jerárquica estructurada (nodo principal arriba, relaciones directas y secundarias desplegadas hacia abajo), con la posibilidad de alternar a la vista orbital radial tradicional.
	
	**Qué se implementó:**
	
	1. **Algoritmo de Topología Jerárquica Causal (**`computeHierarchicalLayout`**):**
	   * Identificación automática de nodos raíz (leads editoriales, nodos fuente de flujo o hubs temáticos principales) situados en el Nivel 0 superior con halo distintivo.
	   * Traversal BFS para asignación de capas de profundidad (Nivel 1: fuentes primarias, Nivel 2+: indicadores, eventos y entidades).
	   * Distribución horizontal equitativa de nodos por nivel para evitar solapamientos.
	2. **Modo de Física Adaptativa:**
	   * En **Jerarquía Causal**: Anclaje vertical elástico a la capa `y` y posicionamiento en `x`, permitiendo arrastre y exploración interactiva.
	   * En **Red Radial**: Física continua electrostática con resortes inter-nodo.
	3. **Control Segmentado en Barra de Herramientas:**
	   * Botones conmutadores `[🌳 Jerarquía Causal]` y `[🕸️ Red Radial]` con animación suave de transición.
	   * La vista jerárquica causal se establece como la vista predeterminada en `/graph`, `EvidenceTree` y `FichaStep`.
	4. **Verificación:**
	   * Build Nuxt 4 (`bun run build`) validado sin errores.
	   * Commit `711ce13` en `dev` sincronizado en GitHub y Gitea.
</details>

<details>
<summary><strong>CPS-102: [T-33] GraphRAG y Pipeline: poblar Indicadores y Eventos en el grafo y corregir resolución de rutas seed [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-102](https://linear.app/checkpoint-std/issue/CPS-102/t-33-graphrag-y-pipeline-poblar-indicadores-y-eventos-en-el-grafo-y) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	En `/ingest`, el usuario observaba advertencias contradictorias de archivos seed faltantes a pesar de procesar cientos de registros válidos. Paralelamente, en `/graph`, las tarjetas de métricas mostraban 0 para "Indicadores Oficiales" y 0 para "Eventos Geofísicos", debido a que el constructor de relaciones del grafo (`persist_graph`) solo contemplaba artículos de prensa y entidades, omitiendo indicadores y eventos geofísicos de la red de GraphRAG.
	
	**Qué se realizó:**
	
	1. **Resolución Robusta de Rutas Seed (**`pipeline.py`**):**
	   * Se aplicó `resolve_data_path()` tanto para `seed_dir` como para `data_dir`, garantizando que la ruta a los datos congelados se ubique siempre sin importar el directorio de trabajo del proceso.
	   * Eliminación de advertencias espurias en el reporte de calidad.
	2. **Relaciones Cross-Modal para Indicadores y Eventos (**`graph_service.py`**):**
	   * Se extendió `persist_graph` para vincular automáticamente indicadores del Banco Mundial con la entidad país "Panamá" y el tópico "Economía", además de relacionar artículos económicos relevantes con indicadores.
	   * Se vincularon eventos sísmicos de USGS con "Panamá" y con noticias sísmicas mediante la arista `corroborates`.
	3. **Poblado Completo en** `/evidence/graph` **(**`evidence.py`**):**
	   * El endpoint ahora garantiza que tanto indicadores representativos de Panamá como eventos geofísicos formen parte activa del grafo global.
	   * En `/graph`, los indicadores y eventos ahora reportan conteos positivos y aparecen como nodos verdes y naranjas conectados interactivamente en la jerarquía causal.
	4. **Verificación:**
	   * Suite completa de backend (80 tests) pasando al 100%.
	   * Sincronizado en commit `f1a3b3e` en ramas dev de GitHub y Gitea.
</details>

<details>
<summary><strong>CPS-105: [T-34] Reporte Markdown renderizado, ingesta por esquema con plantillas, trazabilidad de duplicados y almacenamiento persistente en Coolify [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-105](https://linear.app/checkpoint-std/issue/CPS-105/t-34-reporte-markdown-renderizado-ingesta-por-esquema-con-plantillas) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	En `/jurado`, el usuario requería visualizar el reporte oficial formateado directamente en Markdown enriquecido (HTML) sin vista dividida (no split view), con opción de alternar entre vista renderizada y código .md crudo.
	En `/ingest`, los usuarios necesitaban poder subir archivos manuales validados contra el esquema estricto de las 4 familias (`noticias.csv`, `indicadores.csv`, `eventos.geojson`, `fichas.jsonl`), descargar plantillas canónicas para cada familia, y registrar trazabilidad completa (`upload_id`, marca de tiempo UTC, estado y detección de duplicados colapsados).
	Asimismo, en el entorno de despliegue en Coolify, se presentaba una advertencia de archivo seed faltante debido a que los volúmenes montados sobreescribían los datos de la imagen Docker.
	
	**Qué se implementó:**
	
	1. **Renderizado de Markdown en** `/jurado` **(Sin Split View):**
	   * Integración de `marked` para renderizado nativo en columna única limpia.
	   * Selector superior: `[ Vista Renderizada (Default) | Código Markdown (.md) ]`.
	   * Estilizado tipográfico completo para tablas, citas, código y encabezados, manteniendo descarga de archivo `.md`.
	2. **Carga Manual por Esquema y Descarga de Plantillas en** `/ingest`**:**
	   * 4 tarjetas de carga con drag-and-drop y validación de esquemas.
	   * Endpoint `GET /ingest/templates/{family}` y botones de descarga de plantillas oficiales con datos muestra válidos.
	3. **Trazabilidad de Carga con** `upload_id` **y Detección de Duplicados:**
	   * Identificador único por subida con timestamp UTC, resumen de duplicados detectados/omitidos e historial interactivo.
	4. **Almacenamiento Persistente en Coolify:**
	   * Inclusión de capa inmutable `/app/seed_frozen` en el Dockerfile del backend y auto-aprovisionamiento del volumen persistente `/app/data` en `entrypoint.sh`.
</details>

<details>
<summary><strong>CPS-106: [T-35] Corrección integral de Leads multi-modales: evidencias dinámicas, modalidad saneada y auto-sanación de casos [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-106](https://linear.app/checkpoint-std/issue/CPS-106/t-35-correccion-integral-de-leads-multi-modales-evidencias-dinamicas) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	Al abrir temas priorizados en la bandeja (ej. `#PAN:FP.CPI.TOTL.ZG` con 15 observaciones anuales de inflación del Banco Mundial o eventos sísmicos USGS) como un Lead (`/leads/[id]`), la vista perdía todos los datos:
	
	1. Las fuentes se filtraban a 0 debido a un Set estático basado únicamente en el catálogo mock de Colón (`not-0412`, etc.), dejando la ficha con "0/2 primarias" y "Evidencia sin fuentes".
	2. La modalidad quedaba corrupta mostrando el ID técnico del tema (ej. `ind:PAN:FP.CPI.TOTL.ZG`).
	3. El puntaje de prioridad calculado y su banda se perdían.
	4. Casos creados previamente sin fuentes no podían auto-recuperar las observaciones de indicadores o sismos.
	
	**Qué se implementó:**
	
	1. **Frontend (**`leadEvidence.ts`**):**
	   * Función `catalogSourceFromEvidenceItem` para transformar filas dinámicas del backend en fuentes de catálogo con citas fácticas, fechas y procedencias oficiales.
	   * `registerDynamicSources` para alimentar `CATALOG_BY_ID` y `PROVENANCE` con fuentes de tipo Indicador y Evento.
	   * `deriveEvidence(linkedIds, catalog)` adaptable a catálogos dinámicos.
	2. **Frontend (**`pages/leads/[id].vue` **y** `pages/index.vue`**):**
	   * Eliminado el filtro restrictivo de IDs estáticos.
	   * Saneada la extracción de modalidad (`TVN`, `Banca` o `Investigación`), ignorando identificadores técnicos.
	   * Transmisión y lectura de score de prioridad y banda (`p:...`, `band:...`).
	   * Pasado de `:custom-catalog="dynamicCatalog"` a `EvidenceStep`, `FichaStep` y `DraftStep`.
	3. **Backend (**`cases.py`**):**
	   * Corrección de `_infer_source_type` para clasificar sismos (`us...`) como `event` y series (`ind:...`, `PAN:...`) como `indicator`.
	   * Enriquecimiento del detalle del caso (`_case_detail`) con citas y descripciones completas.
	   * Auto-sanación en `_auto_link_cluster_evidence` para casos de indicadores y sismos huérfanos o previamente abiertos.
	   * Nuevo endpoint `GET /cases/catalog` para suministrar fuentes reales al cajón de vinculación.
</details>

<details>
<summary><strong>CPS-107: [T-36] Modal de detalle de evidencias: limitar conexiones en grafo a 3 con píldora interactiva +N más y expandir/colapsar [Done | High]</strong></summary>
	**Enlace en Linear:** [CPS-107](https://linear.app/checkpoint-std/issue/CPS-107/t-36-modal-de-detalle-de-evidencias-limitar-conexiones-en-grafo-a-3) | **Estado:** `Done` | **Prioridad:** `High`  
	
	**Descripción Original del Ticket:**  
	**Por qué:**
	En el modal de inspección de evidencias (`EvidenceDetailModal.vue`), cuando un nodo cuenta con un volumen grande de relaciones semánticas en el grafo (como noticias vinculadas a entidades e indicadores macroeconómicos con más de 500 conexiones), la sección de relaciones renderizaba todos los botones en un bloque `flex-wrap` saturando el espacio vertical de la pantalla y desplazando fuera del viewport las secciones críticas de citación para borrador, cita textual y botones de acción.
	
	**Qué se implementó:**
	
	1. **Frontend (**`EvidenceDetailModal.vue`**):**
	   * Estado reactivo `showAllRelaciones` con reinicio automático en `false` cada vez que el modal se abre o cambia de ítem.
	   * Límite por defecto a las primeras 3 conexiones del grafo cuando el total supera 3: `(showAllRelaciones ? item.relaciones : item.relaciones.slice(0, 3))`.
	   * Píldora interactiva `+N más` (ej. `+539 más`) al final de la fila compacta con título explicativo.
	   * Enlace en cabecera `Ver todas (N)` / `Mostrar menos` para alternar entre vista compacta y expandida con un solo clic.
	   * Mantiene permanentemente visibles en el viewport el bloque de citación, cita textual y controles de acción.
</details>

<details>
<summary><strong>CPS-108: [T-37] Corrida de Evaluación y control de niveles en grafos (Ficha y Red Global) [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-108](https://linear.app/checkpoint-std/issue/CPS-108/t-37-corrida-de-evaluacion-y-control-de-niveles-en-grafos-ficha-y-red) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	Renombrar 'Modo Jurado' a 'Corrida de Evaluación' en navegación y vistas. Limitar el Grafo de Relaciones de la Ficha a 3 niveles por defecto con controles interactivos de incremento/decremento. En el área global de Grafo (/graph), poner Todos los nodos de filtro final, Noticias como filtro por defecto, selector de niveles (3 por defecto) y vista de Red Radial por defecto.
</details>

<details>
<summary><strong>CPS-109: [T-38] Ordenar leads del más reciente al más antiguo por defecto [Done | High]</strong></summary>
	**Enlace en Linear:** [CPS-109](https://linear.app/checkpoint-std/issue/CPS-109/t-38-ordenar-leads-del-mas-reciente-al-mas-antiguo-por-defecto) | **Estado:** `Done` | **Prioridad:** `High`  
	
	**Descripción Original del Ticket:**  
	Ordenar los leads/casos por defecto cronológicamente de forma descendente (del más reciente al más antiguo por created_at / id) tanto en el listado de API (GET /cases) como en la vista interactiva de leads (/leads), permitiendo además alternar entre más reciente y más antiguo.
</details>

<details>
<summary><strong>CPS-110: [T-39] Sugerencias de evidencias RAG/GraphRAG, buscador semántico y detección de contradicciones en Leads y Bandeja [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-110](https://linear.app/checkpoint-std/issue/CPS-110/t-39-sugerencias-de-evidencias-raggraphrag-buscador-semantico-y) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	Implementar sugerencias inteligentes de evidencias (Top 20) basadas en RAG semántico y GraphRAG en el creador de leads y modal de vinculación de fuentes. Incorporar buscador semántico optimizado con detección de fuentes contradictorias/anti-patrones (rol contradice vs respalda) y extender la optimización a la bandeja de temas ingesta.
</details>

<details>
<summary><strong>CPS-111: [T-40] Agente Copiloto Editorial con Vercel AI SDK y herramientas de plataforma [Done | Urgent]</strong></summary>
	**Enlace en Linear:** [CPS-111](https://linear.app/checkpoint-std/issue/CPS-111/t-40-agente-copiloto-editorial-con-vercel-ai-sdk-y-herramientas-de) | **Estado:** `Done` | **Prioridad:** `Urgent`  
	
	**Descripción Original del Ticket:**  
	Implementar el Agente Copiloto Editorial interactivo en EvidentIA utilizando Vercel AI SDK (ai + @ai-sdk/vue + @ai-sdk/openai). Incorporar herramientas agénticas 100% en el servidor Nitro para interactuar con toda la plataforma: búsqueda de evidencias, creación y edición de leads, vinculación/desvinculación de fuentes, notas de verificación, generación de briefs editoriales y reejecución de pipelines de ingesta. Incluye drawer slide-over accesible globalmente con atajo de teclado ⌘K.
</details>

<details>
<summary><strong>CPS-103: Synthesizer: emit per-sentence classification and per-claim support for the draft [Done | Medium]</strong></summary>
	**Enlace en Linear:** [CPS-103](https://linear.app/checkpoint-std/issue/CPS-103/synthesizer-emit-per-sentence-classification-and-per-claim-support-for) | **Estado:** `Done` | **Prioridad:** `Medium`  
	
	**Descripción Original del Ticket:**  
	## Context
	
	The new-lead wizard's Borrador step (`frontend/components/leads/DraftStep.vue`) was designed with rich per-sentence affordances: each sentence classified as hecho / declaración / inferencia / hipótesis, an inline citation per claim, and controls to "marcar afirmación como sin respaldo" and "pedir una segunda fuente".
	
	The real synthesizer behind `POST /cases/{id}/brief` (`backend/src/evidentia/briefs/tvn.py`, `banca.py`, `generation/synthesizer.py`) returns section text (`titulo_propuesto`, `brief`, `enfoque`, `preguntas`, `fuentes_y_verificaciones`, `guion`, `copy_digital`), aggregate citation counts (`citations_valid`, `citations_dropped`) and `missing_sources` — but **no per-sentence classification and no per-claim support mapping**.
	
	As part of wiring the wizard to real data (see `docs/leads-wizard-wiring-plan.md`), the live draft was simplified to render only what the backend emits. The rich per-sentence UI was dropped until the backend can back it with real data. This ticket covers extending the synthesizer so that UI can return, fully grounded.
	
	## Scope
	
	Extend the synthesizer / brief output so each sentence in the generated draft carries:
	
	* a **class**: `hecho | declaración | inferencia | hipótesis`
	* the **citation(s)** that support it (`[id:campo]`), or an explicit "sin respaldo" marker when none
	* enough structure for the frontend to render per-sentence pills and to flag unsupported sentences without re-parsing prose
	
	Decide the mechanism: structured generation (ask the model for a JSON array of `{text, class, citations}` instead of, or alongside, the markdown sections) versus a post-generation classification pass over the rendered brief. Keep the existing validate_citations guarantees (dropped citations stay dropped; nothing is invented).
	
	## Acceptance criteria
	
	* `POST /cases/{id}/brief` returns a machine-readable per-sentence breakdown for the brief body (at minimum the Brief and Guion sections), each sentence with its class and supporting citations.
	* Citations in the breakdown reconcile with `citations_valid` / `citations_dropped` — no sentence claims a citation that validation dropped.
	* Abstention path unchanged: when the model abstains, the breakdown is empty and the existing `abstained` / `reason` contract holds.
	* Backend tests cover: a well-supported sentence classified `hecho` with a valid citation; an unsupported sentence surfaced as "sin respaldo"; a quote classified `declaración`.
	* Frontend follow-up (separate): restore the classification pills and the "sin respaldo" / "segunda fuente" controls in `DraftStep.vue`, driven by the new data.
	
	## Links
	
	* Plan: `docs/leads-wizard-wiring-plan.md` (phase 4 and the "Decisions taken" section)
</details>
