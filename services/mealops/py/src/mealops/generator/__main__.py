"""CLI: python -m mealops.generator --seed 42 [--params p.json] [--out DIR]."""

import argparse
import json
from pathlib import Path

from mealops.generator.build import generate, json_kanonik, manifest
from mealops.generator.params import ParameterGenerator


def tulis_instans(params: ParameterGenerator, seed: int, folder: Path) -> Path:
    """Tulis <nama>.instance.json dan <nama>.gen.json; kembalikan jalur instans."""
    instans = generate(params, seed)
    isi = json_kanonik(instans.model_dump(mode="json"))
    folder.mkdir(parents=True, exist_ok=True)
    jalur = folder / f"{instans.name}.instance.json"
    # TODO 1: tulis `isi` ke `jalur` (write_bytes, bukan write_text: byte persis sama dengan hash)
    jalur.write_bytes(isi)
    # TODO 2: tulis manifest ke folder / f"{instans.name}.gen.json"
    # manifest(...) DIPANGGIL; json_kanonik supaya formatnya sama dengan instans (konsep F.2)
    (folder / f"{instans.name}.gen.json").write_bytes(json_kanonik(manifest(params, seed, isi)))
    return jalur


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mealops.generator")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--params", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=Path("datasets/mealops/synthetic"))
    args = parser.parse_args(argv)
    if args.params is None:
        params = ParameterGenerator()
    else:
        # strict=False hanya di sini: JSON tidak punya tipe Literal, jadi "RC" perlu dikonversi
        params = ParameterGenerator.model_validate(
            json.loads(args.params.read_text()), strict=False
        )
    print(tulis_instans(params, args.seed, args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
