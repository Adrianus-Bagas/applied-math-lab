import math
import sys

from hypothesis import given
from hypothesis import strategies as st
from lab_stats.summation import kahan_sum, naive_sum, pairwise_sum

EPS = sys.float_info.epsilon  # = 2u

daftar_float = st.lists(
    st.floats(min_value=-1e6, max_value=1e6, allow_nan=False),
    max_size=200,
)


def test_suku_kecil_hilang_di_naif() -> None:
    # 1e-16 < u = 1.1e-16, jadi 1.0 + 1e-16 selalu dibulatkan kembali ke 1.0.
    n = 100_000
    xs = [1.0] + [1e-16] * n
    eksak = math.fsum(xs)
    jumlah_abs = math.fsum(abs(x) for x in xs)

    assert naive_sum(xs) == 1.0
    assert eksak > 1.0
    # Kahan: galat ≤ 2u·Σ|x| (+ pembulatan fsum) → 2·EPS = 4u.
    assert abs(kahan_sum(xs) - eksak) <= 2 * EPS * jumlah_abs
    # Pairwise: galat ≤ ⌈log2 n⌉·u·Σ|x| → ⌈log2 n⌉·EPS memberi kelonggaran 2 kali.
    kedalaman = math.ceil(math.log2(len(xs)))
    assert abs(pairwise_sum(xs) - eksak) <= kedalaman * EPS * jumlah_abs


def test_kasus_tepi() -> None:
    for f in (naive_sum, kahan_sum, pairwise_sum):
        assert f([]) == 0.0
        assert f([2.5]) == 2.5
        assert f([0.5, 0.25]) == 0.75


def test_kahan_menerima_generator() -> None:
    assert kahan_sum(x / 4 for x in range(5)) == 2.5


@given(daftar_float)
def test_bound_galat(xs: list[float]) -> None:
    n = len(xs)
    eksak = math.fsum(xs)
    jumlah_abs = math.fsum(abs(x) for x in xs)

    assert abs(naive_sum(xs) - eksak) <= n * EPS * jumlah_abs
    assert abs(kahan_sum(xs) - eksak) <= 2 * EPS * jumlah_abs
    kedalaman = math.ceil(math.log2(n)) if n >= 2 else 0
    assert abs(pairwise_sum(xs) - eksak) <= kedalaman * EPS * jumlah_abs
