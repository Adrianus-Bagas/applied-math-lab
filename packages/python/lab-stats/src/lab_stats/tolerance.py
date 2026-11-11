"""Latihan toleransi perbandingan float (L0.10, sesi 4)."""

import math


def is_close(a: float, b: float, *, rel_tol: float = 0.0, abs_tol: float = 0.0) -> bool:
    """Perbandingan simetris: |a - b| ≤ max(rel_tol · max(|a|, |b|), abs_tol)."""
    if rel_tol < 0.0 or abs_tol < 0.0:
        raise ValueError("tolerances must be non-negative")
    # Langkah 1: kalau a == b, kembalikan True (ini juga menangani inf == inf).
    if a == b:
        return True
    # Langkah 2: kalau a atau b tidak berhingga (inf atau NaN), kembalikan False.
    if not (math.isfinite(a) and math.isfinite(b)):
        return False
    # Langkah 3: hitung selisih = |a - b| dan batas sesuai rumus di docstring.
    diff = abs(a - b)
    # Langkah 4: kembalikan selisih <= batas.
    return diff <= max(rel_tol * max(abs(a), abs(b)), abs_tol)
