# Experiment Log

책임 주체: GPT Master Agent  
목적: synthetic 및 공개/샘플 DEM·DSM 기반 실험 조건과 결과를 누적 기록한다.

---

## 기록 원칙

- 실제 드론 운용 없이 수행한 오프라인 실험만 기록한다.
- synthetic 데이터와 실제 지형 데이터는 반드시 구분한다.
- 실제 링크상태 데이터가 없으면 RSSI/SINR/packet loss 검증을 수행한 것처럼 기록하지 않는다.
- 실험마다 재현 가능한 입력 파라미터를 남긴다.

---

## Experiment Records

# Experiment EXP-20260708-001

## 관련 Task / Issue / PR

- Task: 001 - Project scaffold and scoring schema preparation
- Issue: #7
- PR: #8

## 목적

향후 synthetic 및 공개/샘플 DEM·DSM 실험을 위한 package/config/schema/test scaffold 준비 상태를 기록한다.

## 데이터 종류

- synthetic DEM: 없음, metadata placeholder only
- synthetic DSM: 없음, metadata placeholder only
- 공개/샘플 DEM: 없음
- 공개/샘플 DSM: 없음
- 실제 링크상태 데이터: 없음
- actual_drone_operation: false
- actual_link_measurement: false

## 결과

- Task 001 scaffold CI status: success
- 색상 등급별 셀 수: 미산출
- 경로 후보별 실 비행거리: 미산출
- 500m 경유점 수: 미산출

## 한계

- 실제 DEM/DSM 없음
- 실제 링크상태 검증 없음
- 실제 드론운용 없음
- 지도 렌더링 확인 없음

---

# Experiment EXP-20260708-002

## 관련 Task / Issue / PR

- Task: 002 - Coordinate and candidate grid module
- Issue: #9
- PR: #10

## 목적

좌표 dataclass, 2D/3D 거리 helper, 후보 발진지 candidate grid scaffold 및 테스트 준비 상태를 기록한다.

## 데이터 종류

- synthetic DEM: 없음
- synthetic DSM: 없음
- 공개/샘플 DEM: 없음
- 공개/샘플 DSM: 없음
- 실제 링크상태 데이터: 없음
- actual_drone_operation: false
- actual_link_measurement: false

## 결과

- 좌표 dataclass scaffold: 작성
- 2D/3D 거리 helper: 작성
- candidate grid scaffold: 작성
- 운용반경 이내/초과 후보 구분: 작성
- CI status: success

## 한계

- 실제 DEM/DSM 없음
- 실제 MGRS 운용 정확도 검증 없음
- 실제 링크상태 검증 없음
- LOS/Fresnel 알고리즘 없음
- 지도 렌더링 확인 없음

---

# Experiment EXP-20260708-003

## 관련 Task / Issue / PR

- Task: 003 - Synthetic DEM/DSM terrain module
- Issue: #11
- PR: #12

## 목적

실제 DEM/DSM 파일 없이 후속 LOS/Fresnel/Scoring 알고리즘 경계조건을 테스트할 수 있도록 순수 Python synthetic DEM/DSM grid generator를 준비한다.

## 데이터 종류

- synthetic DEM: pure Python in-memory grid only
- synthetic DSM: pure Python in-memory grid only
- 공개/샘플 DEM: 없음
- 공개/샘플 DSM: 없음
- 실제 링크상태 데이터: 없음
- actual_drone_operation: false
- actual_link_measurement: false

## 결과

- 8개 synthetic scenario: 작성
- DEM/DSM shape validation: 작성
- DSM >= DEM validation: 작성
- CI status: success

## 한계

- 실제 DEM/DSM 없음
- GeoTIFF 생성 없음
- 실제 링크상태 검증 없음
- LOS/Fresnel 알고리즘 없음
- scoring 없음
- 지도 렌더링 확인 없음

---

# Experiment EXP-20260708-004

## 관련 Task / Issue / PR

- Task: 004 - Terrain profile extraction module
- Issue: #13
- PR: #14

## 목적

synthetic DEM/DSM grid에서 발진점과 드론 위치 사이의 지형 profile sample을 추출하여 이후 DSM-based LOS 및 DSM-based Fresnel 알고리즘의 입력 구조를 준비한다.

## 데이터 종류

- synthetic DEM: profile sampling source only
- synthetic DSM: profile sampling source only
- 공개/샘플 DEM: 없음
- 공개/샘플 DSM: 없음
- 실제 링크상태 데이터: 없음
- actual_drone_operation: false
- actual_link_measurement: false

## 결과

- TerrainProfileSample/TerrainProfile scaffold: 작성
- DEM MSL, DSM MSL, DSM-DEM surface delta, distance fields: 작성
- CI status: success

