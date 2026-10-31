"""Fixture Postgres sungguhan (testcontainers) dengan skema dari migrasi Go."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import psycopg
import pytest
from testcontainers.postgres import PostgresContainer

# tests → lab-worker → python → packages → root repo
ROOT = Path(__file__).resolve().parents[4]
MIGRATIONS = ROOT / "packages" / "go" / "jobqueue" / "migrations"


def _up_sql(path: Path) -> str:
    """Ambil bagian Up dari file migrasi goose (satu sumber kebenaran skema)."""
    text = path.read_text()
    up = text.split("-- +goose Up", 1)[1]
    return up.split("-- +goose Down", 1)[0]


@pytest.fixture(scope="session")
def pg_url() -> Iterator[str]:
    with PostgresContainer("postgres:18", driver=None) as pg:
        url = pg.get_connection_url()
        with psycopg.connect(url, autocommit=True) as conn:
            for path in sorted(MIGRATIONS.glob("*.sql")):
                conn.execute(_up_sql(path))  # tanpa parameter: boleh banyak perintah
        yield url


@pytest.fixture
def conn(pg_url: str) -> Iterator[psycopg.Connection[Any]]:
    with psycopg.connect(pg_url, autocommit=True) as c:
        c.execute("TRUNCATE lab_jobs")
        yield c
