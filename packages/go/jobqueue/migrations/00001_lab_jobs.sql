-- +goose Up
CREATE TABLE lab_jobs (
    id             uuid        PRIMARY KEY DEFAULT uuidv7(),
    kind           text        NOT NULL,              -- mis. 'lab.stats.summary'
    schema_version integer     NOT NULL,              -- versi skema payload
    payload        jsonb       NOT NULL,
    status         text        NOT NULL DEFAULT 'queued'
                   CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
    priority       smallint    NOT NULL DEFAULT 0,    -- lebih besar = lebih dulu
    attempts       integer     NOT NULL DEFAULT 0,    -- naik saat diklaim
    max_attempts   integer     NOT NULL DEFAULT 3 CHECK (max_attempts >= 1),
    run_after      timestamptz NOT NULL DEFAULT now(), -- untuk backoff retry
    timeout_s      integer     NOT NULL DEFAULT 600 CHECK (timeout_s > 0),
    worker_id      text,
    heartbeat_at   timestamptz,
    progress       jsonb,
    result         jsonb,
    error          jsonb,
    created_at     timestamptz NOT NULL DEFAULT now(),
    started_at     timestamptz,
    finished_at    timestamptz,
    CONSTRAINT lab_jobs_running_has_lease
        CHECK (status <> 'running' OR (worker_id IS NOT NULL AND heartbeat_at IS NOT NULL))
);

-- Indeks parsial: hanya job yang menunggu, urutannya sama dengan ORDER BY saat klaim.
CREATE INDEX lab_jobs_queued_idx ON lab_jobs (priority DESC, run_after, id)
    WHERE status = 'queued';

-- Untuk reaper: cari lease yang basi.
CREATE INDEX lab_jobs_running_idx ON lab_jobs (heartbeat_at)
    WHERE status = 'running';

-- +goose Down
DROP TABLE lab_jobs;
