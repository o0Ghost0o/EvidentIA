/**
 * GraphRAG semantic constants and visual styles for EvidentIA.
 * Core visual mapping for evidence, cases, indicators, events and graph entities.
 */

export const GRAPH_TYPE_COLORS: Record<string, string> = {
  case: "#0f172a", // Lead central / dark primary
  news: "#0284c7", // Ficha Noticia / sky blue
  indicator: "#0d9488", // Indicador Banco Mundial / teal
  event: "#d97706", // Evento Sísmico USGS / amber
  entity: "#7c3aed", // Entidad del Grafo / purple
};

export const GRAPH_TYPE_LABELS: Record<string, string> = {
  case: "Lead Central",
  news: "Noticia",
  indicator: "Indicador WB",
  event: "Sismo USGS",
  entity: "Entidad",
};

export const GRAPH_RELATION_LABELS: Record<string, string> = {
  has_evidence: "Evidencia vinculada",
  mentions: "Menciona entidad",
  same_event: "Mismo evento",
  source_of: "Agencia / Fuente",
  contradicts: "Contradice datos",
  corroborates: "Corrobora",
};

export const GRAPH_RELATION_COLORS: Record<string, string> = {
  has_evidence: "#3b82f6",
  mentions: "#8b5cf6",
  same_event: "#f59e0b",
  source_of: "#10b981",
  contradicts: "#ef4444",
  corroborates: "#06b6d4",
};
