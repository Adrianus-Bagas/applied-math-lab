"""Lokasi sintetis dan matriks jarak/waktu bulat yang menjaga segitiga."""

import math
from fractions import Fraction
from typing import Literal

import numpy as np

Titik = tuple[int, int]  # meter, dapur di (0, 0)


def bagi_atas(p: int, q: int) -> int:
    """⌈p/q⌉ untuk p ≥ 0, q ≥ 1, tanpa float."""
    # TODO: satu baris dengan //
    return -(-p // q)


def akar_atas(n: int) -> int:
    """⌈√n⌉ eksak untuk n ≥ 0."""
    # TODO: kasus n == 0, lalu math.isqrt(n - 1) + 1
    if n == 0:
        return 0
    return math.isqrt(n - 1) + 1


def jarak_jalan(p: Titik, r: Titik, sirkuitas: Fraction) -> int:
    """c = ⌈(a/b)·√n⌉ = ⌈⌈√(a²·n)⌉ / b⌉ (konsep B.5)."""
    n = (p[0] - r[0]) ** 2 + (p[1] - r[1]) ** 2
    a, b = sirkuitas.numerator, sirkuitas.denominator
    # TODO: gabungkan akar_atas dan bagi_atas
    return bagi_atas(akar_atas(n * a**2), b)


def matriks_jarak(lokasi: list[Titik], sirkuitas: Fraction) -> list[list[int]]:
    # TODO: indeks 0 = dapur; diagonal otomatis 0; simetris (hitung i < j saja lalu salin)
    return [[jarak_jalan(p, r, sirkuitas) for r in lokasi] for p in lokasi]


def matriks_waktu(jarak: list[list[int]], kecepatan_m_per_menit: int) -> list[list[int]]:
    # TODO: τ = bagi_atas(c, v) per sel
    return [[bagi_atas(c, kecepatan_m_per_menit) for c in baris] for baris in jarak]


PERCOBAAN_MAKS = 10_000  # batas sampling penolakan; tercapai berarti σ terlalu besar dibanding L


# L = setengah_sisi
def _titik_seragam(rng: np.random.Generator, setengah_sisi: int) -> Titik:
    """Tipe R: x, y ~ Uniform bulat [-L, L]."""
    x = int(rng.integers(-setengah_sisi, setengah_sisi, endpoint=True))
    y = int(rng.integers(-setengah_sisi, setengah_sisi, endpoint=True))
    return (x, y)


def _titik_klaster(
    rng: np.random.Generator, pusat: list[Titik], setengah_sisi: int, sigma: int
) -> Titik:
    """Tipe C: pusat seragam + offset normal dibulatkan, ditolak bila keluar kotak."""
    # TODO 3: k = int(rng.integers(0, len(pusat)))   ← pilih pusat SEKALI, di luar loop
    k = int(rng.integers(0, len(pusat)))
    for _ in range(PERCOBAAN_MAKS):
        dx, dy = rng.normal(0.0, sigma, size=2)
        # TODO 4: x = pusat[k][0] + int(np.rint(dx)), begitu juga y
        x = pusat[k][0] + int(np.rint(dx))
        y = pusat[k][1] + int(np.rint(dy))
        # TODO 5: bila -L <= x <= L dan -L <= y <= L → return (x, y)
        if -setengah_sisi <= x <= setengah_sisi and -setengah_sisi <= y <= setengah_sisi:
            return (x, y)
    raise RuntimeError(f"sampling penolakan gagal {PERCOBAAN_MAKS} kali; perkecil sigma")


def sampel_lokasi(
    rng: np.random.Generator,
    n: int,
    tipe: Literal["R", "C", "RC"],
    setengah_sisi: int,
    n_klaster: int,
    sigma: int,
) -> list[Titik]:
    """n lokasi titik layanan (tanpa dapur) di kotak [-L, L]².

    Urutan tarikan: pusat klaster (bila ada), lalu titik 1..n berurutan.
    RC: ⌈n/2⌉ titik pertama tipe C, sisanya tipe R; awalan tidak stabil bila n berubah.
    """
    # TODO 6: validasi n ≥ 1, L ≥ 1, sigma ≥ 1, n_klaster ≥ 1 bila tipe memakai klaster
    if n < 1 or setengah_sisi < 1:
        raise ValueError("n dan setengah_sisi harus ≥ 1")
    if tipe != "R" and (n_klaster < 1 or sigma < 1):
        raise ValueError("tipe C/RC butuh n_klaster ≥ 1 dan sigma ≥ 1")
    # TODO 7: bila tipe != "R": pusat = [_titik_seragam(rng, L) for _ in range(n_klaster)]
    pusat = [_titik_seragam(rng, setengah_sisi) for _ in range(n_klaster)] if tipe != "R" else []
    # TODO 8: n_c = n untuk "C", bagi_atas(n, 2) untuk "RC", 0 untuk "R"
    n_c = {"R": 0, "C": n, "RC": bagi_atas(n, 2)}[tipe]
    # TODO 9: n_c titik klaster, lalu n - n_c titik seragam; gabungkan dan kembalikan
    klaster = [_titik_klaster(rng, pusat, setengah_sisi, sigma) for _ in range(n_c)]
    seragam = [_titik_seragam(rng, setengah_sisi) for _ in range(n - n_c)]
    return klaster + seragam
