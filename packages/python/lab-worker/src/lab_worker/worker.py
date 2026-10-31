"""Loop runtime worker: klaim, jalankan handler, selesaikan (LAB-ADR-010).

Desain crash-only: kehilangan koneksi database menghentikan proses, lalu
supervisor (Docker, restart: unless-stopped) menyalakannya kembali dan
reaper mengambil alih job yang tertinggal.
"""

from __future__ import annotations

import logging
import os
import random
import signal
import socket
import threading
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import FrameType
from typing import Any

import psycopg
from psycopg import sql

from lab_worker.backoff import backoff_seconds
from lab_worker.contracts import (
    InvalidPayloadError,
    Registry,
    UnknownKindError,
    default_contracts_dir,
)
from lab_worker.queue import (
    NOTIFY_CHANNEL,
    ClaimedJob,
    Conn,
    claim,
    complete,
    fail,
    heartbeat,
    reap_expired,
    report_progress,
)

log = logging.getLogger(__name__)


class PermanentError(Exception):
    """Kegagalan yang tidak akan sembuh dengan retry (mis. input mustahil dipenuhi)."""


def _default_worker_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"


@dataclass(frozen=True, slots=True)
class WorkerConfig:
    """Parameter waktu worker. Ambang basi sekitar 3x interval heartbeat."""

    database_url: str
    worker_id: str = field(default_factory=_default_worker_id)
    poll_interval_s: float = 30.0  # polling cadangan bila NOTIFY terlewat
    heartbeat_interval_s: float = 5.0
    stale_after_s: float = 15.0
    reap_interval_s: float = 30.0
    stop_check_s: float = 1.0  # seberapa cepat flag stop diperiksa saat menunggu
    retry_base_s: float = 5.0
    retry_cap_s: float = 300.0


class JobContext:
    """Antarmuka handler: payload, pelaporan progres, dan status lease."""

    def __init__(
        self, job: ClaimedJob, conn: Conn, worker_id: str, lease_lost: threading.Event
    ) -> None:
        self._job = job
        self._conn = conn
        self._worker_id = worker_id
        self._lease_lost = lease_lost

    @property
    def job(self) -> ClaimedJob:
        return self._job

    @property
    def payload(self) -> dict[str, Any]:
        return self._job.payload

    @property
    def lease_lost(self) -> bool:
        """True bila job sudah bukan milik worker ini; handler sebaiknya berhenti."""
        return self._lease_lost.is_set()

    def progress(self, data: Mapping[str, Any]) -> None:
        if not report_progress(self._conn, self._job, self._worker_id, data):
            self._lease_lost.set()


type Handler = Callable[[JobContext], Mapping[str, Any]]


def _exit_on_timeout() -> None:
    # os._exit menghentikan proses meski thread utama terjebak di kode native (Rust).
    os._exit(os.EX_TEMPFAIL)


