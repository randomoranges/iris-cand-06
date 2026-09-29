"""Pluggable QA profiles — one rulebook per dataset type.

A profile = a Target (what the dataset is) + an ordered list of (check, severity)
pairs. The SEVERITY is assigned here, not inside the check. That is the whole
extensibility story:

  * add a new dataset  -> add a Profile to PROFILES
  * add a new rule     -> add a Check class, reference it in the profiles that need it
  * change how strict a dataset is -> flip a Severity in one line, no check code touched

Nothing else in the framework changes.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import checks as C
from .contracts import Severity
from .target import Target


@dataclass(frozen=True)
class CheckSpec:
    check: object            # a Check instance
    severity: Severity       # what a FAILURE of this check escalates to, for THIS dataset


@dataclass(frozen=True)
class Profile:
    target: Target
    specs: list[CheckSpec]


# --- Parcels: land plots. Strict — geometry and identity must be correct. ---
PARCELS = Profile(
    target=Target(
        dataset="parcels",
        table="parcels",
        key="parcel_id",
        country="DE",
        business_cols=("parcel_id", "country_code", "region_code", "source_date", "geom"),
        geom_types=("POLYGON", "MULTIPOLYGON"),
    ),
    specs=[
        CheckSpec(C.RequiredFields(["parcel_id", "country_code", "geom"]), Severity.BLOCK),
        CheckSpec(C.CountryScope(), Severity.BLOCK),
        CheckSpec(C.KeyUniqueness(), Severity.BLOCK),
        CheckSpec(C.DuplicateRows(), Severity.BLOCK),
        CheckSpec(C.GeometryValid(), Severity.BLOCK),
        CheckSpec(C.GeometryType(), Severity.BLOCK),
        CheckSpec(C.GeometrySrid(), Severity.BLOCK),
        CheckSpec(C.SourceDatePresent(), Severity.WARN),   # freshness: warn, don't block
    ],
)

# --- Substations: point infrastructure. ---
SUBSTATIONS = Profile(
    target=Target(
        dataset="substations",
        table="substations",
        key="substation_id",
        country="DE",
        business_cols=("substation_id", "country_code", "region_code", "geom"),
        geom_types=("POINT",),
    ),
    specs=[
        CheckSpec(C.RequiredFields(["substation_id", "country_code", "geom"]), Severity.BLOCK),
        CheckSpec(C.CountryScope(), Severity.BLOCK),
        CheckSpec(C.KeyUniqueness(), Severity.BLOCK),
        CheckSpec(C.DuplicateRows(), Severity.BLOCK),
        CheckSpec(C.GeometryValid(), Severity.BLOCK),
        CheckSpec(C.GeometryType(), Severity.BLOCK),
        CheckSpec(C.GeometrySrid(), Severity.BLOCK),
        CheckSpec(C.SourceDatePresent(), Severity.WARN),
    ],
)

# --- Peatland: soil polygons with OPTIONAL enrichment. Missing soil WARNS. ---
PEATLAND = Profile(
    target=Target(
        dataset="peatland",
        table="peatland",
        key="peatland_id",
        country="DE",
        business_cols=("peatland_id", "country_code", "region_code", "geom"),
        geom_types=("POLYGON", "MULTIPOLYGON"),
    ),
    specs=[
        CheckSpec(C.RequiredFields(["peatland_id", "country_code", "geom"]), Severity.BLOCK),
        CheckSpec(C.CountryScope(), Severity.BLOCK),
        CheckSpec(C.KeyUniqueness(), Severity.BLOCK),
        CheckSpec(C.DuplicateRows(), Severity.BLOCK),
        CheckSpec(C.GeometryValid(), Severity.BLOCK),
        CheckSpec(C.GeometryType(), Severity.BLOCK),
        CheckSpec(C.GeometrySrid(), Severity.BLOCK),
        # The key semantic difference: this same "field present" idea is a WARN here.
        CheckSpec(C.OptionalPresent("peat_depth_m", name="optional_soil_attribute"), Severity.WARN),
        CheckSpec(C.SourceDatePresent(), Severity.WARN),
    ],
)

# --- Screening: commercial suitability polygons. ---
SCREENING = Profile(
    target=Target(
        dataset="screening",
        table="screening",
        key="screening_id",
        country="DE",
        business_cols=("screening_id", "country_code", "region_code", "geom"),
        geom_types=("POLYGON", "MULTIPOLYGON"),
    ),
    specs=[
        CheckSpec(C.RequiredFields(["screening_id", "country_code", "geom"]), Severity.BLOCK),
        CheckSpec(C.CountryScope(), Severity.BLOCK),
        CheckSpec(C.KeyUniqueness(), Severity.BLOCK),
        CheckSpec(C.DuplicateRows(), Severity.BLOCK),
        CheckSpec(C.GeometryValid(), Severity.BLOCK),
        CheckSpec(C.GeometryType(), Severity.BLOCK),
        CheckSpec(C.GeometrySrid(), Severity.BLOCK),
        CheckSpec(C.RequiredFields(["eco_points_per_m2"], name="eco_points_present"), Severity.WARN),
        CheckSpec(C.SourceDatePresent(), Severity.WARN),
    ],
)


PROFILES: dict[str, Profile] = {
    p.target.dataset: p for p in (PARCELS, SUBSTATIONS, PEATLAND, SCREENING)
}


def get_profile(dataset: str) -> Profile:
    try:
        return PROFILES[dataset]
    except KeyError:
        raise KeyError(
            f"no QA profile for '{dataset}'. Known: {', '.join(sorted(PROFILES))}"
        ) from None
