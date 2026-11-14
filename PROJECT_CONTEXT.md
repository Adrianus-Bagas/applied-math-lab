# PROJECT_CONTEXT — Applied Math Lab

> **Versi dokumen:** 1.15
> **Terakhir diperbarui:** 2026-11-14
> **Status:** Dokumen induk lab. Semua proyek dimulai dari nol dengan arsitektur seragam.
> **Dokumen turunan:** `PROJECT_CONTEXT` MealOps v3.1 (dokumen lama berjudul _MBG v3.1_) tetap menjadi rujukan **model matematis dan algoritma MealOps**; istilah khusus program MBG/SPPG di dalamnya dibaca sebagai istilah umum menurut glosarium §5.1. Bagian yang digantikan oleh dokumen ini dicantumkan di §5.1.

### Perubahan v1.15 (14 Nov 2026, MO-1.3)

- **MO-1.3 selesai:** `docs/mathematics/mealops/model.md` §3 (contoh hitung tangan Model A): instans H5 (`n = 5`) dengan tabel uji arc lengkap, solusi layak beserta semua 9 solusi hasil enumerasi, jebakan hitung tangan, contoh solusi tidak layak, dan empat varian instans tidak layak beserta buktinya.
- **Keputusan MO-1.3** (§5.1): tiga tingkat kegagalan dilaporkan terpisah (input tidak valid, instans tidak layak, solusi tidak layak); H5 dan variannya menjadi fixture MO-2.3; batas bawah jumlah kendaraan dari kapasitas total dan dari kelompok node yang saling tidak bisa serute.
- §3, §5.1, §7.2, §8.3, §10 diperbarui.

### Perubahan v1.14 (13 Nov 2026, MO-1.2)

- **MO-1.2 selesai:** `docs/mathematics/mealops/model.md` §2 (Model A CVRPTW): graf dengan dua salinan dapur, formulasi dua-indeks F0–F8, penurunan Big-M terkecil, bukti eliminasi subtour, kesetaraan formulasi dengan pemeriksaan rute lewat jadwal tercepat, praproses arc mustahil, dan contoh `n = 4` yang diverifikasi dengan enumerasi.
- **Keputusan MO-1.2** (§5.1): `q_j` bilangan bulat ≥ 1 (diperiksa saat validasi instans); jam dapur `[e_0, l_0]` dilebur ke jendela efektif `a'_j`, `d'_j`; eliminasi subtour bersandar pada kapasitas; objektif Model A adalah total jarak; kelayakan rute diperiksa dengan satu lintasan maju.
- Notasi tambahan: `V`, `𝒜` (himpunan arc), `a'_j`, `d'_j`, `T*_j`.
- §3, §5.1, §7.2, §8.3, §10 diperbarui.

### Perubahan v1.13 (12 Nov 2026, MO-1.1)

- **MO-1.1 selesai; MealOps MVP dimulai** (MO-1 bertanda ⏳, §7.2). `docs/mathematics/mealops/model.md` §1 dibuat.
- **Keputusan MO-1.1** (§5.1): waktu dalam menit bulat sejak 00:00 dengan pembulatan ke atas saat instans dibuat; satu hari operasi; `d_j` membatasi mulai layanan `T_j` (setara dengan batas waktu tiba); holding = waktu konsumsi terencana − selesai masak; asumsi baru `δ ≥ s_j` dan ketaksamaan segitiga `τ`, keduanya diperiksa saat validasi instans.
- **Glosarium §5.1 diperluas** (waktu makan, buffer, ompreng, penomoran `M<n>.<k>` → `MO-<n>.<k>`) dan ditambah aturan notasi: glosarium §8.1 MealOps v3.1 adalah notasi kanonik; notasi tambahan (`A_j` tiba, `W_j` tunggu) dicatat di `model.md`.
- MealOps v3.1 kini tersimpan di Project knowledge sebagai `claude/PROJECT_CONTEXT_MEALOPS_v3.1.md`.
- §3, §5.1, §6.5, §7.2, §8.3, §10 diperbarui.

### Perubahan v1.12 (11 Nov 2026, L0.11)

- **L0.11 selesai; L0 Fondasi Lab selesai.**
- **LAB-ADR-015** ditambahkan (§2.3): jalur Rust → WASM. Crate binding `<nama>-wasm`, `cargo build` + `wasm-bindgen-cli` (tanpa wasm-pack) dengan versi dipin di tiga tempat, profil `wasm-release`, glue di `apps/web/src/wasm/` dan biner di `apps/web/public/wasm/` (bundler tidak menyentuh `.wasm`), pembungkus bertipe di `src/lib/`, tahap Rust di image `web`, dan Rust + CLI di job `check (web)`.
- `docs/decisions/` mendapat `TEMPLATE.md` dan `README.md` (indeks); LAB-ADR-010 yang tertinggal sejak L0.4 ikut di-commit.
- **`docs/PROGRESS.md` kini ada di repo dan menjadi sumber utama**; salinan di Project knowledge diperbarui pada penutupan thread (§6.5).
- §2.3, §2.5, §3, §6.5, §7.1, §7.3 (D6.1), §10 diperbarui.

### Perubahan v1.11 (11 Nov 2026, L0.10)

- **L0.10 selesai:** `lab_stats` bertambah modul `floats`, `summation`, `distance`, `tolerance`, `quadrature`.
- **Aturan toleransi tes:** selalu eksplisit dan diturunkan dari bound galat (pembulatan: c·κ·u; pemotongan: orde metode; ditambah galat oracle), tidak pernah dari hasil yang diuji atau bawaan pustaka.
- Matriks jarak memakai broadcasting; rumus Gram hanya setelah koordinat dipusatkan.
- SciPy + `scipy-stubs` menjadi dependensi dev (oracle di tes).
- §2.5, §7.1, §8.3 diperbarui.

### Perubahan v1.10 (10 Nov 2026, L0.9b)

- **L0.9b selesai:** modul `lab-numerics::cfrac` (iterator generik `Convergents<I>`, `FusedIterator`, aritmetika `checked_*`, `sqrt2_convergents`, `sqrt2_approx`).
- **Verifikasi deploy disesuaikan** dengan perbaikan `lab-deploy` di L0.9a: yang dibandingkan adalah ID image per tag untuk setiap layanan; versi tertanam hanya dicatat (§2.3, §3, §4.5, §10, dan LAB-ADR-014).
- `-i64::MIN` di `Rational` ditutup: `from_i128` menormalkan tanda di i128 dan panic bila hasil tidak muat di i64.
- §7.1 dan §8.3 diperbarui.

### Perubahan v1.9 (10 Nov 2026, L0.9a)

- **L0.9 dipecah** menjadi L0.9a (sesi 1–5, selesai) dan L0.9b (iterator), sesuai §6.5: jam aktual ~20 dari estimasi 9.
- **Mode Latihan (§6.2) berubah:** penurunan rumus matematika kini dituntun lengkap langkah demi langkah dan ditutup cek pemahaman singkat; kode tetap ditulis pengguna, dengan kerangka yang memuat sebagian potongan kode dan langkah bernomor.
- `lab-numerics` bertambah modul `poly`, `roots`, `quad`, `rational`; `stats::Moments` mendapat `merge`/`merged` (Chan) dan field privat + getter.
- §6.2, §7.1, §8.3, §10 diperbarui. **Kalibrasi:** sub-milestone Mode Latihan pertama memakan ~2× estimasi.

### Perubahan v1.8 (2 Nov 2026, L0.8)

- **LAB-ADR-014** ditambahkan (§2.3): hardening VPS (user admin, SSH kunci saja, firewall dua lapis UFW + hPanel, update otomatis + reboot 03:00 WIB, swap, Docker resmi dengan log driver `local`), domain `applied-math-lab.portfolio-bagas.tech` dengan TLS Caddy, `infrastructure/compose.vps.yaml` (image GHCR `sha-<7>`), deploy otomatis lewat user `deploy` yang dikunci forced command `lab-deploy` (SHA wajib di riwayat `main`, konfigurasi diunduh dari commit yang sama), job CI `retag` + `deploy` (environment `production`), dan monitor uptime eksternal.
- **Keputusan Terbuka nomor 10 ditutup:** slot job berat = cgroup systemd `lab-workers.slice` (`CPUQuota=100%`) sebagai induk semua container worker; kernel yang memaksakan total worker ≤ 1 vCPU.
- **Terverifikasi:** SSE lewat TLS tanpa buffering, stack pulih sendiri setelah reboot, sertifikat bertahan di volume.
- §2.2, §2.5, §3, §4.2, §4.4, §4.5, §4.6, §7, §8.3, §9, §10 diperbarui. Konfigurasi host yang dipasang manual tinggal di `infrastructure/vps/`.

### Perubahan v1.7 (1 Nov 2026, L0.7)

- **LAB-ADR-013** ditambahkan (§2.3): satu workflow `ci.yml` (`changes` → `check` matrix dinamis → `images` → gerbang `ci-ok`); setiap job memanggil `just ci-<bahasa>` dan gabungannya sama dengan `just check`; path filter dengan anchor (Rust ikut memicu Python); image dibangun setelah check lulus dan di-push ke GHCR hanya dari `main` (tag `sha-<7>` + `main`, `VERSION` via build-arg, package publik); action dipin ke SHA + Dependabot; ruleset `main` (PR wajib, `ci-ok` wajib).
- `justfile`: resep `setup-py`, `setup-node`, `ci-go`, `ci-rust`, `ci-python`, `ci-web`; `check` kini mencakup web dan mypy memeriksa `services/*/worker/src`. Skrip `typecheck` web menjalankan `next typegen` lebih dulu.
- **Bug L0.6 ditemukan dan diperbaiki:** `buildinfo.Version` tidak pernah tersuntik karena paketnya tidak diimpor (linker membuangnya, `-X` diabaikan tanpa error). Kini `hello-api version` + log versi saat start + test `-X` + smoke test image.
- §2.5, §3, §4.5, §6.5, §7, §8.3, §10 diperbarui. **Alur penutupan thread berubah:** branch → PR → squash merge (push langsung ke `main` ditolak).

### Perubahan v1.6 (1 Nov 2026, L0.6)

- **LAB-ADR-012** ditambahkan (§2.3): image Docker multi-stage dengan konteks build root repo (`.dockerignore`), Go → distroless static nonroot (+ `jobqueuectl`, subperintah `healthcheck`), worker Python slim yang membangun wheel release maturin lewat `uv sync --no-editable` (runtime hanya `.venv` + `contracts/jobs`), Next.js standalone; Compose lokal `infrastructure/compose.yaml` (postgres, `migrate` sekali jalan, api, worker, web, Caddy `:8000`); **Caddy memegang routing `/api` di container**, rewrite Next.js hanya di `next dev`.
- §9 Keputusan Terbuka nomor 10 ditunda ke L0.8.
- §2.5, §3, §4.5, §4.6, §10 diperbarui (resep `stack-*`, Dockerfile per layanan, `Caddyfile.local`).
- §7: status sub-milestone ditandai ✅ (selesai) dan ⏳ (sedang dikerjakan).

### Perubahan v1.5 (1 Nov 2026, L0.5)

- **LAB-ADR-011** ditambahkan (§2.3): Go API dengan pustaka standar (`ServeMux` berpola metode, pola `run`, timeout eksplisit, graceful shutdown, `/healthz` liveness tanpa DB, `/readyz` ping DB), enqueue transaksional dari HTTP, SSE berbasis snapshot dengan satu koneksi LISTEN per proses (hub), heartbeat 15 s + polling cadangan, portal Next.js dengan rewrite `/api` di dev (`compress: false`), kontrak TS ditulis tangan (OpenAPI ditunda ke API domain pertama).
- **LAB-ADR-010** diperbarui: NOTIFY `lab_job_progress` kini dikirim oleh trigger `lab_jobs_progress_notify` (migrasi `jobqueue` `00002`) setiap status atau progres berubah.
- §2.5 dan §3 diperbarui (`services/hello/api`, `apps/web`, resep `api-hello`, `dev-web`, `lint-web`, `test-web`).

### Perubahan v1.4 (31 Okt 2026)

- **Proyek pertama digeneralisasi** dari "MBG Operations Optimizer" menjadi **MealOps — optimasi dapur massal dan distribusi makanan perishable**. Model matematis dan algoritmanya tidak berubah; yang berubah adalah framing masalah (§1, §5.1), nama, dan identifier.
- Prefiks milestone `MBG-n` menjadi `MO-n`; direktori `services/mbg` menjadi `services/mealops`; crate `mbg-core` menjadi `mealops-core`; rute portal `/mealops`; `docs/mathematics/mealops/`. Belum ada kode proyek ini di repo, jadi penggantian nama tidak memerlukan migrasi.
- Rujukan `PROJECT_CONTEXT` MBG v3.1 menjadi `PROJECT_CONTEXT` MealOps v3.1, dengan glosarium istilah lama → umum di §5.1.

