"""Parameter generator instans sintetis. Nilai bawaan ILUSTRATIF, bukan data nyata."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Ketat(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class ParameterProduksi(_Ketat):
    kitchen_start: int = Field(default=300, ge=0, lt=1440)
    batch_capacity: int = Field(default=400, ge=1)
    cadangan_batch: int = Field(default=1, ge=0)
    cook_fixed: int = Field(default=30, ge=0)
    cook_per_1000: int = Field(default=200, ge=0)
    pack_fixed: int = Field(default=10, ge=0)
    pack_per_1000: int = Field(default=100, ge=0)
    holding_max: int = Field(default=240, ge=0, lt=1440)


class ParameterGenerator(_Ketat):
    # Lokasi
    n_titik: int = Field(default=25, ge=1)
    tipe_lokasi: Literal["R", "C", "RC"] = "RC"
    setengah_sisi: int = Field(default=10_000, ge=1)
    n_klaster: int = Field(default=4, ge=1)
    sigma: int = Field(default=1_500, ge=1)
    sirkuitas_pembilang: int = Field(default=13, ge=1)
    sirkuitas_penyebut: int = Field(default=10, ge=1)
    kecepatan: int = Field(default=500, ge=1)
    # Demand dan waktu layan
    q_min: int = Field(default=30, ge=1)
    q_maks: int = Field(default=250, ge=1)
    s0: int = Field(default=5, ge=0)
    eta_per_1000: int = Field(default=20, ge=0)
    # Armada
    kapasitas: int = Field(default=150, ge=1)
    maks_trip: int = Field(default=2, ge=1)
    waktu_muat: int = Field(default=15, ge=0, lt=1440)
    cadangan_kendaraan: int = Field(default=1, ge=0)
    # Jendela waktu
    e0: int = Field(default=360, ge=0, lt=1440)
    l0_minimum: int = Field(default=840, ge=0, lt=1440)
    m_min: int = Field(default=660, ge=0, lt=1440)
    m_maks: int = Field(default=750, ge=0, lt=1440)
    langkah_m: int = Field(default=15, ge=1)
    delta_tambah_min: int = Field(default=10, ge=0)
    delta_tambah_maks: int = Field(default=30, ge=0)
    lebar_min: int = Field(default=60, ge=0)
    lebar_maks: int = Field(default=180, ge=0)
    # Produksi (None = instans Model A/B)
    produksi: ParameterProduksi | None = None

    @model_validator(mode="after")
    def _cek_rentang(self) -> Self:
        pasangan = [
            ("q_min", "q_maks"),
            ("m_min", "m_maks"),
            ("delta_tambah_min", "delta_tambah_maks"),
            ("lebar_min", "lebar_maks"),
            ("e0", "l0_minimum"),
        ]
        for bawah, atas in pasangan:
            if getattr(self, bawah) > getattr(self, atas):
                raise ValueError(f"{bawah} harus ≤ {atas}")
        if self.sirkuitas_pembilang < self.sirkuitas_penyebut:
            raise ValueError("sirkuitas harus ≥ 1 (jalan tidak lebih pendek dari garis lurus)")
        return self
