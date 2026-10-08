# ✉️ Plantilla de Correo Electrónico para Entrega Oficial
> **Destinatario Oficial:** `hackiathon@viamatica.com`  
> **Asunto:** Entrega Oficial de Reto — TVN Media (Modalidad Editorial) — Proyecto EvidentIA — hackIAthon Panamá 4ta Edición  
> **Instrucciones:** Copiar y enviar el siguiente contenido desde el correo oficial del equipo antes de la hora límite.

---

### Texto del Correo Electrónico

**Para:** `hackiathon@viamatica.com`  
**Asunto:** Entrega Oficial de Reto — TVN Media (Editorial) — Proyecto EvidentIA — hackIAthon Panamá 4ta Edición

Estimado Comité Organizador y Miembros del Jurado Calificador del **hackIAthon Panamá 4ta Edición (Viamatica & TVN Media)**,

Por medio de la presente, el equipo de **EvidentIA** tiene el honor de presentar la entrega formal y definitiva de nuestro desarrollo para el reto **TVN Media: "De la señal a la decisión"**, incluyendo nuestro entorno en producción, documentación técnica y funcional, y material para el Pitch Day.

A continuación, compartimos los elementos solicitados en las directrices oficiales:

---

### 1. Enlace Público del Reto Desarrollado y Explicación Breve

* **Enlace Público en Producción (Cloud Live Main):**  
  👉 **[https://evidentia.vertexdc.com](https://evidentia.vertexdc.com)**  
  *(Despliegue activo y completamente operativo en infraestructura Cloud con HTTPS, persistencia inmutable y soporte offline)*  
  *(Entorno de Desarrollo y Staging complementario: [https://dev-evidentia.vertexdc.com](https://dev-evidentia.vertexdc.com))*

* **Breve Explicación del Reto Desarrollado:**  
  **EvidentIA** es un copiloto de entorno y verificación trazable diseñado para la sala de redacción de **TVN Media** (con extensión a análisis de entorno macroeconómico). En lugar de un chatbot genérico que alucina o parafrasea fuentes a ciegas, EvidentIA transforma el flujo noticioso mediante tres pilares:
  1. **Scoring Multicriterio Determinista:** Ordena los temas por Relevancia, Impacto, Urgencia, Novedad y Evidencia corroborada ($P = 30R + 25I + 20U + 15N + 10E$), penalizando la réplica de cables de agencia bajo la premisa de que *repetir no es corroborar*.
  2. **Light GraphRAG Interactivo a 60 FPS:** Visualiza en SVG nativo las relaciones de causalidad en tiempo real entre noticias, indicadores del Banco Mundial (`WB:PAN:INDICADOR:AÑO`) y eventos geofísicos del USGS.
  3. **Abstención Estructurada y Clasificación Epistémica:** Genera borradores periodísticos con marcado estricto de `[HECHO]`, `[DECLARACIÓN]` e `[INFERENCIA]`; ante la falta de evidencia o cifras fuera de corte, el sistema se abstiene formalmente (`abstained: true`) con cero tolerancia a la alucinación.

---

### 2. Enlaces del Espacio de Trabajo en Notion

Hemos configurado nuestro espacio de trabajo central en Notion, el cual cuenta con los tres accesos directos requeridos por la coordinación:

* 🏠 **Página Principal del Workspace en Notion (Hub Central):**  
  👉 `[Insertar enlace a la página raíz de Notion de EvidentIA]`  
  *(Contiene el resumen ejecutivo del reto, credenciales de auditoría y los tres enlaces canónicos detallados abajo)*

* 📘 **1. Documentación Técnica:**  
  👉 `[Insertar enlace directo a la página de Documentación Técnica en Notion]`  
  *(Detalle exhaustivo de la arquitectura FastAPI + Qdrant + PostgreSQL, fórmulas matemáticas, pipeline de ingesta con upload_id y deduplicación Jaccard, suite T01–T10 en vivo en <7s, y seguridad Dual JWT con RBAC)*

* 📗 **2. Documentación Funcional:**  
  👉 `[Insertar enlace directo a la página de Documentación Funcional en Notion]`  
  *(Enfoque de producto para TVN Media: personas de usuario, flujos paso a paso de bandeja, fichas de investigación y generación de borradores, catálogo de plantillas y casos de prueba prácticos)*

* 🖥️ **3. Presentación para el Pitch Day:**  
  👉 `[Insertar enlace directo a la página de Presentación Pitch Day en Notion]`  
  *(Diapositivas nativas e interactivas diseñadas en Notion para la sustentación cronometrada de 5 minutos de pitch + 5 minutos de defensa ante el jurado)*

---

### 3. Credenciales de Prueba para Auditoría del Jurado

Para facilitar una revisión inmediata e interactiva de todos los niveles de usuario (RBAC) y de la consola de ejecución en vivo en `/jurado`, ponemos a su disposición las siguientes credenciales de acceso:

| Rol | Correo Electrónico | Contraseña | Capacidades |
| :--- | :--- | :--- | :--- |
| **Super Admin / Jurado** | `admin@tvn.com` | `EvidentIA2026!` | Acceso total, ejecución de suite T01-T10 en vivo en `/jurado`, carga de esquemas en `/ingest`. |
| **Editor Jefe (Owner)** | `editor@tvn.com` | `EvidentIA2026!` | Bandeja de entrada, priorización editorial y aprobación de fichas. |
| **Periodista (Member)** | `periodista@tvn.com` | `EvidentIA2026!` | Creación de leads, exploración del grafo visual y redacción con citas. |

---

### 4. Enlaces de Repositorios y Código Fuente

* **Repositorio GitHub:** [https://github.com/o0Ghost0o/EvidentIA](https://github.com/o0Ghost0o/EvidentIA)  
* **Mirror Gitea:** [https://git.vertexdc.com/VERTEXdc/EvidentIA](https://git.vertexdc.com/VERTEXdc/EvidentIA)  
* **Swagger API Docs (Producción):** [https://evidentia.vertexdc.com/docs](https://evidentia.vertexdc.com/docs)

Agradecemos profundamente a la organización de Viamatica y a TVN Media por el reto planteado. Estamos listos y entusiasmados para la sustentación del Pitch Day.

Atentamente,  
**Equipo EvidentIA**  
*hackIAthon Panamá 2026 — 4ta Edición*
