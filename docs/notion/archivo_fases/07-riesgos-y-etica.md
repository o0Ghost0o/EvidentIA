# 07 — Riesgos y Ética

> Página 7/8 del espacio Notion.

## Controles obligatorios

| Riesgo | Control operativo | Estado |
|--------|-------------------|--------|
| Alucinación (hechos, cifras, citas, fuentes) | Generación solo sobre evidencia recuperada; citas `[id:campo]` obligatorias; abstención explícita sin evidencia | pendiente (Fase 4) |
| Prompt injection desde fuentes | Texto de fuente = dato, nunca instrucción; capa de saneado; T07 | pendiente (Fase 4/6) |
| Réplica contada como corroboración | Detección de agencia primaria; N réplicas = 1 procedencia (CU-03) | pendiente (Fase 3) |
| Publicación automática | 5 estados de revisión; "aprobado como borrador" ≠ publicar; salidas marcadas "borrador para revisión" | pendiente (Fase 4) |
| Datos personales / perfiles sensibles | No almacenar PII innecesaria; sin perfiles ni listas de riesgo; acusaciones como declaraciones atribuidas | permanente |
| Derechos de contenido | Solo titulares/metadatos inicialmente; sin redistribuir artículos/imágenes/video; condiciones por fuente en catálogo | permanente |
| Secretos en código/Notion/logs | `.env.example` sin secretos; credenciales solo en `.env` local (no versionado); sin tokens en capturas | permanente |
| Costos de LLM fuera de control | Medición de tokens/costo por consulta; fallback sin key; límites configurables | pendiente (Fase 4) |

## Escenarios fuera de alcance

Veredictos verdadero/falso; rating/audiencia; fraude/culpabilidad/solvencia/riesgo
individual; datos de clientes bancarios; paywalls; clonación de voz; emisión
televisiva; sistemas transaccionales; recomendaciones compra/venta.

## Principio rector

Una alerta es una invitación a investigar. Ni tono negativo, ni volumen de noticias,
ni repetición equivalen a fraude, pérdida financiera o verdad comprobada.
La persona revisora conserva la decisión editorial o analítica final.
