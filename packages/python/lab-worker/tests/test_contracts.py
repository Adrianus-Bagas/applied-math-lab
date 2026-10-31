from pathlib import Path

import pytest
from lab_worker.contracts import InvalidPayloadError, Registry, UnknownKindError

ROOT = Path(__file__).resolve().parents[4]

REG = Registry.from_dir(ROOT / "contracts" / "jobs")
KIND = "lab.stats.summary"


def test_payload_valid_termasuk_seed_maksimum() -> None:
    REG.validate(KIND, 1, {"n": 1000, "seed": 9007199254740991})


@pytest.mark.parametrize(
    "payload",
    [
        {"n": 10},
        {"n": 0, "seed": 1},
        {"n": 10.5, "seed": 1},
        {"n": 10, "seed": 1, "sead": 2},
        {"n": 10, "seed": 9007199254740992},
        {"n": 10, "seed": -1},
    ],
)
def test_payload_invalid_sama_dengan_sisi_go(payload: dict[str, object]) -> None:
    with pytest.raises(InvalidPayloadError):
        REG.validate(KIND, 1, payload)


def test_kind_atau_versi_tidak_dikenal() -> None:
    with pytest.raises(UnknownKindError):
        REG.validate(KIND, 2, {"n": 1, "seed": 1})
