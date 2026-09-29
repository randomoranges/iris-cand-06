"""SQL-side checks.

These express their logic *in SQL* (WHERE / GROUP BY / HAVING and PostGIS
functions) and let PostgreSQL do the work — the natural tool for set-based and
spatial correctness. Satisfies the "at least one check in SQL" requirement.

Every query is deterministic (explicit ORDER BY key) so evidence and outcomes
are byte-for-byte reproducible across runs.
"""

from __future__ import annotations

import psycopg
from psycopg import sql

from ..contracts import CheckResult
from ..target import Target
from .base import EVIDENCE_LIMIT


def _ident(name: str) -> sql.Identifier:
    return sql.Identifier(name)


class KeyUniqueness:
    """Business key must be unique. Duplicate keys inflate counts -> BLOCK/quarantine."""

    name = "key_uniqueness"
    kind = "sql"

    def run(self, conn: psycopg.Connection, target: Target) -> CheckResult:
        query = sql.SQL(
            "SELECT {key} AS key, COUNT(*) AS n "
            "FROM {table} "
            "WHERE {key} IS NOT NULL "
            "GROUP BY {key} HAVING COUNT(*) > 1 "
            "ORDER BY {key}"
        ).format(key=_ident(target.key), table=_ident(target.table))
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
        evidence = [{"key": r["key"], "duplicate_count": r["n"]} for r in rows[:EVIDENCE_LIMIT]]
        return CheckResult(
            name=self.name,
            kind=self.kind,
            ok=not rows,
            failed_count=len(rows),
            evidence=evidence,
            detail=f"{len(rows)} duplicated key value(s)" if rows else "all keys unique",
        )


class DuplicateRows:
    """Fully-identical business rows (every business column equal) -> duplicate inflation."""

    name = "duplicate_rows"
    kind = "sql"

    def run(self, conn: psycopg.Connection, target: Target) -> CheckResult:
        # Compare geometry by its canonical text so identical shapes group together.
        col_exprs = []
        for c in target.business_cols:
            if c == target.geom_col:
                col_exprs.append(sql.SQL("ST_AsText({})").format(_ident(c)))
            else:
                col_exprs.append(sql.SQL("{}::text").format(_ident(c)))
        signature = sql.SQL(" || '|' || ").join(
            sql.SQL("COALESCE({}, '<null>')").format(e) for e in col_exprs
        )
        query = sql.SQL(
            "SELECT sig, COUNT(*) AS n FROM ("
            "  SELECT {signature} AS sig FROM {table}"
            ") s GROUP BY sig HAVING COUNT(*) > 1 ORDER BY sig"
        ).format(signature=signature, table=_ident(target.table))
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
        evidence = [{"signature": r["sig"], "duplicate_count": r["n"]} for r in rows[:EVIDENCE_LIMIT]]
        return CheckResult(
            name=self.name,
            kind=self.kind,
            ok=not rows,
            failed_count=len(rows),
            evidence=evidence,
            detail=f"{len(rows)} fully-duplicated row group(s)" if rows else "no full-row duplicates",
        )


class GeometryValid:
    """Geometry must be OGC-valid (no self-intersections etc.). Uses ST_IsValid."""

    name = "geometry_valid"
    kind = "sql"

    def run(self, conn: psycopg.Connection, target: Target) -> CheckResult:
        query = sql.SQL(
            "SELECT {key} AS key, ST_IsValidReason({geom}) AS reason "
            "FROM {table} "
            "WHERE {geom} IS NOT NULL AND NOT ST_IsValid({geom}) "
            "ORDER BY {key}"
        ).format(key=_ident(target.key), geom=_ident(target.geom_col), table=_ident(target.table))
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
        evidence = [{"key": r["key"], "reason": r["reason"]} for r in rows[:EVIDENCE_LIMIT]]
        return CheckResult(
            name=self.name,
            kind=self.kind,
            ok=not rows,
            failed_count=len(rows),
            evidence=evidence,
            detail=f"{len(rows)} invalid geometry(ies)" if rows else "all geometries valid",
        )


class GeometryType:
    """Geometry type must match the dataset contract (e.g. polygon for parcels)."""

    name = "geometry_type"
    kind = "sql"

    def run(self, conn: psycopg.Connection, target: Target) -> CheckResult:
        allowed = list(target.geom_types)
        query = sql.SQL(
            "SELECT {key} AS key, GeometryType({geom}) AS gtype "
            "FROM {table} "
            "WHERE {geom} IS NOT NULL AND GeometryType({geom}) <> ALL(%s) "
            "ORDER BY {key}"
        ).format(key=_ident(target.key), geom=_ident(target.geom_col), table=_ident(target.table))
        with conn.cursor() as cur:
            cur.execute(query, (allowed,))
            rows = cur.fetchall()
        evidence = [{"key": r["key"], "found_type": r["gtype"]} for r in rows[:EVIDENCE_LIMIT]]
        return CheckResult(
            name=self.name,
            kind=self.kind,
            ok=not rows,
            failed_count=len(rows),
            evidence=evidence,
            detail=(
                f"{len(rows)} row(s) not in {allowed}" if rows else f"all geometries in {allowed}"
            ),
        )


class GeometrySrid:
    """Geometry SRID must equal the expected CRS (default EPSG:4326)."""

    name = "geometry_srid"
    kind = "sql"

    def run(self, conn: psycopg.Connection, target: Target) -> CheckResult:
        query = sql.SQL(
            "SELECT {key} AS key, ST_SRID({geom}) AS srid "
            "FROM {table} "
            "WHERE {geom} IS NOT NULL AND ST_SRID({geom}) <> %s "
            "ORDER BY {key}"
        ).format(key=_ident(target.key), geom=_ident(target.geom_col), table=_ident(target.table))
        with conn.cursor() as cur:
            cur.execute(query, (target.expected_srid,))
            rows = cur.fetchall()
        evidence = [{"key": r["key"], "found_srid": r["srid"]} for r in rows[:EVIDENCE_LIMIT]]
        return CheckResult(
            name=self.name,
            kind=self.kind,
            ok=not rows,
            failed_count=len(rows),
            evidence=evidence,
            detail=(
                f"{len(rows)} row(s) not SRID {target.expected_srid}"
                if rows
                else f"all geometries SRID {target.expected_srid}"
            ),
        )
