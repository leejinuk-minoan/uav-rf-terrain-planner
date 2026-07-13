"""Pure formatter for reviewed candidate preview appendix tables."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from numbers import Real

from .coordinate_io_policy import (
    EXTERNAL_COORDINATE_FORMAT,
    INTERNAL_COORDINATE_FIELD_NAMES,
)
from .fresnel_diagnostics import (
    CandidateFresnelDiagnosticsError,
    DIAGNOSTIC_FIELD_ORDER,
    validate_flat_fresnel_diagnostics,
)


class PreviewAppendixTableError(ValueError):
    """Raised when preview input violates the appendix-table contract."""


_USER_COORDINATE_FIELD = "candidate_cell_mgrs"
_TOP_LEVEL_FIELDS = frozenset(
    {
        "title",
        "external_coordinate_format",
        "user_coordinate_field",
        "record_count",
        "source_sensitive_count",
        "records",
        "summary",
        "reason",
    }
)
_RECORD_FIELDS = frozenset(
    {
        "candidate_id",
        "candidate_cell_mgrs",
        "external_coordinate_format",
        "user_coordinate_field",
        "color_class",
        "color_name",
        "overall_score",
        "shielding_stability_score",
        "source_zone",
        "source_sensitive",
        "source_zone_reason",
        "candidate_reason",
        "display_label",
    }
)
_TABLE_COLUMNS = (
    "row_no",
    "candidate_id",
    "candidate_cell_mgrs",
    "color_class",
    "color_name",
    "overall_score",
    "shielding_stability_score",
    "source_zone",
    "source_sensitive",
    "source_zone_reason",
    "candidate_reason",
)
_DIAGNOSTIC_TABLE_COLUMNS = (
    "row_no",
    "candidate_id",
    "candidate_cell_mgrs",
    "diagnostic_status",
    *DIAGNOSTIC_FIELD_ORDER,
)
_DIAGNOSTIC_FIELD_DECIMAL_PLACES = {
    "average_fresnel_score": 1,
    "worst_obstacle_score": 1,
    "dominant_obstacle_distance_from_start_m": 1,
    "dominant_obstacle_dsm_msl": 1,
    "dominant_obstacle_los_msl": 1,
    "dominant_obstacle_clearance_m": 1,
    "dominant_obstacle_clearance_ratio": 3,
    "dominant_obstacle_fresnel_radius_m": 1,
    "dominant_obstacle_nu": 3,
    "dominant_obstacle_diffraction_loss_db": 1,
}


def format_preview_appendix_table(
    preview: Mapping[str, object],
    *,
    max_rows: int | None = None,
) -> str:
    """Return a deterministic Markdown table without mutating or persisting input."""

    records = _validate_preview(preview)
    resolved_limit = _validate_max_rows(max_rows)
    visible_records = records if resolved_limit is None else records[:resolved_limit]
    lines = [
        _table_row(_TABLE_COLUMNS),
        _table_row(tuple("---" for _ in _TABLE_COLUMNS)),
    ]
    for row_no, record in enumerate(visible_records, start=1):
        values = (row_no, *(record[column] for column in _TABLE_COLUMNS[1:]))
        lines.append(_table_row(values))
    omitted_count = len(records) - len(visible_records)
    if omitted_count:
        lines.append(f"... {omitted_count} additional row(s) omitted.")
    return "\n".join(lines)


def format_fresnel_diagnostics_appendix_table(
    preview: Mapping[str, object],
    *,
    max_rows: int | None = None,
) -> str:
    """Return a separate deterministic Markdown table of Fresnel diagnostics."""

    records = _validate_preview(preview)
    resolved_limit = _validate_max_rows(max_rows)
    try:
        states = tuple(validate_flat_fresnel_diagnostics(record) for record in records)
    except CandidateFresnelDiagnosticsError as exc:
        raise PreviewAppendixTableError(f"invalid Fresnel diagnostics: {exc}") from exc

    visible_count = len(records) if resolved_limit is None else resolved_limit
    visible = tuple(zip(records, states, strict=True))[:visible_count]
    lines = [
        _table_row(_DIAGNOSTIC_TABLE_COLUMNS),
        _table_row(tuple("---" for _ in _DIAGNOSTIC_TABLE_COLUMNS)),
    ]
    for row_no, (record, state) in enumerate(visible, start=1):
        lines.append(_table_row(_diagnostic_row_values(row_no, record, state)))
    omitted_count = len(records) - len(visible)
    if omitted_count:
        lines.append(f"... {omitted_count} additional row(s) omitted.")
    return "\n".join(lines)


def _diagnostic_row_values(
    row_no: int,
    record: Mapping[str, object],
    state: str,
) -> tuple[object, ...]:
    identity = (row_no, record["candidate_id"], record["candidate_cell_mgrs"])
    if state == "legacy":
        return (
            *identity,
            "unavailable",
            *("unavailable" for _ in DIAGNOSTIC_FIELD_ORDER),
        )
    if state == "no_eligible":
        return (
            *identity,
            "no-eligible-obstacle",
            *(
                _format_decimal(record[field], _DIAGNOSTIC_FIELD_DECIMAL_PLACES[field])
                if field == "average_fresnel_score"
                else "not-applicable"
                for field in DIAGNOSTIC_FIELD_ORDER
            ),
        )
    return (
        *identity,
        "eligible",
        *(
            _format_decimal(record[field], _DIAGNOSTIC_FIELD_DECIMAL_PLACES[field])
            for field in DIAGNOSTIC_FIELD_ORDER
        ),
    )


def _format_decimal(value: object, places: int) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PreviewAppendixTableError("diagnostic value must be numeric.")
    return f"{float(value):.{places}f}"


def _validate_preview(
    preview: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    if not isinstance(preview, Mapping):
        raise PreviewAppendixTableError("preview must be a mapping.")
    _require_fields("preview", preview, _TOP_LEVEL_FIELDS)
    _reject_internal_keys("preview", preview)
    if preview["external_coordinate_format"] != EXTERNAL_COORDINATE_FORMAT:
        raise PreviewAppendixTableError("preview external_coordinate_format must be MGRS.")
    if preview["user_coordinate_field"] != _USER_COORDINATE_FIELD:
        raise PreviewAppendixTableError(
            "preview user_coordinate_field must be candidate_cell_mgrs."
        )
    raw_records = preview["records"]
    if isinstance(raw_records, (str, bytes)) or not isinstance(raw_records, Sequence):
        raise PreviewAppendixTableError("preview records must be a sequence of mappings.")
    if not raw_records:
        raise PreviewAppendixTableError("preview records must not be empty.")
    records: list[Mapping[str, object]] = []
    for index, record in enumerate(raw_records):
        if not isinstance(record, Mapping):
            raise PreviewAppendixTableError(f"preview record {index} must be a mapping.")
        _validate_record(index, record)
        records.append(record)
    record_count = preview["record_count"]
    if isinstance(record_count, bool) or not isinstance(record_count, int):
        raise PreviewAppendixTableError("preview record_count must be an integer.")
    if record_count != len(records):
        raise PreviewAppendixTableError("preview record_count must equal len(records).")
    return tuple(records)


def _validate_record(index: int, record: Mapping[str, object]) -> None:
    label = f"preview record {index}"
    _require_fields(label, record, _RECORD_FIELDS)
    _reject_internal_keys(label, record)
    mgrs = record["candidate_cell_mgrs"]
    if not isinstance(mgrs, str) or not mgrs.strip():
        raise PreviewAppendixTableError(f"{label} candidate_cell_mgrs must be non-empty.")
    if record["external_coordinate_format"] != EXTERNAL_COORDINATE_FORMAT:
        raise PreviewAppendixTableError(
            f"{label} external_coordinate_format must be MGRS."
        )
    if record["user_coordinate_field"] != _USER_COORDINATE_FIELD:
        raise PreviewAppendixTableError(
            f"{label} user_coordinate_field must be candidate_cell_mgrs."
        )
    if not isinstance(record["source_sensitive"], bool):
        raise PreviewAppendixTableError(f"{label} source_sensitive must be a bool.")
    for field in ("overall_score", "shielding_stability_score"):
        value = record[field]
        if isinstance(value, bool) or not isinstance(value, Real):
            raise PreviewAppendixTableError(f"{label} {field} must be numeric.")


def _require_fields(
    label: str, mapping: Mapping[str, object], required: frozenset[str]
) -> None:
    missing = required.difference(mapping)
    if missing:
        raise PreviewAppendixTableError(
            f"{label} missing required field(s): {', '.join(sorted(missing))}."
        )


def _reject_internal_keys(label: str, mapping: Mapping[str, object]) -> None:
    blocked = INTERNAL_COORDINATE_FIELD_NAMES.intersection(mapping)
    if blocked:
        raise PreviewAppendixTableError(
            f"{label} contains internal coordinate field(s): {', '.join(sorted(blocked))}."
        )


def _validate_max_rows(max_rows: int | None) -> int | None:
    if max_rows is None:
        return None
    if isinstance(max_rows, bool) or not isinstance(max_rows, int):
        raise PreviewAppendixTableError("max_rows must be an integer or None.")
    if max_rows <= 0:
        raise PreviewAppendixTableError("max_rows must be positive.")
    return max_rows


def _table_row(values: Sequence[object]) -> str:
    return "| " + " | ".join(_format_cell(value) for value in values) + " |"


def _format_cell(value: object) -> str:
    normalized = " ".join(str(value).splitlines())
    return normalized.replace("|", r"\|")
