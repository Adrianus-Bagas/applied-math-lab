# Generator instans sintetis MealOps

Dokumen ini mencatat **distribusi dan jaminan** generator `mealops.generator` (MO-2.2), sesuai MealOps v3.1 §10 ("generator sintetis ber-seed dengan distribusi yang terdokumentasi"). Semua nilai bawaan bersifat **ilustratif**, bukan data nyata.

## 1. Pemakaian

```bash
just gen 42                      # parameter bawaan
just gen 42 --params p.json      # parameter dari file (field yang tidak ada memakai bawaan)
```

Keluaran ditulis ke `datasets/mealops/synthetic/` (tidak di-commit; bisa dibuat ulang dari seed):

- `<nama>.instance.json`: instans `mealops.instance.v1`, JSON kanonik (`indent=2`, UTF-8, diakhiri `\n`).
- `<nama>.gen.json`: manifest `{generator, seed, numpy, instance_sha256, params}`.

Nama instans: `syn-<tipe><n>-<sidik>-s<seed>`, dengan `<sidik>` = 8 karakter pertama sha256 parameter kanonik.

## 2. Reproduksibilitas

- Seed bulat di `[0, 2⁵³ − 1]`; `bool` ditolak (`TypeError`), di luar rentang ditolak (`ValueError`).
- Satu aliran per komponen: `PCG64(SeedSequence(seed, spawn_key=(k,)))` dengan `k` = `LOKASI` 0, `DEMAND` 1, `JENDELA` 2. **Nomor aliran tidak boleh diubah.** Mengubah parameter satu komponen tidak menggeser bilangan acak komponen lain.
- Urutan tarikan tetap: pusat klaster → titik 1..n (lokasi); titik 1..n (demand); per titik `δ⁺ → m̃ → w` (jendela).
- Janji: **versi generator + parameter + seed yang sama → byte instans yang sama.** Perubahan keluaran yang disengaja wajib menaikkan `VERSI_GENERATOR` (`mealops-gen/1`) dan memperbarui golden hash. Diverifikasi dengan NumPy 2.5.3 dan 2.5.4.

## 3. Distribusi (asumsi distribusi, ilustratif)

| Besaran        | Distribusi                                                                                                  | Bawaan                                   |
| -------------- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| Lokasi tipe R  | `x, y ~ U{−L..L}`                                                                                           | `L = 10000` m                            |
| Lokasi tipe C  | pusat ~ R; titik = pusat seragam + `rint(N(0, σ²))` per sumbu, ditolak bila keluar kotak (normal terpotong) | `K = 4`, `σ = 1500` m                    |
| Lokasi tipe RC | `⌈n/2⌉` titik C lalu sisanya R (awalan tidak stabil bila `n` berubah)                                       | `n = 25`, tipe RC                        |
| Jarak          | `c = ⌈⌈√(a²·n)⌉ / b⌉`, sirkuitas `a/b`                                                                      | `13/10`                                  |
| Waktu tempuh   | `τ = ⌈c / v⌉`                                                                                               | `v = 500` m/menit                        |
| Demand titik   | `q ~ U{q_min..q_maks}`                                                                                      | 30..250 porsi                            |
| Potongan       | "penuh dulu" dengan `Q̄ = min(Q, D^max)` (`model.md` §4.1)                                                   |                                          |
| Waktu layan    | `s = s⁰ + ⌈η₁₀₀₀·q / 1000⌉`                                                                                 | `s⁰ = 5`, `η₁₀₀₀ = 20`                   |
| Buffer         | `δ = s^maks_i + δ⁺`, `δ⁺ ~ U{..}`                                                                           | 10..30 menit                             |
| Waktu makan    | `m = max(m̃, e_0 + τ_0i + δ)`, `m̃ ~ U` di grid `m_min + g·k`                                                 | 660..750, `g = 15`                       |
| Jendela        | `d = m − δ`, `a = max(0, d − w)`, `w ~ U{..}`                                                               | 60..180 menit                            |
| Jam dapur      | `e_0` tetap; `l_0 = max(l_0^min, max_i(d_i + s^maks_i + τ_i0))`                                             | 360, `l_0^min = 840`                     |
| Armada         | `\|K\| = ⌈Σq/(Qρ)⌉ + cadangan`                                                                              | `Q = 150`, `ρ = 2`, `λ = 15`, cadangan 1 |
| Batch          | `\|B\| = ⌈Σq/D^max⌉ + cadangan_batch` (bila `production` ada)                                               | `D^max = 400`, cadangan 1                |

**Catatan sensor.** `m` disensor dari bawah: bila `m̃` lebih awal dari `e_0 + τ_0i + δ_i`, nilainya didorong ke batas itu, jadi `m` tidak lagi seragam di grid. Parameter `m_min`/`m_maks` mendeskripsikan `m̃`, bukan `m`. Parameter yang membuat sebagian besar titik tersensor (contoh: `m_min = 360`, `m_maks = 375`; 569 dari 600 titik) menghasilkan jendela sangat sempit dan tidak realistis.

Semua aritmetika metrik bulat (tanpa float). `⌈·⌉` monoton dan subaditif, jadi segitiga Euclid terjaga di `c` dan `τ`; `floor`, `round`, dan versi float tidak menjaganya (contoh float: `1.08·225 = 243.00000000000003`).

## 4. Jaminan

| Pemeriksaan                           | Dijamin? | Lewat                                                                       |
| ------------------------------------- | -------- | --------------------------------------------------------------------------- |
| Tingkat 1 (`check_input`)             | ✔        | konstruksi: segitiga dari `⌈·⌉`, `s ≤ δ`, `0 ≤ a ≤ d`, `q ≤ Q̄`, `e_0 ≤ l_0` |
| `a'_j ≤ d'_j`                         | ✔        | sensor `m` dan `l_0` (lema max ≤ min, empat pasangan)                       |
| `⌈Σq/Q⌉ ≤ \|K\|ρ`                     | ✔        | rumus `\|K\|`                                                               |
| `⌈Σq/D^max⌉ ≤ \|B\|`                  | ✔        | rumus `\|B\|`                                                               |
| Kelompok saling tak serute `≤ \|K\|ρ` | ✘        | masalah clique (NP-hard); menjaminnya menyaring instans sulit               |
| `L_j ≤ U_j` (jendela masak)           | ✘        | `H^max` parameter kebijakan, tidak boleh diubah generator                   |
| `β* ≤ \|B\|`                          | ✘        | sama dengan baris di atas                                                   |
| Instans layak                         | ✘        | lolos semua uji belum berarti layak (R1)                                    |

Instans tidak layak tetap dihasilkan bila parameternya ketat; validator (MO-3) dan lower bound (MO-6.3) membutuhkannya.

## 5. Gagal saat membuat

Generator melempar `ValueError` bila `m ≥ 1440` atau `l_0 ≥ 1440` (perkecil jarak atau buffer), dan `RuntimeError` bila sampling penolakan klaster gagal 10 000 kali (perkecil `σ`). Parameter yang tidak konsisten (`q_min > q_maks`, sirkuitas < 1, field asing) ditolak `ParameterGenerator`.