## 한계

- 실제 DEM/DSM 없음
- LOS 직선고도 계산 없음
- DSM LOS 차단 판정 없음
- Fresnel 반경 또는 clearance 계산 없음
- scoring 없음
- 지도 렌더링 확인 없음

---

# Experiment EXP-20260708-005

## 관련 Task / Issue / PR

- Task: 005 - DSM-based LOS analysis and tests
- Issue: #15
- PR: #16

## 목적

Task 004의 TerrainProfile을 입력으로 받아 발진기지 안테나 MSL과 드론 비행 MSL 사이의 LOS line height, DSM clearance, DSM LOS blocked/clear status, strict dsm_los_score를 계산하는 순수 Python DSM LOS 분석 구조를 준비한다.

## 데이터 종류

- synthetic terrain profile only
- synthetic DEM: TerrainProfile source only
- synthetic DSM: DSM LOS analysis source only
- 공개/샘플 DEM: 없음
- 공개/샘플 DSM: 없음
- 실제 DEM/DSM: 없음
- 실제 링크상태 데이터: 없음
- actual_drone_operation: false
- actual_link_measurement: false

## 결과

- DSM LOS analysis 가능 여부: success
- Task 005 scaffold CI status: success
- package install in CI: success
- syntax check in CI: success
- pytest in CI: success
- ruff in CI: success
- mypy in CI: success
- 색상 등급별 셀 수: 미산출
- 경로 후보별 실 비행거리: 미산출
- 500m 경유점 수: 미산출

## 한계

- 실제 DEM/DSM 없음
- 실제 링크상태 검증 없음
- 실제 드론운용 없음
- Fresnel 반경 또는 clearance 계산 없음
- final scoring 없음
- 색상지도 classification 없음
- 지도 렌더링 확인 없음

---

# Experiment EXP-20260708-006

## 관련 Task / Issue / PR

- Task: 006 - DSM-based Fresnel radius and clearance analysis
- Issue: #17
- PR: #18

## 목적

Task 004 TerrainProfile과 Task 005 LineOfSightAnalysis를 입력으로 받아 sample별 제1 Fresnel radius, DSM clearance ratio, Fresnel intrusion ratio, DSM Fresnel sample score, 평균 dsm_fresnel_score를 계산하는 순수 Python DSM Fresnel 분석 구조를 준비한다.

## 데이터 종류

- synthetic terrain profile and DSM LOS analysis only
- synthetic DEM: TerrainProfile source only
- synthetic DSM: DSM Fresnel analysis source only
- 공개/샘플 DEM: 없음
- 공개/샘플 DSM: 없음
- 실제 DEM/DSM: 없음
- 실제 링크상태 데이터: 없음
- actual_drone_operation: false
- actual_link_measurement: false

## 결과

- Fresnel radius/clearance analysis 가능 여부: success
- Task 006 scaffold CI status: success
- package install in CI: success
- syntax check in CI: success
- pytest in CI: success
- ruff in CI: success
- mypy in CI: success
- 색상 등급별 셀 수: 미산출
- 경로 후보별 실 비행거리: 미산출
- 500m 경유점 수: 미산출

## 한계

- 실제 DEM/DSM 없음
- 실제 링크상태 검증 없음
- 실제 드론운용 없음
- final scoring 없음
- shielding_stability_score 통합 없음
- overall_score 통합 없음
- 색상지도 classification 없음
- 지도 렌더링 확인 없음

---

# Experiment EXP-20260708-007

## 관련 Task / Issue / PR

- Task: 007 - Shielding stability and overall scoring integration
- Issue: #19
- PR: #20

## 목적

Task 005의 DSM LOS component, Task 006의 DSM Fresnel component, 운용반경 대비 3D 거리 기반 distance component를 통합해 candidate launch cell 단위의 shielding_stability_score와 overall_score를 산출하는 순수 Python scoring 구조를 준비한다.

## 데이터 종류

- synthetic score components only
- synthetic DEM: 없음
- synthetic DSM: 없음
- 실제 DEM/DSM: 없음
- 실제 링크상태 데이터: 없음
- actual_drone_operation: false
- actual_link_measurement: false

## 좌표계 및 범위

- distance_3d_m와 operating_radius_m 기반 distance score 계산
- dsm_los_score와 dsm_fresnel_score 기반 shielding_stability_score 계산
- candidate score 산출 구조만 구현
- 색상지도 classification과 지도 렌더링 없음

## 입력 파라미터

- distance_3d_m
- operating_radius_m
- dsm_los_score
- dsm_fresnel_score
- ScoreComponentWeights

## 방법

