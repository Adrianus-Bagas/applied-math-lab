"""Tes ujung ke ujung generator: validitas, determinisme, aliran, golden hash, CLI."""

import json
import math
from pathlib import Path
from typing import Any

import pytest
from mealops.checks import check_input
from mealops.generator.__main__ import main
from mealops.generator.build import (
    generate,
    json_kanonik,
    nama_instans,
    sha256_hex,
)
from mealops.generator.params import ParameterGenerator, ParameterProduksi
from mealops.instance import Instance
from pydantic import ValidationError

# Beberapa variasi parameter yang mewakili ruang input generator
VARIAN: dict[str, ParameterGenerator] = {
    "bawaan": ParameterGenerator(),
    "R": ParameterGenerator(tipe_lokasi="R", n_titik=15),
    "C": ParameterGenerator(tipe_lokasi="C", n_titik=15, sigma=800),
    "produksi": ParameterGenerator(n_titik=12, produksi=ParameterProduksi()),
    # D^max kecil → Q̄ = 80 < Q, banyak titik dipecah
    "pecah": ParameterGenerator(n_titik=10, produksi=ParameterProduksi(batch_capacity=80)),
    # jendela sempit dan buffer nol → paling sering memicu langkah 2 (m dinaikkan)
    "ketat": ParameterGenerator(
        n_titik=20,
        m_min=360,
        m_maks=375,
        delta_tambah_min=0,
        delta_tambah_maks=0,
        lebar_min=0,
        lebar_maks=10,
    ),
}
SEED = range(30)


def masalah(instans: Instance) -> list[Any]:
    """Daftar pelanggaran tingkat 1. Sesuaikan baris ini bila check_input-mu
    mengembalikan objek laporan, bukan list."""
    return list(check_input(instans))


def bytes_instans(instans: Instance) -> bytes:
    return json_kanonik(instans.model_dump(mode="json"))


# ---------------------------------------------------------------------------
# 1. Jaminan G1: tingkat 1 lolos, dua uji tingkat 2 lolos
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("varian", VARIAN)
def test_lolos_check_input(varian: str) -> None:
    for seed in SEED:
        instans = generate(VARIAN[varian], seed)
        assert masalah(instans) == [], (varian, seed)


@pytest.mark.parametrize("varian", VARIAN)
def test_jendela_efektif_tidak_kosong(varian: str) -> None:
    for seed in SEED:
        ins = generate(VARIAN[varian], seed)
        e0, l0, tau = ins.kitchen.open, ins.kitchen.close, ins.travel_time
        for j, node in enumerate(ins.nodes, start=1):
            p = node.point
            a_efektif = max(ins.points[p - 1].ready, e0 + tau[0][p])
            d_efektif = min(ins.deadline(p), l0 - node.service - tau[p][0])
            assert a_efektif <= d_efektif, (varian, seed, j)


@pytest.mark.parametrize("varian", VARIAN)
def test_uji_kapasitas(varian: str) -> None:
    for seed in SEED:
        ins = generate(VARIAN[varian], seed)
        total = sum(n.demand for n in ins.nodes)
        trip = ins.fleet.vehicles * ins.fleet.max_trips
        assert math.ceil(total / ins.fleet.capacity) <= trip, (varian, seed)
        if ins.production is not None:
            batch = math.ceil(total / ins.production.batch_capacity)
            assert batch <= ins.production.max_batches, (varian, seed)


def test_pemecahan_aktif() -> None:
    ins = generate(VARIAN["pecah"], 3)
    assert ins.piece_limit == 80
    assert all(1 <= n.demand <= 80 for n in ins.nodes)
    assert len(ins.nodes) > len(ins.points)  # ada titik yang benar-benar dipecah
    titik = [n.point for n in ins.nodes]
    assert titik == sorted(titik)  # node berurutan per titik


# ---------------------------------------------------------------------------
# 2. Determinisme dan aliran stabil (konsep A)
# ---------------------------------------------------------------------------


def test_deterministik_byte() -> None:
    p = ParameterGenerator()
    assert bytes_instans(generate(p, 42)) == bytes_instans(generate(p, 42))
    assert bytes_instans(generate(p, 42)) != bytes_instans(generate(p, 43))


def test_ubah_demand_lokasi_tetap() -> None:
    a = generate(ParameterGenerator(q_maks=250), 5)
    b = generate(ParameterGenerator(q_maks=400), 5)
    assert a.distance == b.distance
    assert a.travel_time == b.travel_time
    assert [n.demand for n in a.nodes] != [n.demand for n in b.nodes]


