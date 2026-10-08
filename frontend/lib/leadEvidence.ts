// Step 2 "Evidencia" of the Lead Workspace — catalog data + derivation.
//
// Ported from the design prototype (Lead Workspace v3). The ingest catalog is not
// yet a backend endpoint, so the sources below are seeded locally exactly as the
// design seeds them. Linking a source persists to the real evidence API
// (POST/DELETE /cases/{id}/evidence); the evidence *state* (suficiente / parcial /
// insuficiente), the role lanes, the replica consolidation and the requirement
// checklist are all derived from the linked set, client-side, the same way the
// design computes them.

export type SourceType = "Noticia" | "Documento" | "Indicador" | "Evento";
export type Relation = "Respalda" | "Contradice" | "Contexto";

export interface CatalogSource {
  id: string;
  title: string;
  type: SourceType;
  rel: Relation;
  /** One-line summary of what the source asserts. */
  s: string;
  /** The cited clause / figure inside the source. */
  c: string;
  /** Provenance key — sources sharing it (with `ag`) are replicas of one origin. */
  p: string;
  /** True when the source merely republishes a wire cable (an aggregator). */
  ag?: boolean;
  /** Publishing medium. */
  m: string;
  /** Publication date, human form. */
  d: string;
  /** Geographic scope, when wider than the lead. */
  a?: string;
  /** Verbatim extract shown in the evidence-chain drawer. */
  x: string;
}

// Catalog of ingestable sources (design CAT).
export const CATALOG: CatalogSource[] = [
  { id: "not-0412", title: "Comerciantes de Colón reportan facturas hasta 40% más altas", type: "Noticia", rel: "Respalda", s: "Comerciantes y hogares de Colón reportan facturas hasta 40% más altas en septiembre.", c: "cifra", p: "aip-2209-114", ag: true, m: "La Prensa del Caribe", d: "22 sep 2026", x: "«Los comerciantes consultados mostraron facturas de septiembre hasta un 40% superiores a las de agosto.»" },
  { id: "not-0415", title: "Facturas de luz suben hasta 40% en Colón, según comerciantes", type: "Noticia", rel: "Respalda", s: "Comerciantes de Colón reportan facturas de luz hasta 40% más altas.", c: "cifra", p: "aip-2209-114", ag: true, m: "Diario Atlántico", d: "22 sep 2026", x: "«Según comerciantes del centro, las facturas de luz subieron hasta 40%.» (cable AIP)" },
  { id: "not-0416", title: "Alza de hasta 40% en facturas eléctricas golpea a Colón", type: "Noticia", rel: "Respalda", s: "Facturas eléctricas en Colón con alzas de hasta 40%.", c: "cifra", p: "aip-2209-114", ag: true, m: "Costa Abajo Radio (web)", d: "23 sep 2026", x: "«Comerciantes denuncian alzas de hasta 40% en sus facturas.» (cable AIP)" },
  { id: "res-1187", title: "Resolución tarifaria 1187 del ente regulador, vigente desde 1 sep", type: "Documento", rel: "Respalda", s: "La resolución tarifaria 1187 ajustó la tarifa residencial a partir del 1 de septiembre.", c: "art.3", p: "ere-gaceta", m: "Ente Regulador de Energía", d: "28 ago 2026", x: "«Se ajusta el cargo por energía del bloque residencial de 0 a 300 kWh, con vigencia desde el 1 de septiembre.»" },
  { id: "ind-ipc-09", title: "Índice de precios, componente electricidad, septiembre: +11,2%", type: "Indicador", rel: "Respalda", s: "El componente electricidad del índice de precios subió 11,2% en el mes.", c: "valor", p: "ine-ipc", m: "Instituto Nacional de Estadística", d: "5 oct 2026", a: "Nacional", x: "Electricidad, variación mensual de septiembre: +11,2%." },
  { id: "ind-cons-08", title: "Consumo residencial promedio en Colón, agosto: 312 kWh", type: "Indicador", rel: "Respalda", s: "El consumo residencial promedio se mantuvo en 312 kWh, sin cambios que expliquen el alza.", c: "valor", p: "oen-cons", m: "Observatorio Energético Nacional", d: "15 sep 2026", x: "Consumo residencial promedio por cuenta, Colón, agosto: 312 kWh." },
  { id: "not-0418", title: "Distribuidora atribuye el alza a lecturas estimadas", type: "Noticia", rel: "Contradice", s: "La distribuidora atribuye parte del aumento a lecturas estimadas, no a la tarifa.", c: "declaración", p: "atl-entrevista", m: "Diario Atlántico", d: "24 sep 2026", x: "«Buena parte del aumento responde a lecturas estimadas en agosto», dijo el vocero de la distribuidora." },
  { id: "doc-dist-0921", title: "Comunicado de la distribuidora sobre lecturas estimadas", type: "Documento", rel: "Contradice", s: "Un comunicado oficial de la distribuidora reconoce lecturas estimadas en agosto.", c: "párr.2", p: "disca-com", m: "Distribuidora Caribe (DisCa)", d: "21 sep 2026", x: "«Durante agosto se aplicaron lecturas estimadas en parte de las cuentas residenciales.»" },
  { id: "evt-0930", title: "Protesta vecinal frente a oficinas de la distribuidora", type: "Evento", rel: "Contexto", c: "registro", p: "corr-colon", m: "Corresponsalía Colón", d: "30 sep 2026", x: "Vecinos de Barrio Norte se concentran frente a las oficinas de DisCa.", s: "Protesta vecinal frente a las oficinas de la distribuidora." },
  { id: "not-0399", title: "Gremio empresarial pide congelar tarifas por seis meses", type: "Noticia", rel: "Contexto", c: "cita", p: "ccc-com", m: "Diario Atlántico", d: "19 sep 2026", x: "«Pedimos congelar las tarifas por seis meses mientras se revisa la resolución.»", s: "El gremio empresarial pide congelar las tarifas por seis meses." },
];

