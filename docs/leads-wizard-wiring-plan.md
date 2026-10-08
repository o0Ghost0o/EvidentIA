# Plan: wire the new-lead wizard to real backend data

## Goal

The new-lead wizard at [`frontend/pages/leads/new.vue`](../frontend/pages/leads/new.vue) walks through six steps, but only three touch the backend. Steps 1 (Definir) and 6 (Revisión) persist real data, and step 2 (Evidencia) persists the links it creates. Everything else — the source catalog it links from, the priority score, the ficha, and the draft — is generated in the browser from hardcoded fixtures in `frontend/lib/lead*.ts`. This plan replaces those fixtures with the backend services that already exist, adds the one scoring endpoint that is missing, and keeps the read-only lead detail page working, since it reuses the same step components.

## Current state

| Step | Component | Status today | Backend it should use |
|------|-----------|--------------|------------------------|
| 1 Definir | inline in `new.vue` | Real — `POST /cases` | `POST /cases` (unchanged, plus modalidad) |
| 2 Evidencia | `EvidenceStep.vue` | Links persist, but the catalog, role lanes, chains and evidence state all come from the hardcoded `CATALOG` in `leadEvidence.ts`; the `fuente_id`s it saves (`not-0412`, `res-1187`, …) are not real database rows | `GET /ranking`, `POST`/`DELETE /cases/{id}/evidence`, `GET /cases/{id}/tree` |
| 3 Contexto & Priorización | `ContextStep.vue` | Fake — `computePriority()` returns a constant P = 78 | new `GET /cases/{id}/score` |
| 4 Ficha | `FichaStep.vue` | Fake — rows are template strings; the graph is built from hardcoded `PROVENANCE`/`SUB`/`NODES`. The node-detail modal it opens is already real (`GET /evidence/item`) | `GET /cases/{id}/tree`, `GET /evidence/item` |
| 5 Borrador | `DraftStep.vue` | Fake — a `setTimeout` animation over hardcoded `draftSents`; the real synthesizer is never called | `POST /cases/{id}/brief` |
| 6 Revisión | `ReviewStep.vue` | Real — `POST /cases/{id}/notes` sets `estado` | `POST /cases/{id}/notes` (unchanged) |

Both the wizard and the read-only detail page at [`frontend/pages/leads/[id].vue`](../frontend/pages/leads/%5Bid%5D.vue) import `CATALOG`, `deriveEvidence` and `computePriority` from the fixtures. Any change to how a step sources its data has to be made once in the component and work in both its interactive (wizard) and `readonly` (detail) modes.

## Decisions taken

1. **Modalidad.** Step 1 will collect the real backend modalidad (`tvn` or `banca`) with a selector. The existing Investigación / Verificación / Seguimiento choice stays as a descriptive flag on the case; it does not map to the backend's modalidad, which is the scoring and brief-generation lens.
2. **Priority.** Add a backend endpoint `GET /cases/{id}/score` that runs the existing `score_topic` rules over the case's own linked evidence, rather than duplicating the scoring rules in TypeScript or only reusing a ranking row's score.
3. **Draft.** Wire the real `POST /cases/{id}/brief` and render exactly what it returns — the brief sections, the citations, and the `missing_sources` list. The per-sentence classification (hecho / declaración / inferencia / hipótesis) and the "mark unsupported" / "request second source" controls are dropped from the live draft for now, because the backend does not emit per-sentence data. A Linear ticket tracks extending the synthesizer so that richer UI can return, fully backed by data.

## Work

### Phase 0 — Backend: per-case scoring endpoint

Add `GET /cases/{case_id}/score` in [`backend/src/evidentia/api/cases.py`](../backend/src/evidentia/api/cases.py).

