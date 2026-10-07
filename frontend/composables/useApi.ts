/** Typed fetch against the BFF (/api/* → FastAPI). */
export async function api<T>(path: string, opts: { method?: string; body?: unknown; query?: Record<string, string> } = {}): Promise<T> {
  return await $fetch<T>(`/api/${path.replace(/^\//, "")}`, {
    method: (opts.method || "GET") as "GET",
    body: opts.body,
    query: opts.query,
  });
}
