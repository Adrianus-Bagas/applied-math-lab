"""Registry kontrak JSON Schema payload job, cermin dari paket Go jobqueue.

Konvensi nama file sama dengan sisi Go: <kind>.v<N>.schema.json.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

_SCHEMA_FILE = re.compile(
    r"^([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+)\.v([1-9][0-9]*)\.schema\.json$"
)


class UnknownKindError(LookupError):
    """Tidak ada skema untuk kind dan versi tersebut."""


class InvalidPayloadError(ValueError):
    """Payload tidak lolos validasi skema."""


class Registry:
    """Validator terkompilasi, dikunci oleh (kind, versi skema)."""

    def __init__(self, validators: Mapping[tuple[str, int], Draft202012Validator]) -> None:
        self._validators = dict(validators)

    @classmethod
    def from_dir(cls, directory: Path) -> Registry:
        """Muat dan periksa setiap <kind>.v<N>.schema.json di ``directory``."""
        validators: dict[tuple[str, int], Draft202012Validator] = {}
        for path in sorted(directory.glob("*.schema.json")):
            m = _SCHEMA_FILE.match(path.name)
            if m is None:
                raise ValueError(f"{path.name} tidak sesuai pola <kind>.v<N>.schema.json")
            schema = json.loads(path.read_text())
            Draft202012Validator.check_schema(schema)  # skema rusak gagal saat start
            validators[(m[1], int(m[2]))] = Draft202012Validator(schema)
        if not validators:
            raise ValueError(f"tidak ada skema di {directory}")
        return cls(validators)

    @property
    def kinds(self) -> frozenset[str]:
        return frozenset(kind for kind, _ in self._validators)

    def validate(self, kind: str, version: int, payload: Any) -> None:
        """Lempar UnknownKindError atau InvalidPayloadError bila payload ditolak."""
        validator = self._validators.get((kind, version))
        if validator is None:
            raise UnknownKindError(f"{kind} v{version}")
        error = best_match(validator.iter_errors(payload))
        if error is not None:
            raise InvalidPayloadError(f"{error.json_path}: {error.message}")


def default_contracts_dir() -> Path:
    """LAB_CONTRACTS_DIR bila diset (image Docker, L0.6); selain itu cari ke atas dari cwd."""
    env = os.environ.get("LAB_CONTRACTS_DIR")
    if env:
        return Path(env)
    cwd = Path.cwd()
    for parent in (cwd, *cwd.parents):
        candidate = parent / "contracts" / "jobs"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("direktori contracts/jobs tidak ditemukan; set LAB_CONTRACTS_DIR")