- Resolve the case's linked `EvidenceItem`s (reuse the `_evidence_docs` resolver already in the file, or a lighter variant that only needs counts and dates).
- Derive the inputs `score_topic` expects: `primary_sources` (linked items whose type is not `news`, or the dedup primary count), `has_indicator` (any linked item of type `indicator`), `titular_only` (every linked news item is titular-only), `group_size`, and the most recent `published_at` among linked news.
- Call `evidentia.scoring.score.score_topic(...)` under the case's `modalidad` and return its result unchanged: `P`, `components`, `weights`, `band`, `evidence_state`, `rules_version`.
- Register the route alongside the other `/cases` routes (already covered by the `get_current_user` dependency on the router).
- Tests in `backend/tests`: a case with zero evidence returns `insuficiente` and a low P; a case with one titular-only news item returns `insuficiente`; a case with two primaries (or one primary plus an indicator) returns `suficiente`; the band matches the v1.2 cutoffs.

### Phase 1 — Step 2 Evidencia: link from the real catalog

Rework [`EvidenceStep.vue`](../frontend/components/leads/EvidenceStep.vue) and the fixtures in [`leadEvidence.ts`](../frontend/lib/leadEvidence.ts).

- Replace the hardcoded `CATALOG` drawer with the real source groups from `GET /ranking?modalidad={modalidad}`. Each ranking row carries `ids_fuente`, `group_size`, `dedup` (primary count, agency) and `evidence_state` — enough to list real, linkable sources whose `fuente_id`s exist in the database, so later steps (tree, brief) can resolve them.
- When a source is linked, keep the existing optimistic `POST /cases/{id}/evidence`, sending the real `fuente_id` and `fuente_tipo` (`news` / `indicator` / `event` / `document`) and the chosen `rol`. Unlink stays `DELETE /cases/{id}/evidence/{rowId}`.
- Replace the client-side evidence-state derivation (`deriveEvidence`) with the backend's reading: call `GET /cases/{id}/score` (added in phase 0) after each link/unlink, and show `evidence_state` and the primaries meter from its response. This removes the dependence on the fixture's role/relation metadata.
- The role lanes (Respalda / Contradice / Contexto) and the per-source evidence chain are a design concept the current data does not carry. For this phase, drive the lanes from `rol` on each linked item (the field already exists on `EvidenceItem`, user-selectable at link time), and drive the chain drawer from `GET /cases/{id}/tree` / `GET /evidence/tree` instead of the hardcoded `PROVENANCE`/`SUB`. Confirm the tree shape maps onto the drawer's N0..N5 levels; if it does not, scope the chain drawer down to the relations the tree actually returns.
- Keep `readonly` mode working for the detail page: seed the linked set from the case's saved evidence (as it does now via `initialLinkedIds`) and render lanes/state from the backend, not the fixture.

### Phase 2 — Step 3 Contexto & Priorización: real score

Rework [`ContextStep.vue`](../frontend/components/leads/ContextStep.vue).

- Replace `computePriority()` with a call to `GET /cases/{id}/score`. The component needs the `leadId`, so thread it through as a prop from `new.vue` (the wizard already holds `leadId`) and from `[id].vue`.
- Render `P`, each component value and weight, the band, and the rules version from the response. Keep the "Calcular prioridad" interaction, but have it fetch rather than run a local timer; in `readonly` mode fetch once on mount, as it already does for the fake score.
- Keep the high-priority-with-insufficient-evidence warning, now driven by the backend's `evidence_state` and `band`.
- Retire `computePriority`/`SCORE_COMPONENTS` from [`leadPriority.ts`](../frontend/lib/leadPriority.ts) once both `ContextStep.vue` and `[id].vue` stop importing them; keep `BAND_LABEL` and band cutoffs if still used for labels.

### Phase 3 — Step 4 Ficha: compose from the evidence tree

Rework [`FichaStep.vue`](../frontend/components/leads/FichaStep.vue).

