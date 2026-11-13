# PROGRESS — Applied Math Lab

Log handoff antar-thread. Satu entri per sub-milestone, ditambahkan saat thread ditutup (≤ 150 kata per entri). Sumber utama: file ini di repo; salinannya di Project knowledge diperbarui pada penutupan thread.

## ✅ [L0.1] Lingkungan dev — 2026-10-30

- Selesai: WSL2 Ubuntu 26.04 + systemd; Rust 1.99 (clippy, rustfmt, wasm32); Go 1.27 + gopls + dlv; uv + Python 3.13; fnm + Node 26 LTS + pnpm; Docker Engine 29.9 + Compose v5 (sudah ada); Zed (Windows) remote WSL, LSP 4 bahasa terverifikasi.
- Keputusan: Docker Engine di WSL, bukan Desktop. Python 3.13, uv only-managed. Toolchain via installer user-level, bukan apt. PATH Windows diputus; hanya bin Zed ditambahkan. Debugger bawaan Zed (Delve, CodeLLDB) cukup → Keputusan Terbuka nomor 13 ditutup.
- File yang berubah: ~/.bashrc (blok applied-math-lab), /etc/wsl.conf, C:\Users\<user>\.wslconfig, settings Zed.
- Pertanyaan terbuka: log driver Docker di VPS (json-file vs local) → L0.8.
- Berikutnya: L0.2 Monorepo.
- Jam: estimasi 4 / aktual ~1,25

## ✅ [L0.2] Monorepo — 2026-10-30