class Worker:
    """Satu worker, concurrency 1 job (LAB-ADR-007)."""

    def __init__(
        self,
        config: WorkerConfig,
        handlers: Mapping[str, Handler],
        registry: Registry,
        *,
        on_timeout: Callable[[], None] = _exit_on_timeout,
        rng: random.Random | None = None,
    ) -> None:
        missing = set(handlers) - registry.kinds
        if missing:
            raise ValueError(f"handler tanpa kontrak: {sorted(missing)}")
        self._cfg = config
        self._handlers = dict(handlers)
        self._kinds = sorted(handlers)
        self._registry = registry
        self._on_timeout = on_timeout
        self._rng = rng or random.Random()

    def run(self, stop: threading.Event) -> None:
        url = self._cfg.database_url
        with (
            psycopg.connect(url, autocommit=True) as listen_conn,
            psycopg.connect(url, autocommit=True) as work_conn,
            psycopg.connect(url, autocommit=True) as hb_conn,
        ):
            # LISTEN dipasang sebelum klaim pertama agar tidak ada notifikasi yang terlewat.
            listen_conn.execute(sql.SQL("LISTEN {}").format(sql.Identifier(NOTIFY_CHANNEL)))
            log.info("worker %s siap, kinds=%s", self._cfg.worker_id, self._kinds)
            next_reap = 0.0
            while not stop.is_set():
                now = time.monotonic()
                if now >= next_reap:
                    for job_id, status in reap_expired(work_conn, self._cfg.stale_after_s):
                        log.warning("lease basi: job %s -> %s", job_id, status)
                    next_reap = now + self._cfg.reap_interval_s

                job = claim(work_conn, self._cfg.worker_id, self._kinds)
                if job is not None:
                    self._process(job, work_conn, hb_conn)
                    continue  # kosongkan antrean sebelum menunggu lagi
                self._wait(listen_conn, stop)
        log.info("worker %s berhenti", self._cfg.worker_id)

    def _wait(self, listen_conn: Conn, stop: threading.Event) -> None:
        """Tunggu NOTIFY, polling cadangan, atau flag stop, mana yang lebih dulu."""
        deadline = time.monotonic() + self._cfg.poll_interval_s
        while not stop.is_set():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            for _ in listen_conn.notifies(
                timeout=min(self._cfg.stop_check_s, remaining), stop_after=1
            ):
                return

    def _retry_delay(self, job: ClaimedJob) -> float:
        return backoff_seconds(
            job.attempts, base=self._cfg.retry_base_s, cap=self._cfg.retry_cap_s, rng=self._rng
        )

    def _process(self, job: ClaimedJob, work_conn: Conn, hb_conn: Conn) -> None:
        wid = self._cfg.worker_id
        try:
            self._registry.validate(job.kind, job.schema_version, job.payload)
        except (UnknownKindError, InvalidPayloadError) as exc:
            log.error("job %s payload invalid: %s", job.id, exc)
            fail(
                work_conn,
                job,
                wid,
                {"kind": "invalid_payload", "message": str(exc)},
                retryable=False,
                retry_delay_s=0,
            )
            return

        lease_lost = threading.Event()
        done = threading.Event()
        hb = threading.Thread(
            target=self._heartbeat_loop,
            args=(job, hb_conn, lease_lost, done),
            name=f"heartbeat-{job.id}",
            daemon=True,
        )
        hb.start()

        result: Mapping[str, Any] | None = None
        error: Exception | None = None
        try:
            result = self._handlers[job.kind](JobContext(job, work_conn, wid, lease_lost))
        except Exception as exc:  # semua error handler dicatat ke job
            error = exc
        finally:
            # Hentikan heartbeat sebelum menulis status akhir, agar heartbeat
            # tidak salah menganggap lease hilang setelah job selesai.
            done.set()
            hb.join()

        if lease_lost.is_set():
            log.warning("job %s: lease hilang, hasil dibuang", job.id)
            return
        if error is None:
            assert result is not None
            if not complete(work_conn, job, wid, result):
                log.warning("job %s: lease hilang saat complete, hasil dibuang", job.id)
            return

        retryable = not isinstance(error, PermanentError)
        outcome = fail(
            work_conn,
            job,
            wid,
            {"kind": type(error).__name__, "message": str(error)},
            retryable=retryable,
            retry_delay_s=self._retry_delay(job) if retryable else 0,
        )
        log.error("job %s gagal (%s): %r", job.id, outcome, error)

    def _heartbeat_loop(
        self, job: ClaimedJob, conn: Conn, lease_lost: threading.Event, done: threading.Event
    ) -> None:
        wid = self._cfg.worker_id
        deadline = time.monotonic() + job.timeout_s
        # done.wait(t) mengembalikan True begitu job selesai, False bila t habis.
        while not done.wait(self._cfg.heartbeat_interval_s):
            if time.monotonic() >= deadline:
                log.error("job %s melewati timeout %ss", job.id, job.timeout_s)
                fail(
                    conn,
                    job,
                    wid,
                    {"kind": "timeout", "timeout_s": job.timeout_s},
                    retryable=True,
                    retry_delay_s=self._retry_delay(job),
                )
                lease_lost.set()
                self._on_timeout()
                return
            if not heartbeat(conn, job, wid):
                log.warning("job %s: heartbeat ditolak, lease hilang", job.id)
                lease_lost.set()
                return


def run_forever(
    handlers: Mapping[str, Handler],
    *,
    config: WorkerConfig | None = None,
    registry: Registry | None = None,
) -> None:
    """Titik masuk proses worker: logging, sinyal, lalu loop sampai SIGTERM/SIGINT."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(threadName)s %(message)s"
    )
    cfg = config or WorkerConfig(database_url=os.environ["DATABASE_URL"])
    reg = registry or Registry.from_dir(default_contracts_dir())
    stop = threading.Event()

    def _on_signal(signum: int, _frame: FrameType | None) -> None:
        log.info("sinyal %s diterima, berhenti setelah job berjalan selesai", signum)
        stop.set()

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)
    Worker(cfg, handlers, reg).run(stop)
