"""Shared test fixtures.

The DB-backed tests need the PostGIS container running and fixtures loaded. The
`conn` fixture (re)applies schema + fixtures from a clean slate each session, so
results are deterministic and independent of prior `qa run` history. If PostGIS
is not reachable, those tests SKIP with a clear message — the pure-logic tests in
test_outcomes.py still run.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from qa import db
from qa.engine import run_profile
from qa.profiles import get_profile

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load(conn, subdir: str) -> None:
    for path in sorted((REPO_ROOT / "db" / subdir).glob("*.sql")):
        db.run_script(conn, path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def conn():
    try:
        connection = db.connect()
    except Exception as exc:  # OperationalError etc.
        pytest.skip(
            f"PostGIS not reachable ({exc}). Start it with `docker compose up -d`."
        )
    _load(connection, "migrations")
    _load(connection, "fixtures")
    yield connection
    connection.close()


@pytest.fixture
def run(conn):
    """Run a dataset's profile and return the RunResult."""

    def _run(dataset: str):
        return run_profile(conn, get_profile(dataset))

    return _run


@pytest.fixture(scope="session")
def results(conn):
    """Run every dataset once; return {dataset: RunResult} for the whole session."""
    from qa.profiles import PROFILES

    return {name: run_profile(conn, get_profile(name)) for name in PROFILES}
