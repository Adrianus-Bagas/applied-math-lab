import json
from pathlib import Path
from typing import Any

import pytest
from mealops.testing.oracle_model_a import apply_patch, enumerate_solutions

FIXTURES = Path(__file__).resolve().parents[4] / "datasets" / "mealops" / "fixtures"


def _load(name: str) -> dict[str, Any]:
    with (FIXTURES / name).open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


# --- apply_patch: unit ---

BASE: dict[str, Any] = {"a": {"b": 1}, "xs": [{"q": 10}, {"q": 20}], "c/d": 5, "e~f": 6}


def test_replace_bertingkat() -> None:
    got = apply_patch(BASE, [{"op": "replace", "path": "/a/b", "value": 2}])
    assert got["a"]["b"] == 2


def test_replace_indeks_list() -> None:
    got = apply_patch(BASE, [{"op": "replace", "path": "/xs/1/q", "value": 99}])
    assert got["xs"] == [{"q": 10}, {"q": 99}]


def test_beberapa_op_berurutan() -> None:
    ops = [
        {"op": "replace", "path": "/a/b", "value": 7},
        {"op": "replace", "path": "/xs/0/q", "value": 8},
    ]
    got = apply_patch(BASE, ops)
    assert got["a"]["b"] == 7
    assert got["xs"][0]["q"] == 8


def test_base_tidak_berubah() -> None:
    apply_patch(BASE, [{"op": "replace", "path": "/xs/0/q", "value": 0}])
    assert BASE["xs"][0]["q"] == 10


def test_escape_json_pointer() -> None:
    # RFC 6901: "~1" berarti "/", "~0" berarti "~"
    got = apply_patch(BASE, [{"op": "replace", "path": "/c~1d", "value": 50}])
    assert got["c/d"] == 50
    got = apply_patch(BASE, [{"op": "replace", "path": "/e~0f", "value": 60}])
    assert got["e~f"] == 60


def test_op_lain_ditolak() -> None:
    with pytest.raises(ValueError, match="op tidak didukung"):
        apply_patch(BASE, [{"op": "add", "path": "/a/z", "value": 1}])


def test_path_tanpa_garis_miring_ditolak() -> None:
    with pytest.raises(ValueError, match="harus diawali '/'"):
        apply_patch(BASE, [{"op": "replace", "path": "a/b", "value": 1}])


def test_key_tidak_ada_ditolak() -> None:
    # "replace" hanya boleh mengganti yang sudah ada (salah ketik path harus gagal keras)
    with pytest.raises(KeyError):
        apply_patch(BASE, [{"op": "replace", "path": "/a/zz", "value": 1}])


def test_indeks_di_luar_list_ditolak() -> None:
    with pytest.raises(IndexError):
        apply_patch(BASE, [{"op": "replace", "path": "/xs/5/q", "value": 1}])


# --- varian H5: nilai harapan dari model.md §3.8 ---

VARIANTS = _load("h5.variants.json")["variants"]
SOLVABLE = [v for v in VARIANTS if v["expect"]["level"] != "input_tidak_valid"]


@pytest.mark.parametrize("variant", SOLVABLE, ids=[v["name"] for v in SOLVABLE])
def test_varian_h5(variant: dict[str, Any]) -> None:
    inst = apply_patch(_load("h5.instance.json"), variant["patch"])
    sols = enumerate_solutions(inst)
    expect = variant["expect"]
    if expect["level"] == "instans_tidak_layak":
        assert sols == []
        return
    assert sols, "harus ada minimal satu solusi layak"
    if "optimum" in expect:
        assert sols[0].cost == expect["optimum"]
    if "witness" in expect:
        witness = tuple(sorted(tuple(r) for r in expect["witness"]))
        assert witness in {s.routes for s in sols}


def test_semua_varian_bernama_unik() -> None:
    names = [v["name"] for v in VARIANTS]
    assert len(names) == len(set(names)) == 13


def test_path_menembus_nilai_skalar_ditolak() -> None:
    # /a/b bernilai 1 (int), jadi /a/b/c tidak punya tempat untuk diganti
    with pytest.raises(TypeError, match="bukan list atau dict"):
        apply_patch(BASE, [{"op": "replace", "path": "/a/b/c", "value": 1}])


def test_indeks_negatif_ditolak() -> None:
    # Python menerima xs[-1] (elemen terakhir); JSON Pointer tidak
    with pytest.raises(IndexError):
        apply_patch(BASE, [{"op": "replace", "path": "/xs/-1", "value": {"q": 1}}])


def test_path_kosong_ditolak() -> None:
    with pytest.raises(ValueError, match="harus diawali '/'"):
        apply_patch(BASE, [{"op": "replace", "path": "", "value": 1}])
