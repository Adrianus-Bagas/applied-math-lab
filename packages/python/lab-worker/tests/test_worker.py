import dataclasses
import json
import threading
import time
from collections.abc import Iterator, Mapping
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg
import pytest
from lab_worker.contracts import Registry
from lab_worker.worker import JobContext, PermanentError, Worker, WorkerConfig
from psycopg.types.json import Jsonb

type Conn = psycopg.Connection[Any]
KIND = "test.echo"


@pytest.fixture
def registry(tmp_path: Path) -> Registry:
    """Kontrak khusus test, terpisah dari kontrak produksi."""
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["x"],
        "properties": {"x": {"type": "integer"}},
    }
    (tmp_path / f"{KIND}.v1.schema.json").write_text(json.dumps(schema))
    return Registry.from_dir(tmp_path)


def config(pg_url: str, **overrides: Any) -> WorkerConfig:
    """Interval dipercepat agar test selesai dalam hitungan detik."""
    base = WorkerConfig(
        database_url=pg_url,
        worker_id="w-test",
        poll_interval_s=30.0,
        heartbeat_interval_s=0.1,
        stale_after_s=60.0,
        reap_interval_s=0.2,
        stop_check_s=0.1,
        retry_base_s=0.01,
        retry_cap_s=0.05,
    )
    return dataclasses.replace(base, **overrides)


def enqueue(
    conn: Conn,
    payload: Mapping[str, Any],
    *,
    notify: bool = True,
    max_attempts: int = 3,
    timeout_s: int = 600,
) -> UUID:
    with conn.transaction():
        row = conn.execute(
            """INSERT INTO lab_jobs (kind, schema_version, payload, max_attempts, timeout_s)
               VALUES (%s, 1, %s, %s, %s) RETURNING id""",
            (KIND, Jsonb(dict(payload)), max_attempts, timeout_s),
        ).fetchone()
        assert row is not None
        if notify:
            conn.execute("SELECT pg_notify('lab_jobs', %s)", (KIND,))
    return row[0]


def wait_status(conn: Conn, job_id: UUID, want: set[str], timeout: float = 10.0) -> tuple[Any, ...]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        row = conn.execute(
            "SELECT status, attempts, result, error, worker_id FROM lab_jobs WHERE id = %s",
            (job_id,),
        ).fetchone()
        if row is not None and row[0] in want:
            return tuple(row)
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} tidak mencapai {want} dalam {timeout}s")


@contextmanager
def running(worker: Worker) -> Iterator[None]:
    """Jalankan worker di thread lain; exception dari worker diteruskan ke test."""
    stop = threading.Event()
    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(worker.run, stop)
        try:
            yield
        finally:
            stop.set()
            fut.result(timeout=10)


def echo(ctx: JobContext) -> Mapping[str, Any]:
    ctx.progress({"tahap": "mulai"})
    return {"echo": ctx.payload["x"]}


def test_sukses_dibangunkan_notify(pg_url: str, conn: Conn, registry: Registry) -> None:
    # poll_interval 30 s: selesai dalam hitungan detik hanya mungkin lewat NOTIFY.
    with running(Worker(config(pg_url), {KIND: echo}, registry)):
        time.sleep(0.3)  # beri waktu worker masuk ke tahap menunggu
        t0 = time.monotonic()
        job_id = enqueue(conn, {"x": 7})
        _, attempts, result, _, _ = wait_status(conn, job_id, {"succeeded"})
    assert result == {"echo": 7}
    assert attempts == 1
    assert time.monotonic() - t0 < 5


def test_polling_cadangan_tanpa_notify(pg_url: str, conn: Conn, registry: Registry) -> None:
    with running(Worker(config(pg_url, poll_interval_s=0.3), {KIND: echo}, registry)):
        job_id = enqueue(conn, {"x": 1}, notify=False)
        wait_status(conn, job_id, {"succeeded"})


