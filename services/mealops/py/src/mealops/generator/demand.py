"""Demand titik layanan, pemecahan "penuh dulu", waktu layan, dan ukuran armada."""

from dataclasses import dataclass

import numpy as np

from mealops.generator.geometry import bagi_atas


@dataclass(frozen=True)
class Potongan:
    """Satu node pengantaran: potongan demand dari titik layanan `titik` (mulai 1)."""

    titik: int
    q: int  # porsi
    s: int  # waktu layan, menit (sudah dibulatkan ke atas)


def sampel_demand(rng: np.random.Generator, n_titik: int, q_min: int, q_maks: int) -> list[int]:
    """q_i ~ Uniform bulat [q_min, q_maks], satu per titik, berurutan."""
    if not 1 <= q_min <= q_maks:
        raise ValueError("demand harus memenuhi 1 ≤ q_min ≤ q_maks")
    # TODO 1: list comprehension, int(rng.integers(..., endpoint=True))
    return [int(rng.integers(q_min, q_maks, endpoint=True)) for _ in range(n_titik)]


def pecah_demand(q: int, q_bar: int) -> list[int]:
    """Potongan "penuh dulu" (model.md §4.1): k-1 potongan q_bar lalu sisa r."""
    if q < 1 or q_bar < 1:
        raise ValueError("q dan q_bar harus ≥ 1")
    k = bagi_atas(q, q_bar)
    # TODO 2: r = q - (k - 1)·q_bar  (BUKAN q % q_bar)
    r = q - (k - 1) * q_bar
    # TODO 3: kembalikan [q_bar] * (k - 1) + [r]
    return [q_bar] * (k - 1) + [r]


def waktu_layan(q: int, s0: int, eta_per_1000: int) -> int:
    """s = s⁰ + ⌈η₁₀₀₀·q / 1000⌉, aritmetika bulat."""
    # TODO 4: satu baris dengan bagi_atas
    return s0 + bagi_atas(eta_per_1000 * q, 1000)


def bangun_node(demand: list[int], q_bar: int, s0: int, eta_per_1000: int) -> list[Potongan]:
    """Node berurutan per titik; potongan penuh lebih dulu."""
    return [
        Potongan(titik=i, q=qj, s=waktu_layan(qj, s0, eta_per_1000))
        for i, q in enumerate(demand, start=1)
        for qj in pecah_demand(q, q_bar)
    ]


def jumlah_kendaraan(total_q: int, kapasitas: int, rho: int, cadangan: int) -> int:
    """|K| = ⌈Σq / (Qρ)⌉ + cadangan; menjamin ⌈Σq/Q⌉ ≤ |K|ρ (konsep D.4)."""
    # TODO 5
    return bagi_atas(total_q, kapasitas * rho) + cadangan