`distance_score = clamp(100 × (1 - distance_3d_m / operating_radius_m), 0, 100)`로 계산한다. `dsm_los_score == 0`이면 strict LOS cap에 따라 shielding_stability_score를 0으로 둔다. 그 외에는 `dsm_los_score × 0.40 + dsm_fresnel_score × 0.60`으로 shielding_stability_score를 계산한다. overall_score는 `shielding_stability_score × 0.80 + distance_score × 0.20`으로 계산한다.

## 실행 환경

- Cloud: GitHub connector file operations
- Local: Not run in this cloud/GitHub-only context.
- CI: GitHub Actions CI success observed for PR #20 head commit before this CI-status log update; follow-up CI after this log update should be rechecked before merge.

## 실행 명령

- Local commands: Not run in this cloud/GitHub-only context.
- CI commands: GitHub Actions executed install, syntax check, pytest, ruff, and mypy successfully on the checked PR #20 run.

## 결과

- scoring integration 가능 여부: success on the checked PR #20 CI run
- Task 007 scaffold CI status: success on the checked PR #20 CI run
- package install in CI: success
- syntax check in CI: success
- pytest in CI: success
- ruff in CI: success
- mypy in CI: success
- 색상 등급별 셀 수: 미산출
- 경로 후보별 실 비행거리: 미산출
- 500m 경유점 수: 미산출

## 해석

Task 007은 실제 실험 결과가 아니라 candidate scoring integration 준비 단계다. CI success는 scoring integration 코드와 테스트 코드의 동작 확인에 한정하며, 실제 DEM/DSM 또는 링크품질 검증 결과가 아니다.

## 한계

- 실제 DEM/DSM 없음
- 실제 링크상태 검증 없음
- 실제 드론운용 없음
- 색상지도 classification 없음
- 지도 렌더링 확인 없음
- Streamlit/Folium UI 없음
- Top 5 기본 출력 없음

## 논문 반영 가능 여부

방법론의 score integration, strict LOS cap, distance reserve proxy 설계에는 반영 가능. 실제 결과 장에는 아직 반영 불가.

## GPT Master 검토 메모

PR #20 생성 후 distance_score, shielding_stability_score, overall_score, strict LOS cap, weight validation, score validation, CI 결과를 기준으로 편입 여부를 판단한다. 이 로그 업데이트 이후 follow-up CI 결과도 merge 전 확인해야 한다.

---

# Experiment EXP-20260708-008

## 관련 Task / Issue / PR

- Task: 008 - Color map classification and launch-area cell evaluation
- Issue: #21
- PR: #22

## 목적

Task 007의 CandidateScore 결과를 기반으로 launch-area candidate cell을 Green/Yellow/Orange/Red/Excluded 계열의 color class로 분류하는 순수 Python classification 구조를 준비한다.

## 데이터 종류

- synthetic candidate score classification only
- synthetic DEM: 없음
- synthetic DSM: 없음
- 실제 DEM/DSM: 없음
- 실제 링크상태 데이터: 없음
- actual_drone_operation: false
- actual_link_measurement: false

## 좌표계 및 범위

- CandidateScore 기반 color classification
- within_operation_radius 기반 Excluded 처리
- DSM LOS blocked/high-risk Red 처리
- overall_score threshold 기반 Green/Yellow/Orange/Red 처리
- 실제 지도 렌더링 없음

## 입력 파라미터

- cell_id
- CandidateScore
- within_operation_radius
- ColorClassificationThresholds

## 방법

`within_operation_radius == False`이면 Excluded로 분류한다. `dsm_los_score == 0`, `shielding_stability_score == 0`, 또는 `overall_score < 40`이면 Red로 분류한다. `40 <= overall_score < 60`은 Orange, `60 <= overall_score < 75`는 Yellow, `overall_score >= 75`이고 DSM LOS가 clear이면 Green으로 분류한다.

## 실행 환경

- Cloud: GitHub connector file operations
- Local: Not run in this cloud/GitHub-only context.
- CI: PR 생성 후 확인 필요

## 실행 명령

- Local commands: Not run in this cloud/GitHub-only context.
- CI commands: PR 생성 후 GitHub Actions가 install, syntax check, pytest, ruff, mypy를 실행할 것으로 예상

## 결과

- classification 로직 가능 여부: PR/CI 확인 전
- Task 008 scaffold CI status: PR 생성 후 확인 필요
- package install in CI: PR 생성 후 확인 필요
- syntax check in CI: PR 생성 후 확인 필요
- pytest in CI: PR 생성 후 확인 필요
- ruff in CI: PR 생성 후 확인 필요
- mypy in CI: PR 생성 후 확인 필요
- 색상 등급별 셀 수: 미산출
- 경로 후보별 실 비행거리: 미산출
- 500m 경유점 수: 미산출

## 해석