### Perubahan v1.3 (31 Okt 2026, L0.4)

- **LAB-ADR-010** ditambahkan (§2.3): antrean job implementasi sendiri di PostgreSQL (klaim `SKIP LOCKED` satu perintah, lease + fencing token `attempts`, NOTIFY sebagai petunjuk + polling cadangan, heartbeat/reaper, watchdog timeout, retry dengan backoff equal jitter, worker crash-only) dan kontrak payload JSON Schema 2020-12 per `<kind>.v<N>`.
- §9 Keputusan Terbuka nomor 3 dan 4 ditutup; nomor 10 ditambahkan (slot job berat lintas database).
- §2.5 baris Pengujian, Akses DB, dan Kontrak diperbarui; §3 struktur repo diperbarui (`contracts/`, `packages/go/jobqueue`, `packages/python/lab-worker`, `services/hello/worker`, `infrastructure/compose.dev.yaml`); catatan advisory lock di §4.4.

### Perubahan v1.2 (30 Okt 2026, L0.3)

- **LAB-ADR-009** ditambahkan (§2.3): core Rust murni + crate binding `-py` terpisah (PyO3 abi3, tanpa fitur `extension-module`), layout campuran maturin dengan stub `.pyi`, `PYO3_PYTHON` dipin ke `.venv`, `just py-ext` sebelum pytest, input array tanpa salin lewat rust-numpy, toleransi oracle dari analisis galat.
- **LAB-ADR-007** diperbarui: `py.allow_threads` sekarang bernama `py.detach` (PyO3 ≥ 0.26), plus kontrak mutasi array.
- §3 struktur repo diperbarui (`lab-numerics-py`, `.cargo/config.toml`, konvensi `services/*/core-py`).

### Perubahan v1.1 (30 Okt 2026, L0.2)

- **LAB-ADR-008** ditambahkan (§2.3): monorepo, satu Go binary per proyek, **satu `go.mod` di root** (bukan `go.work`), `just` sebagai task runner, semua toolchain dipin.
- §2.5 baris Workspace dan §3 struktur repo diperbarui sesuai kondisi repo nyata.
- §9 Keputusan Terbuka nomor 1 dan 2 ditutup.

### Perubahan utama (30 Okt 2026)

- Lab berisi tiga proyek: **MBG Operations Optimizer** (sejak v1.4: **MealOps**), **DengueSim** (DBD), dan **Harga Pangan** (nama kerja: PanganWatch).
- **Arsitektur empat lapisan seragam** untuk semua proyek: Next.js → Go → Python → Rust.
- Proyek pertama dimulai ulang. Stack lama (Go sebagai satu-satunya backend, tanpa Python) digantikan.
- Fondasi lab (L0) dibangun sekali dan dipakai ulang oleh ketiga proyek.
- Roadmap baru dengan sub-milestone **≤ 10 jam**, ditambah timeline lab secara keseluruhan.

---

## 1. Visi

Laboratorium portofolio berisi **tiga software** yang intinya adalah implementasi **matematika terapan** (dengan AI sebagai pendukung) untuk masalah nyata di Indonesia. Setiap proyek mewakili **cabang matematika yang berbeda**. Tujuannya ganda: membangun portofolio sekaligus mengulas kembali teori matematika terapan. Karena itu setiap implementasi harus disertai pemahaman konsepnya.

| #   | Proyek                         | Masalah                                                                                                                          | Cabang matematika utama                                            |
| --- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| 1   | **MealOps**                    | Produksi di dapur massal dan distribusi makanan perishable ke banyak titik layanan dengan jendela waktu dan batas waktu konsumsi | Optimasi kombinatorial, metaheuristik, simulasi Monte Carlo        |
| 2   | **DengueSim**                  | Wabah DBD musiman dan efektivitas intervensi                                                                                     | Sistem dinamik (ODE), inferensi Bayesian, kontrol optimal          |
| 3   | **Harga Pangan** (PanganWatch) | Gejolak harga pangan pokok dan kebijakan stok penyangga                                                                          | Proses stokastik, model state-space, pemrograman dinamik stokastik |

**Prinsip bersama:** sistem pendukung keputusan, bukan sistem resmi pemerintah. Asumsi, nilai ilustratif, dan hasil model selalu diberi label yang jelas. Tidak ada klaim melampaui apa yang dibuktikan model.

## 2. Arsitektur Seragam

### 2.1 Stack per lapisan

| Lapisan   | Teknologi                       | Tanggung jawab                                                                                        | Bukan tanggung jawabnya |
| --------- | ------------------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------- |
| Frontend  | **Next.js + TypeScript**        | UI, peta, grafik, simulasi interaktif via WASM                                                        | Logika bisnis           |
| API       | **Go**                          | Auth/RBAC, CRUD, validasi input, orkestrasi job, SSE progres, AI gateway (LLM)                        | Matematika apa pun      |
| Modelling | **Python** (dikelola dengan uv) | Persiapan data, definisi model dan skenario, kalibrasi, validasi, analisis hasil, benchmark, notebook | Loop berat              |
| Komputasi | **Rust**                        | _Hot loop_: solver, sampler, filter, simulasi                                                         | I/O, database, HTTP     |

Aturan praktis: fungsi yang dipanggil jutaan kali dalam satu run masuk ke Rust. Pekerjaan merangkai, menyiapkan, dan menganalisis masuk ke Python. Operasi yang mudah divektorisasi (reduksi, aljabar linear) tetap memakai NumPy; Rust dipakai untuk loop yang tidak bisa divektorisasi (terbukti di L0.3: NumPy mean+var lebih cepat dari Welford Rust).

### 2.2 Topologi

```text
                       Internet (HTTPS :443, HTTP/3)
                                │  applied-math-lab.portfolio-bagas.tech
                       ┌────────▼────────┐
                       │ Caddy           │  TLS otomatis, satu domain lab,
                       └───┬─────────┬───┘  routing per proyek lewat path
                           │         │ /api/<proyek>/*
              ┌────────────▼──┐   ┌──▼──────────────────┐
              │ Next.js       │──►│ Go API (per proyek) │──► API penyedia LLM
              │ lab portal    │   │ auth, CRUD, submit  │
              │ (+ modul WASM)│   └──────────┬──────────┘
              └───────────────┘              │ INSERT job (queued) + NOTIFY
                                  ┌──────────▼──────────┐
                                  │ PostgreSQL          │  data, snapshot,
                                  │ + PostGIS/Timescale │  antrean job
                                  └──────────▲──────────┘
                                             │ FOR UPDATE SKIP LOCKED
                                  ┌──────────┴──────────┐
                                  │ Python worker       │  modelling, validasi,
                                  │  └─ import core     │  analisis
                                  │     (Rust via PyO3) │  komputasi berat
                                  └─────────────────────┘
                                  semua worker di cgroup lab-workers.slice (≤ 1 vCPU gabungan)
```

### 2.3 Prinsip arsitektur (ADR lab)

