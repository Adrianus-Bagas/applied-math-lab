import random

import pytest
from hypothesis import given
from hypothesis import strategies as st
from lab_worker.backoff import backoff_seconds


def test_rentang_percobaan_pertama() -> None:
    rng = random.Random(0)
    for _ in range(1000):
        assert 2.5 <= backoff_seconds(1, base=5.0, cap=300.0, rng=rng) <= 5.0


def test_tumbuh_eksponensial_lalu_dibatasi_cap() -> None:
    batas_atas = [5.0, 10.0, 20.0, 40.0, 80.0, 160.0, 300.0, 300.0]
    for k, d in enumerate(batas_atas, start=1):
        rng = random.Random(k)
        xs = [backoff_seconds(k, base=5.0, cap=300.0, rng=rng) for _ in range(500)]
        assert d / 2 <= min(xs)
        assert max(xs) <= d


def test_percobaan_sangat_besar_tidak_overflow() -> None:
    d = backoff_seconds(10_000, base=5.0, cap=300.0, rng=random.Random(1))
    assert 150.0 <= d <= 300.0


def test_deterministik_terhadap_seed() -> None:
    r1, r2 = random.Random(42), random.Random(42)
    assert [backoff_seconds(k, rng=r1) for k in range(1, 20)] == [
        backoff_seconds(k, rng=r2) for k in range(1, 20)
    ]


@pytest.mark.parametrize(
    ("attempt", "base", "cap"),
    [(0, 5.0, 300.0), (-1, 5.0, 300.0), (1, 0.0, 300.0), (1, 10.0, 5.0)],
)
def test_argumen_tidak_valid(attempt: int, base: float, cap: float) -> None:
    with pytest.raises(check=ValueError):
        backoff_seconds(attempt, base=base, cap=cap, rng=random.Random(0))


@given(
    attempt=st.integers(1, 10**6),
    base=st.floats(0.01, 100.0),
    extra=st.floats(0.0, 1000.0),
    seed=st.integers(0, 2**32),
)
def test_properti_rentang(attempt: int, base: float, extra: float, seed: int) -> None:
    cap = base + extra
    d = backoff_seconds(attempt, base=base, cap=cap, rng=random.Random(seed))
    # Pangkat dibatasi 1023 agar test sendiri tidak overflow; base*2**1023 bisa
    # menjadi inf (perkalian float tidak melempar error), dan min(cap, inf) = cap.
    hi = min(cap, base * 2.0 ** min(attempt - 1, 1023))
    assert hi / 2 <= d <= hi
