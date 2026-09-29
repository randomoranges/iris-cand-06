"""The four acceptance criteria from the assignment, as executable tests.

  AC1: Blocking and warning conditions are distinguishable.
  AC2: A missing optional soil attribute warns but does not block.
  AC3: Malformed parcel geometry blocks promotion.
  AC4: Duplicate keys block or quarantine deterministically.
"""

from __future__ import annotations

from qa.contracts import Outcome


def _check(result, name):
    return next(c for c in result.checks if c.result.name == name)


def test_ac1_block_and_warn_distinguishable(run):
    parcels = run("parcels")
    peatland = run("peatland")
    # The two datasets land on different overall verdicts...
    assert parcels.overall is Outcome.BLOCK
    assert peatland.overall is Outcome.WARN
    # ...and both severities are observable at the check level.
    seen = {c.outcome for c in parcels.checks} | {c.outcome for c in peatland.checks}
    assert Outcome.BLOCK in seen
    assert Outcome.WARN in seen


def test_ac2_missing_soil_warns_not_blocks(run):
    result = run("peatland")
    soil = _check(result, "optional_soil_attribute")
    assert soil.outcome is Outcome.WARN
    assert soil.result.failed_count >= 1          # the missing-soil row was found
    assert result.promoted is True                # warn does not hold promotion


def test_ac3_malformed_parcel_geometry_blocks(run):
    result = run("parcels")
    geom = _check(result, "geometry_valid")
    assert geom.outcome is Outcome.BLOCK
    assert geom.result.failed_count >= 1          # the bowtie polygon was caught
    assert result.promoted is False               # block holds promotion


def test_ac4_duplicate_keys_block_deterministically(run):
    first = run("parcels")
    second = run("parcels")
    k1 = _check(first, "key_uniqueness")
    k2 = _check(second, "key_uniqueness")
    assert k1.outcome is Outcome.BLOCK
    assert k1.result.failed_count >= 1
    # Deterministic: identical evidence across independent runs (ORDER BY key).
    assert k1.result.evidence == k2.result.evidence
