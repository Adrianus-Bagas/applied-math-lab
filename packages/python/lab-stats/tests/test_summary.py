import math

import pytest
from hypothesis import given
from hypothesis import strategies as st
from lab_stats import summarize


def test_known_values() -> None:
    s = summarize([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert s.n == 8
    assert s.mean == pytest.approx(5.0)
    assert s.std == pytest.approx(math.sqrt(32 / 7))  # sum (x - mean)^2 = 32, ddof=1


def test_single_sample_has_nan_std() -> None:
    s = summarize([3.0])
    assert s.n == 1
    assert math.isnan(s.std)


@pytest.mark.parametrize("bad", [[], [1.0, float("nan")], [[1.0, 2.0]]])
def test_rejects_invalid_input(bad: list[object]) -> None:
    with pytest.raises(ValueError, match="samples"):
        summarize(bad)


@given(st.lists(st.floats(min_value=-1e6, max_value=1e6), min_size=1))
def test_mean_lies_between_min_and_max(xs: list[float]) -> None:
    s = summarize(xs)
    tol = 1e-9 * max(1.0, abs(s.minimum), abs(s.maximum))
    assert s.minimum - tol <= s.mean <= s.maximum + tol
