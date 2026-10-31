"""Jeda retry eksponensial dengan equal jitter."""

from __future__ import annotations

import random


def backoff_seconds(
    attempt: int, *, base: float = 5.0, cap: float = 300.0, rng: random.Random
) -> float:
    """Jeda sebelum percobaan berikutnya, setelah percobaan ke-``attempt`` gagal.

    d = min(cap, base * 2**(attempt - 1)); hasil berada di [d/2, d].
    ``rng`` disuntikkan agar deterministik dalam test (semangat LAB-ADR-004).

    Raises:
        ValueError: bila attempt < 1, base <= 0, atau cap < base.
    """
    if attempt < 1 or base <= 0 or cap < base:
        raise ValueError("Parameter value is not valid")
    d = min(cap, base * 2.0 ** min(attempt - 1, 1023))
    delay = (d / 2) + rng.random() * (d / 2)

    return delay