// Provenance behind each source (design D, "procedencia" entries). Keyed by `p`.
export interface Provenance {
  t: string;
  m: string;
  d: string;
  f: string;
  x: string;
}
export const PROVENANCE: Record<string, Provenance> = {
  "aip-2209-114": { t: "Cable AIP-2209-114 · Agencia Istmo de Prensa", m: "Agencia Istmo de Prensa · servicio de cables", d: "22 sep 2026", f: "cable", x: "Cable con testimonios de seis comerciantes del centro de Colón. Los medios que lo publican no añaden reporteo propio." },
  "ere-gaceta": { t: "Gaceta Oficial · Ente Regulador de Energía", m: "Gaceta Oficial", d: "28 ago 2026", f: "publicación", x: "Publicación oficial de la resolución 1187, con vigencia desde el 1 de septiembre." },
  "ine-ipc": { t: "INE · Índice de precios al consumidor, serie mensual", m: "Instituto Nacional de Estadística", d: "5 oct 2026", f: "serie", x: "Serie oficial mensual, componente «electricidad, gas y otros combustibles»." },
  "oen-cons": { t: "Observatorio Energético Nacional · datos abiertos", m: "Portal de datos abiertos del OEN", d: "15 sep 2026", f: "dataset", x: "Dataset de consumo residencial por provincia, actualización mensual." },
  "atl-entrevista": { t: "Diario Atlántico · entrevista propia al vocero de DisCa", m: "Diario Atlántico", d: "24 sep 2026", f: "entrevista", x: "Reporteo propio del medio; la declaración no viene acompañada de datos." },
  "disca-com": { t: "Distribuidora Caribe · sala de prensa oficial", m: "Distribuidora Caribe (DisCa)", d: "21 sep 2026", f: "comunicado", x: "Comunicado firmado por la gerencia comercial de la distribuidora." },
  "corr-colon": { t: "Corresponsalía Colón · observación directa", m: "Equipo propio", d: "30 sep 2026", f: "registro", x: "Registro del corresponsal con fotos y conteo aproximado de asistentes." },
  "ccc-com": { t: "Cámara de Comercio de Colón · comunicado reproducido por medio", m: "Diario Atlántico (reproducción)", d: "19 sep 2026", f: "comunicado", x: "El medio reproduce el comunicado gremial sin documento adjunto." },
};

// Sources the "Vincular ejemplo" seed links (design EX_LINK).
export const EXAMPLE_LINK = ["not-0412", "not-0415", "not-0416", "res-1187", "not-0418", "evt-0930"];

// --- Evidence chain (the per-source tree) --------------------------------
// The central claim all evidence hangs off (design CLAIM).
export const CLAIM = "La factura residencial en Colón subió hasta 40% en septiembre.";

// Level names N1..N5 (design LV).
export const LEVEL_NAMES = ["Fuentes", "Procedencia", "Entidades", "Indicadores y eventos", "Correlaciones"];

