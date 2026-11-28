import json
from pathlib import Path
from typing import Any

import pytest
from mealops.testing.oracle_model_a import check_route, node_data

FIXTURES = Path(__file__).resolve().parents[4] / "datasets" / "mealops" / "fixtures"


@pytest.fixture(scope="module")
def h5() -> dict[str, Any]:
    with (FIXTURES / "h5.instance.json").open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


def test_node_data_h5(h5: dict[str, Any]) -> None:
    # Kolom a'_j, d'_j tabel §3.3
    got = [(node_data(h5, j).a_eff, node_data(h5, j).d_eff) for j in range(1, 6)]
    assert got == [(560, 610), (510, 570), (600, 645), (500, 530), (580, 610)]


def test_s1_rute_1(h5: dict[str, Any]) -> None:
    # §3.5: (2, 1, 5) -> T* = 510, 560, 595; pulang 625; muatan 80; jarak 18 (x100 m)
    r = check_route(h5, [2, 1, 5])
    assert r.ok
    assert r.reason is None
    assert r.bad_node is None
    assert r.load == 80
    assert r.starts == (510, 560, 595)
    assert r.back == 625
    assert r.cost == 1800


def test_s1_rute_2(h5: dict[str, Any]) -> None:
    # §3.5: (4, 3) -> T* = 500, 600 (tunggu 70); pulang 635; jarak 14
    r = check_route(h5, [4, 3])
    assert r.ok
    assert r.starts == (500, 600)
    assert r.back == 635
    assert r.cost == 1400


def test_kapasitas_diperiksa_lebih_dulu(h5: dict[str, Any]) -> None:
    # §3.7: (4, 2, 1, 5) muatan 115 > 100; waktunya sebenarnya lolos
    r = check_route(h5, [4, 2, 1, 5])
    assert not r.ok
    assert r.reason == "kapasitas"
    assert r.load == 115
    assert r.starts == ()
    assert r.back is None


def test_jebakan_d_efektif(h5: dict[str, Any]) -> None:
    # §3.6: (2, 1, 5, 3) muatan tepat 100 (boleh); T*_3 = 650 <= d_3 tetapi > d'_3 = 645
    r = check_route(h5, [2, 1, 5, 3])
    assert not r.ok
    assert r.reason == "jendela"
    assert r.bad_node == 3
    assert r.load == 100
    assert r.starts == (510, 560, 595, 650)


def test_jendela_node_5(h5: dict[str, Any]) -> None:
    # §3.7: (4, 3, 5) -> A_5 = 600 + 10 + 45 = 655 > 610
    r = check_route(h5, [4, 3, 5])
    assert not r.ok
    assert r.reason == "jendela"
    assert r.bad_node == 5
    assert r.starts == (500, 600, 655)


def test_uji_arc_hanya_syarat_perlu(h5: dict[str, Any]) -> None:
    # §3.6: arc (1,5) dan (5,3) lolos uji arc, tetapi rute (1, 5, 3) gagal di node 3
    r = check_route(h5, [1, 5, 3])
    assert not r.ok
    assert r.bad_node == 3
    assert r.starts == (560, 595, 650)


def test_node_pertama_tidak_menunggu_dari_a_asli(h5: dict[str, Any]) -> None:
    # (4,) saja: a_4 = 480 tetapi a'_4 = 500; pulang 500 + 5 + 20 = 525; jarak 8
    r = check_route(h5, [4])
    assert r.ok
    assert r.starts == (500,)
    assert r.back == 525
    assert r.cost == 800
