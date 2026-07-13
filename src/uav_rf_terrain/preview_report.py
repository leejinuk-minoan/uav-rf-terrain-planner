"""Pure formatter for deterministic human-readable preview reports."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping

from .preview_appendix_table import (
    PreviewAppendixTableError,
    format_preview_appendix_table,
)
from .fresnel_diagnostics import (
    CandidateFresnelDiagnosticsError,
    validate_flat_fresnel_diagnostics,
)


class PreviewReportError(ValueError):
    """Raised when preview input violates the report contract."""


def format_preview_report(
    preview: Mapping[str, object],
    *,
    include_table: bool = True,
) -> str:
    """Return a deterministic human-readable report without mutating input."""

    try:
        table = format_preview_appendix_table(preview)
    except PreviewAppendixTableError as exc:
        raise PreviewReportError(f"invalid preview report input: {exc}") from exc

    records = preview["records"]
    assert isinstance(records, list)
    try:
        diagnostic_states = [validate_flat_fresnel_diagnostics(record) for record in records]
    except CandidateFresnelDiagnosticsError as exc:
        raise PreviewReportError(f"invalid preview report input: {exc}") from exc
    color_classes = Counter(str(record["color_class"]) for record in records)
    color_names = Counter(str(record["color_name"]) for record in records)
    source_zones = Counter(str(record["source_zone"]) for record in records)
    overall_scores = [record["overall_score"] for record in records]
    shielding_scores = [record["shielding_stability_score"] for record in records]

    sections = [
        "# Preview Candidate Report",
        "",
        "## Summary",
        f"- Record count: {preview['record_count']}",
        f"- Source-sensitive count: {preview['source_sensitive_count']}",
        f"- External coordinate format: {preview['external_coordinate_format']}",
        f"- User coordinate field: {preview['user_coordinate_field']}",
        "",
        "## Source and Output Context",
        "Input provenance: not encoded in preview",
        "",
        "## Candidate Overview",
        f"- Total candidate count: {len(records)}",
        f"- Color class counts: {_format_counts(color_classes)}",
        f"- Color name counts: {_format_counts(color_names)}",
        f"- Overall score range: {min(overall_scores)} to {max(overall_scores)}",
        "- Shielding stability score range: "
        f"{min(shielding_scores)} to {max(shielding_scores)}",
        "",
        "## Fresnel Diagnostics",
        *_format_fresnel_diagnostics(records, diagnostic_states),
        "- Values are terrain/surface diagnostic proxies only; they do not constitute a full link budget or measured RF validation.",
        "",
        "## Source-Zone Interpretation",
        f"- Source-zone counts: {_format_counts(source_zones)}",
        f"- Source-sensitive count: {preview['source_sensitive_count']}",
        "- source_zone, source_sensitive, and source_zone_reason are interpretation metadata only.",
        "",
        "## Coordinate Boundary",
        f"- external_coordinate_format = {preview['external_coordinate_format']}",
        f"- user_coordinate_field = {preview['user_coordinate_field']}",
        "- Candidate coordinates use the existing candidate_cell_mgrs text without conversion or geographic validation.",
    ]
    if include_table:
        sections.extend(("", "## Appendix Table", table))
    sections.extend(
        (
            "",
            "## Limitations",
            "- Uses reviewed preview fields only.",
            "- No coordinate conversion or geographic validation.",
            "- No field RF measurement validation.",
            "- No LOS/Fresnel recalculation.",
            "- No candidate rescoring or reranking.",
            "- No route or waypoint alteration.",
            "- Not an external-device, autopilot, vehicle-control, or flight-control output.",
        )
    )
    return "\n".join(sections) + "\n"


def _format_counts(counts: Counter[str]) -> str:
    return ", ".join(f"{name}={count}" for name, count in counts.items())


def _format_fresnel_diagnostics(
    records: list[object], states: list[str]
) -> list[str]:
    lines: list[str] = []
    for record, state in zip(records, states, strict=True):
        assert isinstance(record, Mapping)
        identity = f"{record['candidate_id']} | {record['candidate_cell_mgrs']}"
        if state == "legacy":
            lines.append(f"- {identity}: diagnostics unavailable in this preview record")
            continue
        average = float(record["average_fresnel_score"])
        if state == "no_eligible":
            lines.append(
                f"- {identity}: average={average:.1f}; no eligible interior dominant obstacle sample"
            )
            continue
        lines.append(
            f"- {identity}: average={average:.1f}; "
            f"worst={float(record['worst_obstacle_score']):.1f}; "
            f"distance={float(record['dominant_obstacle_distance_from_start_m']):.1f} m; "
            f"DSM={float(record['dominant_obstacle_dsm_msl']):.1f} m; "
            f"LOS={float(record['dominant_obstacle_los_msl']):.1f} m; "
            f"clearance={float(record['dominant_obstacle_clearance_m']):.1f} m; "
            f"clearance_ratio={float(record['dominant_obstacle_clearance_ratio']):.3f}; "
            f"Fresnel radius={float(record['dominant_obstacle_fresnel_radius_m']):.1f} m; "
            f"nu={float(record['dominant_obstacle_nu']):.3f}; "
            f"diffraction_loss={float(record['dominant_obstacle_diffraction_loss_db']):.1f} dB"
        )
    return lines
