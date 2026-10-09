---
version: 1
name: EvidentIA
description: An evidence-first intelligence console for newsrooms and analysts. A cool paper canvas under an editorial serif, a confident ink-blue primary, and a disciplined state-color system (evidence sufficiency, review status, priority bands) that does the heavy lifting. Dense but calm, print-serious, with monospaced provenance for every ID and citation. Light and dark.
colors:
  primary: "#1B4D89"        # editorial ink-blue — primary actions
  primary-deep: "#143A6B"   # pressed/hover
  primary-soft: "#E3ECF7"   # selected fills, soft highlights (light)
  accent: "#B45309"         # signal amber — priority/urgency motif, decorative
  canvas: "#F6F8FB"         # cool paper page background (light)
  surface: "#FFFFFF"        # cards/panels (light)
  surface-sunken: "#EDF1F6" # evidence/code/ID panels, table zebra (light)
  hairline: "#D9E0E9"       # borders/dividers (light)
  ink: "#1B2638"            # near-black navy body text (light)
  ink-muted: "#5B6676"      # secondary text, labels, helper
  on-primary: "#F6F9FD"     # text on ink-blue
  success: "#047857"        # evidence suficiente / aprobado
  warning: "#B45309"        # evidence parcial / banda media
  error: "#B42318"          # insuficiente / contradicción / banda alta
  info: "#0369A1"           # neutral informational, news links
typography:
  display-font: "Source Serif 4, Lora, Georgia, serif"
  body-font: "Inter, system-ui, -apple-system, sans-serif"
  mono-font: "IBM Plex Mono, JetBrains Mono, ui-monospace, monospace"
  scale:                     # role: "sizepx/weight/line-height"
    display-xl: "32px/600/1.15"
    display-lg: "24px/600/1.2"
    heading-md: "18px/600/1.3"
    label: "13px/600/1.3"
    body-md: "16px/400/1.55"
    body-sm: "14px/400/1.5"
    mono: "13px/450/1.5"
    caption: "12px/500/1.4"
spacing:
  base: 8
  scale: { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, huge: 48 }
radius:
  sm: 6
  md: 8
  lg: 12
  pill: 9999
elevation:
  1: "0 1px 2px rgba(19,35,58,0.06)"
  2: "0 4px 12px rgba(19,35,58,0.08)"
  3: "0 12px 32px rgba(19,35,58,0.14)"
---

## Overview

EvidentIA is a console for turning scattered public signals into a decision a human can defend. The design language is built for **trust and legibility under density**: an editorial serif (`{typography.display-font}`) gives newsroom gravitas to titles, a neutral sans (`{typography.body-font}`) keeps dense tables and forms readable, and a monospaced face (`{typography.mono-font}`) marks every ID, citation and score so provenance is always visually distinct from prose.

Color is used with discipline. A single confident ink-blue (`{colors.primary}`) carries actions; everything else is a calm paper surface (`{colors.canvas}` → `{colors.surface}`) with hairline (`{colors.hairline}`) structure. The one place color is loud on purpose is the **state system** — evidence sufficiency, review status and priority bands — because in this product the state *is* the information. A reader should know at a glance whether a claim is backed, partial or unsupported, without reading a word.

The signature move is the **sequential lead workflow**: a lead (investigation) is worked as an ordered, gated set of steps, not a wall of panels. You cannot produce a draft before the evidence that would back it exists. The UI encodes the challenge's anti-hallucination rule — *high priority with insufficient evidence never enables publication* — as a locked step with an honest reason, and routes the dead-end to an explicit **abstention**, never an invented draft.

**Key Characteristics:**
- Cool paper canvas (`{colors.canvas}`) instead of pure white; `{colors.surface}` lifts one step for cards.
- A single ink-blue primary (`{colors.primary}`) for actions — the state colors, not the brand color, carry meaning.
- Three-face type system: editorial serif titles, neutral sans body, **mono for every ID / citation / score**.
- A disciplined state palette: `suficiente/parcial/insuficiente`, `bajo/medio/alto`, and the five review states — always the same color each time.
- Gated sequential workflow: steps unlock in order; the draft step is locked until evidence is sufficient.
- Hairlines and a one-step surface lift do the structural work; shadows are quiet (`{elevation.1}`).
- Modest geometry — `{radius.md}` default, nothing pill-heavy except status chips; serious, not playful.
- Full light/dark parity; light is the demo/projector default.

