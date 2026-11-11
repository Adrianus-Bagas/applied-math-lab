# Architecture Decision Records

Satu file per keputusan arsitektur. ADR menjawab "mengapa begini", supaya keputusan lama tidak diperdebatkan ulang tanpa informasi baru.

## Aturan

- Nama file: `LAB-ADR-NNN-judul-singkat.md`, nomor urut tiga digit. Mulai dari salinan `TEMPLATE.md`.
- ADR lab memakai prefiks `LAB-ADR`. ADR khusus proyek memakai `MO-ADR`, `D-ADR`, atau `P-ADR`.
- Tulis ADR di thread tempat keputusannya diambil, lalu ringkas satu paragraf di `PROJECT_CONTEXT` §2.3.
- ADR yang sudah Diterima tidak ditulis ulang. Koreksi kecil boleh; perubahan arah dibuat sebagai ADR baru, dan ADR lama diberi status "Digantikan oleh".

## Indeks

| Nomor                                          | Judul                                                              | Sub-milestone |
| ---------------------------------------------- | ------------------------------------------------------------------ | ------------- |
| 001–007                                        | Prinsip arsitektur awal (tanpa file; lihat `PROJECT_CONTEXT` §2.3) | sebelum L0    |
| [008](LAB-ADR-008-monorepo-dan-tooling.md)     | Monorepo dan tooling lintas bahasa                                 | L0.2          |
| [009](LAB-ADR-009-jembatan-rust-python.md)     | Jembatan Rust → Python                                             | L0.3          |
| [010](LAB-ADR-010-antrean-job.md)              | Antrean job dan kontrak payload                                    | L0.4          |
| [011](LAB-ADR-011-api-hello-dan-sse.md)        | Go API, SSE, dan portal                                            | L0.5          |
| [012](LAB-ADR-012-docker-dan-compose-lokal.md) | Image Docker multi-stage dan Compose lokal                         | L0.6          |
| [013](LAB-ADR-013-ci-github-actions.md)        | CI GitHub Actions dan GHCR                                         | L0.7          |
| [014](LAB-ADR-014-vps-dan-deploy.md)           | VPS, deploy otomatis, dan slot job berat                           | L0.8          |
| [015](LAB-ADR-015-rust-wasm-di-portal.md)      | Rust → WASM di portal                                              | L0.11         |
