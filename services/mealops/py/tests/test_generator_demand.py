"""Tes demand: sampel, pemecahan "penuh dulu", waktu layan, armada."""

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st
from mealops.generator.demand import (
    Potongan,
    bangun_node,
    jumlah_kendaraan,
    pecah_demand,
    sampel_demand,
    waktu_layan,
)
from mealops.generator.rng import Aliran, buat_aliran

# ---------------------------------------------------------------------------
# 1. Pemecahan demand (model.md §4.1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("q", "q_bar", "harapan"),
    [
        (250, 100, [100, 100, 50]),  # contoh §4.1
        (330, 100, [100, 100, 100, 30]),  # contoh §4.1
        (100, 100, [100]),  # pas satu potongan: r = Q̄, bukan 0
        (101, 100, [100, 1]),  # sisa terkecil r = 1
        (40, 100, [40]),  # tidak perlu dipecah
        (250, 80, [80, 80, 80, 10]),  # Q̄ = min(Q, D^max) = 80
    ],
)
def test_pecah_contoh(q: int, q_bar: int, harapan: list[int]) -> None:
    assert pecah_demand(q, q_bar) == harapan


@given(st.integers(1, 5000), st.integers(1, 300))
def test_pecah_sifat(q: int, q_bar: int) -> None:
    potongan = pecah_demand(q, q_bar)
    assert sum(potongan) == q  # tidak ada porsi yang hilang atau bertambah
    assert len(potongan) == math.ceil(q / q_bar)  # k = ⌈q/Q̄⌉ (jumlah paling sedikit)
    assert all(1 <= p <= q_bar for p in potongan)  # 1 ≤ r ≤ Q̄
    assert all(p == q_bar for p in potongan[:-1])  # "penuh dulu"


@pytest.mark.parametrize(("q", "q_bar"), [(0, 100), (10, 0)])
def test_pecah_ditolak(q: int, q_bar: int) -> None:
    with pytest.raises(ValueError, match=r"harus ≥ 1"):
        pecah_demand(q, q_bar)


# ---------------------------------------------------------------------------
# 2. Waktu layan s_j = s⁰ + ⌈η q_j⌉, η dalam menit per 1000 porsi
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("q", "harapan"),
    [(100, 7), (50, 6), (30, 6)],  # tabel §4.1: s⁰ = 5, η = 0,02 → 20 per 1000
)
def test_waktu_layan_contoh(q: int, harapan: int) -> None:
    assert waktu_layan(q, 5, 20) == harapan


def test_waktu_layan_float_keliru() -> None:
    # η = 0,07 menit/porsi, q = 100 → tepat 7 menit; float: 7.000000000000001
    assert 5 + math.ceil(0.07 * 100) == 13  # dokumentasi: float salah satu menit
    assert waktu_layan(100, 5, 70) == 12


# ---------------------------------------------------------------------------
# 3. Node dan sampel demand
# ---------------------------------------------------------------------------


def test_bangun_node_urutan() -> None:
    # Node diberi nomor per titik berurutan; potongan penuh lebih dulu
    assert bangun_node([250, 40], 100, 5, 20) == [
        Potongan(titik=1, q=100, s=7),
        Potongan(titik=1, q=100, s=7),
        Potongan(titik=1, q=50, s=6),
        Potongan(titik=2, q=40, s=6),
    ]


def test_sampel_demand() -> None:
    demand = sampel_demand(buat_aliran(7, Aliran.DEMAND), 5, 30, 250)
    assert demand == [180, 136, 118, 43, 127]  # nilai beku, NumPy 2.5.3
    assert all(type(q) is int for q in demand)


def test_sampel_demand_awalan_stabil() -> None:
    # Soal 2 bagian 1: menambah titik tidak mengubah demand titik-titik awal
    pendek = sampel_demand(buat_aliran(9, Aliran.DEMAND), 10, 1, 500)
    panjang = sampel_demand(buat_aliran(9, Aliran.DEMAND), 12, 1, 500)
    assert panjang[:10] == pendek


@pytest.mark.parametrize(("q_min", "q_maks"), [(0, 10), (20, 10)])
def test_sampel_demand_ditolak(q_min: int, q_maks: int) -> None:
    with pytest.raises(ValueError, match=r"q_min"):
        sampel_demand(buat_aliran(1, Aliran.DEMAND), 3, q_min, q_maks)


# ---------------------------------------------------------------------------
# 4. Armada: |K| = ⌈Σq / (Qρ)⌉ + cadangan menjamin ⌈Σq/Q⌉ ≤ |K|ρ
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("total", "harapan"), [(1350, 7), (1400, 7), (1401, 8)])
def test_jumlah_kendaraan_contoh(total: int, harapan: int) -> None:
    assert jumlah_kendaraan(total, 100, 2, 0) == harapan


@given(st.integers(1, 10**6), st.integers(1, 500), st.integers(1, 5), st.integers(0, 3))
def test_uji_kapasitas_lolos(total: int, kapasitas: int, rho: int, cadangan: int) -> None:
    k = jumlah_kendaraan(total, kapasitas, rho, cadangan)
    assert math.ceil(total / kapasitas) <= k * rho  # uji tingkat 2 §7.6 tidak gagal
