import math
import sys

import numpy as np
from lab_stats.distance import pairwise_dist, pairwise_dist_gram, pairwise_dist_loop

EPS = sys.float_info.epsilon


def _titik(seed: int, n: int, skala: float) -> np.ndarray:
    # Generator ber-seed: hasilnya sama setiap kali tes dijalankan.
    rng = np.random.default_rng(seed)
    return rng.uniform(0.0, skala, size=(n, 2))


def test_hitung_tangan() -> None:
    a = np.array([[0.0, 0.0], [3.0, 4.0]])
    b = np.array([[0.0, 0.0], [3.0, 0.0], [6.0, 8.0]])
    harap = np.array([[0.0, 3.0, 10.0], [5.0, 4.0, 5.0]])
    for f in (pairwise_dist_loop, pairwise_dist, pairwise_dist_gram):
        hasil = f(a, b)
        assert hasil.shape == (2, 3)
        assert hasil.dtype == np.float64
        np.testing.assert_array_equal(hasil, harap)


def test_broadcast_cocok_dengan_loop() -> None:
    a, b = _titik(1, 50, 1e4), _titik(2, 40, 1e4)
    # Selisih, kuadrat, jumlah, akar: beberapa pembulatan relatif ≤ u, tanpa pembesar.
    np.testing.assert_allclose(
        pairwise_dist(a, b), pairwise_dist_loop(a, b), rtol=4 * EPS, atol=0.0
    )


def test_gram_dalam_bound() -> None:
    a, b = _titik(3, 50, 1e4), _titik(4, 40, 1e4)
    oracle = pairwise_dist_loop(a, b)
    hasil = pairwise_dist_gram(a, b)
    na2 = (a * a).sum(axis=1)[:, None]
    nb2 = (b * b).sum(axis=1)[None, :]
    # |d̂ - d| ≤ √τ dengan τ = 8u(‖a‖² + ‖b‖²); 8·EPS = 16u memberi kelonggaran 2 kali.
    batas = np.sqrt(8 * EPS * (na2 + nb2)) + 4 * EPS * oracle
    assert np.all(np.isfinite(hasil))
    assert np.all(np.abs(hasil - oracle) <= batas)


def test_gram_rusak_untuk_titik_berdekatan_jauh_dari_asal() -> None:
    a = 1e6 + _titik(5, 20, 1.0)
    b = a + 1e-3  # tiap b_i berjarak √2 mm dari a_i
    sejati = math.sqrt(2.0) * 1e-3

    # Cara langsung: galatnya hanya dari pembulatan input, ulp(1e6)/1e-3 ≈ 1e-7.
    d_langsung = np.diagonal(pairwise_dist(a, b))
    np.testing.assert_allclose(d_langsung, sejati, rtol=1e-6)

    # Cara Gram: d̂² hanya bisa kelipatan ulp(2e12) ≈ 2.4e-4, padahal d² = 2e-6.
    d_gram = np.diagonal(pairwise_dist_gram(a, b))
    assert np.all(np.isfinite(d_gram))
    assert np.all(np.abs(d_gram - sejati) > 0.5 * sejati)
