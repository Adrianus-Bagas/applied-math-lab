"""Model instans MealOps (kontrak `mealops.instance.v1`).

Modul ini hanya memeriksa *struktur* (tipe, rentang satu angka, field wajib).
Isinya identik dengan JSON Schema di `contracts/mealops/instance.v1.schema.json`,
karena skema itu di-generate dari model di sini (lihat `mealops.schema`).

Syarat §1.7 yang melibatkan lebih dari satu angka (misalnya `a_j <= d_j` atau
ketaksamaan segitiga) diperiksa terpisah di `mealops.checks`. Keduanya bersama-sama
membentuk tingkat 1 ("input tidak valid", `model.md` §3.1). Tingkat 2 (instans tidak
layak, misalnya `a'_j > d'_j`) sengaja TIDAK diperiksa di sini.

Konvensi indeks (sama dengan `model.md`):
- Lokasi 0 adalah dapur; lokasi p = 1..P adalah titik layanan `points[p-1]`.
- Matriks `travel_time` dan `distance` berukuran (P+1) x (P+1), diindeks per lokasi.
  Node yang berasal dari titik yang sama otomatis punya tau = 0 dan c = 0 di antaranya.
- Node j = 1..n adalah `nodes[j-1]`; `node.point` adalah sigma(j).
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "mealops.instance.v1"

# Jam kejadian: menit bulat sejak 00:00 hari operasi, di [0, 1440) (B1, B2).
Clock = Annotated[int, Field(ge=0, lt=1440)]
# Durasi dalam menit bulat. Satu hari operasi, jadi tidak pernah >= 1440.
Minutes = Annotated[int, Field(ge=0, lt=1440)]
# Bilangan bulat >= 1 (jumlah kendaraan, kapasitas, demand, ...).
PositiveInt = Annotated[int, Field(ge=1)]
NonNegativeInt = Annotated[int, Field(ge=0)]


class _Strict(BaseModel):
    """Basis semua model: field asing ditolak, tidak ada konversi tipe diam-diam."""

    # extra="forbid": salah ketik nama field langsung ketahuan (additionalProperties: false).
    # strict=True: "480" (string) atau 480.0 tidak diterima sebagai int.
    # frozen=True: instans immutable, cocok dengan snapshot skenario.
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Kitchen(_Strict):
    """Jam operasional dapur untuk armada, [e_0, l_0]."""

    open: Clock = Field(description="e_0: kendaraan paling cepat berangkat (menit)")
    close: Clock = Field(description="l_0: kendaraan paling lambat kembali (menit)")


class Fleet(_Strict):
    """Armada homogen (A1)."""

    vehicles: PositiveInt = Field(description="|K|: jumlah kendaraan")
    capacity: PositiveInt = Field(description="Q: kapasitas satu kendaraan (porsi)")
    max_trips: PositiveInt = Field(description="rho: trip maksimum per kendaraan per hari")
    load_time: Minutes = Field(description="lambda: waktu muat per trip (menit)")


class ServicePoint(_Strict):
    """Titik layanan asli (sebelum pemecahan demand). Jendela diwarisi node-nodenya."""

    name: str = Field(min_length=1, description="Nama titik layanan, untuk tampilan")
    ready: Clock = Field(description="a: paling awal bisa menerima (menit)")
    consume: Clock = Field(description="m: waktu konsumsi terencana (menit)")
    buffer: Minutes = Field(description="delta: buffer serah-terima; deadline d = m - delta")


class DeliveryNode(_Strict):
    """Node pengantaran setelah pemecahan demand."""

    point: PositiveInt = Field(description="sigma(j): nomor lokasi titik layanan, 1..P")
    demand: PositiveInt = Field(description="q_j: porsi untuk node ini (C1: >= 1)")
    service: Minutes = Field(description="s_j: waktu layan, sudah dibulatkan ke atas (B1)")


class Production(_Strict):
    """Parameter dapur untuk Model C/D. Tidak ada = Model A/B saja.

    Koefisien per porsi disimpan sebagai bilangan bulat "menit per 1000 porsi", supaya
    durasi theta(D) = ceil(phi_0 + phi_1 * D) bisa dihitung eksak dengan aritmetika
    bilangan bulat di Python dan Rust (lihat `cook_minutes`).
    """

    kitchen_start: Clock = Field(description="e_dapur: jam lini masak mulai (menit)")
    batch_capacity: PositiveInt = Field(description="D^max: kapasitas satu batch (porsi)")
    max_batches: PositiveInt = Field(description="|B|: jumlah slot batch per hari")
    cook_fixed: Minutes = Field(description="phi^c_0: setup masak per batch (menit)")
    cook_per_1000: NonNegativeInt = Field(description="phi^c_1 x 1000: menit per 1000 porsi")
    pack_fixed: Minutes = Field(description="phi^p_0: setup packing per batch (menit)")
    pack_per_1000: NonNegativeInt = Field(description="phi^p_1 x 1000: menit per 1000 porsi")
    holding_max: Minutes = Field(description="H^max: batas holding, parameter kebijakan (B8)")

    def cook_minutes(self, portions: int) -> int:
        """theta^c(D): durasi masak batch berukuran D, dibulatkan ke atas. theta(0) = 0."""
        return _batch_minutes(self.cook_fixed, self.cook_per_1000, portions)

    def pack_minutes(self, portions: int) -> int:
        """theta^p(D): durasi packing batch berukuran D, dibulatkan ke atas. theta(0) = 0."""
        return _batch_minutes(self.pack_fixed, self.pack_per_1000, portions)


def _batch_minutes(fixed: int, per_1000: int, portions: int) -> int:
    # ceil(fixed + per_1000 * D / 1000) = fixed + ceil(per_1000 * D / 1000), karena fixed bulat.
    # ceil(a / b) untuk a >= 0, b > 0 ditulis -(-a // b): pembagian bulat, tanpa float.
    if portions == 0:
        return 0
    return fixed + -(-per_1000 * portions // 1000)


class Instance(_Strict):
    """Satu instans MealOps yang sudah melewati pemecahan demand (`model.md` §4.1)."""

    schema_version: Literal["mealops.instance.v1"] = Field(
        description="Versi kontrak; naik bila bentuk JSON berubah tidak kompatibel"
    )
    name: str = Field(min_length=1, description="Identitas instans, misalnya 'H5'")
    kitchen: Kitchen
    fleet: Fleet
    points: list[ServicePoint] = Field(min_length=1, description="Titik layanan, lokasi 1..P")
    nodes: list[DeliveryNode] = Field(min_length=1, description="Node pengantaran, j = 1..n")
    travel_time: list[list[Minutes]] = Field(
        description="tau: (P+1) x (P+1) menit, baris/kolom 0 = dapur"
    )
    distance: list[list[NonNegativeInt]] = Field(
        description="c: (P+1) x (P+1) meter, baris/kolom 0 = dapur"
    )
    production: Production | None = Field(
        default=None, description="Parameter Model C/D; null untuk Model A/B"
    )

    def deadline(self, point: int) -> int:
        """d = m - delta untuk titik layanan nomor `point` (1..P)."""
        p = self.points[point - 1]
        return p.consume - p.buffer

    @property
    def piece_limit(self) -> int:
        """Q-bar = min(Q, D^max): batas ukuran node setelah pemecahan demand (K1)."""
        if self.production is None:
            return self.fleet.capacity
        return min(self.fleet.capacity, self.production.batch_capacity)
