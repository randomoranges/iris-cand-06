"""The QA engine: run a profile over a dataset and aggregate to one verdict.

The engine is deliberately tiny. All the "how bad is this" knowledge lives in the
profile (severity binding); all the "what is wrong" knowledge lives in the checks.
The engine just wires them together:

    failure of a check  ->  outcome = that check's configured severity
    check passes        ->  outcome = PASS
    dataset outcome     ->  worst of all check outcomes
"""

from __future__ import annotations

import psycopg
from psycopg import sql

from .contracts import CheckOutcome, Outcome, RunResult, Severity
from .profiles import Profile


def _row_count(conn: psycopg.Connection, table: str) -> int:
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT COUNT(*) AS n FROM {}").format(sql.Identifier(table)))
        return cur.fetchone()["n"]


def _outcome_for(ok: bool, severity: Severity) -> Outcome:
    if ok:
        return Outcome.PASS
    return Outcome.BLOCK if severity is Severity.BLOCK else Outcome.WARN


def run_profile(conn: psycopg.Connection, profile: Profile) -> RunResult:
    target = profile.target
    outcomes: list[CheckOutcome] = []
    for spec in profile.specs:
        result = spec.check.run(conn, target)
        outcome = _outcome_for(result.ok, spec.severity)
        outcomes.append(CheckOutcome(result=result, severity=spec.severity, outcome=outcome))
    return RunResult(
        dataset=target.dataset,
        country_code=target.country,
        row_count=_row_count(conn, target.table),
        checks=outcomes,
    )
