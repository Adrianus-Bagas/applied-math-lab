"""Tes kontrak instans: skema (struktur) dan validasi input tingkat 1 (§1.7)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from mealops import Instance, InvalidInputError, IssueCode, check_input, parse_instance
from mealops.schema import DEFAULT_PATH, instance_schema, render
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[4]
H5_PATH = ROOT / "datasets/mealops/fixtures/h5.instance.json"


@pytest.fixture
def h5() -> dict[str, Any]:
    """Instans H5 (`model.md` §3.3) sebagai dict mentah; setiap tes boleh mengubahnya."""
    data: dict[str, Any] = json.loads(H5_PATH.read_text(encoding="utf-8"))
    return data


def codes(raw: dict[str, Any]) -> set[IssueCode]:
    """Kumpulan kode pelanggaran; kosong berarti input valid."""
    try:
        parse_instance(json.dumps(raw))
    except InvalidInputError as err:
        return {issue.code for issue in err.issues}
    return set()


# --- H5 sendiri ------------------------------------------------------------------------


def test_h5_valid(h5: dict[str, Any]) -> None:
    inst = parse_instance(json.dumps(h5))
    assert len(inst.nodes) == 5
    assert inst.piece_limit == 100
    # d = m - delta mengembalikan deadline di tabel §3.3.
    assert [inst.deadline(p) for p in range(1, 6)] == [610, 570, 650, 530, 610]


def test_h5_lolos_json_schema(h5: dict[str, Any]) -> None:
    # Validator JSON Schema yang independen dari Pydantic harus setuju.
    jsonschema.Draft202012Validator(instance_schema()).validate(h5)


# --- Skema: Pydantic dan file di repo tidak boleh berbeda --------------------------------


def test_file_skema_tidak_basi() -> None:
    assert (ROOT / DEFAULT_PATH).read_text(encoding="utf-8") == render(), (
        "jalankan: uv run python -m mealops.schema"
    )


def test_skema_sah_draft_2020_12() -> None:
    jsonschema.Draft202012Validator.check_schema(instance_schema())


# --- Tingkat 1 lewat skema (satu angka) ------------------------------------------------


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("fleet", "capacity"), 0),  # §1.7 nomor 8: Q >= 1
        (("nodes", 0, "demand"), 0),  # C1: q >= 1
        (("kitchen", "close"), 1440),  # B2: waktu < 1440
        (("points", 0, "ready"), -5),  # §1.7 nomor 1: tak negatif
        (("nodes", 0, "service"), "10"),  # strict: string bukan int
        (("nodes", 0, "service"), 10.5),  # bukan bilangan bulat
    ],
)
def test_skema_menolak_angka_tunggal(
    h5: dict[str, Any], path: tuple[str | int, ...], value: object
) -> None:
    target: Any = h5
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert codes(h5) == {IssueCode.SCHEMA}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(instance_schema()).validate(h5)


def test_skema_menolak_field_asing(h5: dict[str, Any]) -> None:
    h5["fleet"]["capasity"] = 100  # salah ketik
    assert codes(h5) == {IssueCode.SCHEMA}


def test_error_skema_menunjuk_jalur(h5: dict[str, Any]) -> None:
    h5["nodes"][1]["demand"] = 0
    with pytest.raises(InvalidInputError) as err:
        parse_instance(json.dumps(h5))
    assert [i.path for i in err.value.issues] == ["nodes[1].demand"]


# --- Tingkat 1 lewat check_input (antar-field) -----------------------------------------


def test_matriks_salah_bentuk_berhenti_lebih_dulu(h5: dict[str, Any]) -> None:
    h5["travel_time"].pop()
    h5["nodes"][0]["service"] = 99  # pelanggaran lain diabaikan dulu
    assert codes(h5) == {IssueCode.MATRIX_SHAPE}


def test_rujukan_titik(h5: dict[str, Any]) -> None:
    h5["nodes"][4]["point"] = 6
    assert codes(h5) == {IssueCode.POINT_OUT_OF_RANGE, IssueCode.POINT_WITHOUT_NODE}


def test_jam_dapur_terbalik(h5: dict[str, Any]) -> None:
    h5["kitchen"] = {"open": 700, "close": 680}
    assert codes(h5) == {IssueCode.KITCHEN_HOURS_INVERTED}


def test_deadline_negatif(h5: dict[str, Any]) -> None:
    h5["points"][0].update(ready=0, consume=10, buffer=20)
    assert codes(h5) == {IssueCode.DEADLINE_NEGATIVE}


def test_buffer_kurang_dari_layan(h5: dict[str, Any]) -> None:
    h5["points"][1]["buffer"] = 14  # s_2 = 15 (B5); d ikut naik, jadi jendela tetap sah
    assert codes(h5) == {IssueCode.SERVICE_EXCEEDS_BUFFER}


def test_diagonal(h5: dict[str, Any]) -> None:
    h5["distance"][3][3] = 1
    assert codes(h5) == {IssueCode.DIAGONAL_NONZERO}


def test_segitiga(h5: dict[str, Any]) -> None:
    # tau_02 = 30, tetapi 0 -> 1 -> 2 = 15 + 15 = 30. Naikkan tau_02 menjadi 31.
    h5["travel_time"][0][2] = 31
    with pytest.raises(InvalidInputError) as err:
        parse_instance(json.dumps(h5))
    assert [(i.code, i.path) for i in err.value.issues] == [
        (IssueCode.TRIANGLE_VIOLATED, "travel_time[0][2]")
    ]


def test_semua_pelanggaran_dikumpulkan(h5: dict[str, Any]) -> None:
    h5["points"][1]["buffer"] = 14
    h5["distance"][3][3] = 1
    h5["travel_time"][0][2] = 31
    assert codes(h5) == {
        IssueCode.SERVICE_EXCEEDS_BUFFER,
        IssueCode.DIAGONAL_NONZERO,
        IssueCode.TRIANGLE_VIOLATED,
    }


# --- Pembanding §3.8 + cek pemahaman MO-2.1: tingkat 1 vs tingkat 2 ---------------------
# check_input hanya boleh menolak baris "input tidak valid". Baris "instans tidak layak"
# dan "layak" harus LOLOS di sini; ketidaklayakan instans diuji di MO-6.3 (§7.6).


def _set_deadline(raw: dict[str, Any], point: int, d: int) -> None:
    p = raw["points"][point - 1]
    p["consume"] = d + p["buffer"]


@pytest.mark.parametrize(
    ("ubah", "harapan"),
    [
        (lambda r: r["nodes"][1].update(demand=120), {IssueCode.DEMAND_EXCEEDS_LIMIT}),
        (lambda r: r["fleet"].update(capacity=30), {IssueCode.DEMAND_EXCEEDS_LIMIT}),
        (lambda r: _set_deadline(r, 5, 570), {IssueCode.WINDOW_INVERTED}),
        (lambda r: r["kitchen"].update(open=530), set()),  # tidak layak: a'_4 > d'_4
        (lambda r: _set_deadline(r, 4, 495), set()),  # tidak layak: a'_4 > d'_4
        (lambda r: _set_deadline(r, 2, 540), set()),  # layak (saksi S1)
        (lambda r: r["kitchen"].update(close=640), set()),  # layak (saksi S1)
        # Jebakan: akibatnya a'_4 = 540 > d'_4 = 530 (tampak tingkat 2), tetapi data mentahnya
        # sudah melanggar B6: tau_04 = 60 > tau_01 + tau_14 = 40. Tingkat 1 diperiksa dulu.
        (lambda r: r["travel_time"][0].__setitem__(4, 60), {IssueCode.TRIANGLE_VIOLATED}),
        # V2 (§3.8): |K| = 1 sah sebagai input; ceil(135/100) = 2 > 1 adalah tingkat 2.
        (lambda r: r["fleet"].update(vehicles=1), set()),
    ],
    ids=["q2=120", "Q=30", "d5=570", "e0=530", "d4=495", "d2=540", "l0=640", "tau04=60", "K=1"],
)
def test_pembanding_3_8(h5: dict[str, Any], ubah: Any, harapan: set[IssueCode]) -> None:
    ubah(h5)
    assert codes(h5) == harapan


# --- Produksi (Model C/D) -------------------------------------------------------------

PRODUKSI_H5P: dict[str, int] = {
    # Data §5.5: phi^c = (30; 0,2), phi^p = (10; 0,1), dalam menit per 1000 porsi.
    "kitchen_start": 300,
    "batch_capacity": 100,
    "max_batches": 3,
    "cook_fixed": 30,
    "cook_per_1000": 200,
    "pack_fixed": 10,
    "pack_per_1000": 100,
    "holding_max": 120,
}


def test_durasi_batch_eksak(h5: dict[str, Any]) -> None:
    h5["production"] = PRODUKSI_H5P
    prod = parse_instance(json.dumps(h5)).production
    assert prod is not None
    # Tabel §5.5 dan §7.9: theta^c(75) = 45, theta^c(60) = 42, theta^p(75) = 18, theta^p(60) = 16.
    assert [prod.cook_minutes(d) for d in (75, 60, 35, 80, 20)] == [45, 42, 37, 46, 34]
    assert [prod.pack_minutes(d) for d in (75, 60, 35, 80, 20)] == [18, 16, 14, 18, 12]
    assert prod.cook_minutes(0) == prod.pack_minutes(0) == 0


def test_durasi_tanpa_galat_float(h5: dict[str, Any]) -> None:
    # Dengan float: math.ceil(0.07 * 100) == 8, karena 0.07 * 100 = 7.000000000000001.
    # Dengan menit per 1000 porsi (70) hasilnya eksak: ceil(70 * 100 / 1000) = 7.
    h5["production"] = {**PRODUKSI_H5P, "cook_fixed": 0, "cook_per_1000": 70}
    prod = parse_instance(json.dumps(h5)).production
    assert prod is not None
    assert prod.cook_minutes(100) == 7
    assert prod.cook_minutes(101) == 8  # 7,07 dibulatkan ke atas


def test_batas_potongan_ikut_kapasitas_batch(h5: dict[str, Any]) -> None:
    h5["production"] = {**PRODUKSI_H5P, "batch_capacity": 30}
    # Q-bar = min(100, 30) = 30; node 2 (40) dan node 4 (35) tidak muat (K1).
    with pytest.raises(InvalidInputError) as err:
        parse_instance(json.dumps(h5))
    assert [i.path for i in err.value.issues] == ["nodes[1].demand", "nodes[3].demand"]


def test_instans_immutable(h5: dict[str, Any]) -> None:
    inst = Instance.model_validate_json(json.dumps(h5))
    # frozen=True: setattr ditolak dengan ValidationError (jenis "frozen_instance").
    with pytest.raises(ValidationError, match="frozen"):
        inst.fleet.__setattr__("capacity", 5)
    assert check_input(inst) == []
    # Salinan lewat model_copy tidak mengubah aslinya.
    assert inst.model_copy(deep=True) == inst
    assert copy.deepcopy(inst) == inst
