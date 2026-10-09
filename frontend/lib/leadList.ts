// Leads List derivations — the read-only view the Leads index renders over the
// real case data. Ported from the Lead Workspace v3 design (the `isLeads` screen).
//
// Everything here is derived from fields the backend actually returns
// (`estado`, `evidence[]`, `notes[]`, `updated_at`, `modalidad`). Nothing is
// invented: where the design showed a datum the backend does not store — a
// per-lead priority score — the list omits it rather than fabricate one, in
// keeping with the product's anti-hallucination rule (DESIGN.md).

import { EVIDENCE_STATES, type EvidenceLevel, type EvidenceState } from "~/lib/leadEvidence";
import type { StateTone } from "~/components/ui/StateChip.vue";

// --- Review state ---------------------------------------------------------
// The backend's five review states (see REVIEW_STATES in api/cases.py). Tones
// mirror the lifecycle variants the backend already assigns in
// `_compute_activity_flags`, mapped onto the shared StateChip vocabulary.
export type ReviewState =
  | "nuevo"
  | "en_revision"
  | "requiere_evidencia"
  | "aprobado_borrador"
  | "descartado";

export interface ReviewMeta {
  key: ReviewState;
  label: string;
  tone: StateTone;
  /** Solid color for the distribution bar / legend dot (a semantic token). */
  barVar: string;
}

export const REVIEW_META: Record<ReviewState, ReviewMeta> = {
  nuevo: { key: "nuevo", label: "Nuevo", tone: "neutral", barVar: "hsl(var(--ink-muted))" },
  en_revision: { key: "en_revision", label: "En revisión", tone: "warning", barVar: "hsl(var(--warning))" },
  requiere_evidencia: { key: "requiere_evidencia", label: "Requiere evidencia", tone: "error", barVar: "hsl(var(--error))" },
  aprobado_borrador: { key: "aprobado_borrador", label: "Borrador aprobado", tone: "success", barVar: "hsl(var(--success))" },
  descartado: { key: "descartado", label: "Descartado", tone: "neutral", barVar: "hsl(var(--hairline))" },
};

// Review states in lifecycle order, for the summary bar and the filter tabs.
export const REVIEW_ORDER: ReviewState[] = [
  "nuevo",
  "en_revision",
  "requiere_evidencia",
  "aprobado_borrador",
  "descartado",
];

export function reviewMeta(estado: string): ReviewMeta {
  return REVIEW_META[estado as ReviewState] ?? REVIEW_META.nuevo;
}

// --- Evidence sufficiency -------------------------------------------------
// Derived from the linked evidence items the same way the Lead Workspace derives
// it (leadEvidence.deriveEvidence): a primary is a document or indicator that is
// not a contradiction; the press never counts. Two independent primaries →
// suficiente, one → parcial, linked-but-none → insuficiente, empty → none.
export interface EvidenceLike {
  fuente_tipo: string;
  rol?: string | null;
}

const PRIMARY_TYPES = new Set(["document", "indicator"]);

function isContradiction(rol?: string | null): boolean {
  return /contrad/i.test(rol ?? "");
}

export function deriveEvidenceState(evidence: EvidenceLike[]): EvidenceState {
  if (!evidence.length) return EVIDENCE_STATES.none;
  const primaries = evidence.filter(
    (e) => PRIMARY_TYPES.has(e.fuente_tipo) && !isContradiction(e.rol),
  ).length;
  let level: EvidenceLevel;
  if (primaries === 0) level = "insuficiente";
  else if (primaries === 1) level = "parcial";
  else level = "suficiente";
  return EVIDENCE_STATES[level];
}

const EVIDENCE_TONE: Record<EvidenceState["tone"], StateTone> = {
  neutral: "neutral",
  error: "error",
  warning: "warning",
  success: "success",
};

export function evidenceTone(state: EvidenceState): StateTone {
  return EVIDENCE_TONE[state.tone];
}

// --- Workflow progress ----------------------------------------------------
// The six-step lead flow (Ficha → Evidencia → Contexto → Ficha → Borrador →
// Revisión). The list has no stored step, so the furthest step reached is read
// from the review state and whether evidence is linked — an honest projection of
// status onto the flow, not a second source of truth.
export const STEP_TOTAL = 6;

export interface Progress {
  /** Steps considered complete, 0–6. */
  done: number;
  label: string;
  tone: StateTone;
  /** Lead is closed (descartado): render the rail muted. */
  closed: boolean;
}

