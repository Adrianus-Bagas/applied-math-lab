from collections import Counter

import pytest
from mealops.testing.oracle_model_a import set_partitions


def _as_set(partition: list[list[int]]) -> frozenset[frozenset[int]]:
    return frozenset(frozenset(block) for block in partition)


def test_tiga_item_semua_partisi() -> None:
    # Contoh di konsep: 000, 001, 010, 011, 012 -> 5 partisi (bilangan Bell B_3)
    got = list(set_partitions([1, 2, 3], 3))
    expected = [
        [[1, 2, 3]],
        [[1, 2], [3]],
        [[1, 3], [2]],
        [[1], [2, 3]],
        [[1], [2], [3]],
    ]
    assert {_as_set(p) for p in got} == {_as_set(p) for p in expected}
    assert len(got) == 5


@pytest.mark.parametrize(
    ("n", "max_blocks", "count"),
    [
        (3, 2, 4),  # 2^(3-1)
        (4, 4, 15),  # Bell B_4
        (5, 2, 16),  # 2^(5-1): ruang pencarian H5 dengan |K| = 2
        (5, 3, 41),  # 1 + 15 + 25
        (5, 5, 52),  # Bell B_5
    ],
)
def test_jumlah_partisi(n: int, max_blocks: int, count: int) -> None:
    got = list(set_partitions(list(range(1, n + 1)), max_blocks))
    assert len(got) == count
    # tidak ada partisi yang muncul dua kali
    assert len({_as_set(p) for p in got}) == count


def test_stirling_jenis_kedua_n5() -> None:
    # S(5, k) = banyak partisi 5 item menjadi tepat k blok
    got = Counter(len(p) for p in set_partitions([1, 2, 3, 4, 5], 5))
    assert got == {1: 1, 2: 15, 3: 25, 4: 10, 5: 1}


def test_setiap_item_tepat_sekali_dan_blok_tidak_kosong() -> None:
    items = [2, 4, 1, 5, 3]
    for p in set_partitions(items, 3):
        assert all(len(block) >= 1 for block in p)
        assert sorted(x for block in p for x in block) == sorted(items)


def test_list_kosong() -> None:
    # Satu-satunya partisi himpunan kosong adalah partisi tanpa blok
    assert list(set_partitions([], 2)) == [[]]
