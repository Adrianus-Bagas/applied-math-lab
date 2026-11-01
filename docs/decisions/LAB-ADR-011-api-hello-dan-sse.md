# LAB-ADR-011: Go API hello, progres via SSE, dan portal Next.js

- **Status:** Diterima
- **Tanggal:** 2026-11-01
- **Sub-milestone:** L0.5
- **Terkait:** LAB-ADR-003, LAB-ADR-008, LAB-ADR-010

## Konteks

L0.5 membangun lapisan yang menghubungkan browser dengan antrean job: Go API pertama (`services/hello/api`) dan kerangka lab portal (`apps/web`). Pola yang ditetapkan di sini akan disalin ke API ketiga proyek, jadi keputusannya dicatat sekarang.

Kebutuhan utamanya: pengguna mengajukan job, lalu melihat progresnya secara langsung tanpa polling dari browser, dengan sumber daya VPS yang kecil (`max_connections` ≈ 30, §4.4).

## Keputusan

### Go API

1. **Pustaka standar.** `net/http` dengan `ServeMux` (pola `"METODE /path/{id}"`, Go ≥ 1.22) dan `log/slog`. Tidak ada router atau framework pihak ketiga.
2. **Pola `run`.** `main` hanya menyiapkan sinyal (`signal.NotifyContext`) lalu memanggil `run(ctx, getenv) error`. Ini memberi satu titik `os.Exit` (gocritic `exitAfterDefer`) dan membuat kode bisa diuji.
3. **Timeout server eksplisit** (`ReadHeaderTimeout` 5 s, `ReadTimeout` 10 s, `WriteTimeout` 15 s, `IdleTimeout` 60 s) dan **graceful shutdown** 10 s.
4. **`/healthz` = liveness** dan tidak menyentuh DB. **`/readyz` = readiness** dengan ping DB. Gangguan DB tidak boleh memicu restart API secara berantai.
5. **Body `POST` adalah payload job** dan divalidasi `jobqueue.Registry` terhadap JSON Schema. API tidak menduplikasi skema. Pemetaan error: JSON rusak 400, lebih dari 64 KiB 413, melanggar skema 422, lainnya 500 (termasuk `ErrUnknownKind`, yang merupakan bug konfigurasi). Respons sukses `202 Accepted` + `Location`.
6. **Enqueue di dalam transaksi** (`pgx.BeginFunc`), meskipun hello belum punya data domain. Polanya disiapkan untuk snapshot + enqueue atomik di MealOps.
7. **Bentuk error seragam** `{"error": "..."}`.

### Server-Sent Events

8. **Event berupa snapshot**, bukan delta. Setiap event `job` berisi status lengkap hasil baca ulang tabel (_NOTIFY petunjuk, tabel kebenaran_, LAB-ADR-010). Reconnect EventSource langsung mendapat status terkini, jadi tidak perlu replay `Last-Event-ID`.
9. **Satu koneksi LISTEN per proses** (hub, di luar pool) yang menyebarkan sinyal ke channel per klien. Channel ber-buffer 1 dengan kirim non-blocking ("yang terbaru menang"); penggabungan sinyal aman karena event berupa snapshot. Setelah (re)LISTEN, semua pelanggan diminta membaca ulang.
10. **Subscribe sebelum membaca snapshot awal**, untuk menutup celah perubahan yang terlewat.
11. **Heartbeat 15 s** merangkap polling cadangan: hub membaca ulang tabel, lalu mengirim snapshot bila berubah atau komentar `: ping` bila tidak.
12. **Deadline per koneksi:** deadline baca dihapus dan deadline tulis 10 s dipasang ulang per event lewat `http.ResponseController`. Timeout global server tetap berlaku untuk endpoint lain.
13. **Stream ditutup server saat status terminal.** Klien wajib memanggil `EventSource.close()` saat menerima status terminal agar tidak reconnect tanpa henti. Saat shutdown, hub berhenti dan semua stream ikut selesai, sehingga `Shutdown` tidak tertahan.
14. **NOTIFY `lab_job_progress` dikirim oleh trigger** `lab_jobs_progress_notify` (migrasi `jobqueue` `00002`), `AFTER UPDATE OF status, progress` dengan `WHEN ... IS DISTINCT FROM`. Setiap jalur yang mengubah status atau progres (worker, reaper, cancel di masa depan, `psql`) otomatis memberi tahu; heartbeat tidak memicu notifikasi. `pg_notify` manual di `lab_worker` dihapus.

### Portal Next.js

15. **`apps/web`** (App Router, TypeScript, Tailwind, `src/`) menjadi anggota pnpm workspace dengan satu lockfile di root.
16. **Dev: rewrite `/api/hello/*` → `HELLO_API_URL`** (default `http://127.0.0.1:8080`), meniru Caddy di produksi (satu origin, tanpa CORS). `compress: false`: kompresi diserahkan ke Caddy, dan ini mencegah buffering SSE. Terverifikasi dengan `curl -N` lewat :3000.
17. **Kontrak TS ditulis tangan** untuk hello (`Job`, `HelloApiError` membawa status HTTP). **OpenAPI + oapi-codegen/openapi-typescript ditunda** ke API domain pertama (MO-WS/MO-18).
18. **Vitest** dipasang sebagai lapisan test keempat (`just test-web`); `just lint-web` menjalankan ESLint dan `tsc --noEmit`.

## Alternatif yang ditolak

- **Satu koneksi LISTEN per klien SSE:** menghabiskan `max_connections` dengan cepat.
- **Event delta + replay `Last-Event-ID`:** butuh log event tersimpan; tidak sepadan karena status job kecil.
- **`pg_notify` di setiap fungsi Python yang mengubah status:** mudah terlupa di jalur baru dan harus diulang di setiap bahasa.
- **WebSocket:** komunikasinya hanya satu arah (server → browser); SSE lebih sederhana, berjalan di atas HTTP biasa, dan reconnect otomatis.
- **CORS untuk dev:** kode yang tidak terpakai di produksi.
- **Router pihak ketiga (chi, echo):** `ServeMux` bawaan sudah mendukung metode dan wildcard.

## Konsekuensi

- Setiap API proyek menyalin pola ini: `run`, healthz/readyz, hub SSE, dan pemetaan error.
- Trigger adalah logika di DB; keberadaannya didokumentasikan di sini dan di komentar migrasi.
- Caddy (L0.8) harus meneruskan SSE tanpa buffering dan tanpa kompresi untuk `text/event-stream`; perlu diverifikasi saat deploy.
- Build produksi Next.js (standalone) dan variabel `HELLO_API_URL` diatur di L0.6.
