/**
 * BFF catch-all: the browser calls /api/<path>, Nitro forwards to FastAPI.
 * Keeps backend hostnames and any future credentials server-side.
 */
export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig();
  const path = (event.context.params?.path || "") as string;
  const query = getQuery(event);
  const qs = new URLSearchParams(query as Record<string, string>).toString();
  const url = `${config.backendUrl}/${path}${qs ? `?${qs}` : ""}`;

  const headers: Record<string, string> = {};
  const contentType = getHeader(event, "content-type");
  if (contentType) headers["content-type"] = contentType;

  let body: unknown;
  if (event.method !== "GET" && event.method !== "HEAD") {
    body = await readBody(event).catch(() => undefined);
  }

  return await $fetch(url, {
    method: event.method as "GET" | "POST" | "PATCH" | "DELETE",
    headers,
    body,
    // Pass backend errors through with their status codes.
    onResponseError({ response }) {
      throw createError({ statusCode: response.status, data: response._data });
    },
  });
});
