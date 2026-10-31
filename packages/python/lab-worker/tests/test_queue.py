import threading
from typing import Any
from uuid import UUID

import psycopg
from lab_worker.queue import (
    claim,
    complete,
    fail,
    heartbeat,
    reap_expired,
)

type Conn = psycopg.Connection[Any]


def enqueue(conn: Conn, *, priority: int = 0, max_attempts: int = 3, i: int = 0) -> UUID:
    """Pembantu test. Di produksi hanya Go yang melakukan enqueue."""
    row = conn.execute(
        """INSERT INTO lab_jobs (kind, schema_version, payload, priority, max_attempts)
           VALUES ('demo', 1, jsonb_build_object('i', %s::int), %s, %s) RETURNING id""",
        (i, priority, max_attempts),
    ).fetchone()
    assert row is not None
    return row[0]


def status_of(conn: Conn, job_id: UUID) -> str:
    row = conn.execute("SELECT status FROM lab_jobs WHERE id = %s", (job_id,)).fetchone()
    assert row is not None
    return str(row[0])


def test_klaim_antrean_kosong(conn: Conn) -> None:
    assert claim(conn, "w1", ["demo"]) is None


def test_klaim_prioritas_tertinggi_dan_menaikkan_attempts(conn: Conn) -> None:
    enqueue(conn, priority=0, i=1)
    tinggi = enqueue(conn, priority=5, i=2)
    job = claim(conn, "w1", ["demo"])
    assert job is not None
    assert job.id == tinggi
    assert job.attempts == 1
    assert job.payload == {"i": 2}
    assert status_of(conn, job.id) == "running"


def test_klaim_menyaring_kind(conn: Conn) -> None:
    enqueue(conn)
    assert claim(conn, "w1", ["lain"]) is None


def test_klaim_konkuren_tiap_job_tepat_sekali(pg_url: str, conn: Conn) -> None:
    ids = {enqueue(conn, i=i) for i in range(50)}
    diklaim: list[UUID] = []
    kunci = threading.Lock()

    def kerja(nama: str) -> None:
        with psycopg.connect(pg_url, autocommit=True) as c:
            while (job := claim(c, nama, ["demo"])) is not None:
                with kunci:
                    diklaim.append(job.id)

    threads = [threading.Thread(target=kerja, args=(f"w{i}",)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(diklaim) == 50  # tidak ada yang diproses dua kali
    assert set(diklaim) == ids  # tidak ada yang terlewat


def test_complete_dengan_lease_sah(conn: Conn) -> None:
    enqueue(conn)
    job = claim(conn, "w1", ["demo"])
    assert job is not None
    assert complete(conn, job, "w1", {"ok": True})
    assert status_of(conn, job.id) == "succeeded"


def test_fencing_menolak_worker_dan_percobaan_basi(conn: Conn) -> None:
    enqueue(conn)
    lama = claim(conn, "w1", ["demo"])
    assert lama is not None
    # Lease w1 kedaluwarsa, job kembali ke antrean, lalu diklaim ulang oleh w1 sendiri.
    conn.execute("UPDATE lab_jobs SET heartbeat_at = now() - interval '1 hour'")
    assert reap_expired(conn, stale_after_s=30) == [(lama.id, "queued")]
    baru = claim(conn, "w1", ["demo"])
    assert baru is not None
    assert baru.attempts == 2

    # Thread lama (attempts=1) tidak boleh menyentuh job meski worker_id sama.
    assert not heartbeat(conn, lama, "w1")
    assert not complete(conn, lama, "w1", {"basi": True})
    assert fail(conn, lama, "w1", {"kind": "x"}, retryable=True, retry_delay_s=0) == "lost"
    # Pemilik sah tetap bisa menyelesaikan.
    assert complete(conn, baru, "w1", {"ok": True})


def test_fail_retry_lalu_gagal_permanen(conn: Conn) -> None:
    job_id = enqueue(conn, max_attempts=2)

    j1 = claim(conn, "w1", ["demo"])
    assert j1 is not None
    assert fail(conn, j1, "w1", {"kind": "boom"}, retryable=True, retry_delay_s=60) == "retry"
    assert status_of(conn, job_id) == "queued"
    # run_after di masa depan: belum bisa diklaim.
    assert claim(conn, "w1", ["demo"]) is None

    conn.execute("UPDATE lab_jobs SET run_after = now()")
    j2 = claim(conn, "w1", ["demo"])
    assert j2 is not None
    assert j2.attempts == 2
    assert fail(conn, j2, "w1", {"kind": "boom"}, retryable=True, retry_delay_s=60) == "failed"
    assert status_of(conn, job_id) == "failed"


def test_fail_tidak_retryable_langsung_gagal(conn: Conn) -> None:
    enqueue(conn)
    job = claim(conn, "w1", ["demo"])
    assert job is not None
    assert (
        fail(conn, job, "w1", {"kind": "invalid_payload"}, retryable=False, retry_delay_s=0)
        == "failed"
    )


def test_reaper_menggagalkan_bila_jatah_habis(conn: Conn) -> None:
    enqueue(conn, max_attempts=1)
    job = claim(conn, "w1", ["demo"])
    assert job is not None
    conn.execute("UPDATE lab_jobs SET heartbeat_at = now() - interval '1 hour'")
    assert reap_expired(conn, stale_after_s=30) == [(job.id, "failed")]


def test_reaper_mengabaikan_heartbeat_segar(conn: Conn) -> None:
    enqueue(conn)
    assert claim(conn, "w1", ["demo"]) is not None
    assert reap_expired(conn, stale_after_s=30) == []