- **LAB-ADR-001: Empat lapisan seragam.** Pola dipelajari sekali dan dipakai ulang di tiga proyek. Template dibangun di L0. Menggantikan ADR-001 MealOps (Go sebagai satu bahasa backend).
- **LAB-ADR-002: Go tidak memanggil Rust secara langsung.** Tidak ada cgo/FFI. Rust dikompilasi menjadi modul Python lewat **PyO3 + maturin**.
- **LAB-ADR-003: Go ↔ Python hanya lewat antrean job PostgreSQL** (`SKIP LOCKED` + `LISTEN/NOTIFY`), dengan payload JSONB yang divalidasi skema bersama. Menggantikan ADR-003 MealOps (API dan worker dalam satu binary Go). ADR-002 MealOps (Postgres, bukan Redis) tetap berlaku.
- **LAB-ADR-004: Math core murni.** Crate Rust tanpa I/O, deterministik (seed eksplisit, RNG `rand_chacha`), dan bisa diuji tanpa database atau HTTP. Ini setara ADR-004 MealOps, hanya bahasanya yang berubah.
- **LAB-ADR-005: LLM mengusulkan dan menjelaskan; solver dan validator yang memutuskan.** Akses LLM hanya lewat AI gateway di Go. Setiap angka dalam narasi LLM dicek terhadap data sumber.
- **LAB-ADR-006: Satu crate, dua target.** Crate Rust yang sama dapat dikompilasi menjadi modul Python (server) dan WASM (browser) bila perlu. Jalur WASM ditetapkan LAB-ADR-015.
- **LAB-ADR-007: Lepaskan GIL** (`py.detach`, dulu `py.allow_threads`; PyO3 ≥ 0.26) saat Rust menjalankan loop panjang, supaya worker tetap bisa mengirim heartbeat dan progres. Kontrak: array input yang dibaca tanpa salin tidak boleh dimutasi thread lain selama panggilan (dijamin worker concurrency 1).
- **LAB-ADR-008: Monorepo dan tooling lintas bahasa** (L0.2, `docs/decisions/LAB-ADR-008-monorepo-dan-tooling.md`). Satu repositori untuk ketiga proyek; satu Go binary per proyek; **satu modul Go di root** (`github.com/Adrianus-Bagas/applied-math-lab`) dengan direktif `ignore` untuk `node_modules`, bukan multi-modul + `go.work` (yang tidak dianjurkan di-commit dan memaksa `replace` di CI/Docker); workspace Cargo, uv, dan pnpm masing-masing dengan satu lockfile; `just` sebagai task runner (`just check` identik dengan CI); toolchain dipin (`rust-toolchain.toml`, `.python-version`, `.node-version`, direktif `go`, `packageManager` pnpm, prettier versi persis).
- **LAB-ADR-009: Jembatan Rust → Python** (L0.3, `docs/decisions/LAB-ADR-009-jembatan-rust-python.md`). Matematika di core murni tanpa pyo3; crate binding `<nama>-py` (`cdylib`, `test = false`) hanya mengonversi tipe dan melepas GIL. PyO3 + rust-numpy di `[workspace.dependencies]` dengan minor yang sama, fitur `abi3-py313`, **tanpa** `extension-module` (deprecated; maturin ≥ 1.9.4). Layout campuran maturin: `.so` menjadi `<paket>._core` dengan stub `_core.pyi` + `py.typed` untuk mypy strict. `.cargo/config.toml` memin `PYO3_PYTHON` ke `.venv/bin/python` (`uv sync` harus mendahului `cargo clippy`). `just py-ext` (`maturin develop --uv`) dijalankan sebelum pytest karena cache uv tidak memantau crate core. Input array lewat `PyArrayLike1` (contiguous tanpa salin, view berstride disalin sekali). Toleransi test oracle diturunkan dari analisis galat, bukan angka tetap; input identik dibandingkan dengan `==`.
- **LAB-ADR-010: Antrean job dan kontrak payload** (L0.4, `docs/decisions/LAB-ADR-010-antrean-job.md`). Implementasi sendiri (pustaka antrean hanya satu bahasa): paket Go `jobqueue` (migrasi goose embedded dengan tabel versi `jobqueue_goose_version`, `Enqueue` yang menerima `pgx.Tx` untuk enqueue transaksional) dan paket Python `lab_worker`. Tabel `lab_jobs` (`uuidv7()`, status text + CHECK, indeks parsial). Klaim = satu perintah autocommit `FOR UPDATE SKIP LOCKED`; **lock untuk mengklaim, lease untuk menjalankan**; `attempts` naik saat klaim dan menjadi fencing token di setiap tulisan worker. **NOTIFY petunjuk, tabel kebenaran**: kanal `lab_jobs` (payload kind) + polling cadangan 30 s; kanal `lab_job_progress` (payload id) untuk SSE, dikirim oleh trigger `lab_jobs_progress_notify` setiap status atau progres berubah (migrasi `00002`, L0.5). At-least-once: heartbeat 5 s, reaper ambang 15 s, waktu dari `now()` server; handler idempoten. Thread heartbeat merangkap watchdog `timeout_s` (`os._exit(EX_TEMPFAIL)`). Retry dengan backoff equal jitter; `PermanentError` dan payload invalid tanpa retry. Worker crash-only. Kontrak JSON Schema 2020-12 `contracts/jobs/<kind>.v<N>.schema.json`, divalidasi Go saat enqueue dan Python saat klaim; integer yang harus eksak dibatasi 2⁵³ − 1.
- **LAB-ADR-011: Go API, SSE, dan portal** (L0.5, `docs/decisions/LAB-ADR-011-api-hello-dan-sse.md`). Go API memakai pustaka standar: `ServeMux` dengan pola `"METODE /path/{id}"`, `log/slog`, pola `run(ctx, getenv) error`, timeout server eksplisit, graceful shutdown. `/healthz` = liveness tanpa DB, `/readyz` = ping DB. Body `POST` adalah payload job yang divalidasi `Registry` (400 JSON rusak, 413 > 64 KiB, 422 melanggar skema, 500 lainnya); enqueue dalam `pgx.BeginFunc`; sukses `202` + `Location`; error `{"error": "..."}`. **SSE berbasis snapshot**: setiap event `job` berisi status lengkap hasil baca ulang tabel, sehingga reconnect tidak butuh replay. **Satu koneksi LISTEN per proses** (hub, di luar pool) → channel per klien ber-buffer 1 dengan kirim non-blocking; subscribe sebelum snapshot awal; heartbeat 15 s merangkap polling cadangan; deadline baca dihapus dan deadline tulis dipasang per event (`http.ResponseController`); stream ditutup saat status terminal dan klien wajib `EventSource.close()`. Portal `apps/web`: rewrite dev `/api/hello/*` → `HELLO_API_URL` (meniru Caddy, tanpa CORS; sejak LAB-ADR-012 hanya aktif di `next dev`), `compress: false`; kontrak TS ditulis tangan (`HelloApiError` membawa status HTTP) sampai OpenAPI diperkenalkan di API domain pertama; vitest.
- **LAB-ADR-012: Image Docker multi-stage dan Compose lokal** (L0.6, `docs/decisions/LAB-ADR-012-docker-dan-compose-lokal.md`). Konteks build = root repo dengan `.dockerignore` (termasuk `**/*.so` agar wheel dibangun bersih); Dockerfile di samping kodenya; BuildKit cache mount; runtime non-root. **Go:** `golang` → `distroless/static-debian13:nonroot`, `CGO_ENABLED=0`, `-trimpath -buildvcs=false`, `buildinfo.Version` via `ARG VERSION`; image membawa `hello-api` + `jobqueuectl`; subperintah `hello-api healthcheck` untuk `HEALTHCHECK` (distroless tanpa curl). **Worker:** build dan runtime memakai image Python yang sama (`python:3.13-slim-trixie`, symlink venv); build memakai rustup (toolchain dari `rust-toolchain.toml`) + uv; `uv sync --no-install-workspace` lalu `--no-editable --package <worker>` membangun wheel release maturin; runtime hanya `.venv` + `contracts/jobs` (`LAB_CONTRACTS_DIR`). **Web:** Next.js `output: "standalone"` dengan `outputFileTracingRoot` = root monorepo, pnpm via `npm install -g` (Node ≥ 25 tanpa corepack), `HOSTNAME=0.0.0.0`; **rewrite `/api` hanya di `next dev`** karena rewrites dibekukan saat build. **Compose** `infrastructure/compose.yaml` (proyek `lab-local`): postgres → `migrate` sekali jalan (`jobqueuectl migrate`, `service_completed_successfully`) → api + worker (`init`, `stop_grace_period` 30 s, `restart: unless-stopped`); batas CPU/memori §4.2, `GOMEMLIMIT`, rotasi log. **Caddy memegang routing `/api` di container** (`Caddyfile.local`, `127.0.0.1:8000`): `/api/<proyek>/*` tanpa `encode` + `flush_interval -1`, sisanya ke web dengan `encode zstd gzip`.
- **LAB-ADR-013: CI GitHub Actions dan GHCR** (L0.7, `docs/decisions/LAB-ADR-013-ci-github-actions.md`). Satu workflow `.github/workflows/ci.yml`: `changes` (path filter `dorny/paths-filter`) → `check` (**matrix dinamis** berisi bahasa yang berubah; setiap entri menjalankan `just ci-<bahasa>`, gabungannya = `just check`) → `images` → gerbang `ci-ok` (`if: always()`, satu-satunya required check). Anchor YAML: `justfile`/`ci.yml` memicu semua bahasa, perubahan Rust ikut memicu Python, prettier di job `web`. **Image** dibangun setelah check lulus atau di-skip, dengan filter path kedua per Dockerfile; PR hanya build, `main` push ke `ghcr.io/<owner>/applied-math-lab/<image>` dengan tag `sha-<7>` (deploy/rollback) + `main`, `VERSION=sha-<7>`, cache `type=gha`, `linux/amd64`; package publik; versi build diverifikasi berlapis: subperintah `hello-api version`, test Go yang membangun binary dengan `-X` sungguhan (linker diam bila target `-X` tidak ada atau paketnya terbuang), dan smoke test `docker run … version` di job `images`. Toolchain dipin (runner `ubuntu-24.04`, `rust-toolchain.toml`, `go.mod`, `.node-version`, `packageManager`, versi `just`/`uv`/golangci-lint di `env`). **Keamanan:** `permissions` minimal (`packages: write` hanya di `images` dan `retag`), `persist-credentials: false`, nilai ekspresi lewat `env:` (anti-injeksi), action dipin ke commit SHA (`pinact`) + Dependabot `github-actions` mingguan (cooldown 7 hari, satu grup). **Ruleset `main`:** PR wajib, `ci-ok` wajib, tanpa force push/penghapusan/bypass. `typecheck` web = `next typegen && tsc --noEmit`. Diperluas LAB-ADR-014 dengan job `retag` dan `deploy`.
- **LAB-ADR-014: VPS, deploy otomatis, dan slot job berat** (L0.8, `docs/decisions/LAB-ADR-014-vps-dan-deploy.md`). **Host** Ubuntu 24.04: user admin + `sudo`, SSH kunci saja tanpa root (`sshd_config.d/00-hardening.conf`, prefiks `00` karena nilai pertama yang menang), firewall dua lapis UFW + hPanel (port Docker melewati UFW → hanya Caddy yang punya `ports:`), unattended-upgrades + reboot 20:00 UTC, swap 2 GB `swappiness=10`, Docker resmi dengan `log-driver: local` + `live-restore`, admin tidak di grup `docker`. **Domain** `applied-math-lab.portfolio-bagas.tech` (A + CAA; AAAA ditunda). **Compose VPS** `infrastructure/compose.vps.yaml` (proyek `lab`, turunan compose lokal, image GHCR `${IMAGE_TAG}`, `${VAR:?}`, password hex, volume `caddy_data`, Postgres `max_connections=30`), di `/opt/applied-math-lab` dengan `.env` 600. **Caddyfile VPS**: TLS otomatis, HSTS 1 hari (naik setelah stabil), header keamanan, rute `/api/hello/readyz` untuk monitor. **Deploy:** user `deploy` (grup `docker`) dengan satu kunci `restrict,command="/usr/local/bin/lab-deploy"`; skrip milik root `infrastructure/vps/lab-deploy.sh` (`deploy <sha-40>` | `status`): validasi format, **SHA wajib di riwayat `main`** (GitHub API compare; commit fork bisa diakses lewat URL repo induk), unduh `compose.vps.yaml` + `Caddyfile` dari commit yang sama, `config` + `pull` sebelum menyentuh stack, `up -d --wait`, Caddy dibuat ulang bila Caddyfile berubah, verifikasi ID image container terhadap tag `sha-<7>` untuk setiap layanan (`hello-api version` hanya dicatat, karena image hasil `retag` membawa SHA build lama), prune image > 7 hari, `flock`, `deploy.log`; rollback = deploy SHA lama (`sudo -u deploy lab-deploy deploy <sha>`). **CI:** `changes` → `unchanged` + `deploy`; job `retag` (`imagetools create` `main` → `sha-<7>` untuk image yang tidak berubah, sehingga setiap commit `main` punya tiga tag); job `deploy` (environment `production` dibatasi ke `main`, `StrictHostKeyChecking=yes`, `BatchMode=yes`, `permissions: {}`, concurrency tanpa pembatalan, smoke test publik), tidak masuk `ci-ok`. **Slot job berat:** semua worker `cgroup_parent: lab-workers.slice`, slice systemd `CPUQuota=100%` (cgroup `/lab.slice/lab-workers.slice`; tanda hubung = hierarki) → total worker ≤ 1 vCPU dipaksakan kernel. **Monitoring:** uptime dari luar (layanan eksternal) untuk `/` dan `/api/hello/readyz`; metrik container ditunda ke MO-25.
- **LAB-ADR-015: Rust → WASM di portal** (L0.11, `docs/decisions/LAB-ADR-015-rust-wasm-di-portal.md`). Crate binding `<nama>-wasm` (`cdylib`, `test = false`) di samping crate core, sejajar dengan pola `-py`; matematika tetap di core. Build = `cargo build --target wasm32-unknown-unknown --profile wasm-release` + `wasm-bindgen --target web --omit-default-module-path` (resep `just wasm`; CLI lewat `just wasm-tools`), **tanpa wasm-pack**. Versi wasm-bindgen dipin persis (`=0.2.130`) dan harus sama di `[workspace.dependencies]`, `wasm_bindgen_version` di `justfile`, dan `ARG WASM_BINDGEN_VERSION` di `apps/web/Dockerfile`. **Bundler tidak menyentuh `.wasm`:** glue JS + `.d.ts` di `apps/web/src/wasm/<nama>/`, biner di `apps/web/public/wasm/`, URL diberikan eksplisit ke `init({ module_or_path })`; keduanya artefak build (tidak di-commit; dikecualikan dari prettier, eslint, dan konteks Docker). Satu pembungkus bertipe per modul di `apps/web/src/lib/` (muat sekali per tab); komponen tidak mengimpor glue langsung. Perbatasan tipe: `i64` → `BigInt`, slice `&[f64]` disalin sekali, hitungan memakai `u32`/`usize`. Test perbatasan di vitest dengan byte `.wasm` dari disk. `lint-web`, `test-web`, `dev-web` bergantung pada `wasm`; job `check (web)` memasang Rust + CLI dan ikut terpicu perubahan Rust; image `web` mendapat tahap `wasm`; smoke test deploy memeriksa `/wasm-demo` dan file `.wasm`. Rute halaman tidak boleh bernama sama dengan folder di `public/`.

### 2.4 Alur kerja algoritma: Python sebagai "meja laboratorium"

1. **Prototipe di Python/NumPy.** Kode masih dekat dengan notasi matematika, dan divalidasi terhadap referensi (SciPy, statsmodels, benchmark publik, contoh hitung tangan).
2. **Port hot path ke Rust** setelah algoritmanya terbukti benar.
3. **Versi Python dipertahankan sebagai test oracle.** Test otomatis memastikan output Rust sama dengan Python (dalam toleransi numerik) untuk seed yang sama.

Pola ini diterapkan secara selektif supaya tidak menggandakan pekerjaan:

- **MealOps:** validator, evaluator, dan Split ditulis di Python sebagai pemeriksa **independen** terhadap optimizer Rust. Metaheuristik (ALNS, GA) langsung ditulis di Rust, tetapi semua solusinya selalu diperiksa validator Python.
- **DengueSim dan Harga Pangan:** solver ODE, MCMC, Kalman filter, filter Hamilton, dan value iteration diprototipe di Python dan divalidasi terhadap pustaka referensi sebelum diport ke Rust.

### 2.5 Stack pendukung

| Kebutuhan           | Go                                                                        | Python                                                         | Rust                            | Next.js                                           |
| ------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------- | ------------------------------- | ------------------------------------------------- |
| Tooling & lint      | golangci-lint v2 (gofmt, goimports, revive, dll.), go vet                 | ruff, mypy strict                                              | rustfmt, clippy `-D warnings`   | eslint, `next typegen` + `tsc --noEmit`, prettier |
| Pengujian           | `testing` (`-race`, `-timeout 3m`), testcontainers-go                     | pytest, Hypothesis, testcontainers-python, SciPy (oracle, dev) | `cargo test`, proptest          | vitest                                            |
| Akses DB            | pgx (pgxpool) + sqlc, migrasi goose (Provider API, embedded)              | psycopg 3                                                      | —                               | —                                                 |
| Kontrak             | OpenAPI (oapi-codegen); JSON Schema job via santhosh-tekuri/jsonschema v6 | JSON Schema (`jsonschema`) / Pydantic                          | serde                           | openapi-typescript (hello: tipe ditulis tangan)   |
| HTTP                | `net/http` + `ServeMux` (LAB-ADR-011)                                     | —                                                              | —                               | EventSource (SSE)                                 |
| Profiling           | pprof                                                                     | cProfile                                                       | criterion, flamegraph           | —                                                 |
| Workspace           | satu `go.mod` di root (LAB-ADR-008)                                       | uv workspace                                                   | Cargo workspace                 | pnpm workspace                                    |
| Jembatan            | —                                                                         | maturin (build backend)                                        | PyO3 + rust-numpy (LAB-ADR-009) | —                                                 |
| Image (LAB-ADR-012) | distroless static nonroot                                                 | python slim + `.venv`                                          | wheel maturin di tahap build    | Next.js standalone                                |
| CI (LAB-ADR-013)    | `just ci-go`                                                              | `just ci-python`                                               | `just ci-rust`                  | `just ci-web` (+ prettier)                        |

