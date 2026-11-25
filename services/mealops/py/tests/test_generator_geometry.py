"""Tes geometri generator: pembulatan bulat, matriks jarak/waktu, sampel lokasi."""

import math
from fractions import Fraction
from typing import Literal

import pytest
from hypothesis import given
from hypothesis import strategies as st
from mealops.generator.geometry import (
    Titik,
    akar_atas,
    bagi_atas,
    jarak_jalan,
    matriks_jarak,
    matriks_waktu,
    sampel_lokasi,
)
from mealops.generator.rng import Aliran, buat_aliran

Tipe = Literal["R", "C", "RC"]
SEMUA_TIPE: list[Tipe] = ["R", "C", "RC"]


# ---------------------------------------------------------------------------
# Pembantu
# ---------------------------------------------------------------------------


def cek_metrik(m: list[list[int]]) -> None:
    """Gagal bila bukan persegi, diagonal tak nol, tak simetris, atau segitiga gagal."""
    n = len(m)
    assert all(len(baris) == n for baris in m), "matriks tidak persegi"
    for i in range(n):
        assert m[i][i] == 0, f"diagonal [{i}][{i}] = {m[i][i]}"
        for j in range(n):
            assert m[i][j] == m[j][i], f"tidak simetris di ({i}, {j})"
            for k in range(n):
                # Ketaksamaan segitiga: jalan langsung i→k tidak lebih lama dari lewat j
                assert m[i][k] <= m[i][j] + m[j][k], (
                    f"segitiga gagal: m[{i}][{k}]={m[i][k]} > "
                    f"m[{i}][{j}]={m[i][j]} + m[{j}][{k}]={m[j][k]}"
                )


def rata_tetangga_terdekat(lokasi: list[Titik]) -> float:
    """Rata-rata jarak garis lurus tiap titik ke tetangga terdekatnya (khusus tes)."""
    total = 0.0
    for i, p in enumerate(lokasi):
        total += min(math.dist(p, r) for j, r in enumerate(lokasi) if j != i)
    return total / len(lokasi)


# ---------------------------------------------------------------------------
# 1. Pembulatan bulat
# ---------------------------------------------------------------------------


def test_bagi_atas_kecil() -> None:
    # Di rentang kecil float masih akurat, jadi math.ceil(p / q) boleh jadi pembanding
    for p in range(0, 200):
        for q in range(1, 20):
            assert bagi_atas(p, q) == math.ceil(p / q), (p, q)


def test_bagi_atas_besar() -> None:
    # Di sini float sudah tidak akurat; Fraction eksak menjadi pembanding
    p, q = 10**30 + 1, 7
    assert bagi_atas(p, q) == math.ceil(Fraction(p, q))


def test_akar_atas_kecil() -> None:
    for n in range(0, 10**5):
        assert akar_atas(n) == math.ceil(math.sqrt(n)), n


@pytest.mark.parametrize("k", [1, 2, 10, 12345, 10**8])
def test_akar_atas_kuadrat_sempurna(k: int) -> None:
    # Batas paling rawan: tepat k² harus k, satu di atasnya harus k + 1
    assert akar_atas(k * k) == k
    assert akar_atas(k * k + 1) == k + 1


def test_akar_atas_besar() -> None:
    # Float memberi 10**8 (salah); jawaban eksak 10**8 + 1
    assert math.ceil(math.sqrt(10**16 + 1)) == 10**8  # dokumentasi: float memang keliru
    assert akar_atas(10**16 + 1) == 10**8 + 1


# ---------------------------------------------------------------------------
# 2. Contoh hitung tangan (konsep B.5 dan soal 3)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("p", "r", "sirkuitas", "harapan"),
    [
        # Konsep B.5, κ = 108/100
        ((0, 0), (3000, 4000), Fraction(108, 100), 5400),
        ((3000, 4000), (13500, 18000), Fraction(108, 100), 18900),
        ((0, 0), (13500, 18000), Fraction(108, 100), 24300),
        # Soal 3, κ = 13/10
        ((0, 0), (3000, 4000), Fraction(13, 10), 6500),
        ((3000, 4000), (-6000, 8000), Fraction(13, 10), 12804),
        ((0, 0), (-6000, 8000), Fraction(13, 10), 13000),
    ],
)
def test_jarak_hitung_tangan(p: Titik, r: Titik, sirkuitas: Fraction, harapan: int) -> None:
    assert jarak_jalan(p, r, sirkuitas) == harapan
    assert jarak_jalan(r, p, sirkuitas) == harapan  # simetris


def test_float_melanggar_segitiga() -> None:
    # Dokumentasi konsep B.5: titik (0,0), (30,40), (135,180) segaris, e = 50, 175, 225.
    # Float: 1.08 * 225 = 243.00000000000003 → ceil 244 > 54 + 189 = 243 (melanggar).
    assert math.ceil(1.08 * 225) == 244
    assert math.ceil(1.08 * 50) + math.ceil(1.08 * 175) == 243
    # Versi bulat kita eksak
    k = Fraction(108, 100)
    assert jarak_jalan((0, 0), (135, 180), k) == 243
    assert jarak_jalan((0, 0), (30, 40), k) + jarak_jalan((30, 40), (135, 180), k) == 243


def test_matriks_kecil() -> None:
    lokasi: list[Titik] = [(0, 0), (3000, 4000), (13500, 18000)]
    c = matriks_jarak(lokasi, Fraction(108, 100))
    assert c == [[0, 5400, 24300], [5400, 0, 18900], [24300, 18900, 0]]
    # Tabel B.5: τ = ⌈c / 500⌉
    tau = matriks_waktu(c, 500)
    assert tau == [[0, 11, 49], [11, 0, 38], [49, 38, 0]]
    cek_metrik(c)
    cek_metrik(tau)


