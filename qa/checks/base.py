"""Check protocol — the shape every check implements.

A check inspects one dataset and returns a CheckResult (found problems? what were
they?). It never decides severity; the profile does that.
"""

from __future__ import annotations

from typing import Protocol

import psycopg

from ..contracts import CheckResult
from ..target import Target

EVIDENCE_LIMIT = 50  # cap sample rows kept in evidence, for compact reports


class Check(Protocol):
    name: str
    kind: str  # "sql" | "python"

    def run(self, conn: psycopg.Connection, target: Target) -> CheckResult: ...
