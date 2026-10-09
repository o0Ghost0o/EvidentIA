# 🚀 EvidentIA — Copiloto de Entorno y Verificación Trazable
> **Reto hackIAthon Panamá 4ta edición — TVN Media / Viamatica**  
> *"De la señal a la decisión: Inteligencia con rigor editorial, trazabilidad inmutable y cero alucinaciones."*

---

## 📌 Panel Principal de Entrega del Reto

Bienvenido al espacio oficial de entrega del proyecto **EvidentIA**. Cumpliendo estrictamente las instrucciones del jurado y la coordinación del hackIAthon, este espacio centraliza los tres componentes oficiales requeridos para evaluación:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                               ESPACIO NOTION                                 │
│                                                                              │
│   ┌──────────────────────┐  ┌──────────────────────┐  ┌───────────────────┐  │
│   │ 📘 Doc. Técnica      │  │ 📗 Doc. Funcional    │  │ 🖥️ Presentación   │  │
│   │ Arquitectura, datos, │  │ Problema editorial,  │  │ Pitch Day         │  │
│   │ algoritmos, T01-T10  │  │ casos de uso y UX    │  │ Formato Notion    │  │
│   └──────────────────────┘  └──────────────────────┘  └───────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 🔗 Los 3 Enlaces Obligatorios de la Entrega

| # | Enlace Oficial de Notion | Descripción y Propósito |
|---|--------------------------|-------------------------|
| **1** | [📘 **Documentación Técnica**](01-documentacion-tecnica.md) | Arquitectura completa (FastAPI + Qdrant + GraphRAG + PostgreSQL), scoring determinista, validación de esquemas, suite de pruebas T01–T10 en vivo, seguridad Dual JWT y despliegue continuo. |
| **2** | [📗 **Documentación Funcional**](02-documentacion-funcional.md) | Enfoque de negocio y redacción para TVN Media: "Repetir no es corroborar", flujos de trabajo editorial, gestión de leads, generación de borradores con tags `[HECHO]`, `[DECLARACIÓN]`, `[INFERENCIA]` y casos de uso prácticos. |
| **3** | [🖥️ **Presentación para el Pitch Day**](03-presentacion-pitch-day.md) | Diapositivas nativas para proyectar durante la sustentación en vivo (Notion Presentation), estructuradas visualmente para 5 minutos de impacto más 5 minutos de defensa. |

---

## 🌐 Enlace Público del Reto y Acceso en Vivo

* **Plataforma Web en Producción (Cloud Main):**  
  👉 **[https://evidentia.vertexdc.com](https://evidentia.vertexdc.com)**  
  *(Despliegue activo en alta disponibilidad sobre infraestructura Coolify con HTTPS, volumen persistente y fallback offline)*

* **Entorno de Desarrollo y Staging:**  
  👉 **[https://dev-evidentia.vertexdc.com](https://dev-evidentia.vertexdc.com)**

* **Documentación Interactiva de la API (Swagger UI):**  
  👉 **[https://evidentia.vertexdc.com/docs](https://evidentia.vertexdc.com/docs)** (o local en `http://localhost:8001/docs`)

* **Repositorio de Código Fuente:**  
  👉 **GitHub:** [https://github.com/o0Ghost0o/EvidentIA](https://github.com/o0Ghost0o/EvidentIA)  
  👉 **Mirror Gitea:** [https://git.vertexdc.com/VERTEXdc/EvidentIA](https://git.vertexdc.com/VERTEXdc/EvidentIA)

---

## 🔑 Credenciales Demo para el Jurado

Para facilitar una auditoría completa del Role-Based Access Control (RBAC) y todas las capacidades editoriales, se han provisto las siguientes cuentas activas:

| Rol | Correo Electrónico | Contraseña | Permisos y Capacidades |
|-----|-------------------|------------|------------------------|
| **Super Admin / Jurado** | `admin@tvn.com` | `EvidentIA2026!` | Acceso irrestricto, ejecución de suite T01–T10 en vivo, carga masiva en `/ingest`, gestión de tenants y feature flags. |
| **Editor Jefe (Owner)** | `editor@tvn.com` | `EvidentIA2026!` | Bandeja de entrada, priorización editorial, validación de fichas de evidencia y aprobación de borradores. |
| **Periodista (Member)** | `periodista@tvn.com` | `EvidentIA2026!` | Creación de leads, exploración del grafo visual, consulta de fuentes y redacción asistida con citas obligatorias. |

---

## ⚡ Recursos Adicionales para la Sustentación

* ⏱️ [**Guion Cronometrado de Pitch (5 min) y Playbook de Preguntas (5 min)**](04-guion-pitch-5min-y-defensa.md):  
  Minuto a minuto con indicaciones de interacción en pantalla y matriz de respuestas rápidas ante preguntas difíciles del jurado.
* ✉️ [**Borrador Oficial del Correo para `hackiathon@viamatica.com`**](05-correo-entrega-viamatica.md):  
  Texto listo para el envío oficial de cierre con todos los enlaces verificados.
* 📦 [**Historial de Fases Previas y Bitácoras de Trabajo**](archivo_fases/):  
  Registro histórico del ciclo de vida del desarrollo durante el hackIAthon.

---

## 👥 Datos del Equipo

* **Nombre del Proyecto:** EvidentIA
* **Integrantes del Equipo:**
  * **Alek Rutherford** (`alekissac@gmail.com`)
  * **Pedro Carreras** (`pcarreras@vertexdc.com`)
* **Modalidad Principal:** TVN Media (Editorial Periodística)
* **Modalidad Extensión:** Banca y Finanzas (Boletín de Entorno Económico)
* **Fecha de Entrega:** Octubre 2026
* **Institución Organizadora:** Viamatica & TVN Media — Panamá