# ---------------------------------------------------------------------------
# 3. Property: segitiga terjaga untuk titik, sirkuitas, dan kecepatan sembarang
# ---------------------------------------------------------------------------

koordinat = st.tuples(st.integers(-20_000, 20_000), st.integers(-20_000, 20_000))


@given(
    st.lists(koordinat, min_size=3, max_size=8),
    st.fractions(min_value=1, max_value=2, max_denominator=100),
    st.integers(100, 1500),  # kecepatan m/menit (6–90 km/jam)
)
def test_segitiga_terjaga(lokasi: list[Titik], sirkuitas: Fraction, v: int) -> None:
    c = matriks_jarak(lokasi, sirkuitas)
    cek_metrik(c)
    cek_metrik(matriks_waktu(c, v))


@given(
    st.lists(st.integers(-1000, 1000), min_size=3, max_size=6),
    st.integers(100, 1500),
)
def test_segitiga_titik_segaris(xs: list[int], v: int) -> None:
    # Titik segaris = kasus terketat: di bilangan real segitiganya berupa persamaan
    lokasi: list[Titik] = [(3 * x, 4 * x) for x in xs]
    c = matriks_jarak(lokasi, Fraction(108, 100))
    cek_metrik(c)
    cek_metrik(matriks_waktu(c, v))


# ---------------------------------------------------------------------------
# 4. Sampel lokasi
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tipe", SEMUA_TIPE)
def test_lokasi_dalam_kotak(tipe: Tipe) -> None:
    setengah_sisi = 10_000
    lokasi = sampel_lokasi(buat_aliran(7, Aliran.LOKASI), 200, tipe, setengah_sisi, 4, 1_500)
    assert len(lokasi) == 200
    assert all(
        -setengah_sisi <= x <= setengah_sisi and -setengah_sisi <= y <= setengah_sisi
        for x, y in lokasi
    )
    assert all(type(x) is int and type(y) is int for x, y in lokasi)  # bukan np.int64


@pytest.mark.parametrize("tipe", SEMUA_TIPE)
def test_lokasi_deterministik(tipe: Tipe) -> None:
    def ambil(seed: int) -> list[Titik]:
        return sampel_lokasi(buat_aliran(seed, Aliran.LOKASI), 50, tipe, 10_000, 3, 1_000)

    assert ambil(11) == ambil(11)
    assert ambil(11) != ambil(12)


@pytest.mark.parametrize(
    ("setengah_sisi", "harapan"),
    [
        # Kasus A: tanpa penolakan
        (10_000, [(-2717, -7539), (-4909, -8506), (-1848, 4621), (-5088, -8786)]),
        # Kasus B: titik 1 ditolak sekali, titik 2 ditolak tiga kali
        (2_000, [(-172, -1355), (-1984, -1001), (-1537, 453), (479, 709)]),
    ],
)
def test_lokasi_jejak_rc(setengah_sisi: int, harapan: list[Titik]) -> None:
    rng = buat_aliran(7, Aliran.LOKASI)
    assert sampel_lokasi(rng, 4, "RC", setengah_sisi, 2, 1_500) == harapan


def test_r_tidak_memakai_klaster() -> None:
    # Tipe R mengabaikan n_klaster dan sigma, jadi nilainya tak boleh mengubah hasil
    a = sampel_lokasi(buat_aliran(3, Aliran.LOKASI), 20, "R", 5_000, 1, 1)
    b = sampel_lokasi(buat_aliran(3, Aliran.LOKASI), 20, "R", 5_000, 9, 999)
    assert a == b


def test_klaster_lebih_rapat_dari_seragam() -> None:
    # Sanity distribusi: dengan σ kecil, titik klaster saling berdekatan
    rng_c = buat_aliran(5, Aliran.LOKASI)
    rng_r = buat_aliran(5, Aliran.LOKASI)
    klaster = sampel_lokasi(rng_c, 200, "C", 10_000, 4, 300)
    seragam = sampel_lokasi(rng_r, 200, "R", 10_000, 4, 300)
    assert rata_tetangga_terdekat(klaster) < rata_tetangga_terdekat(seragam) / 2


def test_sampling_penolakan_menyerah() -> None:
    # σ jauh lebih besar dari L → peluang diterima praktis nol
    with pytest.raises(RuntimeError, match=r"sampling penolakan gagal"):
        sampel_lokasi(buat_aliran(1, Aliran.LOKASI), 5, "C", 1, 1, 10**9)


@pytest.mark.parametrize(
    ("n", "tipe", "setengah_sisi", "n_klaster", "sigma"),
    [
        (0, "R", 100, 1, 1),  # n harus ≥ 1
        (5, "R", 0, 1, 1),  # L harus ≥ 1
        (5, "C", 100, 0, 1),  # tipe C butuh pusat
        (5, "RC", 100, 2, 0),  # tipe RC butuh σ ≥ 1
    ],
)
def test_parameter_ditolak(
    n: int, tipe: Tipe, setengah_sisi: int, n_klaster: int, sigma: int
) -> None:
    rng = buat_aliran(1, Aliran.LOKASI)
    with pytest.raises(ValueError, match=r"harus ≥ 1|butuh"):
        sampel_lokasi(rng, n, tipe, setengah_sisi, n_klaster, sigma)
