"""Operasi antrean job lab di PostgreSQL (LAB-ADR-003, LAB-ADR-010).

Semua fungsi mengasumsikan koneksi autocommit: setiap perintah adalah satu
transaksi singkat. Selama job berjalan, kepemilikan dicatat sebagai lease
(worker_id, attempts, heartbeat_at), bukan sebagai lock yang ditahan.
Setiap tulisan worker memakai fencing pada (id, worker_id, attempts); hasil
0 baris berarti lease sudah hilang dan hasil kerja harus dibuang.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, LiteralString
from uuid import UUID

import psycopg
from psycopg.rows import class_row
from psycopg.types.json import Jsonb

NOTIFY_CHANNEL = "lab_jobs"
PROGRESS_CHANNEL = "lab_job_progress"

type Conn = psycopg.Connection[Any]
type FailOutcome = Literal["retry", "failed", "lost"]


@dataclass(frozen=True, slots=True)
class ClaimedJob:
    """Job yang sudah diklaim. ``attempts`` sekaligus berperan sebagai fencing token."""

    id: UUID
    kind: str
    schema_version: int
    payload: dict[str, Any]
    attempts: int
    max_attempts: int
    timeout_s: int


_CLAIM: LiteralString = """
WITH next AS (
    SELECT id FROM lab_jobs
    WHERE status = 'queued' AND run_after <= now() AND kind = ANY(%(kinds)s)
    ORDER BY priority DESC, run_after, id
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
UPDATE lab_jobs AS j
SET status = 'running',
    attempts = j.attempts + 1,
    worker_id = %(worker_id)s,
    started_at = now(),
    heartbeat_at = now(),
    progress = NULL
FROM next
WHERE j.id = next.id
RETURNING j.id, j.kind, j.schema_version, j.payload, j.attempts, j.max_attempts, j.timeout_s
"""


def _lease(job: ClaimedJob, worker_id: str) -> dict[str, Any]:
    return {"id": job.id, "worker_id": worker_id, "attempts": job.attempts}


def claim(conn: Conn, worker_id: str, kinds: Sequence[str]) -> ClaimedJob | None:
    """Klaim satu job queued dengan prioritas tertinggi; None bila tidak ada.

    ``started_at`` diisi ulang tiap percobaan, sehingga ``timeout_s`` berlaku
    per percobaan, bukan total.
    """
    with conn.cursor(row_factory=class_row(ClaimedJob)) as cur:
        return cur.execute(_CLAIM, {"kinds": list(kinds), "worker_id": worker_id}).fetchone()


def heartbeat(conn: Conn, job: ClaimedJob, worker_id: str) -> bool:
    """Perbarui heartbeat. False berarti lease hilang: pekerjaan harus dihentikan."""
    cur = conn.execute(
        """
        UPDATE lab_jobs SET heartbeat_at = now()
        WHERE id = %(id)s AND status = 'running'
          AND worker_id = %(worker_id)s AND attempts = %(attempts)s
        """,
        _lease(job, worker_id),
    )
    return cur.rowcount == 1


def report_progress(
    conn: Conn, job: ClaimedJob, worker_id: str, progress: Mapping[str, Any]
) -> bool:
    """Simpan progres dan beri tahu pendengar (SSE di L0.5) lewat PROGRESS_CHANNEL."""
    with conn.transaction():
        cur = conn.execute(
            """
            UPDATE lab_jobs SET progress = %(progress)s, heartbeat_at = now()
            WHERE id = %(id)s AND status = 'running'
              AND worker_id = %(worker_id)s AND attempts = %(attempts)s
            """,
            {**_lease(job, worker_id), "progress": Jsonb(dict(progress))},
        )
        if cur.rowcount != 1:
            return False
        # Notifikasi ikut transaksi: hanya terkirim bila update di atas ter-commit.
        conn.execute("SELECT pg_notify(%s, %s)", (PROGRESS_CHANNEL, str(job.id)))
    return True


def complete(conn: Conn, job: ClaimedJob, worker_id: str, result: Mapping[str, Any]) -> bool:
    """Tandai job sukses. False berarti lease hilang dan hasil ini dibuang."""
    cur = conn.execute(
        """
        UPDATE lab_jobs
        SET status = 'succeeded', result = %(result)s, finished_at = now()
        WHERE id = %(id)s AND status = 'running'
          AND worker_id = %(worker_id)s AND attempts = %(attempts)s
        """,
        {**_lease(job, worker_id), "result": Jsonb(dict(result))},
    )
    return cur.rowcount == 1


def fail(
    conn: Conn,
    job: ClaimedJob,
    worker_id: str,
    error: Mapping[str, Any],
    *,
    retryable: bool,
    retry_delay_s: float,
) -> FailOutcome:
    """Catat kegagalan: kembali ke antrean bila boleh retry dan jatah masih ada.

    Keputusan retry memakai ``attempts`` dan ``max_attempts`` dari database,
    bukan salinan lokal, agar konsisten dengan reaper.
    """
    cur = conn.execute(
        """
        UPDATE lab_jobs SET
            status      = CASE WHEN %(retry)s AND attempts < max_attempts
                               THEN 'queued' ELSE 'failed' END,
            run_after   = CASE WHEN %(retry)s AND attempts < max_attempts
                               THEN now() + make_interval(secs => %(delay)s)
                               ELSE run_after END,
            finished_at = CASE WHEN %(retry)s AND attempts < max_attempts
                               THEN NULL ELSE now() END,
            worker_id = NULL,
            heartbeat_at = NULL,
            error = %(error)s
        WHERE id = %(id)s AND status = 'running'
          AND worker_id = %(worker_id)s AND attempts = %(attempts)s
        RETURNING status
        """,
        {
            **_lease(job, worker_id),
            "retry": retryable,
            "delay": retry_delay_s,
            "error": Jsonb({**error, "worker_id": worker_id, "attempt": job.attempts}),
        },
    )
    row = cur.fetchone()
    if row is None:
        return "lost"
    return "retry" if row[0] == "queued" else "failed"


def reap_expired(conn: Conn, stale_after_s: float) -> list[tuple[UUID, str]]:
    """Ambil alih job running yang heartbeat-nya basi; kembalikan (id, status baru).

    Ekspresi di SET membaca nilai baris lama, jadi ``worker_id`` di dalam
    ``error`` adalah pemilik lease yang kedaluwarsa.
    """
    cur = conn.execute(
        """
        UPDATE lab_jobs SET
            status      = CASE WHEN attempts < max_attempts THEN 'queued' ELSE 'failed' END,
            finished_at = CASE WHEN attempts < max_attempts THEN NULL ELSE now() END,
            run_after   = now(),
            error = jsonb_build_object(
                'kind', 'lease_expired', 'worker_id', worker_id, 'attempt', attempts),
            worker_id = NULL,
            heartbeat_at = NULL
        WHERE status = 'running'
          AND heartbeat_at < now() - make_interval(secs => %(stale)s)
        RETURNING id, status
        """,
        {"stale": stale_after_s},
    )
    return [(row[0], row[1]) for row in cur.fetchall()]
