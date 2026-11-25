"""Aliran bilangan acak bernama untuk generator instans MealOps."""

from enum import IntEnum

import numpy as np

# Sama dengan batas seed antrean job (LAB-ADR-010): muat persis di float64/JSON.
SEED_MAKS = 2**53 - 1


class Aliran(IntEnum):
    """Nomor aliran per komponen. JANGAN ubah nomor setelah dirilis."""

    LOKASI = 0
    DEMAND = 1
    JENDELA = 2


def buat_aliran(seed: int, nama: Aliran) -> np.random.Generator:
    """Generator independen untuk satu komponen, ditentukan penuh oleh (seed, nama)."""
    # TODO 1: tolak seed di luar [0, SEED_MAKS] dan bool (ingat: bool turunan int)
    # bool turunan int, jadi harus dicek lebih dulu
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError(f"seed harus bilangan bulat, bukan {type(seed).__name__}")
    if not 0 <= seed <= SEED_MAKS:
        raise ValueError(f"seed harus di rentang [0, {SEED_MAKS}], dapat {seed}")
    # TODO 2: SeedSequence(entropy=seed, spawn_key=(int(nama),))
    seed_sequence = np.random.SeedSequence(entropy=seed, spawn_key=(int(nama),))
    # TODO 3: bungkus dengan PCG64 lalu Generator
    return np.random.Generator(np.random.PCG64(seed_sequence))
