"""Database connection helper.

Connection string comes from the IRIS_DB_URL env var, defaulting to the
local docker-compose database. No production credentials anywhere.
"""

from __future__ import annotations

import os

import psycopg
from psycopg.rows import dict_row

DEFAULT_DB_URL = "postgresql://iris:iris@localhost:5432/iris"


def db_url() -> str:
    return os.environ.get("IRIS_DB_URL", DEFAULT_DB_URL)


def connect() -> psycopg.Connection:
    """Open a connection that returns rows as dicts."""
    return psycopg.connect(db_url(), row_factory=dict_row)


def _split_statements(script: str) -> list[str]:
    """Split a .sql script into individual statements.

    psycopg's extended protocol executes one statement per call, so we split on
    ';' and keep only chunks that contain real SQL (not just comments/blank lines).
    Our migration/fixture files use no dollar-quoted bodies or semicolons inside
    string literals, so a plain split is correct here.
    """
    statements = []
    for chunk in script.split(";"):
        has_sql = any(
            line.strip() and not line.strip().startswith("--")
            for line in chunk.splitlines()
        )
        if has_sql:
            statements.append(chunk.strip())
    return statements


def run_script(conn: psycopg.Connection, script: str) -> None:
    """Execute every statement in a .sql script, then commit."""
    for statement in _split_statements(script):
        conn.execute(statement)
    conn.commit()
