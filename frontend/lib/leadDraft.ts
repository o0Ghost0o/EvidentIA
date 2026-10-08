// Step 5 "Borrador" of the Lead Workspace — draft composition from linked evidence.
//
// Ported from the design prototype (Lead Workspace v3). The draft is written only
// from the linked set: every sentence carries a verifiable citation and nothing
// outside the evidence is filled in — what is not backed is flagged, not invented.
// Both the sentence list and the gap list are derived client-side the same way the
// design composes them, so the generation step has no model dependency yet.

import { CATALOG, type EvidenceLevel } from "~/lib/leadEvidence";

// How a sentence is classified. Drives the small uppercase tag after each line.
export type DraftClass = "hecho" | "declaración" | "inferencia" | "hipótesis";

export interface DraftMode {
  /** Trim the draft to its core sentences under ~250 words. */
  short: boolean;
  /** Hedge the attributable sentences with more cautious phrasing. */
  cautious: boolean;
}

export interface DraftSentence {
  /** Stable key, used to flag a sentence or request a second source for it. */
  key: string;
  cls: DraftClass;
  /** Core sentences survive the "short" mode trim. */
  core: boolean;
  /** Citation shown after the sentence, form `[id:campo]`. */
  cite: string;
  text: string;
}

// Count words the way the design does — whitespace-separated, empties dropped.
export function words(s: string): number {
  return s.trim().split(/\s+/).filter(Boolean).length;
}

