# `docs/mathematics/mealops/`

Spesifikasi matematis MealOps (milestone MO-1). Semua kode MealOps (validator Python, core Rust, metaheuristik) mengimplementasikan semantik di sini; bila kode dan dokumen berbeda, dokumen yang benar sampai diubah lewat keputusan baru.

## Isi

| File           | Isi                                                                      |
| -------------- | ------------------------------------------------------------------------ |
| `model.md`     | Model A–D, tiga tingkat kegagalan (§3.1), bukti, contoh, keputusan C1–R5 |
| `notasi.md`    | Glosarium notasi gabungan, Big-M, dan konvensi label                     |
| `generator.md` | Generator instans sintetis: distribusi, aliran seed, jaminan (MO-2.2)    |
| `README.md`    | Indeks ini, peta model, fixture, dan pertanyaan terbuka yang diteruskan  |

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

## Fixture (MO-2.3a)

Semua nilai harapan berasal dari hitung tangan di `model.md` dan diverifikasi dua kali (saat bagiannya ditulis dan ulang secara independen di MO-1.6). **Nilai harapan tidak pernah diambil dari keluaran kode yang diuji.** Hitungan jumlah solusi memakai kendaraan tanpa label. Jarak dalam meter (biaya 32 di `model.md` = 3200 m), holding dalam porsi·menit.

File ada di `datasets/mealops/fixtures/`:

| File                     | Isi                                                                                                    |
| ------------------------ | ------------------------------------------------------------------------------------------------------ |
| `h5.instance.json`       | H5 (§3.3), dengan $\delta = 20$ sehingga $m$ sama dengan §6.6                                          |
| `h5.variants.json`       | 13 varian §3.8 sebagai patch JSON (`replace`, RFC 6902) terhadap H5, beserta tingkat dan nilai harapan |
| `h5s.instance.json`      | H5-S (§4.10): titik 2 berdemand 120 dipecah menjadi node 2 (100) dan node 6 (20), keduanya `point: 2`  |
| `h5p.instance.json`      | H5-P (§7.9): H5 + produksi, $\rho = 2$, $\lambda = 10$                                                 |
| `expected.model-bd.json` | 15 kasus Model B/D (patch + nilai harapan); belum ada oracle                                           |

Status: **oracle** = dibuktikan ulang oleh oracle Model A (`mealops.testing.oracle_model_a`); **cek** = diperiksa `check_input` atau model Pydantic; **data** = hanya dicatat, dibuktikan di milestone kolom terakhir.