// Non-catalog, non-provenance nodes referenced by the chain (design D entries:
// entidad / indicador / correlación / evento). { k: kind, t: title }.
export const NODES: Record<string, { k: string; t: string }> = {
  "ent-comerciantes": { k: "entidad", t: "Asociación de Comerciantes de Colón" },
  "ent-disca": { k: "entidad", t: "Distribuidora Caribe (DisCa)" },
  "ent-ere": { k: "entidad", t: "Ente Regulador de Energía (ERE)" },
  "ent-ine": { k: "entidad", t: "Instituto Nacional de Estadística (INE)" },
  "ent-hogares": { k: "entidad", t: "Hogares residenciales de Colón" },
  "ent-vecinos": { k: "entidad", t: "Comité vecinal de Barrio Norte" },
  "ent-ccc": { k: "entidad", t: "Cámara de Comercio de Colón" },
  "ind-tar-res": { k: "indicador", t: "Cargo por energía, bloque 0–300 kWh: +18%" },
  "ind-ipc-08": { k: "indicador", t: "IPC electricidad, agosto: +0,4%" },
  "ind-cons-07": { k: "indicador", t: "Consumo residencial promedio en Colón, julio: 309 kWh" },
  "evt-ajuste": { k: "evento", t: "DisCa anuncia ajuste de facturas estimadas en octubre" },
  "cor-brecha": { k: "correlación", t: "Tarifa +18% e IPC +11,2% no alcanzan para explicar un alza de 40%" },
  "cor-prot": { k: "correlación", t: "La protesta ocurre 8 días después de la primera factura con la nueva tarifa" },
  "cor-tarcons": { k: "correlación", t: "Tarifa +18% con consumo estable explica cerca de la mitad del alza reportada" },
  "cor-lect": { k: "correlación", t: "Las lecturas estimadas de agosto podrían explicar el resto del alza" },
  "cor-salto": { k: "correlación", t: "El salto del IPC (+0,4% → +11,2%) coincide con la vigencia de res-1187" },
  "cor-cons": { k: "correlación", t: "Consumo estable (309 → 312 kWh) descarta un alza por mayor uso" },
  "cor-presion": { k: "correlación", t: "La presión social antecede la revisión tarifaria anunciada por el ERE" },
  "cor-congelar": { k: "correlación", t: "El pedido gremial asume que res-1187 causa el alza" },
};

type SubEntry = [string, Relation | "Corrobora" | "Menciona", SubEntry[]?];
// Adjacency below each provenance (design SUB), keyed by provenance id.
export const SUB: Record<string, SubEntry[]> = {
  "aip-2209-114": [["ent-comerciantes", "Menciona", [["ind-ipc-09", "Contexto", [["cor-brecha", "Contradice"]]]]], ["ent-disca", "Menciona", [["evt-0930", "Contexto", [["cor-prot", "Corrobora"]]]]]],
  "ere-gaceta": [["ent-ere", "Menciona", [["ind-tar-res", "Respalda", [["cor-tarcons", "Corrobora"]]]]], ["ent-disca", "Menciona", [["doc-dist-0921", "Contradice", [["cor-lect", "Contradice"]]]]]],
  "ine-ipc": [["ent-ine", "Menciona", [["ind-ipc-08", "Contexto", [["cor-salto", "Corrobora"]]]]]],
  "oen-cons": [["ent-hogares", "Menciona", [["ind-cons-07", "Contexto", [["cor-cons", "Respalda"]]]]]],
  "atl-entrevista": [["ent-disca", "Contradice", [["doc-dist-0921", "Corrobora", [["cor-lect", "Contradice"]]]]]],
  "disca-com": [["ent-disca", "Menciona", [["evt-ajuste", "Contexto", [["cor-lect", "Contradice"]]]], ["ent-ere", "Menciona", [["res-1187", "Contexto"]]]]],
  "corr-colon": [["ent-vecinos", "Menciona", [["not-0399", "Contexto", [["cor-presion", "Contexto"]]]]]],
  "ccc-com": [["ent-ccc", "Menciona", [["res-1187", "Contexto", [["cor-congelar", "Respalda"]]]]]],
}; // NOTE: `disca-com` is normalized to a single array of two branches.

const CATALOG_BY_ID = Object.fromEntries(CATALOG.map((s) => [s.id, s]));
function nodeInfo(id: string): { kind: string; title: string } {
  const c = CATALOG_BY_ID[id];
  if (c) return { kind: c.type.toLowerCase(), title: c.title };
  const n = NODES[id];
  if (n) return { kind: n.k, title: n.t };
  const p = PROVENANCE[id];
  if (p) return { kind: "procedencia", title: p.t };
  return { kind: "procedencia", title: id };
}

