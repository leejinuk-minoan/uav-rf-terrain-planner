"""Pure Python candidate display preview scaffold.

This module converts ``CandidateDisplayBundle`` values into JSON-ready dictionaries
and plain-text preview strings. It does not write files, implement a CLI, render UI
content, convert coordinates, read raster data, or change scoring behavior.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .candidate_display_outputs import (
    CandidateDisplayBundle,
    CandidateDisplayRecord,
    summarize_candidate_display_records,
)
from .coordinate_io_policy import (
    EXTERNAL_COORDINATE_FORMAT,
    INTERNAL_COORDINATE_FIELD_NAMES,
    require_mgrs_external_coordinate_field,
)
from .fresnel_diagnostics import (
    DIAGNOSTIC_FIELD_NAMES,
    CandidateFresnelDiagnosticsError,
    validate_flat_fresnel_diagnostics,
)

_USER_COORDINATE_FIELD = "candidate_cell_mgrs"
_PREVIEW_TITLE = "Candidate display preview"

PreviewRecord = dict[str, str | int | float | bool | None]
PreviewSummary = dict[str, int | str]
PreviewDictionary = dict[
    str,
    str | int | list[PreviewRecord] | PreviewSummary,
]


class CandidateDisplayPreviewError(ValueError):
    """Raised when candidate display preview inputs are invalid."""


@dataclass(frozen=True)
class CandidateDisplayPreview:
    """JSON-ready candidate preview data without internal coordinate fields."""

    title: str
    external_coordinate_format: str
    user_coordinate_field: str
    record_count: int
    source_sensitive_count: int
    records: tuple[PreviewRecord, ...]
    summary: PreviewSummary
    reason: str

    def __post_init__(self) -> None:
        require_mgrs_external_coordinate_field(_USER_COORDINATE_FIELD)
        _validate_non_empty_string("title", self.title)
        if self.external_coordinate_format != EXTERNAL_COORDINATE_FORMAT:
            raise CandidateDisplayPreviewError(
                "external_coordinate_format must match the project MGRS policy."
            )
        if self.user_coordinate_field != _USER_COORDINATE_FIELD:
            raise CandidateDisplayPreviewError(
                "user_coordinate_field must be candidate_cell_mgrs."
            )
        _validate_positive_int("record_count", self.record_count)
        _validate_non_negative_int(
            "source_sensitive_count",
            self.source_sensitive_count,
        )
        _ensure_preview_records(self.records)
        if self.record_count != len(self.records):
            raise CandidateDisplayPreviewError(
                "record_count must match preview records."
            )
        actual_sensitive_count = sum(
            1 for record in self.records if record["source_sensitive"] is True
        )
        if self.source_sensitive_count != actual_sensitive_count:
            raise CandidateDisplayPreviewError(
                "source_sensitive_count must match preview records."
            )
        _validate_summary(self.summary)
        _validate_non_empty_string("reason", self.reason)


def build_candidate_display_preview(
    display_bundle: CandidateDisplayBundle,
) -> CandidateDisplayPreview:
    """Build a preview object from candidate display records."""

    resolved_bundle = _require_display_bundle(display_bundle)
    records = tuple(dict(record.to_display_dict()) for record in resolved_bundle.records)
    summary = dict(summarize_candidate_display_records(resolved_bundle))
    return CandidateDisplayPreview(
        title=_PREVIEW_TITLE,
        external_coordinate_format=EXTERNAL_COORDINATE_FORMAT,
        user_coordinate_field=_USER_COORDINATE_FIELD,
        record_count=len(records),
        source_sensitive_count=resolved_bundle.source_sensitive_count,
        records=records,
        summary=summary,
        reason=f"Candidate display preview prepared from: {resolved_bundle.reason}",
    )


def build_candidate_display_preview_dict(
    display_bundle: CandidateDisplayBundle,
) -> PreviewDictionary:
    """Return a JSON-ready preview dictionary containing primitives, lists, and dicts."""

    preview = build_candidate_display_preview(display_bundle)
    return {
        "title": preview.title,
        "external_coordinate_format": preview.external_coordinate_format,
        "user_coordinate_field": preview.user_coordinate_field,
        "record_count": preview.record_count,
        "source_sensitive_count": preview.source_sensitive_count,
        "records": [dict(record) for record in preview.records],
        "summary": dict(preview.summary),
        "reason": preview.reason,
    }


def format_candidate_display_preview(
    display_bundle: CandidateDisplayBundle,
    *,
    max_records: int | None = None,
) -> str:
    """Return a human-readable preview string without writing a file."""

    resolved_bundle = _require_display_bundle(display_bundle)
    resolved_limit = _validate_max_records(max_records)
    records = resolved_bundle.records
    visible_records = records if resolved_limit is None else records[:resolved_limit]

    lines = [
        _PREVIEW_TITLE,
        f"External coordinate format: {EXTERNAL_COORDINATE_FORMAT}",
        f"User coordinate field: {_USER_COORDINATE_FIELD}",
        f"Records: {len(records)}",
        f"Source-sensitive records: {resolved_bundle.source_sensitive_count}",
    ]
    lines.extend(_format_record_line(record) for record in visible_records)

    omitted_count = len(records) - len(visible_records)
    if omitted_count > 0:
        lines.append(f"... {omitted_count} additional record(s) omitted.")
    return "\n".join(lines)


def _format_record_line(record: CandidateDisplayRecord) -> str:
    line = (
        f"- {record.display_label} | score={record.overall_score} | "
        f"source_zone={record.source_zone}"
    )
    diagnostics = record.fresnel_diagnostics
    if diagnostics is None:
        return line
    worst = (
        f"{diagnostics.worst_obstacle_score:.1f}"
        if diagnostics.worst_obstacle_score is not None
        else "unavailable"
    )
    loss = (
        f"{diagnostics.dominant_obstacle_diffraction_loss_db:.1f} dB"
        if diagnostics.dominant_obstacle_diffraction_loss_db is not None
        else "unavailable"
    )
    return (
        f"{line} | fresnel_avg={diagnostics.average_fresnel_score:.1f} | "
        f"fresnel_worst={worst} | diffraction_loss={loss}"
    )


def _require_display_bundle(display_bundle: CandidateDisplayBundle) -> CandidateDisplayBundle:
    if not isinstance(display_bundle, CandidateDisplayBundle):
        raise CandidateDisplayPreviewError(
            "display_bundle must be a CandidateDisplayBundle value."
        )
    if not display_bundle.records:
        raise CandidateDisplayPreviewError("display_bundle records must not be empty.")
    return display_bundle


def _ensure_preview_records(records: Sequence[PreviewRecord]) -> tuple[PreviewRecord, ...]:
    if not records:
        raise CandidateDisplayPreviewError("records must not be empty.")
    resolved = tuple(records)
    for record in resolved:
        _validate_preview_record(record)
    return resolved


def _validate_preview_record(
    record: Mapping[str, str | int | float | bool | None],
) -> None:
    if not isinstance(record, Mapping):
        raise CandidateDisplayPreviewError("preview records must be mappings.")
    blocked_keys = INTERNAL_COORDINATE_FIELD_NAMES.intersection(record.keys())
    if blocked_keys:
        raise CandidateDisplayPreviewError(
            "preview records must not expose internal coordinate keys: "
            + ", ".join(sorted(blocked_keys))
            + "."
        )
    candidate_cell_mgrs = record.get("candidate_cell_mgrs")
    if not isinstance(candidate_cell_mgrs, str) or not candidate_cell_mgrs.strip():
        raise CandidateDisplayPreviewError(
            "preview records must include a non-empty candidate_cell_mgrs value."
        )
    if record.get("external_coordinate_format") != EXTERNAL_COORDINATE_FORMAT:
        raise CandidateDisplayPreviewError(
            "preview record external_coordinate_format must be MGRS."
        )
    if record.get("user_coordinate_field") != _USER_COORDINATE_FIELD:
        raise CandidateDisplayPreviewError(
            "preview record user_coordinate_field must be candidate_cell_mgrs."
        )
    if not isinstance(record.get("source_sensitive"), bool):
        raise CandidateDisplayPreviewError(
            "preview record source_sensitive must be a bool."
        )
    try:
        diagnostic_state = validate_flat_fresnel_diagnostics(record)
    except CandidateFresnelDiagnosticsError as exc:
        raise CandidateDisplayPreviewError(str(exc)) from exc
    for key, value in record.items():
        if not isinstance(key, str):
            raise CandidateDisplayPreviewError("preview record keys must be strings.")
        if isinstance(value, (str, float, bool)):
            continue
        if (
            isinstance(value, int)
            and not isinstance(value, bool)
            and key in DIAGNOSTIC_FIELD_NAMES
        ):
            continue
        if value is None and diagnostic_state == "no_eligible" and key in DIAGNOSTIC_FIELD_NAMES:
            continue
        raise CandidateDisplayPreviewError(
            "preview record values must be JSON-ready primitive values."
        )


def _validate_summary(summary: Mapping[str, int | str]) -> None:
    if not isinstance(summary, Mapping) or not summary:
        raise CandidateDisplayPreviewError("summary must be a non-empty mapping.")
    if summary.get("candidate_display_external_coordinate_format") != (
        EXTERNAL_COORDINATE_FORMAT
    ):
        raise CandidateDisplayPreviewError(
            "summary external coordinate format must be MGRS."
        )
    if summary.get("candidate_display_user_coordinate_field") != (
        _USER_COORDINATE_FIELD
    ):
        raise CandidateDisplayPreviewError(
            "summary user coordinate field must be candidate_cell_mgrs."
        )


def _validate_max_records(max_records: int | None) -> int | None:
    if max_records is None:
        return None
    if isinstance(max_records, bool) or not isinstance(max_records, int):
        raise CandidateDisplayPreviewError("max_records must be an integer or None.")
    if max_records <= 0:
        raise CandidateDisplayPreviewError("max_records must be positive.")
    return max_records


def _validate_non_empty_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CandidateDisplayPreviewError(
            f"{field_name} must be a non-empty string."
        )


def _validate_positive_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CandidateDisplayPreviewError(f"{field_name} must be an integer.")
    if value <= 0:
        raise CandidateDisplayPreviewError(f"{field_name} must be positive.")


def _validate_non_negative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CandidateDisplayPreviewError(f"{field_name} must be an integer.")
    if value < 0:
        raise CandidateDisplayPreviewError(f"{field_name} must be non-negative.")
