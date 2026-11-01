# syntax=docker/dockerfile:1

# Tahap build dan runtime wajib memakai image Python yang sama:
# venv menyimpan symlink ke interpreter /usr/local/bin/python3.13.
ARG PYTHON_IMAGE=python:3.13-slim-trixie

# ---------- Tahap 1: build venv (Rust + maturin + uv) ----------
FROM ${PYTHON_IMAGE} AS build

# gcc dan libc6-dev dibutuhkan linker Rust; curl untuk installer rustup.
RUN apt-get update \
  && apt-get install -y --no-install-recommends gcc libc6-dev curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# uv dari image resmi Astral (samakan minor dengan `uv --version` di laptop).
COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /usr/local/bin/uv

# Rust: rustup memasang toolchain sesuai rust-toolchain.toml (satu sumber versi).
ENV RUSTUP_HOME=/opt/rustup CARGO_HOME=/opt/cargo PATH=/opt/cargo/bin:$PATH
WORKDIR /app
COPY rust-toolchain.toml ./
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
  | sh -s -- -y --profile minimal --default-toolchain none \
  && rustup toolchain install

# Konfigurasi uv untuk container:
# - hanya pakai Python sistem image (bukan unduhan uv), supaya cocok dengan runtime
# - salin file (bukan hardlink) karena cache ada di mount terpisah
# - kompilasi .pyc saat build agar start worker cepat
ENV UV_PYTHON_DOWNLOADS=never \
  UV_PYTHON_PREFERENCE=only-system \
  UV_LINK_MODE=copy \
  UV_COMPILE_BYTECODE=1

# Layer dependensi pihak ketiga (numpy, psycopg, jsonschema). Hanya manifest
# yang disalin, jadi layer ini tidak dibangun ulang saat kode berubah.
COPY pyproject.toml uv.lock ./
COPY packages/python/lab-stats/pyproject.toml packages/python/lab-stats/
COPY packages/python/lab-worker/pyproject.toml packages/python/lab-worker/
COPY packages/rust/lab-numerics-py/pyproject.toml packages/rust/lab-numerics-py/
COPY services/hello/worker/pyproject.toml services/hello/worker/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev --no-install-workspace --package hello-worker

# Layer kode: Rust (workspace Cargo) + paket Python workspace.
COPY Cargo.toml Cargo.lock ./
COPY .cargo ./.cargo
COPY packages/rust ./packages/rust
COPY packages/python ./packages/python
COPY services/hello/worker ./services/hello/worker

# --no-editable: anggota workspace dipasang sebagai wheel sungguhan (bukan
# tautan ke source), jadi .venv berdiri sendiri. maturin membangun wheel
# lab-numerics dalam mode release.
RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=cache,target=/opt/cargo/registry \
  --mount=type=cache,target=/app/target \
  uv sync --frozen --no-dev --no-editable --package hello-worker

# ---------- Tahap 2: runtime ----------
FROM ${PYTHON_IMAGE}
RUN groupadd --system app && useradd --system --gid app --no-create-home app
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
# Skema payload dibaca dari disk oleh lab_worker (Go meng-embed-nya).
COPY contracts/jobs /app/contracts/jobs
ENV PATH=/app/.venv/bin:$PATH \
  LAB_CONTRACTS_DIR=/app/contracts/jobs \
  PYTHONUNBUFFERED=1
USER app
CMD ["python", "-m", "hello_worker"]
