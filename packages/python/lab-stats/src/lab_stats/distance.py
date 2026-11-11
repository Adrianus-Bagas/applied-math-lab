"""Latihan vektorisasi: matriks jarak Euclid (L0.10, sesi 3)."""

import math

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]


def pairwise_dist_loop(a: FloatArray, b: FloatArray) -> FloatArray:
    """Matriks jarak dengan loop ganda. Lambat; dipakai sebagai oracle."""
    n, m = a.shape[0], b.shape[0]
    out = np.empty((n, m))
    for i in range(n):
        for j in range(m):
            out[i, j] = math.hypot(a[i, 0] - b[j, 0], a[i, 1] - b[j, 1])
    return out


def pairwise_dist(a: FloatArray, b: FloatArray) -> FloatArray:
    """Matriks jarak (n, m) dari titik a (n, 2) dan b (m, 2), lewat broadcasting."""
    # Langkah 1: sisipkan sumbu baru dengan None supaya a menjadi (n, 1, 2)
    #            dan b menjadi (1, m, 2), lalu kurangkan → diff berbentuk (n, m, 2).
    diff = a[:, None, :] - b[None, :, :]
    # Langkah 2: kuadratkan diff dan jumlahkan sepanjang sumbu terakhir → (n, m).
    dist_square = np.sum(diff**2, axis=-1)
    # Langkah 3: kembalikan akarnya dengan np.sqrt.
    return np.sqrt(dist_square)


def pairwise_dist_gram(a: FloatArray, b: FloatArray) -> FloatArray:
    """Matriks jarak lewat ‖a‖² + ‖b‖² - 2a·b. Cepat, tetapi rawan pembatalan."""
    # Langkah 1: na2 = jumlah kuadrat tiap baris a → (n,); nb2 untuk b → (m,).
    na2 = (a**2).sum(axis=-1)
    nb2 = (b**2).sum(axis=-1)
    # Langkah 2: g = a @ b.T → (n, m), berisi semua a_i · b_j.
    g = a @ b.T
    # Langkah 3: d2 = na2[:, None] + nb2[None, :] - 2.0 * g.
    d2 = na2[:, None] + nb2[None, :] - 2.0 * g
    # Langkah 4: jepit nilai negatif ke 0 dengan np.maximum(d2, 0.0).
    dist_square = np.maximum(d2, 0.0)
    # Langkah 5: kembalikan akarnya.
    return np.sqrt(dist_square)
