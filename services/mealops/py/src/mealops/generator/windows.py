"""Jendela waktu titik layanan: valid (tingkat 1) dan a'_j ≤ d'_j secara konstruksi."""

from dataclasses import dataclass

import numpy as np

HARI = 1440  # menit; semua jam di [0, 1440)


@dataclass(frozen=True)
class JendelaTitik:
    a: int  # jam paling awal menerima
    m: int  # waktu konsumsi
    delta: int  # buffer

    @property
    def d(self) -> int:
        """Deadline kedatangan d = m - δ (diturunkan, tidak disimpan)."""
        return self.m - self.delta


def bentuk_jendela(
    tau0: int, s_maks: int, e0: int, m_acak: int, delta_tambah: int, lebar: int
) -> JendelaTitik:
    """Langkah 1–4 konsep E.2 untuk satu titik; tanpa RNG supaya bisa dites dengan tangan."""
    delta = s_maks + delta_tambah  # langkah 1
    # TODO 1: langkah 2, m = max(m_acak, e0 + tau0 + delta)
    m = max(m_acak, e0 + tau0 + delta)
    if m >= HARI:
        raise ValueError(f"waktu konsumsi {m} melewati satu hari; perkecil jarak atau buffer")
    # TODO 2: langkah 3 dan 4
    d = m - delta
    a = max(0, d - lebar)
    return JendelaTitik(a=a, m=m, delta=delta)


def sampel_jendela(
    rng: np.random.Generator,
    tau0: list[int],
    s_maks: list[int],
    e0: int,
    m_min: int,
    m_maks: int,
    langkah_m: int,
    delta_tambah_min: int,
    delta_tambah_maks: int,
    lebar_min: int,
    lebar_maks: int,
) -> list[JendelaTitik]:
    """Tarik (δ⁺, m̃, w) per titik dengan urutan tetap, lalu bentuk_jendela."""
    hasil = []
    for t, s in zip(tau0, s_maks, strict=True):
        delta_tambah = int(rng.integers(delta_tambah_min, delta_tambah_maks, endpoint=True))
        # m̃ di grid: m_min + langkah · U{0, …, ⌊(m_maks - m_min)/langkah⌋}
        m_acak = m_min + langkah_m * int(
            rng.integers(0, np.floor((m_maks - m_min) / langkah_m), endpoint=True)
        )
        lebar = int(rng.integers(lebar_min, lebar_maks, endpoint=True))
        hasil.append(bentuk_jendela(t, s, e0, m_acak, delta_tambah, lebar))
    return hasil


def jam_tutup(
    jendela: list[JendelaTitik], s_maks: list[int], tau_pulang: list[int], l0_minimum: int
) -> int:
    """Langkah 5: l0 = max(l0_minimum, max_i (d_i + s_maks_i + τ_i0))."""
    # TODO 3: hitung, tolak bila ≥ HARI dengan pesan "melewati satu hari"
    l0 = max(
        [l0_minimum] + [w.d + s + t for w, s, t in zip(jendela, s_maks, tau_pulang, strict=True)]
    )
    if l0 >= HARI:
        raise ValueError("Melewati satu hari")
    return l0
