"""Test oracle: lab_numerics (Rust) vs NumPy, dengan toleransi dari analisis galat."""

import math
import sys

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from lab_numerics import mean_variance

EPS = sys.float_info.epsilon
SAFETY = 4.0


def test_hitung_tangan() -> None:
    assert mean_variance([2.0, 4, 4, 4, 5, 5, 7, 9], ddof=0) == pytest.approx((5.0, 4.0))
    assert mean_variance([2.0, 4, 4, 4, 5, 5, 7, 9], ddof=1) == pytest.approx((5.0, 32 / 7))


def test_stabil_end_to_end() -> None:
    xs = [1e12 + d for d in (4.0, 7.0, 13.0, 16.0)]
    # Semua langkah Welford di data ini eksak di f64 (lihat test Rust).
    assert mean_variance(xs, ddof=1) == (1e12 + 10.0, 30.0)


@pytest.mark.parametrize(("xs", "ddof"), [([], 0), ([3.0], 1), ([1.0, 2.0], 2)])
def test_tidak_terdefinisi(xs: list[float], ddof: int) -> None:
    assert mean_variance(xs, ddof) is None


def test_kontrak_tipe() -> None:
    # Bukan float64 array dan bukan Vec<f64> → fallback numpy.asarray(dtype=float64) gagal.
    with pytest.raises(ValueError, match="could not convert"):
        mean_variance(["a", "b"])  # type: ignore[list-item]
    with pytest.raises(OverflowError):
        mean_variance([1.0, 2.0], ddof=-1)


def test_list_dan_ndarray_identik_bit() -> None:
    xs = [0.1 * k for k in range(1000)]
    # Data dan algoritma sama → hasil identik bit, bukan sekadar dekat.
    assert mean_variance(xs, 1) == mean_variance(np.asarray(xs), 1)


def test_view_berstride() -> None:
    view = np.arange(10.0)[::2]
    assert not view.flags.c_contiguous
    assert mean_variance(view, 1) == mean_variance(view.copy(), 1)


finite = st.floats(
    min_value=-1e6,
    max_value=1e6,
    allow_nan=False,
    allow_infinity=False,
    allow_subnormal=False,
)


@given(xs=st.lists(finite, min_size=2, max_size=200), ddof=st.integers(0, 1))
def test_oracle_numpy(xs: list[float], ddof: int) -> None:
    result = mean_variance(xs, ddof)
    assert result is not None
    mean, var = result

    arr = np.asarray(xs, dtype=np.float64)
    n = arr.size
    mean_ref = float(arr.mean())
    var_ref = float(arr.var(ddof=ddof))

    # Mean: galat <= c * n * eps * max|x|
    tol_mean = SAFETY * n * EPS * float(np.max(np.abs(arr))) + 1e-300
    assert abs(mean - mean_ref) <= tol_mean

    # M2: galat <= c * n * eps * ||x||_2 * sqrt(M2)   (algoritma stabil, satu faktor kappa)
    m2_ref = var_ref * (n - ddof)
    tol_m2 = SAFETY * n * EPS * float(np.linalg.norm(arr)) * math.sqrt(m2_ref) + 1e-300
    assert abs(var - var_ref) <= tol_m2 / (n - ddof)
