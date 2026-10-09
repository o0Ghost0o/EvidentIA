/**
 * GraphRAG semantic constants and visual styles for EvidentIA.
 * Core visual mapping for evidence, cases, indicators, events and graph entities.
 */

export const GRAPH_TYPE_COLORS: Record<string, string> = {
  case: "#0f172a", // Lead central / dark primary
  caso: "#0f172a",
  news: "#0284c7", // Ficha Noticia / sky blue
  noticia: "#0284c7",
  indicator: "#0d9488", // Indicador Banco Mundial / teal
  indicador: "#0d9488",
  event: "#d97706", // Evento Sísmico USGS / amber
  evento: "#d97706",
  entity: "#7c3aed", // Entidad del Grafo / purple
  entidad: "#7c3aed",
  procedencia: "#6366f1", // Indigo procedencia
  documento: "#0284c7",
  correlacion: "#ec4899", // Rosa correlación
  "correlación": "#ec4899",
};

export const GRAPH_TYPE_LABELS: Record<string, string> = {
  case: "Lead Central",
  caso: "Lead Central",
  news: "Noticia",
  noticia: "Noticia",
  indicator: "Indicador WB",
  indicador: "Indicador",
  event: "Sismo USGS",
  evento: "Evento",
  entity: "Entidad",
  entidad: "Entidad",
  procedencia: "Procedencia",
  documento: "Documento",
  correlacion: "Correlación",
  "correlación": "Correlación",
};

export const GRAPH_RELATION_LABELS: Record<string, string> = {
  has_evidence: "Evidencia vinculada",
  mentions: "Menciona entidad",
  same_event: "Mismo evento",
  source_of: "Agencia / Fuente",
  contradicts: "Contradice datos",
  corroborates: "Corrobora",
  Respalda: "Respalda afirmación",
  Contradice: "Contradice datos",
  Contexto: "Contexto adicional",
  Menciona: "Menciona entidad",
  Corrobora: "Corrobora",
};

export const GRAPH_RELATION_COLORS: Record<string, string> = {
  has_evidence: "#3b82f6",
  mentions: "#8b5cf6",
  same_event: "#f59e0b",
  source_of: "#10b981",
  contradicts: "#ef4444",
  corroborates: "#06b6d4",
  Respalda: "#10b981",
  Contradice: "#ef4444",
  Contexto: "#64748b",
  Menciona: "#8b5cf6",
  Corrobora: "#06b6d4",
};