export interface ChainNode {
  id: string;
  title: string;
  kind: string;
  rel: string;
  depth: number; // N1 source = 1, provenance = 2, …
}
export interface ChainLevel {
  level: number;
  name: string;
  nodes: ChainNode[];
}
export interface SourceChain {
  levels: ChainLevel[];
  counts: { ent: number; datos: number; corr: number };
  contradictions: number;
}

// Build one source's evidence chain: source (N1) → provenance (N2) → SUB subtree
// (entidad N3 → indicador/documento/evento N4 → correlación N5).
export function buildSourceChain(sourceId: string): SourceChain {
  const src = CATALOG_BY_ID[sourceId];
  const nodes: ChainNode[] = [];
  if (!src) return { levels: [], counts: { ent: 0, datos: 0, corr: 0 }, contradictions: 0 };

  const prov = PROVENANCE[src.p];
  if (prov) {
    nodes.push({ id: src.p, title: prov.t, kind: "procedencia", rel: "Procedencia", depth: 2 });
    const walk = (entries: SubEntry[], depth: number) => {
      for (const [id, rel, kids] of entries) {
        const info = nodeInfo(id);
        nodes.push({ id, title: info.title, kind: info.kind, rel, depth });
        if (kids && kids.length) walk(kids, depth + 1);
      }
    };
    walk(SUB[src.p] ?? [], 3);
  }

  const levels: ChainLevel[] = [];
  for (let d = 2; d <= 5; d++) {
    const seen = new Set<string>();
    const atDepth = nodes.filter((n) => n.depth === d && !seen.has(n.id) && seen.add(n.id));
    if (atDepth.length) levels.push({ level: d, name: LEVEL_NAMES[d - 1], nodes: atDepth });
  }
  return {
    levels,
    counts: {
      ent: nodes.filter((n) => n.depth === 3).length,
      datos: nodes.filter((n) => n.depth === 4).length,
      corr: nodes.filter((n) => n.depth === 5).length,
    },
    contradictions: nodes.filter((n) => n.rel === "Contradice").length,
  };
}

export type EvidenceLevel = "none" | "insuficiente" | "parcial" | "suficiente";

export interface EvidenceState {
  key: EvidenceLevel;
  label: string;
  short: string;
  /** Longer rationale shown where there is room (e.g. step 3 Contexto). */
  explain: string;
  /** DESIGN tone → drives card/strip color. */
  tone: "neutral" | "error" | "warning" | "success";
}
export const EVIDENCE_STATES: Record<EvidenceLevel, EvidenceState> = {
  none: { key: "none", label: "sin fuentes", short: "Aún no hay fuentes vinculadas.", explain: "Aún no hay fuentes vinculadas.", tone: "neutral" },
  insuficiente: { key: "insuficiente", label: "insuficiente", short: "Ninguna fuente primaria respalda la afirmación.", explain: "Ninguna fuente primaria respalda la cifra central. No es posible generar un borrador con esta evidencia.", tone: "error" },
  parcial: { key: "parcial", label: "parcial", short: "Una fuente primaria respalda; falta corroborar.", explain: "Una fuente primaria respalda la afirmación. El borrador es posible, pero marcará lo que falta corroborar.", tone: "warning" },
  suficiente: { key: "suficiente", label: "suficiente", short: "Dos fuentes primarias independientes respaldan la afirmación.", explain: "La afirmación central está respaldada por al menos dos fuentes primarias independientes.", tone: "success" },
};

export const RELATION_LABEL: Record<Relation, string> = {
  Respalda: "Respaldan",
  Contradice: "Contradicen",
  Contexto: "Contexto",
};

// A primary source is a document or indicator that supports the claim — the press
// does not count (design isPrim: rel === 'Respalda' && type !== 'Noticia').
export function isPrimary(src: CatalogSource): boolean {
  return src.rel === "Respalda" && src.type !== "Noticia";
}

export interface LaneCard {
  /** Stable key for the merged node (the lead provenance group or the single id). */
  key: string;
  /** Representative source shown on the card. */
  head: CatalogSource;
  /** All sources merged into this card (replicas of one origin). */
  members: CatalogSource[];
  primary: boolean;
  /** The source's evidence chain (N2..N5 under it). */
  chain: SourceChain;
}

export interface Lane {
  rel: Relation;
  label: string;
  cards: LaneCard[];
  empty: string;
}

export interface Check {
  label: string;
  note: string;
  detail: string;
  status: "ok" | "warn" | "todo" | "info";
}

