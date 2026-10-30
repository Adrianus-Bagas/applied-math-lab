# LAB-ADR-008: Monorepo dan tooling lintas bahasa

- Status: Diterima
- Tanggal: 2026-10-30
- Sub-milestone: L0.2
- Menutup: Keputusan Terbuka #1 dan #2 (`PROJECT_CONTEXT` §9)
- Merevisi: `PROJECT_CONTEXT` §2.5 (workspace Go)

## Konteks

Lab berisi tiga proyek, masing-masing empat lapisan (Next.js, Go, Python, Rust),
dengan paket bersama per bahasa. Kontrak job menyentuh Go, Python, dan Rust
sekaligus. Satu orang mengembangkan, satu VPS menjalankan.

## Keputusan

1. **Monorepo lab.** Ketiga proyek dan paket bersama berada di satu repositori.
2. **Satu Go binary per proyek.** Isolasi kegagalan dan deploy per proyek;
   kode bersama di `packages/go`.
3. **Satu modul Go di root** (`github.com/Adrianus-Bagas/applied-math-lab`),
   bukan multi-modul dengan `go.work`. `go.work` tidak dianjurkan untuk
   di-commit, sehingga multi-modul memerlukan direktif `replace` di CI dan
   Docker. Direktif `ignore` mengecualikan `node_modules`.
4. **Workspace per ekosistem dengan satu lockfile:** Cargo workspace,
   uv workspace, pnpm workspace.
5. **`just` sebagai task runner.** `just check` identik dengan pemeriksaan CI.
6. **Toolchain dipin:** `rust-toolchain.toml`, `.python-version`,
   `.node-version`, direktif `go` di `go.mod`, `packageManager` pnpm,
   prettier versi persis.

## Konsekuensi

- Positif: perubahan lintas bahasa masuk dalam satu commit atomik; paket
  bersama dipakai tanpa publikasi; satu perintah verifikasi untuk semua bahasa.
- Negatif: CI butuh path filter per proyek (L0.7); semua Go API berbagi
  versi dependensi yang sama; riwayat git ketiga proyek bercampur.

## Alternatif yang ditolak

- Repo per proyek: paket bersama harus dipublikasikan dan diberi versi.
- Satu Go API untuk seluruh lab: kegagalan dan deploy saling terkait.
- Multi-modul Go dengan `go.work`: rapuh di CI dan Docker.
- Make: dirancang untuk build file, bukan menjalankan perintah.
