"""Latihan galat penjumlahan (L0.10, sesi 2)."""

from collections.abc import Iterable, Sequence


def naive_sum(xs: Iterable[float]) -> float:
    """Penjumlahan kiri ke kanan. Pembanding untuk tes."""
    total = 0.0
    for x in xs:
        total += x
    return total


def kahan_sum(xs: Iterable[float]) -> float:
    """Penjumlahan terkompensasi Kahan."""
    total = 0.0
    comp = 0.0  # bagian yang "jatuh" pada penjumlahan sebelumnya
    for x in xs:
        # Langkah 1: y = x dikoreksi dengan comp.
        y = x - comp
        # Langkah 2: t = total + y.
        t = total + y
        # Langkah 3: comp = (t - total) - y. Kurungnya jangan diubah.
        comp = (t - total) - y
        # Langkah 4: total = t.
        total = t
    return total


def pairwise_sum(xs: Sequence[float]) -> float:
    """Penjumlahan berpasangan: belah dua, jumlahkan tiap separuh, gabung."""

    def _rec(lo: int, hi: int) -> float:
        # Menjumlahkan xs[lo], ..., xs[hi - 1].
        # Langkah 1: kalau rentangnya kosong, kembalikan 0.0;
        #            kalau isinya satu elemen, kembalikan elemen itu.
        length = hi - lo
        if length == 0:
            return 0.0
        if length == 1:
            return xs[lo]
        # Langkah 2: mid = titik tengah (pembagian bulat //).
        mid = (lo + hi) // 2
        # Langkah 3: kembalikan _rec separuh kiri + _rec separuh kanan.
        return _rec(lo, mid) + _rec(mid, hi)

    return _rec(0, len(xs))