Prettier di root juga memformat Markdown, JSON, dan YAML. Semua pemeriksaan dijalankan lewat `just` (`just fmt`, `just lint`, `just test`, `just check`); CI menjalankan resep per bahasa `just ci-<bahasa>` yang gabungannya sama dengan `just check`. Postgres dev: `just db-up` (`infrastructure/compose.dev.yaml`, PostgreSQL 18); alat antrean dev: `just jobq <migrate|status|enqueue|show>`. Walking skeleton dev: `just api-hello` (Go :8080), `just worker-hello`, `just dev-web` (Next.js :3000). WASM (LAB-ADR-015): `just wasm-tools` sekali untuk memasang `wasm-bindgen-cli`, lalu `just wasm` (otomatis dijalankan oleh `lint-web`, `test-web`, dan `dev-web`). Stack container lokal: `just stack-up` (semua lapisan di balik Caddy `http://localhost:8000`), `just stack-ps`, `just stack-logs`, `just stack-down`. **Produksi** (LAB-ADR-014): `https://applied-math-lab.portfolio-bagas.tech`, deploy otomatis setiap merge ke `main`; dari VPS: `cd /opt/applied-math-lab && sudo docker compose ps`, `sudo -u deploy lab-deploy status`, rollback `sudo -u deploy lab-deploy deploy <sha>`.

Kontrak dibagi dua: **OpenAPI** untuk Next.js ↔ Go, dan **JSON Schema** untuk payload job Go ↔ Python (diputuskan di L0.4, LAB-ADR-010).

## 3. Struktur Repositori (diputuskan di L0.2, LAB-ADR-008)

```text
applied-math-lab/
├── .github/
│   ├── workflows/ci.yml        # CI ✔: changes → check (matrix) → images (GHCR) → retag → deploy (VPS); ci-ok (LAB-ADR-013/014)
│   └── dependabot.yml          # update SHA action mingguan ✔
├── apps/
│   └── web/                    # Next.js lab portal ✔: /, /hello, /wasm-demo; Dockerfile ✔; nanti /mealops, /dengue, /pangan
├── services/
│   ├── hello/                  # walking skeleton lab (L0.4–L0.8)
│   │   ├── api/                # hello-api ✔: Go, enqueue + status + SSE (LAB-ADR-011); Dockerfile ✔
│   │   └── worker/             # hello-worker: handler lab.stats.summary ✔; Dockerfile ✔
│   ├── mealops/
│   │   ├── api/                # Go (paket main di modul root)
│   │   ├── worker/             # paket Python (anggota uv workspace)
│   │   ├── core/               # crate Rust murni (mealops-core, anggota Cargo workspace)
│   │   └── core-py/            # binding PyO3 (anggota Cargo + uv workspace, LAB-ADR-009)
│   ├── dengue/
│   │   ├── api/ worker/ core/ core-py/
│   └── pangan/
│       ├── api/ worker/ core/ core-py/
├── packages/
│   ├── go/                     # bersama: buildinfo ✔, jobqueue ✔ (+ cmd/jobqueuectl), auth, llmgateway, httpx
│   ├── python/                 # bersama: lab-stats ✔, lab-worker ✔ (klien antrean + loop worker)
│   └── rust/                   # bersama: lab-numerics ✔, lab-numerics-py ✔ (binding), lab-numerics-wasm ✔ (binding WASM), lab-rng
├── contracts/                  # contracts.go (embed) ✔, jobs/ (JSON Schema) ✔, openapi/
├── datasets/                   # per proyek: synthetic/, fixtures/, raw/ (tidak di-commit)
├── experiments/                # konfigurasi dan hasil benchmark
├── infrastructure/
│   ├── compose.dev.yaml        # Postgres dev ✔
│   ├── compose.yaml            # stack lokal ✔ + Caddyfile.local ✔
│   ├── compose.vps.yaml        # stack produksi, image GHCR ✔ (LAB-ADR-014)
│   ├── Caddyfile               # Caddy VPS: TLS, header keamanan, readyz ✔
│   ├── .env.vps.example        # contoh .env VPS ✔
│   ├── vps/                    # konfigurasi host, dipasang manual oleh admin ✔
│   │   ├── lab-deploy.sh       #   → /usr/local/bin/lab-deploy (forced command user deploy)
│   │   └── lab-workers.slice   #   → /etc/systemd/system/ (slot job berat ≤ 1 vCPU)
│   └── backup/                 # nanti (pg_dump off-site)
├── docs/
│   ├── decisions/              # ADR lab dan proyek (LAB-ADR-008 sampai 015 ✔), TEMPLATE.md ✔, README.md (indeks) ✔
│   ├── mathematics/            # mealops/model.md ✔ (§1–3); nanti dengue/, pangan/
│   └── PROGRESS.md             # log handoff antar-thread ✔ (sumber utama; salinan di Project knowledge)
├── .cargo/config.toml          # PYO3_PYTHON → .venv/bin/python ✔
├── .dockerignore               # konteks build Docker = root repo ✔
├── .env.example                # DATABASE_URL dev ✔ (.env tidak di-commit)
├── go.mod                      # satu modul Go untuk seluruh repo
├── Cargo.toml / Cargo.lock     # Cargo workspace (members: packages/rust/*, services/*/core, services/*/core-py)
├── pyproject.toml / uv.lock    # uv workspace root (package = false) + config ruff/mypy/pytest
├── package.json / pnpm-workspace.yaml / pnpm-lock.yaml   # pnpm workspace (apps/*), satu lockfile
├── justfile                    # setup(-py/-node), fmt, lint, test, ci-*, check, py-ext, wasm, wasm-tools, db-*, jobq, worker-hello, api-hello, dev-web, stack-*
├── rust-toolchain.toml / .python-version / .node-version
├── .golangci.yml / .prettierignore / .editorconfig / .gitattributes / .gitignore
├── README.md
└── PROJECT_CONTEXT.md
```

✔ = sudah ada di repo. Buat direktori hanya ketika sudah ada isi nyatanya. Saat crate atau worker pertama dibuat, tambahkan `services/*/core` dan `services/*/core-py` ke `members` Cargo; `services/*/worker` dan `services/*/core-py` ke `members` uv; path binding baru ke resep `py-ext`, path `python/` binding ke `lint-py` (mypy; `services/*/worker/src` sudah tercakup glob), dan direktori test ke `testpaths` pytest. (Bagian worker sudah dilakukan untuk `services/hello/worker` di L0.4.) API baru memakai pola `services/hello/api` (LAB-ADR-011) dan menambahkan resep `api-<proyek>` serta rewrite dev `/api/<proyek>/*` di `apps/web/next.config.ts`. Untuk container (LAB-ADR-012): Dockerfile API dan worker per proyek, service `migrate` sendiri, entri `/api/<proyek>/*` di Caddyfile, dan manifest anggota workspace baru disalin di tahap dependensi Dockerfile worker. Untuk CI (LAB-ADR-013): path baru masuk filter bahasa di `ci.yml` bila tidak tercakup glob yang ada, setiap image baru mendapat filter image, cabang `case` Dockerfile di job `images`, dan entri di daftar `ALL` job `changes`. Untuk VPS (LAB-ADR-014): service baru di `compose.vps.yaml` (worker dengan `cgroup_parent: lab-workers.slice`), rute `/api/<proyek>/*` dan `readyz` di `infrastructure/Caddyfile`, layanan baru di daftar verifikasi ID image `lab-deploy.sh` (dipasang ulang manual), dan monitor eksternal untuk `readyz` baru. Untuk WASM (LAB-ADR-015): crate `<nama>-wasm`, langkah build-nya di resep `wasm` dan di tahap `wasm` Dockerfile web, serta pembungkus di `apps/web/src/lib/`.

## 4. Infrastruktur dan Deployment

### 4.1 VPS

Hostinger, Ubuntu 24.04 LTS, domain lab `applied-math-lab.portfolio-bagas.tech` (LAB-ADR-014).

| Sumber daya       |           Tersedia |
| ----------------- | -----------------: |
| CPU               |             2 vCPU |
| RAM               | 8 GB (+ swap 2 GB) |
| Disk              |        100 GB NVMe |
| Bandwidth bulanan |               8 TB |

### 4.2 Anggaran sumber daya awal (dikalibrasi lewat pengukuran)

| Container                     | Batas CPU                             | Batas memori         | Catatan                                                                    |
| ----------------------------- | ------------------------------------- | -------------------- | -------------------------------------------------------------------------- |
| caddy                         | 0.25                                  | 128 MB               |                                                                            |
| web (Next.js standalone)      | 0.5                                   | 512 MB               | Satu portal untuk tiga proyek                                              |
| api ×3 (Go)                   | 0.25 masing-masing                    | 128 MB masing-masing | `GOMEMLIMIT` di bawah batas container                                      |
| worker ×3 (Python + Rust)     | 1.0 masing-masing, **gabungan ≤ 1.0** | 768 MB masing-masing | Concurrency 1 job, batas waktu per job; gabungan lewat `lab-workers.slice` |
| postgres                      | 0.5                                   | 1.5 GB               | PostGIS + TimescaleDB, satu database per proyek                            |
| osrm (MealOps, fase lanjutan) | 0.5                                   | 1.5 GB               | Ekstrak satu kota/provinsi                                                 |

Batas CPU per container sengaja _overcommit_, tetapi seluruh worker berada di bawah cgroup induk `lab-workers.slice` (`CPUQuota=100%`), sehingga gabungannya tidak pernah melebihi satu vCPU. Total memori puncak sekitar 5,5 GB. Batas ini dipasang di Compose lokal (L0.6) dan Compose VPS (L0.8).

**Bottleneck pertama yang diperkirakan adalah CPU.** Konsekuensinya:

1. Komputasi berat dilakukan offline di laptop (praproses OSRM, kalibrasi MCMC panjang, matriks jarak); VPS hanya menyimpan hasilnya.
2. Solver selalu dijalankan lewat antrean.
3. Simulasi interaktif dijalankan di klien (WASM).

### 4.3 Kecukupan VPS

| Sumber daya          | Kebutuhan perkiraan                                                                                                                     | Penilaian                                                                                    |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| RAM 8 GB             | ~4 GB tanpa OSRM, ~5,5 GB dengan OSRM                                                                                                   | **Cukup**, dengan sisa untuk page cache Postgres                                             |
| CPU 2 vCPU           | Solver/MCMC bisa memakai 1 core penuh selama menit hingga jam                                                                           | **Batas utama.** Cukup untuk demo, tidak cukup untuk benchmark besar atau banyak job paralel |
| Disk 100 GB NVMe     | OS ~5 GB, image Docker ~5–8 GB, database < 5 GB (Harga Pangan tumbuh paling cepat), backup lokal ~5 GB, data OSRM terproses beberapa GB | **Sangat cukup**                                                                             |
| Bandwidth 8 TB/bulan | Trafik portofolio, pull image saat deploy, backup off-site: jauh di bawah 100 GB/bulan                                                  | **Sangat cukup**                                                                             |

**Kesimpulan:** cukup untuk menjalankan tiga aplikasi sebagai demo portofolio dengan trafik rendah. Tidak cukup (dan tidak perlu) untuk benchmark multi-seed skala penuh, rantai MCMC panjang, praproses OSRM, atau banyak pengguna yang menjalankan solver bersamaan. Pekerjaan itu dilakukan di laptop.

### 4.4 Strategi memaksimalkan VPS

**CPU (prioritas utama)**

1. **Komputasi offline, penyajian online.** Benchmark, kalibrasi MCMC, praproses peta, dan matriks jarak dijalankan di laptop. Hasilnya diunggah ke database sebagai artefak.
2. **Skenario demo diprakomputasi.** Pengunjung portofolio langsung melihat hasil tanpa memicu solver.
3. **Satu slot job berat untuk seluruh lab** (diputuskan di L0.8, LAB-ADR-014). Semua container worker berada di cgroup systemd `lab-workers.slice` dengan `CPUQuota=100%`, sehingga kernel memaksakan total worker ≤ 1 vCPU dan satu core selalu tersisa untuk API, web, dan database. Ini batas sumber daya, bukan mutual exclusion: dua job berat yang berjalan bersamaan berbagi satu core. Advisory lock tidak dipakai karena berlingkup per database.
4. **Batas per job:** batas waktu, ukuran instans maksimum di mode demo, dan rate limit pengajuan job per pengguna.
5. **Memoisasi hasil.** Kombinasi snapshot skenario + algoritma + seed + versi kode yang sama memakai ulang hasil yang sudah ada (hasil bersifat immutable).
6. **Komputasi di browser (WASM)** untuk simulasi interaktif DengueSim, Kalman filter interaktif Harga Pangan, dan instans MealOps kecil, sehingga CPU pengunjung yang bekerja.
7. **Build di CI**, tidak pernah di VPS.

