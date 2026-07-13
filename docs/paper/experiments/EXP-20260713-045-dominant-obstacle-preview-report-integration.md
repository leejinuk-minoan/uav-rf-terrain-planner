# EXP-20260713-045 - Dominant Obstacle Preview/Report Integration

## Experiment Purpose

Task 033A output contract를 runtime candidate preview 및 report 경로에 구현하고 backward compatibility를 검증한다.

## Actual Implementation Path

`FresnelAnalysis` → `CandidateFresnelDiagnostics` → synthetic candidate → map feature → display record → flat preview dictionary → plain text/report 순서로 연결했다.

## Input Data

Synthetic eligible obstacle, no-eligible interior sample, legacy preview, partial/mixed/non-finite diagnostic records를 사용했다.

## Compatibility States Verified

Legacy, complete eligible, complete no-eligible, invalid partial/mixed/non-finite 상태를 검증했다. JSON null과 원래 float 값 보존을 확인했다.

## Output Examples

Plain text는 average/worst/loss 요약을 표시한다. Report는 candidate id와 MGRS를 식별자로 사용해 전체 approved diagnostic을 지정 정밀도로 표시한다. Generated output은 커밋하지 않았다.

검증 결과 JSON의 float/null 상태, plain-text 정밀도, deterministic report section과 candidate 순서가 유지됐다. Appendix table은 diagnostic extra key를 무시하고 기존 column과 row-limit contract를 유지했다. Input mapping은 변경되지 않았고 user-facing output에는 internal coordinate가 추가되지 않았다.

## Scoring Invariants

기존 candidate score, shielding score, color와 record order를 유지하며 diagnostic 값을 scoring에 입력하지 않는다. Route cost와 waypoint cost도 변경하지 않았다.

## Tests Executed

Local Execution Agent 실행 결과:

- `python -m compileall src`: success
- focused tests: 140 passed
- `python -m pytest`: 740 passed
- `python -m ruff check .`: success
- `python -m mypy src`: success
- `git diff --check`: success

## CI Result

Initial implementation reviewed-head evidence:

- CI #770
- head: `31ad2abcb27df940048dc0e7678888ff5e9c11a5`
- status: completed
- conclusion: success
- install, syntax check, pytest, Ruff, mypy: success

Final PR-head evidence:

- CI #772
- head: `db0b555f72b802c0ecc53cac3276e47815ae121c`
- status: completed
- conclusion: success
- install, syntax check, pytest, Ruff, mypy: success

CI #770 is evidence for the initial implementation reviewed head. CI #772 is the separately observed result for the final PR head after the documentation amendment. The two runs are not treated as interchangeable.

## Merge Evidence

```text
PR #85: merged
final PR head: db0b555f72b802c0ecc53cac3276e47815ae121c
merge commit: 33f93f68cd22efde9a3d7b8ae1aae0713681860c
merged at: 2026-07-13T13:04:38Z
Issue #84: completed
Task 033B: complete on main
```

## Interpretation

사용자는 average Fresnel score와 localized worst obstacle proxy를 구분해 검토할 수 있다.

이 결과는 offline synthetic integration evidence다. Field RF evidence는 수집하거나 검증하지 않았다.

## Limitations

이 결과는 offline terrain/surface diagnostic proxy이며 full link budget, measured RF result 또는 communication outcome prediction이 아니다. 실제 비행 가능성도 예측하거나 보장하지 않는다.

## Figure/Table Candidacy

Eligible, no-eligible, legacy 3상태 report 비교가 향후 논문 표 후보가 될 수 있다. 현재 appendix table은 의도적으로 변경하지 않는다.

## Public Repository Sensitivity Check

Synthetic evidence와 repository-relative 문서만 기록하며 GIS data, private path, generated artifact를 포함하지 않는다.

## Follow-Up Tasks

UI projection, appendix-table 확장, scoring 활용 또는 field RF validation은 별도 설계·검증이 필요하다.
