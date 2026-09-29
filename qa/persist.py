"""Persist a QA run summary — to PostgreSQL and/or JSON.

The task allows either; we do both because they serve different readers:
  * Postgres tables -> queryable audit history of every gate decision
  * JSON report     -> a portable artefact to attach to a ticket / hand to a reviewer
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .contracts import RunResult


def _json_default(obj: Any) -> str:
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return str(obj)


def persist_to_db(conn: psycopg.Connection, result: RunResult) -> int:
    """Insert one qa_run row and its qa_run_check rows. Returns the run_id."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO qa_run (dataset, country_code, overall_outcome, promoted, row_count) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING run_id",
            (
                result.dataset,
                result.country_code,
                result.overall.value,
                result.promoted,
                result.row_count,
            ),
        )
        run_id = cur.fetchone()["run_id"]
        for c in result.checks:
            cur.execute(
                "INSERT INTO qa_run_check "
                "(run_id, check_name, kind, severity, outcome, failed_count, evidence) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    run_id,
                    c.result.name,
                    c.result.kind,
                    c.severity.value,
                    c.outcome.value,
                    c.result.failed_count,
                    Jsonb(c.result.evidence),
                ),
            )
    conn.commit()
    return run_id


def report_dict(result: RunResult, run_id: int | None = None) -> dict[str, Any]:
    body = result.to_summary()
    if run_id is not None:
        body["run_id"] = run_id
    return body


def write_json_report(result: RunResult, path: Path, run_id: int | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = report_dict(result, run_id)
    path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")
    return path
