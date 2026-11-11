# LAB-ADR-010: Antrean job dan kontrak payload

- **Status:** Diterima
- **Tanggal:** 2026-10-31
- **Sub-milestone:** L0.4
- **Menutup:** Keputusan Terbuka #3 (kontrak job) dan #4 (implementasi antrean)
- **Terkait:** LAB-ADR-002, LAB-ADR-003, LAB-ADR-004, LAB-ADR-007, LAB-ADR-009

## Konteks

Go API memasukkan job dan Python worker menjalankannya (LAB-ADR-003), hanya lewat PostgreSQL. Volume job rendah (puluhan per hari), tetapi satu job bisa berjalan menit hingga jam di VPS 2 vCPU. Yang dibutuhkan:

1. Enqueue transaksional: job tersimpan atomik bersama data domain (snapshot skenario).
2. Satu job tidak diproses dua worker sekaligus, dan worker yang mati tidak membuat job macet.
3. Payload divalidasi di kedua sisi terhadap satu kontrak.

## Keputusan

### 1. Kontrak: JSON Schema draft 2020-12, bukan Protobuf

- Satu file per jenis job dan versi: `contracts/jobs/<kind>.v<N>.schema.json`. `kind` dan versi dibaca dari nama file.
- Go memvalidasi saat enqueue (`santhosh-tekuri/jsonschema/v6`, angka via `json.Number`). Python memvalidasi ulang saat klaim (`jsonschema`); payload invalid langsung `failed` tanpa retry.
- Kontrak di-embed ke binary Go lewat paket `contracts` (`//go:embed`). Python membaca `LAB_CONTRACTS_DIR`, atau mencari `contracts/jobs` ke atas dari cwd.
- Bilangan bulat yang harus eksak lintas lapisan (seed) dibatasi `maximum: 2^53 - 1`, karena JavaScript dan decoder JSON bawaan Go memakai float64.
- Alasan: payload tersimpan sebagai JSONB yang bisa dibaca dan di-query; validasi native di Go dan Python; Protobuf menambah toolchain codegen di empat bahasa tanpa manfaat berarti pada volume ini.

### 2. Antrean: implementasi sendiri, bukan pustaka

- Pustaka matang hanya untuk satu bahasa (River di Go; Procrastinate atau PgQueuer di Python), masing-masing dengan skema tabel internal sendiri. Antrean lintas bahasa akan membuat satu sisi meniru tabel internal sisi lain.
- Implementasi kecil: paket Go `packages/go/jobqueue` (migrasi + `Enqueue`) dan paket Python `packages/python/lab-worker` (operasi antrean + loop worker).

### 3. Skema dan semantik

- Tabel `lab_jobs` (migrasi goose embedded, tabel versi terpisah `jobqueue_goose_version`). `id` = `uuidv7()` (PostgreSQL 18). `status` text + CHECK: `queued`, `running`, `succeeded`, `failed`, `cancelled`. Indeks parsial untuk job `queued` (urutan klaim) dan `running` (reaper). Constraint: job `running` wajib punya `worker_id` dan `heartbeat_at`.
- **Lock untuk mengklaim, lease untuk menjalankan.** Klaim adalah satu perintah autocommit `WITH … FOR UPDATE SKIP LOCKED … UPDATE … RETURNING`; selama berjalan, kepemilikan dicatat sebagai lease (`worker_id`, `attempts`, `heartbeat_at`), tidak sebagai transaksi terbuka.
- `attempts` naik saat klaim (crash juga terhitung, mencegah poison message) dan sekaligus menjadi **fencing token**: setiap tulisan worker memakai `WHERE id AND status='running' AND worker_id AND attempts`; 0 baris berarti lease hilang dan hasil dibuang.
- **NOTIFY adalah petunjuk, tabel adalah kebenaran.** Enqueue mengirim `pg_notify('lab_jobs', kind)` (terkirim saat commit). Worker `LISTEN` sebelum klaim pertama, mengosongkan antrean dulu, lalu menunggu NOTIFY dengan polling cadangan (default 30 detik). Progres dikirim ke kanal `lab_job_progress` (payload: id job) untuk SSE di L0.5.
- **At-least-once.** Heartbeat dari thread terpisah (default 5 detik); reaper mengembalikan lease basi (default 15 detik, rasio 3) ke `queued` atau ke `failed` bila jatah habis. Waktu heartbeat memakai `now()` server Postgres, sehingga hanya ada satu jam acuan. Handler harus idempoten; di lab ini hasil deterministik terhadap seed.
- **Timeout per percobaan.** Thread heartbeat merangkap watchdog: melewati `timeout_s`, ia mencatat `fail(kind="timeout")` lalu `os._exit(EX_TEMPFAIL)`, karena panggilan Rust yang melepas GIL tidak bisa diinterupsi. Supervisor (Docker) me-restart proses.
- **Retry:** error biasa di-retry dengan backoff eksponensial equal jitter, `delay ∈ [d/2, d]`, `d = min(cap, base·2^(k-1))`; `PermanentError` dan payload invalid langsung `failed`.
- **Crash-only:** worker tidak mencoba menyambung ulang koneksi yang putus; proses berhenti dan supervisor menyalakannya kembali. SIGTERM menghentikan loop setelah job berjalan selesai.

## Konsekuensi

- Kasus tepi (reaper, fencing, retry, timeout) menjadi tanggung jawab kita; ditutup test integrasi terhadap Postgres sungguhan (testcontainers-go dan testcontainers-python), termasuk klaim konkuren 4 thread × 50 job dan skenario worker basi dengan `worker_id` yang sama.
- Test Python mengambil skema dari file migrasi Go, sehingga hanya ada satu sumber kebenaran skema.
- Advisory lock PostgreSQL berlingkup per database, sedangkan lab memakai satu database per proyek. "Satu slot job berat untuk seluruh lab" (§4.4) belum terselesaikan oleh desain ini; dicatat sebagai keputusan terbuka untuk L0.6/L0.8.
- `services/hello/worker` menjadi worker walking skeleton lab sampai proyek pertama punya worker sendiri.
