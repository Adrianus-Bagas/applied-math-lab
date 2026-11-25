"""Tes jendela waktu: validitas tingkat 1 dan a'_j ≤ d'_j secara konstruksi."""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from mealops.generator.rng import Aliran, buat_aliran
from mealops.generator.windows import (
    JendelaTitik,
    bentuk_jendela,
    jam_tutup,
    sampel_jendela,
)

E0 = 420  # 07:00

# ---------------------------------------------------------------------------
# 1. Contoh hitung tangan (konsep E)
# ---------------------------------------------------------------------------


def test_contoh_titik_terpotong() -> None:
    # m acak 450 < e0 + τ0 + δ = 420 + 13 + 23 = 456, jadi m dinaikkan ke 456
    w = bentuk_jendela(tau0=13, s_maks=8, e0=E0, m_acak=450, delta_tambah=15, lebar=60)
    assert w == JendelaTitik(a=373, m=456, delta=23)
    assert w.d == 433


def test_contoh_titik_biasa() -> None:
    w = bentuk_jendela(tau0=26, s_maks=7, e0=E0, m_acak=690, delta_tambah=20, lebar=90)
    assert w == JendelaTitik(a=573, m=690, delta=27)
    assert w.d == 663


def test_contoh_jam_tutup() -> None:
    w1 = JendelaTitik(a=373, m=456, delta=23)
    w2 = JendelaTitik(a=573, m=690, delta=27)
    # syarat: l0 ≥ d + s + τ pulang = max(433 + 8 + 13, 663 + 7 + 26) = 696
    assert jam_tutup([w1, w2], [8, 7], [13, 26], 900) == 900  # sudah cukup
    assert jam_tutup([w1, w2], [8, 7], [13, 26], 600) == 696  # dinaikkan


def test_a_tidak_negatif() -> None:
    # d - lebar < 0 → a dipotong ke 0 (awal hari)
    w = bentuk_jendela(tau0=5, s_maks=5, e0=0, m_acak=0, delta_tambah=0, lebar=500)
    assert w.a == 0


def test_melewati_hari_ditolak() -> None:
    with pytest.raises(ValueError, match=r"melewati satu hari"):
        bentuk_jendela(tau0=900, s_maks=10, e0=600, m_acak=700, delta_tambah=0, lebar=60)


# ---------------------------------------------------------------------------
# 2. Property: valid tingkat 1 dan a'_j ≤ d'_j untuk input apa pun yang sah
# ---------------------------------------------------------------------------


@given(
    st.lists(
        st.tuples(st.integers(0, 120), st.integers(1, 30)),  # (τ0, s_maks) per titik
        min_size=1,
        max_size=10,
    ),
    st.integers(300, 480),  # e0
    st.integers(0, 40),  # delta_tambah
    st.integers(0, 180),  # lebar
    st.integers(500, 800),  # m acak
    st.integers(0, 1300),  # l0 minimum
)
def test_jendela_efektif_tidak_kosong(
    titik: list[tuple[int, int]],
    e0: int,
    delta_tambah: int,
    lebar: int,
    m_acak: int,
    l0_minimum: int,
) -> None:
    tau0 = [t for t, _ in titik]
    s_maks = [s for _, s in titik]
    jendela = [bentuk_jendela(t, s, e0, m_acak, delta_tambah, lebar) for t, s in titik]
    l0 = jam_tutup(jendela, s_maks, tau0, max(l0_minimum, e0))
    assert e0 <= l0
    for w, t, s in zip(jendela, tau0, s_maks, strict=True):
        # tingkat 1 (check_input): d ≥ 0, a ≤ d, s ≤ δ
        assert 0 <= w.a <= w.d
        assert s <= w.delta
        # tingkat 2, uji pertama §7.6: a' ≤ d'
        a_efektif = max(w.a, e0 + t)
        d_efektif = min(w.d, l0 - s - t)
        assert a_efektif <= d_efektif


# ---------------------------------------------------------------------------
# 3. Sampel
# ---------------------------------------------------------------------------


def test_sampel_jendela_beku() -> None:
    rng = buat_aliran(7, Aliran.JENDELA)
    jendela = sampel_jendela(rng, [13, 26, 40], [8, 7, 9], E0, 600, 720, 15, 10, 30, 30, 120)
    assert jendela == [  # nilai beku, NumPy 2.5.3
        JendelaTitik(a=548, m=675, delta=26),
        JendelaTitik(a=600, m=660, delta=27),
        JendelaTitik(a=573, m=690, delta=24),
    ]


def test_sampel_jendela_m_di_grid() -> None:
    rng = buat_aliran(3, Aliran.JENDELA)
    # τ0 kecil supaya m tidak pernah dinaikkan; semua m harus kelipatan 15 dari 600
    jendela = sampel_jendela(rng, [5] * 50, [6] * 50, E0, 600, 720, 15, 10, 30, 30, 120)
    assert all(600 <= w.m <= 720 and (w.m - 600) % 15 == 0 for w in jendela)
