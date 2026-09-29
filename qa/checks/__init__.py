"""Check registry — re-exports every check class for convenient import.

    from qa.checks import RequiredFields, GeometryValid, ...
"""

from __future__ import annotations

from .python_checks import (
    CountryScope,
    OptionalPresent,
    RequiredFields,
    SourceDatePresent,
)
from .sql_checks import (
    DuplicateRows,
    GeometrySrid,
    GeometryType,
    GeometryValid,
    KeyUniqueness,
)

__all__ = [
    "RequiredFields",
    "OptionalPresent",
    "CountryScope",
    "SourceDatePresent",
    "KeyUniqueness",
    "DuplicateRows",
    "GeometryValid",
    "GeometryType",
    "GeometrySrid",
]
