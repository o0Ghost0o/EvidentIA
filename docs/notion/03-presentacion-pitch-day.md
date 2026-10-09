# 🖥️ Presentación para el Pitch Day — EvidentIA
> **hackIAthon Panamá 4ta edición — TVN Media / Viamatica**  
> *Sustentación Oficial ante el Jurado Calificador*  
> **Formato:** Notion Presentation · **Tiempo Asignado:** 10 minutos (5 min Pitch + 5 min Preguntas)  
> **Demo en Vivo (Main):** [https://evidentia.vertexdc.com](https://evidentia.vertexdc.com) · **Dev:** [https://dev-evidentia.vertexdc.com](https://dev-evidentia.vertexdc.com)

---

## 🧭 Índice Rápido de la Presentación

* [Diapositiva 1: Portada y Propósito Central](#diapositiva-1-portada-y-propósito-central)
* [Diapositiva 2: El Problema en TVN — La Trampa de la Inmediatez](#diapositiva-2-el-problema-en-tvn--la-trampa-de-la-inmediatez)
* [Diapositiva 3: Nuestra Tesis — EvidentIA](#diapositiva-3-nuestra-tesis--evidentia)
* [Diapositiva 4: Demostración — Bandeja Inteligente y Grafo a 60 FPS](#diapositiva-4-demostración--bandeja-inteligente-y-grafo-a-60-fps)
* [Diapositiva 5: El Rigor Periodístico — Citas Canónicas y Abstención](#diapositiva-5-el-rigor-periodístico--citas-canónicas-y-abstención)
* [Diapositiva 6: Auditoría Técnica — Suite T01 a T10 en Vivo en 7 Segundos](#diapositiva-6-auditoría-técnica--suite-t01-a-t10-en-vivo-en-7-segundos)
* [Diapositiva 7: Arquitectura Corporativa y Modo Offline a $0.00](#diapositiva-7-arquitectura-corporativa-y-modo-offline-a-000)
* [Diapositiva 8: Impacto Operativo para TVN Media y Cierre](#diapositiva-8-impacto-operativo-para-tvn-media-y-cierre)

---

## Diapositiva 1: Portada y Propósito Central

> ### 🚀 EvidentIA
> **Copiloto de Entorno y Verificación Trazable**  
> *"De la señal a la decisión con rigor editorial inmutable."*

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          HACKIATHON PANAMÁ 2026                             │
│                                                                             │
│   • Reto: TVN Media (Editorial Periodística)                                │
│   • Extensión: Inteligencia de Entorno y Banca                              │
│   • Plataforma en Producción: https://evidentia.vertexdc.com                │
│   • Equipo: Alek Rutherford & Pedro Carreras                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

* **El Mensaje en 1 Frase:** En lugar de un chatbot genérico que inventa o parafrasea noticias, EvidentIA entrega una sala de redacción con trazabilidad de fuentes, ranking transparente y abstención matemática ante la falta de evidencia.

---

## Diapositiva 2: El Problema en TVN — La Trampa de la Inmediatez

> ### ⚠️ El Dilema de la Sala de Redacción
> *"Un periodista no sufre por falta de noticias; sufre por falta de verificación oportuna."*

```
             LLUVIA DE CABLES Y TELETIPOS (Ruido Informativo)
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                            ▼
5 Medios repiten              Cifras sueltas              Modelos LLM
el mismo cable de EFE         "El PIB subió 7%"           alucinan datos
(Falsa corroboración)         (¿De qué año? ¿Fuente?)     y falsifican citas
```

### Los 3 Grandes Dolores de TVN:
1. **Volumen confundido con Verdad:** La repetición masiva de una noticia crea una ilusión de confirmación.
2. **Cifras Anacrónicas:** Datos de inflación o empleo citados sin año de corte ni unidad canónica.
3. **Riesgo Reputacional Inaceptable:** Usar herramientas de IA tradicionales que inventan fuentes o son vulnerables a titulares maliciosos.

---

## Diapositiva 3: Nuestra Tesis — EvidentIA

> ### 💡 Principios Rectores Innegociables
> *"Repetir no es corroborar. Prioridad no es certeza. La IA asiste; el ser humano decide."*

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EL FLUJO DE CONVERSIÓN DE EVIDENTIA                      │
│                                                                             │
│   SEÑALES BRUTAS       ──►  MOTOR EVIDENTIA         ──► DECISIÓN HUMANA     │
│   • Feeds RSS TVN           • Deduplicación Jaccard     • Prioridad P clara │
│   • Banco Mundial           • Light GraphRAG            • Ficha auditable   │
│   • USGS Terremotos         • Citas WB:PAN:...          • Borrador con tags │
│   • GDELT 2.0               • Aislamiento XML           • Aprobación humana │
└─────────────────────────────────────────────────────────────────────────────┘
```

* **Formula de Prioridad Determinista:**
  $$\text{Prioridad } P = 30R + 25I + 20U + 15N + 10E$$
  *Descuenta automáticamente la saturación de réplicas léxicas ($N$) y valida procedencias independientes ($E$).*

---

## Diapositiva 4: Demostración — Bandeja Inteligente y Grafo a 60 FPS

> ### 🖥️ Demostración en Pantalla: El Grafo Causal en Vivo
> *Visualizador físico interactivo en SVG nativo a 60 cuadros por segundo.*

```
       [Noticia: Cierre de Vía] ──(Ocurre en)──► [Tierras Altas, Chiriquí]
                  │                                         │
            (Reportado por)                           (Afecta a)
                  │                                         │
                  ▼                                         ▼
         [Sismo USGS Mag 4.8]                     [PIB Agrícola WB:2023]
```

### Lo que nos diferencia de cualquier otra solución:
* **Física en tiempo real:** Arrastre de nodos, zoom panorámico y filtros por temática sin librerías pesadas.
* **Cruce Multimodal Instantáneo:** Un temblor del USGS se conecta en el grafo con la nota vial y con el indicador del Banco Mundial en milisegundos.
* **Inspección con 1 Clic:** Presionar cualquier nodo abre la fuente original validada.

---

## Diapositiva 5: El Rigor Periodístico — Citas Canónicas y Abstención

> ### 🛡️ Blindaje Editorial Anti-Alucinación
> *Todo hecho tiene su fuente; sin fuente, existe abstención formal.*

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CLASIFICACIÓN EPISTÉMICA ACTIVA                       │
│                                                                             │
│   [HECHO]        "El PIB de Panamá creció 7.3% [WB:PAN:NY.GDP:2023]"        │
│   [DECLARACIÓN]  "El sindicato anunció paro de 48 horas [TVN:104]"          │
│   [INFERENCIA]   "El desabastecimiento podría presionar precios locales"    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### El Comportamiento ante lo Desconocido (Abstención):
* Si se consulta una métrica que no está en el corpus:
  👉 **`abstained: true`**
* EvidentIA no especula: detalla con precisión quirúrgica qué datos faltan y qué llamada periodística corresponde hacer al MEF o a la entidad oficial.

---

## Diapositiva 6: Auditoría Técnica — Suite T01 a T10 en Vivo en 7 Segundos

> ### 🧪 Corrida de Evaluación Integrada (`/jurado`)
> *Demostración empírica de cumplimiento del pliego en tiempo real.*

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CENTRO DE AUDITORÍA OFICIAL (T01 - T10)                  │
│                                                                             │
│   ✅ T01 Ingesta Multifuente       ✅ T06 Abstención Estructurada           │
│   ✅ T02 Deduplicación Léxica      ✅ T07 Blindaje Anti-Prompt Injection    │
│   ✅ T03 Scoring Multicriterio     ✅ T08 Seguridad Dual JWT & RBAC         │
│   ✅ T04 Trazabilidad de Citas     ✅ T09 Resiliencia Offline (0 USD)       │
│   ✅ T05 GraphRAG Causal           ✅ T10 Trazabilidad de Cargas por Esquema │
│                                                                             │
│   ⏱️ Tiempo de Ejecución Total: 6.8 segundos | 10/10 Pruebas en Verde      │
└─────────────────────────────────────────────────────────────────────────────┘
```

* **Transparencia Inmediata:** Cada prueba muestra su aserción de código, su tiempo en milisegundos y el valor evaluado.

---

## Diapositiva 7: Arquitectura Corporativa y Modo Offline a $0.00

> ### 🏢 Preparado para la Escala Empresarial
> *Seguridad de grado financiero y tolerancia a fallos catastróficos.*

| Dimensión | Enfoque EvidentIA | Beneficio Tangible para TVN |
| :--- | :--- | :--- |
| **Autenticación** | Dual JWT (15 min Access / 7 días Refresh rotativo) | Máxima seguridad contra secuestro de tokens y control de sesiones. |
| **Control de Acceso**| RBAC para 4 roles (`Super Admin`, `Owner`, `Admin`, `Member`) | Separación clara entre periodistas, editores y administradores. |
| **Costo Conectado**| Together.ai Llama-3.3-70B-Turbo (~$0.0011 USD/consulta) | Costos de inferencia ultrabajos y predecibles. |
| **Modo Desconectado**| Generador Estructurado Determinista Local | **$0.00 USD**: Si se cae internet, la redacción no se detiene. |
| **Persistencia** | Capa `/app/seed_frozen` + auto-aprovisionamiento | Cero pérdida de datos ante reinicios o despliegues en Coolify. |

---

## Diapositiva 8: Impacto Operativo para TVN Media y Cierre

> ### 📈 El Valor de Negocio
> *"Más primicias verificadas, cero retractaciones públicas."*

```
           TIEMPO DE PREPARACIÓN DE UNA NOTA INVESTIGATIVA
  
  Flujo Tradicional: ████████████████████ (55 minutos)
  Con EvidentIA:     ████ (11 minutos)  ---> ¡80% DE AHORRO!
```

### Conclusiones:
1. **EvidentIA es una realidad desplegada:** No es un mockup ni un prototipo en Figma; está corriendo en vivo en producción.
2. **Respalda la reputación de TVN:** Cada número, cada fecha y cada fuente están garantizados de forma auditable.
3. **Escalable a toda la corporación:** Diseñado para televisión, web, radio y extensible a estudios macroeconómicos.

> **¡Gracias, señores miembros del jurado!**  
> Pasamos a la sesión de preguntas y respuestas técnicas.  
> 🔗 Plataforma en vivo (Main): [https://evidentia.vertexdc.com](https://evidentia.vertexdc.com) · [Dev: dev-evidentia.vertexdc.com](https://dev-evidentia.vertexdc.com)
