# LAB-ADR-015: Rust → WASM di portal

- **Status:** Diterima
- **Tanggal:** 2026-11-11
- **Sub-milestone:** L0.11
- **Terkait:** LAB-ADR-004 (core murni), LAB-ADR-006 (satu crate, dua target), LAB-ADR-009 (pola crate binding), LAB-ADR-012 (image web), LAB-ADR-013 (CI)

## Konteks

Simulasi interaktif (DengueSim, Kalman filter Harga Pangan, instans MealOps kecil) harus berjalan di browser pengunjung, karena CPU VPS adalah batas utama (`PROJECT_CONTEXT` §4.4). LAB-ADR-006 sudah menetapkan bahwa crate Rust yang sama dipakai untuk Python dan WASM, tetapi belum ada jalur build yang terbukti dari crate sampai halaman portal di produksi. Portal memakai Next.js 16 dengan Turbopack dan output standalone. Saat keputusan ini diambil, Turbopack belum punya cara yang mapan untuk mem-bundle file `.wasm` hasil wasm-bindgen: ada laporan build gagal dan regresi file tracing di 16.4 yang mengenai output standalone.

## Keputusan

1. **Crate binding terpisah `<nama>-wasm`**, mengikuti pola `-py` (LAB-ADR-009): `cdylib`, `test = false`, hanya mengonversi tipe. Matematika dan test-nya tetap di crate core. Crate pertama: `packages/rust/lab-numerics-wasm`.
2. **`cargo build` + `wasm-bindgen-cli`, tanpa wasm-pack.** wasm-pack membungkus kedua langkah itu dan menambah pembuatan paket npm yang tidak diperlukan di monorepo ini. Resep `just wasm` menjalankan keduanya; `just wasm-tools` memasang CLI.
3. **Versi wasm-bindgen dipin persis** (`=0.2.130`) di tiga tempat yang harus sama: `[workspace.dependencies]`, `wasm_bindgen_version` di `justfile`, dan `ARG WASM_BINDGEN_VERSION` di `apps/web/Dockerfile`. Bila tidak sama, CLI menolak bekerja dengan pesan versi tidak cocok.
4. **Profil Cargo `wasm-release`** (`opt-level = "s"`, LTO, satu codegen unit). Profil `release` tidak diubah karena dipakai wheel Python.
5. **Bundler tidak menyentuh file `.wasm`.** CLI dijalankan dengan `--target web --omit-default-module-path`. Glue JS dan `.d.ts` masuk ke `apps/web/src/wasm/<nama>/` dan diimpor seperti modul biasa; biner `.wasm` masuk ke `apps/web/public/wasm/` dan URL-nya diberikan eksplisit ke `init({ module_or_path })`. Keduanya artefak build: tidak di-commit, dikecualikan dari prettier, eslint, dan konteks Docker.
6. **Satu pembungkus bertipe per modul** di `apps/web/src/lib/` (contoh: `lab-numerics.ts`): memuat modul sekali per tab (promise di-cache, boleh dicoba ulang bila gagal) dan mengubah keluaran mentah menjadi tipe yang nyaman. Komponen tidak mengimpor glue secara langsung.
7. **Konvensi tipe di perbatasan:** `i64` dikembalikan sebagai `BigInt` (`BigInt64Array`) agar tetap eksak di atas 2⁵³; slice `&[f64]` disalin sekali dari `Float64Array`; parameter hitungan memakai `u32`/`usize` agar pemanggil JS cukup memakai `number`.
8. **Test perbatasan di vitest**, dengan byte `.wasm` dibaca dari disk dan diberikan ke `init`. Rute halaman tidak boleh bernama sama dengan folder di `public/` (demo memakai `/wasm-demo`).
9. **Build:** `lint-web`, `test-web`, dan `dev-web` bergantung pada resep `wasm`. Di CI, job `check (web)` memasang toolchain Rust dan `wasm-bindgen-cli`, dan perubahan path Rust ikut memicu web. Image `web` mendapat tahap `wasm` (Debian slim + rustup + CLI) yang hasilnya disalin ke tahap build Next.js; filter image `web` mencakup path Rust. Smoke test deploy memeriksa `/wasm-demo` dan file `.wasm`.

## Alternatif yang ditolak

- **wasm-pack.** Lapisan tambahan dengan versi sendiri, sementara yang dibutuhkan hanya dua perintah.
- **Mengimpor `.wasm` lewat bundler** (`--target bundler`, atau `new URL(..., import.meta.url)`). Bergantung pada perilaku Turbopack yang masih berubah antarversi.
- **Meng-commit hasil build.** Artefak biner di git, dan mudah tertinggal dari kode Rust.
- **Menambah fitur `wasm` di crate core.** Mencampur dependensi JS ke crate yang harus murni (LAB-ADR-004).

## Konsekuensi

- **(+)** Fungsi Rust yang sama dipakai worker Python dan browser; tidak ada implementasi ganda.
- **(+)** Perilaku pemuatan WASM tidak bergantung pada versi bundler.
- **(+)** Versi yang tidak selaras gagal dengan pesan jelas, tidak lolos diam-diam.
- **(−)** `just check` dan job `check (web)` kini membutuhkan toolchain Rust dan `wasm-bindgen-cli`.
- **(−)** Perubahan Rust apa pun memicu check web dan membangun ulang image `web`.
- **(−)** Nama file `.wasm` di `public/` tidak ber-hash; pembaruan mengandalkan revalidasi cache browser. Perlu ditinjau bila modul membesar.
- **(−)** Perintah build tertulis dua kali (`justfile` dan Dockerfile web) dan harus dijaga sama.
- **(−)** Slice disalin ke memori WASM pada setiap panggilan; untuk data besar yang dipanggil berulang perlu desain lain.

## Verifikasi

- Dari Node: `sqrt2Convergents(5)` memberi `1/1, 3/2, 7/5, 17/12, 41/29` sebagai `BigInt`; `sqrt2Convergents(1000)` berhenti di 50 konvergen; `meanVariance([1, 2, 3, 4], 0)` = `[2.5, 1.25]`; data kosong memberi `undefined`.
- Test vitest: identitas Pell p² − 2q² = ±1 eksak untuk 50 konvergen; hasil WASM dan Welford versi JS sepakat dalam 1e-12.
- `just check` hijau; halaman `/wasm-demo` berjalan di `next dev` dan di stack container lokal (`:8000`).
- CI pull request hijau, termasuk `check (web)` dan `image (web)` dengan tahap Rust.

## Pertanyaan terbuka

- Kompresi brotli dan `wasm-opt` untuk modul yang lebih besar (D6.1).
- Web Worker untuk komputasi yang lebih lama dari satu frame (D6.1).
- Nama file ber-hash atau header cache untuk `.wasm` bila ukuran modul mulai berarti.
