/**
 * EvidentIA Editorial Copilot API endpoint.
 *
 * Runs 100% on the Nitro server using the Vercel AI SDK (ai + @ai-sdk/openai).
 * Uses native jsonSchema validation (zero extra dependencies).
 * Executes multi-step tool calls directly against FastAPI, forwarding the user's JWT bearer token.
 */
import { defineEventHandler, getHeader, readBody, createError } from "h3";
import { streamText, tool, jsonSchema, convertToModelMessages } from "ai";
import { createOpenAI } from "@ai-sdk/openai";

const SYSTEM_PROMPT = `Eres el Copiloto Editorial e Inteligente de EvidentIA, la plataforma de verificación y periodismo de investigación de TVN Media y Vertex DC.

Tus responsabilidades principales:
1. Ayudar a periodistas, analistas y editores a explorar información, crear nuevos leads de investigación, enriquecer y editar leads existentes.
2. Gestionar el ciclo de vida de los leads: estados ('nuevo', 'en_revision', 'requiere_evidencia', 'aprobado_borrador', 'descartado'), asignación de flags, notas de verificación y asociación/desvinculación de evidencias.
3. Monitorear y controlar la ingesta de datos (RSS en vivo de TVN o snapshots de datos semilla) y reportes de calidad.
4. Generar borradores investigativos (briefs) con trazabilidad estricta y citas en formato [id:campo].

Reglas inquebrantables de comportamiento:
- Comunícate de forma precisa, concisa y profesional en español.
- Si el usuario te pide crear, buscar, editar o reejecutar algo, utiliza las herramientas disponibles en el servidor directamente.
- Cuando crees o actualices un lead, menciona su ID claramente (ej: Lead #12) y resume qué cambios se realizaron.
- Jamás inventes datos ni afirmes hechos que no estén respaldados por el catálogo o por las fuentes vinculadas.
- Si no encuentras evidencia suficiente para una afirmación, indícalo de manera transparente.`;

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig();
  const backendUrl = (config.backendUrl || "http://localhost:8000").replace(/\/$/, "");

  // Extract auth header to forward to FastAPI backend
  const authHeader = getHeader(event, "authorization");
  const headers: Record<string, string> = {
    "content-type": "application/json",
  };
  if (authHeader) {
    headers["authorization"] = authHeader;
  }

  // Parse incoming payload
  const body = await readBody(event).catch(() => ({}));
  const rawMessages = body.messages || [];
  const currentContext = body.context || {};

  // Setup model provider
  let model;
  if (config.togetherApiKey) {
    const together = createOpenAI({
      apiKey: config.togetherApiKey as string,
      baseURL: (config.togetherBaseUrl as string) || "https://api.together.xyz/v1",
    });
    model = together.chat(
      (config.llmModel as string) || "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    );
  } else if (config.openaiApiKey) {
    const openai = createOpenAI({
      apiKey: config.openaiApiKey as string,
    });
    model = openai.chat((config.llmModel as string) || "gpt-4o");
  } else {
    throw createError({
      statusCode: 500,
      statusMessage: "Configuración de LLM faltante: TOGETHER_API_KEY u OPENAI_API_KEY no están configuradas.",
    });
  }

  // Helper for server-side FastAPI calls
  async function apiCall<T>(
    path: string,
    opts: { method?: string; body?: unknown; query?: Record<string, string> } = {}
  ): Promise<T> {
    const cleanPath = path.replace(/^\//, "");
    const qs = opts.query ? `?${new URLSearchParams(opts.query).toString()}` : "";
    const url = `${backendUrl}/${cleanPath}${qs}`;
    return await $fetch<T>(url, {
      method: (opts.method || "GET") as "GET" | "POST" | "PATCH" | "DELETE",
      headers,
      body: opts.body,
    });
  }

  // Server-side tools using native jsonSchema from 'ai'
  const tools = {
    search_evidence: tool({
      description:
        "Buscar noticias, indicadores, eventos o elementos del catálogo de evidencias por término de búsqueda.",
      parameters: jsonSchema<{ q: string; tipo?: "news" | "indicator" | "event"; limit?: number }>({
        type: "object",
        properties: {
          q: { type: "string", description: "Término de búsqueda o palabras clave" },
          tipo: {
            type: "string",
            enum: ["news", "indicator", "event"],
            description: "Tipo de fuente opcional para filtrar",
          },
          limit: { type: "number", description: "Número máximo de resultados (por defecto 10)" },
        },
        required: ["q"],
      }),
      execute: async ({ q, tipo, limit }) => {
        try {
          const items = await apiCall<any[]>("/cases/catalog", {
            query: { q, tipo: tipo || "", limit: String(limit || 10) },
          });
          return { success: true, count: items.length, items: items.slice(0, 10) };
        } catch (err: any) {
          return { success: false, error: err?.data?.detail || err?.message || "Error al buscar evidencias" };
        }
      },
    }),

    search_leads: tool({
      description:
        "Buscar y listar leads/casos de investigación existentes, con filtros opcionales por modalidad, estado o texto.",
      parameters: jsonSchema<{ modalidad?: "tvn" | "banca"; estado?: string; query?: string }>({
        type: "object",
        properties: {
          modalidad: {
            type: "string",
            enum: ["tvn", "banca"],
            description: "Filtrar por modalidad investigativa",
          },
          estado: {
            type: "string",
            enum: ["nuevo", "en_revision", "requiere_evidencia", "aprobado_borrador", "descartado"],
            description: "Filtrar por estado de revisión",
          },
          query: {
            type: "string",
            description: "Texto para buscar en título o queries del lead",
          },
        },
      }),
      execute: async ({ modalidad, estado, query }) => {
        try {
          const res = await apiCall<{ count: number; items: any[] }>("/cases", {
            query: modalidad ? { modalidad } : {},
          });
          let items = res.items || [];
          if (estado) {
            items = items.filter((c) => c.estado === estado);
          }
          if (query) {
            const lower = query.toLowerCase();
            items = items.filter(
              (c) =>
                (c.titulo || "").toLowerCase().includes(lower) ||
                (c.queries || []).some((q: string) => q.toLowerCase().includes(lower))
            );
          }
          return {
            success: true,
            total: items.length,
            leads: items.slice(0, 15).map((c) => ({
              id: c.id,
              titulo: c.titulo,
              modalidad: c.modalidad,
              estado: c.estado,
              flags: c.flags,
              evidencias_count: (c.evidence || []).length,
              score: c.score?.puntaje ?? null,
              created_at: c.created_at,
            })),
          };
        } catch (err: any) {
          return { success: false, error: err?.data?.detail || err?.message || "Error al listar leads" };
        }
      },
    }),

    get_lead_details: tool({
      description:
        "Obtener los detalles completos de un lead por su ID numérico (incluye evidencias vinculadas, notas de verificación y desglose de score).",
      parameters: jsonSchema<{ id: number }>({
        type: "object",
        properties: {
          id: { type: "number", description: "ID numérico del lead" },
        },
        required: ["id"],
      }),
      execute: async ({ id }) => {
        try {
          const detail = await apiCall<any>(`/cases/${id}`);
          return { success: true, lead: detail };
        } catch (err: any) {
          return { success: false, error: err?.data?.detail || err?.message || `Lead #${id} no encontrado` };
        }
      },
    }),

    create_lead: tool({
      description: "Crear un nuevo lead de investigación en la plataforma.",
      parameters: jsonSchema<{
        titulo: string;
        modalidad: "tvn" | "banca";
        queries?: string[];
        flags?: string[];
        evidence_ids?: string[];
      }>({
        type: "object",
        properties: {
          titulo: { type: "string", description: "Título claro y conciso del nuevo lead" },
          modalidad: {
            type: "string",
            enum: ["tvn", "banca"],
            description: "Modalidad de investigación (tvn o banca)",
          },
          queries: {
            type: "array",
            items: { type: "string" },
            description: "Términos o preguntas clave de investigación",
          },
          flags: {
            type: "array",
            items: { type: "string" },
            description: "Etiquetas o flags (ej: ['urgente', 'verificar'])",
          },
          evidence_ids: {
            type: "array",
            items: { type: "string" },
            description: "IDs de fuentes para asociar de inmediato como evidencia",
          },
        },
        required: ["titulo", "modalidad"],
      }),
      execute: async ({ titulo, modalidad, queries = [], flags = [], evidence_ids = [] }) => {
        try {
          const created = await apiCall<any>("/cases", {
            method: "POST",
            body: { titulo, modalidad, queries, flags, evidence_ids },
          });
          return {
            success: true,
            message: `Lead #${created.id} creado con éxito.`,
            lead: {
              id: created.id,
              titulo: created.titulo,
              modalidad: created.modalidad,
              estado: created.estado,
              flags: created.flags,
              evidencias_asociadas: (created.evidence || []).length,
            },
          };
        } catch (err: any) {
          return { success: false, error: err?.data?.detail || err?.message || "Error al crear el lead" };
        }
      },
    }),

    update_lead: tool({
      description:
        "Modificar un lead existente (título, modalidad, queries, estado de revisión o flags).",
      parameters: jsonSchema<{
        id: number;
        titulo?: string;
        modalidad?: "tvn" | "banca";
        queries?: string[];
        estado?: "nuevo" | "en_revision" | "requiere_evidencia" | "aprobado_borrador" | "descartado";
        flags?: string[];
      }>({
        type: "object",
        properties: {
          id: { type: "number", description: "ID numérico del lead a modificar" },
          titulo: { type: "string", description: "Nuevo título opcional" },
          modalidad: { type: "string", enum: ["tvn", "banca"], description: "Nueva modalidad opcional" },
          queries: { type: "array", items: { type: "string" }, description: "Nuevas queries de investigación" },
          estado: {
            type: "string",
            enum: ["nuevo", "en_revision", "requiere_evidencia", "aprobado_borrador", "descartado"],
            description: "Nuevo estado de revisión editorial",
          },
          flags: { type: "array", items: { type: "string" }, description: "Lista de flags actualizada" },
        },
        required: ["id"],
      }),
      execute: async ({ id, ...patchData }) => {
        try {
          const updated = await apiCall<any>(`/cases/${id}`, {
            method: "PATCH",
            body: patchData,
          });
          return {
            success: true,
            message: `Lead #${id} modificado correctamente.`,
            lead: {
              id: updated.id,
              titulo: updated.titulo,
              modalidad: updated.modalidad,
              estado: updated.estado,
              flags: updated.flags,
            },
          };
        } catch (err: any) {
          return { success: false, error: err?.data?.detail || err?.message || "Error al actualizar lead" };
        }
      },
    }),

    delete_lead: tool({
      description: "Eliminar un lead de investigación por su ID numérico.",
      parameters: jsonSchema<{ id: number }>({
        type: "object",
        properties: {
          id: { type: "number", description: "ID del lead a eliminar" },
        },
        required: ["id"],
      }),
      execute: async ({ id }) => {
        try {
          await apiCall<void>(`/cases/${id}`, { method: "DELETE" });
          return { success: true, message: `Lead #${id} eliminado satisfactoriamente.` };
        } catch (err: any) {
          return { success: false, error: err?.data?.detail || err?.message || "Error al eliminar lead" };
        }
      },
    }),

    add_lead_flag: tool({
      description: "Añadir una flag a un lead (ej: 'prioritario', 'urgente', 'seguimiento').",
      parameters: jsonSchema<{ id: number; flag: string }>({
        type: "object",
        properties: {
          id: { type: "number", description: "ID del lead" },
          flag: { type: "string", description: "Nombre de la flag a añadir" },
        },
        required: ["id", "flag"],
      }),
      execute: async ({ id, flag }) => {
        try {
          const res = await apiCall<any>(`/cases/${id}/flags`, {
            method: "POST",
            body: { flag },
          });
          return { success: true, flags: res.flags, message: `Flag '${flag}' agregada al lead #${id}.` };
        } catch (err: any) {
          return { success: false, error: err?.data?.detail || err?.message || "Error al añadir flag" };
        }
      },
    }),

    remove_lead_flag: tool({
      description: "Quitar una flag existente de un lead.",
      parameters: jsonSchema<{ id: number; flag: string }>({
        type: "object",
        properties: {
          id: { type: "number", description: "ID del lead" },
          flag: { type: "string", description: "Nombre de la flag a retirar" },
        },
        required: ["id", "flag"],
      }),
      execute: async ({ id, flag }) => {
        try {
          const res = await apiCall<any>(`/cases/${id}/flags/${encodeURIComponent(flag)}`, {
            method: "DELETE",
          });
          return { success: true, flags: res.flags, message: `Flag '${flag}' retirada del lead #${id}.` };
        } catch (err: any) {
          return { success: false, error: err?.data?.detail || err?.message || "Error al retirar flag" };
        }
      },
    }),

    add_lead_evidence: tool({
      description: "Vincular una fuente (noticia, indicador o evento) como evidencia de un lead.",
      parameters: jsonSchema<{
        id: number;
        fuente_tipo: "news" | "indicator" | "event" | "document";
        fuente_id: string;
        rol?: string;
        nota?: string;
      }>({
        type: "object",
        properties: {
          id: { type: "number", description: "ID del lead" },
          fuente_tipo: {
            type: "string",
            enum: ["news", "indicator", "event", "document"],
            description: "Tipo de fuente de la evidencia",
          },
          fuente_id: { type: "string", description: "Identificador exacto de la fuente" },
          rol: {
            type: "string",
            description: "Rol investigativo (ej: 'respaldo', 'contexto', 'contradiccion')",
          },
          nota: { type: "string", description: "Nota explicativa" },
        },
        required: ["id", "fuente_tipo", "fuente_id"],
      }),
      execute: async ({ id, fuente_tipo, fuente_id, rol = "respaldo", nota }) => {
        try {
          const res = await apiCall<any>(`/cases/${id}/evidence`, {
            method: "POST",
            body: { fuente_tipo, fuente_id, rol, nota, marcado_manual: true },
          });
          return {
            success: true,
            evidence: res,
            message: `Evidencia ${fuente_id} vinculada al lead #${id}.`,
          };
        } catch (err: any) {
          return { success: false, error: err?.data?.detail || err?.message || "Error al vincular evidencia" };
        }
      },
    }),

    remove_lead_evidence: tool({
      description: "Desvincular un elemento de evidencia de un lead usando el ID de la evidencia vinculada.",
      parameters: jsonSchema<{ id: number; evidence_id: number }>({
        type: "object",
        properties: {
          id: { type: "number", description: "ID del lead" },
          evidence_id: { type: "number", description: "ID numérico de la evidencia a desvincular" },
        },
        required: ["id", "evidence_id"],
      }),
      execute: async ({ id, evidence_id }) => {
        try {
          await apiCall<void>(`/cases/${id}/evidence/${evidence_id}`, { method: "DELETE" });
          return { success: true, message: `Evidencia #${evidence_id} desvinculada del lead #${id}.` };
        } catch (err: any) {
          return { success: false, error: err?.data?.detail || err?.message || "Error al desvincular evidencia" };
        }
      },
    }),

    add_lead_note: tool({
      description:
        "Añadir una nota de verificación editorial al historial del lead, actualizando su estado de revisión.",
      parameters: jsonSchema<{
        id: number;
        texto: string;
        estado_revision: "nuevo" | "en_revision" | "requiere_evidencia" | "aprobado_borrador" | "descartado";
        autor?: string;
      }>({
        type: "object",
        properties: {
          id: { type: "number", description: "ID del lead" },
          texto: { type: "string", description: "Texto de la nota de verificación o comentario editorial" },
          estado_revision: {
            type: "string",
            enum: ["nuevo", "en_revision", "requiere_evidencia", "aprobado_borrador", "descartado"],
            description: "Estado resultante de la revisión",
          },
          autor: { type: "string", description: "Autor de la nota (ej: nombre o rol)" },
        },
        required: ["id", "texto", "estado_revision"],
      }),
      execute: async ({ id, texto, estado_revision, autor = "Copiloto IA" }) => {
        try {
          const note = await apiCall<any>(`/cases/${id}/notes`, {
            method: "POST",
            body: { autor, estado_revision, texto },
          });
          return {
            success: true,
            note,
            message: `Nota guardada y estado del lead #${id} actualizado a '${estado_revision}'.`,
          };
        } catch (err: any) {
          return { success: false, error: err?.data?.detail || err?.message || "Error al añadir nota" };
        }
      },
    }),

    rerun_ingestion: tool({
      description:
        "Reejecutar el pipeline de ingesta de datos. Soporta RSS en vivo de TVN ('live') o snapshot congelado de datos semilla ('seed').",
      parameters: jsonSchema<{ mode: "live" | "seed"; sync?: boolean }>({
        type: "object",
        properties: {
          mode: {
            type: "string",
            enum: ["live", "seed"],
            description: "'live' para RSS en vivo de TVN o 'seed' para snapshot semilla",
          },
          sync: {
            type: "boolean",
            description: "true para ejecutar sincrónicamente, false para encolar en segundo plano",
          },
        },
        required: ["mode"],
      }),
      execute: async ({ mode, sync = true }) => {
        try {
          if (mode === "live") {
            const res = await apiCall<any>("/ingest/live-now", { method: "POST" });
            return { success: true, mode: "live", result: res, message: "Ingesta en vivo ejecutada correctamente." };
          } else {
            const res = await apiCall<any>("/ingest/run", {
              method: "POST",
              query: { sync: sync ? "true" : "false", use_seed: "true" },
            });
            return { success: true, mode: "seed", result: res, message: "Ingesta de datos semilla ejecutada." };
          }
        } catch (err: any) {
          return { success: false, error: err?.data?.detail || err?.message || "Error al ejecutar ingesta" };
        }
      },
    }),

    get_ingestion_status: tool({
      description:
        "Consultar el reporte de calidad y salud de la última ingesta (total de registros, anomalías, duplicados).",
      parameters: jsonSchema<Record<string, never>>({
        type: "object",
        properties: {},
      }),
      execute: async () => {
        try {
          const report = await apiCall<any>("/ingest/quality-report");
          return { success: true, report };
        } catch (err: any) {
          return {
            success: false,
            error: err?.data?.detail || err?.message || "No se encontró reporte de ingesta disponible.",
          };
        }
      },
    }),

    generate_lead_brief: tool({
      description:
        "Generar el borrador editorial o brief con validación anti-alucinaciones y citas [id:campo] para un lead.",
      parameters: jsonSchema<{ id: number }>({
        type: "object",
        properties: {
          id: { type: "number", description: "ID numérico del lead" },
        },
        required: ["id"],
      }),
      execute: async ({ id }) => {
        try {
          const brief = await apiCall<any>(`/cases/${id}/brief`, { method: "POST" });
          return { success: true, brief };
        } catch (err: any) {
          return { success: false, error: err?.data?.detail || err?.message || "Error al generar brief" };
        }
      },
    }),

    get_lead_score: tool({
      description: "Consultar el desglose de puntaje de suficiencia de evidencias y banda de prioridad de un lead.",
      parameters: jsonSchema<{ id: number }>({
        type: "object",
        properties: {
          id: { type: "number", description: "ID del lead" },
        },
        required: ["id"],
      }),
      execute: async ({ id }) => {
        try {
          const score = await apiCall<any>(`/cases/${id}/score`);
          return { success: true, score };
        } catch (err: any) {
          return { success: false, error: err?.data?.detail || err?.message || "Error al obtener score" };
        }
      },
    }),
  };

  // Convert incoming UI messages to model messages
  let modelMessages = [];
  if (Array.isArray(rawMessages) && rawMessages.length > 0) {
    if (rawMessages.some((m) => Array.isArray(m?.parts))) {
      modelMessages = await convertToModelMessages(rawMessages);
    } else {
      modelMessages = rawMessages.map((m) => ({
        role: m.role || "user",
        content: typeof m.content === "string" ? m.content : JSON.stringify(m.content),
      }));
    }
  }

  // Inject current app context if available
  let dynamicSystem = SYSTEM_PROMPT;
  if (currentContext && Object.keys(currentContext).length > 0) {
    dynamicSystem += `\n\nContexto actual de la aplicación en el navegador del usuario:\n${JSON.stringify(currentContext, null, 2)}`;
  }

  const result = streamText({
    model,
    system: dynamicSystem,
    messages: modelMessages,
    tools,
    maxSteps: 8,
  });

  return result.toUIMessageStreamResponse();
});