## Colors

> **Source:** Reverse-engineered and elevated from the existing Nuxt + shadcn-vue HSL token set; names map 1:1 to the CSS custom properties in `assets/css/tailwind.css` so the refactor is a token swap, not a rewrite.

### Brand & Accent
- `{colors.primary}` (`#1B4D89`): Editorial ink-blue. Primary buttons, active nav, focus rings, the current step in the stepper. One filled primary action per view.
- `{colors.primary-deep}` (`#143A6B`): Pressed/hover for primary surfaces.
- `{colors.primary-soft}` (`#E3ECF7`): Soft fill for the active step, selected rows, link hover backgrounds. (Dark mode: `#16293F`.)
- `{colors.accent}` (`#B45309`): Signal amber. The priority/urgency motif (urgency component, "prioritario" flag) and decorative emphasis — **never a button**.

### Surface
- `{colors.canvas}` (`#F6F8FB`): Default page background (light). Dark mode: `#0C1320`.
- `{colors.surface}` (`#FFFFFF`): Card and panel fill (light). Dark mode: `#121B2B`.
- `{colors.surface-sunken}` (`#EDF1F6`): Recessed zones — evidence/ID panels, table zebra striping, mono pills, the sunken track of the stepper. Dark mode: `#0E1626`.
- `{colors.hairline}` (`#D9E0E9`): 1px borders, dividers, table rules. Dark mode: `#24324A`. The primary structural device.

### Text
- `{colors.ink}` (`#1B2638`): Default body text — a near-black navy, never pure black. Dark mode: `#E6ECF5`.
- `{colors.ink-muted}` (`#5B6676`): Secondary text, captions, section labels, helper copy. Dark mode: `#93A1B5`.
- `{colors.on-primary}` (`#F6F9FD`): Text on ink-blue and other dark fills.

### Semantic
The semantic palette doubles as the **state palette** — reused consistently so a color always means the same thing (see the `state-system` signature component).
- `{colors.success}` (`#047857`): Evidence `suficiente`, status `aprobado_borrador`, corroboration.
- `{colors.warning}` (`#B45309`): Evidence `parcial`, priority band `medio`, "requires attention".
- `{colors.error}` (`#B42318`): Evidence `insuficiente`, `contradicts` relations, priority band `alto`, abstention, `descartado`.
- `{colors.info}` (`#0369A1`): Neutral informational, news-source chips, indicator links.

## Typography

### Font Family
Titles and step headers are set in **Source Serif 4** (`{typography.display-font}`), a screen-optimized humanist serif, at weights 500–600 — it gives the product an editorial, "published" authority without feeling antique. Body, UI, tables and forms use **Inter** (`{typography.body-font}`) at 400–600 for maximum legibility at small sizes and high density. A third face, **IBM Plex Mono** (`{typography.mono-font}`), is reserved for machine-truth: source IDs, citations in `[id:campo]` form, scores, hashes and timestamps — anything the user must read literally and trust. The three-face split is the typographic signature: *serif = voice, sans = interface, mono = evidence.*

### Hierarchy

| Role | Size | Weight | Line Height | Letter Spacing | Use |
|---|---|---|---|---|---|
| display-xl | 32px | 600 | 1.15 | -0.4px | Page title (serif) |
| display-lg | 24px | 600 | 1.2 | -0.2px | Section opener, lead title (serif) |
| heading-md | 18px | 600 | 1.3 | 0 | Card / step title (serif) |
| label | 13px | 600 | 1.3 | 0.6px (uppercase) | Section labels, table headers (sans) |
| body-md | 16px | 400 | 1.55 | 0 | Default UI body (sans) |
| body-sm | 14px | 400 | 1.5 | 0 | Dense tables, helper, secondary (sans) |
| mono | 13px | 450 | 1.5 | 0 | IDs, citations `[id:campo]`, scores, hashes (mono) |
| caption | 12px | 500 | 1.4 | 0.2px | Timestamps, meta, fine print (sans/mono) |

