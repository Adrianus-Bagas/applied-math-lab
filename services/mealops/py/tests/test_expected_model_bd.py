import json
from pathlib import Path
from typing import Any

import pytest
from mealops.checks import check_input
from mealops.instance import Instance
from mealops.testing.oracle_model_a import apply_patch

FIXTURES = Path(__file__).resolve().parents[4] / "datasets" / "mealops" / "fixtures"


def _load(name: str) -> dict[str, Any]:
    with (FIXTURES / name).open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


CASES = _load("expected.model-bd.json")["cases"]


def _plans(expect: dict[str, Any]) -> list[dict[str, Any]]:
    """Semua rencana di satu kasus: field 'plan' dan isi 'optimal_plans'."""
    # Langkah 1: mulai dari list kosong
    plans = []
    # Langkah 2: bila "plan" ada di expect -> tambahkan expect["plan"]
    if "plan" in expect:
        plans.append(expect["plan"])
    # Langkah 3: bila "optimal_plans" ada -> tambahkan semua isinya (petunjuk: list.extend)
    if "optimal_plans" in expect:
        plans.extend(expect["optimal_plans"])
    # Langkah 4: return list-nya
    return plans


def test_nama_kasus_unik() -> None:
    names = [c["name"] for c in CASES]
    assert len(names) == len(set(names)) == 15


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_patch_menghasilkan_input_valid(case: dict[str, Any]) -> None:
    # Langkah 1: data = apply_patch(_load(case["base"]), case["patch"])
    data = apply_patch(_load(case["base"]), case["patch"])
    # Langkah 2: assert check_input(Instance.model_validate(data)) == []
    assert check_input(Instance.model_validate(data)) == []


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_rencana_memuat_setiap_node_tepat_sekali(case: dict[str, Any]) -> None:
    n = len(apply_patch(_load(case["base"]), case["patch"])["nodes"])
    for plan in _plans(case["expect"]):
        # Langkah 1: kumpulkan semua node dari plan["vehicles"]: kendaraan -> trip -> node
        #   (tiga lapis loop, atau satu list comprehension bertingkat)
        nodes_vehicles = [node for vehicle in plan["vehicles"] for trip in vehicle for node in trip]
        # Langkah 2: assert sorted(hasil langkah 1) == list(range(1, n + 1))
        assert sorted(nodes_vehicles) == list(range(1, n + 1))
        # Langkah 3: bila "batches" ada di plan: lakukan hal yang sama untuk plan["batches"]
        #   (dua lapis: batch -> node)
        if "batches" in plan:
            nodes_batches = [node for batch in plan["batches"] for node in batch]
            assert sorted(nodes_batches) == list(range(1, n + 1))
