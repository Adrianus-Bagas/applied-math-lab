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


VARIANTS = _load("h5.variants.json")["variants"]
INVALID = [v for v in VARIANTS if v["expect"]["level"] == "input_tidak_valid"]
VALID = [v for v in VARIANTS if v["expect"]["level"] != "input_tidak_valid"]


def _issues(data: dict[str, Any]) -> list[tuple[str, str]]:
    # Lapis skema harus lolos dulu: ValidationError di sini berarti fixture salah bentuk
    instance = Instance.model_validate(data)
    return sorted((str(i.code), i.path) for i in check_input(instance))


def test_h5_dasar_valid() -> None:
    assert _issues(_load("h5.instance.json")) == []


@pytest.mark.parametrize("variant", INVALID, ids=[v["name"] for v in INVALID])
def test_menolak_yang_salah(variant: dict[str, Any]) -> None:
    # Arah 1: setiap pelanggaran tingkat 1 dilaporkan, tidak lebih dan tidak kurang
    data = apply_patch(_load("h5.instance.json"), variant["patch"])
    expected = sorted((i["code"], i["path"]) for i in variant["expect"]["issues"])
    assert expected, "varian input tidak valid wajib punya daftar issues"
    assert _issues(data) == expected


@pytest.mark.parametrize("variant", VALID, ids=[v["name"] for v in VALID])
def test_meloloskan_yang_benar(variant: dict[str, Any]) -> None:
    # Arah 2: instans tidak layak (tingkat 2) dan instans layak bukan urusan check_input
    data = apply_patch(_load("h5.instance.json"), variant["patch"])
    assert _issues(data) == []
    assert "issues" not in variant["expect"]
