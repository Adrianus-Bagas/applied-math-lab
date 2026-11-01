# syntax=docker/dockerfile:1
ARG NODE_IMAGE=node:26-trixie-slim

# ---------- Tahap 1: dependensi ----------
FROM ${NODE_IMAGE} AS deps
# Node 25+ tidak lagi membawa corepack; versi pnpm = packageManager di package.json.
RUN npm install -g pnpm@12.16.1
WORKDIR /repo
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/
RUN --mount=type=cache,id=pnpm-store,target=/pnpm/store \
  pnpm install --frozen-lockfile --filter web --store-dir /pnpm/store

# ---------- Tahap 2: build ----------
FROM deps AS build
COPY apps/web apps/web
ENV NEXT_TELEMETRY_DISABLED=1
# public/ dijamin ada agar COPY di tahap runtime tidak gagal.
RUN mkdir -p apps/web/public && pnpm --filter web build

# ---------- Tahap 3: runtime ----------
FROM ${NODE_IMAGE}
WORKDIR /app
# HOSTNAME=0.0.0.0: Docker mengisi HOSTNAME dengan ID container, dan server.js
# akan mendengarkan alamat itu saja bila tidak ditimpa.
ENV NODE_ENV=production \
  NEXT_TELEMETRY_DISABLED=1 \
  PORT=3000 \
  HOSTNAME=0.0.0.0
COPY --from=build --chown=node:node /repo/apps/web/.next/standalone ./
COPY --from=build --chown=node:node /repo/apps/web/.next/static ./apps/web/.next/static
COPY --from=build --chown=node:node /repo/apps/web/public ./apps/web/public
USER node
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