// Compose the draft sentences from the linked set (design draftSents). Each clause
// appears only when its source is linked; the cautious variant, when present,
// replaces the plain text under "Más cauto".
export function draftSents(
  linkedIds: string[],
  mode: DraftMode,
  title: string,
  catalog: CatalogSource[] = CATALOG
): DraftSentence[] {
  const has = (id: string) => linkedIds.includes(id);
  const out: DraftSentence[] = [];
  const add = (key: string, cls: DraftClass, core: boolean, cite: string, t: string, k?: string) =>
    out.push({ key, cls, core, cite, text: mode.cautious && k ? k : t });

  const isMock = linkedIds.some((id) => id.startsWith("not-") || id.startsWith("res-") || id.startsWith("doc-"));
  if (isMock) {
    const reps = catalog.filter((c) => c.ag && has(c.id));
    if (reps.length)
      add(
        "cable",
        "declaración",
        true,
        `[${reps[0].id}:cifra]`,
        `Comerciantes y hogares de Colón reportan facturas de septiembre hasta 40% más altas que las de agosto, según un cable de la Agencia Istmo de Prensa${reps.length > 1 ? ` replicado por ${reps.length} medios` : ""}.`,
        `Según testimonios de comerciantes recogidos por un cable de agencia${reps.length > 1 ? ` (${reps.length} réplicas, una sola fuente)` : ""}, algunas facturas de septiembre habrían sido hasta 40% más altas; ninguna fuente independiente ha medido esa cifra.`
      );
    if (has("res-1187")) {
      add("res", "hecho", true, "[res-1187:art.3]", "La resolución tarifaria 1187 del Ente Regulador de Energía ajustó la tarifa residencial a partir del 1 de septiembre.");
      add("tar", "hecho", true, "[ind-tar-res:anexo.B]", "Su anexo eleva el cargo por energía del bloque residencial de 0 a 300 kWh de 0,142 a 0,168 por kWh, un 18%.");
    }
    if (has("ind-ipc-09"))
      add("ipc", "hecho", false, "[ind-ipc-09:valor]", "El componente electricidad del índice de precios nacional subió 11,2% en septiembre, frente a 0,4% en agosto.");
    if (has("ind-cons-08"))
      add("cons", "hecho", false, "[ind-cons-08:valor]", "El consumo residencial promedio en Colón fue de 312 kWh en agosto, frente a 309 kWh en julio.");
    if (has("res-1187"))
      add(
        "calc",
        "inferencia",
        true,
        "[cor-tarcons:cálculo]",
        "Con un consumo estable, el ajuste tarifario explicaría cerca de 18% de la factura típica, menos de la mitad del alza reportada.",
        "Un cálculo preliminar, aún sin revisión editorial, sugiere que con consumo estable el ajuste tarifario explicaría cerca de 18% de la factura típica."
      );
    if (has("not-0418"))
      add(
        "vocero",
        "declaración",
        true,
        "[not-0418:declaración]",
        "La distribuidora atribuye buena parte del aumento a lecturas estimadas en agosto, según declaró su vocero al Diario Atlántico.",
        "El vocero de la distribuidora afirmó al Diario Atlántico, sin aportar datos, que buena parte del aumento respondería a lecturas estimadas en agosto."
      );
    if (has("doc-dist-0921"))
      add("com", "hecho", true, "[doc-dist-0921:párr.2]", "Un comunicado de DisCa reconoce que en agosto se aplicaron lecturas estimadas en parte de las cuentas residenciales.");
    if (has("not-0399"))
      add(
        "ccc",
        "declaración",
        false,
        "[not-0399:cita]",
        "La Cámara de Comercio de Colón pide congelar las tarifas por seis meses mientras se revisa la resolución.",
        "La Cámara de Comercio de Colón pide, en un comunicado reproducido por prensa, congelar las tarifas por seis meses."
      );
    if (has("evt-0930"))
      add("prot", "hecho", false, "[evt-0930:registro]", "El 30 de septiembre, vecinos de Barrio Norte se concentraron frente a las oficinas de la distribuidora.");
  } else {
    // Dynamic real evidence sources (indicators, news, events)
    const linkedSources = catalog.filter((s) => has(s.id));
    for (const src of linkedSources) {
      if (src.type === "Indicador") {
        add(
          `ind-${src.id}`,
          "hecho",
          true,
          `[${src.id}:${src.c}]`,
          `Según los registros oficiales del ${src.m}, la serie «${src.title}» reporta: ${src.s}.`,
          `Datos estadísticos del ${src.m} indican para ${src.title}: ${src.s}, sujeto a revisión periódica.`
        );
      } else if (src.type === "Evento") {
        add(
          `ev-${src.id}`,
          "hecho",
          true,
          `[${src.id}:${src.c}]`,
          `El servicio geofísico de ${src.m} registró ${src.title} (${src.d}).`,
          `Registro preliminar de ${src.m} indica ${src.title} (${src.d}).`
        );
      } else {
        // Noticia
        add(
          `not-${src.id}`,
          src.rel === "Respalda" ? "hecho" : "declaración",
          true,
          `[${src.id}:${src.c}]`,
          `De acuerdo con ${src.m}${src.d ? ` (${src.d})` : ""}: «${src.s}».`,
          `Según reportó ${src.m}, «${src.s}», información sujeta a verificación de fuentes primarias.`
        );
      }
    }
  }

  if (!mode.short) return out;

  // Short mode: keep only core sentences while the running word count stays ≤250.
  let w = words(title || "");
  const keep: DraftSentence[] = [];
  out
    .filter((s) => s.core)
    .forEach((s) => {
      const n = words(s.text);
      if (w + n <= 250) {
        keep.push(s);
        w += n;
      }
    });
  return keep;
}

// The gaps the draft marks rather than fills (design draftGaps)
export function draftGaps(linkedIds: string[], ev: EvidenceLevel, catalog: CatalogSource[] = CATALOG): string[] {
  const g: string[] = [];
  const linked = catalog.filter((c) => linkedIds.includes(c.id));
  const hasPrimaries = linked.some((c) => c.type === "Indicador" || c.type === "Documento");
  const hasContra = linked.some((c) => c.rel === "Contradice");

  if (!hasPrimaries) {
    g.push("Sin fuentes primarias independientes: solo testimonios en prensa sin respaldo estadístico o documental.");
  }
  if (ev === "parcial") {
    g.push("Evidencia parcial: se requiere una segunda fuente primaria independiente que corrobore los datos.");
  }
  if (!hasContra) {
    g.push("Sin versión contraria vinculada: se recomienda contrastar con la contraparte o entidad reguladora.");
  }
  return g;
}
