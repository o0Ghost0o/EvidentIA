// Backend-backed types and mappers for the new-lead wizard. These replace the
// hardcoded fixtures in leadEvidence.ts / leadPriority.ts / leadDraft.ts: the
// wizard now links sources from the real ranking catalog, scores the case with
// the deterministic rules endpoint, composes the ficha from the evidence tree and
// generates the draft from the synthesiser.

import type { EvidenceLevel } from "~/lib/leadEvidence";

// --- Evidence roles -------------------------------------------------------
// The analytic role a linked source plays, stored as EvidenceItem.rol.
export type Rol = "respaldo" | "contradiccion" | "contexto";

export const ROL_META: Record<Rol, { label: string; laneLabel: string; empty: string }> = {
  respaldo: {
    label: "Respalda",
    laneLabel: "Respaldan",
    empty: "Sin fuentes que respalden la afirmación.",
  },
  contradiccion: {
    label: "Contradice",
    laneLabel: "Contradicen",
    empty: "Sin versión contraria vinculada.",
  },
  contexto: {
    label: "Contexto",
    laneLabel: "Contexto",
    empty: "Opcional: eventos y reacciones.",
  },
};

export const ROL_ORDER: Rol[] = ["respaldo", "contradiccion", "contexto"];

// Map a legacy/display relation onto the canonical rol, so evidence saved by the
// older UI (Respalda / Contradice / Contexto) still groups correctly.
export function normaliseRol(value: string | null | undefined): Rol {
  const v = (value || "").toLowerCase();
  if (v.startsWith("contrad")) return "contradiccion";
  if (v.startsWith("context")) return "contexto";
  return "respaldo";
}

// --- Ranking catalog ------------------------------------------------------
// One linkable source group from GET /ranking. ids_fuente are real article ids.
export interface RankItem {
  id: string;
  titulo: string;
  modalidad: string;
  ids_fuente: string[];
  group_size: number;
  dedup: { label: string; primary_sources: number; agency: string | null };
  P: number;
  components: Record<string, number>;
  weights: Record<string, number>;
  rules_version: string;
  band: "alto" | "medio" | "bajo";
  evidence_state: "insuficiente" | "parcial" | "suficiente";
}

export interface RankingResponse {
  rules_version: string;
  count: number;
  items: RankItem[];
}

// --- Per-case score -------------------------------------------------------
// GET /cases/{id}/score — the deterministic P over the case's linked evidence.
export interface ScoreResponse {
  P: number;
  components: Record<string, number>;
  weights: Record<string, number>;
  rules_version: string;
  band: "alto" | "medio" | "bajo";
  evidence_state: "insuficiente" | "parcial" | "suficiente";
}

export const BAND_LABEL: Record<string, string> = {
  alto: "alta",
  medio: "media",
  bajo: "baja",
};

// Component display names, keyed by the formula symbol the backend returns.
export const COMPONENT_LABEL: Record<string, string> = {
  R: "Relevancia",
  I: "Impacto",
  U: "Urgencia",
  N: "Novedad",
  E: "Escala",
};

export const SCORE_FORMULA = "P = 30R + 25I + 20U + 15N + 10E";

// A case with no evidence has no evidence_state to show yet; map the backend
// state onto the wizard's level, treating the empty case as "none".
export function evidenceLevelFrom(state: string | null | undefined, linkedCount: number): EvidenceLevel {
  if (!linkedCount) return "none";
  if (state === "suficiente") return "suficiente";
  if (state === "parcial") return "parcial";
  return "insuficiente";
}

// --- Linked evidence item (frontend view) ---------------------------------
export interface LinkedItem {
  /** Backend EvidenceItem row id, null until the POST resolves. */
  rowId: number | null;
  fuenteId: string;
  fuenteTipo: string;
  rol: Rol;
  titulo: string;
}

// --- Edit seed ------------------------------------------------------------
// The workflow modalities ("tipo") the lead can carry, stored as a bare word in
// the case flags. Kept here so both the wizard and the seed mapper agree.
export const WORKFLOW_MODALITIES = new Set([
  "investigación",
  "investigacion",
  "verificación",
  "verificacion",
  "seguimiento",
]);

// A loaded case detail, in the shape the wizard needs to pre-fill. Mirrors the
// fields GET /cases/{id} returns that the edit flow reads.
export interface SeedDetail {
  id: number;
  titulo: string;
  modalidad: string;
  estado: string;
  queries: string[];
  flags: string[];
  evidence: {
    id: number;
    fuente_id: string;
    fuente_tipo: string;
    rol: string;
    nota?: string | null;
    titulo?: string;
  }[];
}

// The wizard's pre-filled state, mapped from a case so LeadWizard can seed its
// Step 1 form, its linked evidence, its score and its review decision.
export interface WizardSeed {
  leadId: number;
  title: string;
  /** Workflow "tipo" word (Investigación / Verificación / Seguimiento). */
  mod: string;
  /** Scoring lens (tvn / banca). */
  modalidad: string;
  alcance: string;
  pregunta: string;
  flags: string[];
  evidenceItems: LinkedItem[];
  score: ScoreResponse | null;
  estado: string;
}

// Map a loaded case (+ its score) onto the wizard seed. The derivation mirrors
// what the read-only ficha (pages/leads/[id].vue) already computes.
export function seedFromDetail(detail: SeedDetail, score: ScoreResponse | null): WizardSeed {
  const flags = detail.flags ?? [];
  const modFlag = flags.find((f) => WORKFLOW_MODALITIES.has(f.toLowerCase())) ?? "";
  const alcFlag = flags.find((f) => f.toLowerCase().startsWith("alcance:"));
  const alcance = alcFlag ? alcFlag.slice(alcFlag.indexOf(":") + 1).trim() : "";
  const evidenceItems: LinkedItem[] = (detail.evidence ?? []).map((e) => ({
    rowId: e.id,
    fuenteId: e.fuente_id,
    fuenteTipo: e.fuente_tipo,
    rol: normaliseRol(e.rol),
    titulo: e.titulo || e.nota || e.fuente_id,
  }));
  return {
    leadId: detail.id,
    title: detail.titulo,
    mod: modFlag,
    modalidad: detail.modalidad,
    alcance,
    pregunta: detail.queries?.[0] ?? "",
    flags,
    evidenceItems,
    score,
    estado: detail.estado,
  };
}

// Rebuild a case's flags array for a Step 1 save: preserve every flag except the
// old workflow-word and Alcance entries, then re-append the current ones. Keeps
// band:/p:/topic_id:/tipo:<source> metadata intact.
export function mergeStep1Flags(existing: string[], tipo: string, alcance: string): string[] {
  const kept = (existing ?? []).filter(
    (f) => !WORKFLOW_MODALITIES.has(f.toLowerCase()) && !f.toLowerCase().startsWith("alcance:"),
  );
  const next = [...kept];
  if (tipo.trim()) next.push(tipo.trim());
  if (alcance.trim()) next.push(`Alcance: ${alcance.trim()}`);
  return next;
}
