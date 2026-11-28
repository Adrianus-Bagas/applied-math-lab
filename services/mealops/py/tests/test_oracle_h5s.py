import copy
import json
from pathlib import Path
from typing import Any

import pytest
from mealops.checks import check_input
from mealops.instance import Instance
from mealops.testing.oracle_model_a import enumerate_solutions, node_data

FIXTURES = Path(__file__).resolve().parents[4] / "datasets" / "mealops" / "fixtures"


@pytest.fixture(scope="module")
def h5s() -> dict[str, Any]:
    with (FIXTURES / "h5s.instance.json").open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


def test_h5s_input_valid(h5s: dict[str, Any]) -> None:
    assert check_input(Instance.model_validate(h5s)) == []


def test_h5s_pemecahan_demand(h5s: dict[str, Any]) -> None:
    # §4.10: titik 2 berdemand 120 -> node 2 (100) dan node 6 (20), selokasi
    assert [n["demand"] for n in h5s["nodes"]] == [25, 100, 20, 35, 15, 20]
    assert h5s["nodes"][1]["point"] == h5s["nodes"][5]["point"] == 2
    assert sum(n["demand"] for n in h5s["nodes"]) == 215
    assert h5s["fleet"]["max_trips"] == 2
    assert h5s["fleet"]["load_time"] == 10


def test_h5s_jendela_efektif(h5s: dict[str, Any]) -> None:
    # Kolom a'_j, d'_j tabel §4.10 (node 6 mewarisi jendela titik 2, s_6 = 10)
    got = [(node_data(h5s, j).a_eff, node_data(h5s, j).d_eff) for j in range(1, 7)]
    assert got == [(560, 610), (510, 570), (600, 645), (500, 530), (580, 610), (510, 570)]


def test_h5s_satu_trip_tidak_layak(h5s: dict[str, Any]) -> None:
    # Tabel enumerasi §4.10: |K| = 2, rho = 1 -> 0 solusi (perlu 3 trip).
    # Model B dengan rho = 1 sama dengan Model A (J2), jadi oracle Model A berlaku.
    assert enumerate_solutions(h5s) == []


def test_h5s_tiga_kendaraan_satu_trip(h5s: dict[str, Any]) -> None:
    # Tabel enumerasi §4.10: |K| = 3, rho = 1 -> 11 solusi, optimum 44: (2), (4,3), (6,1,5)
    inst = copy.deepcopy(h5s)
    inst["fleet"]["vehicles"] = 3
    sols = enumerate_solutions(inst)
    assert len(sols) == 11
    assert sols[0].cost == 4400
    assert sols[0].routes == ((2,), (4, 3), (6, 1, 5))
