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