export interface DerivedEvidence {
  linked: CatalogSource[];
  state: EvidenceState;
  /** Independent primary provenances, capped display handled by caller. */
  primN: number;
  /** Total contradicting sources. */
  conN: number;
  hasContra: boolean;
  /** Replica groups with more than one member, by size. */
  replicaGroups: { p: string; size: number }[];
  lanes: Lane[];
  checks: Check[];
}

// Merge replicas: sources that share a provenance and are aggregators collapse into
// one card (design: "3 réplicas del mismo cable = 1 fuente").
function mergeCards(sources: CatalogSource[]): LaneCard[] {
  const byGroup = new Map<string, CatalogSource[]>();
  for (const src of sources) {
    const key = src.ag ? `p:${src.p}` : `id:${src.id}`;
    const bucket = byGroup.get(key);
    if (bucket) bucket.push(src);
    else byGroup.set(key, [src]);
  }
  return [...byGroup.entries()].map(([key, members]) => ({
    key,
    head: members[0],
    members,
    primary: isPrimary(members[0]),
    chain: buildSourceChain(members[0].id),
  }));
}

export function deriveEvidence(linkedIds: string[]): DerivedEvidence {
  const linked = CATALOG.filter((s) => linkedIds.includes(s.id));

  // Independent primaries: primary sources deduped by provenance.
  const primProvenances = new Set(linked.filter(isPrimary).map((s) => s.p));
  const primN = primProvenances.size;

  const contra = linked.filter((s) => s.rel === "Contradice");
  const conN = contra.length;
  const hasContra = conN > 0;

  // Replica groups (aggregators sharing a provenance), size > 1.
  const groupSizes = new Map<string, number>();
  for (const s of linked) {
    if (!s.ag) continue;
    groupSizes.set(s.p, (groupSizes.get(s.p) ?? 0) + 1);
  }
  const replicaGroups = [...groupSizes.entries()]
    .filter(([, size]) => size > 1)
    .map(([p, size]) => ({ p, size }));

  let level: EvidenceLevel;
  if (linked.length === 0) level = "none";
  else if (primN === 0) level = "insuficiente";
  else if (primN === 1) level = "parcial";
  else level = "suficiente";

  const lanes: Lane[] = (
    [
      ["Respalda", "Sin fuentes que respalden la afirmación."],
      ["Contradice", "Sin versión contraria. Busca la de la distribuidora."],
      ["Contexto", "Opcional: eventos y reacciones."],
    ] as [Relation, string][]
  ).map(([rel, empty]) => ({
    rel,
    label: RELATION_LABEL[rel],
    empty,
    cards: mergeCards(linked.filter((s) => s.rel === rel)),
  }));

  const firstReplica = replicaGroups[0];
  const checks: Check[] = [
    {
      label: "Al menos una fuente vinculada",
      note: "Requerido para continuar a Contexto",
      detail: String(linked.length),
      status: linked.length ? "ok" : "todo",
    },
    {
      label: "Dos fuentes primarias independientes",
      note: "Documentos o indicadores · la prensa no cuenta",
      detail: `${Math.min(primN, 2)}/2`,
      status: primN >= 2 ? "ok" : primN === 1 ? "warn" : "todo",
    },
    {
      label: "Versión contraria identificada",
      note: hasContra ? "El borrador presentará ambas versiones" : "Recomendado · p. ej. la versión de la distribuidora",
      detail: String(conN),
      status: hasContra ? "ok" : "todo",
    },
    {
      label: "Réplicas del mismo origen",
      note: firstReplica ? `${firstReplica.size} notas del cable AIP cuentan como 1 fuente` : "Se consolidan automáticamente",
      detail: firstReplica ? `${firstReplica.size} → 1` : "—",
      status: "info",
    },
  ];

  return {
    linked,
    state: EVIDENCE_STATES[level],
    primN,
    conN,
    hasContra,
    replicaGroups,
    lanes,
    checks,
  };
}

// Map a catalog source onto the backend evidence payload. The backend stores a
// free-form `fuente_tipo` plus the analytic `rol`; we keep the catalog id as
// `fuente_id` so links round-trip.
const TIPO_BY_TYPE: Record<SourceType, string> = {
  Noticia: "news",
  Documento: "document",
  Indicador: "indicator",
  Evento: "event",
};
export function evidencePayload(src: CatalogSource) {
  return {
    fuente_tipo: TIPO_BY_TYPE[src.type],
    fuente_id: src.id,
    rol: src.rel,
    nota: src.s,
    marcado_manual: true,
  };
}
