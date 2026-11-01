# LAB-ADR-012: Image Docker multi-stage dan Compose lokal semua lapisan

- **Status:** Diterima
- **Tanggal:** 2026-11-01
- **Sub-milestone:** L0.6
- **Terkait:** LAB-ADR-008 (monorepo), LAB-ADR-009 (jembatan Rust → Python), LAB-ADR-010 (antrean job), LAB-ADR-011 (Go API, SSE, portal)

## Konteks

Walking skeleton "hello" (Go API, Python worker + Rust, portal Next.js, PostgreSQL) sudah berjalan di dev lewat `just api-hello`, `just worker-hello`, dan `just dev-web`. Sebelum CI (L0.7) dan deploy ke VPS (L0.8), setiap lapisan perlu dibungkus menjadi image yang kecil, reprodusibel, dan tidak membawa toolchain build. Semuanya juga perlu bisa dijalankan bersama dengan satu perintah.

Kendala yang memengaruhi desain:

1. VPS hanya 2 vCPU / 8 GB. Image harus kecil (pull cepat, disk hemat) dan build tidak boleh terjadi di VPS (§4.4).
2. Monorepo dengan satu `go.mod`, satu workspace Cargo, satu workspace uv, dan satu workspace pnpm (LAB-ADR-008). Konteks build harus root repo.
3. Ekstensi Rust dibangun maturin sebagai build backend uv (LAB-ADR-009). Image worker tidak boleh memakai `.so` hasil `maturin develop` di laptop.
4. Next.js membekukan `rewrites` saat `next build`, sehingga `HELLO_API_URL` tidak bisa diatur saat container berjalan (pertanyaan terbuka L0.5).
5. Image distroless tidak punya shell maupun `curl` untuk `HEALTHCHECK`.

## Keputusan

### Umum

- **Konteks build = root repo** untuk semua image. `.dockerignore` mengecualikan `.git`, `node_modules`, `.next`, `target`, `.venv`, cache tiap bahasa, `**/*.so`, `.env*` (kecuali `.env.example`), `datasets`, dan `experiments`.
- **Dockerfile di samping kodenya:** `services/hello/api/Dockerfile`, `services/hello/worker/Dockerfile`, `apps/web/Dockerfile`.
- **BuildKit cache mount** (`--mount=type=cache`) untuk modul Go, cache compile Go, cache uv, registry Cargo, `target/` Rust, dan store pnpm. Manifest disalin sebelum kode supaya layer dependensi hanya dibangun ulang bila manifest berubah.
- **Semua runtime berjalan sebagai user non-root.**

### Go API (`hello-api`)

- `golang:1.27-trixie` → `gcr.io/distroless/static-debian13:nonroot`.
- `CGO_ENABLED=0`, `-trimpath`, `-buildvcs=false` (`.git` tidak ada di konteks), `-ldflags "-s -w -X …/buildinfo.Version=${VERSION}"` (`ARG VERSION=dev`, diisi CI).
- Image membawa **dua binary**: `hello-api` dan `jobqueuectl`.
- **Subperintah `hello-api healthcheck`**: binary memanggil `/healthz` miliknya sendiri lewat loopback (timeout 2 s), exit 0/1. Dipakai `HEALTHCHECK` Docker karena distroless tidak punya `curl`. Diuji dengan `httptest`.

### Worker (`hello-worker`)

- Tahap build dan runtime memakai **image Python yang sama** (`python:3.13-slim-trixie`), karena venv menyimpan symlink ke `/usr/local/bin/python3.13`.
- Tahap build: gcc + libc6-dev, uv dari `ghcr.io/astral-sh/uv`, rustup dengan toolchain dari `rust-toolchain.toml` (satu sumber versi). `UV_PYTHON_DOWNLOADS=never`, `UV_PYTHON_PREFERENCE=only-system`, `UV_LINK_MODE=copy`, `UV_COMPILE_BYTECODE=1`.
- Dua tahap `uv sync`: (1) `--no-install-workspace` dengan hanya manifest anggota workspace → layer dependensi pihak ketiga; (2) `--no-editable --package hello-worker` setelah kode disalin → anggota workspace dipasang sebagai **wheel sungguhan**, termasuk wheel `lab-numerics` yang dibangun maturin dalam mode release.
- Runtime hanya menerima `.venv` dan `contracts/jobs` (`LAB_CONTRACTS_DIR=/app/contracts/jobs`, karena Python membaca skema dari disk sedangkan Go meng-embed-nya). Tanpa Rust, gcc, maupun uv. `psycopg[binary]` membawa libpq sendiri, jadi tidak perlu paket apt.

