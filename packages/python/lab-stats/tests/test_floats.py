import math
import sys

import pytest
from hypothesis import given
from hypothesis import strategies as st
from lab_stats.floats import (
    machine_epsilon,
    quadratic_roots,
    quadratic_roots_naive,
    ulp,
)

EPS = sys.float_info.epsilon


def test_machine_epsilon() -> None:
    eps = machine_epsilon()
    assert eps == EPS == 2.0**-52
    assert 1.0 + eps > 1.0
    assert 1.0 + eps / 2 == 1.0


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        (1.0, 2.0**-52),
        (1.5, 2.0**-52),
        (2.0, 2.0**-51),
        (0.75, 2.0**-53),
        (1e16, 2.0),
        (-1.0, 2.0**-52),
    ],
)
def test_ulp_nilai_tangan(x: float, expected: float) -> None:
    assert ulp(x) == expected


@given(st.floats(min_value=1e-300, max_value=1e300))
def test_ulp_sama_dengan_math_ulp(x: float) -> None:
    assert ulp(x) == math.ulp(x)
    assert ulp(-x) == math.ulp(x)


@pytest.mark.parametrize("x", [0.0, math.inf, -math.inf, math.nan])
def test_ulp_menolak_input_tak_normal(x: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        ulp(x)


def test_akar_sederhana_eksak() -> None:
    assert quadratic_roots(1.0, -3.0, 2.0) == (1.0, 2.0)
    assert quadratic_roots(1.0, 0.0, 0.0) == (0.0, 0.0)


@pytest.mark.parametrize("b", [-1e8, 1e8])
def test_akar_stabil_saat_naif_gagal(b: float) -> None:
    # Akar sejati: ±1e8 dan ±1e-8 (selisihnya dari nilai ini < 1 ulp).
    # Versi stabil hanya melakukan beberapa pembulatan, masing-masing ≤ u = EPS/2,
    # tanpa faktor pembesar, jadi toleransi beberapa EPS sudah cukup.
    tol = 8 * EPS
    tanda = -math.copysign(1.0, b)
    kecil, besar = sorted(quadratic_roots(1.0, b, 1.0), key=abs)
    assert kecil == pytest.approx(tanda * 1e-8, rel=tol)
    assert besar == pytest.approx(tanda * 1e8, rel=tol)

    # Versi naif kehilangan hampir semua digit pada akar kecil.
    kecil_naif = min(quadratic_roots_naive(1.0, b, 1.0), key=abs)
    assert abs(kecil_naif - tanda * 1e-8) / 1e-8 > 0.1


def test_akar_menolak_input() -> None:
    with pytest.raises(ValueError, match="discriminant"):
        quadratic_roots(1.0, 0.0, 1.0)
    with pytest.raises(ValueError, match="discriminant"):
        quadratic_roots(0.0, 1.0, 1.0)
