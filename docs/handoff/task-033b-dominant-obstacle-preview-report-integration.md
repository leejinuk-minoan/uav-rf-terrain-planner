# Task 033B Dominant Obstacle Preview/Report Integration

## Purpose

Task 033A에서 승인된 optional dominant Fresnel obstacle diagnostic을 candidate preview 및 report 경로에 구현한다.

## Implementation Path

`FresnelAnalysis`를 immutable `CandidateFresnelDiagnostics`로 변환하고, 이를 `SyntheticCandidateRecord`, `CandidateCellMapFeature`, `CandidateDisplayRecord`, preview dictionary, plain text, report로 전달한다. Flat 10-key expansion은 display dictionary 경계에서만 수행한다.

## Compatibility States

- Legacy: diagnostic key 전체 부재를 허용한다.
- Eligible: 10개 key와 finite numeric value 전체를 출력한다.
- No eligible: average는 finite numeric, 나머지 9개 key는 `None`/JSON `null`이다.
- Partial, mixed-null, bool, NaN, infinity는 diagnostic-aware preview/report validation에서 거부한다.

## Output Behavior

JSON은 원래 float 정밀도를 유지한다. Plain text는 average, worst, diffraction loss만 1자리 정밀도로 표시한다. Report는 deterministic `## Fresnel Diagnostics` section에서 candidate 순서를 유지하고 전체 approved 값을 표시한다.

## Appendix Table Boundary

Appendix table의 column, order, row limit은 변경하지 않으며 diagnostic extra key를 표시하지 않는다.

## Scoring and Ordering Invariants

Diagnostic은 score, strict LOS cap, color, rank, route 또는 waypoint 계산에 사용하지 않는다. 기존 default synthetic builder는 legacy output을 유지한다.

## Tests and Verification

Focused conversion, pipeline, validation, plain-text, report 및 appendix-table regression tests를 추가했다. 최종 local 및 CI 결과는 PR completion report에 기록한다.

## Limitations

Single knife-edge loss는 terrain/surface diagnostic proxy이며 full link budget 또는 measured RF validation이 아니다.

## Public Repository Sensitivity Check

Private path, generated output artifact, GIS data, credential 또는 internal coordinate를 추가하지 않았다.

## Follow-Up Tasks

Diagnostic의 scoring 반영 또는 UI 시각화는 별도 검토 Task가 필요하다.