def test_ubah_jendela_demand_tetap() -> None:
    a = generate(ParameterGenerator(lebar_maks=180), 5)
    b = generate(ParameterGenerator(lebar_maks=300), 5)
    assert a.nodes == b.nodes
    assert a.distance == b.distance
    assert [p.ready for p in a.points] != [p.ready for p in b.points]


def test_ubah_lokasi_demand_tetap() -> None:
    a = generate(ParameterGenerator(tipe_lokasi="R"), 5)
    b = generate(ParameterGenerator(tipe_lokasi="C"), 5)
    assert a.nodes == b.nodes  # demand dan s_j tidak bergantung pada lokasi
    assert a.distance != b.distance


# ---------------------------------------------------------------------------
# 3. Nama dan golden hash
# ---------------------------------------------------------------------------


def test_nama_instans() -> None:
    p = ParameterGenerator()
    assert generate(p, 42).name == nama_instans(p, 42)
    assert nama_instans(p, 42).startswith("syn-RC25-")
    assert nama_instans(p, 42).endswith("-s42")
    # parameter berbeda → sidik parameter berbeda, walaupun seed sama
    assert nama_instans(p, 42) != nama_instans(ParameterGenerator(q_maks=300), 42)


@pytest.mark.parametrize(
    ("params", "seed", "harapan"),
    [
        (
            ParameterGenerator(),
            42,
            "c28c89d9cf3fc9ea5f07069a54fd090f084418f8c6b25cea450ec5bb8750d72f",
        ),
        (
            ParameterGenerator(n_titik=10, tipe_lokasi="C", produksi=ParameterProduksi()),
            7,
            "8e60d839b6404d56f7b7ec6912fdd73184f9f56c3428f0fe62452b59d9e8d754",
        ),
    ],
)
def test_golden_hash(params: ParameterGenerator, seed: int, harapan: str) -> None:
    # Dihitung dengan NumPy 2.5.3. Gagal = keluaran generator berubah.
    # Bila perubahan itu disengaja: naikkan VERSI_GENERATOR, lalu perbarui hash ini.
    # Diverifikasi dengan NumPy 2.5.3 dan 2.5.4
    assert sha256_hex(bytes_instans(generate(params, seed))) == harapan


# ---------------------------------------------------------------------------
# 4. Parameter tidak sah
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "salah",
    [
        {"q_min": 300, "q_maks": 100},
        {"m_min": 800, "m_maks": 700},
        {"lebar_min": 200, "lebar_maks": 100},
        {"e0": 900, "l0_minimum": 800},
        {"sirkuitas_pembilang": 9, "sirkuitas_penyebut": 10},
        {"n_titik": 0},
        {"warna": "merah"},  # field asing ditolak (extra="forbid")
    ],
)
def test_parameter_ditolak(salah: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        ParameterGenerator.model_validate(salah)


# ---------------------------------------------------------------------------
# 5. CLI dan manifest
# ---------------------------------------------------------------------------


def test_cli_menulis_instans_dan_manifest(tmp_path: Path) -> None:
    assert main(["--seed", "42", "--out", str(tmp_path)]) == 0
    nama = nama_instans(ParameterGenerator(), 42)
    isi = (tmp_path / f"{nama}.instance.json").read_bytes()
    meta = json.loads((tmp_path / f"{nama}.gen.json").read_text())

    assert Instance.model_validate_json(isi).name == nama  # lolos kontrak
    assert meta["seed"] == 42
    assert meta["instance_sha256"] == sha256_hex(isi)
    assert meta["params"] == ParameterGenerator().model_dump(mode="json")


def test_cli_dengan_file_parameter(tmp_path: Path) -> None:
    file_params = tmp_path / "p.json"
    file_params.write_text(json.dumps({"n_titik": 8, "tipe_lokasi": "R"}))
    keluar = tmp_path / "keluar"
    assert main(["--seed", "1", "--params", str(file_params), "--out", str(keluar)]) == 0
    params = ParameterGenerator(n_titik=8, tipe_lokasi="R")
    assert (keluar / f"{nama_instans(params, 1)}.instance.json").exists()


def test_cli_ulang_identik(tmp_path: Path) -> None:
    main(["--seed", "9", "--out", str(tmp_path / "a")])
    main(["--seed", "9", "--out", str(tmp_path / "b")])
    nama = nama_instans(ParameterGenerator(), 9)
    berkas = f"{nama}.instance.json"
    assert (tmp_path / "a" / berkas).read_bytes() == (tmp_path / "b" / berkas).read_bytes()
