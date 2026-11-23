# MO-ADR-009: Kontrak instans `mealops.instance.v1`

- **Status:** diterima (MO-2.1, 2026-11-23)
- **Penomoran:** melanjutkan ADR-001–008 MealOps v3.1 agar tidak bertabrakan dengan nomor lama yang masih dirujuk.

## Konteks

Semua lapisan MealOps memakai satu bentuk data instans: generator (MO-2.2), fixture (MO-2.3), validator Python (MO-3), core Rust (MO-4.1, serde), dan Go API (snapshot skenario). `model.md` §1.7 menetapkan syarat input valid, dan §3.1 memisahkan tiga tingkat kegagalan. Pertanyaan terbuka dari MO-1.3/MO-1.6: bagaimana skema membedakan _input tidak valid_ dari _instans tidak layak_.

## Keputusan

1. **Satu dokumen instans, sesudah pemecahan demand.** Node (`nodes`) sudah berukuran `1 ≤ q_j ≤ Q̄`, dan `s_j` sudah dibulatkan ke atas (B1). Aturan pemecahan "penuh dulu" (J1, K1) dan rumus `s⁰ + η q` adalah urusan pembuat instans (generator MO-2.2), bukan kontrak.
2. **Matriks diindeks per lokasi, bukan per node.** Lokasi 0 = dapur, lokasi `p = 1..P` = `points[p-1]`; `travel_time` dan `distance` berukuran `(P+1)²`. Node menunjuk lokasinya lewat `point` (= `σ(j)`). Akibatnya `τ = c = 0` antar-potongan selokasi (§1.7 nomor 4 dan 8) terjamin oleh bentuk data, dan ukuran matriks tidak membengkak saat demand dipecah.
3. **Jendela disimpan di titik layanan** sebagai `ready` (`a`), `consume` (`m`), `buffer` (`δ`); deadline `d = m − δ` diturunkan. Node mewarisinya (J1). Fixture Model A memakai `δ = 20`, sehingga `d` sama dengan tabel `model.md`.
4. **Bagian produksi opsional** (`production: null` untuk Model A/B). Koefisien per porsi disimpan sebagai **bilangan bulat menit per 1000 porsi** (`cook_per_1000`, `pack_per_1000`), sehingga `θ(D) = φ₀ + ⌈φ₁·D/1000⌉` dihitung dengan aritmetika bulat yang identik di Python dan Rust. Dengan float, `⌈·⌉` bisa meleset satu menit: `0,07 × 100` dihitung `7,000000000000001`, jadi `⌈·⌉` memberi 8, bukan 7 (16 dari `D = 1..2000` meleset untuk `φ₁ = 0,07`; L0.10).
5. **Pydantic adalah sumber kebenaran; JSON Schema di-generate.** `just schema` (`uv run python -m mealops.schema`) menulis `contracts/mealops/instance.v1.schema.json` (Draft 2020-12, `$id` per versi). File itu di-commit untuk Go dan pembaca, dan dijaga dua tes: `--check` di `lint-py` dan tes pytest yang membandingkan isi file dengan hasil render. File ini **wajib** ada di `.prettierignore`: prettier meringkas array pendek ke satu baris, sehingga format prettier dan format generator saling membatalkan (`lint-misc` vs `--check`). Tes Go `contracts/mealops_instance_test.go` membuktikan skema bisa dikompilasi santhosh-tekuri/jsonschema v6 dan setuju dengan Python untuk kasus struktural. Filter CI: `contracts/mealops/**`, `services/*/py/**`, dan `datasets/**` memicu job Python; `datasets/**` juga memicu job Go.
6. **Tingkat 1 dibagi dua lapis, keduanya "input tidak valid".**
   - _Struktural_ (skema, Python **dan** Go): tipe bilangan bulat, rentang satu angka (`[0, 1440)`, `≥ 1`), field wajib, `additionalProperties: false`, `schema_version` konstan.
   - _Antar-field_ (`mealops.checks.check_input`, Python saja): bentuk matriks, rujukan `point`, `d ≥ 0`, `a ≤ d`, `s ≤ δ` (B5), diagonal nol, segitiga `τ` (B6, broadcasting `O(L³)`), `q ≤ Q̄` (K1), `e₀ ≤ l₀`.
   - Semua pelanggaran dikumpulkan (`InvalidInputError.issues`, kode stabil `IssueCode`, jalur JSON), kecuali kesalahan struktur yang membuat pemeriksaan lain tidak terdefinisi.
7. **Tingkat 2 tidak masuk kontrak.** Tidak ada pemeriksaan yang memakai `a'_j`, `d'_j`, `S^max`, `ℓ_j`, atau `β*`. Instans seperti H5 dengan `e₀ = 530` lolos validasi input; ketidaklayakannya dilaporkan uji §7.6 (MO-6.3). Ini menjawab pertanyaan terbuka MO-1.3/MO-1.6 dan diuji langsung dengan tabel pembanding `model.md` §3.8.
8. **Model immutable dan ketat:** `extra="forbid"`, `strict=True` (tidak ada `"480"` → 480), `frozen=True` (cocok dengan snapshot immutable).
9. **Paket `mealops` di `services/mealops/py`** (anggota uv workspace), terpisah dari worker nanti (`services/mealops/worker`, MO-WS), karena generator, validator, dan benchmark juga dipakai di luar worker. Pola `services/<proyek>/py` dipakai juga oleh DengueSim dan Harga Pangan.
10. **Pemasangan anggota workspace lewat `uv sync --all-packages`** (resep `setup-py`), tanpa menyebutnya di `dependencies` root. Bila suatu saat paket workspace disebut di `dependencies`, pasangan `[tool.uv.sources] <nama> = { workspace = true }` **wajib**; tanpa itu uv mencari nama tersebut di PyPI (risiko _dependency confusion_).

## Alternatif yang ditolak

- **JSON Schema ditulis tangan + model Pydantic ditulis tangan.** Dua sumber yang harus selalu sama; drift hanya ketahuan bila ada tes untuk setiap field.
- **Semua syarat §1.7 di dalam `model_validator` Pydantic.** Berhenti di pelanggaran pertama dan mencampur dua lapis; skema yang dihasilkan tidak lagi menggambarkan apa yang diterima model.
- **Matriks per node.** Syarat selokasi harus divalidasi, dan matriks tumbuh kuadratik terhadap jumlah potongan.
- **Koefisien durasi sebagai float.** Pembulatan ke atas tidak eksak dan bisa berbeda antar-bahasa.

## Konsekuensi

- Go hanya menjamin struktur. Instans yang lolos Go bisa tetap ditolak worker di tingkat 1; worker melaporkannya sebagai `PermanentError` berisi daftar `IssueCode` (MO-WS).
- Kemungkinan perbedaan kecil: JSON Schema menganggap `10.0` bilangan bulat, Pydantic strict menolaknya. Python adalah gerbang terakhir, jadi perbedaan ini hanya membuat Python lebih ketat.
- Perubahan bentuk JSON yang tidak kompatibel menaikkan versi (`mealops.instance.v2`, file skema baru); versi lama tetap dibaca selama ada snapshot yang memakainya.
- Kontrak job MealOps (misalnya `mealops.solve.v1`, MO-WS) merujuk skema ini lewat `$ref` ke `$id`-nya.