**RAM**

- `GOMEMLIMIT` di setiap Go API; Python worker satu proses dengan import sekali dan menunggu via `LISTEN`, bukan polling.
- PostgreSQL disetel untuk RAM kecil: awal L0.8 `max_connections=30`, `shared_buffers=256MB`, `work_mem=4MB`, `shm_size` 256 MB (dinaikkan ke `shared_buffers` ~1 GB saat database proyek bertambah). Karena itu SSE di Go API memakai satu koneksi LISTEN per proses, bukan per klien (LAB-ADR-011).
- Swap 2 GB di NVMe dengan `vm.swappiness=10` (terpasang di L0.8) sebagai jaring pengaman, bukan memori kerja.
- OSRM hanya dinyalakan bila routing on-demand benar-benar dibutuhkan (MO-21). Alternatifnya, matriks waktu tempuh diprakomputasi di laptop dan disimpan di database, sehingga container OSRM tidak perlu ada.

**Disk**

- `lab-deploy` menjalankan `docker image prune -af --filter until=168h` setelah setiap deploy; versi lama untuk rollback ditarik ulang dari GHCR bila sudah terbuang.
- Kompresi dan retensi TimescaleDB untuk data harga harian.
- Log Docker dengan driver `local` (10 MB × 3 per container, bawaan daemon); retensi backup lokal 7 hari, salinan utama off-site.

**Bandwidth**

- Aset statis di-cache Caddy dan browser; modul WASM dikompresi (brotli).
- Tile peta dari penyedia eksternal, tidak di-host sendiri.

**Ukur sebelum menyetel.** Uptime dipantau dari luar oleh layanan monitor eksternal (L0.8) terhadap `/` dan `/api/hello/readyz`; monitor di mesin yang sama tidak bisa melaporkan mesinnya sendiri mati. Metrik container (observability) ditunda ke MO-25; sampai itu `docker stats` dipakai. Batas container di §4.2 adalah titik awal dan dikalibrasi dari pemakaian nyata.

### 4.5 CI/CD

```text
git push / PR ──► GitHub Actions: .github/workflows/ci.yml (LAB-ADR-013, 014)
                  ├─ changes : path filter → bahasa, image berubah, image tidak berubah, perlu deploy?
                  ├─ check   : matrix dinamis, satu runner per bahasa → just ci-<bahasa>
                  │            (go | rust | python | web; Rust ikut memicu Python)
                  ├─ images  : setelah check lulus; Dockerfile LAB-ADR-012, konteks root repo
                  │            PR: build saja · main: push ke GHCR
                  │            tag sha-<7> + main, VERSION=sha-<7>, cache type=gha
                  ├─ retag   : (main) image tidak berubah: main → sha-<7> tanpa build
                  ├─ ci-ok   : gerbang tunggal (required check di ruleset main)
                  └─ deploy  : (main, environment production) ssh deploy@VPS "deploy <sha-40>"
                                     │       + smoke test publik / dan /hello
                                     ▼
                  VPS: forced command lab-deploy → cek SHA di riwayat main → unduh
                  compose.vps.yaml + Caddyfile dari commit itu → pull → up -d --wait
                  → verifikasi ID image → deploy.log
```

Image di-build di CI, tidak pernah di VPS. Test integrasi Go dan Python memakai Docker (testcontainers) yang sudah tersedia di runner GitHub. Stack lokal (`infrastructure/compose.yaml`) membangun image yang sama dari Dockerfile yang sama; compose VPS (`infrastructure/compose.vps.yaml`) memakai image dari GHCR (`ghcr.io/adrianus-bagas/applied-math-lab/<image>`, publik, tanpa token). Action dipin ke commit SHA dan diperbarui Dependabot; `main` dilindungi ruleset (PR wajib, `ci-ok` wajib). Secret deploy hanya ada di environment `production` yang dibatasi ke `main`; kunci deploy tidak bisa membuka shell.

### 4.6 Kebersihan produksi

