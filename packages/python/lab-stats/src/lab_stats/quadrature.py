"""Kuadratur tervektorisasi (L0.10, sesi 5). Prototipe NumPy dari lab-numerics::quad."""

from collections.abc import Callable

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]
Integrand = Callable[[FloatArray], FloatArray]


def trapezoid(f: Integrand, a: float, b: float, n: int) -> float:
    """Aturan trapesium dengan n selang; f dipanggil sekali dengan seluruh titik."""
    if n < 1:
        raise ValueError("n must be at least 1")
    # Langkah 1: x = n + 1 titik berjarak sama dari a ke b (np.linspace); y = f(x).
    x = np.linspace(a, b, n + 1)
    y = f(x)
    # Langkah 2: h = (b - a) / n.
    h = (b - a) / n
    # Langkah 3: kembalikan h * (jumlah semua y - setengah dari jumlah dua ujung),
    #            dibungkus float(...) supaya hasilnya float Python biasa.
    result = h * (y.sum() - (y[0] + y[-1]) / 2)
    return float(result)


def simpson(f: Integrand, a: float, b: float, n: int) -> float:
    """Aturan Simpson 1/3 dengan n selang (n genap); f dipanggil sekali."""
    if n < 2 or n % 2 != 0:
        raise ValueError("n must be even and at least 2")
    # Langkah 1: x, y, h seperti di trapezoid.
    x = np.linspace(a, b, n + 1)
    y = f(x)
    h = (b - a) / n
    # Langkah 2: total = y[0] + y[-1]
    #                    + 4 x jumlah y berindeks ganjil  (slicing 1:-1:2)
    #                    + 2 x jumlah y berindeks genap bagian dalam (slicing 2:-1:2).
    total = y[0] + y[-1] + 4 * y[1:-1:2].sum() + 2 * y[2:-1:2].sum()
    # Langkah 3: kembalikan float(h * total / 3).
    result = h * total / 3
    return float(result)
