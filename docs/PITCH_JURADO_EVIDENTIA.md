# Guion de Pitch y Defensa Técnica ante el Jurado: EvidentIA
> **Duración total:** 10 minutos · **Presentador:** Equipo EvidentIA · **Plataforma:** EvidentIA Live

---

## 1. Estructura y Cronograma del Pitch (10 Minutos)

| Minuto | Bloque Temático | Mensaje Clave | Qué Mostrar en Pantalla |
| :--- | :--- | :--- | :--- |
| **00:00 – 02:00** | **El Problema Editorial y Principios** | El periodista de TVN no sufre por falta de noticias; sufre por falta de verificación oportuna. **Repetir no es corroborar** (cinco teletipos de agencia son 1 sola procedencia). **Prioridad ≠ Verdad** (el ranking ordena atención, no certeza). La IA propone y contextualiza; la decisión editorial siempre es humana. | Inicio de la plataforma (`/`), panel de control con métricas en tiempo real. |
| **02:00 – 06:00** | **Demostración en Vivo (Demo Cuádruple)** | **1. Ingesta y Calidad:** Fechas rotas y nulos no bloquean la ingesta (`/ingest`).<br>**2. Visualizador GraphRAG a 60 FPS:** Abrir `/graph`, mover nodos de noticias e indicadores en vivo; mostrar cómo se conectan los datos del Banco Mundial.<br>**3. Ficha y Evidencia:** Abrir un Lead (`/leads/new` o detalle), mostrar citas oficiales Banco Mundial con año y unidad.<br>**4. Borrador y Abstención:** Citas obligatorias con tags `[HECHO]`, `[DECLARACIÓN]`, `[INFERENCIA]`. Probar consulta sin datos en el corpus $\rightarrow$ **Abstención estructurada inmediata**. | Pantalla de Bandeja (`/`), Grafo de Fuerza Dirigida (`/graph`), Lead Stepper (`/leads/new`), Modal de Evidencia. |
| **06:00 – 08:00** | **Modo Jurado en Vivo (T01–T10)** | Presionar el botón **"Ejecutar Suite T01–T10 en Vivo"** en `/jurado`. En 7 segundos, mostrar cómo las 10 pruebas oficiales del pliego (§9) pasan en verde con aserciones auditables y docstrings. | Pantalla de Modo Jurado (`/jurado`), acordeón de pruebas, tabla de métricas vs. BM25. |
| **08:00 – 10:00** | **Arquitectura, Seguridad y Preguntas** | Nuxt 4 + FastAPI + SQLModel + PostgreSQL + Dual JWT (15m/7d) + RBAC multi-tenant. Modelo Llama-3.3-70B + fallback offline a 0 USD. Respuestas a preguntas del jurado. | Arquitectura, token rotation, sesión de usuario. |

---

## 2. Puntos Diferenciadores Clave frente a la Competencia (TVN NEXO)

1. **Grafo de Causalidad GraphRAG Interactivo vs. Imágenes Estáticas:**
   - La competencia muestra capturas PNG oscuras de Notion.
   - **EvidentIA:** Ofrece un motor físico de fuerza dirigida en SVG nativo a 60 FPS (`ForceGraph.vue`) donde el jurado puede arrastrar nodos, filtrar por temática (economía, sismos, Canal), inspeccionar relaciones semánticas y abrir fuentes con un solo clic.

2. **Seguridad Empresarial vs. Plataforma Desprotegida:**
   - La competencia no tiene autenticación (cualquiera entra y no hay roles).
   - **EvidentIA:** Implementa seguridad de grado corporativo con Dual JWT (15 min / 7 días), rotación automática de refresh tokens, mitigación contra robo de sesión y RBAC para 4 roles periodísticos (`Super Admin`, `Owner`, `Admin`, `Member`).

3. **Ingesta Continua y Dual vs. Snapshot Congelado:**
   - La competencia solo funciona con un snapshot estático de días pasados.
   - **EvidentIA:** Posee modo dual: snapshot offline reproducible para demos sin conexión, y scheduler automático en segundo plano (`/ingest`) con feeds RSS de TVN y GDELT en vivo controlable por Feature Flags.

4. **Centro de Verificación T01–T10 Integrado:**
   - EvidentIA expone la ejecución en vivo de los 10 criterios oficiales del pliego (§9) con timings exactos en milisegundos y aserciones visibles.

---

## 3. Guion de Respuestas Rápidas ante Preguntas Difíciles del Jurado

### P1: «¿De dónde proviene esta cifra económica y de qué año es?»
* **Respuesta:** «Cada cifra del Banco Mundial preserva su identificador único canónico `WB:PAN:INDICADOR:AÑO`, su valor numérico y unidad (ej. `% anual`). El modelo está condicionado para señalar explícitamente que se trata de una cifra anual cerrada y no de la medición del día de hoy. Lo vemos en vivo en la Ficha de Investigación en la sección *Contexto Oficial*.»

### P2: «Si tres medios replican la misma nota de la agencia EFE, ¿cuántas fuentes cuentan?»
* **Respuesta:** «Contamos exactamente una sola procedencia independiente. La réplica léxica no aumenta artificialmente la corroboración ni la urgencia ($N < 1.0$). En el cálculo de la fórmula $P = 30R + 25I + 20U + 15N + 10E$, el componente de novedad penaliza la duplicación y el componente $E$ solo reconoce procedencias distintas.»

### P3: «¿Qué ocurre si no hay evidencia suficiente o la pregunta es sobre el día de hoy?»
* **Respuesta:** «EvidentIA se abstiene formalmente. La abstención estructurada emite `abstained: true`, detalla qué datos faltan en el corpus y propone qué diligencia periodística corresponde realizar. Jamás inventamos cifras ni forjamos citas bibliográficas.»

### P4: «¿Cómo protegen el sistema si un titular malicioso intenta hacer prompt injection?»
* **Respuesta:** «Nuestra arquitectura separa drásticamente las instrucciones del sistema de las fuentes externas. Todo el contenido externo se encapsula como bloques XML de datos pasivos (`<fuente id="...">`). Si un titular contiene una inyección, el validador posterior elimina cualquier cita no registrada en el corpus, neutraliza la orden y deja la evidencia en $E = 0$.»

### P5: «¿Cuánto cuesta la inferencia y cómo opera sin internet?»
* **Respuesta:** «En modo conectado usamos Together.ai con Llama-3.3-70B-Turbo a un costo auditable de apenas **$0.0011 USD por consulta**. Si durante la transmisión en vivo se pierde la conectividad a internet, EvidentIA activa de inmediato el modo offline con snapshot local reproducible y generador determinista estructurado a **0.00 USD** sin tocar la red.»
