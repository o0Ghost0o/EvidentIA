// Priority model for step 3 "Contexto & Priorización" of the new-lead wizard.
//
// Mirrors the backend scoring rules v1.2 (evidentia.scoring.score):
//   P = 30R + 25I + 20U + 15N + 10E
// Each component is normalised to 0–1 by documented rules, then weighted. Bands
// were recalibrated in v1.2 to [0,55) baja · [55,75) media · [75,100] alta.
//
// The weights and the worked component values reproduce the Lead Workspace design
// example — a lead that scores P 78 (banda alta):
//   0.90·30 + 0.80·25 + 0.85·20 + 0.60·15 + 0.50·10 = 78.
//
// Priority orders attention; it is explainable, not a truth probability, and a
// high P never authorises publishing: a high P with insufficient evidence means
// "investigate", handled by the evidence state, not the score.

export const RULES_VERSION = "v1.2";

export type PriorityBand = "alto" | "medio" | "bajo";

export interface ScoreComponent {
  /** Symbol used in the formula (R/I/U/N/E). */
  key: "R" | "I" | "U" | "N" | "E";
  label: string;
  /** Percentage weight in the formula. */
  weight: number;
  /** Normalised component value, 0–1. */
  value: number;
}

// Component weights + normalised values (rules v1.2). "Escala" is the evidence
// component (10E in the formula); the backend calls it `score_weight_evidence`.
export const SCORE_COMPONENTS: ScoreComponent[] = [
  { key: "R", label: "Relevancia", weight: 30, value: 0.9 },
  { key: "I", label: "Impacto", weight: 25, value: 0.8 },
  { key: "U", label: "Urgencia", weight: 20, value: 0.85 },
  { key: "N", label: "Novedad", weight: 15, value: 0.6 },
  { key: "E", label: "Escala", weight: 10, value: 0.5 },
];

export const SCORE_FORMULA = "P = 30R + 25I + 20U + 15N + 10E";

// v1.2 band cutoffs (see backend BAND_*_V12).
const BAND_HIGH = 75;
const BAND_MEDIUM = 55;

export function bandFor(p: number): PriorityBand {
  if (p >= BAND_HIGH) return "alto";
  if (p >= BAND_MEDIUM) return "medio";
  return "bajo";
}

export const BAND_LABEL: Record<PriorityBand, string> = {
  alto: "alta",
  medio: "media",
  bajo: "baja",
};

export interface Priority {
  components: ScoreComponent[];
  /** Weighted total P, rounded to an integer. */
  total: number;
  band: PriorityBand;
  rulesVersion: string;
}

export function computePriority(): Priority {
  const total = Math.round(
    SCORE_COMPONENTS.reduce((sum, c) => sum + c.weight * c.value, 0)
  );
  return {
    components: SCORE_COMPONENTS,
    total,
    band: bandFor(total),
    rulesVersion: RULES_VERSION,
  };
}
