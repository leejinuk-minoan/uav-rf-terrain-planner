"""Pure Python synthetic candidate display preview integration smoke.

This module connects the existing synthetic scenario, map output, candidate display,
and preview scaffolds using deterministic placeholder MGRS strings. It does not read
terrain files, convert coordinates, write files, implement a CLI, render UI content,
or change scoring behavior.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .candidate_display_outputs import build_candidate_display_records
from .candidate_display_preview import (
    PreviewDictionary,
    build_candidate_display_preview,
    build_candidate_display_preview_dict,
    format_candidate_display_preview,
)
from .coordinate_io_policy import (
    EXTERNAL_COORDINATE_FORMAT,
    INTERNAL_COORDINATE_FIELD_NAMES,
    require_mgrs_external_coordinate_field,
)
from .map_outputs import (
    CandidateCellMapFeature,
    build_candidate_cell_map_features,
    build_map_output_package,
)
from .scenario_outputs import build_synthetic_end_to_end_scenario

_USER_COORDINATE_FIELD = "candidate_cell_mgrs"
_REQUIRED_METADATA_KEYS = frozenset(
    {
        "cell_id",
        "candidate_cell_mgrs",
        "external_coordinate_format",
        "user_coordinate_field",
        "source_zone",
        "source_sensitive",
        "source_zone_reason",
        "internal_debug_available",
    }
)


class SyntheticCandidatePreviewSmokeError(ValueError):
    """Raised when synthetic candidate preview smoke inputs are invalid."""


@dataclass(frozen=True)
class SyntheticCandidatePreviewSmokeResult:
    """End-to-end synthetic candidate preview smoke result."""

    scenario_name: str
    candidate_feature_count: int
    display_record_count: int
    preview_record_count: int
    source_sensitive_count: int
    external_coordinate_format: str
    user_coordinate_field: str
    preview_dict: PreviewDictionary
    preview_text: str
    reason: str

    def __post_init__(self) -> None:
        require_mgrs_external_coordinate_field(_USER_COORDINATE_FIELD)
        _validate_non_empty_string("scenario_name", self.scenario_name)
        _validate_positive_int("candidate_feature_count", self.candidate_feature_count)
        _validate_positive_int("display_record_count", self.display_record_count)
        _validate_positive_int("preview_record_count", self.preview_record_count)
        _validate_non_negative_int(
            "source_sensitive_count",
            self.source_sensitive_count,
        )
        if self.display_record_count != self.preview_record_count:
            raise SyntheticCandidatePreviewSmokeError(
                "display_record_count must match preview_record_count."
            )
        if self.candidate_feature_count != self.display_record_count:
            raise SyntheticCandidatePreviewSmokeError(
                "candidate_feature_count must match display_record_count."
            )
        if self.source_sensitive_count > self.preview_record_count:
            raise SyntheticCandidatePreviewSmokeError(
                "source_sensitive_count must not exceed preview_record_count."
            )
        if self.external_coordinate_format != EXTERNAL_COORDINATE_FORMAT:
            raise SyntheticCandidatePreviewSmokeError(
                "external_coordinate_format must match the project MGRS policy."
            )
        if self.user_coordinate_field != _USER_COORDINATE_FIELD:
            raise SyntheticCandidatePreviewSmokeError(
                "user_coordinate_field must be candidate_cell_mgrs."
            )
        _validate_preview_dictionary(self.preview_dict)
        _validate_non_empty_string("preview_text", self.preview_text)
        _validate_non_empty_string("reason", self.reason)


def build_synthetic_candidate_mgrs_by_candidate_id(
    candidate_ids: Sequence[str],
) -> dict[str, str]:
    """Return deterministic placeholder MGRS strings for synthetic candidate ids."""

    if isinstance(candidate_ids, (str, bytes)) or not candidate_ids:
        raise SyntheticCandidatePreviewSmokeError(
            "candidate_ids must be a non-empty sequence of strings."
        )
    result: dict[str, str] = {}
    for index, candidate_id in enumerate(candidate_ids):
        _validate_non_empty_string("candidate_id", candidate_id)
        if candidate_id in result:
            raise SyntheticCandidatePreviewSmokeError(
                f"duplicate candidate_id: {candidate_id}."
            )
        result[candidate_id] = f"52S CG {index * 90:05d} 00000"
    return result


def build_synthetic_candidate_source_zone_metadata_by_candidate_id(
    candidate_features: Sequence[CandidateCellMapFeature],
    candidate_mgrs_by_candidate_id: Mapping[str, str],
) -> dict[str, dict[str, str | bool]]:
    """Build MGRS source-zone metadata for synthetic candidate map features."""

    resolved_features = _ensure_candidate_features(candidate_features)
    if not isinstance(candidate_mgrs_by_candidate_id, Mapping):
        raise SyntheticCandidatePreviewSmokeError(
            "candidate_mgrs_by_candidate_id must be a mapping."
        )
    require_mgrs_external_coordinate_field(_USER_COORDINATE_FIELD)

    metadata_by_candidate_id: dict[str, dict[str, str | bool]] = {}
    for feature in resolved_features:
        if feature.candidate_id not in candidate_mgrs_by_candidate_id:
            raise SyntheticCandidatePreviewSmokeError(
                "missing placeholder MGRS for "
                f"candidate_id={feature.candidate_id}."
            )
        candidate_cell_mgrs = candidate_mgrs_by_candidate_id[feature.candidate_id]
        _validate_non_empty_string("candidate_cell_mgrs", candidate_cell_mgrs)
        metadata = {
            "cell_id": feature.candidate_id,
            "candidate_cell_mgrs": candidate_cell_mgrs,
            "external_coordinate_format": EXTERNAL_COORDINATE_FORMAT,
            "user_coordinate_field": _USER_COORDINATE_FIELD,
            "source_zone": feature.source_zone.value,
            "source_sensitive": feature.source_sensitive,
            "source_zone_reason": feature.source_zone_reason,
            "internal_debug_available": False,
        }
        _validate_metadata(metadata)
        metadata_by_candidate_id[feature.candidate_id] = metadata
    return metadata_by_candidate_id


def build_synthetic_candidate_preview_smoke(
    *,
    max_preview_records: int | None = None,
) -> SyntheticCandidatePreviewSmokeResult:
    """Run the in-memory synthetic scenario-to-preview integration smoke."""

    scenario = build_synthetic_end_to_end_scenario()
    initial_candidate_features = build_candidate_cell_map_features(scenario.candidates)
    candidate_mgrs_by_candidate_id = build_synthetic_candidate_mgrs_by_candidate_id(
        tuple(feature.candidate_id for feature in initial_candidate_features)
    )
    metadata_by_candidate_id = (
        build_synthetic_candidate_source_zone_metadata_by_candidate_id(
            initial_candidate_features,
            candidate_mgrs_by_candidate_id,
        )
    )
    package = build_map_output_package(
        scenario,
        candidate_source_zone_metadata_by_cell_id=metadata_by_candidate_id,
    )
    display_bundle = build_candidate_display_records(package.candidate_features)
    preview = build_candidate_display_preview(display_bundle)
    preview_dict = build_candidate_display_preview_dict(display_bundle)
    preview_text = format_candidate_display_preview(
        display_bundle,
        max_records=max_preview_records,
    )

    return SyntheticCandidatePreviewSmokeResult(
        scenario_name=scenario.scenario_name,
        candidate_feature_count=len(package.candidate_features),
        display_record_count=len(display_bundle.records),
        preview_record_count=preview.record_count,
        source_sensitive_count=preview.source_sensitive_count,
        external_coordinate_format=preview.external_coordinate_format,
        user_coordinate_field=preview.user_coordinate_field,
        preview_dict=preview_dict,
        preview_text=preview_text,
        reason=(
            "Synthetic scenario connected to MGRS-based candidate display previews "
            "using placeholder metadata only."
        ),
    )


def summarize_synthetic_candidate_preview_smoke(
    result: SyntheticCandidatePreviewSmokeResult,
) -> dict[str, int | str]:
    """Return summary fields for the synthetic candidate preview smoke."""

    if not isinstance(result, SyntheticCandidatePreviewSmokeResult):
        raise SyntheticCandidatePreviewSmokeError(
            "result must be a SyntheticCandidatePreviewSmokeResult value."
        )
    return {
        "scenario_name": result.scenario_name,
        "candidate_feature_count": result.candidate_feature_count,
        "display_record_count": result.display_record_count,
        "preview_record_count": result.preview_record_count,
        "source_sensitive_count": result.source_sensitive_count,
        "external_coordinate_format": result.external_coordinate_format,
        "user_coordinate_field": result.user_coordinate_field,
        "synthetic_candidate_preview_reason": result.reason,
    }


def _ensure_candidate_features(
    candidate_features: Sequence[CandidateCellMapFeature],
) -> tuple[CandidateCellMapFeature, ...]:
    if isinstance(candidate_features, (str, bytes)) or not candidate_features:
        raise SyntheticCandidatePreviewSmokeError(
            "candidate_features must be a non-empty sequence."
        )
    resolved = tuple(candidate_features)
    for feature in resolved:
        if not isinstance(feature, CandidateCellMapFeature):
            raise SyntheticCandidatePreviewSmokeError(
                "all candidate_features must be CandidateCellMapFeature values."
            )
    return resolved


def _validate_metadata(metadata: Mapping[str, str | bool]) -> None:
    missing_keys = _REQUIRED_METADATA_KEYS.difference(metadata.keys())
    if missing_keys:
        raise SyntheticCandidatePreviewSmokeError(
            "synthetic candidate metadata is missing required keys: "
            + ", ".join(sorted(missing_keys))
            + "."
        )
    blocked_keys = INTERNAL_COORDINATE_FIELD_NAMES.intersection(metadata.keys())
    if blocked_keys:
        raise SyntheticCandidatePreviewSmokeError(
            "synthetic candidate metadata must not expose internal coordinates: "
            + ", ".join(sorted(blocked_keys))
            + "."
        )


def _validate_preview_dictionary(preview_dict: PreviewDictionary) -> None:
    if not isinstance(preview_dict, Mapping) or not preview_dict:
        raise SyntheticCandidatePreviewSmokeError(
            "preview_dict must be a non-empty mapping."
        )
    if preview_dict.get("external_coordinate_format") != EXTERNAL_COORDINATE_FORMAT:
        raise SyntheticCandidatePreviewSmokeError(
            "preview_dict external coordinate format must be MGRS."
        )
    if preview_dict.get("user_coordinate_field") != _USER_COORDINATE_FIELD:
        raise SyntheticCandidatePreviewSmokeError(
            "preview_dict user coordinate field must be candidate_cell_mgrs."
        )
    records = preview_dict.get("records")
    if not isinstance(records, list) or not records:
        raise SyntheticCandidatePreviewSmokeError(
            "preview_dict records must be a non-empty list."
        )
    for record in records:
        if not isinstance(record, Mapping):
            raise SyntheticCandidatePreviewSmokeError(
                "preview_dict records must contain mappings."
            )
        blocked_keys = INTERNAL_COORDINATE_FIELD_NAMES.intersection(record.keys())
        if blocked_keys:
            raise SyntheticCandidatePreviewSmokeError(
                "preview_dict records must not expose internal coordinates."
            )


def _validate_non_empty_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SyntheticCandidatePreviewSmokeError(
            f"{field_name} must be a non-empty string."
        )


def _validate_positive_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SyntheticCandidatePreviewSmokeError(
            f"{field_name} must be an integer."
        )
    if value <= 0:
        raise SyntheticCandidatePreviewSmokeError(
            f"{field_name} must be positive."
        )


def _validate_non_negative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SyntheticCandidatePreviewSmokeError(
            f"{field_name} must be an integer."
        )
    if value < 0:
        raise SyntheticCandidatePreviewSmokeError(
            f"{field_name} must be non-negative."
        )
