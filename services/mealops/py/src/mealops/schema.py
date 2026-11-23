"""Generate JSON Schema `mealops.instance.v1` dari model Pydantic.

Model Pydantic adalah sumber kebenaran; file skema di `contracts/` adalah hasil generate
yang di-commit supaya Go (dan pembaca manusia) bisa memakainya tanpa Python.

Pemakaian (dari root repo):
    uv run python -m mealops.schema           # tulis ulang file skema
    uv run python -m mealops.schema --check   # gagal bila file di repo sudah basi (dipakai CI)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mealops.instance import SCHEMA_VERSION, Instance

SCHEMA_ID = f"https://applied-math-lab.portfolio-bagas.tech/contracts/{SCHEMA_VERSION}.schema.json"
DEFAULT_PATH = Path("contracts/mealops/instance.v1.schema.json")


def instance_schema() -> dict[str, Any]:
    """Skema sebagai dict. `$schema` dan `$id` ditaruh paling atas supaya mudah dibaca."""
    body = Instance.model_json_schema(mode="validation")
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        **body,
    }


def render() -> str:
    # indent=2 + newline di akhir: sama dengan gaya prettier, jadi `just fmt` tidak mengubahnya.
    return json.dumps(instance_schema(), indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="hanya bandingkan, jangan tulis")
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args(argv)

    expected = render()
    if args.check:
        current = args.path.read_text(encoding="utf-8") if args.path.exists() else ""
        if current != expected:
            print(f"{args.path} basi; jalankan: uv run python -m mealops.schema", file=sys.stderr)
            return 1
        return 0
    args.path.parent.mkdir(parents=True, exist_ok=True)
    args.path.write_text(expected, encoding="utf-8")
    print(f"ditulis: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
