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

- Task: 001 - Project scaffold and scoring schema preparation
- Issue: #7
- PR: #8
- 데이터 종류: scaffold only
- actual_drone_operation: false
- actual_link_measurement: false
- 결과: package/config/schema/test scaffold 준비
- 한계: 실제 DEM/DSM, 실제 링크상태, 실제 드론운용, 지도 렌더링 없음

---

# Experiment EXP-20260708-002

- Task: 002 - Coordinate and candidate grid module
- Issue: #9
- PR: #10
- 데이터 종류: coordinate/grid scaffold only
- actual_drone_operation: false
- actual_link_measurement: false
- 결과: 좌표 dataclass, 2D/3D 거리 helper, candidate grid scaffold 작성
- 한계: 실제 DEM/DSM, 실제 MGRS 운용 정확도 검증, LOS/Fresnel, 지도 렌더링 없음

---

# Experiment EXP-20260708-003

- Task: 003 - Synthetic DEM/DSM terrain module
- Issue: #11
- PR: #12
- 데이터 종류: pure Python in-memory synthetic DEM/DSM only
- actual_drone_operation: false
- actual_link_measurement: false
- 결과: 8개 synthetic scenario 및 DEM/DSM validation scaffold 작성
- 한계: 실제 DEM/DSM, GeoTIFF, 실제 링크상태, LOS/Fresnel, scoring, 지도 렌더링 없음

---

# Experiment EXP-20260708-004

- Task: 004 - Terrain profile extraction module
- Issue: #13
- PR: #14
- 데이터 종류: synthetic terrain profile only
- actual_drone_operation: false
- actual_link_measurement: false
- 결과: TerrainProfileSample/TerrainProfile scaffold와 profile extraction 작성
- 한계: 실제 DEM/DSM, LOS 판정, Fresnel, scoring, 지도 렌더링 없음

---

# Experiment EXP-20260708-005

- Task: 005 - DSM-based LOS analysis and tests
- Issue: #15
- PR: #16
- 데이터 종류: synthetic terrain profile and DSM LOS analysis only
- actual_drone_operation: false
- actual_link_measurement: false
- 결과: DSM LOS line height, clearance, blocked/clear, dsm_los_score scaffold 작성
- 한계: 실제 DEM/DSM, 실제 링크상태, Fresnel, final scoring, 색상지도 classification, 지도 렌더링 없음

---

# Experiment EXP-20260708-006

- Task: 006 - DSM-based Fresnel radius and clearance analysis
- Issue: #17
- PR: #18
- 데이터 종류: synthetic terrain profile and DSM Fresnel analysis only
- actual_drone_operation: false
- actual_link_measurement: false
- 결과: wavelength, first Fresnel radius, clearance ratio, intrusion ratio, dsm_fresnel_score scaffold 작성
- 한계: 실제 DEM/DSM, 실제 링크상태, final scoring, 색상지도 classification, 지도 렌더링 없음

---

# Experiment EXP-20260708-007

- Task: 007 - Shielding stability and overall scoring integration
- Issue: #19
- PR: #20
- 데이터 종류: synthetic score components only
- actual_drone_operation: false
- actual_link_measurement: false
- 결과: CandidateScore, distance_score, shielding_stability_score, overall_score, strict LOS cap scaffold 작성
- 한계: 실제 DEM/DSM, 실제 링크상태, 색상지도 classification, 지도 렌더링, Top 5 기본 출력 없음

---

# Experiment EXP-20260708-008

- Task: 008 - Color map classification and launch-area cell evaluation
- Issue: #21
- PR: #22
- 데이터 종류: synthetic candidate score classification only
- actual_drone_operation: false
- actual_link_measurement: false
- 결과: CandidateScore 기반 Green/Yellow/Orange/Red/Excluded color classification scaffold 작성
- 한계: 실제 DEM/DSM, 실제 링크상태, 실제 지도 렌더링, Folium/Streamlit UI, route planning, Top 5 기본 출력 없음

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

## 입력 파라미터

- route_id
- route_type
- RouteCell sequence
- RouteCostWeights
- distance_normalizer_m

## 방법

`distance_cost = clamp(total_distance_m / distance_normalizer_m, 0, 1) * 100`으로 거리 비용을 계산한다. `shielding_risk_cost = 100 - mean_shielding_stability_score`로 차폐위험 비용을 계산하고, `high_risk_cost = high_risk_cell_count * 100`을 DSM 기반 Red/Orange cell 통과 penalty로 사용한다. 최종 `route_cost`는 각 비용에 RouteCostWeights를 곱해 합산한다.

## 실행 환경

- Cloud: GitHub connector file operations
- Local: Not run in this cloud/GitHub-only context.
- CI: PR 생성 후 확인 필요

## 실행 명령

- Local commands: Not run in this cloud/GitHub-only context.
- CI commands: PR 생성 후 GitHub Actions가 install, syntax check, pytest, ruff, mypy를 실행할 것으로 예상

## 결과

- route candidate scaffold 가능 여부: PR/CI 확인 전
- Task 009 CI status: PR 생성 후 확인 필요
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

PR 생성 후 route data structure, cost model, RED/ORANGE high-risk count, EXCLUDED cell rejection, no real flight/control/link fields, CI 결과를 기준으로 편입 여부를 판단한다.