| Fixture                                                 | Bagian     | Nilai harapan                                                                              | Status                      |
| ------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------ | --------------------------- |
| H5, Model A                                             | §3.3–§3.5  | $a'_j$, $d'_j$; 9 solusi layak (tabel lengkap); optimum unik S1 = 32                       | oracle                      |
| Rute S1 dan jebakan                                     | §3.5, §3.6 | $T^{\ast}$, jam pulang, biaya per rute                                                     | oracle                      |
| Solusi tidak layak H5                                   | §3.7       | lima solusi, satu pelanggaran masing-masing                                                | oracle (3 pelanggaran rute) |
| V1–V4, $e_0 = 530$, $d_4 = 495$                         | §3.8       | instans tidak layak; V3 dan V4 dengan $\lvert K \rvert = 3$: optimum 36 dan 34             | oracle                      |
| $d_2 = 540$, $l_0 = 640$                                | §3.8       | layak, saksi S1                                                                            | oracle                      |
| $q_2 = 120$, $Q = 30$, $d_5 = 570$                      | §3.8       | input tidak valid: `demand_exceeds_limit` (1 dan 2 node), `window_inverted` di `points[4]` | cek                         |
| H5-S, $\rho = 1$                                        | §4.10      | $\lvert K \rvert = 2$: 0; $\lvert K \rvert = 3$: 11, optimum 44                            | oracle (J2)                 |
| H5-S, $\rho \ge 2$                                      | §4.10      | $\lambda = 10$: 8, optimum 46 (M1 + satu lagi); $\lambda = 20$: 4; $\rho = 3$: 11          | data, MO-11                 |
| M2                                                      | §4.10      | layak sampai $\lambda = 15$, biaya 48                                                      | data, MO-3.2                |
| V5                                                      | §4.10      | $\lvert K \rvert = 1$: tidak layak untuk semua $\rho$, $\lambda$                           | data, MO-11                 |
| H5, $\rho = 2$, $\lambda = 10$                          | §4.8       | 41 solusi layak (32 memakai multi-trip); optimum tetap 32                                  | data, MO-11                 |
| $\theta^c$, $\theta^p$ H5-P                             | §5.5, §7.3 | durasi per $q_j$ dan per batch §5.5, §7.9                                                  | cek                         |
| S1 + batch $\lbrace 2,4 \rbrace, \lbrace 1,3,5 \rbrace$ | §6.6, §7.8 | tercepat 32355; paling lambat 19260; layak iff $H^{max} \ge 186$                           | data, MO-13.1               |
| $\ell_j$, $\mathcal{F}_j$, $\beta^{\ast}$ H5            | §7.3, §7.5 | $\ell = (58, 74, 72, 64, 62)$; $\sum q \ell = 9020$; $\beta^{\ast} = 2$                    | data, MO-6.3                |
| H5-P                                                    | §7.9       | 13 rencana layak (5 susunan trip); optimum unik D1: (38, 12395)                            | data, MO-13                 |
| H5-P, $\rho = 1$                                        | §7.9       | tidak layak walau lolos kelima uji §7.6; $\lvert K \rvert = 3$: optimum (40, 11835)        | data, MO-6.2, MO-13         |
| V6                                                      | §7.5       | $H^{max} = 90$: $\beta^{\ast} = 4$; tidak layak juga dengan $\lvert B \rvert = 4$          | data, MO-6.3, MO-13         |
| H5-P, $H^{max} = 200$                                   | §7.9       | optimum (32, 18400)                                                                        | data, MO-13                 |
| Contoh $n = 4$                                          | §2.9       | 8 solusi layak; optimum 25 (dua solusi); berikutnya 28                                     | belum ada fixture           |

Tes yang menjaga data (`services/mealops/py/tests/test_expected_model_bd.py`): setiap patch menghasilkan input valid, dan setiap rencana memuat setiap node tepat sekali. Tes ini tidak menangkap pengelompokan yang salah salin (misalnya batch D1 tertukar); itu baru tertangkap saat oracle milestone terkait menghitung ulang nilainya.

### Oracle Model A

`mealops.testing.oracle_model_a` adalah implementasi pembanding yang sengaja sederhana: membaca dict hasil `json.load` (bukan model Pydantic), enumerasi brute force partisi (restricted growth string, tepat sekali per partisi) × permutasi tiap blok × pemeriksaan rute §2.7. Hanya untuk $n$ kecil ($\lvert K \rvert^n \cdot$ faktorial ukuran blok). Tidak boleh diimpor kode produksi; validator MO-3.2 ditulis terpisah lalu dibandingkan dengannya.

## Pertanyaan terbuka yang diteruskan

| Pertanyaan                                                                                            | Ke              |
| ----------------------------------------------------------------------------------------------------- | --------------- |
| ~~Bedakan input tidak valid vs instans tidak layak di skema~~ selesai (MO-ADR-009)                    | MO-2.1 ✅       |
| Penskalaan instans Solomon ke bilangan bulat; objektif hierarkis (kendaraan, lalu jarak)              | MO-2.3b, MO-6.3 |
| Fixture contoh $n = 4$ (§2.9)                                                                         | MO-2.3b         |
| Oracle Model B (rantai trip) untuk nilai harapan H5-S, M2, V5                                         | MO-11           |
| Jenis pelanggaran: pulang setelah $l_0$, terlambat karena trip sebelumnya, batch terlambat untuk trip | MO-3.2          |
| Urutan trip terbaik per kendaraan                                                                     | MO-11.2         |
| Urutan dan pembagian batch terbaik                                                                    | MO-12, MO-13.1  |
| Uji kapasitas lini masak untuk lower bound yang lebih ketat                                           | MO-13.2         |
