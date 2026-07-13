# EXP-20260714-048 - Dominant Obstacle Diagnostic Appendix-Table Implementation

## Experiment Purpose

Task 034A의 separate diagnostic appendix-table contract를 구현하고 default formatter regression을 검증한다.

## Input Data

Saved-preview-compatible synthetic dictionaries로 legacy, eligible, no-eligible, partial, mixed-null, bool, NaN, positive/negative infinity 상태를 구성했다.

## Method

기존 base preview/max_rows/Markdown helpers와 `validate_flat_fresnel_diagnostics(...)`를 재사용해 별도 14-column Markdown table을 생성했다.

## Actual Result

세 valid 상태가 exact status/null text와 지정 정밀도로 출력됐다. Invalid states는 appendix error boundary에서 거부됐다. Candidate order, max_rows subset, omission wording, MGRS coordinate boundary, Markdown escaping, input immutability와 no-file behavior가 유지됐다.

## Default Formatter Regression

기본 11-column formatter는 exact output contract를 유지하고 malformed diagnostic extras를 계속 무시했다. Report와 CLI implementation은 변경하지 않았다.

## Local Test Result

- compileall: success
- focused tests: 46 passed
- full pytest: 757 passed
- Ruff: success
- mypy: success
- diff check: success

## Interpretation

별도 표는 paper/developer review를 위한 row-wise offline diagnostic projection이다. Scoring, color, rank, route와 waypoint 계산에 영향을 주지 않는다.

## Limitations

Single knife-edge diagnostic은 full link budget, measured RF validation 또는 communication/flight outcome evidence가 아니다.

## Figure/Table Candidacy

Legacy/eligible/no-eligible 상태 비교와 candidate별 clearance/loss 값은 논문 appendix table 후보가 될 수 있다.

## Public Repository Sensitivity Check

Synthetic test evidence만 사용했고 generated table file, GIS data, private path 또는 credential을 커밋하지 않았다.

## Follow-Up Tasks

향후 CLI 또는 report composition은 별도 output-boundary 검토가 필요하다.
