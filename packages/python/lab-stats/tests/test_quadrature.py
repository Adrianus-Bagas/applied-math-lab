import math
import sys

import numpy as np
import pytest
from lab_stats.quadrature import FloatArray, simpson, trapezoid
from lab_stats.tolerance import is_close
from scipy import integrate

EPS = sys.float_info.epsilon


def gauss(x: FloatArray) -> FloatArray:
    # exp(-x²): tidak punya antiturunan elementer, jadi butuh oracle numerik.
    return np.exp(-x * x)


def test_hitung_tangan() -> None:
    assert trapezoid(lambda x: x, 0.0, 1.0, 4) == 0.5
    # Simpson eksak untuk polinom sampai derajat 3: ∫₀² x³ dx = 4.
    assert is_close(simpson(lambda x: x**3, 0.0, 2.0, 2), 4.0, rel_tol=2 * EPS)


def test_cocok_dengan_scipy_quad() -> None:
    a, b, n = 0.0, 2.0, 100
    h = (b - a) / n
    oracle, galat_oracle = integrate.quad(lambda t: math.exp(-t * t), a, b)

    # max|f''| = 2 dan max|f⁗| = 12, keduanya di x = 0.
    batas_trapesium = (b - a) * h**2 / 12 * 2.0
    batas_simpson = (b - a) * h**4 / 180 * 12.0

    assert is_close(trapezoid(gauss, a, b, n), oracle, abs_tol=batas_trapesium + galat_oracle)
    assert is_close(simpson(gauss, a, b, n), oracle, abs_tol=batas_simpson + galat_oracle)


@pytest.mark.parametrize(("aturan", "orde"), [(trapezoid, 2.0), (simpson, 4.0)])
def test_orde_empiris(aturan, orde: float) -> None:  # type: ignore[no-untyped-def]
    eksak = math.e - 1.0  # ∫₀¹ eˣ dx
    galat_n = abs(aturan(np.exp, 0.0, 1.0, 20) - eksak)
    galat_2n = abs(aturan(np.exp, 0.0, 1.0, 40) - eksak)
    assert math.log2(galat_n / galat_2n) == pytest.approx(orde, abs=0.1)


@pytest.mark.parametrize("aturan", [trapezoid, simpson])
def test_f_dipanggil_sekali(aturan) -> None:  # type: ignore[no-untyped-def]
    panggilan = 0

    def f(x: FloatArray) -> FloatArray:
        nonlocal panggilan
        panggilan += 1
        return np.sin(x)

    aturan(f, 0.0, 1.0, 10)
    assert panggilan == 1


def test_menolak_n_tidak_sah() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        trapezoid(np.sin, 0.0, 1.0, 0)
    with pytest.raises(ValueError, match="even"):
        simpson(np.sin, 0.0, 1.0, 3)
