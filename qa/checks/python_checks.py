"""Python-side checks.

These pull the relevant columns and evaluate the rule *in Python* — the natural
place for field-level contract logic (required vs optional, scope membership,
freshness). Satisfies the "at least one check in Python" requirement.

Ordering is deterministic (ORDER BY key) so evidence is reproducible.
"""

from __future__ import annotations

import psycopg
from psycopg import sql

from ..contracts import CheckResult
from ..target import Target
from .base import EVIDENCE_LIMIT


def _fetch(conn: psycopg.Connection, target: Target, columns: list[str]) -> list[dict]:
    select_cols = sql.SQL(", ").join(sql.Identifier(c) for c in [target.key, *columns])
    query = sql.SQL("SELECT {cols} FROM {table} ORDER BY {key}").format(
        cols=select_cols, table=sql.Identifier(target.table), key=sql.Identifier(target.key)
    )
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


class RequiredFields:
    """Named columns must be present (non-null). Missing -> the profile's severity."""

    kind = "python"

    def __init__(self, columns: list[str], name: str = "required_fields"):
        self.columns = columns
        self.name = name

    def run(self, conn: psycopg.Connection, target: Target) -> CheckResult:
        rows = _fetch(conn, target, self.columns)
        offending = []
        for row in rows:
            missing = [c for c in self.columns if row.get(c) is None]
            if missing:
                offending.append({"key": row[target.key], "missing": missing})
        return CheckResult(
            name=self.name,
            kind=self.kind,
            ok=not offending,
            failed_count=len(offending),
            evidence=offending[:EVIDENCE_LIMIT],
            detail=(
                f"{len(offending)} row(s) missing required field(s)"
                if offending
                else "all required fields present"
            ),
        )


class OptionalPresent:
    """An optional enrichment column. If null it should WARN (stay visible as unknown),
    never block — the profile binds this to Severity.WARN."""

    kind = "python"

    def __init__(self, column: str, name: str | None = None):
        self.column = column
        self.name = name or f"optional_{column}"

    def run(self, conn: psycopg.Connection, target: Target) -> CheckResult:
        rows = _fetch(conn, target, [self.column])
        offending = [
            {"key": row[target.key], "unknown": self.column}
            for row in rows
            if row.get(self.column) is None
        ]
        return CheckResult(
            name=self.name,
            kind=self.kind,
            ok=not offending,
            failed_count=len(offending),
            evidence=offending[:EVIDENCE_LIMIT],
            detail=(
                f"{len(offending)} row(s) missing optional '{self.column}'"
                if offending
                else f"'{self.column}' present on all rows"
            ),
        )


class CountryScope:
    """country_code must be non-null AND equal to the dataset's expected country.
    Enforces the non-null country_code contract and catches country mismatch."""

    name = "country_scope"
    kind = "python"

    def run(self, conn: psycopg.Connection, target: Target) -> CheckResult:
        rows = _fetch(conn, target, ["country_code"])
        offending = []
        for row in rows:
            cc = row.get("country_code")
            if cc is None:
                offending.append({"key": row[target.key], "country_code": None, "why": "null"})
            elif cc != target.country:
                offending.append(
                    {"key": row[target.key], "country_code": cc, "why": f"expected {target.country}"}
                )
        return CheckResult(
            name=self.name,
            kind=self.kind,
            ok=not offending,
            failed_count=len(offending),
            evidence=offending[:EVIDENCE_LIMIT],
            detail=(
                f"{len(offending)} row(s) out of country scope"
                if offending
                else f"all rows scoped to {target.country}"
            ),
        )


class SourceDatePresent:
    """source_date is a freshness contract. Missing -> WARN (never invented)."""

    name = "source_date"
    kind = "python"

    def run(self, conn: psycopg.Connection, target: Target) -> CheckResult:
        rows = _fetch(conn, target, ["source_date"])
        offending = [
            {"key": row[target.key], "unknown": "source_date"}
            for row in rows
            if row.get("source_date") is None
        ]
        return CheckResult(
            name=self.name,
            kind=self.kind,
            ok=not offending,
            failed_count=len(offending),
            evidence=offending[:EVIDENCE_LIMIT],
            detail=(
                f"{len(offending)} row(s) missing source_date"
                if offending
                else "source_date present on all rows"
            ),
        )
