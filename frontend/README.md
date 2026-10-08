# EvidentIA — Frontend

Interfaz del copiloto EvidentIA: Nuxt 3 + Vue 3 sobre TailwindCSS. Esta guía
cubre el sistema de diseño implementado en el frontend. La especificación
completa vive en [`../DESIGN.md`](../DESIGN.md); este README documenta cómo esos
tokens se usan en el código.

## Arranque

```bash
cd frontend
bun install          # o npm install
bun run dev          # servidor en http://localhost:3000
```

El frontend habla con el BFF de Nuxt (`server/api`), que a su vez reenvía al
backend en `NUXT_BACKEND_URL` (por defecto `http://localhost:8000`). Sin backend,
la UI se renderiza pero las vistas con datos muestran su estado vacío.

## Sistema de diseño

Reconstruido a partir del diseño "Lead Workspace v3" (Claude Design) y alineado
con `DESIGN.md`. Tres piezas lo sostienen:

- **Tokens** — [`assets/css/tailwind.css`](assets/css/tailwind.css): la paleta y
  los estados como propiedades CSS (`--primary`, `--canvas`, `--ink`, …) en
  tripletas HSL, con su variante oscura bajo `.dark`.
- **Mapa de Tailwind** — [`tailwind.config.ts`](tailwind.config.ts): expone esos
  tokens como clases (`bg-surface`, `text-ink-muted`, `border-hairline`, …),
  junto con las familias tipográficas, la escala de texto, los radios y las
  sombras.
- **Fuentes** — [`nuxt.config.ts`](nuxt.config.ts): carga las tres familias desde
  Google Fonts.

### Color

Un único azul tinta (`primary`) carga las acciones; el resto es papel y
estructura. El color "fuerte" se reserva para el sistema de estados, donde cada
color significa siempre lo mismo.

| Clase | Uso |
|-------|-----|
| `bg-canvas` | Fondo de página (nunca blanco puro) |
| `bg-surface` / `bg-surface-sunken` | Tarjetas / zonas hundidas (evidencia, zebra, píldoras) |
| `border-hairline` | Bordes y divisores de 1px — el recurso estructural principal |
| `text-ink` / `text-ink-muted` | Texto principal / secundario |
| `bg-primary` `text-on-primary` | Acción primaria (una por vista) |
| `primary-deep` / `primary-soft` | Presionado-hover / relleno suave de selección |
| `text-success` `text-warning` `text-error` `text-info` | Estados: suficiente / parcial / insuficiente · informativo |
| `text-accent` | Ámbar de señal (prioridad/urgencia) — decorativo, nunca un botón |

Modo oscuro vía clase `dark` en `<html>`; el conmutador vive en la barra
superior y persiste en `localStorage`.

### Tipografía

Tres familias con un papel fijo — *serif = voz, sans = interfaz, mono =
evidencia*:

| Clase | Familia | Para |
|-------|---------|------|
| `font-serif` (o `font-display`) | Source Serif 4 | Títulos y cabeceras de paso |
| `font-sans` | Inter | Cuerpo, tablas, formularios, UI (por defecto) |
| `font-mono` | IBM Plex Mono | IDs, citas `[id:campo]`, scores, hashes |

> Nota: los nombres con espacios o dígitos (`Source Serif 4`) van entrecomillados
> en la config; sin comillas el CSS es inválido y la familia cae silenciosamente
> a la de cuerpo.

Escala de texto con interlineado y peso incluidos: `text-display-xl`,
`text-display-lg`, `text-heading-md`, `text-label`, `text-body-md`,
`text-body-sm`, `text-mono`, `text-caption`.

### Forma y profundidad

- Radios: `rounded-sm` 6px (campos, píldoras de ID), `rounded-md` 8px (botones,
  tarjetas, por defecto), `rounded-lg` 12px (modales, contenedores grandes),
  `rounded-full` solo para chips de estado.
- Sombras: `shadow-ev-1` (tarjetas en reposo), `shadow-ev-2` (popovers),
  `shadow-ev-3` (modales). La profundidad se asienta en hairlines y un escalón de
  superficie antes que en sombras.
- Ancho del contenido: `max-w-container` (1120px).

### Compatibilidad

Los componentes `ui/*` heredados (de shadcn-vue) siguen funcionando: sus nombres
de token (`background`, `card`, `muted`, `destructive`, …) se mantienen como
alias que apuntan a la paleta EvidentIA, así que el refactor es un cambio de
tokens, no una reescritura.

## Estructura

```
assets/css/tailwind.css   Tokens del sistema de diseño (+ modo oscuro)
tailwind.config.ts        Mapa de tokens → clases, fuentes, escala, radios, sombras
layouts/default.vue       Barra superior (app-bar) y shell de página
components/ui/*            Primitivas (Button, Badge, Card, Input, Textarea)
components/*               Componentes de dominio (EvidenceTree, RankingTable, …)
pages/*                   Rutas (bandeja, leads, proyectos, ingesta)
composables/*             useAuth, useApi
server/api/*              BFF que reenvía al backend
```

## Convenciones

- Una sola acción primaria rellena por vista; el estado lo cargan los colores de
  estado, no la marca.
- Todo ID, cita, score o hash va en `font-mono`; nunca en cuerpo sans.
- Las etiquetas de sección usan `text-label` en mayúsculas en vez de un `<h2>` en
  negrita.
- Nada por encima de peso 600; números con `tabular-nums` para que las columnas
  alineen.
- Al añadir un estado nuevo, dale su propio color y token dentro del sistema de
  estados; no reutilices uno existente para decorar.
