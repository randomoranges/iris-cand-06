"""What a check needs to know about the dataset it is inspecting."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Target:
    dataset: str
    table: str
    key: str                                   # business key column (uniqueness is checked on this)
    country: str                               # expected country scope, e.g. "DE"
    business_cols: tuple[str, ...]             # columns that define a "row" for full-duplicate detection
    geom_col: str = "geom"
    expected_srid: int = 4326
    geom_types: tuple[str, ...] = field(default_factory=tuple)  # e.g. ("POLYGON", "MULTIPOLYGON")
