# LAB-ADR-013: CI GitHub Actions dan publikasi image ke GHCR

- **Status:** Diterima
- **Tanggal:** 2026-11-01
- **Sub-milestone:** L0.7
- **Terkait:** LAB-ADR-008 (monorepo, `just check` = CI), LAB-ADR-009 (jembatan Rust → Python), LAB-ADR-012 (image Docker)

## Konteks

Sampai L0.6, semua pemeriksaan hanya dijalankan di laptop (`just check`) dan image hanya dibangun lokal (`just stack-up`). L0.8 membutuhkan image siap tarik dari registry, dan `main` perlu dijaga agar kode yang gagal lint/test tidak pernah sampai ke VPS. Monorepo berisi empat bahasa, sehingga menjalankan semuanya di setiap perubahan boros waktu; tetapi melewatkan pemeriksaan yang relevan lebih berbahaya. Insiden rantai pasok seperti `tj-actions/changed-files` (Maret 2025) menunjukkan tag action bisa dipindahkan ke kode berbahaya.

## Keputusan

1. **Satu workflow `.github/workflows/ci.yml`** dengan empat job: `changes` → `check` (matrix) → `images` (matrix) → `ci-ok`.
2. **CI memanggil resep `just` yang sama dengan lokal.** Setiap job `check` menjalankan tepat satu resep `just ci-<bahasa>` (`ci-go`, `ci-rust`, `ci-python`, `ci-web`); gabungan keempatnya sama dengan `just check`. `setup` dipecah menjadi `setup-py` dan `setup-node`. Saat pemecahan, ditemukan dan diperbaiki dua celah: `check` sebelumnya tidak memanggil `lint-web`/`test-web`, dan mypy tidak memeriksa `services/*/worker/src`.
3. **Matrix dinamis dari path filter** (`dorny/paths-filter`). Nama filter = nama bahasa = akhiran resep. YAML anchor `&shared` (`justfile`, `ci.yml`) memicu semua bahasa; `&rustpaths` membuat perubahan Rust ikut memicu Python (binding PyO3). Prettier (Markdown/JSON/YAML) berjalan di job `web`. Anchor ditempel di dalam filter lain, bukan sebagai filter sendiri, agar namanya tidak masuk ke matrix. Matrix kosong di-skip lewat `if`. `workflow_dispatch` memeriksa semua bahasa dan membangun semua image.
4. **Gerbang `ci-ok`** (`if: always()`, gagal bila ada `failure`/`cancelled`) adalah satu-satunya _required status check_, sehingga job yang di-skip karena path filter tidak memblokir merge, sedangkan job gagal selalu memblokir.
5. **Image** (`hello-api`, `hello-worker`, `web`) memakai filter path kedua yang mencerminkan isi `COPY` tiap Dockerfile, dan baru dibangun setelah `check` lulus atau di-skip. Pull request: build saja (bukti Dockerfile valid). `main`: push ke `ghcr.io/<owner-lowercase>/applied-math-lab/<image>` dengan tag `sha-<7 karakter>` (permanen, dipakai deploy dan rollback) dan `main`. Build-arg `VERSION=sha-<7>` ke `buildinfo`. Konteks build `.` (hasil checkout, `.dockerignore` berlaku), `linux/amd64`, cache layer `type=gha` per image. Label OCI dari `docker/metadata-action` menautkan package ke repo. Package GHCR **publik** (repo publik, image tanpa secret), sehingga VPS tidak membutuhkan token registry.
6. **Toolchain dipin**, sama dengan laptop: runner `ubuntu-24.04`; Rust dari `rust-toolchain.toml` lewat `rustup toolchain install`; Go dari direktif `go` (`go-version-file`); Node dari `.node-version`; pnpm dari `packageManager`; `just` 1.59.0, `uv` 0.13.6, golangci-lint v2.15.0 di blok `env`. Cache: modul Go (setup-go), `Swatinem/rust-cache` per bahasa, cache uv, cache pnpm.
7. **Keamanan:**
   - `permissions: contents: read` di level workflow; `pull-requests: read` hanya di `changes`; `packages: write` hanya di `images`; login GHCR memakai `GITHUB_TOKEN`.
   - `persist-credentials: false` di setiap checkout.
   - Nilai ekspresi `${{ }}` masuk skrip lewat `env:`, tidak disisipkan langsung (mencegah injeksi skrip).
   - Semua action dipin ke commit SHA penuh dengan komentar versi (`pinact run -u`), diperbarui Dependabot (`github-actions`, mingguan, _cooldown_ 7 hari, satu grup PR).
   - Pengaturan repo: izin default `GITHUB_TOKEN` read-only.
   - `concurrency` membatalkan run lama di branch/PR yang sama, kecuali di `main`.