- Selesai: repo `~/code/applied-math-lab`, commit pertama `69bbcb5`. Workspace Cargo (`lab-numerics`), uv (`lab_stats`), satu modul Go (`packages/go/buildinfo`), pnpm (prettier 3.9.10 exact). Lint: clippy `-D warnings`, ruff + mypy strict, golangci-lint v2.15.0, prettier. `justfile` (`setup`/`fmt`/`lint`/`test`/`check`); `just check` hijau, uji negatif terbukti gagal.
- Keputusan: LAB-ADR-008. Monorepo (Terbuka #1 ditutup); satu Go binary per proyek (Terbuka #2 ditutup); satu `go.mod` root `github.com/Adrianus-Bagas/applied-math-lab` + direktif `ignore`, bukan `go.work`; `just`; semua toolchain dipin. `PROJECT_CONTEXT` direvisi ke v1.1 (§2.3, §2.5, §3, §9, §10).
- File yang berubah: file root (manifest, lockfile, pin versi, config lint), `packages/*`, `README.md`, `docs/decisions/LAB-ADR-008-monorepo-dan-tooling.md`.
- Pertanyaan terbuka: pin golangci-lint v2.15.0 di CI (L0.7); just-lsp Zed gagal unduh aset (non-blokir); remote GitHub + SSH → L0.7.
- Berikutnya: L0.3 Jembatan Rust → Python.
- Jam: estimasi 5 / aktual ~1

## ✅ [L0.3] Jembatan Rust → Python — 2026-10-30

- Selesai: `lab-numerics::stats` (Welford; test hitung tangan, offset 1e12, kasus tepi). Crate binding `lab-numerics-py` (PyO3 0.30.1 abi3-py313, rust-numpy 0.30, maturin) → `import lab_numerics`. Oracle pytest vs NumPy dengan toleransi dari bound galat (c·n·ε·‖x‖₂·√M₂) + Hypothesis; list vs ndarray identik bit. `just check` hijau (15 test Python). Timing 10⁷ elemen (release): ndarray 70 ms, list 236 ms, NumPy 42 ms.
- Keputusan: LAB-ADR-009 (core murni + binding `-py`; tanpa `extension-module`; `PYO3_PYTHON` → `.venv`; `just py-ext` sebelum pytest; `PyArrayLike1` + `py.detach`). `PROJECT_CONTEXT` v1.2.
- File yang berubah: `Cargo.toml`, `.cargo/config.toml`, `pyproject.toml`, `uv.lock`, `justfile`, `.gitignore`, `packages/rust/lab-numerics/src/{lib,stats}.rs`, `packages/rust/lab-numerics-py/*`, `docs/decisions/LAB-ADR-009-jembatan-rust-python.md`.
- Pertanyaan terbuka: CI wajib `uv sync` sebelum clippy (L0.7); wheel release di image (L0.6); Welford per-chunk + merge Chan untuk SIMD (opsional, L0.9).
- Berikutnya: L0.4 Antrean job.
- Jam: estimasi 5 / aktual ~1,5

## ✅ [L0.4] Antrean job — 2026-10-31

- Selesai: Postgres 18 dev (`just db-up`). Tabel `lab_jobs` + migrasi goose embedded. Go `jobqueue` (`Enqueue` dalam `pgx.Tx`, validasi JSON Schema, NOTIFY) + `jobqueuectl` (`just jobq`); 5 test testcontainers. Python `lab_worker`: klaim `SKIP LOCKED`, fencing `attempts`, heartbeat/reaper, watchdog timeout, backoff equal jitter (latihan), loop LISTEN + polling; test klaim konkuren 4×50. `services/hello/worker` (`lab.stats.summary` → Rust): end-to-end lulus, hasil identik bit untuk seed sama.
- Keputusan: LAB-ADR-010; Terbuka #3 (JSON Schema) dan #4 (implementasi sendiri) ditutup; seed dibatasi 2⁵³−1. `PROJECT_CONTEXT` v1.3.
- File yang berubah: `infrastructure/compose.dev.yaml`, `.env.example`, `justfile`, `pyproject.toml`, `go.mod`, `contracts/*`, `packages/go/jobqueue/*`, `packages/python/lab-worker/*`, `services/hello/worker/*`, `docs/decisions/LAB-ADR-010-antrean-job.md`.
- Pertanyaan terbuka: slot job berat lintas DB (Terbuka #10, L0.6/L0.8); `stop_grace_period` worker (L0.6); Docker di runner CI (L0.7).
- Berikutnya: L0.5 Portal + Go API hello + SSE.
- Jam: estimasi 6 / aktual ~4

## ✅ [L0.5] Portal + Go API hello + SSE — 2026-11-01

- Selesai: `services/hello/api` (`net/http` + `ServeMux`, pola `run`, graceful shutdown, `/healthz` liveness, `/readyz` ping DB); `POST /api/hello/jobs` (Enqueue dalam `pgx.BeginFunc`; 400/413/422) dan `GET /api/hello/jobs/{id}`; SSE `/events` (hub satu koneksi LISTEN, snapshot, ping + polling 15 s, deadline per write). Migrasi `jobqueue` `00002`: trigger NOTIFY `lab_job_progress` saat status/progres berubah (`pg_notify` Python dihapus). `apps/web`: rewrite `/api/hello` → :8080 (`compress: false`, terbukti tanpa buffering), `useJobEvents`, `HelloApiError`, `progressStage`, halaman `/` dan `/hello`; vitest. Test testcontainers API + SSE; `just check` hijau (4 bahasa).
- Keputusan: LAB-ADR-011; OpenAPI ditunda ke API domain pertama. `PROJECT_CONTEXT` v1.5.
- File yang berubah: `services/hello/api/*`, `packages/go/jobqueue/{migrations/00002_*,*.go}`, `lab_worker/queue.py`, `apps/web/*`, `justfile`, `pnpm-workspace.yaml`, `.prettierignore`, `docs/decisions/LAB-ADR-011-api-hello-dan-sse.md`.
- Pertanyaan terbuka: build standalone Next.js + `HELLO_API_URL` (L0.6); Caddy meneruskan SSE tanpa buffer (L0.8).
- Berikutnya: L0.6 Docker multi-stage + Compose.
- Jam: estimasi 4 / aktual ~4,5

## ✅ [L0.6] Docker multi-stage + Compose — 2026-11-01

- Selesai: `.dockerignore` (konteks root). Image `hello-api` (golang → distroless static nonroot, + `jobqueuectl`, subperintah `healthcheck` + test), `hello-worker` (python slim + rustup + uv; `uv sync --no-editable` membangun wheel release maturin; runtime hanya `.venv` + `contracts/jobs`), `web` (Next standalone, pnpm via npm). `infrastructure/compose.yaml`: postgres, `migrate` sekali jalan, api, worker (`init`, grace 30 s), web, Caddy :8000; batas §4.2, rotasi log; resep `stack-*`. Rewrite Next hanya di dev. Terverifikasi: E2E `/hello` via Caddy, SSE tanpa buffer/kompresi, SIGKILL worker → restart + reaper (`attempts`=2), `just check` hijau.
- Keputusan: LAB-ADR-012; Terbuka #10 ditunda ke L0.8. `PROJECT_CONTEXT` v1.6 (+ tanda ✅/⏳ di §7).
- File yang berubah: `.dockerignore`, `services/hello/{api,worker}/Dockerfile`, `services/hello/api/{healthcheck.go,healthcheck_test.go,main.go}`, `apps/web/{Dockerfile,next.config.ts}`, `infrastructure/{compose.yaml,Caddyfile.local}`, `justfile`, `docs/decisions/LAB-ADR-012-docker-dan-compose-lokal.md`, `PROJECT_CONTEXT.md`.
- Pertanyaan terbuka: pin tag `uv`/`caddy` ke patch + build-arg `VERSION` di CI (L0.7); Caddy TLS + SSE di VPS, slot job berat (L0.8).
- Berikutnya: L0.7 CI GitHub Actions.
- Jam: estimasi 5 / aktual ~1

## ✅ [L0.7] CI GitHub Actions — 2026-11-01

- Selesai: repo GitHub publik + SSH. `justfile` dipecah (`setup-py/-node`, `ci-*`; `check` kini mencakup web, mypy worker). `ci.yml`: path filter → matrix dinamis `just ci-<bahasa>` → image GHCR (push dari `main`, tag `sha-<7>` + `main`, cache gha) → gerbang `ci-ok`. Action dipin SHA (pinact) + Dependabot; ruleset `main`; package publik. Uji negatif dan uji filter lulus. Bug L0.6 ditemukan: `buildinfo` tak diimpor → `-X` diabaikan diam-diam; kini `hello-api version`, test `-X`, smoke test CI (`sha-9ae2e69` terverifikasi). `typecheck` web = `next typegen && tsc`.
- Keputusan: LAB-ADR-013; kerja per branch → PR → squash merge. `PROJECT_CONTEXT` v1.7.
- File yang berubah: `justfile`, `.github/{workflows/ci.yml,dependabot.yml}`, `apps/web/package.json`, `services/hello/api/{main,version,version_test}.go`, `docs/decisions/LAB-ADR-013-ci-github-actions.md`, `PROJECT_CONTEXT.md`.
- Pertanyaan terbuka: compose VPS dengan tag `sha-…`, log driver, slot job berat (L0.8); Dependabot ekosistem lain; deprecation `testcontainers.postgres`.
- Berikutnya: L0.8 VPS.
- Jam: estimasi 4 / aktual ~2,25

## ✅ [L0.8] VPS — 2026-11-02

- Selesai: Hostinger Ubuntu 24.04: user `adrianus`, SSH kunci saja tanpa root, UFW + firewall hPanel, unattended-upgrades + reboot 03:00 WIB, swap 2 GB, Docker 29.9 (`local` log, live-restore). `https://applied-math-lab.portfolio-bagas.tech` (A + CAA). `compose.vps.yaml` (image GHCR) + Caddyfile TLS/HSTS/readyz. User `deploy` + forced command `lab-deploy` (SHA wajib di riwayat `main`). CI `retag` + `deploy` (env `production`); deploy otomatis `sha-5ba8517` hijau setelah bug trap `local` diperbaiki. Terverifikasi: SSE via TLS, reboot, port 5432/8080 tertutup, slice, UptimeRobot (`readyz` 503 → alert, portal tetap hijau).
- Keputusan: LAB-ADR-014; Terbuka #10 ditutup (cgroup `lab-workers.slice`, `CPUQuota=100%`); monitor eksternal, metrik → MO-25. `PROJECT_CONTEXT` v1.8.
- File yang berubah: `.github/workflows/ci.yml`, `infrastructure/{compose.vps.yaml,Caddyfile,.env.vps.example}`, `infrastructure/vps/{lab-deploy.sh,lab-workers.slice}`, `docs/decisions/LAB-ADR-014-vps-dan-deploy.md`, `PROJECT_CONTEXT.md`.
- Pertanyaan terbuka: AAAA/IPv6; HSTS → 1 tahun; shellcheck di CI; backup `pg_dump` (MO-25); pin digest `caddy`/`postgres`.
- Berikutnya: L0.9 Latihan Rust.
- Jam: estimasi 6 / aktual ~4,5

## ✅ [L0.9a] Latihan Rust, sesi 1–5 — 2026-11-10

- Selesai: modul baru `lab-numerics`: `poly` (Horner, nilai + turunan satu lintasan), `roots` (`bisection`, `newton`, `RootError` + `Display`), `quad` (trait `Quadrature`, `Trapezoid`, `Simpson`, `richardson`, `empirical_order`), `rational` (`gcd`, bentuk kanonik, operator lewat i128). `stats::Moments`: `merge`/`merged` (Chan), field privat. Teori ⭐: Horner, merge Chan, konvergensi linear vs kuadratik, orde galat + Richardson. Perbaikan `lab-deploy`: verifikasi kini membandingkan ID image per tag untuk tiga layanan; versi tertanam hanya dicatat, karena image hasil `retag` membawa SHA build lama (deploy `sha-bdc79ef` sempat gagal palsu).
- Keputusan: L0.9 dipecah a/b (§6.5). Penurunan matematika di Mode Latihan dituntun lengkap; kode tetap ditulis pengguna. `PROJECT_CONTEXT` v1.9.
- File yang berubah: `packages/rust/lab-numerics/src/{lib,poly,stats,roots,quad,rational}.rs`, `infrastructure/vps/lab-deploy.sh`, `PROJECT_CONTEXT.md`.
- Pertanyaan terbuka: estimasi Mode Latihan ~2× terlalu rendah → kalibrasi ulang setelah L0.10; kalimat "verifikasi versi" di LAB-ADR-014 dan `PROJECT_CONTEXT` belum disesuaikan (L0.9b); `-i64::MIN` di `Rational`.
- Berikutnya: L0.9b Iterator (pecahan berlanjut √2).
- Jam: estimasi 9 / aktual ~20

## ✅ [L0.9b] Iterator (pecahan berlanjut √2) — 2026-11-10

- Selesai: modul `lab-numerics::cfrac`: iterator generik `Convergents<I>` (rekurensi konvergen; berhenti saat input habis atau overflow i64 lewat `checked_mul`/`checked_add`; `FusedIterator`), `sqrt2_quotients`, `sqrt2_convergents`, `sqrt2_approx` (`find`). 8 test: konvergen √2, 415/93, rasio emas → Fibonacci, identitas Pell, FPB = 1, galat < 1/q², berhenti tepat di 50 konvergen (cocok dengan estimasi ln). Teori ⭐: rekurensi lewat matriks, determinan ±1, identitas Pell.
- Keputusan: `-i64::MIN` di `Rational` ditutup tanpa kode baru: `from_i128` menormalkan tanda di i128 dan panic bila hasil tidak muat di i64. Kalimat "verifikasi versi" diganti "verifikasi ID image". `PROJECT_CONTEXT` v1.10.
- File yang berubah: `packages/rust/lab-numerics/src/{lib,cfrac}.rs`, `docs/decisions/LAB-ADR-014-vps-dan-deploy.md`, `PROJECT_CONTEXT.md`.
- Pertanyaan terbuka: kalibrasi estimasi Mode Latihan setelah L0.10.
- Berikutnya: L0.10 Latihan Python numerik.
- Jam: estimasi 1 / aktual ~1

## ✅ [L0.10] Latihan Python numerik — 2026-11-11

- Selesai: modul baru `lab_stats`: `floats` (`machine_epsilon`, `ulp`, `quadratic_roots` stabil), `summation` (`kahan_sum`, `pairwise_sum`), `distance` (`pairwise_dist` broadcasting, `pairwise_dist_gram`), `tolerance` (`is_close`), `quadrature` (`trapezoid`, `simpson` tervektorisasi; oracle `scipy.integrate.quad`). Teori ⭐: model galat pembulatan, pembatalan, bound penjumlahan (naif/pairwise/Kahan), broadcasting, bilangan kondisi, galat pemotongan vs pembulatan. Timing 1000×1000 jarak: loop 0,71 s, broadcasting 0,042 s, Gram 0,011 s. `just check` hijau.
- Keputusan: toleransi tes selalu eksplisit dan diturunkan dari bound, tidak dari hasil; jarak memakai broadcasting (Gram rawan pembatalan, perlu pemusatan); SciPy + `scipy-stubs` dependensi dev (oracle saja). `PROJECT_CONTEXT` v1.11.
- File yang berubah: `packages/python/lab-stats/src/lab_stats/{floats,summation,distance,tolerance,quadrature}.py`, `packages/python/lab-stats/tests/test_*.py`, `pyproject.toml`, `uv.lock`, `PROJECT_CONTEXT.md`.
- Pertanyaan terbuka: penurunan toleransi dari bilangan kondisi masih perlu diulang (latihan lagi di MO-3.3 dan D3.1); Mode Latihan sejauh ini 27 jam dari estimasi 16 (~1,7×), kalibrasi ulang setelah MO-1.
- Berikutnya: L0.11 Template ADR, `PROGRESS.md`, demo Rust → WASM.
- Jam: estimasi 6 / aktual ~6

## ✅ [L0.11] Template ADR, PROGRESS.md, demo Rust → WASM — 2026-11-11

- Selesai: `docs/decisions/TEMPLATE.md` + `README.md` (indeks); LAB-ADR-010 yang tertinggal sejak L0.4 ikut di-commit; `PROGRESS.md` masuk repo. Crate `lab-numerics-wasm` (`sqrt2Convergents` → `BigInt64Array`, `meanVariance`), profil `wasm-release`, resep `wasm`/`wasm-tools`. Portal: pembungkus `lab-numerics.ts`, test vitest (Pell eksak, WASM vs JS), halaman `/wasm-demo`. Image `web` mendapat tahap Rust; `check (web)` memasang Rust + CLI; smoke test deploy mencakup `/wasm-demo`. `just check`, stack lokal, dan CI PR hijau.
- Keputusan: LAB-ADR-015 (crate binding `-wasm`; `wasm-bindgen-cli` tanpa wasm-pack, dipin `=0.2.130`; `.wasm` di `public/`, di luar bundler). `docs/PROGRESS.md` di repo menjadi sumber utama. `PROJECT_CONTEXT` v1.12; L0 selesai.
- File yang berubah: `Cargo.{toml,lock}`, `justfile`, `packages/rust/lab-numerics-wasm/*`, `apps/web/{Dockerfile,eslint.config.mjs,app/page.tsx,app/wasm-demo/page.tsx,src/lib/lab-numerics*.ts}`, `.github/workflows/ci.yml`, file abaikan, `docs/decisions/{TEMPLATE,README,LAB-ADR-010-*,LAB-ADR-015-*}.md`, `docs/PROGRESS.md`, `README.md`, `PROJECT_CONTEXT.md`.
- Pertanyaan terbuka: brotli/`wasm-opt` dan Web Worker (D6.1); DNS build Docker di WSL sempat gagal (`EAI_AGAIN`).
- Berikutnya: MO-1.1 Skenario, satuan, semantik waktu, asumsi.
- Jam: estimasi 4 / aktual ~3

## ✅ [MO-1.1] Skenario, satuan, semantik waktu, asumsi — 2026-11-12

- Selesai: `docs/mathematics/mealops/model.md` §1. Jam kejadian di rute (`A_j = T_i + s_i + τ_ij`, `T_j = max(A_j, a_j)`, `W_j`), bukti batas mulai layanan setara batas tiba, jam berangkat paling lambat (mundur dari deadline). Holding `h_j = m − f_b`, dekomposisi teleskopik, jendela `f_b` dari dua sisi. Contoh hitung tangan untuk keduanya.
- Keputusan: waktu menit bulat sejak 00:00, durasi turunan dibulatkan ke atas saat instans dibuat; satu hari operasi `[0, 1440)`; `d_j` membatasi `T_j` (Solomon); notasi §8.1 v3.1 kanonik, tambahan `A_j`, `W_j`; asumsi baru `δ ≥ s_j` dan ketaksamaan segitiga `τ`, ditolak saat validasi instans. `PROJECT_CONTEXT` v1.13.
- File yang berubah: `docs/mathematics/mealops/model.md`, `docs/PROGRESS.md`, `PROJECT_CONTEXT.md`.
- Pertanyaan terbuka: rumus umum holding minimum (MO-1.5); trip yang membawa lebih dari satu batch (MO-1.5); penskalaan instans Solomon ke bilangan bulat (MO-2.3).
- Berikutnya: MO-1.2 Model A CVRPTW.
- Jam: estimasi 4 / aktual ~3

## ✅ [MO-1.2] Model A CVRPTW — 2026-11-13

- Selesai: `model.md` §2. Graf dengan dua salinan dapur (`n(n+1)` arc), formulasi dua-indeks F0–F8 (`x_ij`, `T_j`, `u_j`), penurunan Big-M terkecil (`M = Q`; `M_ij = max{0, d'_i + s_i + τ_ij − a'_j}`), bukti subtour hilang (kapasitas, waktu), kesetaraan F4–F7 dengan pemeriksaan rute lewat jadwal tercepat `T*`, praproses arc mustahil. Contoh n = 4 diverifikasi enumerasi (8 solusi layak, optimum 25).
- Keputusan: `q_j` bulat ≥ 1 (§1.7); jam dapur `[e_0, l_0]` dilebur ke jendela efektif `a'_j`, `d'_j` (bersandar pada B6); eliminasi subtour bersandar pada kapasitas; objektif Model A = total jarak. `PROJECT_CONTEXT` v1.14.
- File yang berubah: `docs/mathematics/mealops/model.md`, `docs/PROGRESS.md`, `PROJECT_CONTEXT.md`.
- Pertanyaan terbuka: objektif hierarkis Solomon (kendaraan dulu, lalu jarak) → MO-2.3/MO-6.3; indeks pada jadwal tercepat (`T_i`, bukan `A_i`) dan uji arc (deadline node tujuan) perlu latihan ulang di MO-1.3.
- Berikutnya: MO-1.3 Contoh hitung tangan feasible + infeasible.
- Jam: estimasi 6 / aktual ~4
