"""Validasi input tingkat 1: syarat §1.7 `model.md` yang melibatkan lebih dari satu angka.

Syarat satu angka (tipe, rentang, >= 1) sudah dijaga skema (`mealops.instance`).
Di sini hanya yang tidak bisa diungkapkan JSON Schema: bentuk matriks, rujukan indeks,
dan ketaksamaan antar-field.

Aturan penting (`model.md` §3.1): semua pemeriksaan di sini HANYA membaca data mentah.
Tidak ada a'_j, d'_j, S^max, ell_j, atau beta*. Masalah yang baru terlihat setelah
menghitung besaran turunan adalah "instans tidak layak" (tingkat 2), bukan urusan modul ini.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from pydantic import ValidationError

from mealops.instance import Instance


class IssueCode(StrEnum):
    """Jenis pelanggaran input. Nilai string-nya stabil karena ikut dikirim ke API."""

    # Tidak lolos skema (tipe, field, rentang satu angka). §1.7 nomor 1, 6, 7, 8.
    SCHEMA = "schema"
    # Struktur yang tidak bisa diperiksa skema.
    MATRIX_SHAPE = "matrix_shape"
    POINT_OUT_OF_RANGE = "point_out_of_range"
    POINT_WITHOUT_NODE = "point_without_node"
    # §1.7 nomor 1: deadline d = m - delta harus jam yang sah (>= 0).
    DEADLINE_NEGATIVE = "deadline_negative"
    # §1.7 nomor 2: a <= d.
    WINDOW_INVERTED = "window_inverted"
    # §1.7 nomor 3 (B5): s_j <= delta.
    SERVICE_EXCEEDS_BUFFER = "service_exceeds_buffer"
    # §1.7 nomor 4 dan 8: diagonal matriks nol.
    DIAGONAL_NONZERO = "diagonal_nonzero"
    # §1.7 nomor 5 (B6): tau_ij <= tau_ik + tau_kj.
    TRIANGLE_VIOLATED = "triangle_violated"
    # §1.7 nomor 6 (C1, K1): q_j <= Q-bar.
    DEMAND_EXCEEDS_LIMIT = "demand_exceeds_limit"
    # §1.7 nomor 8: e_0 <= l_0.
    KITCHEN_HOURS_INVERTED = "kitchen_hours_inverted"


@dataclass(frozen=True, slots=True)
class InputIssue:
    """Satu pelanggaran input. `path` menunjuk lokasi di JSON, misalnya 'nodes[1].demand'."""

    code: IssueCode
    path: str
    message: str


class InvalidInputError(Exception):
    """Input tidak valid (tingkat 1). Membawa SEMUA pelanggaran, bukan hanya yang pertama."""

    def __init__(self, issues: list[InputIssue]) -> None:
        self.issues = issues
        lines = "; ".join(f"{i.path}: {i.message}" for i in issues[:5])
        more = f" (+{len(issues) - 5} lagi)" if len(issues) > 5 else ""
        super().__init__(f"input tidak valid: {lines}{more}")


def parse_instance(raw: str | bytes) -> Instance:
    """Baca JSON, periksa skema lalu §1.7. Gagal -> `InvalidInputError` berisi semua pelanggaran."""
    try:
        instance = Instance.model_validate_json(raw)
    except ValidationError as err:
        raise InvalidInputError(_schema_issues(err)) from err
    issues = check_input(instance)
    if issues:
        raise InvalidInputError(issues)
    return instance


def check_input(instance: Instance) -> list[InputIssue]:
    """Semua pelanggaran §1.7 yang tidak dijaga skema. Daftar kosong = input valid."""
    # Langkah 1: struktur dulu. Kalau matriks salah bentuk atau rujukan indeks rusak,
    # pemeriksaan berikutnya akan mengindeks di luar batas, jadi berhenti di sini.
    issues = _check_structure(instance)
    if issues:
        return issues
    # Langkah 2: pemeriksaan antar-field. Semuanya dikumpulkan, tidak berhenti di yang pertama.
    issues += _check_kitchen(instance)
    issues += _check_points(instance)
    issues += _check_nodes(instance)
    issues += _check_diagonal(instance, "travel_time")
    issues += _check_diagonal(instance, "distance")
    issues += _check_triangle(instance)
    return issues


def _schema_issues(err: ValidationError) -> list[InputIssue]:
    # Ubah error Pydantic menjadi InputIssue. `loc` berisi jalur, misalnya ("nodes", 1, "demand").
    issues = []
    for e in err.errors():
        path = ""
        for part in e["loc"]:
            path += f"[{part}]" if isinstance(part, int) else (f".{part}" if path else str(part))
        issues.append(InputIssue(IssueCode.SCHEMA, path or "$", e["msg"]))
    return issues


def _check_structure(inst: Instance) -> list[InputIssue]:
    issues: list[InputIssue] = []
    size = len(inst.points) + 1  # P titik layanan + dapur
    for field in ("travel_time", "distance"):
        matrix: list[list[int]] = getattr(inst, field)
        if len(matrix) != size or any(len(row) != size for row in matrix):
            issues.append(
                InputIssue(
                    IssueCode.MATRIX_SHAPE, field, f"harus {size} x {size} (dapur + P titik)"
                )
            )
    used = set()
    for j, node in enumerate(inst.nodes):
        if node.point > len(inst.points):
            issues.append(
                InputIssue(
                    IssueCode.POINT_OUT_OF_RANGE,
                    f"nodes[{j}].point",
                    f"{node.point} di luar 1..{len(inst.points)}",
                )
            )
        used.add(node.point)
    for p in range(1, len(inst.points) + 1):
        if p not in used:
            issues.append(
                InputIssue(
                    IssueCode.POINT_WITHOUT_NODE,
                    f"points[{p - 1}]",
                    "titik layanan tanpa node; titik tanpa demand ditolak (C1)",
                )
            )
    return issues


def _check_kitchen(inst: Instance) -> list[InputIssue]:
    k = inst.kitchen
    if k.open > k.close:
        return [
            InputIssue(
                IssueCode.KITCHEN_HOURS_INVERTED, "kitchen", f"open {k.open} > close {k.close}"
            )
        ]
    return []


def _check_points(inst: Instance) -> list[InputIssue]:
    issues = []
    for p, point in enumerate(inst.points):
        d = point.consume - point.buffer
        if d < 0:
            issues.append(
                InputIssue(IssueCode.DEADLINE_NEGATIVE, f"points[{p}]", f"d = m - delta = {d} < 0")
            )
        elif point.ready > d:
            issues.append(
                InputIssue(
                    IssueCode.WINDOW_INVERTED, f"points[{p}]", f"a = {point.ready} > d = {d}"
                )
            )
    return issues


def _check_nodes(inst: Instance) -> list[InputIssue]:
    issues = []
    limit = inst.piece_limit
    for j, node in enumerate(inst.nodes):
        buffer = inst.points[node.point - 1].buffer
        if node.service > buffer:
            issues.append(
                InputIssue(
                    IssueCode.SERVICE_EXCEEDS_BUFFER,
                    f"nodes[{j}].service",
                    f"s = {node.service} > delta = {buffer} (B5)",
                )
            )
        if node.demand > limit:
            issues.append(
                InputIssue(
                    IssueCode.DEMAND_EXCEEDS_LIMIT,
                    f"nodes[{j}].demand",
                    f"q = {node.demand} > Q-bar = {limit}; pecah demand dulu (§4.1, K1)",
                )
            )
    return issues


def _check_diagonal(inst: Instance, field: str) -> list[InputIssue]:
    matrix = np.asarray(getattr(inst, field))
    bad = np.flatnonzero(np.diag(matrix))
    return [
        InputIssue(IssueCode.DIAGONAL_NONZERO, f"{field}[{i}][{i}]", f"= {matrix[i, i]}, harus 0")
        for i in bad
    ]


def _check_triangle(inst: Instance) -> list[InputIssue]:
    # B6: tau[i, j] <= tau[i, k] + tau[k, j] untuk semua i, j, k.
    # Broadcasting (L0.10): via[i, k, j] = tau[i, k] + tau[k, j], ukuran L x L x L.
    # Lalu ambil jalan memutar terpendek atas k: shortcut[i, j] = min_k via[i, k, j].
    # Melanggar bila tau[i, j] > shortcut[i, j]. Semua bilangan bulat, jadi tanpa toleransi.
    tau = np.asarray(inst.travel_time, dtype=np.int64)
    via = tau[:, :, None] + tau[None, :, :]
    shortcut = via.min(axis=1)
    issues = []
    for i, j in zip(*np.nonzero(tau > shortcut), strict=True):
        k = int(via[i, :, j].argmin())
        issues.append(
            InputIssue(
                IssueCode.TRIANGLE_VIOLATED,
                f"travel_time[{i}][{j}]",
                f"{tau[i, j]} > {tau[i, k]} + {tau[k, j]} lewat lokasi {k} (B6)",
            )
        )
    return issues