8. **Ruleset branch `main`:** wajib pull request (0 approval), `ci-ok` wajib lulus, tanpa force push dan penghapusan, tanpa bypass. Alur penutupan thread menjadi branch → PR → _squash merge_.
9. **`typecheck` web = `next typegen && tsc --noEmit`.** Tipe rute Next.js (`LayoutProps`, `PageProps`) dibangkitkan ke `.next/types/`, yang tidak ada di clone bersih. Sebelumnya typecheck lokal diam-diam bergantung pada sisa `next dev`.

## Alternatif yang ditolak

- **Workflow terpisah per bahasa dengan `on.<event>.paths`.** Workflow yang tidak terpicu tidak melaporkan status, sehingga required check menggantung; selain itu muncul banyak status check yang harus didaftarkan satu per satu.
- **Matrix statis empat bahasa + `if` per step.** Tetap memakai empat runner meski hanya satu bahasa yang berubah.
- **Membangun image paralel dengan `check`.** Lebih cepat, tetapi image dari kode yang gagal test bisa sampai ke registry.
- **Hanya tag `latest`/`main`.** Tidak reprodusibel dan menyulitkan rollback.
- **Personal access token untuk GHCR.** Secret berumur panjang; `GITHUB_TOKEN` berumur satu run dan berlingkup repo.
- **Dependabot untuk semua ekosistem sekarang.** Belasan PR per minggu untuk kerangka proyek; ditunda sampai kode domain ada.

## Konsekuensi

- **(+)** `just check` hijau di laptop ⇒ CI hijau, kecuali beda environment (yang memang ingin ditangkap, contoh: `next typegen`).
- **(+)** Perubahan kecil hanya memicu bahasa dan image yang relevan; run tanpa cache: Rust ~43 s, Python ~1 min, image 1,5–2 min.
- **(+)** Isi GHCR hanya berasal dari `main` yang lulus CI; deploy L0.8 cukup menarik tag `sha-…`.
- **(−)** Daftar path di filter harus dirawat manual: proyek baru wajib menambah filter bahasa (bila perlu), filter image, dan cabang `case` Dockerfile di job `images`.
- **(−)** Di pull request, path filter membandingkan seluruh isi PR dengan `main`, bukan per commit.
- **(−)** Cache mount BuildKit di Dockerfile tidak ikut tersimpan di cache `gha`; kecepatan build CI bergantung pada urutan layer.
- **(−)** Versi `just`/`uv`/golangci-lint di `ci.yml` harus disamakan manual saat laptop di-upgrade.

## Verifikasi

- PR pertama: keempat `check` hijau setelah perbaikan `next typegen`.
- PR image: tiga `image (…)` di-build tanpa push; setelah merge, tiga package muncul di GHCR dengan tag `main` dan `sha-…`; `docker pull` anonim berhasil.
- Uji negatif (PR sengaja merusak format Go, tidak di-merge): hanya `check (go)` yang berjalan dan merah, `image (hello-api)` di-skip, `ci-ok` merah, merge terkunci.
- Push langsung ke `main` ditolak ruleset.

## Pertanyaan terbuka

- Compose VPS menarik image GHCR dengan tag `sha-…` dan log driver Docker (L0.8).
- Dependabot untuk cargo, uv, npm, gomod, dan base image Docker (saat API domain pertama).
- Opsional: `pinact run --check` atau zizmor di CI untuk menolak `uses:` yang belum dipin.
