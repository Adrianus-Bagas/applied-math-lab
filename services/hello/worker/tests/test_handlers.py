from collections.abc import Mapping
from typing import Any

import pytest
from hello_worker.handlers import stats_summary
from lab_worker.worker import PermanentError


class KonteksTiruan:
    """Pengganti JobContext: hanya atribut yang dipakai handler."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.laporan: list[Mapping[str, Any]] = []

    def progress(self, data: Mapping[str, Any]) -> None:
        self.laporan.append(dict(data))


def jalankan(payload: dict[str, Any]) -> tuple[Mapping[str, Any], KonteksTiruan]:
    ctx = KonteksTiruan(payload)
    return stats_summary(ctx), ctx  # type: ignore[arg-type]


def test_deterministik_terhadap_seed() -> None:
    a, _ = jalankan({"n": 10_000, "seed": 42})
    b, _ = jalankan({"n": 10_000, "seed": 42})
    assert a == b  # identik bit demi bit, bukan sekadar dekat


def test_seed_berbeda_hasil_berbeda() -> None:
    a, _ = jalankan({"n": 10_000, "seed": 1})
    b, _ = jalankan({"n": 10_000, "seed": 2})
    assert a["mean"] != b["mean"]


def test_n_float_dikonversi() -> None:
    hasil, _ = jalankan({"n": 1000.0, "seed": 7})
    assert hasil["n"] == 1000
    assert isinstance(hasil["n"], int)


def test_progres_dilaporkan_berurutan() -> None:
    _, ctx = jalankan({"n": 100, "seed": 3})
    assert [p["tahap"] for p in ctx.laporan] == ["bangkitkan", "hitung"]


def test_n_satu_gagal_permanen() -> None:
    with pytest.raises(PermanentError):
        jalankan({"n": 1, "seed": 3})