- HTTPS lewat Caddy (Let's Encrypt, sertifikat di volume `caddy_data`, HSTS); hanya port 22 (dibatasi), 80, dan 443 (TCP + UDP) yang terbuka, dijaga UFW **dan** firewall hPanel; PostgreSQL dan API tidak publik (terverifikasi dari luar).
- SSH hanya dengan kunci; login root dimatikan; admin memakai `sudo`; CI memakai user `deploy` yang dikunci forced command.
- Patch keamanan otomatis (unattended-upgrades) dengan reboot otomatis 03:00 WIB; stack pulih sendiri setelah reboot (terverifikasi).
- Secret disimpan di `.env` (mode 600) yang tidak di-commit, dengan prinsip _least privilege_.
- `pg_dump` terjadwal ke lokasi off-site, dengan uji restore berkala (MO-25).
- Healthcheck `/healthz` (liveness, tanpa DB; di image distroless lewat `hello-api healthcheck`) dan `/readyz` (ping DB; publik lewat `/api/hello/readyz` untuk monitor eksternal), `restart: unless-stopped` (wajib untuk worker crash-only, LAB-ADR-010), rotasi log.
- Caddy meneruskan `text/event-stream` tanpa buffering dan tanpa kompresi: terverifikasi di Compose lokal (L0.6) dan lewat TLS di VPS (L0.8: heartbeat tiba tiap 15 s, event progres real time).
- Container berjalan sebagai user non-root.
- Hanya data sintetis atau data publik; tidak ada data pribadi yang dikirim ke penyedia LLM.

## 5. Ringkasan Proyek

### 5.1 MealOps — optimasi dapur massal dan distribusi makanan perishable

- **Masalah:** dapur massal (dapur produksi terpusat, katering institusi seperti sekolah, rumah sakit, dan kantor, dapur umum tanggap bencana, cloud kitchen) memasak ribuan porsi dalam beberapa batch dan mengirimkannya ke banyak titik layanan dengan armada terbatas. Makanan siap saji bersifat **perishable**: ada batas waktu sejak selesai dimasak sampai dikonsumsi (_holding time_), sehingga jadwal produksi dan rute pengiriman harus diputuskan **bersama**. Memasak terlalu awal melanggar batas waktu; terlalu lambat melanggar jendela waktu titik layanan.
- **Matematika:** varian VRP dengan jendela waktu dan kapasitas (CVRPTW), multi-trip dan pemecahan demand, penjadwalan batch produksi dengan release date, constraint holding time yang mengikat produksi dan routing, metaheuristik (ALNS, GA memetic), dan simulasi Monte Carlo untuk robustness rencana terhadap ketidakpastian waktu masak dan waktu tempuh.
- **Konteks Indonesia:** program makan bergizi skala besar, katering institusi, dan dapur umum bencana adalah contoh penerapan. Skenario dan data bersifat **sintetis/ilustratif**; MealOps tidak mewakili, tidak dievaluasi terhadap, dan tidak berafiliasi dengan program atau lembaga mana pun.
- **Batasan:** rencana yang dihasilkan adalah usulan di bawah asumsi model (waktu tempuh, durasi masak, batas holding time sebagai parameter yang dapat diatur), bukan standar keamanan pangan.

**Glosarium istilah dokumen lama (MealOps v3.1, dulu MBG v3.1):**

| Istilah lama               | Istilah umum                                    |
| -------------------------- | ----------------------------------------------- |
| Program MBG                | Program layanan makan massal (contoh penerapan) |
| SPPG                       | Dapur massal / dapur produksi                   |
| Sekolah / penerima manfaat | Titik layanan / pelanggan                       |
| Porsi MBG                  | Porsi / demand                                  |
| Waktu makan sekolah `m_i`  | Waktu konsumsi terencana di titik layanan       |
| Buffer sekolah `δ_i`       | Buffer serah-terima internal titik layanan      |
| Ompreng                    | Wadah porsi; kapasitas dihitung dalam porsi     |
| `MBG-n`                    | `MO-n`                                          |
| `M<n>.<k>` (roadmap v3.1)  | `MO-<n>.<k>`; M0 → L0; rincian di §7            |

**Notasi:** glosarium §8.1 MealOps v3.1 adalah notasi kanonik model (misalnya `τ_ij` waktu tempuh, `a_j` paling awal menerima, `d_j` deadline, `T_j` mulai layanan). Notasi tambahan yang diperkenalkan sejak MO-1 dicatat di `docs/mathematics/mealops/model.md` (sejauh ini `A_j` waktu tiba, `W_j` lama menunggu, `V` dan `𝒜` himpunan node dan arc Model A, `a'_j` dan `d'_j` jendela efektif, `T*_j` mulai layanan pada jadwal tercepat).

**Keputusan MO-1.1** (rincian dan contoh hitung di `model.md` §1):

- **Satuan:** waktu = menit bulat sejak 00:00 hari operasi, semua di `[0, 1440)`; demand dalam porsi; jarak dalam meter. Durasi turunan (misalnya `s_j = s⁰ + η q_j`) dibulatkan **ke atas** sekali saat instans dibuat, sehingga validator dan core hanya membandingkan bilangan bulat.
- **Jam di rute:** `A_j = T_i + s_i + τ_ij`, `T_j = max(A_j, a_j)`, `W_j = T_j − A_j`; layak bila `T_j ≤ d_j` (jendela keras, konvensi Solomon).
- **Holding:** `h_j = m_σ(j) − f_b`; seluruh batch selesai pada satu saat `f_b`, jam berhenti di waktu konsumsi terencana. Batas `H^max` memberi batas bawah `f_b`, rute memberi batas atasnya.
- **Asumsi baru:** `δ_σ(j) ≥ s_j` (bongkar selesai sebelum waktu konsumsi) dan ketaksamaan segitiga `τ_ij ≤ τ_ik + τ_kj`; instans yang melanggar ditolak saat validasi input (MO-2.1, MO-3.2).

**Keputusan MO-1.2** (rincian, bukti, dan contoh di `model.md` §2):

- **Model A:** graf dengan dua salinan dapur (`0` berangkat, `n+1` kembali), `n(n+1)` arc; variabel `x_ij` tanpa indeks kendaraan (armada homogen), `T_j`, `u_j`; objektif total jarak, jumlah kendaraan hanya dibatasi `|K|`.
- **Demand:** `q_j` bilangan bulat ≥ 1; node tanpa demand ditolak saat validasi instans. Ini yang membuat propagasi muatan menghapus subtour tanpa syarat; propagasi waktu hanya penjamin kedua (bisa gagal bila `s + τ = 0` di antara node pecahan).
- **Jam dapur dilebur ke node:** `a'_j = max(a_j, e_0 + τ_0j)`, `d'_j = min(d_j, l_0 − s_j − τ_j,n+1)`; sah karena ketaksamaan segitiga. `a'_j > d'_j` berarti instans tidak layak (bukan input tidak valid).
- **Big-M terkecil:** `M = Q` untuk muatan, `M_ij = max{0, d'_i + s_i + τ_ij − a'_j}` untuk waktu. `M` yang terlalu kecil membuang solusi layak.
- **Pemeriksaan satu rute** (setara dengan constraint muatan dan waktu): jumlah demand ≤ `Q`, lalu satu lintasan maju jadwal tercepat `T*_j1 = a'_j1`, `T*_next = max(T*_i + s_i + τ_ij, a'_j)`, gagal bila `T* > d'`. Ini yang diimplementasikan validator (MO-3.2) dan evaluator core.
- **Praproses arc mustahil:** `a'_i + s_i + τ_ij > d'_j` atau `q_i + q_j > Q` → `x_ij = 0` (MO-5, MO-6.2).

**Keputusan MO-1.3** (contoh hitung tangan di `model.md` §3):

- **Tiga tingkat kegagalan, dilaporkan terpisah:** _input tidak valid_ (data melanggar pemeriksaan instans, ditolak saat validasi), _instans tidak layak_ (data sah tetapi tidak ada solusi; cukup satu saksi untuk membuktikan layak, perlu argumen atas semua solusi untuk membuktikan tidak layak), dan _solusi tidak layak_ (satu solusi tertentu melanggar struktur, armada, kapasitas, atau jendela waktu).
- **Fixture hitung tangan:** instans H5 (`n = 5`, `|K| = 2`, `Q = 100`; 9 solusi layak, optimum unik 32) dan varian tidak layak V1–V4 menjadi fixture di MO-2.3; nilai harapannya adalah angka di `model.md` §3.
- **Batas bawah jumlah kendaraan:** yang terbesar dari `⌈Σq/Q⌉` dan ukuran kelompok node yang berpasangan tidak bisa serute (arc mustahil di kedua arah, atau `q_i + q_j > Q`); dipakai di MO-6.3.

**Rujukan utama:** `PROJECT_CONTEXT` MealOps v3.1. Bagian berikut **tetap berlaku**: §1–4 (masalah, batasan, pengguna, strategi rilis), §8 (model matematis A → D dan Monte Carlo), §9 (algoritma ALNS dan GA memetic), §10 (eksperimen), §11 (AI hanya LLM), §12–14 (model data, API, dashboard), §19 (standar), §21 (deliverable). ADR-002, 005, 006, 007, dan 008 juga tetap berlaku.

**Digantikan oleh dokumen ini:**

| Bagian MealOps v3.1                    | Pengganti                                  |
| -------------------------------------- | ------------------------------------------ |
| §5 Stack dan ADR-001 (Go satu-satunya) | §2 dokumen ini; LAB-ADR-001                |
| ADR-003 (api + worker satu binary Go)  | LAB-ADR-003 (Go API + Python worker)       |
| ADR-004 (`internal/optimizer` di Go)   | LAB-ADR-004 (crate `mealops-core` di Rust) |
| §6 Arsitektur dan struktur repo        | §2.2 dan §3 dokumen ini                    |
| §7 Deployment dan spesifikasi VPS      | §4 dokumen ini                             |
| §15–16 Roadmap dan timeline            | §7–8 dokumen ini                           |
| §17–18 Alur thread dan kolaborasi      | §6 dokumen ini                             |
| §22 Konteks singkat                    | §10 dokumen ini                            |

**Pembagian lapisan MealOps:**

- **Rust (`mealops-core`):** model instans/solusi, evaluator cepat dengan forward time slack, konstruktif, local search, ALNS, GA memetic (paralel dengan rayon, RNG per thread diturunkan dari seed utama), solver exact enumerasi + branch-and-bound, decoder produksi, dan simulator eksekusi Monte Carlo.
- **Python:** generator data sintetis, loader Solomon + BKS, **validator independen**, harness benchmark, statistik (Wilcoxon diimplementasikan sendiri lalu diverifikasi terhadap SciPy), dan analisis Monte Carlo (interval Wilson, common random numbers).
- **Go:** API domain, snapshot skenario, pengajuan run dan simulasi, AI gateway.
- **Next.js:** peta rute, Gantt produksi, robustness, perbandingan, asisten what-if.

### 5.2 DengueSim — pemodelan dan intervensi DBD

- **Masalah:** dinas kesehatan perlu memperkirakan lonjakan kasus DBD musiman dan memilih waktu serta intensitas intervensi (fogging, PSN) dengan anggaran terbatas.
- **Matematika:** model **SEIR (manusia) – SEI (nyamuk)** dengan parameter yang dipengaruhi iklim; analisis ekuilibrium, kestabilan, dan **R₀ via next-generation matrix**; kalibrasi **MCMC (Metropolis–Hastings)**; **kontrol optimal** (prinsip maksimum Pontryagin, forward–backward sweep).
- **Lapisan:** Rust (RK4, RK45 adaptif Dormand–Prince, MCMC, forward–backward sweep, target WASM); Python (data, definisi model, diagnosa MCMC, validasi terhadap `solve_ivp`); Go (API skenario, hasil kalibrasi); Next.js (kurva epidemi, peta risiko, simulator slider).
- **AI:** LLM menjelaskan hasil skenario dalam bahasa awam.
- **Data (perlu diverifikasi):** kasus DBD per kabupaten/kota (Kemenkes/dinkes, Satu Data); iklim harian (BMKG, alternatif NASA POWER).
- **Batasan:** output berupa proyeksi di bawah asumsi model, bukan prediksi pasti dan bukan pengganti surveilans epidemiologi.

### 5.3 Harga Pangan (PanganWatch)

- **Masalah:** harga pangan pokok (beras, cabai, bawang) bergejolak dan berbeda antarwilayah. Pengambil kebijakan perlu deteksi dini serta keputusan kapan dan berapa banyak melepas stok penyangga.
- **Matematika:** harga sebagai **proses stokastik**; **model state-space** (local level + musiman, termasuk efek Ramadan/Lebaran yang bergeser mengikuti kalender Hijriah) dengan **Kalman filter/smoother** dan estimasi MLE; **Markov regime-switching** (filter Hamilton) untuk deteksi lonjakan; simulasi **Monte Carlo** untuk interval prediksi; **pemrograman dinamik stokastik** (persamaan Bellman, value iteration) untuk kebijakan stok penyangga.
- **Lapisan:** Rust (Kalman filter/smoother, filter Hamilton, generator jalur, value iteration); Python (ingest harian, pembersihan, MLE, validasi terhadap statsmodels, backtesting); Go (API harga dan sinyal, job harian); Next.js (grafik + interval prediksi, peta disparitas, panel peringatan, simulator kebijakan).
- **AI:** LLM merangkum kondisi harga dan menjelaskan peringatan dini.
- **Data (perlu diverifikasi):** Panel Harga Pangan Badan Pangan Nasional, PIHPS Nasional (Bank Indonesia), BPS. Data time series disimpan di TimescaleDB.
- **Batasan:** model kebijakan stok adalah penyederhanaan ilustratif, bukan rekomendasi resmi.

## 6. Alur Kolaborasi

Pengguna adalah sarjana matematika dan software engineer frontend (React/Next.js) berpengalaman 3 tahun, dan baru mempelajari Go, Python untuk komputasi, serta Rust. Kerja dibagi ke dalam tiga mode; setiap sub-milestone di §7 diberi label mode.

### 6.1 Mode Tuntun (T): setup environment, proyek, dan deployment

Berlaku untuk lingkungan dev, scaffolding proyek, monorepo, tooling, plumbing antarlapisan (PyO3, antrean job, kontrak), database dan migrasi, Docker, Caddy, CI/CD, deployment, profiling, dan integrasi pustaka.

1. Claude menjelaskan **tujuan dan alasan** setiap langkah, termasuk apa yang terjadi bila langkah itu dilewati.
2. Claude memberikan instruksi langkah demi langkah: perintah untuk WSL Ubuntu dan isi file lengkap.
3. Pengguna menjalankan, lalu melaporkan hasil atau error.
4. Claude membantu debug dan menjelaskan apa yang terjadi.
5. Ditutup dengan checklist verifikasi (tes hijau, pipeline CI lulus, endpoint merespons).

### 6.2 Mode Latihan (L): logika bisnis dan matematika

Berlaku untuk formulasi model, penurunan teori, validator, algoritma, solver numerik, inferensi, statistik, simulasi, dan logika fitur LLM.

1. Jelaskan **konsep matematis** terlebih dahulu (definisi, intuisi). **Penurunan rumus dituntun lengkap langkah demi langkah** (sejak L0.9) dan ditutup satu-dua pertanyaan cek pemahaman; pengguna tidak diminta menurunkannya sendiri.
2. Berikan satu **tugas kecil yang konkret**, disertai kerangka: signature fungsi, definisi tipe, tes yang sudah ada, sebagian potongan kode, dan langkah bernomor di dalam fungsi.
3. Pengguna mengimplementasikan logikanya sendiri sampai tes hijau.
4. Review: kebenaran, kompleksitas, stabilitas numerik, dan gaya idiomatik bahasanya.
5. Lanjut hanya setelah langkah tersebut dipahami dan tervalidasi.

### 6.3 Mode Mandiri (Md): frontend

Berlaku untuk Next.js, area keahlian pengguna. Pengguna mengimplementasikan; Claude mereview dan membantu bagian integrasi (OpenAPI, WASM, kontrak data).

### 6.4 Prinsip umum

- **Bahasa diajarkan just-in-time.** Rust (ownership, borrowing, trait, generics, iterator, error) dan Python numerik diperkenalkan di L0, lalu didalami saat dibutuhkan. Go hanya dipakai di lapisan API, jadi diajarkan saat milestone API.
- **Penjelasan Go, Python, dan Rust memakai bahasa sederhana** (analogi, alasan di balik setiap flag/pola), karena ketiganya masih baru bagi pengguna.
- Hindari memberikan implementasi lengkap untuk tugas Mode Latihan, kecuali diminta secara eksplisit.
- Instruksi disesuaikan dengan WSL Ubuntu, Docker Engine langsung di WSL, dan editor Zed. Akses VPS dari WSL lewat alias SSH `lab-vps`.
- Teori dan komputasi diseimbangkan: setiap ⭐ adalah titik belajar teori yang wajib dipahami, bukan hanya diimplementasikan.
- **Komentar dan docstring di kode ditulis dalam Bahasa Indonesia** (doc comment Go tetap diawali nama identifier). Pesan error runtime boleh berbahasa Inggris.

### 6.5 Alur thread (efisiensi token)

- **Satu sub-milestone = satu thread Claude.** Sub-milestone dibatasi **≤ 10 jam** dan bisa dikerjakan dalam beberapa sesi di thread yang sama.
- Simpan `PROJECT_CONTEXT.md` (lab), `PROJECT_CONTEXT` MealOps (`claude/PROJECT_CONTEXT_MEALOPS_v3.1.md`), `docs/PROGRESS.md`, dan `docs/mathematics/<proyek>/model.md` di Project knowledge. Jangan menempelkan ulang konteks di setiap thread.
- **Membuka thread** dengan satu baris: `Thread L0.1 — Lingkungan dev. Status terakhir: lihat PROGRESS.md.`
- **Kerja di branch** (sejak L0.7): setiap thread dikerjakan di branch sendiri, misalnya `l0.9-rust`. `main` dilindungi ruleset (PR wajib, `ci-ok` wajib), jadi push langsung ke `main` ditolak. Sejak L0.8, merge ke `main` otomatis men-deploy ke VPS bila image atau konfigurasi VPS berubah.
- **Menutup thread** dengan catatan handoff (≤ 150 kata) yang ditambahkan Claude ke `PROGRESS.md` di Project knowledge dan diberikan sebagai file untuk `docs/PROGRESS.md` di repo (sumber utama sejak L0.11), memperbarui tanda status di §7, lalu commit di branch thread, PR, tunggu `ci-ok` hijau, dan **squash merge** ke `main`:

```markdown
## [MO-1.2] Model A CVRPTW — YYYY-MM-DD

- Selesai:
- Keputusan (referensi ADR):
- File yang berubah:
- Pertanyaan terbuka:
- Berikutnya: MO-1.3
- Jam: estimasi X / aktual Y
```

- Jika sub-milestone melebihi estimasi, pecah menjadi a/b alih-alih memperpanjang thread.

## 7. Roadmap

Konvensi: format `nomor Nama (jam, mode)`. ⭐ menandai titik utama belajar teori. Prefiks: **L** = lab, **MO** = MealOps, **D** = DengueSim, **P** = Harga Pangan. **Status:** ✅ selesai · ⏳ sedang dikerjakan · tanpa tanda = belum dimulai. Milestone bertanda ⏳ selama ada sub-milestone yang sudah dimulai, dan ✅ setelah semua sub-milestone selesai.

### 7.1 L0 — Fondasi Lab (~59 jam) ✅

| Sub-milestone (jam, mode)                                                                                                         |
| --------------------------------------------------------------------------------------------------------------------------------- |
| ✅ L0.1 Lingkungan dev: WSL, Go, rustup, uv (Python), Node + pnpm, Docker Engine, Zed + LSP tiap bahasa (4, T)                    |
| ✅ L0.2 Monorepo: struktur, workspace Go/Cargo/uv/pnpm, lint/format tiap bahasa, Makefile/justfile, ADR struktur repo (5, T)      |
| ✅ L0.3 Jembatan Rust → Python: PyO3 + maturin, fungsi contoh, test oracle dengan pytest (5, T)                                   |
| ✅ L0.4 Antrean job: Go enqueue, Python worker `SKIP LOCKED` + `LISTEN/NOTIFY`, heartbeat, kontrak JSON Schema (6, T)             |
| ✅ L0.5 Kerangka Next.js lab portal + Go API hello (dasar Go: modul, paket, `net/http`) + progres via SSE (4, T)                  |
| ✅ L0.6 Docker multi-stage (wheel maturin), Compose lokal untuk semua lapisan (5, T)                                              |
| ✅ L0.7 CI GitHub Actions: matriks 4 bahasa, path filter, push ke GHCR (4, T)                                                     |
| ✅ L0.8 VPS: hardening, Caddy, deploy pertama end-to-end "hello lab" (6, T)                                                       |
| ✅ L0.9a ⭐ Latihan Rust lewat soal matematika: ownership, borrowing, struct, enum, error, trait, generics, trait operator (9, L) |
| ✅ L0.9b Latihan Rust: iterator lewat pecahan berlanjut √2 (1, L)                                                                 |
| ✅ L0.10 ⭐ Latihan Python numerik: vektorisasi NumPy, SciPy, aritmetika floating-point dan toleransi tes (6, L)                  |
| ✅ L0.11 Template ADR, `PROGRESS.md`, demo Rust → WASM di portal (4, T)                                                           |

### 7.2 MealOps — MVP (~317 jam) ⏳

Detail matematis setiap milestone mengikuti MealOps v3.1 §8–10.

**Fase 0 — Formulasi dan fondasi data (~83 jam)**

| Milestone                                   | Sub-milestone (jam, mode)                                                                                                                                                                                                                                                                                    | Total |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----- |
| ⏳ **MO-1** Formulasi matematis             | ✅ 1.1 Skenario, satuan, semantik waktu, asumsi (4, L) · ✅ 1.2 ⭐ Model A CVRPTW (6, L) · ✅ 1.3 Contoh hitung tangan feasible + infeasible (4, L) · 1.4 ⭐ Model B multi-trip + pemecahan demand (6, L) · 1.5 ⭐ Model C/D, lower bound holding (8, L) · 1.6 Review dan `docs/mathematics/mealops/` (3, L) | 31    |
| **MO-2** Data sintetis dan kontrak (Python) | 2.1 Skema instans: JSON Schema + Pydantic (5, T) · 2.2 Generator ber-seed dengan `numpy.random.Generator` (6, L) · 2.3 Fixture, instans Solomon + BKS (5, L)                                                                                                                                                 | 16    |
| **MO-3** Validator independen (Python)      | 3.1 Representasi solusi dan decoder (5, L) · 3.2 Feasibility checker dengan laporan pelanggaran terstruktur (8, L) · 3.3 Objektif/metrik + property test dengan Hypothesis (6, L)                                                                                                                            | 19    |
| **MO-4** Core dan harness benchmark         | 4.1 Crate `mealops-core`: model instans/solusi, serde, binding PyO3 (6, T) · 4.2 Runner multi-seed, anggaran, perekaman environment (5, T) · 4.3 ⭐ Wilcoxon signed-rank: implementasi sendiri, verifikasi terhadap SciPy (6, L)                                                                             | 17    |

**Fase 1 — Routing dan metaheuristik di Rust (~156 jam)**

| Milestone                                  | Sub-milestone (jam, mode)                                                                                                                                                                                                                | Total |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| **MO-5** Baseline konstruktif              | 5.1 Nearest neighbor yang sadar jendela waktu (6, L) · 5.2 ⭐ Insertion Solomon I1 dan regret insertion (9, L) · 5.3 Benchmark (3, L)                                                                                                    | 18    |
| **MO-6** Verifikasi tanpa solver eksternal | 6.1 ⭐ Split sebagai shortest path pada DAG: prototipe Python → Rust (7, L) · 6.2 ⭐ Solver exact enumerasi + branch-and-bound (8, L) · 6.3 Lower bound analitis dan Solomon BKS (5, L)                                                  | 20    |
| **MO-7** Local search bersama              | 7.1a Operator relocate, swap, 2-opt*, or-opt (6, L) · 7.1b ⭐ Evaluasi delta dengan forward time slack (6, L) · 7.2 VND (4, L)                                                                                                           | 16    |
| **MO-8** ALNS                              | 8.1 ⭐ Operator destroy dan repair (8, L) · 8.2 ⭐ Bobot adaptif dan penerimaan Simulated Annealing: rantai Markov, jadwal pendinginan (8, L) · 8.3 Benchmark dan ablation (6, L)                                                        | 22    |
| **MO-9** GA memetic                        | 9.1 ⭐ Giant tour, Split, crossover OX (8, L) · 9.2 Seleksi, mutasi, local search pada offspring (8, L) · 9.3 Manajemen diversitas ala HGS; penalti vs repair (8, L) · 9.4 Paralelisme rayon yang reprodusibel, tuning, benchmark (6, L) | 30    |
| **MO-WS** Walking skeleton                 | WS.1 Go API → antrean → Python worker → `mealops-core`, deploy ke VPS (6, T) · WS.2 Peta rute di Next.js (8, Md)                                                                                                                         | 14    |
| **MO-10** Profiling dan perbandingan       | 10.1 Profiling Rust: criterion, flamegraph, alokasi di hot loop (8, T) · 10.2 ⭐ ALNS vs GA vs baseline: Wilcoxon berpasangan (4, L)                                                                                                     | 12    |
| **MO-11** Multi-trip                       | 11.1 Pembentukan trip (5, L) · 11.2 ⭐ Penjadwalan trip ke kendaraan (10, L) · 11.3 Perluasan validator, ALNS, GA; benchmark (9, L)                                                                                                      | 24    |

**Fase 2 — Produksi, integrasi, dan robustness (~78 jam)**

| Milestone                              | Sub-milestone (jam, mode)                                                                                                                                                                                                                                                              | Total |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| **MO-12** Penjadwalan produksi         | 12.1 Model batch satu lini (6, L) · 12.2 Lini paralel, baseline EDD (8, L) · 12.3 ⭐ Penjadwalan eksak instans kecil: programa dinamis/enumerasi (8, L)                                                                                                                                | 22    |
| **MO-13** Integrasi produksi + routing | 13.1 Release date dan decoder produksi (8, L) · 13.2 Constraint holding, lower bound infeasibility (8, L) · 13.3a ⭐ Pendekatan sekuensial vs iteratif (7, L) · 13.3b ⭐ Pendekatan terintegrasi dan perbandingan (7, L) · 13.4 Integrasi ke ALNS dan GA, ablation, laporan MVP (6, L) | 36    |
| **MO-14** Simulasi Monte Carlo         | 14.1 ⭐ Model ketidakpastian; simulator eksekusi rencana di Rust (8, L) · 14.2 ⭐ Estimator, interval Wilson, ukuran sampel, common random numbers di Python (6, L) · 14.3 Pemilihan rencana robust dari solusi elite, laporan (6, L)                                                  | 20    |

### 7.3 DengueSim — MVP (~149 jam)

| Milestone                 | Sub-milestone (jam, mode)                                                                                                                                                                                                                                                     | Total |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| **D1** Riset dan data     | 1.1 ⭐ Literatur: model Ross–Macdonald hingga SEIR–SEI, konteks kebijakan (5, L) · 1.2 Ketersediaan data kasus dan iklim; pilih wilayah studi (5, L) · 1.3 Ingest dan pembersihan data di Python (6, L)                                                                       | 16    |
| **D2** Formulasi model    | 2.1 ⭐ SIR → SEIR → SEIR–SEI: asumsi, satuan, kompartemen (6, L) · 2.2 ⭐ Ekuilibrium, stabilitas, R₀ via next-generation matrix (8, L) · 2.3 Forcing iklim: parameter sebagai fungsi suhu/hujan (5, L) · 2.4 `docs/mathematics/dengue/` (2, L)                               | 21    |
| **D3** Solver ODE         | 3.1 ⭐ Euler dan RK4 di Python: galat dan orde konvergensi; validasi terhadap `solve_ivp` (7, L) · 3.2 ⭐ RK45 adaptif (Dormand–Prince) di Rust (9, L) · 3.3 Binding PyO3, test oracle, uji konservasi populasi (4, L)                                                        | 20    |
| **D4** Kalibrasi Bayesian | 4.1 ⭐ Likelihood (Poisson/Negative Binomial, under-reporting) dan prior (6, L) · 4.2 ⭐ Metropolis–Hastings di Rust (8, L) · 4.3 ⭐ Diagnosa: trace, R-hat, ESS, posterior predictive (ArviZ) (7, L) · 4.4 Identifiabilitas dan parameter recovery pada data sintetis (5, L) | 26    |
| **D5** Kontrol optimal    | 5.1 ⭐ Kalkulus variasi, prinsip maksimum Pontryagin, Hamiltonian, persamaan adjoint (8, L) · 5.2 ⭐ Forward–backward sweep di Rust (9, L) · 5.3 Skenario anggaran dan analisis sensitivitas (5, L)                                                                           | 22    |
| **D6** Simulator WASM     | 6.1 Target WASM dari crate yang sama, pola LAB-ADR-015 (5, T) · 6.2 UI simulator dengan slider parameter (8, Md)                                                                                                                                                              | 13    |
| **D7** Aplikasi           | 7.1 Go API skenario + job kalibrasi/kontrol (6, T) · 7.2 Dashboard: kurva epidemi, peta risiko (10, Md) · 7.3 Deploy (3, T)                                                                                                                                                   | 19    |
| **D8** LLM dan case study | 8.1 Penjelasan skenario dengan cek kesetiaan angka (6, L) · 8.2 Laporan case study (6, L)                                                                                                                                                                                     | 12    |

### 7.4 Harga Pangan — MVP (~140 jam)

| Milestone                       | Sub-milestone (jam, mode)                                                                                                                                                                                                                                             | Total |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| **P1** Riset dan data           | 1.1 ⭐ Dinamika harga pangan, kebijakan stok penyangga dan operasi pasar (4, L) · 1.2 Sumber data; pilih komoditas dan wilayah (4, L) · 1.3 Pipeline ingest terjadwal + TimescaleDB (6, T) · 1.4 Pembersihan, data hilang, analisis eksploratif (5, L)                | 19    |
| **P2** Fondasi stokastik        | 2.1 ⭐ Random walk, stasioneritas, proses AR, log-return (6, L) · 2.2 ⭐ Musiman dan efek hari besar bergeser (Ramadan/Lebaran) (5, L)                                                                                                                                | 11    |
| **P3** State-space dan Kalman   | 3.1 ⭐ Model state-space: local level + musiman (6, L) · 3.2 ⭐ Penurunan Kalman filter dari conditioning Gaussian; smoother RTS (7, L) · 3.3 Implementasi Rust; validasi terhadap statsmodels (8, L) · 3.4 ⭐ Estimasi MLE via prediction-error decomposition (6, L) | 27    |
| **P4** Regime switching         | 4.1 ⭐ Rantai Markov dan model Markov-switching (5, L) · 4.2 ⭐ Filter Hamilton dan smoother Kim di Rust (8, L) · 4.3 Estimasi, validasi terhadap statsmodels, sinyal peringatan dini (6, L)                                                                          | 19    |
| **P5** Monte Carlo dan prediksi | 5.1 Simulasi jalur harga, interval prediksi (5, L) · 5.2 Backtesting rolling-origin: MAPE, CRPS, coverage interval (6, L)                                                                                                                                             | 11    |
| **P6** Kebijakan stok penyangga | 6.1 ⭐ MDP dan persamaan Bellman (6, L) · 6.2 ⭐ Value iteration di Rust, diskretisasi state (8, L) · 6.3 Evaluasi kebijakan via simulasi vs aturan ambang sederhana (6, L)                                                                                           | 20    |
| **P7** Aplikasi                 | 7.1 Go API harga, sinyal, job harian (6, T) · 7.2 Dashboard: grafik, peta disparitas, panel peringatan, simulator kebijakan (12, Md) · 7.3 Deploy + ingest terjadwal di VPS (3, T)                                                                                    | 21    |
| **P8** LLM dan case study       | 8.1 Ringkasan kondisi harga dengan cek kesetiaan angka (6, L) · 8.2 Laporan case study (6, L)                                                                                                                                                                         | 12    |

### 7.5 L-Final — Penutup lab (~6 jam)

| Sub-milestone (jam, mode)                                                                                                |
| ------------------------------------------------------------------------------------------------------------------------ |
| LF.1 Halaman depan lab portal dan indeks case study (4, Md) · LF.2 Review arsitektur lintas proyek dan README lab (2, L) |

### 7.6 MealOps — Pasca-MVP (~229 jam, setelah ketiga MVP selesai)

| Fase                           | Milestone (sub-milestone)                                                                                                                                                                                                                                                                                                                                                  | Total     |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| **F3** Perencanaan sumber daya | MO-15 Ukuran armada (15.1 armada minimum 5, L · 15.2 kurva biaya vs armada 5, L) · MO-16 Tenaga kerja (16.1 kapasitas 5, L · 16.2 ⭐ shift sebagai set covering 10, L · 16.3 durasi vs jumlah staf 6, L) · MO-17 Optimizer terintegrasi (17.1a/b dekomposisi 6+6, L · 17.2a/b ⭐ front Pareto, NSGA-II 6+6, L)                                                             | 55        |
| **F4** Aplikasi                | MO-18 Backend Go (18.1 domain, pgx + sqlc, goose 10, T · 18.2 auth/RBAC dari paket bersama 8, T · 18.3 snapshot, OpenAPI 8, T) · MO-19 Job lanjutan: cancel, retry, SSE (6, T) · MO-20 Dashboard (20.1 master data 10, Md · 20.2 peta rute 10, Md · 20.3 Gantt 10, Md · 20.4 robustness 8, Md)                                                                             | 70        |
| **F5** Lanjutan                | MO-21 OSRM + waktu tempuh bergantung waktu (10, T · 8, L) · MO-22 Kebijakan dan indikator (6+6, L) · MO-23 What-if dan re-optimasi inkremental (8, L · 6+6, L) · MO-24 LLM (24.1 ⭐ penjelasan 10, L · 24.2a/b ⭐ what-if tool calling 7+7, L · 24.3 ⭐ evaluasi 8, L · 24.4 RAG opsional 10, T) · MO-25 Backup off-site, observability, case study (4, T · 6, T · 6+6, L) | 104 (+10) |

## 8. Timeline

### 8.1 Ringkasan jam

Alokasi: **10–15 jam per minggu**, dengan buffer 20%.

| Tahap              | Jam inti | Dengan buffer | 10 jam/minggu | 15 jam/minggu |
| ------------------ | -------: | ------------: | ------------: | ------------: |
| L0 Fondasi lab     |       59 |            71 |      7 minggu |      5 minggu |
| MealOps MVP        |      317 |           380 |     38 minggu |     25 minggu |
| DengueSim MVP      |      149 |           179 |     18 minggu |     12 minggu |
| Harga Pangan MVP   |      140 |           168 |     17 minggu |     11 minggu |
| L-Final            |        6 |             7 |      1 minggu |      1 minggu |
| **Total tiga MVP** |  **671** |       **805** | **81 minggu** | **54 minggu** |
| MealOps pasca-MVP  |      229 |           275 |    +28 minggu |    +19 minggu |

### 8.2 Kalender (mulai Senin, 2 November 2026)

| Tahap            | Dengan 15 jam/minggu     | Dengan 10 jam/minggu      |
| ---------------- | ------------------------ | ------------------------- |
| L0 Fondasi lab   | 2 Nov – 6 Des 2026       | 2 Nov – 20 Des 2026       |
| MealOps MVP      | 7 Des 2026 – 30 Mei 2027 | 21 Des 2026 – 12 Sep 2027 |
| DengueSim MVP    | 31 Mei – 22 Agu 2027     | 13 Sep 2027 – 16 Jan 2028 |
| Harga Pangan MVP | 23 Agu – 7 Nov 2027      | 17 Jan – 14 Mei 2028      |
| L-Final          | 8 – 14 Nov 2027          | 15 – 21 Mei 2028          |

**Urutan:** L0 → MealOps MVP → DengueSim → Harga Pangan → L-Final → MealOps pasca-MVP. MealOps MVP adalah tahap terpanjang. Bila motivasi atau visibilitas portofolio mulai menjadi masalah, DengueSim bisa disisipkan setelah MO-WS, karena saat itu pola empat lapisan sudah terbukti berjalan end-to-end.

### 8.3 Ritme mingguan

- 2 sesi hari kerja × 1,5–2 jam: teori, formulasi, review (cocok untuk sub-milestone ⭐ dan Mode Latihan).
- 1 sesi akhir pekan × 5–8 jam: implementasi, setup, debugging (cocok untuk Mode Tuntun).
- Satu sub-milestone biasanya selesai dalam 1–3 sesi.
- Setiap 4–6 minggu, bandingkan jam aktual dengan estimasi di `PROGRESS.md` dan kalibrasi ulang timeline. (Catatan per L0.8: L0.1–L0.8 selesai dalam ~20 jam dari estimasi 39 jam. Sub-milestone Mode Tuntun konsisten di bawah estimasi; sub-milestone Mode Latihan berikutnya belum terkalibrasi. Catatan per L0.9a: sub-milestone Mode Latihan pertama memakan ~20 jam dari estimasi 9 (~2×); estimasi Mode Latihan di §7.2–7.4 kemungkinan terlalu rendah dan dikalibrasi ulang setelah L0.10. Catatan per L0.9b: ~1 jam dari estimasi 1. Catatan per L0.10: 6 jam dari estimasi 6; Mode Latihan total 27 jam dari estimasi 16 (~1,7×, terutama dari L0.9a); kalibrasi ulang §7.2 setelah MO-1. Catatan per MO-1.1: 3 jam dari estimasi 4; Mode Latihan total 30 jam dari estimasi 20 (~1,5×). Catatan per MO-1.2: ~4 jam dari estimasi 6; Mode Latihan total 34 jam dari estimasi 26 (~1,3×). Catatan per MO-1.3: ~2 jam dari estimasi 4; Mode Latihan total 36 jam dari estimasi 30 (~1,2×).)

## 9. Keputusan Terbuka

1. ~~**Struktur repo:** monorepo lab vs repo per proyek.~~ **Diputuskan di L0.2: monorepo** (LAB-ADR-008).
2. ~~**Go API:** satu binary per proyek vs satu API untuk seluruh lab.~~ **Diputuskan di L0.2: satu binary per proyek** (LAB-ADR-008).
3. ~~**Kontrak job Go ↔ Python:** JSON Schema vs Protobuf.~~ **Diputuskan di L0.4: JSON Schema 2020-12** per `<kind>.v<N>` (LAB-ADR-010).
4. ~~**Antrean job:** implementasi sendiri vs pustaka siap pakai.~~ **Diputuskan di L0.4: implementasi sendiri** (LAB-ADR-010).
5. **Penyedia LLM** dan batas biaya bulanan.
6. **Wilayah studi DengueSim** dan ketersediaan datanya. Diputuskan di D1.2.
7. **Komoditas dan wilayah Harga Pangan.** Diputuskan di P1.2.
8. **Nama final** proyek Harga Pangan.
9. Keputusan terbuka MealOps v3.1 §20 nomor 1–7, 10, 11, dan 14 tetap berlaku. Nomor 8–9 dan 12 sudah atau akan diputuskan di L0 (Docker Engine di WSL sudah dipilih). Nomor 13 menjadi dukungan debugger per bahasa di Zed, dievaluasi di L0.1.
10. ~~**Slot job berat lintas proyek** (§4.4 nomor 3).~~ **Diputuskan di L0.8: cgroup systemd `lab-workers.slice` (`CPUQuota=100%`) sebagai induk semua container worker** (LAB-ADR-014); batas sumber daya dipaksakan kernel, tanpa kode koordinasi.

## 10. Konteks Singkat untuk Sesi Berikutnya

> Kita membangun **Applied Math Lab**: tiga software portofolio berbasis matematika terapan untuk masalah Indonesia, yaitu **MealOps** (optimasi dapur massal dan distribusi makanan perishable: VRP terintegrasi penjadwalan produksi dengan batas holding time; ALNS + GA memetic; Monte Carlo), **DengueSim** (SEIR–SEI; R₀; MCMC; kontrol optimal Pontryagin), dan **Harga Pangan** (state-space + Kalman; regime switching; value iteration untuk stok penyangga). **Arsitektur seragam:** Next.js (satu lab portal) → Go API (auth, CRUD, orkestrasi job, AI gateway) → antrean job PostgreSQL (`SKIP LOCKED`) → Python worker (modelling, validasi, analisis) → Rust core via PyO3/maturin (hot loop; bisa juga WASM). Go tidak memanggil Rust secara langsung. **Jembatan (LAB-ADR-009):** core Rust murni + crate binding `-py` (PyO3 abi3, rust-numpy, `py.detach`), stub `.pyi`, `just py-ext` sebelum pytest, toleransi oracle dari analisis galat. **WASM (LAB-ADR-015):** crate binding `-wasm` + `wasm-bindgen-cli` dipin (`just wasm`, tanpa wasm-pack); glue di `apps/web/src/wasm/`, biner di `public/wasm/` di luar bundler; pembungkus bertipe di `src/lib/`; demo `/wasm-demo`. **Antrean (LAB-ADR-010):** implementasi sendiri, `lab_jobs` + paket Go `jobqueue` (`Enqueue` dalam `pgx.Tx`) + paket Python `lab_worker`; lock untuk klaim, lease + fencing `attempts` untuk menjalankan; NOTIFY petunjuk, tabel kebenaran; trigger NOTIFY `lab_job_progress` saat status/progres berubah; heartbeat/reaper at-least-once; watchdog timeout; worker crash-only; kontrak JSON Schema `contracts/jobs/<kind>.v<N>.schema.json`. **API + SSE (LAB-ADR-011):** Go `net/http` + `ServeMux`, pola `run`, healthz (liveness) / readyz (DB); SSE berbasis snapshot dengan satu koneksi LISTEN per proses (hub), heartbeat 15 s + polling cadangan; portal `apps/web` dengan rewrite `/api` hanya di dev; walking skeleton `services/hello/{api,worker}` + halaman `/hello`. **Container (LAB-ADR-012):** Dockerfile multi-stage per layanan dengan konteks root repo (Go → distroless + subperintah `healthcheck`; worker → wheel maturin via `uv sync --no-editable`, runtime hanya `.venv`; web → Next.js standalone); `infrastructure/compose.yaml` dengan service `migrate` sekali jalan dan Caddy pemegang routing `/api` (`just stack-up`, `:8000`). **CI (LAB-ADR-013):** satu workflow `ci.yml` — path filter → matrix dinamis `just ci-<bahasa>` (gabungannya = `just check`) → image ke GHCR dari `main` (tag `sha-<7>` + `main`, package publik) → gerbang `ci-ok`; action dipin ke SHA + Dependabot; `main` dilindungi ruleset (kerja di branch, PR, squash merge). **VPS + deploy (LAB-ADR-014):** Hostinger Ubuntu 24.04, `https://applied-math-lab.portfolio-bagas.tech`; SSH kunci saja tanpa root, UFW + firewall hPanel (hanya Caddy punya `ports:`), unattended-upgrades + reboot 03:00 WIB, swap 2 GB; `infrastructure/compose.vps.yaml` (image GHCR `sha-<7>`) di `/opt/applied-math-lab`; merge ke `main` → job `retag` (tag lengkap untuk image tak berubah) → job `deploy` (environment `production`) → SSH user `deploy` yang dikunci forced command `lab-deploy` (SHA wajib di riwayat `main`, konfigurasi dari commit yang sama, pull → up --wait → verifikasi ID image); rollback = deploy SHA lama; semua worker di `lab-workers.slice` (≤ 1 vCPU gabungan, dipaksakan kernel); uptime dipantau monitor eksternal. Pola algoritma: prototipe di Python → port ke Rust → Python sebagai test oracle; di MealOps, validator Python memeriksa semua solusi Rust secara independen. **Repo:** monorepo `github.com/Adrianus-Bagas/applied-math-lab` (LAB-ADR-008): satu `go.mod` di root, workspace Cargo/uv/pnpm, toolchain dipin, `just check` = pemeriksaan CI. **Infra:** VPS 2 vCPU / 8 GB / 100 GB NVMe / 8 TB bandwidth (CPU adalah batas utama; komputasi berat offline, hasil disajikan online), Docker Compose, Caddy, PostgreSQL 18 + PostGIS + TimescaleDB, CI GitHub Actions → GHCR → deploy otomatis. **Dev:** WSL Ubuntu, Docker Engine di WSL, Zed; alias SSH `lab-vps`. **Model matematis MealOps** mengikuti `PROJECT_CONTEXT` MealOps v3.1 §8–10 (di Project knowledge: `claude/PROJECT_CONTEXT_MEALOPS_v3.1.md`); semantik waktu, satuan, dan asumsi yang sudah ditetapkan ada di `docs/mathematics/mealops/model.md` (waktu menit bulat sejak 00:00, `T_j ≤ d_j`, holding = waktu konsumsi − selesai masak; Model A di §2: formulasi dua-indeks, jendela efektif `a'_j`/`d'_j`, `q_j ≥ 1`, pemeriksaan rute lewat jadwal tercepat; contoh hitung tangan H5 dan tiga tingkat kegagalan di §3). **Kolaborasi:** _Tuntun_ (setup environment, proyek, deployment: jelaskan alasan dengan bahasa sederhana, beri langkah dan file lengkap), _Latihan_ (logika bisnis dan matematika: konsep dan penurunan dituntun lengkap → tugas kecil dengan kerangka, sebagian kode, dan tes → pengguna implementasi → review), _Mandiri_ (frontend). Bahasa diajarkan just-in-time; komentar kode dalam Bahasa Indonesia; status roadmap ditandai ✅/⏳; `PROGRESS.md` diperbarui dan PR di-squash merge di akhir setiap thread. **Roadmap:** L0 → MealOps MVP → DengueSim → Harga Pangan → L-Final → MealOps pasca-MVP; satu sub-milestone (≤ 10 jam) per thread; 10–15 jam/minggu. AI hanya LLM: mengusulkan dan menjelaskan, solver dan validator yang memutuskan.
