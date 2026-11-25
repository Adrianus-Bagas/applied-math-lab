"""Menyusun instans mealops.instance.v1 dari parameter dan seed."""

import hashlib
import json
from fractions import Fraction
from typing import Any

import numpy as np

from mealops.generator.demand import bangun_node, jumlah_kendaraan, sampel_demand
from mealops.generator.geometry import bagi_atas, matriks_jarak, matriks_waktu, sampel_lokasi
from mealops.generator.params import ParameterGenerator
from mealops.generator.rng import Aliran, buat_aliran
from mealops.generator.windows import jam_tutup, sampel_jendela
from mealops.instance import DeliveryNode, Fleet, Instance, Kitchen, Production, ServicePoint

VERSI_GENERATOR = "mealops-gen/1"


def json_kanonik(data: Any) -> bytes:
    """Byte JSON yang sama untuk data yang sama (konsep F.2)."""
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sidik_parameter(params: ParameterGenerator) -> str:
    """8 karakter pertama sha256 parameter (konsep F.1)."""
    return sha256_hex(json_kanonik(params.model_dump(mode="json")))[:8]


def nama_instans(params: ParameterGenerator, seed: int) -> str:
    # TODO 1: f"syn-{tipe}{n}-{sidik}-s{seed}"
    return f"syn-{params.tipe_lokasi}{params.n_titik}-{sidik_parameter(params)}-s{seed}"


def generate(params: ParameterGenerator, seed: int) -> Instance:
    """Urutan tetap: lokasi → jarak/waktu → demand → node → jendela → l0 → armada → produksi."""
    p = params

    # ① Lokasi (aliran LOKASI); indeks 0 = dapur
    lokasi = sampel_lokasi(
        buat_aliran(seed, Aliran.LOKASI),
        p.n_titik,
        p.tipe_lokasi,
        p.setengah_sisi,
        p.n_klaster,
        p.sigma,
    )
    semua = [(0, 0), *lokasi]
    jarak = matriks_jarak(semua, Fraction(p.sirkuitas_pembilang, p.sirkuitas_penyebut))
    waktu = matriks_waktu(jarak, params.kecepatan)  # TODO 2

    # ② Demand (aliran DEMAND) dan pemecahan dengan Q̄ = min(Q, D^max)
    demand = sampel_demand(buat_aliran(seed, Aliran.DEMAND), p.n_titik, p.q_min, p.q_maks)
    q_bar = (
        p.kapasitas if p.produksi is None else min(p.kapasitas, p.produksi.batch_capacity)
    )  # TODO 3
    node = bangun_node(demand, q_bar, p.s0, p.eta_per_1000)

    # ③ s_maks per titik, τ pergi/pulang per titik (konsep E.1)
    s_maks = [0] * p.n_titik
    for pot in node:
        # TODO 4: s_maks[pot.titik - 1] = max(...)
        s_maks[pot.titik - 1] = max(s_maks[pot.titik - 1], pot.s)
    tau_pergi = [waktu[0][i] for i in range(1, p.n_titik + 1)]
    tau_pulang = [waktu[i][0] for i in range(1, p.n_titik + 1)]  # TODO 5: kolom 0, baris 1..n

    # ④ Jendela (aliran JENDELA) lalu jam tutup
    jendela = sampel_jendela(
        buat_aliran(seed, Aliran.JENDELA),
        tau_pergi,
        s_maks,
        p.e0,
        p.m_min,
        p.m_maks,
        p.langkah_m,
        p.delta_tambah_min,
        p.delta_tambah_maks,
        p.lebar_min,
        p.lebar_maks,
    )
    l0 = jam_tutup(jendela, s_maks, tau_pulang, p.l0_minimum)

    # ⑤ Produksi: |B| = ⌈Σq / D^max⌉ + cadangan (pola konsep D.4)
    total = sum(demand)
    produksi = None
    if p.produksi is not None:
        pp = p.produksi
        produksi = Production(
            kitchen_start=pp.kitchen_start,
            batch_capacity=pp.batch_capacity,
            max_batches=bagi_atas(total, pp.batch_capacity) + pp.cadangan_batch,  # TODO 6
            cook_fixed=pp.cook_fixed,
            cook_per_1000=pp.cook_per_1000,
            pack_fixed=pp.pack_fixed,
            pack_per_1000=pp.pack_per_1000,
            holding_max=pp.holding_max,
        )

    # ⑥ Rakit kontrak; Pydantic memeriksa struktur (tingkat 1 lapis pertama)
    return Instance(
        schema_version="mealops.instance.v1",  # literal, bukan konstanta: mypy minta Literal
        name=nama_instans(p, seed),
        kitchen=Kitchen(open=p.e0, close=l0),
        fleet=Fleet(
            vehicles=jumlah_kendaraan(total, p.kapasitas, p.maks_trip, p.cadangan_kendaraan),
            capacity=p.kapasitas,
            max_trips=p.maks_trip,
            load_time=p.waktu_muat,
        ),
        points=[
            ServicePoint(name=f"T{i}", ready=w.a, consume=w.m, buffer=w.delta)
            for i, w in enumerate(jendela, start=1)
        ],
        nodes=[
            DeliveryNode(point=node_point.titik, demand=node_point.q, service=node_point.s)
            for node_point in node
        ],  # TODO 7: DeliveryNode(point=..., demand=..., service=...) per Potongan
        travel_time=waktu,
        distance=jarak,
        production=produksi,
    )


def manifest(params: ParameterGenerator, seed: int, isi_instans: bytes) -> dict[str, Any]:
    """Catatan reproduksi (konsep F.3)."""
    return {
        "generator": VERSI_GENERATOR,
        "seed": seed,
        "numpy": np.__version__,
        "instance_sha256": sha256_hex(isi_instans),
        "params": params.model_dump(mode="json"),
    }