### Portal (`web`)

- `node:26-trixie-slim`, tiga tahap (deps → build → runtime). pnpm dipasang dengan `npm install -g pnpm@<packageManager>` karena Node ≥ 25 tidak lagi membawa corepack.
- `output: "standalone"` dengan `outputFileTracingRoot` = root monorepo; runtime menjalankan `node apps/web/server.js` dengan `HOSTNAME=0.0.0.0`. `.next/static` dan `public/` disalin manual.
- **Rewrite `/api/hello/*` hanya aktif saat `NODE_ENV=development`.** Di build produksi `rewrites()` mengembalikan `[]`.

### Compose lokal (`infrastructure/compose.yaml`, proyek `lab-local`)

- Service: `postgres` (18, database `lab_hello`, tidak di-publish ke host), `migrate` (sekali jalan: `jobqueuectl migrate`), `hello-api`, `hello-worker`, `web`, `caddy`.
- Urutan: `postgres` healthy → `migrate` `service_completed_successfully` → `hello-api` dan `hello-worker`; `caddy` menunggu `hello-api` healthy.
- `migrate` juga memiliki blok `build` yang sama dengan `hello-api`, supaya Compose tidak mencoba pull image lokal dari registry.
- Worker: `init: true` (tini sebagai PID 1), `stop_grace_period: 30s`, `restart: unless-stopped` (wajib untuk worker crash-only, LAB-ADR-010).
- Batas `cpus`/`mem_limit` mengikuti §4.2; `GOMEMLIMIT=100MiB` untuk API. Log `json-file` dengan rotasi 10 MB × 3.
- **Caddy memegang routing `/api` di container** (`infrastructure/Caddyfile.local`, `127.0.0.1:8000`, tanpa TLS): `/api/hello/*` → `hello-api:8080` dengan `flush_interval -1` dan tanpa `encode`; sisanya → `web:3000` dengan `encode zstd gzip`. Topologinya sama dengan VPS (§2.2).
- Resep `just stack-up`, `stack-down`, `stack-ps`, `stack-logs`.

### Ditunda

- **Keputusan Terbuka #10 (slot job berat lintas database)** ditunda ke L0.8. Di lokal baru ada satu proyek, sehingga konfliknya belum bisa diuji.

## Alternatif yang ditolak

- **Rewrite Next.js di produksi dengan URL dari env runtime.** Tidak bisa, karena nilai rewrite dibekukan saat build. Membangun image web per lingkungan juga melanggar prinsip "satu image, banyak lingkungan".
- **`wget`/`curl` di image API untuk healthcheck.** Membutuhkan base image dengan shell (mis. alpine), sehingga permukaan serangan dan ukuran image bertambah.
- **Build wheel dengan `maturin build` lalu `pip install` di runtime.** Butuh pip/uv di runtime dan langkah tambahan. `uv sync --no-editable` sudah menghasilkan venv yang berdiri sendiri dari lockfile yang sama.
- **Base image `rust:*` untuk build worker.** Python Debian (`/usr/bin/python3.13`) tidak sama dengan Python image `python:*-slim` (`/usr/local/bin/python3.13`), sehingga venv rusak saat disalin.
- **Migrasi dijalankan oleh `hello-api` saat start.** Bila API diskalakan atau di-restart berulang, migrasi ikut berjalan berulang. Service sekali jalan membuat urutan eksplisit dan kegagalan terlihat jelas.

## Konsekuensi

- Image kecil dan tanpa toolchain; build kedua cepat berkat cache mount.
- SSE melewati Caddy tanpa buffering dan tanpa kompresi sudah terverifikasi di lokal. L0.8 tinggal memverifikasi ulang dengan TLS di VPS.
- Pengujian end-to-end lokal kini memakai artefak yang sama dengan yang akan di-deploy.
- Proyek baru menyalin pola ini: Dockerfile API/worker per proyek, service `migrate`, entri routing Caddy `/api/<proyek>/*`, dan rewrite dev di `next.config.ts`.
- Tag image `uv` dan `caddy` sebaiknya dipin ke versi patch saat CI dibuat (L0.7).

## Verifikasi (L0.6)

- `migrate` exit 0, `hello-api` healthy, service lain running.
- `/hello` lewat `http://localhost:8000` menjalankan job end-to-end dengan progres SSE.
- `curl -N` ke endpoint SSE: `text/event-stream` tanpa `content-encoding`, event datang bertahap.
- `SIGKILL` pada worker saat job berjalan → container restart, reaper mengembalikan job, job selesai dengan `attempts = 2`.
- `just check` hijau.