- Build the relations graph from `GET /cases/{id}/tree` (nodes + typed edges) instead of the hardcoded `PROVENANCE`/`SUB`/`NODES`. The `ForceGraph` component and the already-real `EvidenceDetailModal` (which calls `GET /evidence/item`) stay as they are; only the data feeding `fichaGraph` changes.
- The ficha rows (Qué se reporta / Quién / Qué respalda / Qué falta / Acción) are today template heuristics. Compose them from real signals: "Qué respalda" from the primaries in the linked set and the score's `evidence_state`; "Qué falta" from the score state and from the brief's `missing_sources` once phase 4 lands. Where the backend genuinely has no data for a row (for example a narrative "Quién"), either omit the row or label it as not yet derived rather than inventing content.
- Keep the stale-on-change behavior (confirming the ficha, then invalidating it when the linked set changes) and `readonly` mode.

### Phase 4 — Step 5 Borrador: real brief

Rework [`DraftStep.vue`](../frontend/components/leads/DraftStep.vue).

- Replace the simulated generation with a real call to `POST /cases/{id}/brief?formato=json`. Show a genuine loading state while it runs (the synthesizer calls an LLM, so latency is real and variable).
- Render the returned package: `titulo_propuesto`, `brief`, `enfoque`, `preguntas`, `fuentes_y_verificaciones`, `guion`, `copy_digital`, plus the citation counts (`citations_valid`, `citations_dropped`) and the `titular_only` warning. Show `missing_sources` as the "Qué falta" surface.
- Handle the abstention path from the real response: when the backend returns `abstained: true`, render the abstention state with its `reason` instead of a draft. This replaces the current client-only "insufficient evidence blocks the draft" logic, which must stay consistent with the backend's decision.
- Drop the per-sentence classification pills and the "marcar sin respaldo" / "pedir segunda fuente" controls from the live draft (tracked for a later, backed version in the Linear ticket). Keep "Regenerar" as a re-POST.
- `readonly` mode on the detail page should fetch and show the last brief, or a neutral "sin borrador" state if none has been generated. Decide whether briefs are persisted (currently `POST /cases/{id}/brief` regenerates each call); if detail should show a stored brief, that is a follow-up (note it, do not silently assume persistence).

### Phase 5 — Step 1 Definir: modalidad + detail alignment

- Add a `tvn` / `banca` selector to step 1 in [`new.vue`](../frontend/pages/leads/new.vue) and send `modalidad` in the `POST /cases` body. Keep Investigación / Verificación / Seguimiento as a flag, as decided.
- Update [`[id].vue`](../frontend/pages/leads/%5Bid%5D.vue) to stop importing `CATALOG`/`computePriority`, read the real modalidad from the case, and pass `leadId` to the steps that now need it. Verify the read-only ficha renders end to end for a real case.
- Remove the dead fixtures (`CATALOG`, `PROVENANCE`, `SUB`, `NODES`, `draftSents`, `computePriority`, and their helpers) once nothing imports them.

## Risks and open questions

- **Role / relation data.** Respalda / Contradice / Contexto is a design concept the ingest pipeline does not classify today. Phase 1 drives it from the user-chosen `rol`; if the product needs automatic classification, that is separate work.
- **Evidence-chain drawer.** The N0..N5 chain in step 2 is richer than what `GET /cases/{id}/tree` returns. The drawer may need to be scoped down to the relations the tree actually has.
- **Brief persistence.** `POST /cases/{id}/brief` regenerates on every call and does not store the result. If the detail page must show the exact brief a reviewer approved, the brief needs to be persisted — a follow-up to size separately.
- **LLM latency and failure.** Step 5 now depends on a live model call. The UI needs real loading, error and retry states, and a sensible timeout.

## Suggested sequence

Phase 0 first (unblocks steps 2 and 3). Then phase 1, 2, 3, 4 in order, since each later step depends on the linked set and score being real. Phase 5 can land alongside phase 1 (the modalidad selector) with the cleanup done last, once no component imports the fixtures.
