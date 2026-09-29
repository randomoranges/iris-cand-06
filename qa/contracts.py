"""Core QA contracts: the outcome model.

The single most important idea in this framework lives here:

    A check does NOT decide how bad its own failure is.
    The PROFILE decides, by binding a Severity to the check for that dataset.

So the exact same `RequiredFields` check is a BLOCK for parcels and a WARN for
an optional soil attribute on peatland — one implementation, different meaning
per dataset. That is what makes the profiles "pluggable" and is what the rubric
calls QA semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """How bad a failure of a check is, *as configured for a dataset*."""

    BLOCK = "BLOCK"  # a correctness failure — stops promotion
    WARN = "WARN"    # tolerable — visible, but does not stop promotion


class Outcome(str, Enum):
    """The verdict of a single check, or of a whole run."""

    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"

    @property
    def rank(self) -> int:
        return {"PASS": 0, "WARN": 1, "BLOCK": 2}[self.value]


def worst(outcomes: list[Outcome]) -> Outcome:
    """Aggregate rule: any BLOCK -> BLOCK, else any WARN -> WARN, else PASS."""
    if not outcomes:
        return Outcome.PASS
    return max(outcomes, key=lambda o: o.rank)


@dataclass
class CheckResult:
    """What a check reports after inspecting a dataset.

    A check only says *whether* it found problems and *what* they were (evidence).
    It never says PASS/WARN/BLOCK — the engine derives that from the profile's
    severity binding.
    """

    name: str
    kind: str                       # "sql" or "python"
    ok: bool                        # True = no problems found
    failed_count: int = 0
    evidence: list[dict[str, Any]] = field(default_factory=list)  # sample offending rows/reasons
    detail: str = ""                # short human-readable note


@dataclass
class CheckOutcome:
    """A CheckResult combined with the severity the profile assigned to it."""

    result: CheckResult
    severity: Severity
    outcome: Outcome

    def to_row(self) -> dict[str, Any]:
        return {
            "check_name": self.result.name,
            "kind": self.result.kind,
            "severity": self.severity.value,
            "outcome": self.outcome.value,
            "failed_count": self.result.failed_count,
            "evidence": self.result.evidence,
            "detail": self.result.detail,
        }


@dataclass
class RunResult:
    """The full result of running one profile over one dataset."""

    dataset: str
    country_code: str
    row_count: int
    checks: list[CheckOutcome]

    @property
    def overall(self) -> Outcome:
        return worst([c.outcome for c in self.checks])

    @property
    def promoted(self) -> bool:
        """Promotion is allowed unless something BLOCKs. WARN still promotes."""
        return self.overall is not Outcome.BLOCK

    def to_summary(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "country_code": self.country_code,
            "row_count": self.row_count,
            "overall_outcome": self.overall.value,
            "promoted": self.promoted,
            "checks": [c.to_row() for c in self.checks],
        }