export interface ProgressOptions {
  evidenceCount?: number;
  hasScore?: boolean;
  hasFicha?: boolean;
  hasDraft?: boolean;
  hasReview?: boolean;
  notesCount?: number;
}

export function deriveProgress(
  estado: string,
  evidenceOrOptions?: number | ProgressOptions,
  extraOptions?: ProgressOptions,
): Progress {
  const opts: ProgressOptions =
    typeof evidenceOrOptions === "number"
      ? { evidenceCount: evidenceOrOptions, ...(extraOptions || {}) }
      : { ...(evidenceOrOptions || {}) };

  const evidenceCount = opts.evidenceCount ?? 0;
  const hasScore = opts.hasScore ?? false;
  const hasFicha = opts.hasFicha ?? false;
  const hasDraft = opts.hasDraft ?? false;
  const hasReview = opts.hasReview ?? (opts.notesCount ? opts.notesCount > 0 : false);

  if (estado === "descartado") {
    return { done: 0, label: "Descartado", tone: "neutral", closed: true };
  }

  if (estado === "aprobado_borrador") {
    return { done: 6, label: "Borrador aprobado", tone: "success", closed: false };
  }

  // Calculate sequential steps reached based on real data:
  // Step 1: Lead exists (Definido)
  let done = 1;
  // Step 2: Linked sources
  if (evidenceCount > 0) {
    done = 2;
    // Step 3: Priority calculated / scored
    if (hasScore) {
      done = 3;
      // Step 4: Ficha composed / confirmed
      if (hasFicha) {
        done = 4;
        // Step 5: Draft generated / abstained
        if (hasDraft) {
          done = 5;
          // Step 6: Review saved / decision filed
          if (hasReview) {
            done = 6;
          }
        }
      }
    }
  }

  if (estado === "en_revision") {
    const finalDone = Math.max(done, hasReview ? 6 : 5);
    return { done: finalDone, label: "En revisión", tone: "warning", closed: false };
  }

  if (estado === "requiere_evidencia") {
    return {
      done: Math.max(done, evidenceCount > 0 ? 2 : 1),
      label: "Requiere evidencia",
      tone: "error",
      closed: false,
    };
  }

  const LABELS: Record<number, string> = {
    1: "Ficha creada",
    2: "Evidencia vinculada",
    3: "Prioridad calculada",
    4: "Ficha compuesta",
    5: "Borrador listo",
    6: "Revisión lista",
  };
  const TONES: Record<number, StateTone> = {
    1: "neutral",
    2: "info",
    3: "info",
    4: "info",
    5: "warning",
    6: "success",
  };

  return {
    done,
    label: LABELS[done] ?? "Ficha creada",
    tone: TONES[done] ?? "neutral",
    closed: false,
  };
}

// --- Reviewer -------------------------------------------------------------
// The reviewer is the author of the latest review note; none means unassigned.
export interface NoteLike {
  autor: string;
  created_at?: string | null;
}

export interface Reviewer {
  name: string;
  initials: string;
  assigned: boolean;
}

export function deriveReviewer(notes: NoteLike[]): Reviewer {
  if (!notes.length) return { name: "Sin asignar", initials: "··", assigned: false };
  const last = [...notes].sort((a, b) =>
    String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")),
  )[0];
  const name = last.autor.trim() || "Sin asignar";
  const initials =
    name
      .split(/\s+/)
      .map((p) => p[0])
      .filter(Boolean)
      .slice(0, 2)
      .join("")
      .toUpperCase() || "··";
  return { name, initials, assigned: true };
}

// --- Last activity --------------------------------------------------------
// Compact "hace N" stamp in Panamá time (the design footnote notes UTC−5). Falls
// back to a short date for anything older than a week.
export function formatUpdated(iso?: string | null): string {
  if (!iso) return "—";
  const then = new Date(iso);
  if (Number.isNaN(then.getTime())) return "—";
  const diffMs = Date.now() - then.getTime();
  const min = Math.round(diffMs / 60000);
  if (min < 1) return "ahora";
  if (min < 60) return `hace ${min} min`;
  const hr = Math.round(min / 60);
  if (hr < 24) return `hace ${hr} h`;
  const days = Math.round(hr / 24);
  if (days < 7) return `hace ${days} d`;
  return then.toLocaleDateString("es-PA", { day: "2-digit", month: "short" });
}

export const MODALIDAD_LABEL: Record<string, string> = {
  tvn: "TVN",
  banca: "Banca",
};

export function modalidadLabel(m: string): string {
  return MODALIDAD_LABEL[m] ?? m.toUpperCase();
}
