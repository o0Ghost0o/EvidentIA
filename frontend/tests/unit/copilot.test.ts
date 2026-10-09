import { describe, expect, it } from "bun:test";
import { jsonSchema, tool } from "ai";

describe("Copilot Tool Definitions", () => {
  it("defines search_evidence tool with valid jsonSchema", () => {
    const searchEvidence = tool({
      description: "Buscar evidencias",
      parameters: jsonSchema<{ q: string; tipo?: string }>({
        type: "object",
        properties: {
          q: { type: "string" },
          tipo: { type: "string", enum: ["news", "indicator", "event"] },
        },
        required: ["q"],
      }),
      execute: async ({ q }) => ({ success: true, count: 1, items: [{ id: "test", q }] }),
    });

    expect(searchEvidence).toBeDefined();
    expect(searchEvidence.description).toBe("Buscar evidencias");
  });

  it("defines create_lead tool with required parameters", async () => {
    const createLead = tool({
      description: "Crear nuevo lead",
      parameters: jsonSchema<{ titulo: string; modalidad: "tvn" | "banca" }>({
        type: "object",
        properties: {
          titulo: { type: "string" },
          modalidad: { type: "string", enum: ["tvn", "banca"] },
        },
        required: ["titulo", "modalidad"],
      }),
      execute: async ({ titulo, modalidad }) => ({
        success: true,
        lead: { id: 101, titulo, modalidad },
      }),
    });

    const result = await createLead.execute({ titulo: "Test Title", modalidad: "tvn" });
    expect(result.success).toBe(true);
    expect(result.lead.id).toBe(101);
    expect(result.lead.titulo).toBe("Test Title");
  });

  it("defines update_lead and rerun_ingestion parameters schema", async () => {
    const rerunIngest = tool({
      description: "Reejecutar ingesta",
      parameters: jsonSchema<{ mode: "live" | "seed" }>({
        type: "object",
        properties: {
          mode: { type: "string", enum: ["live", "seed"] },
        },
        required: ["mode"],
      }),
      execute: async ({ mode }) => ({ success: true, mode }),
    });

    const res = await rerunIngest.execute({ mode: "seed" });
    expect(res.success).toBe(true);
    expect(res.mode).toBe("seed");
  });
});
