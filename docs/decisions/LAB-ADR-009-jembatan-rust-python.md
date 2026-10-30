# LAB-ADR-009: Jembatan Rust → Python (PyO3 + maturin)

- **Status:** Diterima
- **Tanggal:** 2026-10-30 (L0.3)
- **Terkait:** LAB-ADR-002, 004, 006, 007, 008

## Konteks

Hot loop ditulis di Rust, sedangkan modelling dan validasi di Python (LAB-ADR-002). Pola ini dipakai
di setiap core crate ketiga proyek, jadi tata letak, build, dan pengujiannya perlu seragam.

## Keputusan

1. **Core murni + crate binding terpisah.** Matematika ada di crate tanpa pyo3 (mis. `lab-numerics`).
   Binding `<nama>-py` adalah `cdylib` yang hanya mengonversi tipe dan melepas GIL. `[lib] test = false`:
   matematika diuji dengan `cargo test` di core; perbatasan diuji dengan pytest.
   Untuk proyek: `services/<proyek>/core` + `services/<proyek>/core-py`.
2. **PyO3 dan rust-numpy** di `[workspace.dependencies]`, satu minor yang sama. Fitur `abi3-py313`
   (satu wheel untuk CPython ≥ 3.13). **Tanpa** fitur `extension-module` (deprecated); maturin ≥ 1.9.4.
3. **Layout campuran maturin.** `Cargo.toml` dan `pyproject.toml` dalam satu direktori; `.so` menjadi
   `<paket>._core`; paket Python di `python/` berisi `__init__.py`, stub `_core.pyi`, dan `py.typed`
   (wajib untuk mypy strict).
4. **Interpreter dipin.** `.cargo/config.toml` mengarahkan `PYO3_PYTHON` ke `.venv/bin/python`.
   `.venv` harus ada sebelum `cargo clippy` (di CI: `uv sync` lebih dulu).
5. **Rebuild eksplisit.** `just py-ext` (`maturin develop --uv`) dijalankan sebelum pytest, karena
   `tool.uv.cache-keys` tidak memantau crate core di direktori lain sehingga `uv sync` bisa memakai
   `.so` usang.
6. **Input array lewat `PyArrayLike1`.** Array float64 contiguous dibaca tanpa salin; view berstride
   disalin sekali (`Cow`); input lain dikonversi `numpy.asarray(dtype=float64)`.
7. **GIL dilepas dengan `py.detach`** (nama baru `allow_threads`, PyO3 ≥ 0.26) selama komputasi.
   Kontrak: array input tidak dimutasi thread lain selama panggilan. Ini dijamin worker
   (satu proses, concurrency 1 job).
8. **Toleransi oracle diturunkan dari analisis galat**, bukan angka tetap. Contoh variansi:
   galat M₂ ≲ c·n·ε·‖x‖₂·√M₂ untuk algoritma stabil. Input yang identik (list vs ndarray)
   dibandingkan dengan `==`.

## Konsekuensi

- (+) Core bisa diuji dan dikompilasi ke WASM (LAB-ADR-006) tanpa menyentuh Python.
- (+) Satu wheel abi3 per platform; build image (L0.6) cukup sekali.
- (−) Dua crate per core; nama fungsi diulang di binding dan stub `.pyi` (harus disinkronkan manual).
- (−) Urutan wajib: `uv sync` sebelum `cargo clippy`.

## Alternatif yang ditolak

- **pyo3 di core di balik feature flag:** core tidak lagi murni; rawan error linker libpython saat `cargo test`.
- **cffi/ctypes dengan C ABI:** konversi dan pengecekan tipe ditulis manual dan rawan salah.
- **Mengandalkan `uv sync` saja untuk rebuild:** `.so` usang tidak terdeteksi bila yang berubah crate core.
