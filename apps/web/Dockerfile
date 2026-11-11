# syntax=docker/dockerfile:1
ARG NODE_IMAGE=node:26-trixie-slim
# Harus sama dengan wasm-bindgen di Cargo.toml dan wasm_bindgen_version di justfile.
ARG WASM_BINDGEN_VERSION=0.2.130

# ---------- Tahap 0: Rust → WASM ----------
FROM debian:trixie-slim AS wasm
ARG WASM_BINDGEN_VERSION
# gcc dan libc6-dev: wasm-bindgen-cli dikompilasi untuk mesin build (bukan untuk wasm).
RUN apt-get update \
  && apt-get install -y --no-install-recommends gcc libc6-dev curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*
ENV RUSTUP_HOME=/opt/rustup CARGO_HOME=/opt/cargo PATH=/opt/cargo/bin:$PATH
WORKDIR /repo
COPY rust-toolchain.toml ./
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
  | sh -s -- -y --profile minimal --default-toolchain none \
  && rustup toolchain install
# Layer sendiri: hanya dibangun ulang bila versi CLI berubah.
RUN cargo install wasm-bindgen-cli --version ${WASM_BINDGEN_VERSION} --locked
COPY Cargo.toml Cargo.lock ./
COPY packages/rust ./packages/rust
# Perintah yang sama dengan resep `just wasm`.
RUN --mount=type=cache,target=/opt/cargo/registry \
  --mount=type=cache,target=/repo/target \
  cargo build -p lab-numerics-wasm --target wasm32-unknown-unknown --profile wasm-release --locked \
  && wasm-bindgen target/wasm32-unknown-unknown/wasm-release/lab_numerics_wasm.wasm \
  --target web --omit-default-module-path --out-dir /out/glue --out-name lab_numerics \
  && mkdir -p /out/bin \
  && mv /out/glue/lab_numerics_bg.wasm /out/bin/

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
# Glue JS/TS dan biner WASM dari tahap 0 (tidak ada di repo).
COPY --from=wasm /out/glue apps/web/src/wasm/lab-numerics
COPY --from=wasm /out/bin apps/web/public/wasm
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
