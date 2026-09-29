"""Pure-logic tests for the outcome model — no database required.

These lock down the highest-risk correctness rule in the whole framework: how a
check failure + a severity binding produce an outcome, and how outcomes aggregate.
"""

from __future__ import annotations

from qa.contracts import (
    CheckOutcome,
    CheckResult,
    Outcome,
    RunResult,
    Severity,
    worst,
)
from qa.engine import _outcome_for


def test_worst_aggregation_rules():
    assert worst([]) is Outcome.PASS
    assert worst([Outcome.PASS, Outcome.PASS]) is Outcome.PASS
    assert worst([Outcome.PASS, Outcome.WARN]) is Outcome.WARN
    assert worst([Outcome.WARN, Outcome.BLOCK]) is Outcome.BLOCK
    assert worst([Outcome.BLOCK, Outcome.PASS, Outcome.WARN]) is Outcome.BLOCK


def test_outcome_for_severity_binding():
    # Same "failed" state maps to different outcomes depending on severity.
    assert _outcome_for(ok=True, severity=Severity.BLOCK) is Outcome.PASS
    assert _outcome_for(ok=False, severity=Severity.BLOCK) is Outcome.BLOCK
    assert _outcome_for(ok=False, severity=Severity.WARN) is Outcome.WARN


def _co(name, severity, outcome):
    return CheckOutcome(
        result=CheckResult(name=name, kind="python", ok=(outcome is Outcome.PASS), failed_count=1),
        severity=severity,
        outcome=outcome,
    )


def test_warn_only_run_promotes():
    rr = RunResult("peatland", "DE", 3, [_co("soil", Severity.WARN, Outcome.WARN)])
    assert rr.overall is Outcome.WARN
    assert rr.promoted is True


def test_any_block_holds_promotion():
    rr = RunResult(
        "parcels",
        "DE",
        5,
        [_co("soil", Severity.WARN, Outcome.WARN), _co("geom", Severity.BLOCK, Outcome.BLOCK)],
    )
    assert rr.overall is Outcome.BLOCK
    assert rr.promoted is False
