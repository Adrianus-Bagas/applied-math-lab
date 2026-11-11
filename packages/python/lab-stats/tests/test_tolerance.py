import math
import sys

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from lab_stats.summation import kahan_sum
from lab_stats.tolerance import is_close

semua_float = st.floats(allow_nan=True, allow_infinity=True)
EPS = sys.float_info.epsilon


@given(
    semua_float,
    semua_float,
    st.floats(min_value=0.0, max_value=1.0),
    st.floats(min_value=0.0, max_value=1e3),
)
def test_sama_dengan_math_isclose(a: float, b: float, rel: float, abs_: float) -> None:
    harap = math.isclose(a, b, rel_tol=rel, abs_tol=abs_)
    assert is_close(a, b, rel_tol=rel, abs_tol=abs_) == harap


def test_bawaan_berarti_sama_persis() -> None:
    assert is_close(0.5, 0.5)
    assert not is_close(0.1 + 0.2, 0.3)
    assert is_close(0.1 + 0.2, 0.3, rel_tol=2.0**-52)


def test_menolak_toleransi_negatif() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        is_close(1.0, 1.0, rel_tol=-1.0)


def test_a_kahan_vs_fsum() -> None:
    # Data positif semua, jadi Σ|x| = |Σx|.
    rng = np.random.default_rng(0)
    xs = rng.uniform(1.0, 2.0, 1000).tolist()
    rtol = 2 * EPS
    assert is_close(kahan_sum(xs), math.fsum(xs), rel_tol=rtol)


def test_b_exp_log_bolak_balik() -> None:
    # exp(log(x)) seharusnya x. Anggap log dan exp masing-masing meleset ≤ EPS relatif.
    for x in np.geomspace(1e-3, 1e3, 61).tolist():
        rtol = (abs(math.log(x)) + 1) * EPS  # GANTI: boleh bergantung pada x; pakai κ dari exp
        assert is_close(math.exp(math.log(x)), x, rel_tol=rtol)


def test_d_log_exp_bolak_balik() -> None:
    for x in np.linspace(1.0, 100.0, 100).tolist():
        rtol = (1 / x + 1) * EPS
        assert is_close(math.log(math.exp(x)), x, rel_tol=rtol)


def test_c_trapesium_sin() -> None:
    # ∫₀^π sin x dx = 2, dihampiri aturan trapesium dengan n selang.
    n = 1000
    x = np.linspace(0.0, math.pi, n + 1)
    hampiran = float(np.trapezoid(np.sin(x), x))
    h = math.pi / n
    atol = math.pi * h**2 / 12  # GANTI: ini galat pemotongan, bukan pembulatan
    assert is_close(hampiran, 2.0, abs_tol=atol)
