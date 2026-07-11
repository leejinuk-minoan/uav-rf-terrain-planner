"""Pure Python candidate display output formatter scaffold.

This module converts ``CandidateCellMapFeature`` records with attached MGRS-based
candidate metadata into rendering-independent display records for future candidate
tables, map popups, and UI cards. It does not render tables or maps, convert MGRS,
read raster files, or change scoring behavior.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite

from .coordinate_io_policy import (
    EXTERNAL_COORDINATE_FORMAT,
    INTERNAL_COORDINATE_FIELD_NAMES,
    require_mgrs_external_coordinate_field,
)
from .map_outputs import CandidateCellMapFeature
from .schemas import ColorClass

_USER_COORDINATE_FIELD = "candidate_cell_mgrs"
_REQUIRED_METADATA_KEYS = frozenset(
    {
        "candidate_cell_mgrs",
        "external_coordinate_format",
        "user_coordinate_field",
        "source_zone",
        "source_sensitive",
        "source_zone_reason",
    }
)


class CandidateDisplayOutputError(ValueError):
    """Raised when candidate display output inputs are invalid."""


@dataclass(frozen=True)
class CandidateDisplayRecord:
    """User-facing candidate display record with an MGRS coordinate boundary."""

    candidate_id: str
    candidate_cell_mgrs: str
    external_coordinate_format: str
    user_coordinate_field: str
    color_class: ColorClass
    color_name: str
    overall_score: float
    shielding_stability_score: float
    source_zone: str
    source_sensitive: bool
    source_zone_reason: str
    candidate_reason: str
    display_label: str

    def __post_init__(self) -> None:
        require_mgrs_external_coordinate_field(_USER_COORDINATE_FIELD)
        _validate_non_empty_string("candidate_id", self.candidate_id)
        _validate_non_empty_string("candidate_cell_mgrs", self.candidate_cell_mgrs)
        if self.external_coordinate_format != EXTERNAL_COORDINATE_FORMAT:
            raise CandidateDisplayOutputError(
                "external_coordinate_format must match the project MGRS policy."
            )
        if self.user_coordinate_field != _USER_COORDINATE_FIELD:
            raise CandidateDisplayOutputError(
                "user_coordinate_field must be candidate_cell_mgrs."
            )
        if not isinstance(self.color_class, ColorClass):
            raise CandidateDisplayOutputError("color_class must be a ColorClass value.")
        _validate_non_empty_string("color_name", self.color_name)
        _validate_score("overall_score", self.overall_score)
        _validate_score("shielding_stability_score", self.shielding_stability_score)
        _validate_non_empty_string("source_zone", self.source_zone)
        if not isinstance(self.source_sensitive, bool):
            raise CandidateDisplayOutputError("source_sensitive must be a bool.")
        _validate_non_empty_string("source_zone_reason", self.source_zone_reason)
        _validate_non_empty_string("candidate_reason", self.candidate_reason)
        _validate_non_empty_string("display_label", self.display_label)
        expected_label = (
            f"{self.candidate_id} | {self.candidate_cell_mgrs} | "
            f"{self.color_class.value}"
        )
        if self.display_label != expected_label:
            raise CandidateDisplayOutputError(
                "display_label must use candidate_id, candidate_cell_mgrs, and color class."
            )

    def to_display_dict(self) -> dict[str, str | float | bool]:
        """Return primitive user-facing display properties without internal coordinates."""

        return {
            "candidate_id": self.candidate_id,
            "candidate_cell_mgrs": self.candidate_cell_mgrs,
            "external_coordinate_format": self.external_coordinate_format,
            "user_coordinate_field": self.user_coordinate_field,
            "color_class": self.color_class.value,
            "color_name": self.color_name,
            "overall_score": self.overall_score,
            "shielding_stability_score": self.shielding_stability_score,
            "source_zone": self.source_zone,
            "source_sensitive": self.source_sensitive,
            "source_zone_reason": self.source_zone_reason,
            "candidate_reason": self.candidate_reason,
            "display_label": self.display_label,
        }


@dataclass(frozen=True)
class CandidateDisplayBundle:
    """Collection of candidate display records and interpretation summary."""

    records: tuple[CandidateDisplayRecord, ...]
    source_sensitive_count: int
    reason: str

    def __post_init__(self) -> None:
        _ensure_display_records(self.records)
        _validate_non_negative_int("source_sensitive_count", self.source_sensitive_count)
        actual_sensitive_count = sum(
            1 for record in self.records if record.source_sensitive
        )
        if self.source_sensitive_count != actual_sensitive_count:
            raise CandidateDisplayOutputError(
                "source_sensitive_count must match display records."
            )
        _validate_non_empty_string("reason", self.reason)


def build_candidate_display_records(
    candidate_features: Sequence[CandidateCellMapFeature],
) -> CandidateDisplayBundle:
    """Convert candidate map features into user-facing display records."""

    resolved_features = _ensure_candidate_features(candidate_features)
    records: list[CandidateDisplayRecord] = []
    for feature in resolved_features:
        metadata = feature.candidate_source_zone_map_properties
        _validate_feature_metadata(metadata, candidate_id=feature.candidate_id)

        candidate_cell_mgrs = _required_string(metadata, "candidate_cell_mgrs")
        external_coordinate_format = _required_string(
            metadata,
            "external_coordinate_format",
        )
        user_coordinate_field = _required_string(metadata, "user_coordinate_field")
        source_zone = _required_string(metadata, "source_zone")
        source_sensitive = metadata["source_sensitive"]
        if not isinstance(source_sensitive, bool):
            raise CandidateDisplayOutputError("source_sensitive must be a bool.")
        source_zone_reason = _required_string(metadata, "source_zone_reason")

        records.append(
            CandidateDisplayRecord(
                candidate_id=feature.candidate_id,
                candidate_cell_mgrs=candidate_cell_mgrs,
                external_coordinate_format=external_coordinate_format,
                user_coordinate_field=user_coordinate_field,
                color_class=feature.color_class,
                color_name=feature.style.color_name,
                overall_score=feature.overall_score,
                shielding_stability_score=feature.shielding_stability_score,
                source_zone=source_zone,
                source_sensitive=source_sensitive,
                source_zone_reason=source_zone_reason,
                candidate_reason=feature.reason,
                display_label=(
                    f"{feature.candidate_id} | {candidate_cell_mgrs} | "
                    f"{feature.color_class.value}"
                ),
            )
        )

    source_sensitive_count = sum(1 for record in records if record.source_sensitive)
    return CandidateDisplayBundle(
        records=tuple(records),
        source_sensitive_count=source_sensitive_count,
        reason=(
            "Candidate map features converted to MGRS-based display records; "
            f"source-sensitive records={source_sensitive_count}."
        ),
    )


def build_candidate_display_records_by_candidate_id(
    display_bundle: CandidateDisplayBundle,
) -> dict[str, dict[str, str | float | bool]]:
    """Return display dictionaries keyed by candidate identifier."""

    if not isinstance(display_bundle, CandidateDisplayBundle):
        raise CandidateDisplayOutputError(
            "display_bundle must be a CandidateDisplayBundle value."
        )
    records_by_candidate_id: dict[str, dict[str, str | float | bool]] = {}
    for record in display_bundle.records:
        if record.candidate_id in records_by_candidate_id:
            raise CandidateDisplayOutputError(
                f"duplicate candidate_id in display records: {record.candidate_id}."
            )
        records_by_candidate_id[record.candidate_id] = record.to_display_dict()
    return records_by_candidate_id


def summarize_candidate_display_records(
    display_bundle: CandidateDisplayBundle,
) -> dict[str, int | str]:
    """Return counts and coordinate policy fields for candidate display records."""

    if not isinstance(display_bundle, CandidateDisplayBundle):
        raise CandidateDisplayOutputError(
            "display_bundle must be a CandidateDisplayBundle value."
        )
    return {
        "candidate_display_record_count": len(display_bundle.records),
        "candidate_display_external_coordinate_format": EXTERNAL_COORDINATE_FORMAT,
        "candidate_display_user_coordinate_field": _USER_COORDINATE_FIELD,
        "candidate_display_source_sensitive_count": display_bundle.source_sensitive_count,
        "green_candidate_display_count": _count_color(
            display_bundle.records,
            ColorClass.GREEN,
        ),
        "yellow_candidate_display_count": _count_color(
            display_bundle.records,
            ColorClass.YELLOW,
        ),
        "orange_candidate_display_count": _count_color(
            display_bundle.records,
            ColorClass.ORANGE,
        ),
        "red_candidate_display_count": _count_color(
            display_bundle.records,
            ColorClass.RED,
        ),
        "excluded_candidate_display_count": _count_color(
            display_bundle.records,
            ColorClass.EXCLUDED,
        ),
        "candidate_display_reason": display_bundle.reason,
    }


def _validate_feature_metadata(
    metadata: Mapping[str, str | bool],
    *,
    candidate_id: str,
) -> None:
    if not isinstance(metadata, Mapping):
        raise CandidateDisplayOutputError(
            "candidate source-zone map properties must be a mapping."
        )
    if not metadata:
        raise CandidateDisplayOutputError(
            f"candidate display metadata is not attached for candidate_id={candidate_id}."
        )
    missing_keys = _REQUIRED_METADATA_KEYS.difference(metadata.keys())
    if missing_keys:
        raise CandidateDisplayOutputError(
            "candidate display metadata is missing required keys: "
            + ", ".join(sorted(missing_keys))
            + "."
        )
    blocked_keys = INTERNAL_COORDINATE_FIELD_NAMES.intersection(metadata.keys())
    if blocked_keys:
        raise CandidateDisplayOutputError(
            "candidate display metadata must not expose internal coordinate keys: "
            + ", ".join(sorted(blocked_keys))
            + "."
        )
    require_mgrs_external_coordinate_field(_USER_COORDINATE_FIELD)
    if metadata["external_coordinate_format"] != EXTERNAL_COORDINATE_FORMAT:
        raise CandidateDisplayOutputError(
            "external_coordinate_format must match the project MGRS policy."
        )
    if metadata["user_coordinate_field"] != _USER_COORDINATE_FIELD:
        raise CandidateDisplayOutputError(
            "user_coordinate_field must be candidate_cell_mgrs."
        )


def _required_string(metadata: Mapping[str, str | bool], key: str) -> str:
    value = metadata[key]
    if not isinstance(value, str) or not value.strip():
        raise CandidateDisplayOutputError(f"{key} must be a non-empty string.")
    return value


def _ensure_candidate_features(
    candidate_features: Sequence[CandidateCellMapFeature],
) -> tuple[CandidateCellMapFeature, ...]:
    if not candidate_features:
        raise CandidateDisplayOutputError("candidate_features must not be empty.")
    resolved = tuple(candidate_features)
    for feature in resolved:
        if not isinstance(feature, CandidateCellMapFeature):
            raise CandidateDisplayOutputError(
                "all candidate_features must be CandidateCellMapFeature values."
            )
    return resolved


def _ensure_display_records(
    records: Sequence[CandidateDisplayRecord],
) -> tuple[CandidateDisplayRecord, ...]:
    if not records:
        raise CandidateDisplayOutputError("records must not be empty.")
    resolved = tuple(records)
    for record in resolved:
        if not isinstance(record, CandidateDisplayRecord):
            raise CandidateDisplayOutputError(
                "all records must be CandidateDisplayRecord values."
            )
    return resolved


def _count_color(
    records: Sequence[CandidateDisplayRecord],
    color_class: ColorClass,
) -> int:
    return sum(1 for record in records if record.color_class is color_class)


def _validate_non_empty_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CandidateDisplayOutputError(
            f"{field_name} must be a non-empty string."
        )


def _validate_score(field_name: str, value: float) -> None:
    if not isfinite(value) or value < 0.0 or value > 100.0:
        raise CandidateDisplayOutputError(f"{field_name} must be within [0, 100].")


def _validate_non_negative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CandidateDisplayOutputError(f"{field_name} must be an integer.")
    if value < 0:
        raise CandidateDisplayOutputError(f"{field_name} must be non-negative.")
