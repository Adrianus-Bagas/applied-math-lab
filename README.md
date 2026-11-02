# Applied Math Lab

Tiga software portofolio berbasis matematika terapan untuk masalah di Indonesia:
**MealOps — optimasi dapur massal dan distribusi makanan perishable**, **DengueSim**, dan **Harga Pangan**.

Arsitektur: Next.js → Go API → antrean job PostgreSQL → Python worker → Rust core (PyO3).

## Prasyarat

- Rust (versi dipin di `rust-toolchain.toml`, dipasang otomatis oleh rustup)
- Go 1.27+ dan golangci-lint v2
- uv (Python 3.13, dipin di `.python-version`)
- Node 26 (dipin di `.node-version`) dan pnpm
- just

## Perintah

| Perintah      | Fungsi                                      |
| ------------- | ------------------------------------------- |
| `just setup`  | Pasang dependensi Python dan Node           |
| `just fmt`    | Rapikan format semua bahasa                 |
| `just check`  | Lint dan test semua bahasa (sama dengan CI) |
| `just --list` | Semua resep                                 |

## Struktur

| Direktori          | Isi                                 |
| ------------------ | ----------------------------------- |
| `packages/rust/`   | Crate Rust bersama (`lab-numerics`) |
| `packages/python/` | Paket Python bersama (`lab_stats`)  |
| `packages/go/`     | Paket Go bersama (`buildinfo`)      |
| `docs/decisions/`  | Architecture Decision Records       |

Keputusan struktur repo: [LAB-ADR-008](docs/decisions/LAB-ADR-008-monorepo-dan-tooling.md).
