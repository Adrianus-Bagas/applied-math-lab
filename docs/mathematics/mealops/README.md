# `docs/mathematics/mealops/`

Spesifikasi matematis MealOps (milestone MO-1). Semua kode MealOps (validator Python, core Rust, metaheuristik) mengimplementasikan semantik di sini; bila kode dan dokumen berbeda, dokumen yang benar sampai diubah lewat keputusan baru.

## Isi

| File        | Isi                                                                      |
| ----------- | ------------------------------------------------------------------------ |
| `model.md`  | Model A–D, tiga tingkat kegagalan (§3.1), bukti, contoh, keputusan C1–R5 |
| `notasi.md` | Glosarium notasi gabungan, Big-M, dan konvensi label                     |
| `README.md` | Indeks ini, peta model, fixture, dan pertanyaan terbuka yang diteruskan  |

## Peta model

| Model | Isi                                         | Formulasi     | Bagian | Dipakai oleh                       |
| ----- | ------------------------------------------- | ------------- | ------ | ---------------------------------- |
| A     | CVRPTW satu trip per kendaraan              | F0–F8         | §2, §3 | Solomon + BKS (MO-2.3), MO-5, MO-6 |
| B     | A + multi-trip, $\lambda$, pemecahan demand | G0–G10        | §4     | MO-11                              |
| C     | Produksi batch, dua lini                    | P1–P8         | §5     | MO-12                              |
| D     | B + C + release date + holding              | G + P + I1–I4 | §6, §7 | MO-13 (model akhir MVP)            |

Hubungan: Model B dengan $\rho = 1$ sama dengan Model A (J2). Model D dengan $H^{max}$ sangat besar dan dapur yang selalu siap sebelum $e_0 - \lambda$ sama dengan Model B.

## Pemeriksaan yang dipakai kode

| Pemeriksaan                    | Bagian     | Kompleksitas                | Milestone       |
| ------------------------------ | ---------- | --------------------------- | --------------- |
| Validasi input (tingkat 1)     | §1.7, §3.1 | $O(n^3)$ (segitiga)         | MO-2.1          |
| Satu rute / satu trip          | §2.7, §4.3 | $O(m)$                      | MO-3.2, core    |
| Rantai trip satu kendaraan     | §4.4       | $O(\rho)$                   | MO-3.2, core    |
| Uji arc mustahil               | §2.8       | $O(n^2)$                    | MO-5, MO-6.2    |
| Uji instans (tingkat 2)        | §7.6       | $O(n \log n)$               | MO-6.3, MO-13.2 |
| Jadwal paling lambat (decoder) | §7.7       | linear dalam ukuran rencana | MO-13.1         |

## Fixture untuk MO-2.3

Semua nilai di bawah diverifikasi dua kali: saat bagiannya ditulis dan ulang secara independen di MO-1.6. Hitungan jumlah solusi memakai kendaraan tanpa label.

| Fixture                                                 | Bagian     | Nilai harapan                                                                                                                                  |
| ------------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Contoh $n = 4$                                          | §2.9       | 8 solusi layak; optimum 25 (dua solusi); berikutnya 28                                                                                         |
| H5, Model A                                             | §3.3–§3.5  | 9 solusi layak; optimum unik S1 = 32                                                                                                           |
| H5, $\rho = 2$, $\lambda = 10$                          | §4.8       | 41 solusi layak (32 memakai multi-trip); optimum tetap 32                                                                                      |
| Solusi tidak layak H5                                   | §3.7       | lima solusi, satu pelanggaran masing-masing                                                                                                    |
| V1–V4                                                   | §3.8       | tidak layak; V3 dan V4 dengan $\lvert K \rvert = 3$: optimum 36 dan 34                                                                         |
| H5-S                                                    | §4.10      | $\rho = 1$: 0; $\rho = 2$, $\lambda = 10$: 8, optimum 46; $\lambda = 20$: 4; $\rho = 3$: 11; $\lvert K \rvert = 3$, $\rho = 1$: 11, optimum 44 |
| M2                                                      | §4.10      | layak sampai $\lambda = 15$                                                                                                                    |
| V5                                                      | §4.10      | $\lvert K \rvert = 1$: tidak layak untuk semua $\rho$, $\lambda$                                                                               |
| S1 + batch $\lbrace 2,4 \rbrace, \lbrace 1,3,5 \rbrace$ | §6.6, §7.8 | tercepat 32355; paling lambat 19260; layak iff $H^{max} \ge 186$                                                                               |
| $\ell_j$, $\mathcal{F}_j$ H5                            | §7.3       | $\ell = (58, 74, 72, 64, 62)$; $\sum q \ell = 9020$                                                                                            |
| H5-P                                                    | §7.9       | 13 rencana layak (5 susunan trip); optimum unik D1: (38, 12395)                                                                                |
| V6                                                      | §7.5       | $H^{max} = 90$: $\beta^{\ast} = 4$; tidak layak juga dengan $\lvert B \rvert = 4$                                                              |
| H5-P, $H^{max} = 200$                                   | §7.9       | optimum (32, 18400)                                                                                                                            |

## Pertanyaan terbuka yang diteruskan

| Pertanyaan                                                                                            | Ke             |
| ----------------------------------------------------------------------------------------------------- | -------------- |
| ~~Bedakan input tidak valid vs instans tidak layak di skema~~ selesai (MO-ADR-009)                    | MO-2.1 ✅      |
| Penskalaan instans Solomon ke bilangan bulat; objektif hierarkis (kendaraan, lalu jarak)              | MO-2.3, MO-6.3 |
| Jenis pelanggaran: pulang setelah $l_0$, terlambat karena trip sebelumnya, batch terlambat untuk trip | MO-3.2         |
| Urutan trip terbaik per kendaraan                                                                     | MO-11.2        |
| Urutan dan pembagian batch terbaik                                                                    | MO-12, MO-13.1 |
| Uji kapasitas lini masak untuk lower bound yang lebih ketat                                           | MO-13.2        |