### Principles
- Serif only for titles and step headers; never for body, tables or buttons.
- Every source ID, citation, score and hash renders in `{typography.mono}` — never in body sans. Mono signals "verifiable datum".
- Section labels use `{typography.label}` uppercase with tracking; this replaces bold slate `<h2>`s for scannability.
- Nothing above weight 600 — this is a serious tool, not a loud one.
- Tabular numbers (`font-variant-numeric: tabular-nums`) on all scores, component values and metrics so columns align.

### Note on Font Substitutes
All three faces are free via Google Fonts / open licenses, so substitution is rarely needed. If Source Serif 4 is unavailable, fall back to **Lora**, then Georgia, at the same weights. For Inter, fall back to system-ui. For IBM Plex Mono, fall back to **JetBrains Mono** then ui-monospace. Avoid Times/Times New Roman for the serif (reads older and thinner than intended) and avoid Courier for mono.

## Layout

### Spacing System
- **Base unit:** 8px (`{spacing.base}`).
- **Scale:** `{spacing.xs}` 4px · `{spacing.sm}` 8px · `{spacing.md}` 12px · `{spacing.lg}` 16px · `{spacing.xl}` 24px · `{spacing.xxl}` 32px · `{spacing.huge}` 48px.
- **Section padding (between stacked cards):** `{spacing.xl}` vertical.
- **Card padding:** `{spacing.lg}` on mobile, `{spacing.xl}` from the `md` breakpoint up.

### Grid & Container
Mobile-first. The base layout is a **single full-width column** with `{spacing.lg}` (16px) side gutters inside a top app-bar shell. Content caps at a **1120px** container from the `lg` breakpoint (1024px) up. The lead workspace is the one screen that expands into two regions at `lg`: a **sticky left rail** (the step list / lead summary, ~280px) and the main step content; below `lg` that rail collapses into a horizontal stepper strip pinned under the header.

### Whitespace Philosophy
This is a dense product, so whitespace is *rhythmic*, not lavish: a consistent `{spacing.xl}` between cards and `{spacing.lg}` inside them keeps dense tables from feeling cramped without wasting vertical space the analyst needs. When a region holds a lot of data (evidence tree, score breakdown), group with hairlines and `{colors.surface-sunken}` zones rather than large gaps.

### Responsive Strategy
Progressive enhancement from the single mobile column: the stepper goes from a compact "Paso 3 de 6" pill (mobile) to a full horizontal stepper (tablet) to a persistent vertical rail (desktop). Tables reflow to stacked label/value rows on mobile and become true columns at `md`.

## Elevation & Depth

| Level | Treatment | Use |
|---|---|---|
| 0 | Flat on `{colors.canvas}` | Page background, inline regions |
| 1 | `0 1px 2px rgba(19,35,58,0.06)` + 1px `{colors.hairline}` | Resting cards, panels |
| 2 | `0 4px 12px rgba(19,35,58,0.08)` | Popovers, dropdowns, sticky stepper rail on scroll |
| 3 | `0 12px 32px rgba(19,35,58,0.14)` | Modals (auth, confirmations) |

### Decorative Depth
Depth is asserted mainly through **hairlines and a one-step surface lift** (`{colors.canvas}` → `{colors.surface}` → recessed `{colors.surface-sunken}`), not heavy shadows — appropriate for a data-dense console where drop shadows on every card create noise. Shadows carry the navy ink tint (never neutral gray) and stay subtle until something truly floats (level 3). The current step in the stepper is emphasized with a `{colors.primary}` left-border/underline accent rather than elevation.

## Shapes

### Border Radius Scale