Task 008은 실제 지도 결과가 아니라 color launch-area map에 사용할 classification data structure 준비 단계다. 논문 결과 장에는 아직 반영하지 않는다.

## 한계

- 실제 DEM/DSM 없음
- 실제 링크상태 검증 없음
- 실제 드론운용 없음
- 실제 지도 렌더링 없음
- Folium/Streamlit UI 없음
- route planning 없음
- Top 5 기본 출력 없음

## 논문 반영 가능 여부

방법론의 launch-area color classification heuristic, threshold design, excluded/high-risk handling에는 반영 가능. 실제 결과 장에는 아직 반영 불가.

## GPT Master 검토 메모

PR #22 생성 후 ColorClass 재사용, threshold validation, within-radius/out-of-radius 분류, LOS blocked Red 처리, score threshold 분류, CI 결과를 기준으로 편입 여부를 판단한다.

---

# Experiment EXP-20260709-009

## 관련 Task / Issue / PR

- Task: 009 - Route candidate evaluation scaffold
- Issue: #24
- PR: #25

## 목적

선택된 발진기지와 목표지점 사이의 후보 경로를 표현하고, 경로별 거리비용, 차폐위험비용, high-risk cell 통과 penalty를 계산할 수 있는 순수 Python route candidate evaluation scaffold를 준비한다.

## 데이터 종류

- synthetic route candidate only
- actual_drone_operation: false
- actual_link_measurement: false
- real_dem_dsm_loading: false
- map_rendering: false
- route_execution: false
- 실제 링크상태 데이터: 없음

## 좌표계 및 범위

- RouteCell 기반 경로 후보 데이터 구조
- RouteCandidateType 3종: shielding_minimum, distance_shielding_balanced, detour_stability
- route total distance, mean/min shielding score, high-risk cell count, route_cost 계산
- high-risk cell은 DSM 기반 color classification 결과의 Red/Orange cell만 의미
- 적 위협·방공망·회피기동·침투경로·공격경로 의미 없음

## 입력 파라미터

- route_id
- route_type
- RouteCell sequence
- RouteCostWeights
- distance_normalizer_m

## 방법

distance_cost = clamp(total_distance_m / distance_normalizer_m, 0, 1) * 100 으로 거리 비용을 계산한다.
shielding_risk_cost = 100 - mean_shielding_stability_score 로 차폐위험 비용을 계산한다.
high_risk_cost = high_risk_cell_count * 100 을 DSM 기반 Red/Orange cell 통과 penalty로 사용한다.
최종 route_cost는 각 비용에 RouteCostWeights를 곱해 합산한다.

## 실행 환경

- Cloud: GitHub connector file operations
- Local: Not run in this cloud/GitHub-only context.
- CI: GitHub Actions CI success observed for PR #25 head commit `68bd3bf7201ca916b2b2b30aadce0c472b4cca41`

## 실행 명령

- Local commands: Not run in this cloud/GitHub-only context.
- CI commands: GitHub Actions executed install, syntax check, pytest, ruff, and mypy successfully on the checked PR #25 run.

## 결과

- route candidate scaffold 가능 여부: success on checked PR #25 CI run
- Task 009 CI status: success
- package install in CI: success
- syntax check in CI: success
- pytest in CI: success
- ruff in CI: success
- mypy in CI: success
- 색상 등급별 셀 수: 미산출
- 실제 DEM/DSM 기반 경로 후보: 미산출
- 500m waypoint output: 미산출

## 해석

Task 009는 실제 지도 결과나 실제 비행경로 실행 결과가 아니라, 후속 지도/UI와 논문 분석에 사용할 offline route evaluation data structure 준비 단계다. 최종 논문에서는 시스템 구현 및 모델 반응성 분석 자료로만 활용하며, 실측 통신품질 검증으로 표현하지 않는다.

## 한계

- 실제 DEM/DSM 없음
- 실제 링크상태 검증 없음
- 실제 드론운용 없음
- 실제 비행경로 실행 없음
- 자율비행/비행명령 생성 없음
- 지도 렌더링 없음
- Folium/Streamlit UI 없음
- Task 010 waypoint 본구현 없음

## 논문 반영 가능 여부

방법론의 route candidate cost model, route type 비교, high-risk cell penalty 설계, 민감도 분석 항목에는 반영 가능하다. 실제 지형 적용 결과, 실제 지도 렌더링 결과, 실제 비행 결과, 실제 링크품질 검증 결과로는 아직 반영할 수 없다.

## GPT Master 검토 메모

PR #25는 코드 기준 Task 009 acceptance criteria를 충족한다. 단, merge 전 experiment-log 기존 상세 기록 보존 여부와 CI success 기록 갱신 여부를 재확인해야 한다.
