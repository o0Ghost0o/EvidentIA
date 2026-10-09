# Nuxt build con Bun + runtime Node optimizado
FROM oven/bun:1-alpine AS build
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile
COPY . .
RUN bun run build

FROM node:22-slim AS run
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl wget && rm -rf /var/lib/apt/lists/*
ENV NITRO_PORT=3000 NITRO_HOST=0.0.0.0 NODE_ENV=production
COPY --from=build /app/.output ./.output
EXPOSE 3000
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3000/healthz || wget -qO- http://localhost:3000/healthz || exit 1
CMD ["node", ".output/server/index.mjs"]