| Name | Value | Use |
|---|---|---|
| sm | 6px | Inputs, selects, mono ID pills, small chips |
| md | 8px | Buttons, cards, panels (default) |
| lg | 12px | Modals, the stepper container, large surfaces |
| pill | 9999px | Status/state chips and badges only |

### Photography & Illustration Geometry
EvidentIA is near-imageless by design — trust comes from data, not stock photography. The visual texture is **structured data**: tables, the evidence tree, score bars, chips, and mono tokens. Any diagram (architecture, evidence graph) sits in a `{radius.lg}` framed `{colors.surface-sunken}` panel with a `{colors.hairline}` border and no shadow. Charts follow the state palette (bands/evidence), with tabular-num axes.

## Components

### Buttons
**`button-primary`** — the single filled call to action per view.
- Background `{colors.primary}`, text `{colors.on-primary}`, type `{typography.body-sm}` (600), padding `{spacing.sm}` `{spacing.lg}`, radius `{radius.md}`, height 36px.
- `button-primary-pressed`: background `{colors.primary-deep}`.
- `button-primary-disabled`: 50% opacity, no pointer — used when a gated step action isn't yet permitted (pair with an inline reason, never a silent dead button).

**`button-outline`** — secondary actions (export, link evidence, add note).
- Transparent background, text `{colors.ink}`, 1px `{colors.hairline}` border, same metrics; hover fills `{colors.surface-sunken}`.

**`button-ghost`** — tertiary/inline (step navigation "Atrás", remove).
- No border/background; text `{colors.ink-muted}`, hover text `{colors.ink}`.