def test_error_biasa_di_retry_lalu_gagal(pg_url: str, conn: Conn, registry: Registry) -> None:
    calls: list[int] = []

    def boom(ctx: JobContext) -> Mapping[str, Any]:
        calls.append(ctx.job.attempts)
        raise RuntimeError("sementara")

    cfg = config(pg_url, poll_interval_s=0.1)
    with running(Worker(cfg, {KIND: boom}, registry)):
        job_id = enqueue(conn, {"x": 1}, max_attempts=2)
        _status, attempts, _, error, _ = wait_status(conn, job_id, {"failed"})
    assert calls == [1, 2]
    assert attempts == 2
    assert error["kind"] == "RuntimeError"


def test_permanent_error_tanpa_retry(pg_url: str, conn: Conn, registry: Registry) -> None:
    def mustahil(_ctx: JobContext) -> Mapping[str, Any]:
        raise PermanentError("input mustahil")

    with running(Worker(config(pg_url), {KIND: mustahil}, registry)):
        job_id = enqueue(conn, {"x": 1}, max_attempts=3)
        _, attempts, _, error, _ = wait_status(conn, job_id, {"failed"})
    assert attempts == 1
    assert error["kind"] == "PermanentError"


def test_payload_invalid_handler_tidak_dipanggil(
    pg_url: str, conn: Conn, registry: Registry
) -> None:
    dipanggil = threading.Event()

    def handler(_ctx: JobContext) -> Mapping[str, Any]:
        dipanggil.set()
        return {}

    with running(Worker(config(pg_url), {KIND: handler}, registry)):
        job_id = enqueue(conn, {"x": "bukan integer"})
        _, attempts, _, error, _ = wait_status(conn, job_id, {"failed"})
    assert error["kind"] == "invalid_payload"
    assert attempts == 1
    assert not dipanggil.is_set()


def test_lease_hilang_hasil_dibuang(pg_url: str, conn: Conn, registry: Registry) -> None:
    selesai = threading.Event()

    def diserobot(ctx: JobContext) -> Mapping[str, Any]:
        # Simulasi reaper/worker lain mengambil alih job di tengah jalan.
        with psycopg.connect(pg_url, autocommit=True) as other:
            other.execute("UPDATE lab_jobs SET worker_id = 'penyusup' WHERE id = %s", (ctx.job.id,))
        time.sleep(0.5)  # cukup untuk beberapa detak heartbeat
        selesai.set()
        return {"seharusnya": "dibuang"}

    with running(Worker(config(pg_url), {KIND: diserobot}, registry)):
        job_id = enqueue(conn, {"x": 1})
        assert selesai.wait(10)
        time.sleep(0.2)
        _status, _, result, _, worker_id = wait_status(conn, job_id, {"running"})
    assert worker_id == "penyusup"
    assert result is None


def test_timeout_memicu_watchdog(pg_url: str, conn: Conn, registry: Registry) -> None:
    watchdog = threading.Event()

    def lambat(_ctx: JobContext) -> Mapping[str, Any]:
        time.sleep(1.5)
        return {"terlambat": True}

    worker = Worker(config(pg_url), {KIND: lambat}, registry, on_timeout=watchdog.set)
    with running(worker):
        job_id = enqueue(conn, {"x": 1}, max_attempts=1, timeout_s=1)
        _, _, result, error, _ = wait_status(conn, job_id, {"failed"})
        assert watchdog.wait(5)
    assert error["kind"] == "timeout"
    assert result is None


def test_reaper_mengambil_alih_lease_basi(pg_url: str, conn: Conn, registry: Registry) -> None:
    row = conn.execute(
        """INSERT INTO lab_jobs (kind, schema_version, payload, status, attempts,
                                 worker_id, heartbeat_at, started_at)
           VALUES (%s, 1, '{"x": 3}', 'running', 1, 'worker-mati',
                   now() - interval '1 hour', now() - interval '1 hour')
           RETURNING id""",
        (KIND,),
    ).fetchone()
    assert row is not None

    with running(Worker(config(pg_url, stale_after_s=0.5), {KIND: echo}, registry)):
        _, attempts, result, _, worker_id = wait_status(conn, row[0], {"succeeded"})
    assert attempts == 2
    assert result == {"echo": 3}
    assert worker_id == "w-test"
