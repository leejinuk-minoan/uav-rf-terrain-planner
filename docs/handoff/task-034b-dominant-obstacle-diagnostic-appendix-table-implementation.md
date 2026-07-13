# Task 034B Dominant Obstacle Diagnostic Appendix-Table Implementation

## Purpose

Task 034A에서 승인한 별도 opt-in pure Markdown diagnostic appendix formatter를 구현한다.

## Implementation

`src/uav_rf_terrain/preview_appendix_table.py`에 `format_fresnel_diagnostics_appendix_table(preview, *, max_rows=None)`를 추가했다. 기존 preview validation, max-row validation, Markdown cell escaping과 `fresnel_diagnostics.py`의 diagnostic state validator를 재사용한다.

## Default Formatter Regression

기존 `format_preview_appendix_table(...)` signature, 11개 열과 순서, candidate order, row numbering, omission wording, input immutability와 no-file behavior는 변경하지 않았다. Malformed diagnostic extra도 기존 기본 formatter에서는 계속 무시한다.

## Diagnostic Contract

별도 표는 승인된 14개 열을 사용한다. Legacy는 `unavailable`, eligible은 지정 정밀도 numeric text, no-eligible은 finite average와 9개 `not-applicable`을 표시한다. Partial, mixed-null, bool, NaN과 infinity는 `PreviewAppendixTableError`로 변환한다.

## Local Verification

- `python -m compileall src`: success
- `python -m pytest tests/test_preview_appendix_table.py tests/test_dominant_obstacle_preview_integration.py`: 46 passed
- `python -m pytest`: 757 passed
- `python -m ruff check .`: success
- `python -m mypy src`: success
- `git diff --check`: success

## Invariants

Scoring, color, ranking, route, waypoint, preview JSON, plain text, report, CLI와 map/UI behavior는 변경하지 않았다.

## Limitations

Diagnostic values는 offline terrain/surface support proxy이며 full link budget 또는 field RF evidence가 아니다.

## Public Repository Sensitivity Check

GIS data, `METADATA_MAP`, generated table, credential, private path 또는 device/flight-control content를 추가하지 않았다.

## Follow-Up Tasks

CLI/file output 또는 report 자동 composition은 별도 reviewed Task가 필요하다.
