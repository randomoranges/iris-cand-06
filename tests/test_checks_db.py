"""Full per-check expectation matrix against the fixture set.

Every check on every dataset has a known, deterministic outcome and failure count
given the committed fixtures. This table pins all of them down, so any future change
that breaks a check is caught immediately.
"""

from __future__ import annotations

import pytest

from qa.contracts import Outcome

# (dataset, check_name, expected_failed_count, expected_outcome)
EXPECTED_CHECKS = [
    # --- parcels: strict, several blocks ---
    ("parcels", "required_fields", 2, Outcome.BLOCK),
    ("parcels", "country_scope", 2, Outcome.BLOCK),
    ("parcels", "key_uniqueness", 2, Outcome.BLOCK),
    ("parcels", "duplicate_rows", 1, Outcome.BLOCK),
    ("parcels", "geometry_valid", 2, Outcome.BLOCK),
    ("parcels", "geometry_type", 0, Outcome.PASS),
    ("parcels", "geometry_srid", 2, Outcome.BLOCK),
    ("parcels", "source_date", 1, Outcome.WARN),
    # --- substations: point dataset ---
    ("substations", "required_fields", 2, Outcome.BLOCK),
    ("substations", "country_scope", 2, Outcome.BLOCK),
    ("substations", "key_uniqueness", 1, Outcome.BLOCK),
    ("substations", "duplicate_rows", 0, Outcome.PASS),
    ("substations", "geometry_valid", 0, Outcome.PASS),
    ("substations", "geometry_type", 1, Outcome.BLOCK),
    ("substations", "geometry_srid", 1, Outcome.BLOCK),
    ("substations", "source_date", 1, Outcome.WARN),
    # --- peatland: WARN-only (nothing blocks) ---
    ("peatland", "required_fields", 0, Outcome.PASS),
    ("peatland", "country_scope", 0, Outcome.PASS),
    ("peatland", "key_uniqueness", 0, Outcome.PASS),
    ("peatland", "duplicate_rows", 0, Outcome.PASS),
    ("peatland", "geometry_valid", 0, Outcome.PASS),
    ("peatland", "geometry_type", 0, Outcome.PASS),
    ("peatland", "geometry_srid", 0, Outcome.PASS),
    ("peatland", "optional_soil_attribute", 2, Outcome.WARN),
    ("peatland", "source_date", 2, Outcome.WARN),
    # --- screening: fully clean (happy path) ---
    ("screening", "required_fields", 0, Outcome.PASS),
    ("screening", "country_scope", 0, Outcome.PASS),
    ("screening", "key_uniqueness", 0, Outcome.PASS),
    ("screening", "duplicate_rows", 0, Outcome.PASS),
    ("screening", "geometry_valid", 0, Outcome.PASS),
    ("screening", "geometry_type", 0, Outcome.PASS),
    ("screening", "geometry_srid", 0, Outcome.PASS),
    ("screening", "eco_points_present", 0, Outcome.PASS),
    ("screening", "source_date", 0, Outcome.PASS),
]

# (dataset, overall_outcome, promoted)
EXPECTED_OVERALL = [
    ("parcels", Outcome.BLOCK, False),
    ("substations", Outcome.BLOCK, False),
    ("peatland", Outcome.WARN, True),
    ("screening", Outcome.PASS, True),
]


def _check(result, name):
    return next(c for c in result.checks if c.result.name == name)


@pytest.mark.parametrize(
    "dataset,check_name,count,outcome",
    EXPECTED_CHECKS,
    ids=[f"{d}-{c}" for d, c, _, _ in EXPECTED_CHECKS],
)
def test_check_outcome_and_count(results, dataset, check_name, count, outcome):
    c = _check(results[dataset], check_name)
    assert c.result.failed_count == count
    assert c.outcome is outcome


@pytest.mark.parametrize(
    "dataset,overall,promoted",
    EXPECTED_OVERALL,
    ids=[d for d, _, _ in EXPECTED_OVERALL],
)
def test_dataset_overall(results, dataset, overall, promoted):
    r = results[dataset]
    assert r.overall is overall
    assert r.promoted is promoted


def test_geometry_evidence_captures_reason(results):
    c = _check(results["parcels"], "geometry_valid")
    assert c.result.evidence
    assert "reason" in c.result.evidence[0]


def test_null_geometry_does_not_crash_geometry_checks(results):
    # parcels has a null-geom row; geometry checks must skip it, not error.
    for name in ("geometry_valid", "geometry_type", "geometry_srid"):
        _check(results["parcels"], name)  # simply resolving/reading them is enough
