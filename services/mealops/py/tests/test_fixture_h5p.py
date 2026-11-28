import json
from pathlib import Path
from typing import Any

import pytest
from mealops.checks import check_input
from mealops.instance import Instance, Production

FIXTURES = Path(__file__).resolve().parents[4] / "datasets" / "mealops" / "fixtures"


@pytest.fixture(scope="module")
def h5p() -> dict[str, Any]:
    with (FIXTURES / "h5p.instance.json").open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


@pytest.fixture(scope="module")
def prod(h5p: dict[str, Any]) -> Production:
    p = Instance.model_validate(h5p).production
    assert p is not None, "H5-P wajib punya production"
    return p


def test_h5p_input_valid(h5p: dict[str, Any]) -> None:
    assert check_input(Instance.model_validate(h5p)) == []


def test_h5p_parameter(h5p: dict[str, Any], prod: Production) -> None:
    # §7.9: |K| = 2, rho = 2, lambda = 10, |B| = 3, H^max = 120; dapur §5.5
    assert h5p["fleet"] == {"vehicles": 2, "capacity": 100, "max_trips": 2, "load_time": 10}
    assert (prod.kitchen_start, prod.batch_capacity, prod.max_batches) == (300, 100, 3)
    assert (prod.cook_fixed, prod.cook_per_1000) == (30, 200)
    assert (prod.pack_fixed, prod.pack_per_1000) == (10, 100)
    assert prod.holding_max == 120


def test_h5p_sama_dengan_h5_selain_armada_dan_dapur(h5p: dict[str, Any]) -> None:
    with (FIXTURES / "h5.instance.json").open(encoding="utf-8") as f:
        h5: dict[str, Any] = json.load(f)
    for key in ("kitchen", "points", "nodes", "travel_time", "distance"):
        assert h5p[key] == h5[key], key


# (D, theta^c, theta^p): q_j §7.3, batch §5.5, batch D1 §7.9, dan batas
THETA = [
    (25, 35, 13),
    (40, 38, 14),
    (20, 34, 12),
    (35, 37, 14),
    (15, 33, 12),
    (75, 45, 18),  # §5.5 batch {2, 4}
    (60, 42, 16),  # §5.5 batch {1, 3, 5}
    (80, 46, 18),  # §7.9 D1 batch {1, 2, 5}
    (100, 50, 20),  # D^max
    (1, 31, 11),  # 0,2 dan 0,1 menit dibulatkan ke atas jadi 1
    (0, 0, 0),  # batch kosong
]


@pytest.mark.parametrize(("portions", "cook", "pack"), THETA)
def test_h5p_durasi_batch(prod: Production, portions: int, cook: int, pack: int) -> None:
    assert prod.cook_minutes(portions) == cook
    assert prod.pack_minutes(portions) == pack
