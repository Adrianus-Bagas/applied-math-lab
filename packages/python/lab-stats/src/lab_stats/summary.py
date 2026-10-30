"""Statistik deskriptif bersama untuk Applied Math Lab."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike


@dataclass(frozen=True, slots=True)
class Summary:
    n: int
    mean: float
    std: float  # simpangan baku sampel (ddof=1); NaN bila n < 2
    minimum: float
    maximum: float


def summarize(samples: ArrayLike) -> Summary:
    """Ringkasan deskriptif untuk sampel 1-D yang berhingga dan tidak kosong."""
    x = np.asarray(samples, dtype=np.float64)
    if x.ndim != 1 or x.size == 0:
        raise ValueError("samples harus array 1-D yang tidak kosong")
    if not np.all(np.isfinite(x)):
        raise ValueError("samples mengandung NaN atau inf")
    std = float(np.std(x, ddof=1)) if x.size >= 2 else float("nan")
    return Summary(
        n=int(x.size),
        mean=float(np.mean(x)),
        std=std,
        minimum=float(x.min()),
        maximum=float(x.max()),
    )