### Cards & Containers
**`card`** — default content container (replaces today's generic `Card`).
- Background `{colors.surface}`, padding `{spacing.lg}`→`{spacing.xl}` at `md`, radius `{radius.md}`, `{elevation.1}`, 1px `{colors.hairline}`.
- `card-header`: `{typography.heading-md}` serif title + optional `{typography.label}` meta on the right, divided by a `{colors.hairline}` rule.

**`panel-sunken`** — recessed data region (evidence list, score breakdown, raw citation).
- Background `{colors.surface-sunken}`, radius `{radius.md}`, inner padding `{spacing.md}`, no shadow.

### Inputs & Forms
**`text-input` / `select`** — standard field.
- Background `{colors.surface}`, text `{colors.ink}`, type `{typography.body-sm}`, padding `{spacing.sm}` `{spacing.md}`, radius `{radius.sm}`, 1px `{colors.hairline}`, height 36px.
- `-focused`: 2px `{colors.primary}` ring, border `{colors.primary}`.
- IDs typed by the user (evidence `fuente_id`) render in `{typography.mono}` inside the field.

### Navigation
**`app-bar`** — top navigation shell.
- Background `{colors.surface}` with a bottom `{colors.hairline}`, height 56px, padding `{spacing.lg}`. Serif wordmark left; `{typography.label}` nav links (Bandeja · Leads · Ingesta) with the active route in `{colors.primary}`; session chip + theme toggle right.

**`breadcrumb`** — context trail on detail screens (`← Leads / Ficha #12`), `{typography.caption}` in `{colors.ink-muted}`.

### Pills, Tags, and Chips
**`id-token`** — a source identifier or citation.
- `{typography.mono}`, `{colors.ink-muted}` on `{colors.surface-sunken}`, radius `{radius.sm}`, padding 0 `{spacing.xs}`. On hover/press, reveals provenance (source, date, scope). Citations render as `[id:campo]` inside this token.

**`state-chip`** — see `state-system`. Radius `{radius.pill}`, `{typography.caption}` 600.

### Signature Components

**`lead-stepper`** — the defining component: a lead is worked as an ordered, gated sequence, mirroring the challenge's 7 stages collapsed to six working steps. **This replaces the single-scroll `/leads/[id]` page.**

Steps (in order): **1 · Definir** → **2 · Evidencia** → **3 · Contexto & Priorización** → **4 · Ficha** → **5 · Borrador** → **6 · Revisión**.

- Each step carries one of five visual states, each with a fixed treatment:
  - `complete` — `{colors.success}` check, filled; clickable to revisit.
  - `current` — `{colors.primary}` accent (left border on rail / underline on strip), serif `{typography.heading-md}` title.
  - `available` — `{colors.ink}` outline, clickable.
  - `locked` — `{colors.ink-muted}` 50%, lock glyph, **not** clickable, with an inline reason.
  - `blocked` — `{colors.error}` outline when a prerequisite failed (e.g. evidence insufficient at the draft gate).
- **Gating rules (the product-integrity core):**
  - Step 2 unlocks after the lead exists (title + modalidad).
  - Step 3 unlocks after ≥1 evidence item is linked; it renders the `score-breakdown` and the `evidence_state`.
  - Step 4 (Ficha) unlocks after step 3; it composes "qué se reporta / quién / qué respalda / qué falta / acción".
  - **Step 5 (Borrador) is gated: locked unless `evidence_state ∈ {parcial, suficiente}`.** When `insuficiente`, the step shows `blocked` with the reason "Evidencia insuficiente para generar un borrador" and two honest exits: *Vincular más evidencia* (back to step 2) or *Registrar abstención* (the `abstention-card`). The generate button is never silently clickable from an unsupported state.
  - Step 6 (Revisión) unlocks only after a draft or abstention exists; it drives the five review states.
- Mobile: a `{colors.surface-sunken}` strip "Paso 3 de 6 · Priorización" with ‹ › controls; the step list opens as a sheet. Tablet+: full horizontal stepper. Desktop: sticky vertical rail (`panel-sunken`) with the lead summary pinned above it.

**`state-system`** — the shared vocabulary of status, used everywhere (bandeja rows, chips, stepper, tree). Always the same color for the same meaning:
- Evidence: `suficiente` → `{colors.success}` · `parcial` → `{colors.warning}` · `insuficiente` → `{colors.error}` (outline).
- Priority band: `bajo` → `{colors.ink-muted}` · `medio` → `{colors.warning}` · `alto` → `{colors.error}`.
- Review: `nuevo` → info · `en_revision` → `{colors.primary}` · `requiere_evidencia` → `{colors.warning}` · `aprobado_borrador` → `{colors.success}` · `descartado` → `{colors.ink-muted}`.
- Rendered as `state-chip` pills; in dense tables, as a 8px leading dot + `{typography.label}`.

**`score-breakdown`** — the `P = 30R + 25I + 20U + 15N + 10E` display.
- The total `P` in `{typography.display-lg}` mono with a `band` `state-chip`; below, five labeled horizontal bars (R/I/U/N/E), each showing the normalized 0–1 value (mono, tabular-nums) and its weight. Rules version shown as a `{typography.caption}` `id-token` (e.g. `reglas v1.2`). Makes priority *explainable*, per the rubric.

**`evidence-tree`** — the hierarchical provenance graph (evolve the existing `EvidenceTree`/`TreeBranch`).
- Node-type badges use the `state-system` family (news=info, indicator=teal/info, event=warning, entity=purple, case=primary). Relations like `contradicts` render in `{colors.error}`. Keep the level controls, but restyle to `button-ghost` + `state-chip`; connector lines use `{colors.hairline}`.

**`abstention-card`** — the explicit "no answer" state, a first-class, recognizable element (not an error).
- `{colors.error}` outline on a soft error fill, `{typography.heading-md}` "Abstención", a plain explanation of what evidence is missing, and the reassurance "Ninguna cifra o cita fue inventada". This is a feature of the product, styled with dignity.

## Do's and Don'ts

### Do
- Work a lead through `lead-stepper` in order; keep each step's content to that step.
- Lock step 5 (Borrador) until `evidence_state` is at least `parcial`; always show the reason and an exit.
- Render every source ID, citation `[id:campo]`, score and hash in `{typography.mono}`.
- Use the `state-system` colors consistently — same color, same meaning, every screen.
- Reserve `{colors.primary}` for one filled action per view; let state colors carry status.
- Set titles and step headers in the serif `{typography.display-font}`; body and tables in Inter.
- Use hairlines and `{colors.surface-sunken}` zones to structure dense data before reaching for shadows.

### Don't
- Don't enable "Generar borrador" from an `insuficiente` state, or show all lead panels at once in a flat scroll.
- Don't invent a draft when evidence is missing — route to `abstention-card` instead.
- Don't put IDs, citations or scores in body sans; mono is how the user tells data from prose.
- Don't reuse a state color for decoration, or introduce a new status color outside the `state-system`.
- Don't use pure white (`#FFFFFF`) as the page background — the page is `{colors.canvas}`; white is for cards.
- Don't adopt TVN's (or any third party's) brand colors — EvidentIA has its own identity; the output is a reviewable draft, not a TVN publication.
- Don't drop shadows on every card; depth is hairlines + one surface step, `{elevation.1}` at rest.

## Responsive Behavior

Mobile-first: a single-column lead flow is the base; wider viewports add the persistent stepper rail and true table columns.

### Breakpoints

| Name | Min Width | Enhancements |
|---|---|---|
| Mobile | base (0px) | Single column, 16px gutters, card padding `{spacing.lg}`, stepper as "Paso n/6" strip + sheet, tables as stacked rows |
| Tablet | 768px (`md`) | Card padding `{spacing.xl}`, full horizontal stepper, tables become columns, two-up chip rows |
| Desktop | 1024px (`lg`) | 1120px container, lead workspace splits into sticky stepper/summary rail + main content, evidence tree gets more horizontal room |

### Touch Targets
All interactive elements hit ≥ 44×44px from the mobile base up; stepper controls, chips with actions, and table row buttons size via padding, never by shrinking below 44px. The theme toggle and session chip are thumb-reachable in the app bar.

### Expansion Strategy
The single mobile column stays single through the whole lead flow; at `lg` the *navigation* of the flow (the stepper) detaches into a persistent rail so the analyst keeps context while scrolling a step. Type scales up modestly (display-xl 28px mobile → 32px desktop). Tables expand from stacked label/value pairs into aligned, tabular-num columns at `md`.

### Image Behavior
Minimal imagery; diagrams and charts scale fluidly inside their `{radius.lg}` `{colors.surface-sunken}` frames, keeping the border and tabular-num labels at every size. No photographic art direction.

## Iteration Guide

1. Refactor one component at a time, referring to it by its stable name (`lead-stepper`, `state-chip`, `score-breakdown`, `id-token`, `abstention-card`).
2. Implement the tokens first: swap the HSL values in `assets/css/tailwind.css` and map them to these names, add the three font families, add dark-mode variables under `.dark`. The rest is reuse.
3. The `lead-stepper` gating is non-negotiable — it is the product's integrity guarantee, not a UX nicety. Never ship a path that generates a draft from `insuficiente`.
4. Keep `{colors.primary}` rare; if more than one filled primary button appears per view, reconsider.
5. Default body to `{typography.body-md}`; dense tables to `{typography.body-sm}`; anything verifiable to `{typography.mono}`.
6. Add new status meanings only inside the `state-system` with a dedicated color+token; never overload an existing one.
7. Light is the default (projector-safe for the pitch); verify every component in dark before calling it done.
8. When adding a component, give it a lowercase-hyphenated name, a `{radius.md}` default, and `{elevation.1}` at rest.

## Known Gaps

- **Dark-mode exact tokens:** canvas/surface/ink/hairline dark values are specified inline above; the full dark ramp for `primary-soft` and the state chips' dark backgrounds still needs a contrast pass (target WCAG AA on text, AA-large on chips).
- **Wordmark/logo:** no EvidentIA mark exists yet; the app bar uses a serif wordmark as a placeholder.
- **Chart spec:** the `score-breakdown` bars and any trend charts need the dataviz palette mapped onto the state colors (sequential for scores, categorical for node types) — defer to a dataviz pass.
- **Stepper persistence:** whether step completion is derived purely from backend state (evidence count, estado, brief existence) or also stored per-lead is an implementation decision for the refactor ticket.
