"""Tes aliran bilangan acak bernama (mealops.generator.rng)."""

import numpy as np
import pytest
from mealops.generator.rng import SEED_MAKS, Aliran, buat_aliran

# ---------------------------------------------------------------------------
# 1. Determinisme: (seed, nama) yang sama → barisan yang sama
# ---------------------------------------------------------------------------


def test_deterministik() -> None:
    a = buat_aliran(42, Aliran.LOKASI).integers(0, 10**9, 5)
    b = buat_aliran(42, Aliran.LOKASI).integers(0, 10**9, 5)
    np.testing.assert_array_equal(a, b)


# ---------------------------------------------------------------------------
# 2. Independensi: nama atau seed berbeda → barisan berbeda
# ---------------------------------------------------------------------------


def test_aliran_berbeda_per_nama() -> None:
    # TODO: bandingkan LOKASI vs DEMAND dengan seed 42; harus TIDAK sama
    lokasi = buat_aliran(42, Aliran.LOKASI).integers(0, 10**9, 5)
    demand = buat_aliran(42, Aliran.DEMAND).integers(0, 10**9, 5)
    assert not np.array_equal(lokasi, demand)


def test_seed_berbeda() -> None:
    # TODO: seed 42 vs 43 untuk aliran yang sama; harus TIDAK sama
    a = buat_aliran(42, Aliran.LOKASI).integers(0, 10**9, 5)
    b = buat_aliran(43, Aliran.LOKASI).integers(0, 10**9, 5)
    assert not np.array_equal(a, b)


# ---------------------------------------------------------------------------
# 3. Validasi seed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [-1, SEED_MAKS + 1])
def test_seed_di_luar_rentang(seed: int) -> None:
    with pytest.raises(ValueError, match=r"seed harus di rentang"):
        buat_aliran(seed, Aliran.LOKASI)


@pytest.mark.parametrize("seed", [True, False, 1.0, "42"])
def test_seed_bukan_bulat(seed: object) -> None:
    with pytest.raises(TypeError, match=r"seed harus bilangan bulat"):
        buat_aliran(seed, Aliran.LOKASI)  # type: ignore[arg-type]


@pytest.mark.parametrize("seed", [0, 1, SEED_MAKS])
def test_seed_batas_diterima(seed: int) -> None:
    buat_aliran(seed, Aliran.LOKASI)  # tidak boleh melempar


# ---------------------------------------------------------------------------
# 4. Nilai beku: menjaga instans lama tetap sama lintas versi NumPy
# ---------------------------------------------------------------------------

# Dihitung dengan NumPy 2.5.3: PCG64(SeedSequence(42, spawn_key=(k,))), integers(0, 10**9, 5).
NILAI_BEKU = {
    Aliran.LOKASI: [497403284, 916744157, 581440256, 910986667, 218016674],
    Aliran.DEMAND: [74695622, 467490779, 182402882, 46448896, 656055070],
    Aliran.JENDELA: [703192112, 71239202, 771961734, 710159722, 106625338],
}


@pytest.mark.parametrize("nama", list(Aliran))
def test_nilai_beku(nama: Aliran) -> None:
    hasil = buat_aliran(42, nama).integers(0, 10**9, 5).tolist()
    assert hasil == NILAI_BEKU[nama]


# ---------------------------------------------------------------------------
# 5. Nomor aliran tidak boleh berubah
# ---------------------------------------------------------------------------


def test_nomor_aliran_tetap() -> None:
    # Mengubah nomor = mengubah semua instans yang pernah dirilis.
    assert {a.name: a.value for a in Aliran} == {"LOKASI": 0, "DEMAND": 1, "JENDELA": 2}
