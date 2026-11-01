set dotenv-load
# Applied Math Lab: perintah lintas bahasa.
# Jalankan `just` tanpa argumen untuk melihat daftar resep.

set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

# ---------- setup ----------

# Pasang dependensi Python dan Node persis sesuai lockfile
setup:
    uv sync --all-packages --locked
    pnpm install --frozen-lockfile

# ---------- format (mengubah file) ----------

# Rapikan format semua bahasa
fmt: fmt-rust fmt-go fmt-py fmt-misc

fmt-rust:
    cargo fmt --all

fmt-go:
    golangci-lint fmt ./...

fmt-py:
    uv run ruff format
    uv run ruff check --select I --fix

fmt-misc:
    pnpm format

# ---------- lint (read-only, dipakai CI) ----------

# Periksa format dan lint semua bahasa tanpa mengubah file
lint: lint-rust lint-go lint-py lint-misc

lint-rust:
    cargo fmt --all --check
    cargo clippy --workspace --all-targets -- -D warnings

lint-go:
    go vet ./...
    golangci-lint run ./...

lint-py:
    uv run ruff format --check
    uv run ruff check
    uv run mypy packages/python/*/src packages/rust/*/python

lint-misc:
    pnpm format:check

# ---------- test ----------
# Bangun ulang extension module PyO3 ke .venv (debug, inkremental)
py-ext:
    uv run maturin develop --uv -m packages/rust/lab-numerics-py/Cargo.toml

# Jalankan semua test
test: test-rust test-go test-py

test-rust:
    cargo test --workspace

test-go:
    go test -race -timeout 3m ./...

test-py: py-ext
    uv run pytest

# ---------- gabungan ----------

# Semua pemeriksaan yang juga dijalankan CI
check: lint test

compose_dev := "docker compose -f infrastructure/compose.dev.yaml"

# Nyalakan Postgres dev dan tunggu sampai sehat
db-up:
    {{ compose_dev }} up -d --wait

# Matikan Postgres dev (data tetap ada di volume)
db-down:
    {{ compose_dev }} down

# Hapus total, termasuk data
db-reset:
    {{ compose_dev }} down -v

# Shell psql ke DB dev
db-psql:
    {{ compose_dev }} exec postgres psql -U lab -d lab_dev

# Alat dev antrean: just jobq <migrate|status|enqueue ...|show ...>
[positional-arguments]
jobq *args:
    go run ./packages/go/jobqueue/cmd/jobqueuectl "$@"

# Jalankan worker hello (Ctrl+C untuk berhenti rapi)
worker-hello:
    uv run python -m hello_worker

# Jalankan hello-api di :8080 (butuh `just db-up`)
api-hello:
    go run ./services/hello/api

# Jalankan lab portal di :3000 (rewrite /api/hello → hello-api :8080)
dev-web:
    pnpm --filter web dev

lint-web:
    pnpm --filter web lint
    pnpm --filter web typecheck

test-web:
    pnpm --filter web test
