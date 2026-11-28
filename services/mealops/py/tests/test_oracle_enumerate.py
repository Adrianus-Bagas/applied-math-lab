import copy
import json
from pathlib import Path
from typing import Any

import pytest
from mealops.testing.oracle_model_a import enumerate_solutions

FIXTURES = Path(__file__).resolve().parents[4] / "datasets" / "mealops" / "fixtures"


@pytest.fixture(scope="module")
def h5() -> dict[str, Any]:
    with (FIXTURES / "h5.instance.json").open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


# Tabel "Semua solusi layak" model.md §3.5 (biaya dalam meter, rute tanpa label kendaraan)
H5_ALL = {
    (((2, 1, 5), (4, 3)), 3200),
    (((1, 5), (4, 2, 3)), 3400),
    (((2, 3), (4, 1, 5)), 3400),
    (((2, 1, 3), (4, 5)), 3600),
    (((4, 2, 1), (5, 3)), 3600),
    (((1, 3), (4, 2, 5)), 3800),
    (((2, 1), (4, 5, 3)), 3800),
    (((2, 5), (4, 1, 3)), 3800),
    (((2, 5, 3), (4, 1)), 4000),
}


def test_h5_sembilan_solusi_layak(h5: dict[str, Any]) -> None:
    sols = enumerate_solutions(h5)
    assert len(sols) == 9
    assert {(s.routes, s.cost) for s in sols} == H5_ALL


def test_h5_optimum_unik_s1(h5: dict[str, Any]) -> None:
    sols = enumerate_solutions(h5)
    assert sols[0].routes == ((2, 1, 5), (4, 3))
    assert sols[0].cost == 3200
    assert sols[1].cost > sols[0].cost  # unik


def test_h5_terurut_menurut_biaya(h5: dict[str, Any]) -> None:
    costs = [s.cost for s in enumerate_solutions(h5)]
    assert costs == [3200, 3400, 3400, 3600, 3600, 3800, 3800, 3800, 4000]


def test_v2_satu_kendaraan_tidak_layak(h5: dict[str, Any]) -> None:
    # V2 (§3.8): |K| = 1, total demand 135 > 100
    inst = copy.deepcopy(h5)
    inst["fleet"]["vehicles"] = 1
    assert enumerate_solutions(inst) == []


def test_l0_640_tetap_layak_dengan_s1(h5: dict[str, Any]) -> None:
    # Pembanding §3.8: l_0 = 640 -> d'_3 = 605; saksi S1 masih layak
    inst = copy.deepcopy(h5)
    inst["kitchen"]["close"] = 640
    routes = {s.routes for s in enumerate_solutions(inst)}
    assert ((2, 1, 5), (4, 3)) in routes
