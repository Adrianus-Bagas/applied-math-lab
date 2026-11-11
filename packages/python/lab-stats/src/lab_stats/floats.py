"""Latihan aritmetika floating-point (L0.10, sesi 1)."""

import math


def machine_epsilon() -> float:
    """Mencari epsilon mesin (jarak dari 1.0 ke float berikutnya) lewat percobaan."""
    eps = 1.0
    # Langkah 1: selama 1.0 + eps / 2 masih lebih besar dari 1.0, bagi dua eps.
    while 1.0 + eps / 2 > 1.0:
        eps /= 2
    # Langkah 2: kembalikan eps.
    return eps


def ulp(x: float) -> float:
    """Jarak antar-float di sekitar x. Hanya untuk bilangan normal (bukan 0, inf, NaN)."""
    if not math.isfinite(x) or x == 0.0:
        raise ValueError("ulp is only defined for finite, nonzero x")
    # Langkah 1: pecah |x| menjadi (m, e) dengan math.frexp.
    _, e = math.frexp(x)
    # Langkah 2: kembalikan 2**(e - 53) dengan math.ldexp.
    return math.ldexp(1.0, e - 53)


def quadratic_roots_naive(a: float, b: float, c: float) -> tuple[float, float]:
    """Rumus abc apa adanya. Sengaja dibiarkan untuk dibandingkan di tes."""
    s = math.sqrt(b * b - 4.0 * a * c)
    x1 = (-b - s) / (2.0 * a)
    x2 = (-b + s) / (2.0 * a)
    return (min(x1, x2), max(x1, x2))


def quadratic_roots(a: float, b: float, c: float) -> tuple[float, float]:
    """Akar real ax² + bx + c = 0 tanpa pembatalan, terurut naik."""
    disc = b * b - 4.0 * a * c
    if a == 0.0 or disc < 0.0:
        raise ValueError("need a != 0 and a non-negative discriminant")
    # Langkah 1: s = akar dari disc.
    s = math.sqrt(disc)
    # Langkah 2: hitung q dengan rumus (★); pakai math.copysign untuk sign(b)·s.
    q = -(b + math.copysign(s, b)) / 2
    # Langkah 3: kalau q == 0.0 (terjadi saat b = 0 dan c = 0), kembalikan (0.0, 0.0).
    if q == 0:
        return (0.0, 0.0)
    # Langkah 4: x1 = q / a, x2 = c / q.
    x1 = q / a
    x2 = c / q
    # Langkah 5: kembalikan (yang kecil, yang besar).
    return (min(x1, x2), max(x1, x2))
